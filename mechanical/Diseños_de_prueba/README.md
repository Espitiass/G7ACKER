# 🧪 Diseños de prueba

Esta carpeta contiene los primeros prototipos mecánicos y modelos experimentales desarrollados durante la etapa inicial del robot móvil **G7ACKER**.

El objetivo principal de esta sección fue validar diferentes conceptos mecánicos antes de implementar las versiones finales utilizadas en el robot.

Durante esta etapa se realizaron pruebas relacionadas con:

- Diseño del chasis
- Sistema de dirección
- Soportes de cámara
- Integración de ruedas
- Mecanismos Ackerman
- Sistema de tracción
- Distribución estructural

Cada subcarpeta contiene archivos de diseño CAD y modelos para impresión 3D.

---

# 📂 Estructura de archivos

Dentro de cada subcarpeta se incluyen principalmente dos tipos de archivos:

| Extensión | Descripción |
|---|---|
| `.f3d` | Archivo de diseño editable de Autodesk Fusion 360 |
| `.stl` | Archivo de malla 3D utilizado para impresión 3D |

Los archivos `.f3d` permiten modificar y editar el diseño mecánico, mientras que los `.stl` corresponden a versiones listas para fabricación mediante impresión 3D.

---

# 📁 bases

La carpeta `bases` contiene los primeros diseños del chasis principal del robot.

Estos modelos fueron utilizados para evaluar:

- Tamaño general del robot
- Distribución de componentes
- Espacio para electrónica
- Ubicación de sensores
- Soporte estructural

## 📄 Archivos principales

| Archivo | Descripción |
|---|---|
| `base_piso_3_carga.f3d` | Diseño editable de la base principal |
| `base_piso_3_carga.stl` | Modelo STL para impresión 3D |
| `base_v1.f3d` | Primera versión experimental del chasis |
| `base_v1.stl` | Modelo STL correspondiente |

---

# 📁 Camara

La carpeta `Camara` contiene prototipos iniciales del sistema de soporte para la cámara del robot.

Estos diseños permitieron realizar pruebas de:

- Ángulo de visión
- Altura de montaje
- Estabilidad mecánica
- Integración con la Raspberry Pi

## 📄 Archivos principales

| Archivo | Descripción |
|---|---|
| `base_camara.f3d` | Diseño base del soporte de cámara |
| `base_camara.stl` | Modelo imprimible del soporte |
| `pilar_camara.f3d` | Soporte vertical de la cámara |
| `pilar_camara.stl` | Modelo STL del pilar |

---

# 📁 direccion_v1

La carpeta `direccion_v1` contiene la primera versión funcional del sistema de dirección mecánica del robot.

Este diseño se basó en un mecanismo tipo Ackerman para mejorar la estabilidad de giro y el control de trayectoria.

Durante esta etapa se desarrollaron componentes como:

- Acoples de rueda
- Barras de dirección
- Engranajes
- Soportes Ackerman
- Piñones
- Brazos de dirección
- Integración con servomotor

## 📄 Componentes principales

| Componente | Función |
|---|---|
| `ACOPLE_RUEDA_*` | Acople mecánico entre rueda y sistema de dirección |
| `BARRA_DIRECCION` | Transmisión del movimiento de giro |
| `BARRA_SERVO` | Conexión mecánica con el servomotor |
| `BRAZO_DIRECCION` | Brazo articulado de dirección |
| `ENGRANAJE_BRAZO` | Sistema de transmisión mecánica |
| `PIÑON_SERVO` | Piñón conectado al servomotor |
| `SOPORTE_ACKERMAN_BASE` | Base estructural del mecanismo Ackerman |

Cada componente incluye su versión editable `.f3d` y su modelo `.stl`.

---

# 📁 direccion_v2

La carpeta `direccion_v2` contiene una segunda iteración del sistema de dirección, desarrollada para mejorar:

- Precisión del giro
- Resistencia estructural
- Estabilidad mecánica
- Integración entre ruedas y servo

En esta versión se realizaron ajustes sobre:

- Barras superiores
- Pilares laterales
- Acoples mecánicos
- Unión de dirección

## 📄 Componentes principales

| Componente | Función |
|---|---|
| `ACOPLE_RUEDA_PILAR` | Unión entre rueda y soporte vertical |
| `BARRA_DIRECCION_V2` | Segunda versión de la barra de dirección |
| `BARRA_UNION_INFERIOR` | Unión estructural inferior |
| `BARRA_UNION_SUPERIOR` | Unión estructural superior |
| `PILAR_DER` | Pilar lateral derecho |
| `PILAR_IZQ` | Pilar lateral izquierdo |

Todos los archivos se encuentran disponibles tanto en formato editable `.f3d` como en formato imprimible `.stl`.

---

# 📁 traccion_v1

La carpeta `traccion_v1` contiene los primeros diseños relacionados con el sistema de tracción del robot.

Estos modelos fueron utilizados para probar:

- Montaje de motores
- Integración de ruedas
- Distribución de fuerza
- Soporte mecánico de transmisión

## 📄 Archivos

| Archivo | Descripción |
|---|---|
| `traccion_v1.md` | Documento descriptivo del sistema de tracción |

---

# 🛠️ Fabricación de piezas

Los modelos STL incluidos en esta carpeta fueron diseñados para fabricación mediante impresión 3D utilizando tecnología FDM.

Esto permitió:

- Construcción rápida de prototipos
- Modificación iterativa de diseños
- Validación física de componentes
- Reducción de costos de desarrollo

---

# ⚙️ Flujo de desarrollo

El proceso de diseño mecánico siguió una metodología iterativa basada en:

1. Diseño CAD en Fusion 360.
2. Exportación de modelos STL.
3. Impresión 3D de prototipos.
4. Ensamble mecánico.
5. Pruebas físicas.
6. Correcciones estructurales.
7. Desarrollo de nuevas versiones.

Las diferentes versiones almacenadas en esta carpeta reflejan la evolución del sistema mecánico del robot G7ACKER.

---

# 🚀 Importancia dentro del proyecto

Los diseños de prueba permitieron validar el comportamiento mecánico del robot antes de fabricar la versión final del sistema.

Gracias a esta etapa fue posible:

- Detectar fallas mecánicas tempranas
- Mejorar la estabilidad
- Optimizar el sistema de dirección
- Ajustar dimensiones estructurales
- Facilitar la integración electrónica

Esta fase fue fundamental para el desarrollo exitoso del robot móvil autónomo G7ACKER.