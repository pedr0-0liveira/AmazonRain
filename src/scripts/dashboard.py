import streamlit as st
import pandas as pd
import sqlite3
import os
import math
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "dados", "dados_microclima.db")

st.set_page_config(page_title="AmazonRain — Microclima Manaus", layout="wide")
st_autorefresh(interval=10000, limit=None, key="auto_refresh")

# --- Funções de cálculo ---

def preparar_grafico(df, colunas):
    """Remove segundos do timestamp para exibição limpa nos gráficos."""
    cols = colunas if isinstance(colunas, list) else [colunas]
    df_plot = df[['timestamp'] + cols].copy()
    df_plot['timestamp'] = df_plot['timestamp'].dt.strftime('%d/%m %H:%M')
    return df_plot.set_index('timestamp')

def classificar_chuva(df, janela=60):
    if 'chuva' not in df.columns:
        return "Sem chuva", "🌤️", 0.0
    ultimas = df.tail(janela)
    pulsos_positivos = ultimas[ultimas['chuva'] > 0]['chuva'].count()
    total_5min = ultimas['chuva'].sum()
    mmh_volume = total_5min * 12

    if pulsos_positivos == 0:
        return "Sem chuva", "🌤️", 0.0
    if pulsos_positivos == 1:
        return "Traços", "🌂", mmh_volume

    mmh_instantaneo = 0.0
    if 'intervalo_ms' in df.columns:
        ultimo_intervalo = df[df['intervalo_ms'] > 0]['intervalo_ms'].tail(1)
        if not ultimo_intervalo.empty:
            intervalo_s = ultimo_intervalo.values[0] / 1000.0
            if intervalo_s > 0:
                mmh_instantaneo = (0.25 / intervalo_s) * 3600

    mmh = max(mmh_volume, mmh_instantaneo * 0.3)

    if mmh < 0.5:
        return "Traços", "🌂", mmh
    elif mmh < 2.5:
        return "Fraca", "🌦️", mmh
    elif mmh < 10:
        return "Moderada", "🌧️", mmh
    elif mmh < 50:
        return "Forte", "⛈️", mmh
    else:
        return "Muito forte", "🌊", mmh

def detectar_estado_chuva(df, janela_inicio=6, janela_fim=36):
    if len(df) < janela_fim:
        return "indefinido"
    recentes = df['chuva'].tail(janela_inicio)
    ultimas_3min = df['chuva'].tail(janela_fim)
    if recentes.sum() > 0:
        return "chovendo"
    elif ultimas_3min.sum() > 0:
        return "parando"
    else:
        return "seco"

def calcular_tendencia_pressao(df):
    pres_valida = df[df['pres'] > 0][['timestamp', 'pres']].copy()
    if len(pres_valida) < 2:
        return 0.0
    agora = pres_valida.iloc[-1]
    limite = agora['timestamp'] - pd.Timedelta(minutes=30)
    anteriores = pres_valida[pres_valida['timestamp'] <= limite]
    antes_pres = anteriores.iloc[-1]['pres'] if not anteriores.empty else pres_valida.iloc[0]['pres']
    return round(float(agora['pres'] - antes_pres), 2)

def calcular_variacao_altitude(df, janela=12):
    if 'alt' not in df.columns or len(df) < 2:
        return 0.0
    alt_valida = df[df['alt'] > 0]['alt']
    if len(alt_valida) < 2:
        return 0.0
    recente = alt_valida.tail(janela).mean()
    anterior = alt_valida.head(janela).mean()
    return round(float(recente - anterior), 2)

def calcular_acumulado_evento(df, tolerancia_min=10):
    if df.empty or 'chuva' not in df.columns:
        return 0.0
    tolerancia_leituras = tolerancia_min * 12
    chuva = df['chuva'].values[::-1]
    acumulado = 0.0
    sem_chuva_consecutivo = 0
    for valor in chuva:
        if valor > 0:
            acumulado += valor
            sem_chuva_consecutivo = 0
        else:
            sem_chuva_consecutivo += 1
            if sem_chuva_consecutivo > tolerancia_leituras:
                break
    return round(acumulado, 2)

