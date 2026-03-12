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
        self._pin_a  = Pin(pin_a, Pin.IN, Pin.PULL_UP)
        self._pin_b  = Pin(pin_b, Pin.IN, Pin.PULL_UP)
        self._ppr    = ppr
        self._nombre = nombre
        self._pulsos = 0
        self._ultimo_a = self._pin_a.value()

        # Interrupción en flanco de subida y bajada del canal A
        self._pin_a.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
                        handler=self._isr)
        print(f"[Encoder-{self._nombre}] Inicializado | A={pin_a} B={pin_b} | PPR={ppr}")

    # ── ISR ──────────────────────────────────────────────────
    def _isr(self, pin):
        """Rutina de interrupción: cuenta pulsos y determina dirección."""
        a = self._pin_a.value()
        b = self._pin_b.value()
        if a != self._ultimo_a:          # Flanco detectado en A
            if a == b:
                self._pulsos += 1        # Adelante
            else:
                self._pulsos -= 1        # Atrás
        self._ultimo_a = a

    # ── Públicos ─────────────────────────────────────────────
    def reset(self):
        """Reinicia el contador de pulsos a cero."""
        self._pulsos = 0

    @property
    def pulsos(self):
        """Retorna el conteo total de pulsos (con signo)."""
        return self._pulsos

    @property
    def revoluciones(self):
        """Retorna las revoluciones completas desde el último reset."""
        return self._pulsos / self._ppr

    def rpm(self, intervalo_ms=100):
        """
        Calcula RPM durante un intervalo dado.

        Parámetros:
            intervalo_ms: tiempo de medición en milisegundos
        Retorna:
            RPM (float)
        """
        inicio = self._pulsos
        time.sleep_ms(intervalo_ms)
        delta = self._pulsos - inicio
        rpm = (delta / self._ppr) * (60000 / intervalo_ms)
        return round(rpm, 2)

    def imprimir_estado(self):
        """Imprime el estado actual del encoder."""
        print(f"[Encoder-{self._nombre}] "
              f"Pulsos={self._pulsos:+6d} | "
              f"Rev={self.revoluciones:+.2f} | "
              f"RPM≈{self.rpm(200):+.1f}")