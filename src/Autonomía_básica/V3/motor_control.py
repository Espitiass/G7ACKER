#!/usr/bin/env python3
# motor_control.py - AprilTags + COOLDOWN_TAG no bloqueante + dict líneas

from flask import Flask, Response
from picamera2 import Picamera2
from pupil_apriltags import Detector
import cv2
import numpy as np
import serial
import time
import threading
from gpiozero import DistanceSensor
import multiprocessing as mp
import sys

# ==============================
# Variables globales de estado
# ==============================
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

# Variables globales de comunicación (se asignan en run_motor_control)
qr_queue = None
action_queue = None
line_status_queue = None
status_queue = None

# ==============================
# Serial
# ==============================
try:
    ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
    serial_lock = threading.Lock()
    time.sleep(2)
    print("[Motor] Puerto serie abierto")
except Exception as e:
    print(f"[Motor] Error al abrir puerto serie: {e}")
    ser = None

# Pulsos acumulados desde último reset (se actualiza desde hilo lector)
pulsos_acumulados = 0

def hilo_lector_serial():
    global pulsos_acumulados
    while True:
        try:
            if ser:
                linea = None
                with serial_lock:
                    if ser.in_waiting > 0:
                        linea = ser.readline().decode('utf-8', errors='ignore').strip()
                if linea and linea.startswith("P1:"):
                    partes = linea.split()
                    p1 = int(partes[0].split(":")[1])
                    p2 = int(partes[1].split(":")[1])
                    pulsos_acumulados = (p1 + p2) // 2
                    # Enviar pulsos directamente aunque esté en override
                    if line_status_queue is not None:
                        try:
                            line_status_queue.put({"pulsos": pulsos_acumulados}, block=False)
                        except:
                            pass
        except:
            pass
        time.sleep(0.02)

threading.Thread(target=hilo_lector_serial, daemon=True).start()

# ==============================
# Controlador PI
# ==============================
Kp = 0.12
Ki = 0.0
integral_error = 0.0
tiempo_pi = time.time()
OFFSET_DERECHA = 300  # píxeles: distancia deseada entre centro del carro y línea azul oscura
OFFSET_CENTRO = 60   # bias de dos líneas: desplaza el carro a la derecha del midpoint
SERVO_MIN = 40
SERVO_MAX = 140

# Debug
_ultimo_log_angulo = 0.0
debug_error = 0
debug_angulo = 90
debug_ambas = False

# Debounce: frames consecutivos sin línea antes de enviar stop
contador_sin_linea = 0

# ==============================
# Ultrasonido
# ==============================
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

# ==============================
# Cámara
# ==============================
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

# ==============================
# Detector AprilTag
# ==============================
detector_apriltag = Detector(families="tag36h11")
ultimo_tag_id = None
tiempo_ultimo_tag = 0
cooldown_tag = 0.5

def leer_tag(frame_bgr):
    """Detecta AprilTags en el frame completo. Devuelve (detectado, tag_id, corners)."""
    global ultimo_tag_id, tiempo_ultimo_tag

    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    resultados = detector_apriltag.detect(gray)

    if resultados:
        tag = max(resultados, key=lambda t: t.decision_margin)
        tag_id = tag.tag_id
        ahora = time.time()

        if tag_id != ultimo_tag_id or (ahora - tiempo_ultimo_tag) > cooldown_tag:
            ultimo_tag_id = tag_id
            tiempo_ultimo_tag = ahora
            return True, tag_id, tag.corners

    return False, None, None

# ==============================
# Detección de marco amarillo
# ==============================
def detectar_marco_azul(frame):
    """Detecta el marco amarillo del tag en la mitad derecha del frame."""
    h, w = frame.shape[:2]

    x_inicio = int(w * 0.5)
    roi = frame[:, x_inicio:]

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    lower = np.array([10, 120, 120])
    upper = np.array([35, 255, 255])

    mask = cv2.inRange(hsv, lower, upper)

    kernel = np.ones((5, 5), np.uint8)
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

