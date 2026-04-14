# Dirección

El sistema de **dirección del robot** fue diseñado utilizando **Autodesk Fusion 360**, con el objetivo de implementar un mecanismo de giro preciso que permita orientar las ruedas delanteras del robot durante su desplazamiento.

Para este proyecto se estableció un sistema de **dirección tipo Ackermann**, ampliamente utilizado en vehículos terrestres debido a su capacidad de reducir el deslizamiento lateral de las ruedas durante los giros. Este tipo de mecanismo permite que cada rueda del eje delantero describa un radio de giro diferente, mejorando la eficiencia del movimiento y la estabilidad del robot.

El sistema de dirección es accionado mediante un **servo motor SG90**, el cual transmite el movimiento a través de un sistema de **piñón y engranaje**, permitiendo transformar el movimiento angular del servo en el desplazamiento del mecanismo de dirección.

Durante el proceso de diseño se modelaron todas las piezas del sistema dentro de **Fusion 360**, con el objetivo de verificar:

- Correcta integración entre componentes.
- Espacio suficiente para el movimiento de las piezas.
- Posibles interferencias mecánicas.
- Alineación adecuada del sistema de dirección.

Posteriormente, los componentes fueron **fabricados mediante impresión 3D**, lo cual permite obtener geometrías personalizadas y facilita la iteración rápida durante el proceso de desarrollo.

---

# SG90 Servo Motor

