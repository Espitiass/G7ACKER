#include <Arduino.h>
#define LED_PIN 2
// ==================== PROTOTIPOS ====================
void aplicarMovimiento(float v, int dir);
void motor1Adelante(int vel);
void motor1Atras(int vel);
void motor2Adelante(int vel);
void motor2Atras(int vel);
void detenerMotores();

// ==================== ECUACIONES ====================
const float A_M1 = 510;
const float B_M1 = 7;

const float A_M2 = 590;
const float B_M2 = 9;

// ==================== CONSTANTES ====================
const float DIAMETRO = 0.067;
const int PPR_M1 = 1221; // izquierdo
const int PPR_M2 = 1340; // derecho
const int INTERVALO_MS = 500;

// 🔥 VELOCIDAD FIJA
float vDeseada = 0.20;

// ==================== PINES ====================
#define AIN1 27
#define AIN2 26
#define PWMA 25

#define BIN1 12
#define BIN2 13
#define PWMB 14

const int ENCODER1_A = 32;
const int ENCODER2_A = 34;

// ==================== VARIABLES ====================
volatile long pulsos1 = 0;
volatile long pulsos2 = 0;

unsigned long tiempoAnterior = 0;

char comando = 0;

// ==================== INTERRUPCIONES ====================
void IRAM_ATTR contarPulso1() { pulsos1++; }
void IRAM_ATTR contarPulso2() { pulsos2++; }

// ==================== SETUP ====================
void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);

  pinMode(AIN1, OUTPUT);
  pinMode(AIN2, OUTPUT);
  pinMode(BIN1, OUTPUT);
  pinMode(BIN2, OUTPUT);

  pinMode(ENCODER1_A, INPUT_PULLUP);
  pinMode(ENCODER2_A, INPUT_PULLUP);

  attachInterrupt(digitalPinToInterrupt(ENCODER1_A), contarPulso1, RISING);
  attachInterrupt(digitalPinToInterrupt(ENCODER2_A), contarPulso2, RISING);

  ledcSetup(0, 5000, 8);
  ledcAttachPin(PWMA, 0);

  ledcSetup(1, 5000, 8);
  ledcAttachPin(PWMB, 1);

  Serial.println("Solo escribe direccion:");
  Serial.println("1=adelante -1=atras");

  tiempoAnterior = millis();
}

// ==================== LOOP ====================
void loop() {

  // 🔹 SOLO DIRECCION
    if (Serial.available()) {
    comando = Serial.read();
    }

  // Movimiento siempre con velocidad fija
    if (comando == 'a') {
    aplicarMovimiento(vDeseada, 1);  // avanzar
    digitalWrite(LED_PIN, HIGH); 
    } 
    else if (comando == 'x') {
    detenerMotores();               // detener
    digitalWrite(LED_PIN, LOW);
    }

  // Medición
  if (millis() - tiempoAnterior >= INTERVALO_MS) {

    noInterrupts();
    long p1 = pulsos1;
    long p2 = pulsos2;
    pulsos1 = 0;
    pulsos2 = 0;
    interrupts();

    float intervalo = INTERVALO_MS / 1000.0;

    float rpm1 = (p1 * (60.0 / intervalo)) / PPR_M1;
    float rpm2 = (p2 * (60.0 / intervalo)) / PPR_M2;

    float vReal1 = (rpm1 * PI * DIAMETRO) / 60.0;
    float vReal2 = (rpm2 * PI * DIAMETRO) / 60.0;

    Serial.print("V1:");
    Serial.print(vReal1, 2);
    Serial.print(" V2:");
    Serial.println(vReal2, 2);

    tiempoAnterior = millis();
  }
}

// ==================== MOVIMIENTO ====================
void aplicarMovimiento(float v, int dir) {

  int pwm1 = constrain((int)(A_M1 * v + B_M1), 0, 255);
  int pwm2 = constrain((int)(A_M2 * v + B_M2), 0, 255);

  switch (dir) {
    case 1:
      motor1Adelante(pwm1);
      motor2Adelante(pwm2);
      break;

    case -1:
      motor1Atras(pwm1);
      motor2Atras(pwm2);
      break;
  }
}

// ==================== MOTORES ====================
void motor1Adelante(int vel) {
  digitalWrite(AIN1, HIGH);
  digitalWrite(AIN2, LOW);
  ledcWrite(0, vel);
}

void motor1Atras(int vel) {
  digitalWrite(AIN1, LOW);
  digitalWrite(AIN2, HIGH);
  ledcWrite(0, vel);
}

void motor2Adelante(int vel) {
  digitalWrite(BIN1, HIGH);
  digitalWrite(BIN2, LOW);
  ledcWrite(1, vel);
}

void motor2Atras(int vel) {
  digitalWrite(BIN1, LOW);
  digitalWrite(BIN2, HIGH);
  ledcWrite(1, vel);
}

void detenerMotores() {
  ledcWrite(0, 0);
  ledcWrite(1, 0);
}
