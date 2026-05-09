#MOTOR CONTROL
#!/usr/bin/env python3
# motor_control.py - Con logs y sin recargador automático

from flask import Flask, Response
from picamera2 import Picamera2
import cv2
import numpy as np
import serial
import time
import threading
from gpiozero import DistanceSensor
import multiprocessing as mp
import sys

# Variables globales
qr_logic_activo = False
esperando_qr_logic = False
tiempo_espera_qr_logic = 0

ultimo_comando = None
override_activo = False
comando_override = None

estado = "SEGUIR_LINEA"
qr_guardado = None
tiempo_estado = 0

app = Flask(__name__)

# Variables globales de comunicación
qr_queue = None
action_queue = None
line_status_queue = None
status_queue = None

# Estado del robot (para mostrar)
estado_robot = {
    "estado": "INICIANDO",
    "num_estacion": "---",
    "carril": "---",
    "direccion": "---",
    "ambas_lineas": False,
    "qr_visible": False,
    "fin_carrera": False
}

# --- Serial ---
try:
    ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
    serial_lock = threading.Lock()
    time.sleep(2)
    print("[Motor] Puerto serie abierto")
except Exception as e:
    print(f"[Motor] Error al abrir puerto serie: {e}")
    ser = None

# --- Ultrasonido ---
obstaculo_cercano = False
try:
    sensor = DistanceSensor(echo=24, trigger=23, max_distance=4)
    print("[Motor] Sensor ultrasonido inicializado")
except Exception as e:
    print(f"[Motor] Error ultrasonido: {e}")
    sensor = None

def hilo_ultrasonido():
    global obstaculo_cercano
    while True:
        try:
            if sensor:
                distancias = []
                for _ in range(3):
                    d = sensor.distance * 100
                    if 2 < d < 400:
                        distancias.append(d)
                    time.sleep(0.05)
                if distancias:
                    distancia = sum(distancias) / len(distancias)
                    obstaculo_cercano = distancia <= 20
                else:
                    obstaculo_cercano = False
            else:
                obstaculo_cercano = False
        except Exception as e:
            print(f"[Ultrasonido] Error: {e}")
            obstaculo_cercano = False
        time.sleep(0.3)

threading.Thread(target=hilo_ultrasonido, daemon=True).start()

# --- Cámara ---
try:
    picam2 = Picamera2()
    config = picam2.create_video_configuration(main={"size": (1280, 720), "format": "XBGR8888"})
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
    print("[Motor] Cámara inicializada")
except Exception as e:
    print(f"[Motor] Error cámara: {e}")
    sys.exit(1)

# --- Detector QR ---
detector_qr = cv2.QRCodeDetector()
ultimo_qr = ""
tiempo_ultimo_qr = 0
cooldown_qr = 0.5

def leer_qr(frame_bgr):
    global ultimo_qr, tiempo_ultimo_qr

    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

    variantes = [
        gray,
        cv2.equalizeHist(gray),
        cv2.adaptiveThreshold(gray, 255,
                              cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                              cv2.THRESH_BINARY, 11, 2)
    ]

    for img in variantes:
        data, bbox, _ = detector_qr.detectAndDecode(img)

        if data and data != "":
            ahora = time.time()

            if data != ultimo_qr or (ahora - tiempo_ultimo_qr) > cooldown_qr:
                ultimo_qr = data
                tiempo_ultimo_qr = ahora
                return True, data, bbox

    return False, None, None

def detectar_marco_azul(frame):
    h, w = frame.shape[:2]

    x_inicio = int(w * 0.5)
    roi = frame[:, x_inicio:]

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    lower = np.array([10, 120, 120])
    upper = np.array([35, 255, 255])

    mask = cv2.inRange(hsv, lower, upper)

    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    contornos, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for c in contornos:
        area = cv2.contourArea(c)

        if area > 2000:
            x, y, wc, hc = cv2.boundingRect(c)
            ratio = wc / float(hc)

            if 0.7 < ratio < 1.3:
                x_global = x + x_inicio
                return True, (x_global, y, wc, hc)

    return False, None

def mejorar_imagen(frame):
    return frame

def auto_brillo(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5,5), 0)
    error = 120 - np.mean(gray)
    return cv2.convertScaleAbs(frame, alpha=1.0+error/200, beta=error*0.5)

