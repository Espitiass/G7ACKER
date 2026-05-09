#!/usr/bin/env python3
# qr_logic.py - Versión corregida con control de override limpio

import json
import time
import multiprocessing as mp
from gpiozero import Button
import lgpio

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

        self.ultimo_qr_procesado = ""
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
    # 📦 PARSEO QR
    # ==============================
    def parsear_qr(self, qr_str):
        try:
            data = json.loads(qr_str)
            if isinstance(data, list) and len(data) > 0:
                data = data[0]

            if not isinstance(data, dict):
                return None

            clave = list(data.keys())[0]
            contenido = data[clave]

            if isinstance(contenido, dict):
                return clave, contenido

            return None
        except Exception:
            return None

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

            # QR recibido
            try:
                qr_data = self.qr_queue.get(block=False)
                print(f"[QR] Recibido: {qr_data}")
                self.procesar_qr(qr_data)
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
            print("[QR] QR perdido de vista (timeout)")
            self.qr_visible = False

    # ==============================
    # 🧠 PROCESAMIENTO QR
    # ==============================
    def procesar_qr(self, qr_str):
        ahora = time.time()

        if self.estado not in ("ESPERA_CARGA",):
            parsed = self.parsear_qr(qr_str)
            if parsed:
                clave, contenido = parsed
                if contenido.get("tipo de estacion", "").lower() == "carga":
                    print("[QR] Ignorando QR de carga, estado actual:", self.estado)
                    return

        if self.estado == "AVANZAR_8S":
            return

        if qr_str == self.ultimo_qr_procesado and (ahora - self.tiempo_ultimo_procesamiento) < self.cooldown_procesamiento:
            return

        self.ultimo_qr_procesado = qr_str
        self.tiempo_ultimo_procesamiento = ahora
        self.tiempo_ultimo_qr = ahora
        self.qr_visible = True

        parsed = self.parsear_qr(qr_str)

        if parsed is None:
            print("[QR] Formato no reconocido")
            return

        clave, contenido = parsed
        print("CLAVE:", clave)
        print("CONTENIDO:", contenido)
        print("ESTADO ACTUAL:", self.estado)

        # ==============================
        # 🟢 ESPERA CARGA
        # ==============================
        if self.estado == "ESPERA_CARGA":
            if contenido.get("tipo de estacion", "").lower() == "carga":
                if contenido.get("posicion del qr", "").lower() == "entrada":
                    print("[Estado] QR Carga Entrada -> seguir línea directo")
                    self.ultimo_comando_enviado = "FORZAR"
                    self.enviar_accion(None)
                    self.estado = "ESPERA_OBJETIVO"
            return

        # ==============================
        # 🟢 OBJETIVO
        # ==============================
        if self.estado in ("ESPERA_OBJETIVO", "ESPERA_OBJETIVO_QR"):
            if "objetivo" in clave.lower():
                tipo = contenido.get("tipo de estacion", "").lower()
                numero = contenido.get("numero de estacion", "")
                carril = contenido.get("carril", "").lower()

                if tipo == "descarga" and numero and carril:
                    self.tipo_estacion = tipo
                    self.numero_estacion = numero
                    self.carril_objetivo = carril
                    print(f"[Estado] Objetivo guardado: Estación {self.numero_estacion} en {self.carril_objetivo}")
            return

        # ==============================
        # 🟡 GIRO
        # ==============================
        if self.estado == "ESPERA_GIRO":
            if "informativa" in clave.lower():

                direccion = None

                if self.carril_objetivo in contenido:
                    valor = contenido[self.carril_objetivo].lower()

                    if "izquierda" in valor:
                        direccion = "izquierda"
                    elif "derecho" in valor:
                        direccion = "derecho"

                if direccion:
                    self.direccion_guardada = direccion
                    print(f"[Estado] QR Giro -> dirección: {direccion}")
                    self.ultimo_comando_enviado = "FORZAR"  # ← romper anti-spam
                    self.enviar_accion(None)                # ← seguir línea
                    self.estado = "ESPERANDO_PERDER_LINEAS"

            return

        # ==============================
        # 🟢 DESCARGA
        # ==============================
        if self.estado == "ESPERA_DESCARGA":
            if "descarga" in clave.lower() and "entrada" in str(contenido).lower():

                num_estacion_qr = contenido.get("numero de estacion", "")

                if num_estacion_qr == self.numero_estacion:
                    print(f"[Estado] Entrada a estación {self.numero_estacion}")
                    self.enviar_accion("a")
                    self.estado = "ESPERA_FIN_DESCARGA"

            return

        # ==============================
        # 🟢 FIN RECORRIDO
        # ==============================
        if self.estado == "ESPERA_FIN_RECORRIDO":
            if "fin recorrido" in clave.lower():

                if "Carril 1" in contenido:
                    dir_text = contenido["Carril 1"].lower()

                    if "izquierda" in dir_text:
                        self.direccion_guardada = "izquierda"
                    elif "derecho" in dir_text:
                        self.direccion_guardada = "derecho"

                    print(f"[Estado] Fin recorrido -> dirección: {self.direccion_guardada}")
                    self.estado = "ESPERANDO_PERDER_LINEAS"

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
                if self.contador_infrarrojo >= self.umbral_infrarrojo:
                    self.ultimo_comando_enviado = "FORZAR"
                    self.enviar_accion("x")
                    print("[Estado] Infrarrojo confirmado → STOP, esperando fin de carrera")
            else:
                self.contador_infrarrojo = 0

            if self.fin_carrera.is_pressed:
                print("[Estado] Fin carrera → seguir línea buscando QR objetivo")
                self.ultimo_comando_enviado = "FORZAR"
                self.ultimo_qr_procesado = ""
                self.numero_estacion = None
                self.enviar_accion("SEGUIR_BUSCANDO")  # ← señal especial para buscar marcos
                self.estado = "ESPERA_OBJETIVO_QR"

        elif self.estado == "ESPERA_OBJETIVO_QR":
            if self.numero_estacion is not None:
                print(f"[Estado] Objetivo recibido → Estación {self.numero_estacion} → ESPERA_GIRO")
                self.ultimo_qr_procesado = ""  # ← agregar
                self.estado = "ESPERA_GIRO"
                
            if self.ultimo_comando_enviado != "SEGUIR_BUSCANDO":
                self.ultimo_comando_enviado = "FORZAR"
                self.enviar_accion("SEGUIR_BUSCANDO")

            if self.numero_estacion is not None:
                print(f"[Estado] Objetivo recibido → Estación {self.numero_estacion} → ESPERA_GIRO")
                self.estado = "ESPERA_GIRO"

        elif self.estado == "ESPERA_GIRO":          # ← agregar este bloque
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
                print("[Estado] QR descarga perdido -> STOP")
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

        # #elif self.estado == "AVANZAR_8S":
        #     if (ahora - self.tiempo_inicio_avance) >= 8.0:
        #         print("[Estado] 8s completados -> STOP")
        #         self.ultimo_comando_enviado = None
        #         self.enviar_accion("x")
        #         self.estado = "ESPERA_CARGA"

        # elif self.estado == "ESPERA_CARGA":
        #     if self.fin_carrera.is_pressed:
        #         print("[Estado] Fin de carrera -> seguir línea hacia objetivo")
        #         self.ultimo_comando_enviado = None
        #         self.enviar_accion(None)
        #         self.estado = "ESPERA_OBJETIVO"


def run_qr_logic(qr_q, action_q, line_q, status_q):
    logic = QRLogic(qr_q, action_q, line_q, status_q)
    logic.ejecutar()


if __name__ == '__main__':
    qr_q = mp.Queue()
    action_q = mp.Queue()
    line_q = mp.Queue()
    status_q = mp.Queue()

    run_qr_logic(qr_q, action_q, line_q, status_q)