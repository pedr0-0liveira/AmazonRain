import serial
import serial.tools.list_ports
import sqlite3
import time
import math
import os
import logging

# --- Caminhos absolutos ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "dados", "dados_microclima.db")
LOG_PATH = os.path.join(BASE_DIR, "..", "dados", "coletor.log")

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

def calcular_ponto_orvalho(t, h):
    if t == 0 or h == 0: return 0
    a, b = 17.27, 237.7
    alpha = ((a * t) / (b + t)) + math.log(h / 100.0)
    return (b * alpha) / (a - alpha)

def encontrar_arduino():
    portas = serial.tools.list_ports.comports()
    for p in portas:
        if "Arduino" in p.description or "USB" in p.description or "CH340" in p.description:
            return p.device
    return None

# --- Banco de Dados ---
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS leituras 
               (timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, 
                chuva REAL, temp REAL, umid REAL, pres REAL, ponto_orvalho REAL)''')
conn.commit()

# --- Loop principal ---
logging.info("Sistema iniciado. Buscando Arduino...")
try:
    while True:
        porta_com = encontrar_arduino()
        if porta_com:
            try:
                logging.info(f"Conectado em: {porta_com}")
                ser = serial.Serial(porta_com, 9600, timeout=1)
                time.sleep(2)
                while True:
                    linha = ser.readline().decode('utf-8').strip()
                    if linha:
                        dados = linha.split(',')
                        if len(dados) == 4:
                            chuva, temp, umid, pres = map(float, dados)
                            orvalho = calcular_ponto_orvalho(temp, umid)
                            cursor.execute(
                                "INSERT INTO leituras (chuva, temp, umid, pres, ponto_orvalho) VALUES (?,?,?,?,?)",
                                (chuva, temp, umid, pres, orvalho)
                            )
                            conn.commit()
                            logging.info(f"Dados salvos: T:{temp}C | Chuva:{chuva}mm")
            except Exception as e:
                logging.error(f"Erro na conexão: {e}. Tentando reconectar em 5s...")
                time.sleep(5)
        else:
            logging.warning("Arduino não encontrado. Verifique o cabo...")
            time.sleep(5)

finally:
    conn.close()
    logging.info("Banco de dados fechado com segurança.")