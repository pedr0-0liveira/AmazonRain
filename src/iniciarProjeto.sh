#!/bin/bash

echo "======================================================"
echo "   INICIALIZANDO SISTEMA DE MONITORAMENTO (MANAUS)"
echo "======================================================"

# Caminhos absolutos a partir da pasta do script
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPTS_DIR="$SRC_DIR/scripts"
DADOS_DIR="$SRC_DIR/dados"
VENV_DIR="$SRC_DIR/venv"

# Garante que a pasta de dados existe
mkdir -p "$DADOS_DIR"

# Cria o ambiente virtual se não existir
if [ ! -d "$VENV_DIR" ]; then
    echo "[INFO] Criando ambiente virtual..."
    python3 -m venv "$VENV_DIR"
fi

# Ativa o ambiente virtual
source "$VENV_DIR/bin/activate"

# Instala dependências
echo "[INFO] Verificando dependências..."
pip install -r "$SCRIPTS_DIR/requirements.txt" --quiet

# Inicia o coletor em background e salva o PID
echo "[INFO] Iniciando Coletor..."
python3 "$SCRIPTS_DIR/coletor.py" &
COLETOR_PID=$!
echo "[INFO] Coletor iniciado com PID: $COLETOR_PID"

# Inicia o dashboard (bloqueia até CTRL+C)
echo "[INFO] Abrindo Dashboard..."
echo "[INFO] Pressione CTRL+C para encerrar o sistema completo."
python3 -m streamlit run "$SCRIPTS_DIR/dashboard.py"

# Quando o dashboard encerrar, mata o coletor
echo ""
echo "[INFO] Dashboard encerrado. Parando o Coletor..."
kill $COLETOR_PID 2>/dev/null
echo "[INFO] Coletor encerrado com segurança."
echo "======================================================"
echo "SISTEMA ENCERRADO."
echo "======================================================"