import RPi.GPIO as GPIO
import time

# Pines
TRIG = 23
ECHO = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# Asegurar TRIG en bajo
GPIO.output(TRIG, False)
print("Esperando sensor...")
time.sleep(2)

try:
    while True:
        # Enviar pulso
        GPIO.output(TRIG, True)
        time.sleep(0.00001)  # 10 microsegundos
        GPIO.output(TRIG, False)

        # Medir tiempo de respuesta
        while GPIO.input(ECHO) == 0:
            inicio = time.time()

        while GPIO.input(ECHO) == 1:
            fin = time.time()

        duracion = fin - inicio

        # Calcular distancia
        distancia = (duracion * 34300) / 2

        print(f"Distancia: {distancia:.2f} cm")

        time.sleep(0.5)

except KeyboardInterrupt:
    print("Programa detenido")
    GPIO.cleanup()