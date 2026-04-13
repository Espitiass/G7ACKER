from picamera2 import Picamera2
import time

try:
    picam2 = Picamera2()
    print("Cámaras detectadas:", picam2.global_camera_info())

    picam2.start()
    time.sleep(2)
    picam2.capture_file("foto_prueba.jpg")
    picam2.stop()

    print("Foto tomada correctamente")td

except Exception as e:
    print("Error:", e)