def reducir_saturacion(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hsv[:,:,2] = np.clip(hsv[:,:,2], 0, 230)
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

def detectar_carriles(frame):
    global obstaculo_cercano

    altura, ancho = frame.shape[:2]
    roi_y = int(altura * 0.7)
    roi = frame[roi_y:, :].copy()
    roi_h, roi_w = roi.shape[:2]

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    mask_azul = cv2.inRange(hsv,
                            np.array([90, 80, 50]),
                            np.array([140, 255, 255]))

    mask_cian = cv2.inRange(hsv,
                            np.array([70, 50, 50]),
                            np.array([100, 255, 255]))

    mask_total = cv2.bitwise_or(mask_azul, mask_cian)

    kernel = np.ones((5,5), np.uint8)
    mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_CLOSE, kernel)
    mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_OPEN, kernel)

    contornos, _ = cv2.findContours(mask_total, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    contornos_filtrados = [c for c in contornos if cv2.contourArea(c) > 100]
    print("Contornos:", len(contornos_filtrados))

    centros_izq = []
    centros_der = []
    centro_imagen = roi_w // 2

    for c in contornos_filtrados:
        M = cv2.moments(c)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            if cx < centro_imagen:
                centros_izq.append(cx)
            else:
                centros_der.append(cx)

    ambas_lineas = len(centros_izq) > 0 and len(centros_der) > 0

    if centros_izq and centros_der:
        centro_carril = (int(np.mean(centros_izq)) + int(np.mean(centros_der))) // 2
    elif centros_izq:
        centro_carril = int(np.mean(centros_izq)) + 50
    elif centros_der:
        centro_carril = int(np.mean(centros_der)) - 50
    else:
        centro_carril = None

    comando = "x"
    direccion = "STOP"
    error = 0

    if obstaculo_cercano:
        direccion = "OBSTACULO"
    elif centro_carril is None:
        direccion = "SIN LINEA"
    else:
        error = centro_imagen - centro_carril
        if -90 < error < 90:
            comando = "a"
            direccion = "ADELANTE"
        elif error >= 90:
            comando = "d"
            direccion = "IZQUIERDA"
        elif error <= -90:
            comando = "i"
            direccion = "DERECHA"

    enviar_comando(comando)

    cv2.line(roi, (centro_imagen, 0), (centro_imagen, roi_h), (255,255,255), 2)

    if centro_carril is not None:
        cv2.circle(roi, (centro_carril, roi_h//2), 5, (0,255,0), -1)

    cv2.circle(roi, (centro_imagen, roi_h//2), 5, (255,255,255), -1)

    mask_debug = cv2.cvtColor(mask_total, cv2.COLOR_GRAY2BGR)
    frame[roi_y:, :] = cv2.addWeighted(frame[roi_y:, :], 0.7, mask_debug, 0.3, 0)

    if line_status_queue is not None:
        try:
            line_status_queue.put(ambas_lineas, block=False)
        except:
            pass

    return frame, direccion, comando, centro_carril, centro_imagen, error, obstaculo_cercano, ambas_lineas


def generar_frames():
    global estado, qr_guardado, tiempo_estado
    global override_activo, comando_override
    global qr_logic_activo
    global ultimo_qr, tiempo_ultimo_qr
    global esperando_qr_logic, tiempo_espera_qr_logic

    print("[Motor] Entrando a generar_frames()")

    while True:
        try:
            # ==============================
            # 🚨 PRIORIDAD: ULTRASONIDO
            # ==============================
            if obstaculo_cercano:
                enviar_comando("x")
                time.sleep(0.03)
                continue

            # ==============================
            # 🔴 1. LEER ACCIONES QR_LOGIC
            # ==============================
            try:
                accion = action_queue.get(block=False)

                if accion is None:
                    override_activo = False
                    comando_override = None
                    estado = "SEGUIR_LINEA"
                    qr_logic_activo = True
                    ultimo_qr = ""
                    tiempo_ultimo_qr = 0
                    print("[Motor] Override OFF → siguiendo línea")

                elif accion == "SEGUIR_BUSCANDO":
                    override_activo = False
                    comando_override = None
                    estado = "SEGUIR_LINEA"
                    qr_logic_activo = False
                    esperando_qr_logic = False  # ← desbloquear marcos
                    ultimo_qr = ""
                    tiempo_ultimo_qr = 0
                    print("[Motor] Siguiendo línea buscando QR")

                else:
                    override_activo = True
                    comando_override = accion
                    estado = "SEGUIR_LINEA"
                    qr_logic_activo = False
                    print(f"[Motor] Override ON → {accion}")

            except:
                pass

            # ==============================
            # 📷 CAPTURA FRAME
            # ==============================
            frame = picam2.capture_array()

            if frame is None:
                continue

            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            frame_proc = frame_bgr.copy()

            w_box = 0

            # ==============================
            # 🔴 2. OVERRIDE
            # ==============================
            if override_activo:
                enviar_comando(comando_override)

                cv2.putText(frame_proc, f"OVERRIDE: {comando_override}", (10, 120),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)

            else:
                marco_detectado, bbox_marco = detectar_marco_azul(frame_bgr)

                # ==============================
                # 🟢 SEGUIR LINEA
                # ==============================
                if estado == "SEGUIR_LINEA":
                    resultado = detectar_carriles(frame_bgr)
                    if resultado is not None:
                        frame_proc, direccion, comando, centro_carril, centro_imagen, error, obstaculo, ambas_lineas = resultado

                    # Desbloquear marcos por timeout de seguridad (3s)
                    if esperando_qr_logic and (time.time() - tiempo_espera_qr_logic) > 3.0:
                        print("[Motor] Timeout esperando qr_logic → desbloqueando marcos")
                        esperando_qr_logic = False

                    if not qr_logic_activo and not esperando_qr_logic:
                        marco_detectado, bbox_marco = detectar_marco_azul(frame_bgr)
                        if marco_detectado and bbox_marco is not None:
                            x, y, w_box, h_box = bbox_marco
                            if w_box > 180:
                                print("[INFO] MARCO GRANDE → ACERCANDO")
                                estado = "ACERCARSE_QR"
                                tiempo_estado = time.time()

                # ==============================
                # 🟡 ACERCARSE
                # ==============================
                elif estado == "ACERCARSE_QR":
                    marco_detectado, bbox_marco = detectar_marco_azul(frame_bgr)

                    if bbox_marco is not None:
                        x, y, w_box, h_box = bbox_marco

                        cv2.putText(frame_proc, f"W_box: {w_box}", (10, 90),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)

                        if w_box < 180:
                            enviar_comando("a")

                        elif w_box >= 180:
                            print("[INFO] DISTANCIA → DETENER")
                            enviar_comando("a")
                            time.sleep(0.2)
                            enviar_comando("x")
                            estado = "DETECTAR_QR"
                            tiempo_estado = time.time()

                    else:
                        print("[WARN] PERDÍ EL MARCO")
                        estado = "SEGUIR_LINEA"

                # ==============================
                # 🔵 DETECTAR QR
                # ==============================
                elif estado == "DETECTAR_QR":

                    enviar_comando("x")

                    if time.time() - tiempo_estado > 0.3:

                        if bbox_marco is not None:
                            x, y, w_box, h_box = bbox_marco

                            roi_qr = frame_bgr[y:y+h_box, x:x+w_box]
                            roi_qr = cv2.resize(roi_qr, None, fx=3, fy=3)

                            qr_detectado, qr_data, bbox = leer_qr(roi_qr)

                            cv2.rectangle(frame_proc, (x, y), (x+w_box, y+h_box), (0,255,255), 2)

                            if qr_detectado:
                                print(f"[QR] LEÍDO: {qr_data}")
                                qr_guardado = qr_data
                                if qr_queue is not None:
                                    qr_queue.put(qr_data)
                                time.sleep(1.5)
                                estado = "SEGUIR_LINEA"
                                esperando_qr_logic = True          # ← bloquear marcos
                                tiempo_espera_qr_logic = time.time()  # ← timestamp

            # ==============================
            # OVERLAY
            # ==============================
            cv2.putText(frame_proc, f"Estado: {estado}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

            cv2.putText(frame_proc, f"QR: {qr_guardado}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,0), 2)

            cv2.putText(frame_proc, f"W: {w_box}", (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2)

            # ==============================
            # STREAM
            # ==============================
            print("Frame OK")
            _, buffer = cv2.imencode('.jpg', frame_proc, [cv2.IMWRITE_JPEG_QUALITY, 85])

            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

            time.sleep(0.03)

        except Exception as e:
            print(f"[Motor] Error en generar_frames: {e}")
            time.sleep(0.1)

def enviar_comando(cmd):
    global ultimo_comando

    if ser is None:
        return

    if cmd != ultimo_comando:
        try:
            with serial_lock:
                ser.write((cmd + "\n").encode())
                print(f"[Motor] Enviado: {cmd}")
                ultimo_comando = cmd
        except Exception as e:
            print(f"[Motor] Error serial: {e}")

@app.route('/')
def video():
    return Response(
        generar_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

def run_motor_control(qr_q, action_q, line_q, status_q):
    global qr_queue, action_queue, line_status_queue, status_queue
    qr_queue = qr_q
    action_queue = action_q
    line_status_queue = line_q
    status_queue = status_q
    print("[Motor] Iniciando servidor Flask en puerto 5000...")
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=False, use_reloader=False)

if __name__ == '__main__':
    qr_q = mp.Queue()
    action_q = mp.Queue()
    line_q = mp.Queue()
    status_q = mp.Queue()

    run_motor_control(qr_q, action_q, line_q, status_q)