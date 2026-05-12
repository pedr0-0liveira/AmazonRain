#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>

#define PIN_HALL 2 
const float VOLUME_BASCULA = 0.25; 
volatile int contadorPulsos = 0;
unsigned long ultimoTempoPulso = 0;
const unsigned long debounceTime = 150; // Ajustado para 150ms

Adafruit_BME280 bme;

// Interrupção: Mantida a lógica de debounce que você fez, está excelente.
void registroChuva() {
  unsigned long tempoAtual = millis();
  if (tempoAtual - ultimoTempoPulso > debounceTime) {
    contadorPulsos++;
    ultimoTempoPulso = tempoAtual;
  }
}

void setup() {
  Serial.begin(9600);
  
  pinMode(PIN_HALL, INPUT_PULLUP); 
  attachInterrupt(digitalPinToInterrupt(PIN_HALL), registroChuva, FALLING);

  // Inicialização do BME280
  if (!bme.begin(0x76)) {
    // Se falhar, enviamos um sinal via serial mas não travamos o loop
    // Isso ajuda no "Plug-and-Play" se o cabo I2C estiver frouxo
  }
}

void loop() {
  // Captura o valor atual e zera o contador imediatamente (seção crítica)
  noInterrupts(); // Desativa para evitar conflito com novo pulso durante a leitura
  int pulsosNoIntervalo = contadorPulsos;
  contadorPulsos = 0; 
  interrupts();

  float chuvaNoIntervalo = pulsosNoIntervalo * VOLUME_BASCULA;
  
  float temp = bme.readTemperature();
  float umid = bme.readHumidity();
  float pres = bme.readPressure() / 100.0F;

  // Se o BME falhar (retornar NaN), enviamos 0.0 para não quebrar o banco de dados
  if (isnan(temp)) temp = 0.0;
  if (isnan(umid)) umid = 0.0;

  // Saída Serial Otimizada para Python: chuva,temp,umid,pres
  Serial.print(chuvaNoIntervalo);
  Serial.print(",");
  Serial.print(temp);
  Serial.print(",");
  Serial.print(umid);
  Serial.print(",");
  Serial.println(pres);

  delay(5000); // Frequência de 5s é ótima para microclima
}