[Link al diseño en Fusion 360](https://a360.co/3P9kEA0)
![alt text](Imágenes/image-7.png)

El **servo motor SG90** es el actuador encargado de generar el movimiento del sistema de dirección.

Este tipo de servo es utilizado en este proyecto de robot de conducción autónoma debido a su:

- Bajo peso.
- Tamaño compacto.
- Facilidad de control mediante señales PWM.
- Buena relación entre torque y consumo energético.

Dentro del sistema de dirección, el servo transmite su movimiento rotacional a un **piñón**, el cual engrana con una rueda dentada de mayor diámetro. Este mecanismo permite **aumentar la precisión del movimiento y mejorar el control del ángulo de giro**.

El modelo del servo fue incluido dentro del entorno CAD con el propósito de **verificar su correcta integración mecánica con el resto del sistema**.

---

# Piñón Servo

[Link al diseño en Fusion 360](https://a360.co/4cQ5PMJ)
![alt text](Imágenes/image-8.png)

El **piñón del servo** es la pieza encargada de transmitir el movimiento rotacional del servo hacia el engranaje principal del sistema de dirección.

Este componente se fija directamente al eje del servo motor y engrana con la pieza llamada **Engranaje de brazo**, permitiendo transferir el movimiento de forma eficiente.

El diseño del piñón fue realizado considerando:

- El diámetro del eje del servo.
- El módulo del engranaje.
- La correcta alineación con el engranaje principal.

Esta pieza fue **fabricada mediante impresión en resina**, lo que permite ajustar con precisión las dimensiones necesarias para su correcta integración con el servo.

---

# Engranaje Brazo

[Link al diseño en Fusion 360](https://a360.co/4ux1Vie)
![alt text](Imágenes/image-9.png)

El **engranaje del brazo de dirección** es la pieza encargada de recibir el movimiento del piñón del servo y transmitirlo hacia el mecanismo de dirección.

Gracias a su mayor diámetro en comparación con el piñón, este engranaje permite:

- Aumentar la precisión del movimiento.
- Reducir la velocidad angular.
- Mejorar el control del sistema de dirección.

Este componente se encuentra conectado al **brazo de dirección**, el cual convierte el movimiento rotacional en desplazamiento lateral del sistema Ackermann. Esta pieza también fue **fabricada mediante impresión en resina.**

---

# Brazo Direccion

[Link al diseño en Fusion 360](https://a360.co/4ltEYrR)
![alt text](Imágenes/image-10.png)

El **brazo de dirección** es el elemento encargado de transmitir el movimiento proveniente del engranaje hacia las barras que controlan la orientación de las ruedas.

Su función principal es **transformar el movimiento rotacional del sistema de engranajes**, necesario para accionar el mecanismo Ackermann.

El diseño de esta pieza busca garantizar:

- Rigidez estructural.
- Correcta transmisión del movimiento.
- Compatibilidad con las barras de dirección.

---

# Barra Direccion

[Link al diseño en Fusion 360](https://a360.co/4lwSNpI)
![alt text](Imágenes/image-11.png)

La **barra de dirección** conecta ambos lados del sistema Ackermann, permitiendo que el movimiento generado por el brazo de dirección se transmita a las ruedas delanteras.

Esta barra es responsable de:

- Sincronizar el movimiento de las ruedas.
- Mantener la geometría correcta del sistema de dirección.
- Permitir que cada rueda gire en un ángulo diferente durante las curvas.

Este comportamiento es fundamental para el funcionamiento del **principio de dirección Ackermann**.

---

# Acople de la rueda con la barra derecha

[Link al diseño en Fusion 360](https://a360.co/40ZcX1X)
![alt text](Imágenes/image-12.png)

El **acople derecho** conecta la barra de dirección con el soporte de la rueda derecha.

Esta pieza permite transmitir el movimiento de la barra hacia la rueda, permitiendo modificar su orientación durante el giro.

El diseño fue optimizado para permitir:

- Libertad de movimiento.
- Buena transmisión de fuerzas.
- Integración sencilla con el resto del sistema.

---

# Acople de la rueda con la barra izquierda

[Link al diseño en Fusion 360](https://a360.co/4brRZOb)
![alt text](Imágenes/image-13.png)

El **acople izquierdo** cumple la misma función que el acople derecho, pero en el lado opuesto del sistema de dirección.

Este componente conecta la barra de dirección con la rueda izquierda, permitiendo que ambas ruedas se orienten correctamente durante los giros del robot.

El diseño de ambas piezas permite mantener la **simetría del sistema de dirección** y asegurar el correcto funcionamiento del mecanismo Ackermann.

---

# Soporte Ackerman a la base

[Link al diseño en Fusion 360](https://a360.co/4lu62Yf)
![alt text](Imágenes/image-15.png)

El **soporte del sistema Ackermann** es la pieza encargada de fijar el mecanismo de dirección a la base estructural del robot.

Su función principal es:

- Mantener la posición del sistema de dirección.
- Garantizar la estabilidad del mecanismo.
- Permitir el correcto alineamiento entre las piezas móviles.

Esta pieza actúa como interfaz estructural entre el sistema de dirección y el chasis del robot.

---

# Ensamblaje del sistema de dirección

[Link al diseño en Fusion 360](https://a360.co/3NeH8PA)
![alt text](Imágenes/image-14.png)

El sistema completo de dirección se obtiene mediante el **ensamblaje de todos los componentes descritos anteriormente**.

En primer lugar, el **servo motor SG90** se fija a la **base de dirección** mediante tornillos. Posteriormente, el **piñón del servo** se conecta al eje del servo y engrana con el **engranaje del brazo de dirección**, permitiendo transmitir el movimiento rotacional.

El **engranaje** se encuentra unido al **brazo de dirección**, el cual convierte el movimiento rotacional en un desplazamiento que acciona la **barra de dirección**.

Esta barra conecta los **acoples de las ruedas izquierda y derecha**, permitiendo que ambas ruedas giren simultáneamente cuando el servo cambia su posición.

Gracias a la geometría del mecanismo, las ruedas describen ángulos diferentes durante los giros, cumpliendo con el **principio de dirección Ackermann**, lo que mejora la estabilidad y reduce el deslizamiento de las ruedas.

El diseño modular del sistema permite **facilitar el ensamblaje, mantenimiento y futuras modificaciones del robot**, ya que cada componente puede ser reemplazado o ajustado sin afectar el resto del mecanismo.
