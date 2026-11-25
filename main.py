import json
import sqlite3
import threading
import time
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import serial

PORTA_ARDUINO = "COM3"  # Ajuste para a porta do seu Arduino (ex: COM3, COM4)
BAUD_RATE = 9600
DB_NAME = "estacionamento.db"

app = FastAPI()

estado = {
    "total_vagas": 10,
    "ocupadas": 0,
    "entradas_dia": 0,
    "saidas_dia": 0,
    "ultimo_evento_id": 0,
    "ultimo_evento_tipo": None,
    "arduino_conectado": False
}

arduino_serial = None

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            vagas_ocupadas INTEGER NOT NULL,
            data_dia TEXT NOT NULL,
            hora TEXT NOT NULL
        )
    """)
    conn.commit()
    
    # Carrega contagem do dia atual do SQLite ao iniciar
    hoje = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(*) FROM movimentacoes WHERE tipo = 'ENTRADA' AND data_dia = ?", (hoje,))
    estado["entradas_dia"] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM movimentacoes WHERE tipo = 'SAIDA' AND data_dia = ?", (hoje,))
    estado["saidas_dia"] = cursor.fetchone()[0]
    
    cursor.execute("SELECT id, tipo FROM movimentacoes ORDER BY id DESC LIMIT 1")
    ultimo = cursor.fetchone()
    if ultimo:
        estado["ultimo_evento_id"] = ultimo[0]
        estado["ultimo_evento_tipo"] = ultimo[1]
        
    conn.close()

def salvar_movimentacao(tipo: str, ocupadas: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    agora = datetime.now()
    hoje = agora.strftime("%Y-%m-%d")
    hora = agora.strftime("%H:%M:%S")
    
    cursor.execute(
        "INSERT INTO movimentacoes (tipo, vagas_ocupadas, data_dia, hora) VALUES (?, ?, ?, ?)",
        (tipo, ocupadas, hoje, hora)
    )
    novo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    estado["ultimo_evento_id"] = novo_id
    estado["ultimo_evento_tipo"] = tipo
    if tipo == "ENTRADA":
        estado["entradas_dia"] += 1
    elif tipo == "SAIDA":
        estado["saidas_dia"] += 1

def ler_serial():
    global arduino_serial
    while True:
        try:
            if arduino_serial is None or not arduino_serial.is_open:
                arduino_serial = serial.Serial(PORTA_ARDUINO, BAUD_RATE, timeout=1)
                time.sleep(2)
                estado["arduino_conectado"] = True
                print(f"Arduino conectado na {PORTA_ARDUINO}")

            if arduino_serial.in_waiting > 0:
                linha = arduino_serial.readline().decode("utf-8", errors="ignore").strip()
                if linha.startswith("{") and linha.endswith("}"):
                    dados = json.loads(linha)
                    estado["ocupadas"] = dados.get("ocupadas", estado["ocupadas"])
                    estado["total_vagas"] = dados.get("total", 10)
                    evento = dados.get("evento", "")
                    
                    if evento in ["ENTRADA", "SAIDA"]:
                        salvar_movimentacao(evento, estado["ocupadas"])

        except Exception:
            estado["arduino_conectado"] = False
            arduino_serial = None
            time.sleep(3)

@app.on_event("startup")
def startup():
    init_db()
    threading.Thread(target=ler_serial, daemon=True).start()

@app.get("/", response_class=HTMLResponse)
def index():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/dados")
def get_dados():
    return estado

@app.post("/api/entrada")
def registrar_entrada():
    if estado["ocupadas"] >= estado["total_vagas"]:
        return {"erro": "Estacionamento lotado!"}
        
    if arduino_serial and arduino_serial.is_open:
        arduino_serial.write(b"E")
        return {"ok": True, "origem": "arduino"}
    else:
        # Fallback caso o Arduino não esteja plugado no momento do teste
        estado["ocupadas"] += 1
        salvar_movimentacao("ENTRADA", estado["ocupadas"])
        return {"ok": True, "origem": "simulacao"}

@app.post("/api/saida")
def registrar_saida():
    if estado["ocupadas"] <= 0:
        return {"erro": "Não existe veículo para sair."}
        
    if arduino_serial and arduino_serial.is_open:
        arduino_serial.write(b"S")
        return {"ok": True, "origem": "arduino"}
    else:
        # Fallback caso o Arduino não esteja plugado no momento do teste
        estado["ocupadas"] -= 1
        salvar_movimentacao("SAIDA", estado["ocupadas"])
        return {"ok": True, "origem": "simulacao"}