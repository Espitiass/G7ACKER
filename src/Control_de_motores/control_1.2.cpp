#include <ESP32Servo.h>
#include <Arduino.h>

Servo servo;
int direccionAnterior = -1;
#define SERVO_PIN 18
#define LED_PIN 2

// ==================== PROTOTIPOS ====================
void aplicarMovimiento(float v, int dir);
void motor1Adelante(int vel);
void motor1Atras(int vel);
void motor2Adelante(int vel);
void motor2Atras(int vel);
void detenerMotores();

// ==================== ECUACIONES ====================
const float A_M1 = 500; //izquierdo rapido
const float B_M1 = 15;

const float A_M2 = 850; //derecho lento
const float B_M2 = 30;

// ==================== CONSTANTES ====================
const float DIAMETRO = 0.067;
const int PPR_M1 = 1340; // izquierdo
const int PPR_M2 = 1221; // derecho
const int INTERVALO_MS = 500;

// 🔥 VELOCIDAD FIJA
float vDeseada = 0.25;

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

  // Servo con rango ajustado
  servo.attach(SERVO_PIN, 1000, 2000);
  servo.write(90); // centrado inicial

  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);

  // Pines motores
  pinMode(AIN1, OUTPUT);
  pinMode(AIN2, OUTPUT);
  pinMode(BIN1, OUTPUT);
  pinMode(BIN2, OUTPUT);

  // Pines encoders
  pinMode(ENCODER1_A, INPUT_PULLUP);
  pinMode(ENCODER2_A, INPUT_PULLUP);

  attachInterrupt(digitalPinToInterrupt(ENCODER1_A), contarPulso1, RISING);
  attachInterrupt(digitalPinToInterrupt(ENCODER2_A), contarPulso2, RISING);

  // PWM motores
  ledcSetup(2, 5000, 8); //motor izquierdo canal 2
  ledcAttachPin(PWMA, 2);

  ledcSetup(3, 5000, 8);  //motor derecho canal 3
  ledcAttachPin(PWMB, 3);

  tiempoAnterior = millis();
}

// ==================== LOOP ====================
void loop() {

  // 🔹 SOLO DIRECCION
if (Serial.available()) {
  comando = Serial.read();

  if (comando != '\n' && comando != '\r') {
    while (Serial.available()) Serial.read();
  }
}

  // 🔥 convertir comando a dirección
  int dir = 0;

  if (comando == 'a') dir = 1;
  else if (comando == 'i') dir = 3;
  else if (comando == 'd') dir = 2;
  else if (comando == 'x') dir = 0;

  // 🔥 MOVER SERVO SOLO SI CAMBIA
  if (dir != direccionAnterior) {
    moverServo(dir);
    direccionAnterior = dir;
  }

  // 🔥 MOVIMIENTO
  if (dir != 0) {
    aplicarMovimiento(vDeseada, dir);
    digitalWrite(LED_PIN, HIGH);
  } else {
    detenerMotores();
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

    float rpm1 = (p1 * (100.0 / intervalo)) / PPR_M1;
    float rpm2 = (p2 * (100.0 / intervalo)) / PPR_M2;

    float vReal1 = (rpm1 * PI * DIAMETRO) / 100.0;
    float vReal2 = (rpm2 * PI * DIAMETRO) / 100.0;

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

  // evitar zona muerta
  pwm1 = max(pwm1, 80);
  pwm2 = max(pwm2, 80);

switch (dir) {

  case 1: // ADELANTE
    motor1Adelante(pwm1);
    motor2Adelante(pwm2);
    break;

  case 2: // DERECHA
    motor1Adelante(pwm1);     // izquierda adelante
    detenerMotor2();            // derecha detenida
    break;

  case 3: // IZQUIERDA
    motor2Adelante(pwm2);  // derecha adelante
    detenerMotor1();       // izquierda detenida
    break;

  default:
    detenerMotores();
    break;
}
}

// ==================== MOTORES ====================
void motor1Adelante(int vel) {
  digitalWrite(AIN1, HIGH);
  digitalWrite(AIN2, LOW);
  ledcWrite(2, vel);
}

void motor1Atras(int vel) {
  digitalWrite(AIN1, LOW);
  digitalWrite(AIN2, HIGH);
  ledcWrite(2, vel);
}

void detenerMotor1() {
  digitalWrite(AIN1, LOW);
  digitalWrite(AIN2, LOW);
  ledcWrite(2, 0);
}

void motor2Adelante(int vel) {
  digitalWrite(BIN1, HIGH);
  digitalWrite(BIN2, LOW);
  ledcWrite(3, vel);
}

void motor2Atras(int vel) {
  digitalWrite(BIN1, LOW);
  digitalWrite(BIN2, HIGH);
  ledcWrite(3, vel);
}

void detenerMotor2() {
  digitalWrite(BIN1, LOW);
  digitalWrite(BIN2, LOW);
  ledcWrite(3, 0);
}

void detenerMotores() {
  detenerMotor1();
  detenerMotor2();
}

// ==================== SERVO ====================
void moverServo(int dir) {
  switch (dir) {
    case 1:
      servo.write(90);
      break;
    case 2:
      servo.write(150);
      break;
    case 3:
      servo.write(30);
      break;
    default:
      servo.write(90);
      break;
  }
}