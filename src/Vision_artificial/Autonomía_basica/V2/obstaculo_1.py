from flask import Flask, Response
from picamera2 import Picamera2
import cv2
import numpy as np
import serial
import time
import threading

app = Flask(__name__)

# ─────────────────────────────────────────
# SERIAL (único puerto compartido)
# ─────────────────────────────────────────
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
serial_lock = threading.Lock()
time.sleep(2)

# ──────────────────────────a───────────────
# ESTADO COMPARTIDO DEL ULTRASONIDO
# ─────────────────────────────────────────
obstaculo_cercano = False  # True si distancia <= 30 cm

# ─────────────────────────────────────────
# CÁMARA
# ─────────────────────────────────────────
picam2 = Picamera2()
config = picam2.create_video_configuration(
    main={"size": (1280, 720), "format": "XBGR8888"}
)
picam2.configure(config)
picam2.start()
picam2.set_controls({
    "AwbEnable": False,
    "ColourGains": (1.4, 1.6),
    "AeEnable": True,
    "ExposureValue": -0.2,
    "Brightness": 0.0,
    "Contrast": 1.2,
    "Saturation": 1.1,
})

# ─────────────────────────────────────────
# ULTRASONIDO (GPIO)
# ─────────────────────────────────────────
import RPi.GPIO as GPIO

TRIG = 23
ECHO = 24
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.output(TRIG, False)
time.sleep(1)

def medir_distancia():
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)
    inicio = time.time()
    fin = time.time()
    timeout = time.time() + 0.04  # 40 ms máximo
    while GPIO.input(ECHO) == 0:
        inicio = time.time()
        if inicio > timeout:
            return 999  # sin eco → asumir libre
    timeout = time.time() + 0.04
    while GPIO.input(ECHO) == 1:
        fin = time.time()
        if fin > timeout:
            return 999
    return (fin - inicio) * 34300 / 2

def hilo_ultrasonido():
    global obstaculo_cercano
    while True:
        try:
            distancia = medir_distancia()
            obstaculo_cercano = distancia <= 30
        except Exception:
            obstaculo_cercano = False  # en caso de error, asumir libre
        time.sleep(0.3)

threading.Thread(target=hilo_ultrasonido, daemon=True).start()

# ─────────────────────────────────────────
# PROCESAMIENTO DE IMAGEN
# ─────────────────────────────────────────
def mejorar_imagen(frame):
    r, g, b = frame[:,:,0], frame[:,:,1], frame[:,:,2]
    return cv2.merge([b, g, r])

