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

        except Exception:
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


# ─────────────────────────────────────────
# LÓGICA PRINCIPAL: CARRILES + DECISIÓN
# ─────────────────────────────────────────

ultimo_comando = None
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

    # =========================
    # SOLO MÁSCARA ROJA
    # =========================
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    mask_r1 = cv2.inRange(hsv, np.array([0, 100, 60]), np.array([10, 255, 255]))
    mask_r2 = cv2.inRange(hsv, np.array([165, 100, 60]), np.array([180, 255, 255]))
    mask_rojo = cv2.bitwise_or(mask_r1, mask_r2)

    kernel = np.ones((5,5), np.uint8)
    mask_rojo = cv2.morphologyEx(mask_rojo, cv2.MORPH_OPEN, kernel)
    mask_rojo = cv2.morphologyEx(mask_rojo, cv2.MORPH_CLOSE, kernel)

    # =========================
    # CONTORNOS
    # =========================
    contornos, _ = cv2.findContours(mask_rojo, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contornos:
        enviar_comando("x")
        cv2.putText(frame, "SIN LINEA", (10, 140), 0, 0.7, (0,0,255), 2)
        return frame

    # tomar el contorno más grande
    c = max(contornos, key=cv2.contourArea)

    if cv2.contourArea(c) < 300:
        enviar_comando("x")
        return frame

    cv2.drawContours(roi, [c], -1, (0,255,0), 2)

    # =========================
    # FIT LINE 🔥
    # =========================
    [vx, vy, x0, y0] = cv2.fitLine(c, cv2.DIST_L2, 0, 0.01, 0.01)

    # evitar división por cero
    if vx == 0:
        vx = 0.0001

    pendiente = vy / vx

    # punto inferior de la línea (donde "toca" el robot)
    y_eval = roi_h - 1
    if abs(vy) < 1e-5:
        vy = 1e-5

    x_linea = int(x0 + (y_eval - y0) * (vx / vy))

    # dibujar línea detectada
    pt1 = (int(x0 - vx*1000), int(y0 - vy*1000))
    pt2 = (int(x0 + vx*1000), int(y0 + vy*1000))
    cv2.line(roi, pt1, pt2, (255,0,0), 2)

    cv2.circle(roi, (x_linea, y_eval), 6, (0,255,255), -1)



    # =========================
    # CONTROL 🔥 (VERSIÓN BUENA)
    # =========================

    # 🎯 zona donde quieres la línea (lado derecho)
    x_min = int(roi_w * 0.55)
    x_max = int(roi_w * 0.75)

    cv2.line(roi, (x_min, 0), (x_min, roi_h), (255,255,255), 1)
    cv2.line(roi, (x_max, 0), (x_max, roi_h), (255,255,255), 1)

    comando = "x"
    direccion = ""

    # prioridad 1: obstáculo
    if obstaculo_cercano:
        comando = "x"
        direccion = "STOP - OBSTACULO"

    else:

        # =========================
        # 🔥 CURVAS (MANDAN)
        # =========================
        if pendiente > 0.4:
            comando = "i"   # curva hacia la izquierda → giras derecha
            direccion = "CURVA IZQ"

        elif pendiente < -0.4:
            comando = "d"   # curva hacia la derecha → giras izquierda
            direccion = "CURVA DER"

        else:
            # =========================
            # 🔥 POSICIÓN (SOLO CORRIGE)
            # =========================

            if x_linea < x_min:
                comando = "d"   # línea muy hacia el centro → te alejas
                direccion = "AJUSTE DER"

            elif x_linea > x_max:
                comando = "i"   # línea muy pegada → te separas
                direccion = "AJUSTE IZQ"

            else:
                comando = "a"   # PERFECTO → NO TOCAR
                direccion = "RECTO"

    enviar_comando(comando)

    # =========================
    # DEBUG VISUAL
    # =========================

    cv2.putText(frame, f"Pendiente: {float(pendiente):.2f}", (10, 110), 0, 0.7, (0,255,0), 2)
    cv2.putText(frame, direccion, (10, 170), 0, 0.7, (0,255,255), 2)
    cv2.putText(frame, f"CMD: {comando}", (10, 200), 0, 0.7, (255,255,0), 2)

    frame[roi_y:, :] = roi
    return frame

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