#!/usr/bin/env python3
"""
debug_tags.py — Depuración de AprilTags con Flask
Raspberry Pi 5 + Picamera2
Accede desde el navegador: http://<IP_DE_LA_PI>:5000
"""

from flask import Flask, Response, render_template_string
from picamera2 import Picamera2
from pupil_apriltags import Detector
import cv2
import numpy as np
import threading
import time

# ─────────────────────────────────────────────
# MAPA DE TAGS
# ─────────────────────────────────────────────
MAPA_TAGS = {
    1: {
        "tipo": "carga",
        "numero": 1,
    },
    2: {
        "tipo": "descarga",
        "numero": 1,
        "carril": "carril 2"
    },
    3: {
        "tipo": "descarga",
        "numero": 2,
        "carril": "carril 3"
    },
    4: {
        "tipo": "descarga",
        "numero": 3,
        "carril": "carril 3"
    },
    5: {
        "carril 2": "izquierda",
        "carril 3": "avanzar"
    },
    6: {
        "tipo": "descarga",
        "numero": 1,
        "posicion": "entrada"
    },
    7: {
        "tipo": "descarga",
        "numero": 2,
        "posicion": "entrada"
    },
    8: {
        "tipo": "descarga",
        "numero": 3,
        "posicion": "entrada"
    },
    9: {
        "carril 1": "izquierda",
        "carril 3": "derecha"
    },
    10: {
        "carril 1": "avanzar",
        "carril 2": "izquierda"
    },
}

# ─────────────────────────────────────────────
# COLORES POR TIPO (BGR para OpenCV)
# ─────────────────────────────────────────────
COLOR_TIPO = {
    "carga":       (0, 200, 80),    # verde
    "descarga":    (0, 140, 255),   # naranja
    "interseccion":(255, 200, 0),   # azul claro
    "desconocido": (80, 80, 255),   # rojo
}

def interpretar_tag(tag_id):
    """Retorna (descripcion_corta, tipo, datos) para un tag_id."""
    if tag_id not in MAPA_TAGS:
        return f"ID {tag_id} — no está en MAPA_TAGS", "desconocido", {}

    info = MAPA_TAGS[tag_id]
    tipo = info.get("tipo", "interseccion")

    if tipo == "carga":
        desc = f"CARGA #{info.get('numero', '?')}"
    elif tipo == "descarga":
        partes = [f"DESCARGA #{info.get('numero', '?')}"]
        if "carril" in info:
            partes.append(f"carril={info['carril']}")
        if "posicion" in info:
            partes.append(f"pos={info['posicion']}")
        desc = "  ".join(partes)
    else:
        # Tags sin "tipo" → intersección / fin de carril
        tipo = "interseccion"
        opciones = "  |  ".join(f"{k}: {v}" for k, v in info.items())
        desc = f"INTERSEC  {opciones}"

    return desc, tipo, info


# ─────────────────────────────────────────────
# ESTADO COMPARTIDO
# ─────────────────────────────────────────────
class Estado:
    def __init__(self):
        self.lock = threading.Lock()
        self.frame_jpeg = None          # último frame JPEG para stream
        self.ultimo_tag = None          # dict con info del último tag visto
        self.historial = []             # lista de dicts (max 20)
        self.fps = 0.0

estado = Estado()

