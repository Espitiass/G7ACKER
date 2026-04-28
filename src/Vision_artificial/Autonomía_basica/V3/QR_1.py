import cv2
from picamera2 import Picamera2
import socket
import json
import time

class LectorQRSimple:
    def __init__(self):
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"size": (640, 480), "format": "RGB888"}
        )
        self.picam2.configure(config)
        self.picam2.start()
        time.sleep(1)
        
        self.qr_detector = cv2.QRCodeDetector()
        self.socket_client = None
        self.conectar_socket()
        
        self.ultimo_qr = ""
        self.tiempo_ultima_lectura = 0
        
    def conectar_socket(self):
        try:
            self.socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_client.connect(('localhost', 9999))
            print("✅ Conectado al sistema de carril")
            return True
        except Exception as e:
            print(f"❌ Error conectando: {e}")
            self.socket_client = None
            return False
    
    def enviar_comando(self, comando):
        if self.socket_client:
            try:
                mensaje = json.dumps({'comando': comando, 'timestamp': time.time()})
                self.socket_client.send(mensaje.encode())
                print(f"📤 Comando enviado: {comando}")
                return True
            except:
                print("🔄 Reconectando...")
                self.conectar_socket()
                if self.socket_client:
                    self.socket_client.send(mensaje.encode())
                    return True
        return False
    
    def procesar_qr(self, qr_data):
        print(f"📱 QR detectado: {qr_data}")
        
        # Intentar parsear como JSON (puede venir como lista o dict)
        try:
            # El JSON puede ser un array con un objeto, o directamente un objeto
            data = json.loads(qr_data)
            if isinstance(data, list) and len(data) > 0:
                data = data[0]  # Tomar el primer elemento
            
            # Extraer información
            # Las claves pueden ser dinámicas: "Descarga 2 S", "Estacion Carga Entrada", etc.
            # Pero dentro hay un objeto con campos estándar.
            # Asumimos que el objeto tiene: tipo_estacion, numero_estacion, posicion_qr
            # Ejemplo: {"tipo de estacion":"Descarga","numero de estacion":"2","posicion del qr":"Salida"}
            
            tipo = data.get("tipo de estacion", "").lower()
            numero = data.get("numero de estacion", "")
            posicion = data.get("posicion del qr", "").lower()
            
            print(f"📌 Tipo: {tipo}, Número: {numero}, Posición: {posicion}")
            
            # Lógica de decisión
            if posicion == "entrada":
                # Al entrar a una estación, detenerse
                comando = "x"
                razon = f"Entrada a {tipo} estación {numero}"
                self.enviar_comando(comando)
                print(f"🛑 {razon} -> Comando STOP")
                
            elif posicion == "salida":
                # Al salir, seguir adelante
                comando = "a"
                razon = f"Salida de {tipo} estación {numero}"
                self.enviar_comando(comando)
                print(f"🚀 {razon} -> Comando ADELANTE")
                
            else:
                print(f"⚠️ Posición no reconocida: {posicion}")
                
        except json.JSONDecodeError:
            print(f"⚠️ No es JSON válido: {qr_data}")
        except Exception as e:
            print(f"❌ Error procesando QR: {e}")
    
    def leer_qr(self):
        print("🔍 Iniciando lectura de QR (modo estaciones)...")
        print("Presiona 'q' para salir")
        
        while True:
            frame = self.picam2.capture_array()
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            qr_data, bbox, _ = self.qr_detector.detectAndDecode(gray)
            
            if qr_data and qr_data != "":
                tiempo_actual = time.time()
                if qr_data != self.ultimo_qr or (tiempo_actual - self.tiempo_ultima_lectura) > 2:
                    self.ultimo_qr = qr_data
                    self.tiempo_ultima_lectura = tiempo_actual
                    self.procesar_qr(qr_data)
            
            if bbox is not None and len(bbox) > 0:
                for i in range(len(bbox)):
                    pt1 = tuple(bbox[i][0])
                    pt2 = tuple(bbox[(i+1) % len(bbox)][0])
                    cv2.line(frame, pt1, pt2, (0, 255, 0), 3)
                if qr_data:
                    cv2.putText(frame, qr_data[:50], (10, 60), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.putText(frame, "Lector QR Estaciones", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow('Lector QR', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break
            
            time.sleep(0.05)
        
        cv2.destroyAllWindows()
    
    def ejecutar(self):
        try:
            self.leer_qr()
        except KeyboardInterrupt:
            print("\n👋 Deteniendo lector QR...")
        finally:
            if self.socket_client:
                self.socket_client.close()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    lector = LectorQRSimple()
    lector.ejecutar()