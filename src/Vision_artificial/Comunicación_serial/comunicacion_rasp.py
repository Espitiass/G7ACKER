import serial
import sys
import tty
import termios

# CONFIGURA TU PUERTO
SERIAL_PORT = '/dev/ttyUSB0'  # Cambia si es necesario
BAUDRATE = 115200

# Abrir puerto serial
ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)

print("Control iniciado:")
print("a = Adelante | r = Atrás | d = Detenido | i = Izquierda | e = Derecha")
print("Presiona 'q' para salir\n")

# Función para leer una tecla sin Enter
def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        key = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return key

while True:
    tecla = get_key()

    if tecla == 'q':
        print("\nSaliendo...")
        break

    if tecla in ['a', 'r', 'd', 'i', 'e']:
        ser.write(tecla.encode())
        print(f"Enviado: {tecla}")

ser.close()