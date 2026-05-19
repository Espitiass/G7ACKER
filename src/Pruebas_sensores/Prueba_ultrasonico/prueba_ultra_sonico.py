from gpiozero import DistanceSensor
import time

sensor = DistanceSensor(echo=24, trigger=23)

while True:
    print(sensor.distance * 100)
    time.sleep(0.5)