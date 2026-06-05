# 🤖 G7ACKER - Robot Móvil Autónomo con Visión Artificial

Sistema de robot móvil con conducción autónoma basado en visión artificial, diseñado para navegación en entornos estructurados mediante seguimiento de carril, detección de obstáculos y dirección tipo Ackermann.

---

# 📖 Descripción del Proyecto

El proyecto consiste en el desarrollo de un robot móvil autónomo que integra procesamiento visual, sensores de proximidad y control embebido distribuido para lograr un desplazamiento inteligente sin intervención humana.

El sistema está orientado a simular escenarios reales de movilidad autónoma, como vehículos terrestres a pequeña escala que operan sobre carriles definidos.

El enfoque del proyecto combina:

- Visión artificial para percepción del entorno
- Detección de estaciones mediante sensor infrarrojo
- Control distribuido (Raspberry Pi + ESP32)
- Sistema de dirección tipo Ackermann

---

# 🎥 Demo del Sistema

## Funcionamiento del robot

> *(Agregar imágenes, GIF o enlace de video del funcionamiento)*

---

# 🔄 Flujo del Sistema

```text
[Cámara IMX219]
        ↓
[Procesamiento en Raspberry Pi (OpenCV)]
        ↓
[Decisiones de navegación]
        ↓
[ESP32]
        ↓
[Driver TB6612FNG]
        ↓
[Motores JGY-370 + Servo MG90]
```

---

# 🛠️ Hardware del Sistema

## 🧠 Unidad de procesamiento

- Raspberry Pi 5
- ESP32

---

## 📡 Sensores

- Cámara IMX219 (visión artificial)
- Sensor ultrasónico HC-SR04 (detección frontal de obstáculos)
- 1 Sensor infrarrojo TCRT5000 (detección lateral de estaciones de carga y descarga)

---

## ⚙️ Actuadores

- 2 Motores DC JGY-370
- Servo motor MG90 (engranajes metálicos)

---

## 🚗 Sistema de dirección

- Configuración tipo Ackermann

---

## ⚡ Etapa de potencia

- Driver TB6612FNG Dual Motor

---

## 🔋 Alimentación

- Batería LiPo 7.4V – 5A
- Regulador XL4016 (salida a 5V, alta corriente)
- Regulador LM2596 (salida a 3.3V)

---

# 💻 Software y Tecnologías

| Tecnología | Uso |
|---|---|
| Python | Lógica principal y visión artificial |
| OpenCV | Procesamiento de imagen |
| ESP32 (C/C++) | Control embebido |
| Serial USB | Comunicación Raspberry Pi ↔ ESP32 |

---

# 📂 Estructura del Repositorio

```text
G7ACKER/
├── .vscode/                          # Configuración de Visual Studio Code
│   └── settings.json
│
├── docs/                             # Documentación del proyecto
│   ├── acta_constitucion/
│   ├── bitacoras/
│   ├── imagenes/
│   ├── matriz_control_de_documentos/
│   ├── poster/
│   ├── presentacion_final/
│   └── README.md
│
├── hardware/                         # Diseño electrónico y PCB
│   ├── esquematico/
│   ├── pcb/
│   └── README.md
│
├── mechanical/                       # Diseño mecánico y estructural
│   ├── Diseños_de_prueba/
│   ├── Diseños_finales/
│   └── README.md
│
├── src/                              # Código fuente
│   ├── Autonomía_básica/
│   ├── Control_de_motores/
│   ├── Pruebas/
│   └── README.md
│
├── .gitignore
├── LICENSE
├── README.md
├── Scriptsactivate
└── test.jpg
```

---

# 📊 Estado del Proyecto

| Módulo | Estado |
|---|---|
| Diseño electrónico | ✅ Completado |
| PCB | ✅ Fabricada y operativa |
| Sistema mecánico | ✅ Completado |
| Visión artificial | ✅ Integrada y funcional |
| Control autónomo | 🧪 Pruebas finales |

---

# 👥 Autores

| Integrante | Área |
|---|---|
| Sofía Salomé Espitia Jiménez | Área de diseño |
| Vanesa Galeano Franco | Área de programación |
| Julián Andrés García Correa | Área eléctrica y electrónica |
| Jose Lisander Hurtado Castañeda | Área mecánica |

---

# 📄 Licencia

Este proyecto se distribuye bajo la licencia MIT License.
