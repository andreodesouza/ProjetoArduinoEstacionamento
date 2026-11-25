# 🚗 Estacionamento Inteligente — Arduino + Python + SQLite

Sistema de controle e monitoramento de vagas de estacionamento em tempo real, integrando hardware (**Arduino Uno R3**, sensor ultrassônico HC-SR04, servo motor de rotação contínua e display LCD I2C 16x2) a um painel web responsivo com backend em **FastAPI**, comunicação serial via **PySerial** e persistência de dados em **SQLite**.

---

## 🛠️ Arquitetura do Projeto

```text
estacionamento/
├── estacionamento.ino   # Firmware do Arduino Uno
├── main.py              # Backend FastAPI + Thread Serial + SQLite
├── index.html           # Painel Web (HTML5, CSS3 e JavaScript)
├── requirements.txt     # Dependências Python
├── README.md            # Documentação do projeto
└── estacionamento.db    # Banco de dados SQLite (gerado automaticamente)