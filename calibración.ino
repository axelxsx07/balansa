#include "HX711.h"

#define DT 5
#define SCK 4

HX711 scale;

long raw_tara = 0;
long raw_peso = 0;
float peso_conocido = 0;
float factor_calibracion = 1.0;

bool calibrado = false;

void setup() {
  Serial.begin(9600);
  delay(1000);

  Serial.println("=== BASCULA AUTO-CALIBRABLE ===");
  Serial.println("No pongas peso...");
  delay(3000);

  scale.begin(DT, SCK);
  scale.set_gain(128);

  // 1️⃣ TARA AUTOMATICA
  raw_tara = scale.read_average(50);

  Serial.print("RAW TARA: ");
  Serial.println(raw_tara);

  Serial.println("Coloca un peso conocido y escribe su valor en kg:");
}

void loop() {
  // Espera peso conocido
  if (!calibrado && Serial.available()) {
    peso_conocido = Serial.parseFloat();

    if (peso_conocido > 0) {
      delay(3000); // estabilizar

      // 2️⃣ RAW CON PESO
      raw_peso = scale.read_average(50);

      Serial.print("RAW CON PESO: ");
      Serial.println(raw_peso);

      // 3️⃣ CALIBRACION
      factor_calibracion = (raw_peso - raw_tara) / peso_conocido;

      Serial.print("FACTOR CALIBRACION: ");
      Serial.println(factor_calibracion, 3);

      calibrado = true;
      Serial.println("=== CALIBRACION COMPLETA ===");
    }
  }

  // 4️⃣ LECTURA CONTINUA
  if (calibrado) {
    long raw_actual = scale.read_average(20);
    float peso = (raw_actual - raw_tara) / factor_calibracion;

    if (abs(peso) < 0.01) peso = 0;

    Serial.print("RAW: ");
    Serial.print(raw_actual);

    Serial.print(" | TARA: ");
    Serial.print(raw_tara);

    Serial.print(" | FACTOR: ");
    Serial.print(factor_calibracion, 3);

    Serial.print(" | PESO: ");
    Serial.print(peso, 3);
    Serial.println(" kg");

    delay(500);
  }
}
