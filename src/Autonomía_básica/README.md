# 🤖 Autonomía Básica

Esta carpeta contiene el desarrollo del sistema de **autonomía básica del robot móvil G7ACKER**, encargado del seguimiento de líneas, detección de obstáculos, lectura de códigos QR/AprilTags y toma de decisiones dentro de la pista.

Aquí se encuentran las diferentes versiones del sistema autónomo implementadas durante el desarrollo del proyecto, permitiendo observar la evolución desde las primeras pruebas funcionales hasta la arquitectura final de navegación.

El objetivo principal de esta sección es integrar los módulos de:

- Visión artificial
- Seguimiento de carriles
- Detección de obstáculos
- Comunicación con el ESP32
- Navegación autónoma
- Toma de decisiones basada en señales visuales

---

# 📂 Estructura de la carpeta

La carpeta se divide en dos versiones principales del sistema:

- `V1/` → Primera versión funcional del sistema autónomo.
- `V2/` → Versión final e integrada de autonomía básica.

---

# 🔹 V1 — Primera versión funcional

La carpeta `V1` contiene la primera implementación estable del sistema de autonomía básica del robot.

Esta versión se enfocó principalmente en:

- Seguimiento de líneas mediante visión artificial.
- Detección de obstáculos usando sensor ultrasónico.
- Comunicación serial con el ESP32.
- Visualización del procesamiento en tiempo real mediante Flask.

---

## ⚙️ Funcionalidades implementadas en V1

### 👁️ Detección de carriles

El sistema utiliza una cámara conectada a la Raspberry Pi para capturar imágenes en tiempo real y detectar las líneas de navegación presentes en la pista.

Para ello se implementaron técnicas de procesamiento de imagen utilizando OpenCV:

- Conversión a espacio de color HSV.
- Aplicación de máscaras por color.
- Filtrado morfológico.
- Detección de contornos.
- Cálculo dinámico del centro del carril.

El algoritmo identifica las líneas izquierda y derecha de la pista y calcula el error respecto al centro de la imagen para corregir la trayectoria del robot.

---

### 📡 Detección de obstáculos

Se integró un sensor ultrasónico conectado a la Raspberry Pi mediante GPIO para detectar obstáculos frente al robot.

El sistema realiza múltiples lecturas consecutivas para reducir ruido y falsas detecciones.

Cuando un objeto es detectado a una distancia menor al umbral establecido:

- El robot detiene inmediatamente su movimiento.
- Se bloquea el envío de comandos de avance.
- Se muestra el estado del sensor en el stream de video.

---

### 🔌 Comunicación serial con ESP32

La Raspberry Pi envía comandos de movimiento al ESP32 mediante comunicación serial USB.

Los comandos implementados permiten:

- Avanzar
- Girar a la izquierda
- Girar a la derecha
- Detener el robot

Esta arquitectura divide el sistema en:

- Raspberry Pi → procesamiento y toma de decisiones.
- ESP32 → ejecución de movimiento y control de motores.

---

### 📺 Streaming en tiempo real

La versión V1 implementa un servidor Flask para visualizar el procesamiento de imagen en tiempo real desde cualquier navegador conectado a la red local.

El stream incluye:

- Detección de líneas
- Contornos encontrados
- Centro del carril
- Estado del ultrasonido
- Dirección actual
- Comando enviado

Esto permitió facilitar el proceso de depuración y ajuste del sistema autónomo.

---

# 🔹 V2 — Versión final de autonomía básica

La carpeta `V2` contiene la arquitectura final del sistema autónomo del robot.

Esta versión integra:

- Seguimiento de líneas
- Detección de obstáculos
- Lectura de QR / AprilTags
- Máquina de estados
- Navegación por estaciones
- Comunicación entre procesos
- Control inteligente de recorrido

La arquitectura fue separada en múltiples módulos para mejorar:

- Organización del código
- Escalabilidad
- Mantenimiento
- Depuración

---

# 📄 main.py

El archivo `main.py` actúa como el núcleo principal del sistema autónomo.

Su función es:

- Inicializar el sistema.
- Crear procesos independientes.
- Gestionar la comunicación entre módulos.
- Ejecutar el sistema de navegación.

Para ello se implementa `multiprocessing`, permitiendo ejecutar distintos procesos simultáneamente sin bloquear el procesamiento de cámara.

