// Motor TB6612FNG
#include <Arduino.h>
#define IN1 26
#define IN2 27
#define PWM 25

#define CHANNEL 0
#define FREQ 1000
#define RESOLUTION 8

// Encoder
#define ENCODER_A 32

volatile long pulsos = 0;

unsigned long tiempo_anterior = 0;

// 👉 AJUSTA ESTOS VALORES
float PPR = 1221.00;        // pulsos por vuelta (tu valor real)
float radio = 0.0335;      // metros (ej: 3 cm)

// Resultados
float rpm = 0;
float vel_angular = 0;   // rad/s
float vel_lineal = 0;    // m/s

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

  // Motor girando
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  ledcWrite(CHANNEL, 100);

  tiempo_anterior = millis();
}

void loop() {

  if (millis() - tiempo_anterior >= 1000) {

    noInterrupts();
    long p = pulsos;
    pulsos = 0;
    interrupts();

    // RPM
    rpm = (p * 60.0) / PPR;

    // Velocidad angular
    vel_angular = (2 * PI * rpm) / 60.0;

    // Velocidad lineal
    vel_lineal = vel_angular * radio;

    Serial.print("RPM: ");
    Serial.print(rpm);
    Serial.print(" | rad/s: ");
    Serial.print(vel_angular);
    Serial.print(" | m/s: ");
    Serial.println(vel_lineal);

    tiempo_anterior = millis();
  }
}