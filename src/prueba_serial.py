import serial
import sys
import termios
import tty
import select

SERIAL_PORT = '/dev/ttyUSB0'
BAUDRATE = 115200

ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=0)

print("Control iniciado:")
print("a = Adelante | r = Atrás | d = Detenido | i = Izquierda | e = Derecha")
print("Presiona 'q' para salir\n")

# Configurar terminal en modo raw
fd = sys.stdin.fileno()
old_settings = termios.tcgetattr(fd)
tty.setcbreak(fd)

try:
    while True:

        rlist, _, _ = select.select([sys.stdin, ser], [], [], 0.01)

        if ser in rlist:
            try:
                linea = ser.readline().decode(errors='ignore').strip()
                if linea:
                    print(f"ESP32: {linea}")
            except:
                pass


        if sys.stdin in rlist:
            tecla = sys.stdin.read(1)

            if tecla == 'q':
                print("\nSaliendo...")
                break

            if tecla in ['a', 'r', 'd', 'i', 'e']:
                ser.write(tecla.encode())
                print(f"Enviado: {tecla}")

finally:
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    ser.close()