def preparar_acumulado_por_hora(df):
    if df.empty:
        return pd.DataFrame()
    df_hora = df.copy()
    df_hora['hora'] = df_hora['timestamp'].dt.floor('h')
    return df_hora.groupby('hora')['chuva'].sum().reset_index()

def limpar_dados():
    if not os.path.exists(DB_PATH):
        return
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM leituras")
    conn.commit()
    conn.close()

def carregar_dados():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(), 0.0, 0.0

    conn = sqlite3.connect(DB_PATH)
    tabela_existe = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='leituras'"
    ).fetchone()
    if not tabela_existe:
        conn.close()
        return pd.DataFrame(), 0.0, 0.0

    df = pd.read_sql_query(
        "SELECT * FROM leituras ORDER BY timestamp ASC LIMIT 1000", conn
    )

    agora = datetime.now()
    meia_noite = agora.replace(hour=0, minute=0, second=0, microsecond=0)
    uma_hora_atras = agora - pd.Timedelta(hours=1)

    acum_diario = conn.execute(
        "SELECT COALESCE(SUM(chuva), 0) FROM leituras WHERE timestamp >= ?",
        [meia_noite.strftime('%Y-%m-%d %H:%M:%S')]
    ).fetchone()[0]

    acum_horario = conn.execute(
        "SELECT COALESCE(SUM(chuva), 0) FROM leituras WHERE timestamp >= ?",
        [uma_hora_atras.strftime('%Y-%m-%d %H:%M:%S')]
    ).fetchone()[0]

    conn.close()

    if df.empty:
        return df, round(acum_diario, 2), round(acum_horario, 2)

    df = df.fillna(0)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    return df, round(acum_diario, 2), round(acum_horario, 2)

# --- Interface ---

st.title("🌦️ AmazonRain — Monitorização de Microclima")
st.caption("Manaus · BMP280 + Pluviômetro de báscula KY-024")

with st.sidebar:
    st.header("🛠️ Ferramentas de teste")
    st.warning("Use apenas durante testes.")
    if st.button("🗑️ Limpar todos os dados", type="primary"):
        limpar_dados()
        st.success("Banco limpo com sucesso!")
        st.rerun()

df, acum_diario, acum_horario = carregar_dados()

if df.empty:
    st.warning("Aguardando dados do Arduino...")
    st.stop()

ultima = df.iloc[-1]
intensidade, emoji, mmh = classificar_chuva(df)
estado = detectar_estado_chuva(df)
tendencia = calcular_tendencia_pressao(df)
var_alt = calcular_variacao_altitude(df)
acum_evento = calcular_acumulado_evento(df)

status_map = {
    "chovendo":   "🟢 Chovendo agora",
    "parando":    "🟡 Chuva cessando",
    "seco":       "⚪ Sem chuva",
    "indefinido": "⏳ Aguardando dados suficientes"
}
st.info(status_map[estado])

if tendencia > 0.5:
    tend_label = f"▲ +{tendencia} hPa (subindo)"
elif tendencia < -1.5:
    tend_label = f"▼ {tendencia} hPa (⚠️ queda rápida)"
elif tendencia < -0.5:
    tend_label = f"▼ {tendencia} hPa (caindo)"
else:
    tend_label = f"→ {tendencia} hPa (estável)"

# --- Linha 1: atmosfera ---
st.subheader("Leitura atual")
c1, c2, c3 = st.columns(3)
c1.metric("🌡️ Temperatura", f"{ultima['temp']:.1f} °C")
c2.metric("📊 Pressão", f"{ultima['pres']:.1f} hPa")
c3.metric("⛰️ Altitude", f"{ultima['alt']:.1f} m",
          help="Calculada pela pressão atmosférica. Referência: 1013.25 hPa ao nível do mar.")