# ─────────────────────────────────────────────
# CÁMARA + DETECTOR (hilo aparte)
# ─────────────────────────────────────────────
def hilo_camara():
    # Inicializar cámara
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
    print("[Cámara] Iniciada")

    # Inicializar detector AprilTag
    detector = Detector(
        families="tag36h11",
        nthreads=3,          # Pi 5 tiene 4 cores, dejamos 1 libre
        quad_decimate=2.0,   # buen balance velocidad/precisión
        quad_sigma=0.0,
        refine_edges=1,
        decode_sharpening=0.25,
    )
    print("[Detector] Listo")

    t_prev = time.time()
    frame_count = 0

    while True:
        # Capturar frame
        frame_bgr = picam2.capture_array("main")
        frame_bgr = cv2.cvtColor(frame_bgr, cv2.COLOR_BGRA2BGR)
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

        # Detectar tags
        tags = detector.detect(gray)

        for tag in tags:
            if tag.decision_margin < 40:   # ignorar detecciones flojas
                continue

            tag_id = tag.tag_id
            desc, tipo, datos = interpretar_tag(tag_id)
            color = COLOR_TIPO[tipo]

            # Dibujar contorno del tag
            corners = tag.corners.astype(int)
            cv2.polylines(frame_bgr, [corners], True, color, 2)

            # Dibujar esquinas
            for c in corners:
                cv2.circle(frame_bgr, tuple(c), 5, color, -1)

            # Centro y etiqueta
            cx, cy = int(tag.center[0]), int(tag.center[1])
            cv2.circle(frame_bgr, (cx, cy), 4, (255, 255, 255), -1)

            # Fondo semitransparente para el texto
            texto_id   = f"TAG {tag_id}"
            texto_desc = desc[:50]  # truncar si muy largo
            texto_conf = f"conf={tag.decision_margin:.0f}  hamming={tag.hamming}"

            for i, linea in enumerate([texto_id, texto_desc, texto_conf]):
                y_txt = cy - 50 + i * 22
                # sombra
                cv2.putText(frame_bgr, linea, (cx - 59, y_txt + 1),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)
                # texto
                cv2.putText(frame_bgr, linea, (cx - 60, y_txt),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

            # Actualizar estado compartido
            entrada = {
                "tag_id": tag_id,
                "desc": desc,
                "tipo": tipo,
                "datos": datos,
                "confianza": round(float(tag.decision_margin), 1),
                "hamming": int(tag.hamming),
                "hora": time.strftime("%H:%M:%S"),
            }
            with estado.lock:
                estado.ultimo_tag = entrada
                estado.historial.insert(0, entrada)
                if len(estado.historial) > 20:
                    estado.historial.pop()

        # FPS
        frame_count += 1
        now = time.time()
        if now - t_prev >= 1.0:
            with estado.lock:
                estado.fps = round(frame_count / (now - t_prev), 1)
            frame_count = 0
            t_prev = now

        # Overlay FPS + cantidad de tags
        cv2.putText(frame_bgr, f"FPS: {estado.fps}  Tags: {len(tags)}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)

        # Codificar a JPEG y guardar en estado
        ok, buf = cv2.imencode(".jpg", frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if ok:
            with estado.lock:
                estado.frame_jpeg = buf.tobytes()


# ─────────────────────────────────────────────
# FLASK
# ─────────────────────────────────────────────
app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Debug AprilTags</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0d0d0d; color: #e0e0e0; font-family: 'Courier New', monospace; }
  header { background: #111; border-bottom: 1px solid #222; padding: 12px 20px;
           display: flex; align-items: center; gap: 16px; }
  header h1 { font-size: 16px; color: #aaa; font-weight: normal; letter-spacing: 2px; text-transform: uppercase; }
  .dot { width: 10px; height: 10px; border-radius: 50%; background: #0f0; animation: blink 1s infinite; }
  @keyframes blink { 50% { opacity: .3; } }
  .layout { display: grid; grid-template-columns: 1fr 340px; height: calc(100vh - 48px); }
  .video-wrap { display: flex; align-items: center; justify-content: center; background: #080808; }
  .video-wrap img { max-width: 100%; max-height: 100%; border: 1px solid #1a1a1a; }
  .panel { background: #111; border-left: 1px solid #1e1e1e; display: flex; flex-direction: column; overflow: hidden; }
  .panel-section { padding: 14px 16px; border-bottom: 1px solid #1e1e1e; }
  .label { font-size: 10px; color: #555; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 8px; }
  .tag-id { font-size: 36px; font-weight: bold; color: #fff; line-height: 1; }
  .tag-tipo { display: inline-block; margin-top: 6px; padding: 3px 10px; border-radius: 3px;
              font-size: 11px; letter-spacing: 1px; text-transform: uppercase; }
  .tipo-carga       { background: #0a3320; color: #00c853; border: 1px solid #00c853; }
  .tipo-descarga    { background: #2a1800; color: #ff9100; border: 1px solid #ff9100; }
  .tipo-interseccion{ background: #001a2a; color: #00bcd4; border: 1px solid #00bcd4; }
  .tipo-desconocido { background: #1a0000; color: #f44336; border: 1px solid #f44336; }
  .tag-desc { font-size: 13px; color: #aaa; margin-top: 8px; line-height: 1.5; }
  .datos-grid { display: grid; grid-template-columns: auto 1fr; gap: 4px 12px; font-size: 12px; margin-top: 8px; }
  .dk { color: #555; }
  .dv { color: #ccc; }
  .historial { flex: 1; overflow-y: auto; padding: 10px 0; }
  .hist-item { padding: 8px 16px; border-bottom: 1px solid #181818; cursor: default;
               display: flex; justify-content: space-between; align-items: center;
               transition: background .15s; }
  .hist-item:hover { background: #161616; }
  .hist-id { font-size: 18px; font-weight: bold; }
  .hist-meta { font-size: 11px; color: #555; text-align: right; }
  .empty { color: #333; font-size: 13px; padding: 20px 16px; }
  @media (max-width: 700px) {
    .layout { grid-template-columns: 1fr; grid-template-rows: 60vw 1fr; }
    .panel { border-left: none; border-top: 1px solid #1e1e1e; }
  }
</style>
</head>
<body>
<header>
  <div class="dot"></div>
  <h1>AprilTag Debug — Raspberry Pi 5</h1>
</header>
<div class="layout">
  <div class="video-wrap">
    <img src="/video" alt="stream">
  </div>
  <div class="panel">
    <div class="panel-section" id="ultimo">
      <div class="label">Último tag detectado</div>
      <div class="empty">Esperando detección…</div>
    </div>
    <div class="panel-section">
      <div class="label">Historial</div>
    </div>
    <div class="historial" id="historial">
      <div class="empty">Sin detecciones aún.</div>
    </div>
  </div>
</div>

<script>
const COLORES = {
  carga: '#00c853', descarga: '#ff9100',
  interseccion: '#00bcd4', desconocido: '#f44336'
};

async function poll() {
  try {
    const r = await fetch('/estado');
    const d = await r.json();

    // Panel último tag
    const el = document.getElementById('ultimo');
    if (d.ultimo) {
      const u = d.ultimo;
      const c = COLORES[u.tipo] || '#aaa';
      const datosHtml = Object.entries(u.datos)
        .map(([k,v]) => `<span class="dk">${k}</span><span class="dv">${JSON.stringify(v)}</span>`)
        .join('');
      el.innerHTML = `
        <div class="label">Último tag detectado</div>
        <div class="tag-id" style="color:${c}">TAG ${u.tag_id}</div>
        <span class="tag-tipo tipo-${u.tipo}">${u.tipo}</span>
        <div class="tag-desc">${u.desc}</div>
        <div class="datos-grid">${datosHtml}</div>
        <div style="margin-top:10px;font-size:11px;color:#444">
          conf=${u.confianza} &nbsp; hamming=${u.hamming} &nbsp; ${u.hora}
        </div>`;
    }

    // Historial
    const hist = document.getElementById('historial');
    if (d.historial.length === 0) {
      hist.innerHTML = '<div class="empty">Sin detecciones aún.</div>';
    } else {
      hist.innerHTML = d.historial.map(h => {
        const c = COLORES[h.tipo] || '#aaa';
        return `<div class="hist-item">
          <span class="hist-id" style="color:${c}">TAG ${h.tag_id}</span>
          <div class="hist-meta">
            <div>${h.tipo}</div>
            <div>${h.hora}</div>
            <div>conf=${h.confianza}</div>
          </div>
        </div>`;
      }).join('');
    }
  } catch(e) { /* red ocupada */ }
  setTimeout(poll, 400);
}
poll();
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/video")
def video():
    def generar():
        while True:
            with estado.lock:
                frame = estado.frame_jpeg
            if frame:
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
            time.sleep(0.03)
    return Response(generar(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/estado")
def api_estado():
    import json
    with estado.lock:
        data = {
            "ultimo": estado.ultimo_tag,
            "historial": estado.historial[:20],
            "fps": estado.fps,
        }
    return app.response_class(
        response=json.dumps(data, ensure_ascii=False),
        mimetype="application/json"
    )

# ─────────────────────────────────────────────
# ARRANQUE
# ─────────────────────────────────────────────
if __name__ == "__main__":
    t = threading.Thread(target=hilo_camara, daemon=True)
    t.start()
    print("[Flask] Servidor en http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, threaded=True)