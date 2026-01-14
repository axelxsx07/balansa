#include "HX711.h"

// ================= ULTRASONICO =================
const int Trigger = 2;
const int Echo = 3;
const float ALTURA_SENSOR = 200.0; // cm

// ================= HX711 =================
#define DT 5
#define SCK 4

#define MARGEN_TARA 500
#define FACTOR_CALIBRACION 19740.615

HX711 scale;
long raw_tara = 0;

// ================= FUNCIONES =================
void esperarHX711() {
  while (!scale.is_ready()) {
    delay(10);
  }
}

// ================= SETUP =================
void setup() {
  Serial.begin(9600);

  // Ultrasonico
  pinMode(Trigger, OUTPUT);
  pinMode(Echo, INPUT);
  digitalWrite(Trigger, LOW);

  // HX711
  delay(1000);
  Serial.println("=== SISTEMA PESO + ALTURA ===");
  Serial.println("No pongas peso...");
  delay(3000);

  scale.begin(DT, SCK);
  scale.set_gain(128);

  esperarHX711();
  raw_tara = scale.read_average(50);

  Serial.print("RAW TARA: ");
  Serial.println(raw_tara);

  Serial.println("Sistema listo");
  Serial.println("============================");
}

// ================= LOOP =================
void loop() {

  // ===== ALTURA =====
  long t;
  float distancia;
  float altura;

  digitalWrite(Trigger, LOW);
  delayMicroseconds(2);
  digitalWrite(Trigger, HIGH);
  delayMicroseconds(10);
  digitalWrite(Trigger, LOW);

  t = pulseIn(Echo, HIGH, 30000);

  if (t == 0) {
    Serial.print("ALTURA: Fuera de rango | ");
  } else {
    distancia = t * 0.034 / 2;
    altura = ALTURA_SENSOR - distancia;

    if (altura < 0 || altura > ALTURA_SENSOR) {
      Serial.print("ALTURA: Invalida | ");
    } else {
      Serial.print("ALTURA: ");
      Serial.print(altura, 1);
      Serial.print(" cm | ");
    }
  }

  // ===== PESO =====
  esperarHX711();
  long raw_actual = scale.read_average(20);
  long diferencia = raw_actual - raw_tara;

  float peso;
  if (abs(diferencia) <= MARGEN_TARA) {
    peso = 0.0;
  } else {
    peso = diferencia / FACTOR_CALIBRACION;
  }

  if (peso < 0) peso = 0;

  // ===== SALIDA SERIAL =====
  Serial.print("RAW: ");
  Serial.print(raw_actual);

  Serial.print(" | TARA: ");
  Serial.print(raw_tara);

  Serial.print(" | DIF: ");
  Serial.print(diferencia);

  Serial.print(" | PESO: ");
  Serial.print(peso, 2);
  Serial.println(" kg");

  Serial.println("---------------------------------");
  delay(500);
}
