from machine import Pin

encoder_izq = Pin(34, Pin.IN)
encoder_der = Pin(18, Pin.IN)

contador_izq = 0
contador_der = 0

def contar_izq(pin):
    global contador_izq
    contador_izq += 1

def contar_der(pin):
    global contador_der
    contador_der += 1

encoder_izq.irq(trigger=Pin.IRQ_RISING, handler=contar_izq)
encoder_der.irq(trigger=Pin.IRQ_RISING, handler=contar_der)