def auto_brillo(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    error = 120 - np.mean(gray)
    return cv2.convertScaleAbs(frame, alpha=1.0 + error/200, beta=error*0.5)

def reducir_saturacion(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hsv[:,:,2] = np.clip(hsv[:,:,2], 0, 230)
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

def dibujar_linea_puntos(roi, mask, color):
    h, _ = mask.shape
    xs_detectados = []
    for y in range(0, h, 3):
        xs = np.where(mask[y] == 255)[0]
        if len(xs) > 0:
            x = xs[len(xs)//2]
            xs_detectados.append(x)
            cv2.circle(roi, (x, y), 3, color, -1)
    return int(np.mean(xs_detectados)) if xs_detectados else None

# ─────────────────────────────────────────
# LÓGICA PRINCIPAL: CARRILES + DECISIÓN
# ─────────────────────────────────────────
def enviar_comando(cmd):
    """Envía un comando por serial con protección de hilo."""
    with serial_lock:
        try:
            ser.write((cmd + "\n").encode())
        except Exception:
            pass

def detectar_carriles(frame):
    global obstaculo_cercano
    altura, ancho = frame.shape[:2]
    roi_y = int(altura * 0.75)
    roi = frame[roi_y:, :].copy()
    roi_h, roi_w = roi.shape[:2]

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    mask_y = cv2.inRange(hsv, np.array([15, 80, 80]),  np.array([38, 255, 255]))
    mask_negro = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 225, 120]))
    mask_r1 = cv2.inRange(hsv, np.array([0, 100, 60]), np.array([10, 255, 255]))
    mask_r2 = cv2.inRange(hsv, np.array([165, 100, 60]), np.array([180, 255, 255]))
    mask_rojo = cv2.bitwise_or(mask_r1, mask_r2)

    tercio_izq = roi_w // 3
    tercio_der = (roi_w * 2) // 3

    mask_borde_izq = np.zeros_like(mask_negro)
    mask_borde_izq[:, :tercio_izq] = mask_negro[:, :tercio_izq]

    mask_borde_der = np.zeros_like(mask_negro)
    mask_borde_der[:, tercio_der:] = cv2.bitwise_or(
        mask_negro[:, tercio_der:], mask_rojo[:, tercio_der:]
    )

    mask_amarillo_centro = np.zeros_like(mask_y)
    mask_amarillo_centro[:, tercio_izq:tercio_der] = mask_y[:, tercio_izq:tercio_der]
    if cv2.countNonZero(mask_amarillo_centro) < 100:
        mask_amarillo_centro = mask_y

    k_open  = np.ones((3, 3), np.uint8)
    k_close = np.ones((5, 5), np.uint8)
    def limpiar(m):
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k_open)
        return cv2.morphologyEx(m, cv2.MORPH_CLOSE, k_close)

    x_y = dibujar_linea_puntos(roi, limpiar(mask_amarillo_centro), (0, 220, 255))
    x_l = dibujar_linea_puntos(roi, limpiar(mask_borde_izq), (255, 60, 60))
    x_r = dibujar_linea_puntos(roi, limpiar(mask_borde_der), (0, 60, 220))

    centro_imagen = roi_w // 2

    if x_l is not None and x_r is not None:
        centro_carril = (x_l + x_r) // 2
    elif x_y is not None:
        centro_carril = x_y
    else:
        centro_carril = None

    # ── DECISIÓN COMBINADA ──────────────────────────────────────
    if centro_carril is not None:
        error = centro_imagen - centro_carril
        cv2.circle(roi, (centro_carril, roi_h//2), 6, (0, 255, 0), -1)
        cv2.circle(roi, (centro_imagen,  roi_h//2), 6, (255, 255, 255), -1)
        cv2.putText(frame, f"Error: {error}", (10, 110), 0, 0.7, (0, 255, 0), 2)

        en_carril = -600 < error < 600

        if en_carril and not obstaculo_cercano:
            # ✅ Centrado + sin obstáculo → ADELANTE
            comando = "a"
            direccion = "ADELANTE"
        else:
            # ❌ Fuera de carril O hay obstáculo → STOP
            comando = "x"
            direccion = "STOP - " + ("OBSTACULO" if obstaculo_cercano else "FUERA CARRIL")
    else:
        # ❌ Sin línea detectada → STOP
        comando = "x"
        direccion = "SIN LINEA"

    enviar_comando(comando)

    # Indicador de ultrasonido en pantalla
    color_obs = (0, 0, 255) if obstaculo_cercano else (0, 255, 0)
    estado_obs = "OBS: SI" if obstaculo_cercano else "OBS: NO"
    cv2.putText(frame, estado_obs,  (10, 80),  0, 0.7, color_obs, 2)
    cv2.putText(frame, direccion,   (10, 140), 0, 0.7, (0, 255, 255), 2)
    cv2.putText(frame, f"CMD: {comando}", (10, 170), 0, 0.7, (255, 255, 0), 2)
    cv2.line(frame, (0, roi_y), (ancho, roi_y), (80, 80, 80), 1)

    frame[roi_y:, :] = roi
    return frame

# ─────────────────────────────────────────
# STREAM
# ─────────────────────────────────────────
def generar_frames():
    while True:
        frame = picam2.capture_array()
        frame = mejorar_imagen(frame)
        frame = auto_brillo(frame)
        frame = reducir_saturacion(frame)
        frame = detectar_carriles(frame)
        time.sleep(0.03)
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/')
def video():
    return Response(generar_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)