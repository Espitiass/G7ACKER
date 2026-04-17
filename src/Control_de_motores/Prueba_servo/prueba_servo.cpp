#include <Arduino.h>
#include <ESP32Servo.h>

Servo servo;

const int PIN_SERVO = 18;
char comando;

void setup() {
  Serial.begin(9600);

  servo.setPeriodHertz(50);
  servo.attach(PIN_SERVO, 500, 2500);

  Serial.println("Listo");
}

void loop() {

  if (Serial.available()) {
    comando = Serial.read();

    if (comando == 'd') { //recto
      servo.write(95); 
    }
    else if (comando == 's') { //derecha
      servo.write(140);
    }
    else if (comando == 'f') { //izquierda
      servo.write(40);
    }
  }
}