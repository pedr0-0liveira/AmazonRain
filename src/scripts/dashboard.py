import streamlit as st
import pandas as pd
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "dados", "dados_microclima.db")

from datetime import datetime

from streamlit_autorefresh import st_autorefresh

# Atualiza a página a cada 10 segundos (10000ms)
st_autorefresh(interval=10000, limit=None, key="auto_refresh")

st.set_page_config(page_title="Pluviómetro Inteligente - Manaus", layout="wide")

def carregar_dados():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM leituras ORDER BY timestamp DESC LIMIT 1000", conn)
    conn.close()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

st.title("🌦️ Monitorização de Microclima - Protótipo")

df = carregar_dados()

if not df.empty:
    # Métricas principais (Última leitura)
    ultima = df.iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temperatura", f"{ultima['temp']} °C")
    c2.metric("Humidade", f"{ultima['umid']} %")
    c3.metric("Chuva (Último Intervalo)", f"{ultima['chuva']} mm")
    c4.metric("Ponto de Orvalho", f"{ultima['ponto_orvalho']:.2f} °C")

    # Gráficos
    st.subheader("Histórico Recente")
    tab1, tab2 = st.tabs(["Temperatura e Humidade", "Precipitação"])
    
    with tab1:
        st.line_chart(df.set_index('timestamp')[['temp', 'umid', 'ponto_orvalho']])
    
    with tab2:
        st.bar_chart(df.set_index('timestamp')['chuva'])
else:
    st.warning("Aguardando dados do Arduino...")

# Auto-refresh a cada 10 segundos
st.caption(f"Atualizado em: {datetime.now().strftime('%H:%M:%S')} · refresh a cada 10s")
