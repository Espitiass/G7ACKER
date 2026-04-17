from flask import Flask, Response
from picamera2 import Picamera2
import cv2
import numpy as np
import serial
import time
import threading

app = Flask(__name__)

# ─────────────────────────────────────────
# SERIAL
# ─────────────────────────────────────────
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
serial_lock = threading.Lock()
time.sleep(2)

# ─────────────────────────────────────────
# ULTRASONIDO
# ─────────────────────────────────────────
from gpiozero import DistanceSensor

sensor = DistanceSensor(echo=24, trigger=23, max_distance=4)
obstaculo_cercano = False

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

        except:
            obstaculo_cercano = False

        time.sleep(0.3)

threading.Thread(target=hilo_ultrasonido, daemon=True).start()

# ─────────────────────────────────────────
# CÁMARA
# ─────────────────────────────────────────
picam2 = Picamera2()
config = picam2.create_video_configuration(
    main={"size": (1280, 720), "format": "XBGR8888"}
)
picam2.configure(config)
picam2.start()

# ─────────────────────────────────────────
# ENVÍO SERIAL OPTIMIZADO
# ─────────────────────────────────────────
ultimo_comando = None

def enviar_comando(cmd):
    global ultimo_comando
    if cmd != ultimo_comando:
        with serial_lock:
            try:
                ser.write((cmd + "\n").encode())
                ultimo_comando = cmd
            except:
                pass

# ─────────────────────────────────────────
# DETECCIÓN DE CARRILES
# ─────────────────────────────────────────
def detectar_carriles(frame):
    global obstaculo_cercano

    altura, ancho = frame.shape[:2]
    roi_y = int(altura * 0.75)
    roi = frame[roi_y:, :].copy()
    roi_h, roi_w = roi.shape[:2]

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    mask_y = cv2.inRange(hsv, np.array([15, 80, 80]), np.array([38, 255, 255]))
    mask_r1 = cv2.inRange(hsv, np.array([0, 100, 60]), np.array([10, 255, 255]))
    mask_r2 = cv2.inRange(hsv, np.array([165, 100, 60]), np.array([180, 255, 255]))
    mask_total = cv2.bitwise_or(mask_y, cv2.bitwise_or(mask_r1, mask_r2))

    kernel = np.ones((5,5), np.uint8)
    mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_OPEN, kernel)
    mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_CLOSE, kernel)

    contornos, _ = cv2.findContours(mask_total, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    centros_izq = []
    centros_der = []
    centro_imagen = roi_w // 2

    for c in contornos:
        if cv2.contourArea(c) < 300:
            continue

        M = cv2.moments(c)
        if M["m00"] == 0:
            continue

        cx = int(M["m10"] / M["m00"])

        if cx < centro_imagen:
            centros_izq.append(cx)
        else:
            centros_der.append(cx)

    if centros_izq and centros_der:
        centro_carril = (int(np.mean(centros_izq)) + int(np.mean(centros_der))) // 2
    elif centros_izq:
        centro_carril = int(np.mean(centros_izq)) + 100
    elif centros_der:
        centro_carril = int(np.mean(centros_der)) - 100
    else:
        centro_carril = None

    # ───────── DECISIÓN ─────────
    if obstaculo_cercano:
        comando = "x"

    elif centro_carril is None:
        comando = "x"

    else:
        error = centro_imagen - centro_carril

        if -80 < error < 80:
            comando = "a"

        elif 80 <= error < 200:
            comando = "l"

        elif error >= 200:
            comando = "L"

        elif -200 < error <= -80:
            comando = "r"

        elif error <= -200:
            comando = "R"

    enviar_comando(comando)

    return frame

# ─────────────────────────────────────────
# STREAM
# ─────────────────────────────────────────
def generar_frames():
    while True:
        frame = picam2.capture_array()
        frame = detectar_carriles(frame)
        _, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/')
def video():
    return Response(generar_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)