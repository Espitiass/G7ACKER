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

DEBUG = True
debug_guardado = False


def mejorar_imagen(frame):
    r = frame[:, :, 0]
    g = frame[:, :, 1]
    b = frame[:, :, 2]
    return cv2.merge([b, g, r])


def filtrar_por_angulo(lineas, angulo_min=50, angulo_max=130):
    if lineas is None:
        return []
    aceptadas = []
    for l in lineas:
        x1, y1, x2, y2 = l[0]
        angulo = np.degrees(np.arctan2(abs(y2 - y1), abs(x2 - x1) + 1e-6))
        if angulo_min <= angulo <= angulo_max:
            aceptadas.append(l)
    return aceptadas


def linea_mas_larga(lineas):
    if not lineas:
        return None
    mejor = max(lineas, key=lambda l: np.hypot(
        l[0][2] - l[0][0], l[0][3] - l[0][1]
    ))
    return tuple(mejor[0])


def extender_linea(x1, y1, x2, y2, roi_h):
    dx = x2 - x1
    dy = y2 - y1
    if abs(dy) < 1:
        return x1, y1, x2, y2
    x_top    = int(x1 + (0 - y1) * dx / dy)
    x_bottom = int(x1 + (roi_h - 1 - y1) * dx / dy)
    return x_top, 0, x_bottom, roi_h - 1


def detectar_carriles(frame):
    global debug_guardado
    altura, ancho = frame.shape[:2]

    roi_y = int(altura * 0.60)
    roi   = frame[roi_y:, :]
    roi_h, roi_w = roi.shape[:2]

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # ── Amarillo ──────────────────────────────────────────────────
    mask_y = cv2.inRange(hsv,
                         np.array([15,  80,  80]),
                         np.array([38, 255, 255]))

    # ── Negro/gris oscuro (bordes izquierdo y derecho) ────────────
    mask_negro = cv2.inRange(hsv,
                             np.array([0,   0,   0]),
                             np.array([180, 60, 90]))

    # ── Rojo (borde derecho, pegado a la línea negra) ─────────────
    mask_r1 = cv2.inRange(hsv,
                          np.array([0,   100, 60]),
                          np.array([10,  255, 255]))
    mask_r2 = cv2.inRange(hsv,
                          np.array([165, 100, 60]),
                          np.array([180, 255, 255]))
    mask_rojo = cv2.bitwise_or(mask_r1, mask_r2)

    # ── Separar por zonas horizontales ───────────────────────────
    # El carril tiene: negro-izq | amarillo-centro | negro+rojo-der
    tercio_izq = roi_w // 3
    tercio_der = (roi_w * 2) // 3

    # Borde izquierdo: negro en el tercio izquierdo
    mask_borde_izq = np.zeros_like(mask_negro)
    mask_borde_izq[:, :tercio_izq] = mask_negro[:, :tercio_izq]

    # Borde derecho: negro O rojo en el tercio derecho
    mask_borde_der_negro = np.zeros_like(mask_negro)
    mask_borde_der_negro[:, tercio_der:] = mask_negro[:, tercio_der:]

    mask_borde_der_rojo = np.zeros_like(mask_rojo)
    mask_borde_der_rojo[:, tercio_der:] = mask_rojo[:, tercio_der:]

    # Combina negro+rojo en el borde derecho para detectar mejor
    mask_borde_der = cv2.bitwise_or(mask_borde_der_negro, mask_borde_der_rojo)

    # Amarillo en el tercio central (evita falsos positivos)
    mask_amarillo_centro = np.zeros_like(mask_y)
    mask_amarillo_centro[:, tercio_izq:tercio_der] = mask_y[:, tercio_izq:tercio_der]
    # Si no hay nada en el centro, usa toda la máscara amarilla
    if cv2.countNonZero(mask_amarillo_centro) < 100:
        mask_amarillo_centro = mask_y

    # ── Morfología ────────────────────────────────────────────────
    k_open  = np.ones((3, 3),  np.uint8)
    k_close = np.ones((15, 15), np.uint8)

    def limpiar(m):
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN,  k_open)
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k_close)
        return m

    mask_amarillo_centro = limpiar(mask_amarillo_centro)
    mask_borde_izq       = limpiar(mask_borde_izq)
    mask_borde_der       = limpiar(mask_borde_der)

    # ── DEBUG ─────────────────────────────────────────────────────
    if DEBUG and not debug_guardado:
        cv2.imwrite('/tmp/roi.jpg',              roi)
        cv2.imwrite('/tmp/mask_amarillo.jpg',    mask_amarillo_centro)
        cv2.imwrite('/tmp/mask_borde_izq.jpg',   mask_borde_izq)
        cv2.imwrite('/tmp/mask_borde_der.jpg',   mask_borde_der)
        cv2.imwrite('/tmp/mask_rojo_full.jpg',   mask_rojo)
        cv2.imwrite('/tmp/mask_negro_full.jpg',  mask_negro)
        cv2.imwrite('/tmp/roi_hsv_h.jpg',        hsv[:, :, 0])
        cv2.imwrite('/tmp/roi_hsv_s.jpg',        hsv[:, :, 1])
        cv2.imwrite('/tmp/roi_hsv_v.jpg',        hsv[:, :, 2])
        debug_guardado = True
        print("[DEBUG] Máscaras guardadas en /tmp/")

    # ── Hough ─────────────────────────────────────────────────────
    def detectar(mask):
        lineas = cv2.HoughLinesP(
            mask,
            rho=1,
            theta=np.pi / 180,
            threshold=20,
            minLineLength=int(roi_h * 0.15),
            maxLineGap=60
        )
        lineas_ok = filtrar_por_angulo(lineas)
        return linea_mas_larga(lineas_ok)

    linea_y = detectar(mask_amarillo_centro)
    linea_l = detectar(mask_borde_izq)
    linea_r = detectar(mask_borde_der)

    # ── Dibujar ───────────────────────────────────────────────────
    for linea, color in [
        (linea_y, (0,   220, 255)),   # cian/amarillo
        (linea_l, (255, 60,  60)),    # azul = borde izq negro
        (linea_r, (0,   60,  220)),   # rojo = borde der negro+rojo
    ]:
        if linea is not None:
            x1, y1, x2, y2 = extender_linea(*linea, roi_h)
            cv2.line(roi, (x1, y1), (x2, y2), color, 3)

    # ── Estado en pantalla ────────────────────────────────────────
    estado_y = "OK" if linea_y else "---"
    estado_l = "OK" if linea_l else "---"
    estado_r = "OK" if linea_r else "---"

    cv2.line(frame, (0, roi_y), (ancho, roi_y), (80, 80, 80), 1)

    cv2.putText(frame, f"Amarillo:  {estado_y}",
                (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 255), 2)
    cv2.putText(frame, f"Borde izq: {estado_l}",
                (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 60, 60), 2)
    cv2.putText(frame, f"Borde der: {estado_r}",
                (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 60, 220), 2)

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
    return Response(generar_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)