# ==============================
# Detección de carriles
# ✅ Ahora devuelve también hay_amarilla (cian izq = línea amarilla física)
# ==============================
def detectar_carriles(frame):
    global obstaculo_cercano

    altura, ancho = frame.shape[:2]
    roi_y = int(altura * 0.75)
    roi = frame[roi_y:, :].copy()
    roi_h, roi_w = roi.shape[:2]

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    mask_azul = cv2.inRange(hsv,
                            np.array([90, 80, 50]),
                            np.array([140, 255, 255]))

    # ✅ Cian/turquesa = línea amarilla física de la pista
    mask_cian = cv2.inRange(hsv,
                            np.array([70, 50, 50]),
                            np.array([100, 255, 255]))

    mask_total = cv2.bitwise_or(mask_azul, mask_cian)

    kernel = np.ones((5, 5), np.uint8)
    mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_CLOSE, kernel)
    mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_OPEN, kernel)

    # Procesar también cian por separado para saber si la amarilla está presente
    mask_cian_clean = cv2.morphologyEx(mask_cian, cv2.MORPH_CLOSE, kernel)
    mask_cian_clean = cv2.morphologyEx(mask_cian_clean, cv2.MORPH_OPEN, kernel)

    contornos, _ = cv2.findContours(mask_total, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contornos_filtrados = [c for c in contornos if cv2.contourArea(c) > 300]

    # Contornos solo de cian (amarilla física) en el lado izquierdo
    contornos_cian, _ = cv2.findContours(mask_cian_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    centro_imagen = roi_w // 2

    centros_izq = []
    centros_der = []

    for c in contornos_filtrados:
        M = cv2.moments(c)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            if cx < centro_imagen:
                centros_izq.append(cx)
            else:
                centros_der.append(cx)

    ambas_lineas = len(centros_izq) > 0 and len(centros_der) > 0

    # ✅ hay_amarilla: hay contornos cian significativos en el lado izquierdo
    cian_izq = [c for c in contornos_cian
                if cv2.contourArea(c) > 100 and
                cv2.moments(c)["m00"] != 0 and
                int(cv2.moments(c)["m10"] / cv2.moments(c)["m00"]) < centro_imagen]
    hay_amarilla = len(cian_izq) > 0

    if centros_izq and centros_der:
        centro_carril = (int(np.mean(centros_izq)) + int(np.mean(centros_der))) // 2
    elif centros_izq:
        centro_carril = int(np.mean(centros_izq)) + 80
    elif centros_der:
        centro_carril = int(np.mean(centros_der)) - 150
    else:
        centro_carril = None

    direccion = "STOP"
    error = 0

    if obstaculo_cercano:
        direccion = "OBSTACULO"
    elif centro_carril is None:
        direccion = "SIN LINEA"
    else:
        error = centro_imagen - centro_carril
        if -100 < error < 100:
            direccion = "ADELANTE"
        elif error >= 100:
            direccion = "IZQUIERDA"
        elif error <= -100:
            direccion = "DERECHA"

    # Centro de la línea azul oscura — mayor contorno del mask azul, sin importar lado
    mask_azul_clean = cv2.morphologyEx(mask_azul, cv2.MORPH_CLOSE, kernel)
    mask_azul_clean = cv2.morphologyEx(mask_azul_clean, cv2.MORPH_OPEN, kernel)
    contornos_azul_d, _ = cv2.findContours(mask_azul_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contornos_azul_d = [c for c in contornos_azul_d if cv2.contourArea(c) > 300]
    if contornos_azul_d:
        c_mayor = max(contornos_azul_d, key=cv2.contourArea)
        M_az = cv2.moments(c_mayor)
        dark_blue_center = int(M_az["m10"] / M_az["m00"]) if M_az["m00"] != 0 else None
    else:
        dark_blue_center = None

    # Detección de curvatura: compara posición X de azul oscura en mitad sup vs inf del ROI
    curvatura = False
    if dark_blue_center is not None:
        mitad_y = roi_h // 2
        pts_sup = cv2.findNonZero(mask_azul_clean[:mitad_y, :])
        pts_inf = cv2.findNonZero(mask_azul_clean[mitad_y:, :])
        if pts_sup is not None and pts_inf is not None and len(pts_sup) > 10 and len(pts_inf) > 10:
            x_sup = float(np.mean(pts_sup[:, 0, 0]))
            x_inf = float(np.mean(pts_inf[:, 0, 0]))
            curvatura = abs(x_sup - x_inf) > 40

    # 🔍 DIAGNÓSTICO de carril
    cv2.line(roi, (centro_imagen, 0), (centro_imagen, roi_h), (255, 255, 255), 2)
    if centro_carril is not None:
        cv2.circle(roi, (centro_carril, roi_h // 2), 5, (0, 255, 0), -1)
    cv2.circle(roi, (centro_imagen, roi_h // 2), 5, (255, 255, 255), -1)

    mask_debug = cv2.cvtColor(mask_total, cv2.COLOR_GRAY2BGR)
    frame[roi_y:, :] = cv2.addWeighted(frame[roi_y:, :], 0.7, mask_debug, 0.3, 0)

    # ✅ Enviar dict en vez de bool simple
    if line_status_queue is not None:
        try:
            line_status_queue.put(
                {"ambas": ambas_lineas, "amarilla": hay_amarilla, "pulsos": pulsos_acumulados},
                block=False
            )
        except:
            pass

    return frame, direccion, centro_carril, dark_blue_center, centro_imagen, error, obstaculo_cercano, ambas_lineas, curvatura


# ==============================
# Loop principal de frames
# ==============================
def generar_frames():
    global estado, qr_guardado, tiempo_estado
    global override_activo, comando_override
    global qr_logic_activo
    global esperando_qr_logic, tiempo_espera_qr_logic
    global integral_error, tiempo_pi
    global debug_error, debug_angulo, debug_ambas
    global contador_sin_linea, pulsos_acumulados

    print("[Motor] Entrando a generar_frames()")

    while True:
        try:
            # ==============================
            # 🚨 PRIORIDAD: ULTRASONIDO
            # ==============================
            if obstaculo_cercano:
                enviar_stop()
                time.sleep(0.03)
                continue

            # ==============================
            # 🔴 1. LEER ACCIONES DE QR_LOGIC
            # ==============================
            try:
                accion = action_queue.get(block=False)

                if accion is None:
                    override_activo = False
                    comando_override = None
                    estado = "SEGUIR_LINEA"
                    qr_logic_activo = True
                    print("[Motor] Override OFF → siguiendo línea")

                elif accion == "RESET_ENCODER":
                    pulsos_acumulados = 0
                    if ser:
                        with serial_lock:
                            ser.write(b'r\n')
                    print("[Motor] Encoder reseteado")

                elif accion == "SEGUIR_BUSCANDO":
                    override_activo = False
                    comando_override = None
                    estado = "SEGUIR_LINEA"
                    qr_logic_activo = False
                    esperando_qr_logic = False
                    print("[Motor] Siguiendo línea buscando tag")

                else:
                    override_activo = True
                    comando_override = accion
                    estado = "SEGUIR_LINEA"
                    qr_logic_activo = False
                    integral_error = 0.0  # reset PI al entrar en override
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
            # 🔴 2. OVERRIDE ACTIVO
            # ==============================
            if override_activo:
                ahora_pi = time.time()
                dt = ahora_pi - tiempo_pi
                tiempo_pi = ahora_pi

                if comando_override == "CRUZANDO":
                    # PI con línea azul oscura como referencia derecha
                    resultado = detectar_carriles(frame_bgr)
                    if resultado is not None:
                        frame_proc, _, _, dark_blue_center, centro_imagen, _, _, _, _ = resultado
                        if dark_blue_center is not None:
                            error_cruzando = (centro_imagen + OFFSET_DERECHA) - dark_blue_center
                            angulo = aplicar_pi(error_cruzando, dt)
                            enviar_angulo(angulo)
                        else:
                            enviar_stop()
                    cv2.putText(frame_proc, "OVERRIDE: CRUZANDO PI", (10, 120),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                elif isinstance(comando_override, str) and comando_override.startswith("S:"):
                    # Ángulo fijo para intersecciones
                    try:
                        ang_fijo = int(comando_override.split(":")[1])
                        enviar_angulo(ang_fijo)
                    except ValueError:
                        enviar_stop()
                    cv2.putText(frame_proc, f"OVERRIDE: {comando_override}", (10, 120),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                elif comando_override == "x":
                    enviar_stop()
                    cv2.putText(frame_proc, "OVERRIDE: STOP", (10, 120),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            else:
                # ==============================
                # 🟢 SEGUIR LINEA
                # ==============================
                if estado == "SEGUIR_LINEA":
                    resultado = detectar_carriles(frame_bgr)
                    if resultado is not None:
                        frame_proc, direccion, centro_carril, dark_blue_center, centro_imagen, error, _, ambas_lineas, _ = resultado

                        ahora_pi = time.time()
                        dt = ahora_pi - tiempo_pi
                        tiempo_pi = ahora_pi

                        debug_ambas = ambas_lineas
                        if obstaculo_cercano:
                            enviar_stop()
                            integral_error = 0.0
                            contador_sin_linea = 0
                        elif ambas_lineas and centro_carril is not None:
                            # Caso 1: ambas líneas → PI sobre midpoint con bias derecha
                            debug_error = error - OFFSET_CENTRO
                            angulo = aplicar_pi(error - OFFSET_CENTRO, dt)
                            debug_angulo = angulo
                            enviar_angulo(angulo)
                            contador_sin_linea = 0
                        elif dark_blue_center is not None:
                            # Caso 2: solo línea azul oscura → PI con ref derecha + offset
                            error_azul = (centro_imagen + OFFSET_DERECHA) - dark_blue_center
                            debug_error = error_azul
                            angulo = aplicar_pi(error_azul, dt)
                            debug_angulo = angulo
                            enviar_angulo(angulo)
                            contador_sin_linea = 0
                        else:
                            contador_sin_linea += 1
                            debug_error = 0
                            debug_angulo = 90
                            if contador_sin_linea >= 5:
                                integral_error = 0.0

                    # Timeout de seguridad
                    if esperando_qr_logic and (time.time() - tiempo_espera_qr_logic) > 8.0:
                        print("[Motor] Timeout 8s → desbloqueando marcos por seguridad")
                        esperando_qr_logic = False

                    if not qr_logic_activo and not esperando_qr_logic:
                        marco_detectado, bbox_marco = detectar_marco_azul(frame_bgr)
                        if marco_detectado and bbox_marco is not None:
                            x, y, w_box, h_box = bbox_marco
                            if w_box > 210:
                                print(f"[INFO] MARCO DETECTADO (w={w_box}) → ACERCANDO")
                                estado = "ACERCARSE_TAG"
                                tiempo_estado = time.time()

                # ==============================
                # 🟡 ACERCARSE AL TAG
                # ==============================
                elif estado == "ACERCARSE_TAG":
                    marco_detectado, bbox_marco = detectar_marco_azul(frame_bgr)

                    if bbox_marco is not None:
                        x, y, w_box, h_box = bbox_marco
                        cv2.putText(frame_proc, f"W_box: {w_box}", (10, 90),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

                        if w_box < 215:
                            enviar_angulo(90)  # avanzar recto
                        else:
                            print("[INFO] DISTANCIA OK → DETENER")
                            enviar_stop()
                            estado = "DETECTAR_TAG"
                            tiempo_estado = time.time()
                    else:
                        print("[WARN] PERDÍ EL MARCO → volviendo a seguir línea")
                        estado = "SEGUIR_LINEA"

                # ==============================
                # 🔵 DETECTAR TAG (AprilTag)
                # ==============================
                elif estado == "DETECTAR_TAG":
                    enviar_stop()

                    if time.time() - tiempo_estado > 0.3:
                        marco_detectado, bbox_marco = detectar_marco_azul(frame_bgr)

                        if marco_detectado and bbox_marco is not None:
                            x, y, w_box, h_box = bbox_marco

                            tag_detectado, tag_id, corners = leer_tag(frame_bgr)

                            if tag_detectado and corners is not None:
                                pts = corners.astype(int)
                                for i in range(4):
                                    cv2.line(frame_proc,
                                             tuple(pts[i]),
                                             tuple(pts[(i + 1) % 4]),
                                             (0, 255, 0), 2)
                                cv2.putText(frame_proc, f"ID: {tag_id}",
                                            tuple(pts[0]),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

                            if tag_detectado:
                                print(f"[TAG] LEÍDO: ID={tag_id}")
                                qr_guardado = f"TAG:{tag_id}"
                                if qr_queue is not None:
                                    qr_queue.put(tag_id)
                                estado = "COOLDOWN_TAG"
                                tiempo_estado = time.time()
                                esperando_qr_logic = True
                                tiempo_espera_qr_logic = time.time()

                        else:
                            print("[WARN] Marco perdido en DETECTAR_TAG → volviendo a buscar")
                            estado = "SEGUIR_LINEA"

                # ==============================
                # ⏱️ COOLDOWN POST-LECTURA (no bloqueante)
                # ==============================
                elif estado == "COOLDOWN_TAG":
                    enviar_stop()
                    if time.time() - tiempo_estado > 1.5:
                        print("[Motor] Cooldown terminado → SEGUIR_LINEA")
                        integral_error = 0.0
                        estado = "SEGUIR_LINEA"

            # ==============================
            # OVERLAY
            # ==============================
            cv2.putText(frame_proc, f"Estado: {estado}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame_proc, f"TAG: {qr_guardado}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
            cv2.putText(frame_proc, f"W: {w_box}", (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cv2.putText(frame_proc, f"Error: {debug_error}  Ang: {debug_angulo}  Ambas: {debug_ambas}",
                        (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

            # ==============================
            # STREAM
            # ==============================
            _, buffer = cv2.imencode('.jpg', frame_proc, [cv2.IMWRITE_JPEG_QUALITY, 85])
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

            time.sleep(0.03)

        except Exception as e:
            print(f"[Motor] Error en generar_frames: {e}")
            time.sleep(0.1)


def enviar_angulo(angulo):
    global _ultimo_log_angulo, ultimo_comando
    if ser is None:
        return
    try:
        with serial_lock:
            ser.write(f"S:{angulo}\n".encode())
        ultimo_comando = None  # permite que el próximo enviar_stop() fire inmediatamente
        ahora = time.time()
        if ahora - _ultimo_log_angulo >= 0.5:
            print(f"[PI] Angulo={angulo}  Error={debug_error}  Ambas={debug_ambas}")
            _ultimo_log_angulo = ahora
    except Exception as e:
        print(f"[Motor] Error serial enviar_angulo: {e}")

def enviar_stop():
    global ultimo_comando
    if ser is None:
        return
    if ultimo_comando != "x":
        try:
            with serial_lock:
                ser.write("x\n".encode())
                print("[Motor] Enviado: x")
                ultimo_comando = "x"
        except Exception as e:
            print(f"[Motor] Error serial enviar_stop: {e}")

def aplicar_pi(error, dt):
    global integral_error
    integral_error += error * dt
    integral_error = max(-200.0, min(200.0, integral_error))  # anti-windup
    u = Kp * error + Ki * integral_error
    angulo = int(90 - u)
    return max(SERVO_MIN, min(SERVO_MAX, angulo))

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