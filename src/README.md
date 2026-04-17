# 📁 Carpeta de Código Fuente 

En esta carpeta se encuentra el **código fuente del robot móvil autónomo G7ACKER**, desarrollado para implementar las funcionalidades principales de **control, percepción, comunicación y pruebas del sistema**.

Aquí se almacenan los diferentes scripts utilizados durante el desarrollo del proyecto, incluyendo módulos de control de hardware, visión artificial, comunicación serial y pruebas individuales de componentes.

El objetivo de esta carpeta es **centralizar todo el software del sistema**, permitiendo organizar, modificar y escalar el desarrollo del robot de manera estructurada.

---

## 🧩 Estructura del proyecto 

La organización del código se divide en los siguientes módulos:

### 🔧 Control_de_motores/

Contiene el código relacionado con el control de actuadores del robot.

**Subcarpetas:**

- `Prueba_motores/`
  - `PPR.cpp` → Cálculo de pulsos por revolución.
  - `RPM.cpp` → Medición de velocidad de los motores.

- `Prueba_servo/`
  - `prueba_servo.cpp` → Pruebas de funcionamiento del servomotor.

**Archivos principales:**
- `control_1.cpp`
- `control_1.1.cpp`
- `control_1.2.cpp`  
  → Versiones del sistema de control del robot.

- `control_teclado.cpp`  
  → Control manual mediante entrada por teclado.

---

### 👁️ Vision_artificial/

Contiene los módulos de percepción y navegación autónoma.

#### 📂 Autonomía_basica/

**V1 (primeras pruebas):**
- `Detencion_de_line.py` → Detección de línea.
- `Detencion_obstaculos.py` → Detección básica de obstáculos.
- `det.py` → Script auxiliar de detección.
- `detencion_distancia.py` → Detección basada en distancia.

**V2 (versiones mejoradas):**
- `obstaculo_1.py`
- `obstaculo_1.1.py`
- `obstaculo_2.py`
- `obstaculo_2.1.py`  
→ Algoritmos mejorados de detección y evasión de obstáculos.

---

### 🔌 Comunicación_serial/

Módulos encargados de la comunicación entre la **Raspberry Pi y el ESP32**.

- `com_rasp_esp.cpp` → Comunicación desde el ESP32.
- `comunicacion_rasp.py` → Comunicación desde Raspberry Pi.
- `prueba_serial.py` → Pruebas de envío y recepción de datos.

---

### 📷 Prueba_camara/

Scripts para pruebas con la cámara.

- `prueba_camara.py` → Captura de imagen.
- `pru_cam_con_serial.py` → Integración cámara + comunicación serial.
- `servidor.py` → Streaming o servidor de cámara.

---

### 📡 Prueba_ultrasonico/

Código relacionado con sensores de distancia.

- `ultra_sonico.py` → Lectura del sensor ultrasónico.
- `prueba_ultra_sonico.py` → Pruebas básicas.
- `codigo_camara_ultra.py` → Integración cámara + sensor ultrasónico.

---

## ⚙️ Organización del código 

El código del proyecto se desarrolla siguiendo un enfoque **modular**, donde cada archivo cumple una función específica dentro del sistema.  

Además, se trabaja con múltiples versiones de prueba (V1, V2, control_1.x), lo que permite mejorar progresivamente cada componente sin afectar el resto del sistema.

Esta organización facilita:

- La comprensión del funcionamiento del robot.
- La depuración y mejora del código.
- La integración de nuevas funcionalidades.
- El trabajo colaborativo dentro del equipo.

---

## 🚀 Desarrollo continuo 

Dado que el proyecto se encuentra en constante evolución, esta carpeta seguirá creciendo con nuevos módulos relacionados con:

- Control del robot
- Visión artificial avanzada
- Navegación autónoma
- Integración de sensores
- Comunicación entre sistemas
- Optimización del rendimiento

Por esta razón, el contenido de esta carpeta puede actualizarse a medida que el desarrollo del robot avance.