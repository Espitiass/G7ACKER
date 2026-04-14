# G7ACKER - Robot Móvil Autónomo con Visión Artificial

Sistema de robot móvil con conducción autónoma basado en visión artificial, diseñado para navegación en entornos estructurados mediante seguimiento de carril, detección de obstáculos y dirección tipo Ackermann.

---

## Descripción del Proyecto

El proyecto consta del desarrolo de un robot móvil autónomo que integra procesamiento visual, sensores de proximidad y control embebido distribuido para lograr un desplazamiento inteligente sin intervención humana.

El sistema está orientado a simular escenarios reales de movilidad autónoma, como vehículos terrestres a pequeña escala que operan sobre carriles definidos.

El enfoque del proyecto combina:

* Visión artificial para percepción del entorno
* Sensado híbrido (ultrasonido + infrarrojo)
* Control distribuido (Raspberry Pi + ESP32)
* Sistema de dirección tipo Ackermann

---

## Demo del Sistema



![Robot](docs/images/robot.jpg)

---

### Flujo del sistema

```
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

## Hardware del Sistema

### Unidad de procesamiento

* Raspberry Pi 5
* ESP32

### Sensores

* Cámara IMX219 (visión artificial)
* Sensor ultrasónico HC-SR04 (detección frontal de obstáculos)
* 2 Sensores infrarrojos FC-51 (seguimiento de línea lateral)

### Actuadores

* 2 motores DC JGY-370
* Servo motor MG90 (engranajes metálicos)

### Sistema de dirección

* Configuración tipo Ackermann

### Etapa de potencia

* Driver TB6612FNG Dual Motor

### Alimentación

* Batería LiPo 7.4V – 5A
* Regulador XL4016 (salida a 5V, alta corriente)
* Regulador LM2596 (salida a 3.3V)

---

## Software y Tecnologías

* Lenguaje principal: Python
* Procesamiento de imagen: OpenCV
* Control embebido: ESP32 (C/C++)
* Comunicación: Serial USB

---

## Estructura del Repositorio

```
G7ACKER/
│── src/            # Código fuente
│── docs/           # Documentación e imágenes
│── hardware/       # Diseño electrónico y PCB
│── mechanical/     # Diseño estructural
│── README.md
```

---

## Estado del Proyecto

* Diseño electrónico completado
* PCB en fabricación
* Sistema mecánico en desarrollo
* Integración de visión artificial en progreso
* Implementación de control autónomo en desarrollo

---

## Autores

- **Sofía Salomé Espitia Jiménez** – Área de diseño  
- **Vanesa Galeano Franco** – Área de programación  
- **Julián Andrés García Correa** – Área eléctrica y electrónica  
- **Jose Lisander Hurtado Castañeda** – Área mecánica  

---

## Licencia

MIT License

---