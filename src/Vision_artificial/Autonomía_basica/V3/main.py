#!/usr/bin/env python3
# main.py - Ejecuta el sistema de carril y el lector QR simultáneamente

import subprocess
import time
import signal
import sys
import os

class SistemaRobot:
    def __init__(self):
        self.procesos = []
        
    def iniciar_carril(self):
        """Iniciar el sistema de seguimiento de carril"""
        print("🚗 Iniciando sistema de seguimiento de carril...")
        try:
            proceso = subprocess.Popen(
                ['python3', 'carril_con_qr.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.procesos.append(('Carril', proceso))
            print("✅ Sistema de carril iniciado correctamente")
            return True
        except Exception as e:
            print(f"❌ Error al iniciar sistema de carril: {e}")
            return False
    
    def iniciar_qr(self):
        """Iniciar el lector QR"""
        print("📷 Iniciando lector QR...")
        try:
            proceso = subprocess.Popen(
                ['python3', 'qr_simple.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.procesos.append(('QR', proceso))
            print("✅ Lector QR iniciado correctamente")
            return True
        except Exception as e:
            print(f"❌ Error al iniciar lector QR: {e}")
            return False
    
    def detener_todos(self):
        """Detener todos los procesos"""
        print("\n🛑 Deteniendo todos los sistemas...")
        for nombre, proceso in self.procesos:
            print(f"  Deteniendo {nombre}...")
            try:
                proceso.terminate()
                proceso.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proceso.kill()
                print(f"  {nombre} detenido forzosamente")
            except:
                print(f"  Error al detener {nombre}")
        print("✅ Todos los sistemas detenidos")
    
    def monitorear(self):
        """Monitorear que los procesos sigan ejecutándose"""
        while True:
            for nombre, proceso in self.procesos:
                if proceso.poll() is not None:
                    print(f"⚠️ {nombre} se detuvo inesperadamente")
                    return False
            time.sleep(2)
        return True
    
    def ejecutar(self):
        """Ejecutar todos los sistemas"""
        print("=" * 50)
        print("🤖 ROBOT - SISTEMA DE NAVEGACIÓN")
        print("=" * 50)
        
        # Iniciar sistemas
        if not self.iniciar_carril():
            return
        
        time.sleep(2)  # Esperar que el servidor socket esté listo
        
        if not self.iniciar_qr():
            self.detener_todos()
            return
        
        print("\n" + "=" * 50)
        print("✅ SISTEMAS OPERATIVOS")
        print("📡 Stream de video: http://localhost:5000")
        print("🔍 Lector QR activo (presiona 'q' en ventana QR para cerrar)")
        print("🛑 Presiona Ctrl+C para detener todos los sistemas")
        print("=" * 50 + "\n")
        
        # Manejar señal de interrupción
        def signal_handler(sig, frame):
            print("\n\n⚠️ Señal de interrupción recibida")
            self.detener_todos()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Monitorear procesos
        try:
            self.monitorear()
        except KeyboardInterrupt:
            signal_handler(None, None)

if __name__ == "__main__":
    robot = SistemaRobot()
    robot.ejecutar()