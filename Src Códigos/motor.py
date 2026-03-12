# ============================================================
# motor.py - Clase Motor para TB6612FNG
# Compatible con MicroPython en ESP32
# ============================================================

from machine import Pin, PWM
import time

class Motor:
    """
    Control de un motor DC mediante el driver TB6612FNG.

    Parámetros:
        in1      : Pin dirección 1  (AIN1 o BIN1)
        in2      : Pin dirección 2  (AIN2 o BIN2)
        pwm_pin  : Pin señal PWM    (PWMA o PWMB)
        stby_pin : Pin STANDBY compartido
        canal_pwm: Canal PWM del ESP32 (0-15)
        freq     : Frecuencia PWM en Hz (default 1000)
    """

    ADELANTE  = (1, 0)
    ATRAS     = (0, 1)
    FRENO     = (1, 1)
    LIBRE     = (0, 0)

    def __init__(self, in1, in2, pwm_pin, stby_pin,
                 canal_pwm=0, freq=1000):
        self._in1  = Pin(in1,  Pin.OUT)
        self._in2  = Pin(in2,  Pin.OUT)
        self._stby = Pin(stby_pin, Pin.OUT)
        self._pwm  = PWM(Pin(pwm_pin), freq=freq, duty=0)
        self._velocidad = 0

        # Activar driver (STBY en HIGH)
        self._stby.value(1)
        self._set_direccion(self.LIBRE)
        print(f"[Motor] Inicializado | PWM pin={pwm_pin} | STBY pin={stby_pin}")

    # ── Privados ─────────────────────────────────────────────
    def _set_direccion(self, modo):
        self._in1.value(modo[0])
        self._in2.value(modo[1])

    def _duty_desde_pct(self, pct):
        """Convierte porcentaje 0-100 a valor duty 0-1023 (MicroPython)."""
        return int(abs(pct) / 100 * 1023)

    # ── Públicos ─────────────────────────────────────────────
    def adelante(self, velocidad=60):
        """Gira hacia adelante. velocidad: 0-100 (%)"""
        velocidad = max(0, min(100, velocidad))
        self._set_direccion(self.ADELANTE)
        self._pwm.duty(self._duty_desde_pct(velocidad))
        self._velocidad = velocidad

    def atras(self, velocidad=60):
        """Gira hacia atrás. velocidad: 0-100 (%)"""
        velocidad = max(0, min(100, velocidad))
        self._set_direccion(self.ATRAS)
        self._pwm.duty(self._duty_desde_pct(velocidad))
        self._velocidad = -velocidad

    def detener(self):
        """Freno activo (IN1=1, IN2=1)."""
        self._set_direccion(self.FRENO)
        self._pwm.duty(0)
        self._velocidad = 0

    def libre(self):
        """Deja el motor en rueda libre (IN1=0, IN2=0)."""
        self._set_direccion(self.LIBRE)
        self._pwm.duty(0)
        self._velocidad = 0

    def set_velocidad(self, velocidad):
        """
        Controla velocidad y dirección con un solo valor.
        velocidad: -100 (atrás máx) a +100 (adelante máx)
        """
        if velocidad > 0:
            self.adelante(velocidad)
        elif velocidad < 0:
            self.atras(abs(velocidad))
        else:
            self.detener()

    def standby(self, activar=True):
        """Pone el driver en standby (desactiva ambos motores)."""
        self._stby.value(0 if activar else 1)

    @property
    def velocidad(self):
        """Retorna la velocidad actual en %."""
        return self._velocidad