# 🧪 Carpeta de Pruebas

Esta carpeta contiene el conjunto de pruebas, validaciones y prototipos desarrollados durante la construcción del robot móvil autónomo G7ACKER.

El objetivo principal de esta sección del proyecto fue verificar individualmente el funcionamiento de cada subsistema antes de integrarlos en la arquitectura final del robot.

Las pruebas incluyen:

- Comunicación serial
- Visión artificial
- Cámara Raspberry Pi
- Sensores
- Motores DC
- Encoders
- Servomotores
- Sensores ultrasónicos
- Sensores infrarrojos
- Finales de carrera

Esta metodología permitió desarrollar el sistema de manera modular, facilitando:

- Depuración
- Calibración
- Ajuste de parámetros
- Integración progresiva
- Validación de hardware

---

# 📂 Contenido de la carpeta

Dentro de esta carpeta se encuentran distintos scripts y programas de prueba utilizados durante el desarrollo del robot.

Los principales módulos evaluados fueron:

- Cámara y procesamiento de imagen
- Comunicación Raspberry ↔ ESP32
- Control de motores
- Lectura de sensores
- Movimiento del servomotor
- Medición de velocidad
- Detección de obstáculos

Cada archivo corresponde a una prueba específica del sistema.

---

# 📷 Prueba de Cámara

## `prueba_camara.py`

Este archivo implementa el sistema de visión artificial utilizado para detectar carriles y generar comandos de navegación para el robot.

El sistema utiliza:

- Picamera2
- OpenCV
- Flask
- Comunicación serial con ESP32

Las funciones principales incluyen:

- Captura de video en tiempo real
- Corrección automática de brillo
- Ajuste de color y saturación
- Detección de líneas amarillas
- Detección de bordes negros y rojos
- Cálculo del centro del carril
- Generación de comandos de movimiento

El sistema procesa la imagen utilizando espacios de color HSV y operaciones morfológicas para mejorar la estabilidad de detección.

Además, implementa un servidor Flask para visualizar el procesamiento desde el navegador en tiempo real.

---

# 📸 Captura de Imagen

## `foto_prueba.py`

Este script fue utilizado para verificar el funcionamiento básico de la cámara conectada a la Raspberry Pi.

El código realiza:

- Inicialización de Picamera2
- Captura de una fotografía
- Almacenamiento automático de la imagen

Esta prueba permitió validar:

- Conexión física de la cámara
- Configuración del sistema
- Funcionamiento del sensor
- Acceso desde Python

---

# 🔌 Pruebas de Comunicación Serial

## `prueba_comunicacion_esp32.ino`

Este programa implementa una prueba básica de recepción serial en el ESP32.

El sistema:

- Recibe caracteres enviados desde la Raspberry Pi
- Enciende o apaga el LED integrado
- Imprime mensajes en el monitor serial

Los comandos implementados son:

| Comando | Acción |
|---|---|
| `a` | Encender LED |
| `x` | Apagar LED |

Esta prueba permitió verificar:

- Comunicación USB serial
- Baudrate
- Recepción de datos
- Funcionamiento básico del ESP32

---

## `prueba_comunicacion_raspberry.py`

Este script permite enviar comandos manuales desde la Raspberry Pi utilizando el teclado.

El sistema:

- Lee teclas en tiempo real
- Envía caracteres mediante serial
- Permite controlar manualmente el robot

Los comandos disponibles son:

| Tecla | Acción |
|---|---|
| `a` | Adelante |
| `r` | Atrás |
| `d` | Detenido |
| `i` | Izquierda |
| `e` | Derecha |

Esta prueba fue utilizada para validar la integración entre Raspberry Pi y ESP32 antes de implementar navegación autónoma.

---

# 🔘 Prueba de Final de Carrera

## `prueba_final_carrera.py`

Este script implementa la lectura de un sensor de final de carrera conectado a la Raspberry Pi utilizando la librería `gpiozero`.

