import serial
import serial.tools.list_ports
import sqlite3
import time
import math

# --- Configurações ---
DB_NAME = "dados_microclima.db"

def calcular_ponto_orvalho(t, h):
    if t == 0 or h == 0: return 0
    a, b = 17.27, 237.7
    alpha = ((a * t) / (b + t)) + math.log(h/100.0)
    return (b * alpha) / (a - alpha)

def encontrar_arduino():
    portas = serial.tools.list_ports.comports()
    for p in portas:
        if "Arduino" in p.description or "USB" in p.description or "CH340" in p.description:
            return p.device
    return None

# Inicializa Banco de Dados
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS leituras 
               (timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, 
                chuva REAL, temp REAL, umid REAL, pres REAL, ponto_orvalho REAL)''')
conn.commit()

print("Buscando Arduino...")
while True:
    porta_com = encontrar_arduino()
    if porta_com:
        try:
            print(f"Conectado em: {porta_com}")
            ser = serial.Serial(porta_com, 9600, timeout=1)
            time.sleep(2) # Aguarda estabilização
            
            while True:
                linha = ser.readline().decode('utf-8').strip()
                if linha:
                    dados = linha.split(',')
                    if len(dados) == 4:
                        chuva, temp, umid, pres = map(float, dados)
                        orvalho = calcular_ponto_orvalho(temp, umid)
                        
                        cursor.execute("INSERT INTO leituras (chuva, temp, umid, pres, ponto_orvalho) VALUES (?, ?, ?, ?, ?)",
                                       (chuva, temp, umid, pres, orvalho))
                        conn.commit()
                        print(f"Dados salvos: T:{temp}C | Chuva:{chuva}mm")
        except Exception as e:
            print(f"Erro na conexão: {e}. Tentando reconectar...")
            time.sleep(5)
    else:
        print("Arduino não encontrado. Verifique o cabo...")
        time.sleep(5)