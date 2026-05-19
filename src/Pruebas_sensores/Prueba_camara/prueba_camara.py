from flask import Flask, Response
from picamera2 import Picamera2
import cv2
import numpy as np

app = Flask(__name__)
picam2 = Picamera2()

    picam2.start()
    time.sleep(2)
    picam2.capture_file("foto_prueba.jpg")
    picam2.stop()

    print("Foto tomada correctamente")

except Exception as e:
    print("Error:", e)
