#!/usr/bin/env python3
from picamera2 import Picamera2
import cv2
import numpy as np
import json
import time
from flask import Flask, Response

app = Flask(__name__)

# Inicializar cámara (una sola vez, fuera del bucle)
picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "RGB888"}
)
picam2.configure(config)
picam2.start()
time.sleep(1)

detector = cv2.QRCodeDetector()
ultimo_qr = ""
tiempo_ultimo = 0
cooldown = 2

def extraer_info_qr(data):
    """Parsea JSON anidado (con clave dinámica) o directo."""
    try:
        contenido = json.loads(data)
        if isinstance(contenido, list) and len(contenido) > 0:
            contenido = contenido[0]
        if isinstance(contenido, dict) and len(contenido) == 1:
            clave_externa = list(contenido.keys())[0]
            valor_interno = contenido[clave_externa]
            if isinstance(valor_interno, dict):
                contenido = valor_interno
        tipo = contenido.get("tipo de estacion", "")
        numero = contenido.get("numero de estacion", "")
        posicion = contenido.get("posicion del qr", "").lower()
        return {"tipo": tipo, "numero": numero, "posicion": posicion}
    except Exception as e:
        print(f"Error parseando: {e}")
        return None

def generar_frames():
    global ultimo_qr, tiempo_ultimo
    while True:
        # Capturar frame
        frame = picam2.capture_array()
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

        # Detectar QR
        data, bbox, _ = detector.detectAndDecode(gray)

        if data and data != "":
            ahora = time.time()
            if data != ultimo_qr or (ahora - tiempo_ultimo) > cooldown:
                ultimo_qr = data
                tiempo_ultimo = ahora
                # Mostrar en consola
                print("\n" + "="*60)
                print("📱 QR DETECTADO")
                print(f"Datos crudos: {data}")
                info = extraer_info_qr(data)
                if info:
                    print(f"   Tipo: {info['tipo']}")
                    print(f"   Número: {info['numero']}")
                    print(f"   Posición: {info['posicion']}")
                    if info['posicion'] == "entrada":
                        print("   🛑 Acción: DETENER (x)")
                    elif info['posicion'] == "salida":
                        print("   🚀 Acción: AVANZAR (a)")
                else:
                    print("   ⚠️ No se interpretó")
                print("="*60 + "\n")

        # Dibujar borde AZUL si hay QR
        if bbox is not None and len(bbox) > 0:
            pts = bbox[0].astype(int)
            for i in range(4):
                pt1 = tuple(pts[i])
                pt2 = tuple(pts[(i+1)%4])
                cv2.line(frame_bgr, pt1, pt2, (255, 0, 0), 3)  # Azul
            cv2.putText(frame_bgr, "QR detectado", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,0,0), 2)

        # Codificar a JPEG
        _, buffer = cv2.imencode('.jpg', frame_bgr)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        time.sleep(0.03)  # ~30 fps

@app.route('/')
def video():
    return Response(generar_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    print("🔍 Servidor QR iniciado")
    print("   Abre en tu navegador: http://<IP_de_la_Raspberry>:5000")
    print("   Presiona Ctrl+C para detener\n")
    try:
        app.run(host='0.0.0.0', port=5000, threaded=True)
    finally:
        picam2.stop()
        cv2.destroyAllWindows()
        print("\nCámara liberada")