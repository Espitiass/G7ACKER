import time
import motores

while True:

    motores.adelante()
    time.sleep(3)

    motores.izquierda()
    time.sleep(2)

    motores.derecha()
    time.sleep(2)

    motores.atras()
    time.sleep(3)

    motores.paro()
    time.sleep(3)