"""
Robot seguidor de carril — versión mejorada
Mejoras aplicadas:
  - Control proporcional (P) sobre error de posición + ángulo
  - threading.Event en vez de variable global para obstáculo
  - Ángulo calculado con math.atan2 (independiente de escala)
  - ROI y umbrales centralizados como constantes
  - Logging estructurado (reemplaza silenciar excepciones)
  - Shutdown limpio de cámara y serial
  - FPS controlado por timestamp (no sleep bloqueante)
"""

from flask import Flask, Response
from picamera2 import Picamera2
import cv2
import numpy as np
import serial
import time
import threading
import math
import logging
import signal
import sys

# ─────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger("robot")

# ─────────────────────────────────────────
# CONFIGURACIÓN CENTRALIZADA
# ─────────────────────────────────────────
SERIAL_PORT    = "/dev/ttyUSB0"
SERIAL_BAUD    = 115200

CAM_WIDTH      = 1280
CAM_HEIGHT     = 720

ROI_FACTOR     = 0.70    # fracción de altura donde empieza el ROI (0.0 = arriba, 1.0 = abajo)
MIN_CONTOUR_AREA = 300

# Zona objetivo: dónde debe estar la línea (fracción del ancho del ROI)
ZONE_LEFT      = 0.55
ZONE_RIGHT     = 0.75

# Control proporcional
# error de posición: máximo posible = ancho ROI / 2
# error de ángulo:   máximo útil ≈ 45°
KP_POS         = 0.003   # ganancia para error lateral (produce valor 0..1)
KP_ANG         = 0.015   # ganancia para ángulo

# Umbral de ángulo para detectar curva (grados)
ANGLE_CURVE_THRESHOLD = 22.0

# Distancia de obstáculo (cm)
OBSTACLE_DIST_CM = 30.0

# FPS máximo del stream
STREAM_FPS     = 25
FRAME_INTERVAL = 1.0 / STREAM_FPS

# ─────────────────────────────────────────
# FLASK
# ─────────────────────────────────────────
app = Flask(__name__)

# ─────────────────────────────────────────
# SERIAL
# ─────────────────────────────────────────
try:
    ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=1)
    time.sleep(2)
    log.info("Serial abierto en %s @ %d", SERIAL_PORT, SERIAL_BAUD)
except serial.SerialException as e:
    log.error("No se pudo abrir serial: %s", e)
    ser = None

serial_lock = threading.Lock()

# ─────────────────────────────────────────
# ESTADO COMPARTIDO (thread-safe)
# ─────────────────────────────────────────
obstaculo_event = threading.Event()   # set() = hay obstáculo

# ─────────────────────────────────────────
# CÁMARA
# ─────────────────────────────────────────
picam2 = Picamera2()
config = picam2.create_video_configuration(
    main={"size": (CAM_WIDTH, CAM_HEIGHT), "format": "XBGR8888"}
)
picam2.configure(config)
picam2.start()
picam2.set_controls({
    "AwbEnable":    False,
    "ColourGains":  (1.4, 1.6),
    "AeEnable":     True,
    "ExposureValue": -0.2,
    "Brightness":   0.0,
    "Contrast":     1.2,
    "Saturation":   1.1,
})
log.info("Cámara iniciada (%dx%d)", CAM_WIDTH, CAM_HEIGHT)

# ─────────────────────────────────────────
# SENSOR ULTRASÓNICO
# ─────────────────────────────────────────
try:
    from gpiozero import DistanceSensor
    sensor = DistanceSensor(echo=24, trigger=23, max_distance=4)
    log.info("Sensor ultrasónico listo (GPIO 23/24)")
except Exception as e:
    sensor = None
    log.warning("Sensor ultrasónico no disponible: %s", e)


def hilo_ultrasonido():
    while True:
        try:
            if sensor is None:
                time.sleep(1)
                continue

            lecturas = []
            for _ in range(3):
                d = sensor.distance * 100
                if 2 < d < 400:
                    lecturas.append(d)
                time.sleep(0.05)

            if lecturas:
                distancia = sum(lecturas) / len(lecturas)
                if distancia <= OBSTACLE_DIST_CM:
                    obstaculo_event.set()
                else:
                    obstaculo_event.clear()
            else:
                # Sin lecturas válidas → conservar estado anterior (no limpiar)
                pass

        except Exception as e:
            log.warning("Ultrasonido error: %s", e)
            obstaculo_event.clear()

        time.sleep(0.3)


