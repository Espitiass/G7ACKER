#include <Arduino.h>
#define IN1 26
#define IN2 27
#define PWM 25

#define CHANNEL 0
#define FREQ 1000
#define RESOLUTION 8

// Encoder
#define ENCODER_A 32   // usa pin con pullup

volatile long pulsos = 0;
bool corriendo = false;

void IRAM_ATTR contar() {
  pulsos++;
}

void setup() {
  Serial.begin(9600);

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  pinMode(ENCODER_A, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENCODER_A), contar, CHANGE);

  ledcSetup(CHANNEL, FREQ, RESOLUTION);
  ledcAttachPin(PWM, CHANNEL);

  Serial.println("=== CALIBRACION PPR ===");
  Serial.println("Presiona 'a' para iniciar");
}

void loop() {

  if (Serial.available()) {
    char c = Serial.read();

    // 🔁 INICIAR / REINICIAR
    if (c == 'a') {
      pulsos = 0;
      corriendo = true;

      digitalWrite(IN1, HIGH);
      digitalWrite(IN2, LOW);
      ledcWrite(CHANNEL, 100);

      Serial.println("\n--- NUEVA MEDICION ---");
      Serial.println("Girando... presiona 's' para detener");
    }

    // 🛑 DETENER
    if (c == 's' && corriendo) {
      corriendo = false;

      ledcWrite(CHANNEL, 0);
      digitalWrite(IN1, LOW);
      digitalWrite(IN2, LOW);

      Serial.println("\n=== RESULTADO ===");
      Serial.print("Pulsos en la vuelta: ");
      Serial.println(pulsos);
    }
  }
}