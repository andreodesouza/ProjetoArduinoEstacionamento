#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <Servo.h>

LiquidCrystal_I2C lcd(0x27, 16, 2);
Servo cancela;

const int trigPin = 9;
const int echoPin = 8;

int vagasOcupadas = 0;
int totalVagas = 10;
bool carroDetectado = false;
bool cancelaAberta = false;
unsigned long tempoAbertura = 0;

int pontoNeutro = 92; // Ponto calibrado

int lerDistanciaUltrassonico();
void abrirCancela();
void fecharCancela();
void atualizarDisplay();
void enviarStatusSerial(String evento);

void setup() {
  Serial.begin(9600);

  lcd.init();
  lcd.backlight();
  
  cancela.attach(6);
  cancela.write(pontoNeutro);

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  lcd.setCursor(0, 0);
  lcd.print("Sistema de Vagas");
  lcd.setCursor(0, 1);
  lcd.print("Iniciando...");
  delay(2000);
  lcd.clear();

  enviarStatusSerial("INICIO");
}

void loop() {
  // Recebe comandos vindos do seu painel HTML via Python
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    if (cmd == 'E') { // Botão Entrada / Sensor
      if (!cancelaAberta && vagasOcupadas < totalVagas) {
        vagasOcupadas++;
        abrirCancela();
        cancelaAberta = true;
        tempoAbertura = millis();
        enviarStatusSerial("ENTRADA");
      }
    } else if (cmd == 'S') { // Botão Saída
      if (vagasOcupadas > 0) {
        vagasOcupadas--;
        enviarStatusSerial("SAIDA");
      }
    } else if (cmd == 'R') { // Reset
      vagasOcupadas = 0;
      enviarStatusSerial("RESET");
    }
  }

  int distancia = lerDistanciaUltrassonico();

  // Sensor ultrassônico detecta veículo
  if (distancia > 0 && distancia < 10) {
    if (!carroDetectado && !cancelaAberta) {
      carroDetectado = true;
      
      if (vagasOcupadas < totalVagas) {
        vagasOcupadas++;
        abrirCancela();
        cancelaAberta = true;
        tempoAbertura = millis();
        enviarStatusSerial("ENTRADA");
      }
    }
  } 

  // Fecha após 3 segundos 
  if (cancelaAberta && (millis() - tempoAbertura >= 3000)) {
    fecharCancela();
    cancelaAberta = false;
    carroDetectado = false;
    enviarStatusSerial("CANCELA_FECHADA");
  }

  atualizarDisplay();
  delay(100);
}

void enviarStatusSerial(String evento) {
  Serial.print("{\"ocupadas\":");
  Serial.print(vagasOcupadas);
  Serial.print(",\"total\":");
  Serial.print(totalVagas);
  Serial.print(",\"evento\":\"");
  Serial.print(evento);
  Serial.println("\"}");
}

int lerDistanciaUltrassonico() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duracao = pulseIn(echoPin, HIGH);
  return duracao * 0.034 / 2;
}

void abrirCancela() {
  cancela.write(pontoNeutro - 15); 
  delay(380); 
  cancela.write(pontoNeutro); 
}

void fecharCancela() {
  cancela.write(pontoNeutro + 15); 
  delay(300); 
  cancela.write(pontoNeutro); 

  cancela.write(pontoNeutro + 8); 
  delay(50);                      
  cancela.write(pontoNeutro); 
}

void atualizarDisplay() {
  lcd.setCursor(0, 0);
  lcd.print("Vagas Ocupadas: ");
  lcd.setCursor(0, 1);
  lcd.print(vagasOcupadas);
  lcd.print(" de ");
  lcd.print(totalVagas);
  lcd.print("   ");
}