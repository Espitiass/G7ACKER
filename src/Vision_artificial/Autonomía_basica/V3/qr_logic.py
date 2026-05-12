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

        # 🔥 Control de comandos (ANTI-SPAM)
        self.ultimo_comando_enviado = None

        self.estado = "ESPERA_CARGA"
        self.tipo_estacion = None
        self.numero_estacion = None
        self.carril_objetivo = None
        self.direccion_guardada = None
        self.ambas_lineas = False

        self.qr_visible = False
        self.tiempo_ultimo_qr = 0
        self.timeout_perdida_qr = 2.0

        # ⚠️ Ahora comparamos enteros (ID del tag) en vez de strings
        self.ultimo_qr_procesado = None
        self.tiempo_ultimo_procesamiento = 0
        self.cooldown_procesamiento = 1.5

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
            # Estado de líneas
            try:
                self.ambas_lineas = self.line_status_queue.get(block=False)
            except:
                pass

            # QR recibido (ahora es un entero: ID del tag)
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
    # 🧠 PROCESAMIENTO TAG (antes: procesar_qr con JSON)
    # ==============================
    def procesar_qr(self, tag_id):
        """
        Recibe un entero (ID del AprilTag), lo resuelve en MAPA_TAGS
        y ejecuta la misma lógica de estados que antes.
        """
        # --- Ignorar tags de carga cuando no toca ---
        if self.estado not in ("ESPERA_CARGA",):
            if tag_id == 1:  # ID 1 = carga
                print("[QR] Ignorando tag de carga, estado actual:", self.estado)
                return

        if self.estado == "AVANZAR_8S":
            return

        ahora = time.time()

        # Cooldown anti-spam (comparación entera)
        if tag_id == self.ultimo_qr_procesado and (ahora - self.tiempo_ultimo_procesamiento) < self.cooldown_procesamiento:
            return

        # Resolver el tag en el mapa
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
                    self.tipo_estacion    = tipo
                    self.numero_estacion  = numero
                    self.carril_objetivo  = carril
                    print(f"[Estado] Objetivo guardado: Estación {self.numero_estacion} en {self.carril_objetivo}")
            return

        # ==============================
        # 🟡 GIRO  →  ID 5
        # ==============================
        if self.estado == "ESPERA_GIRO":
            if tag_id == 5:
                direccion = None

                # contenido tiene forma {"carril 2": "izquierda", "carril 3": "avanzar"}
                if self.carril_objetivo and self.carril_objetivo in contenido:
                    valor = contenido[self.carril_objetivo].lower()

                    if "izquierda" in valor:
                        direccion = "izquierda"
                    elif "derecho" in valor or "avanzar" in valor:
                        # "avanzar" = seguir recto, mantenemos la lógica original
                        # que solo actuaba con izquierda/derecho; si es avanzar
                        # no giramos pero sí liberamos el override para seguir línea.
                        direccion = valor  # guardamos el valor literal

                if direccion:
                    self.direccion_guardada = direccion
                    print(f"[Estado] Tag Giro (ID 5) -> dirección: {direccion}")
                    self.ultimo_comando_enviado = "FORZAR"
                    self.enviar_accion(None)
                    self.estado = "ESPERANDO_PERDER_LINEAS"
            return

        # ==============================
        # 🟢 DESCARGA  →  ID 6, 7, 8
        # ==============================
        if self.estado == "ESPERA_DESCARGA":
            if tag_id in (6, 7, 8):
                num_estacion_tag = contenido.get("numero")
                posicion         = contenido.get("posicion", "").lower()

                if posicion == "entrada" and num_estacion_tag == self.numero_estacion:
                    print(f"[Estado] Entrada a estación {self.numero_estacion} (ID {tag_id})")
                    self.enviar_accion("a")
                    self.estado = "ESPERA_FIN_DESCARGA"
            return

        # ==============================
        # 🟢 FIN RECORRIDO  →  ID 9, 10
        # ==============================
        if self.estado == "ESPERA_FIN_RECORRIDO":
            if tag_id in (9, 10):
                # Buscamos la dirección para "carril 1"
                # (misma lógica que el bloque original con "Carril 1")
                dir_text = contenido.get("carril 1", "").lower()

                if dir_text:
                    if "izquierda" in dir_text:
                        self.direccion_guardada = "izquierda"
                    elif "derecho" in dir_text or "derecha" in dir_text:
                        self.direccion_guardada = "derecho"

                    print(f"[Estado] Fin recorrido (ID {tag_id}) -> dirección: {self.direccion_guardada}")
                    self.estado = "ESPERANDO_PERDER_LINEAS"
            return

    # ==============================
    # ⚙️ ACCIONES  (sin cambios)
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
                if self.contador_infrarrojo >= self.umbral_infrarrojo:
                    self.ultimo_comando_enviado = "FORZAR"
                    self.enviar_accion("x")
                    print("[Estado] Infrarrojo confirmado → STOP, esperando fin de carrera")
            else:
                self.contador_infrarrojo = 0

            if self.fin_carrera.is_pressed:
                print("[Estado] Fin carrera → seguir línea buscando QR objetivo")
                self.ultimo_comando_enviado = "FORZAR"
                self.ultimo_qr_procesado = None
                self.numero_estacion = None
                self.enviar_accion("SEGUIR_BUSCANDO")
                self.estado = "ESPERA_OBJETIVO_QR"

        elif self.estado == "ESPERA_OBJETIVO_QR":
            if self.numero_estacion is not None:
                print(f"[Estado] Objetivo recibido → Estación {self.numero_estacion} → ESPERA_GIRO")
                self.ultimo_qr_procesado = None
                self.estado = "ESPERA_GIRO"

            if self.ultimo_comando_enviado != "SEGUIR_BUSCANDO":
                self.ultimo_comando_enviado = "FORZAR"
                self.enviar_accion("SEGUIR_BUSCANDO")

            if self.numero_estacion is not None:
                print(f"[Estado] Objetivo recibido → Estación {self.numero_estacion} → ESPERA_GIRO")
                self.estado = "ESPERA_GIRO"

        elif self.estado == "ESPERA_GIRO":
            if self.ultimo_comando_enviado != "SEGUIR_BUSCANDO":
                self.ultimo_comando_enviado = "FORZAR"
                self.enviar_accion("SEGUIR_BUSCANDO")

        elif self.estado == "ESPERANDO_PERDER_LINEAS":
            if not self.ambas_lineas:
                print("[Estado] Ejecutando giro")

                if self.direccion_guardada == "izquierda":
                    self.enviar_accion("i")
                elif self.direccion_guardada == "derecho":
                    self.enviar_accion("a")

                self.estado = "ESPERANDO_RECUPERAR_LINEAS"

        elif self.estado == "ESPERANDO_RECUPERAR_LINEAS":
            if self.ambas_lineas:
                print("[Estado] Línea recuperada")
                self.enviar_accion(None)
                self.estado = "ESPERA_DESCARGA"
                self.direccion_guardada = None

        elif self.estado == "ESPERA_FIN_DESCARGA":
            if not self.qr_visible:
                print("[Estado] Tag descarga perdido -> STOP")
                self.enviar_accion("x")
                self.estado = "ESPERANDO_FIN_CARRERA_DESACTIVAR"
                self.tiempo_inicio_espera = ahora

        elif self.estado == "ESPERANDO_FIN_CARRERA_DESACTIVAR":
            if not self.fin_carrera.is_pressed:

                if not hasattr(self, 'tiempo_desactivacion'):
                    self.tiempo_desactivacion = ahora

                elif (ahora - self.tiempo_desactivacion) >= 3.0:
                    print("[Estado] Fin carrera liberado -> continuar")
                    self.enviar_accion(None)
                    self.estado = "ESPERA_FIN_RECORRIDO"
                    del self.tiempo_desactivacion

            else:
                if hasattr(self, 'tiempo_desactivacion'):
                    del self.tiempo_desactivacion


def run_qr_logic(qr_q, action_q, line_q, status_q):
    logic = QRLogic(qr_q, action_q, line_q, status_q)
    logic.ejecutar()


if __name__ == '__main__':
    qr_q = mp.Queue()
    action_q = mp.Queue()
    line_q = mp.Queue()
    status_q = mp.Queue()

    run_qr_logic(qr_q, action_q, line_q, status_q)