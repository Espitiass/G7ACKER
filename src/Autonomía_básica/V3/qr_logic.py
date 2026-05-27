#!/usr/bin/env python3
# qr_logic.py - Adaptado a detección por ID de AprilTag (MAPA_TAGS)

import time
import multiprocessing as mp
from gpiozero import Button
import lgpio

# ==============================
# 🗺️ MAPA DE TAGS
# ==============================
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


class QRLogic:
    def __init__(self, qr_queue, action_queue, line_status_queue, status_queue):
        self.qr_queue = qr_queue
        self.action_queue = action_queue
        self.line_status_queue = line_status_queue
        self.status_queue = status_queue
        self.fin_carrera = Button(25, pull_up=True)
        self._lgpio_handle = lgpio.gpiochip_open(4)
        lgpio.gpio_claim_input(self._lgpio_handle, 27)
        self.contador_infrarrojo = 0
        self.umbral_infrarrojo = 5  # 5 lecturas × 0.05s = 0.25s de confirmación
        self.contador_ambas = 0
        self.contador_zigzag = 0
        self.MAX_ZIGZAG = 20

        # 🔥 Control de comandos (ANTI-SPAM)
        self.ultimo_comando_enviado = None

        self.estado = "ESPERA_CARGA"
        self.tipo_estacion = None
        self.numero_estacion = None
        self.carril_objetivo = None
        self.direccion_guardada = None

        # ✅ Ahora recibimos dict {"ambas": bool, "amarilla": bool}
        self.ambas_lineas = False
        self.hay_amarilla = False

        self.qr_visible = False
        self.tiempo_ultimo_qr = 0
        self.timeout_perdida_qr = 4.0

        self.ultimo_qr_procesado = None
        self.tiempo_ultimo_procesamiento = 0
        self.cooldown_procesamiento = 1.5

        # ✅ Control del zigzag en intersección
        self.zigzag_paso = 0        # 0 = d, 1 = a, alternando
        self.zigzag_tiempo = 0      # timestamp del último cambio de paso
        self.ZIGZAG_D = 0.60        # segundos girando (d)
        self.ZIGZAG_A = 0.2        # segundos avanzando (a)

    # ==============================
    # 🔧 ENVÍO CONTROLADO DE ACCIONES
    # ==============================
    def enviar_accion(self, cmd):
        if cmd != self.ultimo_comando_enviado:
            self.action_queue.put(cmd)
            self.ultimo_comando_enviado = cmd

    def infrarrojo_detecta(self):
        valor = lgpio.gpio_read(self._lgpio_handle, 27)
        return valor == 0  # 0 = detecta

    # ==============================
    # 🔁 LOOP PRINCIPAL
    # ==============================
    def ejecutar(self):
        print("[QR Logic] Iniciado. Final de carrera GPIO25.")

        while True:
            # Vaciar cola, usar solo dato más reciente
            try:
                line_data = None
                while True:
                    try:
                        line_data = self.line_status_queue.get(block=False)
                    except:
                        break
                if line_data is not None:
                    if isinstance(line_data, dict):
                        self.ambas_lineas = line_data.get("ambas", False)
                        self.hay_amarilla = line_data.get("amarilla", False)
                    else:
                        self.ambas_lineas = bool(line_data)
            except:
                pass

            # QR recibido (entero: ID del tag)
            try:
                tag_id = self.qr_queue.get(block=False)
                print(f"[QR] Tag recibido: ID={tag_id}")
                self.procesar_qr(tag_id)
            except:
                pass

            self.actualizar_visibilidad_qr()
            self.actualizar_accion()
            self.enviar_estado()

            time.sleep(0.05)

    # ==============================
    # 📡 DEBUG PARA STREAM
    # ==============================
    def enviar_estado(self):
        estado_info = {
            "estado": self.estado,
            "num_estacion": self.numero_estacion or "---",
            "carril": self.carril_objetivo or "---",
            "direccion": self.direccion_guardada or "---",
            "ambas_lineas": self.ambas_lineas,
            "hay_amarilla": self.hay_amarilla,
            "qr_visible": self.qr_visible,
            "fin_carrera": self.fin_carrera.is_pressed
        }
        try:
            self.status_queue.put(estado_info, block=False)
        except:
            pass

    # ==============================
    # 👁️ VISIBILIDAD QR
    # ==============================
    def actualizar_visibilidad_qr(self):
        ahora = time.time()
        if self.qr_visible and (ahora - self.tiempo_ultimo_qr) > self.timeout_perdida_qr:
            print("[QR] Tag perdido de vista (timeout)")
            self.qr_visible = False

    # ==============================
    # 🧠 PROCESAMIENTO TAG
    # ==============================
    def procesar_qr(self, tag_id):
        if self.estado not in ("ESPERA_CARGA",):
            if tag_id == 1:
                print("[QR] Ignorando tag de carga, estado actual:", self.estado)
                return

        if self.estado == "AVANZAR_8S":
            return

        ahora = time.time()

        if tag_id == self.ultimo_qr_procesado and (ahora - self.tiempo_ultimo_procesamiento) < self.cooldown_procesamiento:
            return

        contenido = MAPA_TAGS.get(tag_id)
        if contenido is None:
            print(f"[QR] ID {tag_id} no encontrado en MAPA_TAGS")
            return

        self.ultimo_qr_procesado = tag_id
        self.tiempo_ultimo_procesamiento = ahora
        self.tiempo_ultimo_qr = ahora
        self.qr_visible = True

        print(f"TAG ID: {tag_id}")
        print(f"CONTENIDO: {contenido}")
        print(f"ESTADO ACTUAL: {self.estado}")

        # ==============================
        # 🟢 ESPERA CARGA  →  ID 1
        # ==============================
        if self.estado == "ESPERA_CARGA":
            if tag_id == 1:
                print("[Estado] Tag Carga (ID 1) -> seguir línea directo")
                self.ultimo_comando_enviado = "FORZAR"
                self.enviar_accion(None)
                self.estado = "ESPERA_OBJETIVO"
            return

        # ==============================
        # 🟢 OBJETIVO  →  ID 2, 3, 4
        # ==============================
        if self.estado in ("ESPERA_OBJETIVO", "ESPERA_OBJETIVO_QR"):
            if tag_id in (2, 3, 4):
                tipo   = contenido.get("tipo", "").lower()
                numero = contenido.get("numero")
                carril = contenido.get("carril", "").lower()

                if tipo == "descarga" and numero is not None and carril:
                    self.tipo_estacion   = tipo
                    self.numero_estacion = numero
                    self.carril_objetivo = carril
                    print(f"[Estado] Objetivo guardado: Estación {self.numero_estacion} en {self.carril_objetivo}")
            return

        # ==============================
        # 🟡 GIRO  →  ID 5
        # ==============================
        if self.estado == "ESPERA_GIRO":
            if tag_id == 5:
                if self.carril_objetivo == "carril 2":
                    print("[Estado] Tag 5 + carril 2 → CRUZANDO_INTERSECCION")
                    self.estado = "CRUZANDO_INTERSECCION"
                    self.ultimo_comando_enviado = "FORZAR"
                    self.enviar_accion(None)
                elif self.carril_objetivo == "carril 3":
                    print("[Estado] Tag 5 + carril 3 → CRUZANDO")
                    self.estado = "CRUZANDO"
                    self.ultimo_comando_enviado = "FORZAR"
                    self.enviar_accion(None)
            return

        # ==============================
        # 🟢 DESCARGA  →  ID 6, 7, 8
        # ==============================
        if self.estado in ("ESPERA_DESCARGA"):
            if tag_id in (6, 7, 8):
                num_estacion_tag = contenido.get("numero")
                posicion         = contenido.get("posicion", "").lower()

                if posicion == "entrada" and num_estacion_tag == self.numero_estacion:
                    print(f"[Estado] Entrada a estación {self.numero_estacion} (ID {tag_id})")
                    self.ultimo_comando_enviado = "FORZAR"
                    self.enviar_accion(None)   # bloquea marcos + sigue línea
                    self.estado = "ESPERA_FIN_DESCARGA"
            return

        # ==============================
        # 🟢 FIN RECORRIDO  →  ID 9, 10
        # ==============================
        if self.estado == "ESPERA_FIN_RECORRIDO":
            if tag_id == 9:
                print(f"[Estado] Tag 9 → CRUZANDO_INTERSECCION_2")
                self.estado = "CRUZANDO_INTERSECCION_2"
                # Vaciar cola para que no haya "x" pendientes que consuman el delay de 4s
                try:
                    while True:
                        self.action_queue.get(block=False)
                except:
                    pass
                self.ultimo_comando_enviado = "FORZAR"
                self.enviar_accion(None)

            elif tag_id == 10:
                print("[Estado] Tag 10 + carril 3 → CRUZANDO")
                self.estado = "CRUZANDO"
                self.ultimo_comando_enviado = "FORZAR"
                self.enviar_accion(None)
            return

    # ==============================
    # ⚙️ ACCIONES
    # ==============================
    def actualizar_accion(self):
        ahora = time.time()

        if self.estado == "ESPERANDO_FIN_CARRERA":
            if self.fin_carrera.is_pressed:
                print("[Estado] Fin de carrera -> continuar")
                self.enviar_accion(None)
                self.estado = "ESPERA_OBJETIVO"

        elif self.estado == "ESPERA_OBJETIVO":
            if self.infrarrojo_detecta():
                self.contador_infrarrojo += 1
                if self.contador_infrarrojo == self.umbral_infrarrojo:
                    self.ultimo_comando_enviado = "FORZAR"
                    self.enviar_accion("x")
                    print("[Estado] Infrarrojo confirmado → STOP")
            else:
                self.contador_infrarrojo = 0

            if self.fin_carrera.is_pressed:
                if not hasattr(self, 'tiempo_fin_carrera'):
                    self.tiempo_fin_carrera = ahora
                    print("[Estado] Fin carrera activo → esperando 5s")
                elif (ahora - self.tiempo_fin_carrera) >= 5.0:
                    print("[Estado] Delay completo → seguir línea buscando QR")
                    del self.tiempo_fin_carrera
                    self.ultimo_comando_enviado = "FORZAR"
                    self.ultimo_qr_procesado = None
                    self.numero_estacion = None
                    self.enviar_accion("SEGUIR_BUSCANDO")
                    self.estado = "ESPERA_OBJETIVO_QR"
            else:
                if hasattr(self, 'tiempo_fin_carrera'):
                    del self.tiempo_fin_carrera

        elif self.estado == "ESPERA_OBJETIVO_QR":
            if self.numero_estacion is not None:
                print(f"[Estado] Objetivo recibido → Estación {self.numero_estacion} → ESPERA_GIRO")
                self.ultimo_qr_procesado = None
                self.estado = "ESPERA_GIRO"

            if self.ultimo_comando_enviado != "SEGUIR_BUSCANDO":
                self.ultimo_comando_enviado = "FORZAR"
                self.enviar_accion("SEGUIR_BUSCANDO")

        elif self.estado == "ESPERA_GIRO":
            if self.ultimo_comando_enviado != "SEGUIR_BUSCANDO":
                self.ultimo_comando_enviado = "FORZAR"
                self.enviar_accion("SEGUIR_BUSCANDO")

        elif self.estado == "CRUZANDO":
            if not hasattr(self, 'inter_tiempo'):
                self.inter_tiempo = ahora
                self.enviar_accion("CRUZANDO")
                print("[Cruzar] PI activo con referencia azul oscura")

            if (ahora - self.inter_tiempo) >= 4.0:
                print("[Cruzar] completo → seguir línea buscando QR")
                del self.inter_tiempo
                self.ultimo_comando_enviado = "FORZAR"
                self.enviar_accion("SEGUIR_BUSCANDO")
                self.estado = "ESPERA_DESCARGA"
                self.direccion_guardada = None

        # ==============================
        # 🔶 CRUZANDO INTERSECCIÓN (curva fija 100°)
        # ==============================
        elif self.estado == "CRUZANDO_INTERSECCION":
            if not hasattr(self, 'inter_tiempo'):
                self.inter_tiempo = ahora
                self.enviar_accion("S:55")
                print("[Intersección] Curva fija S:55 por 6s")

            if (ahora - self.inter_tiempo) >= 6.0:
                print("[Intersección] completo → seguir línea buscando QR")
                del self.inter_tiempo
                self.ultimo_comando_enviado = "FORZAR"
                self.enviar_accion("SEGUIR_BUSCANDO")
                self.estado = "ESPERA_DESCARGA"
                self.direccion_guardada = None

        elif self.estado == "CRUZANDO_INTERSECCION_2":
            if not hasattr(self, '_ci2_init'):
                self._ci2_init = ahora
                self._amarilla_vista = False
                self._sin_amarilla_count = 0
                self.ultimo_comando_enviado = "FORZAR"
                self.enviar_accion(None)  # qr_logic_activo=True: sigue línea sin detección de marcos
                print("[Intersección2] Siguiendo línea hasta perder azul clarita")

            if not hasattr(self, 'inter_tiempo'):
                if self.hay_amarilla:
                    self._amarilla_vista = True
                    self._sin_amarilla_count = 0
                    if hasattr(self, '_perdida_tiempo'):
                        del self._perdida_tiempo
                else:
                    if self._amarilla_vista:
                        self._sin_amarilla_count += 1

                timeout_alcanzado = (ahora - self._ci2_init) >= 15.0
                amarilla_perdida = self._amarilla_vista and self._sin_amarilla_count >= 3

                if amarilla_perdida and not hasattr(self, '_perdida_tiempo'):
                    self._perdida_tiempo = ahora
                    self.ultimo_comando_enviado = "FORZAR"
                    self.enviar_accion("S:90")
                    print("[Intersección2] Azul clarita perdida → avanzando recto 2.5s más")

                listo_para_girar = hasattr(self, '_perdida_tiempo') and (ahora - self._perdida_tiempo) >= 4.0

                if listo_para_girar or timeout_alcanzado:
                    self.inter_tiempo = ahora
                    self.ultimo_comando_enviado = "FORZAR"
                    self.enviar_accion("S:50")
                    if timeout_alcanzado:
                        print("[Intersección2] Timeout 15s → Curva S:50 por 6s")
                    else:
                        print("[Intersección2] Delay completo → Curva S:50 por 6s")
            else:
                if (ahora - self.inter_tiempo) >= 6.0:
                    print("[Intersección2] completo → ESPERA_OBJETIVO")
                    del self.inter_tiempo
                    del self._ci2_init
                    del self._amarilla_vista
                    del self._sin_amarilla_count
                    if hasattr(self, '_perdida_tiempo'):
                        del self._perdida_tiempo
                    self.ultimo_comando_enviado = "FORZAR"
                    self.enviar_accion("SEGUIR_BUSCANDO")
                    self.estado = "ESPERA_OBJETIVO"
                    self.direccion_guardada = None

        elif self.estado == "ESPERA_FIN_DESCARGA":
            if self.infrarrojo_detecta():
                self.contador_infrarrojo += 1
                if self.contador_infrarrojo >= self.umbral_infrarrojo:
                    self.ultimo_comando_enviado = "FORZAR"
                    self.enviar_accion("x")
                    print("[Estado] IR confirmado → STOP, esperando fin carrera")
                    self.estado = "ESPERANDO_FIN_CARRERA_DESCARGA"
            else:
                self.contador_infrarrojo = 0
                 # ✅ seguir línea mientras no hay IR
                if self.ultimo_comando_enviado != None:
                    self.ultimo_comando_enviado = "FORZAR"
                    self.enviar_accion(None)

        elif self.estado == "ESPERANDO_FIN_CARRERA_DESCARGA":
            if not self.fin_carrera.is_pressed:
                if not hasattr(self, 'tiempo_descarga'):
                    self.tiempo_descarga = ahora
                    print("[Estado] Fin carrera desactivado + IR activo → timer 7s")
                elif (ahora - self.tiempo_descarga) >= 7.0:
                    print("[Estado] Timer completo → seguir línea buscando QR")
                    del self.tiempo_descarga
                    self.contador_infrarrojo = 0
                    self.ultimo_comando_enviado = "FORZAR"
                    self.enviar_accion("SEGUIR_BUSCANDO")
                    self.estado = "ESPERA_FIN_RECORRIDO"
            else:
                if hasattr(self, 'tiempo_descarga'):
                    del self.tiempo_descarga


def run_qr_logic(qr_q, action_q, line_q, status_q):
    logic = QRLogic(qr_q, action_q, line_q, status_q)
    logic.ejecutar()


if __name__ == '__main__':
    qr_q = mp.Queue()
    action_q = mp.Queue()
    line_q = mp.Queue()
    status_q = mp.Queue()

    run_qr_logic(qr_q, action_q, line_q, status_q)