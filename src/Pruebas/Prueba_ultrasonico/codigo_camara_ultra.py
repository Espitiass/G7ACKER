from gpiozero import DistanceSensor
import time
import serial

# Configuración del sensor
sensor = DistanceSensor(echo=24, trigger=23, max_distance=4)

# Configurar serial
ser = serial.Serial('/dev/serial0', 115200, timeout=1)

print("Iniciando sensor...")
time.sleep(2)

def medir_distancia():
    try:
        distancia = sensor.distance * 100  # convertir a cm
        return distancia
    except Exception as e:
        print("Error sensor:", e)
        return None

try:
    while True:
        distancia = medir_distancia()

        if distancia is None:
            print("❌ Sin lectura")
            ser.write(b'x\n')

        else:
            print(f"Distancia: {distancia:.2f} cm")

            if 2 < distancia <= 30:
                ser.write(b'x\n')
                print("➡️ Enviando: x (obstáculo)")
            else:
                ser.write(b'a\n')
                print("➡️ Enviando: a (avanzar)")

        time.sleep(0.3)

except KeyboardInterrupt:
    print("Programa detenido")
    ser.close()