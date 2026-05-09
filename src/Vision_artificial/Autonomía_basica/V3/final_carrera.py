# ==========================================
# Lectura de final de carrera GPLV3
# Raspberry Pi 5 - GPIO 25
# ==========================================

from gpiozero import Button
from signal import pause

# Configurar el final de carrera en GPIO 25
# pull_up=True activa la resistencia pull-up interna
final_carrera = Button(25, pull_up=True)

print("Esperando activación del final de carrera...")

# Evento cuando se presiona
def activado():
    print("FINAL DE CARRERA ACTIVADO")

# Evento cuando se libera
def liberado():
    print("Final de carrera liberado")

# Asignar eventos
final_carrera.when_pressed = activado
final_carrera.when_released = liberado

# Mantener el programa ejecutándose
pause()