# --- Linha 2: chuva ---
st.subheader("Precipitação")
c4, c5, c6, c7 = st.columns(4)
c4.metric(
    f"{emoji} Intensidade",
    intensidade,
    f"{mmh:.1f} mm/h",
    help="Baseado no volume dos últimos 5 min e na taxa entre pulsos."
)
c5.metric(
    "⛈️ Acumulado — evento",
    f"{acum_evento:.2f} mm",
    help="Total desde o início da chuva atual. Zera após 10 min sem chuva."
)
c6.metric(
    "🕐 Acumulado — última hora",
    f"{acum_horario:.2f} mm",
    help="Total da última hora rolante. Calculado diretamente do banco."
)
c7.metric(
    "📅 Acumulado — hoje",
    f"{acum_diario:.2f} mm",
    help="Total desde meia-noite. Calculado diretamente do banco."
)

# --- Linha 3: tendências ---
st.subheader("Tendências")
c8, c9 = st.columns(2)
c8.metric("📈 Pressão (30 min)", tend_label)
c9.metric("⛰️ Variação de altitude", f"{var_alt:+.1f} m",
          help="Diferença entre altitude média recente e a mais antiga carregada.")

st.divider()

# --- Gráficos ---
st.subheader("Histórico recente")

tab1, tab2, tab3, tab4 = st.tabs([
    "🌡️ Temperatura",
    "📊 Pressão & Altitude",
    "🌧️ Precipitação",
    "📋 Dados brutos"
])

with tab1:
    st.line_chart(preparar_grafico(df, 'temp'), color=["#e05c2a"])
    st.caption("Temperatura em °C ao longo do tempo.")

with tab2:
    col_p, col_a = st.columns(2)
    with col_p:
        st.markdown("**Pressão atmosférica (hPa)**")
        st.line_chart(preparar_grafico(df, 'pres'), color=["#7c3aed"])
        st.caption(f"Tendência 30 min: {tend_label}. Quedas > 1.5 hPa indicam chuva se aproximando.")
    with col_a:
        st.markdown("**Altitude estimada (m)**")
        st.line_chart(preparar_grafico(df, 'alt'), color=["#2a7ae0"])
        st.caption("Altitude calculada pela pressão. Variações indicam mudanças atmosféricas.")

with tab3:
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("**Por intervalo (5s)**")
        st.bar_chart(preparar_grafico(df, 'chuva'), color=["#1d9e75"])
        st.caption("Precipitação em mm por intervalo de 5 segundos.")
    with col_b:
        st.markdown("**Acumulado contínuo**")
        df['chuva_acumulada'] = df['chuva'].cumsum()
        st.line_chart(preparar_grafico(df, 'chuva_acumulada'), color=["#0f6e56"])
        st.caption("Acumulado das leituras carregadas (últimas 1000).")
    with col_c:
        st.markdown("**Total por hora**")
        df_horas = preparar_acumulado_por_hora(df)
        if not df_horas.empty:
            df_horas['hora'] = df_horas['hora'].dt.strftime('%d/%m %H:%M')
            st.bar_chart(df_horas.set_index('hora')['chuva'], color=["#0a4d38"])
        st.caption("Chuva total agrupada por hora do dia.")

with tab4:
    colunas = ['timestamp', 'temp', 'pres', 'alt', 'chuva']
    if 'intervalo_ms' in df.columns:
        colunas.append('intervalo_ms')
    renomear = {
        'timestamp':    'Data/Hora',
        'temp':         'Temp (°C)',
        'pres':         'Pressão (hPa)',
        'alt':          'Altitude (m)',
        'chuva':        'Chuva (mm)',
        'intervalo_ms': 'Intervalo (ms)'
    }
    st.dataframe(
        df[colunas]
        .sort_values('timestamp', ascending=False)
        .rename(columns=renomear),
        use_container_width=True,
        hide_index=True
    )

st.divider()
st.caption(f"Atualizado em: {datetime.now().strftime('%H:%M:%S')} · refresh a cada 10s")