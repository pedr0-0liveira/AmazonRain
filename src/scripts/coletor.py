import serial
import serial.tools.list_ports
import sqlite3
import time
import os
import logging
from datetime import datetime

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
               (timestamp DATETIME,
                chuva REAL, temp REAL, pres REAL, alt REAL,
                intervalo_ms INTEGER)''')
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
                        if linha.startswith("ERRO:"):
                            logging.warning(f"Arduino reportou: {linha}")
                            continue
                        dados = linha.split(',')
                        if len(dados) == 5:
                            chuva       = float(dados[0])
                            temp        = float(dados[1])
                            pres        = float(dados[2])
                            alt         = float(dados[3])
                            intervalo_ms = int(float(dados[4]))

                            if temp == 0.0 and pres == 0.0:
                                logging.warning("Leitura ignorada: BMP280 ausente ou com falha.")
                                continue

                            agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                            cursor.execute(
                                "INSERT INTO leituras (timestamp, chuva, temp, pres, alt, intervalo_ms) VALUES (?,?,?,?,?,?)",
                                (agora, chuva, temp, pres, alt, intervalo_ms)
                            )
                            conn.commit()
                            logging.info(f"Dados salvos: T:{temp}°C | P:{pres}hPa | Alt:{alt}m | Chuva:{chuva}mm | Intervalo:{intervalo_ms}ms")
            except Exception as e:
                logging.error(f"Erro na conexão: {e}. Tentando reconectar em 5s...")
                time.sleep(5)
        else:
            logging.warning("Arduino não encontrado. Verifique o cabo...")
            time.sleep(5)

finally:
    conn.close()
    logging.info("Banco de dados fechado com segurança.")