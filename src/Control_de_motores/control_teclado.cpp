#include <Arduino.h>
#include <ESP32Servo.h>

Servo servo;
int direccionAnterior = 0;

// ==================== PROTOTIPOS ====================
void aplicarMovimiento(float v, int dir);
void motor1Adelante(int vel);
void motor1Atras(int vel);
void motor2Adelante(int vel);
void motor2Atras(int vel);
void detenerMotores();
void moverServo(int dir);

// ==================== ECUACIONES ====================
const float A_M1 = 510; //izquierdo
const float B_M1 = 7;

const float A_M2 = 590;//derecho
const float B_M2 = 9;


// ==================== CONSTANTES ====================
const float DIAMETRO = 0.067;
const int PPR_M1 = 1221;
const int PPR_M2 = 1340;
const int INTERVALO_MS = 500;

const float vDeseada = 0.20;

// ==================== PINES ====================
#define AIN1 27
#define AIN2 26
#define PWMA 25

#define BIN1 12
#define BIN2 13
#define PWMB 14

const int ENCODER1_A = 32;
const int ENCODER2_A = 33;

// ==================== VARIABLES ====================
volatile long pulsos1 = 0;
volatile long pulsos2 = 0;
unsigned long tiempoAnterior = 0;
int direccion = 0;

// ==================== INTERRUPCI0ONES ====================
void IRAM_ATTR contarPulso1() { pulsos1++; }
void IRAM_ATTR contarPulso2() { pulsos2++; }

// ==================== SETUP ====================
void setup() {
  Serial.begin(9600);

  // Servo con rango ajustado
  servo.attach(18, 1000, 2000);
  servo.write(90);
  Serial.println("Servo en 90 grados");

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

  // PWM motores (Cambiados a canal 2 y 3 para evitar conflicto con el Servo)
  ledcSetup(2, 5000, 8);
  ledcAttachPin(PWMA, 2);
  ledcSetup(3, 5000, 8);
  ledcAttachPin(PWMB, 3);

  Serial.println("Comandos: 1=adelante -1=atras 2=derecha 3=izquierda");

  tiempoAnterior = millis();
}

// ==================== LOOP ====================
void loop() {
  // Leer direccion
  if (Serial.available()) {
    direccion = Serial.parseInt();
    Serial.print("Direccion: ");
    Serial.println(direccion);
    while (Serial.available())
      Serial.read();
  }

  // Mover servo SOLO si cambia la direccion
  if (direccion != direccionAnterior) {
    moverServo(direccion);
    direccionAnterior = direccion;
  }

  // Mover motores
  if (direccion != 0) {
    aplicarMovimiento(vDeseada, direccion);
  } else {
    detenerMotores();
  }

  // Medición de velocidad
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
  case 2:
    motor1Adelante(pwm1);
    motor2Atras(pwm2);
    break;
  case 3:
    motor1Atras(pwm1);
    motor2Adelante(pwm2);
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

void detenerMotores() {
  ledcWrite(2, 0);
  ledcWrite(3, 0);
}

// ==================== SERVO ====================
void moverServo(int dir) {
  switch (dir) {
  case 1:  // adelante
  case -1: // atras
    servo.write(90);
    Serial.println("Servo 90°");
    break;
  case 2: // derecha
    servo.write(140);
    Serial.println("Servo 140°");
    break;
  case 3: // izquierda
    servo.write(50);
    Serial.println("Servo 50°");
    break;
  default:
    servo.write(90);
    Serial.println("Servo 90°");
    break;
  }
}