threading.Thread(target=hilo_ultrasonido, daemon=True, name="ultrasonido").start()

# ─────────────────────────────────────────
# PROCESAMIENTO DE IMAGEN
# ─────────────────────────────────────────

def mejorar_imagen(frame: np.ndarray) -> np.ndarray:
    """Convierte XBGR → BGR (reordena canales)."""
    r, g, b = frame[:, :, 0], frame[:, :, 1], frame[:, :, 2]
    return cv2.merge([b, g, r])


def auto_brillo(frame: np.ndarray) -> np.ndarray:
    """Ajuste automático de brillo basado en luminosidad media."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    error = 120 - float(np.mean(gray))
    return cv2.convertScaleAbs(frame, alpha=1.0 + error / 200, beta=error * 0.5)


def reducir_saturacion(frame: np.ndarray) -> np.ndarray:
    """Recorta el canal V para evitar sobreexposición."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hsv[:, :, 2] = np.clip(hsv[:, :, 2], 0, 230)
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


# ─────────────────────────────────────────
# ENVÍO DE COMANDOS (sin duplicados)
# ─────────────────────────────────────────
ultimo_comando: str | None = None


def enviar_comando(cmd: str) -> None:
    global ultimo_comando
    if cmd == ultimo_comando:
        return
    if ser is None:
        ultimo_comando = cmd
        return
    with serial_lock:
        try:
            ser.write((cmd + "\n").encode())
            ultimo_comando = cmd
        except serial.SerialException as e:
            log.error("Error al enviar comando '%s': %s", cmd, e)


# ─────────────────────────────────────────
# DETECCIÓN DE CARRILES + CONTROL P
# ─────────────────────────────────────────

