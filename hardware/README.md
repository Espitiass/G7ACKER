# Diseño Electrónico

Esta carpeta contiene el desarrollo del sistema electrónico del robot G7ACKER, incluyendo el diseño del esquemático y la PCB utilizada para la integración del sistema.

---

## Estructura

```text
hardware/
│── esquematico/
│── pcb/
```

---

## Contenido

### Esquemático

Incluye la representación del sistema electrónico antes de su implementación física:

* Imagen del esquemático por medio de ilustración en el sofware DRAW.IO (formato PNG) para visualización rápida
* Archivo original del esquemático (formato `.sch`) con todas las conexiones y componentes definidos

Este diseño permite validar la correcta interconexión de los módulos antes de avanzar al diseño de la PCB.

---

### PCB

Contiene el diseño final de la placa electrónica:

* Archivo de la PCB con ruteo completo (formato `.f3z`, Fusion 360)
* Modelo 3D de la PCB (formato `.brd`)

Este diseño corresponde a la versión enviada a fabricación, incluyendo:

* Rutas eléctricas
* Distribución de componentes
* Integración del sistema completo

---

## Propósito

* Documentar el diseño electrónico del sistema
* Facilitar la fabricación de la PCB
* Permitir la revisión y modificación del circuito
* Servir como base para futuras iteraciones

---

## Notas

* Mantener consistencia entre esquemático y PCB
* Verificar nombres de componentes y conexiones
* Evitar modificaciones directas sobre versiones finales sin control
