#include <Wire.h>
#include <Adafruit_BMP280.h>

#define PIN_HALL 2
const float VOLUME_BASCULA = 0.25;
const float PRESSAO_NIVEL_MAR = 1013.25; // hPa — ajustar para Manaus se tiver referência local

volatile int contadorPulsos = 0;
unsigned long ultimoTempoPulso = 0;
const unsigned long debounceTime = 200;

Adafruit_BMP280 bmp;

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

  if (!bmp.begin(0x76)) {
    Serial.println("ERRO:BMP280");
    while (1) delay(10);
  }

  // Configurações de precisão do BMP280
  bmp.setSampling(
    Adafruit_BMP280::MODE_NORMAL,
    Adafruit_BMP280::SAMPLING_X16,   // temperatura: 16 amostras
    Adafruit_BMP280::SAMPLING_X16,   // pressão: 16 amostras
    Adafruit_BMP280::FILTER_X16,     // filtro IIR máximo — elimina ruído
    Adafruit_BMP280::STANDBY_MS_500  // ciclo de 500ms
  );
}

void loop() {
  noInterrupts();
  int pulsosNoIntervalo = contadorPulsos;
  contadorPulsos = 0;
  interrupts();

  float chuvaNoIntervalo = pulsosNoIntervalo * VOLUME_BASCULA;
  float temp = bmp.readTemperature();
  float pres = bmp.readPressure() / 100.0F; // Pa → hPa
  float alt  = bmp.readAltitude(PRESSAO_NIVEL_MAR);

  if (isnan(temp)) temp = 0.0;
  if (isnan(pres)) pres = 0.0;
  if (isnan(alt))  alt  = 0.0;

  // Formato: chuva,temp,pres,alt
  Serial.print(chuvaNoIntervalo); Serial.print(",");
  Serial.print(temp);             Serial.print(",");
  Serial.print(pres);             Serial.print(",");
  Serial.println(alt);

  delay(5000);
}