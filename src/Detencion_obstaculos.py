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

# CONFIGURACIÓN DE COLOR (la tuya)
picam2.set_controls({
    "AwbEnable": False,
    "ColourGains": (1.4, 1.6),
    "AeEnable": True,
    "ExposureValue": 0.0,
    "Brightness": 0.0,
    "Contrast": 1.0,
    "Saturation": 1.0,
})

# Frame anterior para detección
frame_anterior = None

def mejorar_imagen(frame):
    r = frame[:, :, 0]
    g = frame[:, :, 1]
    b = frame[:, :, 2]
    return cv2.merge([b, g, r])

def detectar_obstaculo(frame):
    global frame_anterior

    # SOLO ZONA CENTRAL (frente del robot)
    altura, ancho, _ = frame.shape
    zona = frame[int(altura*0.4):altura, int(ancho*0.3):int(ancho*0.7)]

    gris = cv2.cvtColor(zona, cv2.COLOR_BGR2GRAY)
    gris = cv2.GaussianBlur(gris, (21, 21), 0)

    if frame_anterior is None:
        frame_anterior = gris
        return frame

    # Diferencia
    diff = cv2.absdiff(frame_anterior, gris)
    _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)

    thresh = cv2.dilate(thresh, None, iterations=2)

    contornos, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    obstaculo_detectado = False

    for c in contornos:
        if cv2.contourArea(c) < 3000:
            continue

        (x, y, w, h) = cv2.boundingRect(c)

        # Ajustar coordenadas a la imagen original
        x_global = x + int(ancho*0.3)
        y_global = y + int(altura*0.4)

        cv2.rectangle(frame, (x_global, y_global),
                      (x_global+w, y_global+h), (0, 0, 255), 2)

        obstaculo_detectado = True

    if obstaculo_detectado:
        cv2.putText(frame, "OBSTACULO", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

    # Dibujar zona de detección (opcional visual)
    cv2.rectangle(frame,
                  (int(ancho*0.3), int(altura*0.4)),
                  (int(ancho*0.7), altura),
                  (255, 0, 0), 2)

    frame_anterior = gris
    return frame


def generar_frames():
    while True:
        frame = picam2.capture_array()

        frame = mejorar_imagen(frame)

        # 🔥 AQUÍ SE AGREGA LA DETECCIÓN
        frame = detectar_obstaculo(frame)

        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')


@app.route('/')
def video():
    return Response(generar_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)