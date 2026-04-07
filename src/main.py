# ============================================================
# main.py - ESP32 + TB6612FNG + MicroPython
# Control de motores DC con encoder
# ============================================================

from motor import Motor
from encoder import Encoder
from prueba_motores import PruebaMotores
import time

# ── Pines TB6612FNG ──────────────────────────────────────────
# Motor A (Izquierdo)
AIN1 = 14   # Dirección A - pin 1
AIN2 = 27   # Dirección A - pin 2
PWMA = 26   # PWM Motor A

# Motor B (Derecho)
BIN1 = 33   # Dirección B - pin 1
BIN2 = 32   # Dirección B - pin 2
PWMB = 23   # PWM Motor B


# ── Pines Encoders ───────────────────────────────────────────
ENC_A_A = 34  # Encoder Motor A - canal A
ENC_A_B = 35  # Encoder Motor A - canal B

ENC_B_A = 18  # Encoder Motor B - canal A
ENC_B_B = 19  # Encoder Motor B - canal B


# ── Inicialización ───────────────────────────────────────────
print("=" * 40)
print("  Iniciando sistema de motores ESP32")
print("=" * 40)

motor_izq = Motor(AIN1, AIN2, PWMA, canal_pwm=0)
motor_der = Motor(BIN1, BIN2, PWMB, canal_pwm=1)

encoder_izq = Encoder(ENC_A_A, ENC_A_B, nombre="Izquierdo")
encoder_der = Encoder(ENC_B_A, ENC_B_B, nombre="Derecho")

prueba = PruebaMotores(motor_izq, motor_der, encoder_izq, encoder_der)


# ── Menú principal ───────────────────────────────────────────
def menu():

    print("\n╔══════════════════════════════╗")
    print("║   PRUEBA DE MOTORES TB6612   ║")
    print("╠══════════════════════════════╣")
    print("║ 1. Prueba básica (adelante)  ║")
    print("║ 2. Prueba atrás              ║")
    print("║ 3. Giro izquierda            ║")
    print("║ 4. Giro derecha              ║")
    print("║ 5. Rampa velocidad           ║")
    print("║ 6. Prueba encoders           ║")
    print("║ 7. Prueba completa           ║")
    print("║ 8. Control manual PWM        ║")
    print("║ 0. Detener motores           ║")
    print("╚══════════════════════════════╝")


# ── Ejecución automática al arrancar ─────────────────────────
if __name__ == "__main__":

    time.sleep(1)

    # Ejecuta todas las pruebas automáticamente
    prueba.prueba_completa()