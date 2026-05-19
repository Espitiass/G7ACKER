#include <Arduino.h>   // 🔥 ESTA LÍNEA ES LA CLAVE

#define LED_PIN 2

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  Serial.println("ESP32 lista...");
}

void loop() {
  if (Serial.available()) {
    char dato = Serial.read();

    Serial.print("Recibido: ");
    Serial.println(dato);

    if (dato == 'a') {
      digitalWrite(LED_PIN, HIGH);  // LED ON
      Serial.println("LED ENCENDIDO");
    }
    else if (dato == 'x') {
      digitalWrite(LED_PIN, LOW);   // LED OFF
      Serial.println("LED APAGADO");
    }
  }
}