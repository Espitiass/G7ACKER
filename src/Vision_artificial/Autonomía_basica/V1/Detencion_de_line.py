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
picam2.set_controls({
    "AwbEnable": False,
    "ColourGains": (1.4, 1.6),
    "AeEnable": True,
    "ExposureValue": 0.0,
    "Brightness": 0.0,
    "Contrast": 1.0,
    "Saturation": 1.0,
})

def mejorar_imagen(frame):
    r = frame[:, :, 0]
    g = frame[:, :, 1]
    b = frame[:, :, 2]
    return cv2.merge([b, g, r])

# 🔥 SOLO PUNTOS (sin líneas, sin curvas)
def dibujar_linea_puntos(roi, mask, color):
    h, w = mask.shape

    detectado = False

    # Recorre fila por fila
    for y in range(0, h, 3):  # separación entre puntos
        fila = mask[y]
        xs = np.where(fila == 255)[0]

        if len(xs) > 0:
            x = xs[len(xs)//2]  # toma el punto real del medio
            cv2.circle(roi, (x, y), 3, color, -1)
            detectado = True
            

    return detectado

def detectar_carriles(frame):
    altura, ancho = frame.shape[:2]
    roi_y = int(altura * 0.60)
    roi = frame[roi_y:, :].copy()
    roi_h, roi_w = roi.shape[:2]

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # Amarillo
    mask_y = cv2.inRange(hsv, np.array([15, 80, 80]), np.array([38, 255, 255]))
    
    # Negro
    mask_negro = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 225, 120]))

    # Rojo
    mask_r1 = cv2.inRange(hsv, np.array([0, 100, 60]), np.array([10, 255, 255]))
    mask_r2 = cv2.inRange(hsv, np.array([165, 100, 60]), np.array([180, 255, 255]))
    mask_rojo = cv2.bitwise_or(mask_r1, mask_r2)

    # División en zonas
    tercio_izq = roi_w // 3
    tercio_der = (roi_w * 2) // 3

    # Izquierda (negro)
    mask_borde_izq = np.zeros_like(mask_negro)
    mask_borde_izq[:, :tercio_izq] = mask_negro[:, :tercio_izq]

    # Derecha (negro + rojo)
    mask_borde_der_negro = np.zeros_like(mask_negro)
    mask_borde_der_negro[:, tercio_der:] = mask_negro[:, tercio_der:]
    mask_borde_der_rojo = np.zeros_like(mask_rojo)
    mask_borde_der_rojo[:, tercio_der:] = mask_rojo[:, tercio_der:]
    mask_borde_der = cv2.bitwise_or(mask_borde_der_negro, mask_borde_der_rojo)

    # Amarillo centro
    mask_amarillo_centro = np.zeros_like(mask_y)
    mask_amarillo_centro[:, tercio_izq:tercio_der] = mask_y[:, tercio_izq:tercio_der]
    if cv2.countNonZero(mask_amarillo_centro) < 100:
        mask_amarillo_centro = mask_y

    # Limpieza
    k_open = np.ones((3, 3), np.uint8)
    k_close = np.ones((5, 5), np.uint8)

    def limpiar(m):
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k_open)
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k_close)
        return m

    m_amarilla = limpiar(mask_amarillo_centro)
    m_izq = limpiar(mask_borde_izq)
    m_der = limpiar(mask_borde_der)

    # 🔥 SOLO PUNTOS
    estado_y = dibujar_linea_puntos(roi, m_amarilla, (0, 220, 255))
    estado_l = dibujar_linea_puntos(roi, m_izq, (255, 60, 60))
    estado_r = dibujar_linea_puntos(roi, m_der, (0, 60, 220))

    # Info en pantalla
    cv2.line(frame, (0, roi_y), (ancho, roi_y), (80, 80, 80), 1)
    cv2.putText(frame, f"Amarillo: {'OK' if estado_y else '---'}", (10, 25), 0, 0.6, (0, 220, 255), 2)
    cv2.putText(frame, f"Borde izq: {'OK' if estado_l else '---'}", (10, 50), 0, 0.6, (255, 60, 60), 2)
    cv2.putText(frame, f"Borde der: {'OK' if estado_r else '---'}", (10, 75), 0, 0.6, (0, 60, 220), 2)

    frame[roi_y:, :] = roi
    return frame

def generar_frames():
    while True:
        frame = picam2.capture_array()
        frame = mejorar_imagen(frame)
        frame = detectar_carriles(frame)
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/')
def video():
    return Response(generar_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)