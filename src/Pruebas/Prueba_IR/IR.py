#!/usr/bin/env python3
"""
Sensor IR - GPIO 17 - Raspberry Pi 5
Lectura cruda con lgpio
"""

import lgpio
import time

CHIP = 4   # Raspberry Pi 5 usa gpiochip4
PIN  = 27

h = lgpio.gpiochip_open(CHIP)
lgpio.gpio_claim_input(h, PIN)

print(f"Leyendo GPIO {PIN} (chip {CHIP}) — Ctrl+C para salir\n")

try:
    while True:
        valor = lgpio.gpio_read(h, PIN)
        print(f"GPIO 17 = {valor}")
        time.sleep(0.2)

except KeyboardInterrupt:
    print("\nSaliendo...")

finally:
    lgpio.gpiochip_close(h)