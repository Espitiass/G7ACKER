from machine import Pin, PWM

AIN1 = Pin(26, Pin.OUT)
AIN2 = Pin(27, Pin.OUT)

BIN1 = Pin(32, Pin.OUT)
BIN2 = Pin(33, Pin.OUT)

PWMA = PWM(Pin(25))
PWMB = PWM(Pin(14))

PWMA.freq(1000)
PWMB.freq(1000)

velocidad = 700

PWMA.duty(velocidad)
PWMB.duty(velocidad)

def adelante():

    AIN1.value(1)
    AIN2.value(0)

    BIN1.value(1)
    BIN2.value(0)

def atras():

    AIN1.value(0)
    AIN2.value(1)

    BIN1.value(0)
    BIN2.value(1)

def izquierda():

    AIN1.value(0)
    AIN2.value(1)

    BIN1.value(1)
    BIN2.value(0)

def derecha():

    AIN1.value(1)
    AIN2.value(0)

    BIN1.value(0)
    BIN2.value(1)

def paro():

    AIN1.value(0)
    AIN2.value(0)

    BIN1.value(0)
    BIN2.value(0)