---

## 🔄 Comunicación entre procesos

El sistema utiliza colas (`Queue`) para compartir información entre módulos:

- `qr_queue` → IDs detectados.
- `action_queue` → acciones de movimiento.
- `line_status_queue` → estado de detección de líneas.
- `status_queue` → información general del robot.

Esta arquitectura modular facilita el intercambio de información entre los distintos componentes del sistema autónomo.

---

# 📄 motor_control.py

El archivo `motor_control.py` es el encargado del procesamiento principal relacionado con:

- Visión artificial
- Seguimiento de línea
- Lectura de QR
- Detección de obstáculos
- Comunicación serial
- Streaming del sistema

Este módulo constituye el núcleo de percepción del robot.

---

## 👁️ Seguimiento de línea

El sistema detecta líneas de color mediante OpenCV utilizando máscaras HSV y análisis de contornos.

A partir de la posición del carril detectado se calcula el error respecto al centro de la imagen para decidir:

- Avanzar
- Girar a la izquierda
- Girar a la derecha
- Detenerse

---

## 📷 Lectura de QR y AprilTags

La versión V2 incorpora un sistema de lectura de QR/AprilTags utilizado para identificar estaciones y tomar decisiones dentro de la pista.

El sistema:

- Detecta marcos visuales.
- Se aproxima automáticamente.
- Captura la región de interés.
- Decodifica el identificador.
- Envía la información al módulo lógico.

Esto permite que el robot navegue de forma autónoma según el recorrido establecido.

---

## 📡 Sensor ultrasónico

El módulo también integra el sensor ultrasónico para detener el robot ante obstáculos cercanos.

La prioridad del sensor es superior al seguimiento de línea, por lo que cualquier detección bloquea inmediatamente el movimiento del robot.

---

## 📺 Visualización y depuración

El sistema genera un stream de video en tiempo real mostrando:

- Estado actual
- Carriles detectados
- Detección de QR
- Comandos enviados
- Distancia detectada
- Variables internas del sistema

Esto facilita el monitoreo del comportamiento autónomo durante las pruebas.

---

# 📄 qr_logic.py

El archivo `qr_logic.py` contiene la lógica de navegación y toma de decisiones del robot.

Este módulo implementa una máquina de estados encargada de interpretar los IDs detectados y decidir el comportamiento del robot dentro de la pista.

---

# 🧠 Máquina de estados

La lógica del sistema se organiza mediante estados secuenciales que representan cada etapa del recorrido.

Algunos estados implementados son:

- Espera de carga
- Espera de objetivo
- Espera de giro
- Espera de descarga
- Fin de recorrido

Cada transición depende de:

- IDs detectados
- Sensores
- Estado del robot
- Posición dentro de la pista

---

# 🗺️ Mapa de tags

El sistema utiliza un diccionario (`MAPA_TAGS`) donde cada ID representa una acción o estación específica.

Por ejemplo:

- Estaciones de carga
- Estaciones de descarga
- Intersecciones
- Direcciones de giro
- Finales de recorrido

Esto permite modificar el comportamiento del robot simplemente cambiando la configuración lógica de los tags.

---

# 📡 Integración de sensores

Además de la visión artificial, este módulo integra:

- Sensor infrarrojo
- Final de carrera
- Estado de líneas detectadas

La combinación de sensores permite aumentar la confiabilidad del sistema de navegación autónoma.

---

# ⚙️ Arquitectura modular

La versión V2 fue desarrollada siguiendo una arquitectura modular distribuida, donde cada archivo cumple una función específica dentro del sistema.

Esto permite:

- Escalar funcionalidades.
- Modificar módulos sin afectar el resto del sistema.
- Facilitar pruebas individuales.
- Mejorar la mantenibilidad del proyecto.

---

# 🚀 Evolución del sistema

La transición de V1 a V2 representa la evolución del robot desde un sistema básico de seguimiento de líneas hasta una plataforma de navegación autónoma capaz de:

- Interpretar señales visuales.
- Tomar decisiones.
- Navegar entre estaciones.
- Gestionar recorridos.
- Integrar múltiples sensores.
- Coordinar distintos procesos simultáneamente.

Esta arquitectura constituye la base del sistema autónomo implementado en el robot móvil G7ACKER.