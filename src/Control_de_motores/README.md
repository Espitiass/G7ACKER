# ⚙️ Control de Motores

Esta carpeta contiene el desarrollo del sistema de **control de movimiento del robot móvil G7ACKER**, implementado sobre un microcontrolador ESP32.

El objetivo principal de este módulo es recibir las instrucciones enviadas desde la Raspberry Pi y convertirlas en acciones físicas sobre el robot, controlando:

- Motores de tracción
- Dirección del sistema
- Velocidad de desplazamiento
- Lectura de encoders
- Control PWM
- Servomotor de dirección

Este sistema constituye la capa de ejecución del robot, encargada de transformar las decisiones del sistema autónomo en movimiento real.

---

# 📂 Contenido de la carpeta

Dentro de esta carpeta se encuentran distintas versiones y pruebas relacionadas con el control de motores del robot.

La versión principal y final utilizada en el proyecto corresponde a:

- `control_1.2.cpp`

Además, se incluyen archivos de prueba y calibración utilizados durante el desarrollo.

---

# 📄 control_1.2.cpp

El archivo `control_1.2.cpp` corresponde a la versión final del sistema de control implementado en el ESP32.

Este código se encarga de:

- Recibir comandos desde la Raspberry Pi mediante comunicación serial.
- Controlar los motores DC del robot.
- Gestionar el movimiento diferencial.
- Accionar el servomotor de dirección.
- Leer encoders para medición de velocidad.
- Ejecutar el control de tracción del robot.

---

# 🔌 Comunicación con Raspberry Pi

El ESP32 recibe comandos enviados desde la Raspberry Pi mediante comunicación serial USB.

Los comandos implementados son:

| Comando | Acción |
|---|---|
| `a` | Avanzar |
| `i` | Girar izquierda |
| `d` | Girar derecha |
| `x` | Detener |

Cada instrucción es interpretada por el ESP32 para ejecutar el movimiento correspondiente sobre el sistema de tracción.

Esta arquitectura permite separar:

- Raspberry Pi → procesamiento y toma de decisiones.
- ESP32 → control físico de actuadores.

---

# 🚗 Sistema de movimiento

El robot utiliza un sistema de tracción diferencial compuesto por:

- Dos motores DC con caja reductora.
- Driver de potencia.
- Control PWM independiente para cada motor.

El código controla de manera individual ambos motores para generar:

- Movimiento frontal
- Correcciones de trayectoria
- Giros
- Frenado

---

# ⚡ Control PWM

La velocidad de los motores se regula mediante señales PWM generadas por el ESP32.

El sistema utiliza:

- Canal PWM independiente para cada motor.
- Frecuencia configurada a 5 kHz.
- Resolución de 8 bits.

Esto permite controlar la velocidad del robot de manera eficiente y suave.

---

# 📏 Calibración de motores

Debido a diferencias mecánicas entre motores, se implementaron ecuaciones de calibración independientes para cada lado del sistema de tracción.

Estas ecuaciones permiten compensar diferencias de velocidad y mantener un desplazamiento más estable y recto.

El sistema utiliza constantes de ajuste para:

- Motor izquierdo
- Motor derecho

De esta manera se mejora la precisión del movimiento autónomo del robot.

---

# 🔄 Control diferencial

El movimiento del robot se implementa mediante lógica diferencial.

Dependiendo del comando recibido:

- Ambos motores avanzan.
- Un motor se detiene.
- Se generan correcciones de dirección.

Esto permite realizar giros y ajustes de trayectoria sin necesidad de mecanismos complejos de dirección.

---

# 🎯 Control del servomotor

El sistema incorpora un servomotor encargado de modificar la dirección mecánica del robot.

El servo se posiciona según el movimiento solicitado:

| Dirección | Ángulo aproximado |
|---|---|
| Centro | 90° |
| Derecha | 150° |
| Izquierda | 30° |

El código evita movimientos innecesarios del servo utilizando una variable de control que detecta cambios de dirección.

Esto reduce vibraciones y mejora la estabilidad mecánica.

---

# 📡 Lectura de encoders

El sistema utiliza encoders para medir la velocidad de rotación de los motores.

Las señales de encoder son capturadas mediante interrupciones del ESP32 para obtener:

- Pulsos por revolución (PPR)
- RPM
- Velocidad lineal aproximada

Esto permite monitorear el comportamiento real de los motores durante el desplazamiento.

---

# ⚙️ Arquitectura del sistema

El código fue desarrollado utilizando una estructura modular basada en funciones independientes para:

- Movimiento de motores
- Frenado
- Control PWM
- Lectura de encoders
- Movimiento del servo
- Aplicación de trayectorias

Esta organización facilita:

- Mantenimiento del código
- Escalabilidad
- Pruebas individuales
- Depuración del sistema

---

# 🧪 Desarrollo y pruebas

Durante el desarrollo se realizaron múltiples pruebas relacionadas con:

- Control de velocidad
- Estabilidad del movimiento
- Respuesta del servo
- Comunicación serial
- Medición de RPM
- Ajuste de PWM
- Corrección de trayectoria

Las distintas versiones del código reflejan el proceso iterativo de mejora del sistema de locomoción.

---

# 🚀 Función dentro del robot

Este módulo representa la capa de ejecución física del robot móvil G7ACKER.

Mientras la Raspberry Pi procesa información del entorno y toma decisiones autónomas, el ESP32 ejecuta dichas acciones controlando directamente los actuadores del sistema.

La integración entre ambos dispositivos permite implementar un sistema robótico distribuido, modular y escalable.