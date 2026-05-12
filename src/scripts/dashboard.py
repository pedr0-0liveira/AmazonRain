import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "dados", "dados_microclima.db")

st.set_page_config(page_title="AmazonRain — Microclima Manaus", layout="wide")
st_autorefresh(interval=10000, limit=None, key="auto_refresh")

# --- Funções de cálculo ---

def calcular_heat_index(t, h):
    """Fórmula de Rothfusz. Válida para t >= 27°C e h >= 40%."""
    if t < 27 or h < 40:
        return t
    hi = (-8.78469475556
          + 1.61139411 * t
          + 2.33854883889 * h
          - 0.14611605 * t * h
          - 0.012308094 * t**2
          - 0.016424828 * h**2
          + 0.002211732 * t**2 * h
          + 0.00072546 * t * h**2
          - 0.000003582 * t**2 * h**2)
    return round(hi, 1)

def classificar_intensidade(chuva_mm_por_5s):
    """Converte mm/5s para mm/h e classifica."""
    mmh = chuva_mm_por_5s * 720
    if mmh == 0:
        return "Sem chuva", "🌤️"
    elif mmh < 2.5:
        return "Fraca", "🌦️"
    elif mmh < 10:
        return "Moderada", "🌧️"
    elif mmh < 50:
        return "Forte", "⛈️"
    else:
        return "Muito forte", "🌊"

def calcular_tendencia_pressao(df):
    """Diferença de pressão entre agora e ~30 min atrás."""
    if len(df) < 2:
        return 0.0
    agora = df['pres'].iloc[-1]
    # 30 min atrás = 360 leituras de 5s; pega o mais antigo disponível se não tiver
    idx = max(0, len(df) - 360)
    antes = df['pres'].iloc[idx]
    return round(agora - antes, 2)

def carregar_dados():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT * FROM leituras ORDER BY timestamp ASC LIMIT 1000", conn
    )
    conn.close()
    if df.empty:
        return df
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['chuva_acumulada'] = df['chuva'].cumsum()
    df['heat_index'] = df.apply(
        lambda r: calcular_heat_index(r['temp'], r['umid']), axis=1
    )
    return df

# --- Interface ---

st.title("🌦️ AmazonRain — Monitorização de Microclima")
st.caption("Manaus · BME280 + Sensor de báscula KY-024")

df = carregar_dados()

if df.empty:
    st.warning("Aguardando dados do Arduino...")
    st.stop()

ultima = df.iloc[-1]  # mais recente (df está ASC)
intensidade, emoji = classificar_intensidade(ultima['chuva'])
tendencia = calcular_tendencia_pressao(df)
heat_index = calcular_heat_index(ultima['temp'], ultima['umid'])

# Tendência de pressão: ícone e texto
if tendencia > 0.5:
    tend_label = f"▲ +{tendencia} hPa (subindo)"
elif tendencia < -1.5:
    tend_label = f"▼ {tendencia} hPa (⚠️ queda rápida)"
elif tendencia < -0.5:
    tend_label = f"▼ {tendencia} hPa (caindo)"
else:
    tend_label = f"→ {tendencia} hPa (estável)"

# --- Linha 1: métricas principais ---
st.subheader("Leitura atual")
c1, c2, c3, c4 = st.columns(4)
c1.metric("🌡️ Temperatura", f"{ultima['temp']:.1f} °C")
c2.metric("💧 Humidade", f"{ultima['umid']:.1f} %")
c3.metric("🌡️ Sensação térmica", f"{heat_index} °C",
          help="Heat Index (Rothfusz): como o calor é sentido com a humidade atual")
c4.metric("🔵 Ponto de Orvalho", f"{ultima['ponto_orvalho']:.1f} °C")

# --- Linha 2: pressão e chuva ---
c5, c6, c7, c8 = st.columns(4)
c5.metric("📊 Pressão", f"{ultima['pres']:.1f} hPa")
c6.metric("📈 Tendência (30 min)", tend_label)
c7.metric(f"{emoji} Intensidade", intensidade)
c8.metric("🌧️ Chuva acumulada", f"{ultima['chuva_acumulada']:.2f} mm",
          help="Acumulado das últimas 1000 leituras carregadas")

st.divider()

# --- Gráficos ---
st.subheader("Histórico recente")

tab1, tab2, tab3, tab4 = st.tabs([
    "🌡️ Temperatura & Sensação",
    "💧 Humidade & Orvalho",
    "📊 Pressão",
    "🌧️ Precipitação"
])

with tab1:
    st.line_chart(
        df.set_index('timestamp')[['temp', 'heat_index']],
        color=["#e05c2a", "#f0a04a"]
    )
    st.caption("Temperatura real vs sensação térmica (Heat Index). "
               "A diferença aumenta com a humidade.")

with tab2:
    st.line_chart(
        df.set_index('timestamp')[['umid', 'ponto_orvalho']],
        color=["#2a7ae0", "#2ac4e0"]
    )
    st.caption("Quando o ponto de orvalho se aproxima da temperatura, "
               "a condensação (garoa, nevoeiro) torna-se provável.")

with tab3:
    st.line_chart(
        df.set_index('timestamp')['pres'],
        color=["#7c3aed"]
    )
    st.caption(f"Tendência dos últimos 30 min: {tend_label}. "
               "Quedas rápidas (> 1.5 hPa) indicam frente de chuva se aproximando.")

with tab4:
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Por intervalo (5s)**")
        st.bar_chart(
            df.set_index('timestamp')['chuva'],
            color=["#1d9e75"]
        )
        st.caption("Precipitação em mm por intervalo de 5 segundos.")
    with col_b:
        st.markdown("**Acumulado**")
        st.line_chart(
            df.set_index('timestamp')['chuva_acumulada'],
            color=["#0f6e56"]
        )
        st.caption("Chuva acumulada ao longo do tempo (últimas 1000 leituras).")

st.divider()
st.caption(f"Atualizado em: {datetime.now().strftime('%H:%M:%S')} · refresh a cada 10s")