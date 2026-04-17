from flask import Flask, Response
from picamera2 import Picamera2
import cv2
import numpy as np

app = Flask(__name__)

picam2 = Picamera2()
config = picam2.create_video_configuration(
    main={"size": (1280, 720), "format": "XBGR8888"}
)
picam2.configure(config)
picam2.start()

# 🔥 CONFIGURACIÓN PRO
picam2.set_controls({
    "AwbEnable": False,
    "ColourGains": (1.4, 1.6),

    "AeEnable": True,
    "ExposureValue": -0.2,

    "Brightness": 0.0,
    "Contrast": 1.2,
    "Saturation": 1.1,
})

# 🔧 CORRECCIÓN DE COLOR
def mejorar_imagen(frame):
    r = frame[:, :, 0]
    g = frame[:, :, 1]
    b = frame[:, :, 2]
    return cv2.merge([b, g, r])

# 🔥 AUTO BRILLO INTELIGENTE
def auto_brillo(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    media = np.mean(gray)

    objetivo = 120
    error = objetivo - media

    alpha = 1.0 + (error / 200)
    beta = error * 0.5

    return cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)

# 🔥 REDUCCIÓN DE ZONAS QUEMADAS
def reducir_saturacion(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hsv[:, :, 2] = np.clip(hsv[:, :, 2], 0, 230)
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

# 🔥 PUNTOS + POSICIÓN
def dibujar_linea_puntos(roi, mask, color):
    h, w = mask.shape
    xs_detectados = []

    for y in range(0, h, 3):
        fila = mask[y]
        xs = np.where(fila == 255)[0]

        if len(xs) > 0:
            x = xs[len(xs)//2]
            xs_detectados.append(x)
            cv2.circle(roi, (x, y), 3, color, -1)

    if len(xs_detectados) > 0:
        return int(np.mean(xs_detectados))
    else:
        return None

def detectar_carriles(frame):
    altura, ancho = frame.shape[:2]

    # 🔥 ROI MÁS ESTABLE
    roi_y = int(altura * 0.75)
    roi = frame[roi_y:, :].copy()
    roi_h, roi_w = roi.shape[:2]

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # 🎯 Máscaras
    mask_y = cv2.inRange(hsv, np.array([15, 80, 80]), np.array([38, 255, 255]))
    mask_negro = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 225, 120]))

    mask_r1 = cv2.inRange(hsv, np.array([0, 100, 60]), np.array([10, 255, 255]))
    mask_r2 = cv2.inRange(hsv, np.array([165, 100, 60]), np.array([180, 255, 255]))
    mask_rojo = cv2.bitwise_or(mask_r1, mask_r2)

    # 📏 División
    tercio_izq = roi_w // 3
    tercio_der = (roi_w * 2) // 3

    mask_borde_izq = np.zeros_like(mask_negro)
    mask_borde_izq[:, :tercio_izq] = mask_negro[:, :tercio_izq]

    mask_borde_der_negro = np.zeros_like(mask_negro)
    mask_borde_der_negro[:, tercio_der:] = mask_negro[:, tercio_der:]

    mask_borde_der_rojo = np.zeros_like(mask_rojo)
    mask_borde_der_rojo[:, tercio_der:] = mask_rojo[:, tercio_der:]

    mask_borde_der = cv2.bitwise_or(mask_borde_der_negro, mask_borde_der_rojo)

    mask_amarillo_centro = np.zeros_like(mask_y)
    mask_amarillo_centro[:, tercio_izq:tercio_der] = mask_y[:, tercio_izq:tercio_der]

    if cv2.countNonZero(mask_amarillo_centro) < 100:
        mask_amarillo_centro = mask_y

    # 🧼 Limpieza
    k_open = np.ones((3, 3), np.uint8)
    k_close = np.ones((5, 5), np.uint8)

    def limpiar(m):
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k_open)
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k_close)
        return m

    m_amarilla = limpiar(mask_amarillo_centro)
    m_izq = limpiar(mask_borde_izq)
    m_der = limpiar(mask_borde_der)

    # 🔥 POSICIONES
    x_y = dibujar_linea_puntos(roi, m_amarilla, (0, 220, 255))
    x_l = dibujar_linea_puntos(roi, m_izq, (255, 60, 60))
    x_r = dibujar_linea_puntos(roi, m_der, (0, 60, 220))

    # 🎯 CENTRO DINÁMICO
    centro_imagen = roi_w // 2

    if x_y is not None:
        centro_carril = x_y
    elif x_l is not None and x_r is not None:
        centro_carril = (x_l + x_r) // 2
    else:
        centro_carril = None

    # 🚗 ERROR
    if centro_carril is not None:
        error = centro_imagen - centro_carril

        cv2.circle(roi, (centro_carril, roi_h//2), 6, (0,255,0), -1)
        cv2.circle(roi, (centro_imagen, roi_h//2), 6, (255,255,255), -1)

        cv2.putText(frame, f"Error: {error}", (10, 110), 0, 0.7, (0,255,0), 2)

        if error > 20:
            direccion = "IZQUIERDA"
        elif error < -20:
            direccion = "DERECHA"
        else:
            direccion = "RECTO"

        cv2.putText(frame, direccion, (10, 140), 0, 0.7, (0,255,255), 2)

    # Info
    cv2.line(frame, (0, roi_y), (ancho, roi_y), (80, 80, 80), 1)

    cv2.putText(frame, f"Amarillo: {'OK' if x_y else '---'}", (10, 25), 0, 0.6, (0, 220, 255), 2)
    cv2.putText(frame, f"Borde izq: {'OK' if x_l else '---'}", (10, 50), 0, 0.6, (255, 60, 60), 2)
    cv2.putText(frame, f"Borde der: {'OK' if x_r else '---'}", (10, 75), 0, 0.6, (0, 60, 220), 2)

    frame[roi_y:, :] = roi
    return frame

def generar_frames():
    while True:
        frame = picam2.capture_array()
        frame = mejorar_imagen(frame)

        # 🔥 PROCESAMIENTO PRO
        frame = auto_brillo(frame)
        frame = reducir_saturacion(frame)

        frame = detectar_carriles(frame)

        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/')
def video():
    return Response(generar_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)