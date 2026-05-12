@echo off
title Sistema Pluviometro AmazonRain
cls

echo ======================================================
echo    INICIALIZANDO SISTEMA DE MONITORAMENTO (MANAUS)
echo ======================================================

:: 1. Define caminhos absolutos PRIMEIRO, antes de tudo
set "SRC_DIR=%~dp0"
set "SCRIPTS_DIR=%SRC_DIR%scripts"
set "COLETOR=%SCRIPTS_DIR%\coletor.py"
set "DASHBOARD=%SCRIPTS_DIR%\dashboard.py"
set "DADOS_DIR=%SRC_DIR%dados"
set "VENV_DIR=%SRC_DIR%venv"

:: 2. Garante que a pasta de dados existe
if not exist "%DADOS_DIR%" mkdir "%DADOS_DIR%"

:: 3. Encontra o Python
set PYTHON_EXE=python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado no PATH.
    pause
    exit
)

:: 4. Cria o ambiente virtual se ainda não existir
if not exist "%VENV_DIR%" (
    echo [INFO] Criando ambiente virtual...
    %PYTHON_EXE% -m venv "%VENV_DIR%"
)

:: 5. Ativa o ambiente virtual
call "%VENV_DIR%\Scripts\activate.bat"

:: 6. Instala dependências
echo [INFO] Verificando dependências...
pip install -r "%SCRIPTS_DIR%\requirements.txt" --quiet

:: 7. Inicia o Coletor em segundo plano
echo [INFO] Iniciando Coletor...
start /b python "%COLETOR%"

:: 8. Inicia o Dashboard
echo [INFO] Abrindo Dashboard...
python -m streamlit run "%DASHBOARD%"

echo ======================================================
echo SISTEMA EM EXECUCAO!
echo ======================================================
pause