def detectar_carriles(frame: np.ndarray) -> np.ndarray:
    altura, ancho = frame.shape[:2]
    roi_y = int(altura * ROI_FACTOR)
    roi = frame[roi_y:, :].copy()
    roi_h, roi_w = roi.shape[:2]

    # ── Máscara roja (doble rango HSV) ──────────────────────────────
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    mask_r1 = cv2.inRange(hsv, np.array([0, 100, 60]),   np.array([10,  255, 255]))
    mask_r2 = cv2.inRange(hsv, np.array([165, 100, 60]), np.array([180, 255, 255]))
    mask_rojo = cv2.bitwise_or(mask_r1, mask_r2)

    kernel = np.ones((5, 5), np.uint8)
    mask_rojo = cv2.morphologyEx(mask_rojo, cv2.MORPH_OPEN,  kernel)
    mask_rojo = cv2.morphologyEx(mask_rojo, cv2.MORPH_CLOSE, kernel)

    # ── Contornos ───────────────────────────────────────────────────
    contornos, _ = cv2.findContours(mask_rojo, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contornos:
        enviar_comando("x")
        cv2.putText(frame, "SIN LINEA", (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        return frame

    c = max(contornos, key=cv2.contourArea)
    if cv2.contourArea(c) < MIN_CONTOUR_AREA:
        enviar_comando("x")
        return frame

    cv2.drawContours(roi, [c], -1, (0, 255, 0), 2)

    # ── FitLine → ángulo real con atan2 ─────────────────────────────
    [vx, vy, x0, y0] = cv2.fitLine(c, cv2.DIST_L2, 0, 0.01, 0.01)
    vx, vy = float(vx), float(vy)

    # Ángulo en grados respecto a la horizontal (0° = línea horizontal)
    angulo_deg = math.degrees(math.atan2(abs(vy), abs(vx) + 1e-9))

    # Punto de intersección con la fila inferior del ROI
    y_eval = roi_h - 1
    if abs(vy) < 1e-5:
        vy = 1e-5
    x_linea = int(x0 + (y_eval - y0) * (vx / vy))
    x_linea = np.clip(x_linea, 0, roi_w - 1)

    # Dibujar línea detectada
    pt1 = (int(x0 - vx * 1000), int(y0 - vy * 1000))
    pt2 = (int(x0 + vx * 1000), int(y0 + vy * 1000))
    cv2.line(roi, pt1, pt2, (255, 0, 0), 2)
    cv2.circle(roi, (x_linea, y_eval), 6, (0, 255, 255), -1)

    # ── Zona objetivo ────────────────────────────────────────────────
    x_min = int(roi_w * ZONE_LEFT)
    x_max = int(roi_w * ZONE_RIGHT)
    cv2.line(roi, (x_min, 0), (x_min, roi_h), (255, 255, 255), 1)
    cv2.line(roi, (x_max, 0), (x_max, roi_h), (255, 255, 255), 1)

    # ── Decisión de control ─────────────────────────────────────────
    comando   = "x"
    direccion = ""

    if obstaculo_event.is_set():
        comando   = "x"
        direccion = "STOP - OBSTACULO"

    elif angulo_deg > ANGLE_CURVE_THRESHOLD:
        # Curva detectada: la dirección depende del signo de vx·vy
        # Si la línea sube hacia la derecha (pendiente positiva en imagen) → girar derecha
        if vy * vx > 0:
            comando   = "i"
            direccion = f"CURVA IZQ  ({angulo_deg:.0f}°)"
        else:
            comando   = "d"
            direccion = f"CURVA DER  ({angulo_deg:.0f}°)"

    else:
        # Línea casi recta → corregir posición con control P
        x_centro_zona = (x_min + x_max) // 2
        error_pos = x_linea - x_centro_zona          # positivo = línea a la derecha del centro
        correccion = KP_POS * error_pos + KP_ANG * angulo_deg * (1 if error_pos >= 0 else -1)

        if abs(correccion) < 0.15:
            comando   = "a"
            direccion = "RECTO"
        elif correccion > 0:
            comando   = "i"
            direccion = f"AJUSTE IZQ (err={error_pos:+d})"
        else:
            comando   = "d"
            direccion = f"AJUSTE DER (err={error_pos:+d})"

    enviar_comando(comando)

    # ── Debug visual ─────────────────────────────────────────────────
    cv2.putText(frame, f"Angulo: {angulo_deg:.1f} deg", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0),   2)
    cv2.putText(frame, direccion,                        (10, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    cv2.putText(frame, f"CMD: {comando}",                (10, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    if obstaculo_event.is_set():
        cv2.putText(frame, "!! OBSTACULO !!", (10, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 3)

    frame[roi_y:, :] = roi
    return frame


# ─────────────────────────────────────────
# GENERADOR MJPEG (FPS controlado)
# ─────────────────────────────────────────

def generar_frames():
    t_ultimo = 0.0
    while True:
        ahora = time.monotonic()
        espera = FRAME_INTERVAL - (ahora - t_ultimo)
        if espera > 0:
            time.sleep(espera)
        t_ultimo = time.monotonic()

        frame = picam2.capture_array()
        frame = mejorar_imagen(frame)
        frame = auto_brillo(frame)
        frame = reducir_saturacion(frame)
        frame = detectar_carriles(frame)

        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
        )


# ─────────────────────────────────────────
# RUTAS FLASK
# ─────────────────────────────────────────

@app.route("/")
def video():
    return Response(
        generar_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/status")
def status():
    """Endpoint simple para health-check."""
    return {
        "obstaculo": obstaculo_event.is_set(),
        "ultimo_comando": ultimo_comando,
    }


# ─────────────────────────────────────────
# SHUTDOWN LIMPIO
# ─────────────────────────────────────────

def shutdown(sig, frame_sig):
    log.info("Señal %s recibida — cerrando...", sig)
    try:
        picam2.stop()
        log.info("Cámara detenida")
    except Exception:
        pass
    if ser and ser.is_open:
        try:
            ser.write(b"x\n")   # detener motores antes de cerrar
            ser.close()
            log.info("Serial cerrado")
        except Exception:
            pass
    sys.exit(0)


signal.signal(signal.SIGINT,  shutdown)
signal.signal(signal.SIGTERM, shutdown)


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
if __name__ == "__main__":
    log.info("Iniciando servidor Flask en 0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, threaded=True)