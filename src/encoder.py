# ============================================================
# encoder.py - Lectura de encoder incremental cuadratura
# Compatible con MicroPython en ESP32
# ============================================================

from machine import Pin
import time


class Encoder:
    """
    Lectura de encoder incremental en cuadratura (canales A y B).

    Parámetros:
        pin_a   : Pin canal A del encoder
        pin_b   : Pin canal B del encoder
        ppr     : Pulsos por revolución del encoder (default 20)
        nombre  : Etiqueta para logs (default "Motor")
    """

    def __init__(self, pin_a, pin_b, ppr=20, nombre="Motor"):

        self._pin_a = Pin(pin_a, Pin.IN, Pin.PULL_UP)
        self._pin_b = Pin(pin_b, Pin.IN, Pin.PULL_UP)

        self._ppr = ppr
        self._nombre = nombre
        self._pulsos = 0

        self._ultimo_a = self._pin_a.value()

        # Interrupción en flanco de subida y bajada
        self._pin_a.irq(
            trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
            handler=self._isr
        )

        print("[Encoder-%s] Inicializado | A=%d B=%d | PPR=%d" %
              (self._nombre, pin_a, pin_b, ppr))

    # ─────────────────────────────────────────
    # ISR (Interrupción)
    # ─────────────────────────────────────────
    def _isr(self, pin):

        a = self._pin_a.value()
        b = self._pin_b.value()

        if a != self._ultimo_a:

            if a == b:
                self._pulsos += 1
            else:
                self._pulsos -= 1

        self._ultimo_a = a

    # ─────────────────────────────────────────
    # Funciones públicas
    # ─────────────────────────────────────────

    def reset(self):
        """Reinicia el contador"""
        self._pulsos = 0

    @property
    def pulsos(self):
        """Retorna pulsos acumulados"""
        return self._pulsos

    @property
    def revoluciones(self):
        """Retorna revoluciones"""
        return self._pulsos / self._ppr

    def rpm(self, intervalo_ms=100):
        """
        Calcula RPM en un intervalo de tiempo
        """

        inicio = self._pulsos

        time.sleep_ms(intervalo_ms)

        delta = self._pulsos - inicio

        rpm = (delta / self._ppr) * (60000 / intervalo_ms)

        return round(rpm, 2)

    # ─────────────────────────────────────────
    # Debug
    # ─────────────────────────────────────────
    def imprimir_estado(self):

        print("[Encoder-%s] Pulsos=%d | Rev=%.2f | RPM≈ %.1f" % (
            self._nombre,
            self._pulsos,
            self.revoluciones,
            self.rpm(200)
        ))