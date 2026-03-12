# ============================================================
# prueba_motores.py - Suite completa de pruebas
# TB6612FNG + Encoders | MicroPython ESP32
# ============================================================

import time

class PruebaMotores:
    """
    Suite de pruebas para dos motores DC con encoders.

    Parámetros:
        motor_izq   : instancia de Motor (izquierdo)
        motor_der   : instancia de Motor (derecho)
        encoder_izq : instancia de Encoder (izquierdo)
        encoder_der : instancia de Encoder (derecho)
    """

    SEP = "─" * 40

    def __init__(self, motor_izq, motor_der,
                 encoder_izq=None, encoder_der=None):
        self.mi  = motor_izq
        self.md  = motor_der
        self.ei  = encoder_izq
        self.ed  = encoder_der

    # ── Utilidades ───────────────────────────────────────────
    def _titulo(self, texto):
        print(f"\n{self.SEP}")
        print(f"  {texto}")
        print(self.SEP)

    def _pausa(self, seg, msg=""):
        if msg:
            print(f"  ⏱  {msg} ({seg}s)...")
        time.sleep(seg)

    def _estado_encoders(self):
        if self.ei:
            self.ei.imprimir_estado()
        if self.ed:
            self.ed.imprimir_estado()

    def _reset_encoders(self):
        if self.ei: self.ei.reset()
        if self.ed: self.ed.reset()

    def _detener_todo(self):
        self.mi.detener()
        self.md.detener()

    # ── Test 1: Adelante ─────────────────────────────────────
    def test_adelante(self, velocidad=70, duracion=2):
        self._titulo("TEST 1 — ADELANTE")
        self._reset_encoders()
        print(f"  Velocidad: {velocidad}%  |  Duración: {duracion}s")

        self.mi.adelante(velocidad)
        self.md.adelante(velocidad)
        self._pausa(duracion, "Motores hacia adelante")

        self._estado_encoders()
        self._detener_todo()
        print("  ✓ Test adelante completado")

    # ── Test 2: Atrás ────────────────────────────────────────
    def test_atras(self, velocidad=70, duracion=2):
        self._titulo("TEST 2 — ATRÁS")
        self._reset_encoders()
        print(f"  Velocidad: {velocidad}%  |  Duración: {duracion}s")

        self.mi.atras(velocidad)
        self.md.atras(velocidad)
        self._pausa(duracion, "Motores hacia atrás")

        self._estado_encoders()
        self._detener_todo()
        print("  ✓ Test atrás completado")

    # ── Test 3: Giro Izquierda ───────────────────────────────
    def test_giro_izquierda(self, velocidad=60, duracion=1.5):
        self._titulo("TEST 3 — GIRO IZQUIERDA")
        self._reset_encoders()
        print(f"  Motor izq ATRÁS | Motor der ADELANTE")

        self.mi.atras(velocidad)
        self.md.adelante(velocidad)
        self._pausa(duracion, "Girando a la izquierda")

        self._estado_encoders()
        self._detener_todo()
        print("  ✓ Test giro izquierda completado")

    # ── Test 4: Giro Derecha ─────────────────────────────────
    def test_giro_derecha(self, velocidad=60, duracion=1.5):
        self._titulo("TEST 4 — GIRO DERECHA")
        self._reset_encoders()
        print(f"  Motor izq ADELANTE | Motor der ATRÁS")

        self.mi.adelante(velocidad)
        self.md.atras(velocidad)
        self._pausa(duracion, "Girando a la derecha")

        self._estado_encoders()
        self._detener_todo()
        print("  ✓ Test giro derecha completado")

    # ── Test 5: Rampa de velocidad ───────────────────────────
    def test_rampa(self, paso=10, espera=0.4):
        self._titulo("TEST 5 — RAMPA DE VELOCIDAD")
        print("  Subiendo: 0% → 100% → 0%")
        self._reset_encoders()

        # Subida
        for v in range(0, 101, paso):
            self.mi.adelante(v)
            self.md.adelante(v)
            print(f"  PWM: {v:3d}% ", end="")
            if self.ei:
                print(f"| RPM izq≈{self.ei.rpm(int(espera*1000)):+.0f}", end="")
            if self.ed:
                print(f"| RPM der≈{self.ed.rpm(int(espera*1000)):+.0f}", end="")
            print()
            time.sleep(espera)

        # Bajada
        for v in range(100, -1, -paso):
            self.mi.adelante(v)
            self.md.adelante(v)
            print(f"  PWM: {v:3d}%")
            time.sleep(espera)

        self._detener_todo()
        print("  ✓ Test rampa completado")

    # ── Test 6: Encoders ─────────────────────────────────────
    def test_encoders(self, velocidad=60, duracion=3):
        self._titulo("TEST 6 — MONITOREO DE ENCODERS")
        if not self.ei and not self.ed:
            print("  ⚠  No hay encoders configurados")
            return

        self._reset_encoders()
        self.mi.adelante(velocidad)
        self.md.adelante(velocidad)

        print(f"  Muestreo cada 500ms durante {duracion}s\n")
        muestras = int(duracion * 2)
        for i in range(muestras):
            print(f"  [{i+1}/{muestras}]", end=" ")
            self._estado_encoders()
            time.sleep(0.5)

        self._detener_todo()
        print("  ✓ Test encoders completado")

    # ── Test 7: Motor individual ─────────────────────────────
    def test_motor_individual(self, motor='A', velocidad=70, duracion=2):
        self._titulo(f"TEST — MOTOR {'IZQ' if motor=='A' else 'DER'} INDIVIDUAL")
        m = self.mi if motor == 'A' else self.md
        e = self.ei if motor == 'A' else self.ed

        if e: e.reset()
        m.adelante(velocidad)
        print(f"  Adelante {velocidad}% por {duracion}s")
        time.sleep(duracion)
        if e: e.imprimir_estado()

        m.atras(velocidad)
        print(f"  Atrás {velocidad}% por {duracion}s")
        if e: e.reset()
        time.sleep(duracion)
        if e: e.imprimir_estado()

        m.detener()
        print(f"  ✓ Motor {'A' if motor=='A' else 'B'} OK")

    # ── Test 8: Control PWM manual ───────────────────────────
    def test_pwm_manual(self, pwm_val=50):
        """
        Útil para verificar que el driver responde a valores específicos.
        pwm_val: 0-100
        """
        self._titulo(f"TEST PWM MANUAL — {pwm_val}%")
        self.mi.set_velocidad(pwm_val)
        self.md.set_velocidad(pwm_val)
        print(f"  Motores a {pwm_val}%  (presiona Ctrl+C para detener)")
        try:
            while True:
                self._estado_encoders()
                time.sleep(1)
        except KeyboardInterrupt:
            self._detener_todo()
            print("\n  Detenido por usuario")

    # ── Prueba COMPLETA ──────────────────────────────────────
    def prueba_completa(self):
        print("\n" + "═" * 40)
        print("   INICIO PRUEBA COMPLETA DE MOTORES")
        print("═" * 40)

        pausa = 1   # segundos entre pruebas

        self.test_motor_individual('A', velocidad=65, duracion=2)
        time.sleep(pausa)
        self.test_motor_individual('B', velocidad=65, duracion=2)
        time.sleep(pausa)
        self.test_adelante(velocidad=70, duracion=2)
        time.sleep(pausa)
        self.test_atras(velocidad=70, duracion=2)
        time.sleep(pausa)
        self.test_giro_izquierda(velocidad=60, duracion=1.5)
        time.sleep(pausa)
        self.test_giro_derecha(velocidad=60, duracion=1.5)
        time.sleep(pausa)
        self.test_rampa(paso=10, espera=0.3)
        time.sleep(pausa)
        self.test_encoders(velocidad=60, duracion=3)

        print("\n" + "═" * 40)
        print("   ✅ TODAS LAS PRUEBAS COMPLETADAS")
        print("═" * 40)