El sistema detecta:

- Activación del interruptor
- Liberación del interruptor

La prueba permitió validar:

- Lectura digital de entradas GPIO
- Eventos de interrupción
- Respuesta del sistema ante contacto físico

Este sensor se utiliza posteriormente para detectar posiciones límite y eventos mecánicos dentro del robot.

---

# 📡 Prueba de Sensor IR

## `prueba_ir.py`

Este archivo implementa la lectura directa de un sensor infrarrojo utilizando la librería `lgpio`.

El sistema realiza:

- Lectura continua del GPIO
- Visualización del estado lógico del sensor
- Monitoreo en tiempo real

La prueba permitió verificar:

- Funcionamiento del sensor IR
- Compatibilidad con Raspberry Pi 5
- Lectura digital estable

Este sensor se utiliza posteriormente para detección de objetos o activación de eventos específicos dentro del recorrido autónomo.

---

# ⚙️ Pruebas de Motores

## `prueba_motores_ppr.ino`

Este programa fue desarrollado para calcular los pulsos por revolución (PPR) de los encoders instalados en los motores DC.

El sistema:

- Hace girar el motor
- Cuenta pulsos mediante interrupciones
- Detiene la medición manualmente
- Muestra el total de pulsos registrados

Esta prueba permitió obtener los valores reales de calibración de los encoders.

---

## `prueba_motores_velocidad.ino`

Este archivo implementa el cálculo de:

- RPM
- Velocidad angular
- Velocidad lineal

Utilizando:

- Lectura de encoder
- Conversión matemática
- Medición temporal

Los resultados obtenidos fueron utilizados posteriormente para calibrar el sistema de control de movimiento del robot.

---

# 🎯 Prueba de Servomotor

## `prueba_servo.ino`

Este programa permite controlar manualmente el servomotor encargado de la dirección del robot.

El sistema recibe comandos seriales y posiciona el servo en distintos ángulos:

| Comando | Dirección |
|---|---|
| `d` | Centro |
| `s` | Derecha |
| `f` | Izquierda |

La prueba permitió:

- Calibrar ángulos
- Ajustar límites mecánicos
- Verificar estabilidad del servo

---

# 📏 Pruebas de Sensor Ultrasónico

## `prueba_ultrasonido_gpiozero.py`

Este script implementa medición de distancia utilizando la librería `gpiozero`.

El sistema:

- Calcula distancia en centímetros
- Detecta obstáculos
- Envía comandos seriales al ESP32

Comportamiento implementado:

| Distancia | Acción |
|---|---|
| ≤ 30 cm | Detener |
| > 30 cm | Avanzar |

Esta versión ofrece una implementación más sencilla y estable para Raspberry Pi.

---

## `prueba_ultrasonido_rpigpio.py`

Esta versión implementa la lectura manual del sensor ultrasónico utilizando `RPi.GPIO`.

El sistema controla directamente:

- Pulso TRIG
- Lectura ECHO
- Cálculo temporal del eco

Esta prueba permitió comprender el funcionamiento interno del sensor HC-SR04 y validar mediciones manuales.

---

# 🧩 Metodología de Desarrollo

El desarrollo del robot se realizó mediante una estrategia modular basada en pruebas individuales.

Cada subsistema fue validado de forma independiente antes de integrarse en el sistema principal.

Esta metodología permitió:

- Reducir errores
- Aislar fallos
- Ajustar parámetros
- Validar hardware
- Mejorar estabilidad del sistema final

---

# 🚀 Función dentro del proyecto

La carpeta de pruebas representa el proceso experimental y de validación utilizado durante el desarrollo del robot móvil autónomo G7ACKER.

Gracias a estas pruebas fue posible:

- Diseñar el sistema final
- Calibrar sensores
- Ajustar motores
- Validar comunicación
- Construir la arquitectura autónoma del robot

Cada archivo refleja una etapa importante dentro del proceso de desarrollo e integración del sistema robótico.