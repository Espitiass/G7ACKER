# Tracción

El sistema de tracción del robot fue diseñado en **Autodesk Fusion 360**, con el objetivo de proporcionar un desplazamiento estable, eficiente y fácil de fabricar para un robot móvil terrestre de pequeña escala. 

La locomoción se basa en **dos motores con caja reductora JGY370**, acoplados a ruedas convencionales, lo que permite obtener un buen equilibrio entre torque y velocidad para el desplazamiento del robot en superficies planas.

Para el diseño del sistema se modelaron varios componentes en Fusion 360, los cuales posteriormente fueron **fabricados mediante corte láser o impresión 3D**, dependiendo de los requerimientos mecánicos de cada pieza.

El conjunto completo de estos componentes conforma el **sistema de tracción del robot**, el cual se ensambla sobre la base estructural principal.

---

## Base_Traccion
Link al diseño en Fusion 360: 

La **base de tracción** constituye la estructura principal sobre la cual se montan los demás componentes del sistema de locomoción. Su función es proporcionar una superficie rígida y estable para la fijación de los motores, soportes y demás elementos mecánicos.

Esta pieza fue diseñada considerando la distribución del peso del robot, la ubicación de los motores y el espacio necesario para otros componentes electrónicos.

La base fue **fabricada mediante corte láser**, lo que permite obtener una pieza precisa, ligera y resistente, además de facilitar la reproducción del diseño.

---

## GearBox + JGY370 + JGA25-370
Link al diseño en Fusion 360:

El **motorreductor JGY370** es el encargado de generar el movimiento del robot. Este tipo de motor integra una caja reductora que disminuye la velocidad del motor eléctrico y aumenta el torque disponible, lo cual resulta ideal para aplicaciones de robótica móvil.

El motor no fue diseñado dentro del proyecto, ya que corresponde a un componente comercial previamente fabricado y suministrado para el desarrollo del robot.

En el modelo de Fusion 360 se incluye su representación con el fin de **asegurar la correcta integración mecánica con los demás componentes del sistema de tracción**.

---

## Acople + motoreductor
Link al diseño en Fusion 360:

El **acople del motorreductor** fue diseñado para conectar el eje del motor con la rueda del sistema de tracción.

Su objetivo principal es **transmitir el movimiento rotacional del motor hacia la rueda de manera segura y alineada**, evitando deslizamientos o pérdidas de torque.

Este componente fue **fabricado mediante impresión 3D en filamento PLA**, lo que permitió adaptar el diseño exactamente al diámetro del eje del motor y al sistema de fijación de la rueda.

---

## Soporte de motor derecho
Link al diseño en Fusion 360:

El **soporte de motor derecho** tiene como función fijar el motorreductor al chasis del robot, manteniendo su posición correcta respecto a la base y a la rueda.

Este soporte fue diseñado para:
- Garantizar la alineación del eje del motor con la rueda.
- Reducir vibraciones durante el movimiento.
- Facilitar el montaje y desmontaje del motor.

La pieza fue **fabricada mediante impresión 3D en PLA**, lo que permitió crear una geometría adaptada al motor y al espacio disponible en el robot.

---

## Soporte de motor izquierdo
Link al diseño en Fusion 360:

El **soporte de motor izquierdo** cumple la misma función estructural que el soporte derecho, permitiendo la fijación del segundo motor del sistema de tracción.

Se diseñó como una pieza independiente para mantener la simetría del sistema de locomoción y asegurar que ambos motores queden correctamente posicionados respecto a la base del robot.

Al igual que el soporte derecho, esta pieza fue **fabricada mediante impresión 3D en filamento PLA**.

---

## Wheel (scaled)
Link al diseño en Fusion 360:

La **rueda del sistema de tracción** es el elemento encargado de transformar el movimiento rotacional del motor en desplazamiento del robot sobre el suelo.

Este componente corresponde a una rueda comercial que fue suministrada para el proyecto, por lo que no fue fabricada por el equipo.

En el modelo CAD se incluyó una representación escalada de la rueda con el objetivo de **verificar dimensiones, interferencias y correcta integración con el sistema de tracción**.

---

## Soporte LiPo
Link al diseño en Fusion 360:

El **soporte de la batería LiPo** fue diseñado para alojar de forma segura la batería que alimenta el sistema eléctrico del robot.

Su objetivo es:
- Mantener la batería fija durante el movimiento.
- Distribuir adecuadamente el peso dentro de la estructura.
- Facilitar el acceso para mantenimiento o reemplazo.

Este soporte será **fabricado mediante corte de material plano**, el cual posteriormente será ensamblado y fijado a la base del robot.

---

## Ensamblaje del sistema de tracción

El sistema completo de tracción se obtiene mediante el ensamblaje de todos los componentes descritos anteriormente. 

Los motores JGY370 se fijan a la base mediante los soportes impresos en 3D, mientras que los acoples permiten conectar el eje de cada motor con su respectiva rueda. De esta manera se obtiene un sistema de locomoción diferencial capaz de generar movimiento hacia adelante, atrás y realizar giros mediante el control independiente de cada motor.

El diseño modular del sistema facilita tanto la fabricación como el mantenimiento de los componentes, permitiendo realizar ajustes o reemplazos sin afectar la estructura principal del robot.