import RPi.GPIO as GPIO
import time

TRIG = 23
ECHO = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

GPIO.output(TRIG, False)
print("Esperando sensor...")
time.sleep(2)

def medir_distancia():
    # Pulso TRIG
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    inicio = time.time()
    timeout = inicio

    # Esperar que ECHO suba
    while GPIO.input(ECHO) == 0:
        inicio = time.time()
        if inicio - timeout > 0.02:  # 20 ms timeout
            return None

    # Esperar que ECHO baje
    while GPIO.input(ECHO) == 1:
        fin = time.time()
        if fin - inicio > 0.02:  # 20 ms timeout
            return None

    duracion = fin - inicio
    distancia = duracion * 34300 / 2
    return distancia

try:
    while True:
        distancia = medir_distancia()

        if distancia is None:
            print("⚠️ No hay lectura (revisa conexión)")
        else:
            print(f"Distancia: {distancia:.2f} cm")

        time.sleep(0.5)

except KeyboardInterrupt:
    print("Programa detenido")
    GPIO.cleanup()