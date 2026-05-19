# 📁 Carpeta de Código Fuente 

En esta carpeta se encuentra el **código fuente del robot móvil autónomo G7ACKER**, desarrollado para implementar las funcionalidades principales de **control, percepción, comunicación y pruebas del sistema**.

Aquí se almacenan los diferentes scripts utilizados durante el desarrollo del proyecto, incluyendo módulos de control de hardware, visión artificial, comunicación serial y pruebas individuales de componentes.

El objetivo de esta carpeta es **centralizar todo el software del sistema**, permitiendo organizar, modificar y escalar el desarrollo del robot de manera estructurada.

---

# 🧩 Estructura del proyecto

La organización del código se divide en diferentes módulos según la funcionalidad desarrollada dentro del robot.

---

## 🤖 Autonomía_básica/

Esta carpeta contiene los algoritmos relacionados con la **navegación autónoma básica del robot**, incluyendo seguimiento de carriles, detección de obstáculos y toma de decisiones sobre la pista.

La carpeta se divide en dos versiones principales:

### 📂 V1/

Contiene la primera versión funcional del sistema de autonomía básica del robot.

En esta etapa se desarrollaron e integraron:

- Seguimiento de líneas o carriles.
- Detección de obstáculos mediante sensor ultrasónico.
- Control básico de desplazamiento autónomo.

Esta versión representa la primera implementación estable de navegación autónoma sobre pista.

---

### 📂 V2/

Corresponde a la versión más reciente y estructurada del sistema de autonomía básica.

Esta versión divide las funciones principales del robot en diferentes módulos:

- `main.py`  
  Archivo principal encargado de iniciar y coordinar la ejecución del sistema.

- `motor_control.py`  
  Gestiona el control de movimiento del robot, la activación de motores y la comunicación con la ESP32.

- `qr_logic.py`  
  Procesa la información obtenida mediante lectura de códigos QR y toma decisiones de navegación dentro de la pista.

Esta estructura modular permite separar la lógica de navegación, percepción y control, facilitando la organización y escalabilidad del proyecto.

---

## ⚙️ Control_de_motores/

Esta carpeta contiene el código desarrollado para el control de los motores y actuadores del robot desde la ESP32.

Aquí se encuentra la versión final del sistema de control:

- `control_1.2.cpp`

Este código es el encargado de:

- Recibir las instrucciones enviadas desde la Raspberry Pi 5.
- Interpretar los comandos de movimiento.
- Controlar los motores mediante señales enviadas al driver.
- Ejecutar acciones como avance, retroceso, giros y detención del robot.

Además, dentro de esta carpeta se encuentran versiones previas y pruebas realizadas durante el desarrollo del sistema de control.

---

## 🧪 Pruebas/

Esta carpeta contiene todas las pruebas realizadas de manera independiente sobre sensores, actuadores y sistemas de comunicación del robot.

El objetivo de estas pruebas es:

- Validar el funcionamiento individual de cada componente.
- Detectar errores antes de integrar los módulos al sistema principal.
- Facilitar la depuración del hardware y software.
- Comprobar estabilidad y comunicación entre dispositivos.

Dentro de esta carpeta se incluyen pruebas relacionadas con:

### 📷 Cámara
Pruebas de captura de imagen, procesamiento y funcionamiento de la cámara.

### 🔌 Comunicación serial
Pruebas de comunicación entre Raspberry Pi y ESP32.

### 📡 Sensores
Pruebas individuales de sensores ultrasónicos, sensores IR y finales de carrera.

### ⚙️ Motores
Pruebas de velocidad, RPM, encoders y control de motores.

### 🔄 Servo motores
Pruebas de funcionamiento y posicionamiento del servomotor.

### 🏁 Integración final
Pruebas completas del comportamiento del robot sobre la pista.

---

# ⚙️ Organización del código

El proyecto sigue un enfoque de desarrollo **modular**, donde cada archivo cumple una función específica dentro del sistema general del robot.

Esta metodología permite:

- Facilitar la comprensión del sistema.
- Mejorar la depuración del código.
- Integrar nuevas funcionalidades sin afectar otros módulos.
- Mantener un desarrollo organizado y escalable.
- Favorecer el trabajo colaborativo dentro del equipo.

Además, se manejan múltiples versiones y pruebas progresivas para validar el funcionamiento del robot antes de integrar cada componente al sistema principal.

---

# 🚀 Desarrollo continuo

El proyecto se encuentra en constante evolución, por lo que esta carpeta seguirá creciendo con nuevos módulos y mejoras relacionadas con:

- Navegación autónoma
- Visión artificial
- Integración de sensores
- Comunicación entre sistemas
- Optimización de control
- Automatización de decisiones
- Mejora del rendimiento general del robot

Por esta razón, el contenido de esta carpeta puede actualizarse continuamente a medida que avance el desarrollo del robot móvil autónomo G7ACKER.