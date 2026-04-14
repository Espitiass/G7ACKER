import RPi.GPIO as GPIO
import time
import serial

# Configuración de pines
TRIG = 23
ECHO = 24

# Configurar GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# Configurar serial (ajusta si es necesario)
ser = serial.Serial('/dev/serial0', 115200, timeout=1)

# Inicializar TRIG
GPIO.output(TRIG, False)
print("Iniciando sensor...")
time.sleep(2)

def medir_distancia():
    # Pulso TRIG
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    # Medir tiempos
    inicio = time.time()
    fin = time.time()

    # Esperar inicio del eco
    while GPIO.input(ECHO) == 0:
        inicio = time.time()

    # Esperar fin del eco
    while GPIO.input(ECHO) == 1:
        fin = time.time()

    duracion = fin - inicio
    distancia = (duracion * 34300) / 2

    return distancia

try:
    while True:
        distancia = medir_distancia()
        print(f"Distancia: {distancia:.2f} cm")

        if distancia <= 30:
            ser.write(b'x\n')
            print("➡️ Enviando: x (obstáculo)")
        else:
            ser.write(b'a\n')
            print("➡️ Enviando: a (avanzar)")

        time.sleep(0.3)

except KeyboardInterrupt:
    print("Programa detenido")
    GPIO.cleanup()
    ser.close()
