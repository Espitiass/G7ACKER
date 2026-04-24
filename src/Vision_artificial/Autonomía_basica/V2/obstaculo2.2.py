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

# ─────────────────────────────────────────
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
from gpiozero import DistanceSensor

sensor = DistanceSensor(echo=24, trigger=23, max_distance=4)

def hilo_ultrasonido():
    global obstaculo_cercano
    while True:
        try:
            distancias = []
            for _ in range(3):
                d = sensor.distance * 100
                if 2 < d < 400:
                    distancias.append(d)
                time.sleep(0.05)

            if distancias:
                distancia = sum(distancias) / len(distancias)
                obstaculo_cercano = distancia <= 30
            else:
                obstaculo_cercano = False

        except Exception as e:
            print("Error ultrasonido:", e)
            obstaculo_cercano = False

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

ultimo_comando = None
ultimo_comando_valido = "x"
frames_sin_ambas_lineas = 0
MAX_FRAMES_SIN_LINEAS = 10  # ajustable (clave)
def enviar_comando(cmd):
    global ultimo_comando
    if cmd != ultimo_comando:
        with serial_lock:
            try:
                ser.write((cmd + "\n").encode())
                ultimo_comando = cmd
            except Exception:
                pass

def detectar_carriles(frame):
    global obstaculo_cercano
    altura, ancho = frame.shape[:2]
    roi_y = int(altura * 0.7)
    roi = frame[roi_y:, :].copy()
    roi_h, roi_w = roi.shape[:2]

    # ─────────────────────────────────────────
    # MÁSCARAS SOLO AMARILLO + ROJO
    # ─────────────────────────────────────────
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)  

    # Amarillo
    mask_y = cv2.inRange(hsv, np.array([15, 80, 80]), np.array([38, 255, 255]))

    # Rojo (dos rangos en HSV)
    mask_r1 = cv2.inRange(hsv, np.array([0, 100, 60]), np.array([10, 255, 255]))
    mask_r2 = cv2.inRange(hsv, np.array([165, 100, 60]), np.array([180, 255, 255]))
    mask_rojo = cv2.bitwise_or(mask_r1, mask_r2)

    # Combinar máscaras
    mask_total = cv2.bitwise_or(mask_y, mask_rojo)

    # Limpieza
    kernel = np.ones((5,5), np.uint8)
    mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_OPEN, kernel)
    mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_CLOSE, kernel)

    # ─────────────────────────────────────────
    # CONTORNOS
    # ─────────────────────────────────────────
    contornos, _ = cv2.findContours(mask_total, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contornos_filtrados = [c for c in contornos if cv2.contourArea(c) > 300]

    # Filtrar contornos grandes
    centros_izq = []
    centros_der = []

    centro_imagen = roi_w // 2  # importante que esté antes

    for c in contornos_filtrados:
        cv2.drawContours(roi, [c], -1, (0, 255, 0), 2)

        M = cv2.moments(c)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])

            # Separar izquierda / derecha
            if cx < centro_imagen:
                centros_izq.append(cx)
                color = (255, 0, 0)  # azul
            else:
                centros_der.append(cx)
                color = (0, 0, 255)  # rojo

            cv2.circle(roi, (cx, cy), 5, color, -1)

    # ─────────────────────────────────────────
    # CENTRO DEL CARRIL (DINÁMICO)
    # ─────────────────────────────────────────
    if centros_izq and centros_der:
        frames_sin_ambas_lineas = 0
        centro_carril = (int(np.mean(centros_izq)) + int(np.mean(centros_der))) // 2


    elif centros_izq or centros_der:
        frames_sin_ambas_lineas += 1

        if frames_sin_ambas_lineas < MAX_FRAMES_SIN_LINEAS:
            centro_carril = None  # 🔥 NO recalculas todavía
        else:
            # ya pasó suficiente tiempo → ahora sí usa una línea
            if centros_izq:
                centro_carril = int(np.mean(centros_izq)) + 100
            else:
                centro_carril = int(np.mean(centros_der)) - 100

    else:
        frames_sin_ambas_lineas += 1
        centro_carril = None

    # ─────────────────────────────────────────
    # VISUALIZACIÓN
    # ─────────────────────────────────────────

    # Línea fija (referencia)
    cv2.line(roi, (centro_imagen, 0), (centro_imagen, roi_h), (255, 255, 255), 2)

    # Línea del carril detectado
    if centro_carril is not None:
        cv2.line(roi, (centro_carril, 0), (centro_carril, roi_h), (0, 255, 0), 2)

    comando = "x"
    direccion = "DEFAULT STOP"

    # ── DECISIÓN COMBINADA ──────────────────────────────────────
    if obstaculo_cercano:
        comando = "x"
        direccion = "STOP - OBSTACULO"

    elif centro_carril is None:
        comando = ultimo_comando_valido  # 🔥 mantiene movimiento
        direccion = "MEMORIA"

    else:
        error = centro_imagen - centro_carril

        cv2.circle(roi, (centro_carril, roi_h//2), 6, (0, 255, 0), -1)
        cv2.circle(roi, (centro_imagen,  roi_h//2), 6, (255, 255, 255), -1)
        cv2.putText(frame, f"Error: {error}", (10, 110), 0, 0.7, (0, 255, 0), 2)

        if -110 < error < 110:
            comando = "a"
            direccion = "ADELANTE"

        elif error >= 110:
            comando = "d"
            direccion = "DERECHA"

        elif error <= -100:
            comando = "i"
            direccion = "IZQUIERDA"
            
        ultimo_comando_valido = comando

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