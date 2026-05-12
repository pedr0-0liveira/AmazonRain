@echo off
title Sistema Pluviometro AmazonRain
cls

echo ======================================================
echo    INICIALIZANDO SISTEMA DE MONITORAMENTO (MANAUS)
echo ======================================================

:: 1. Tenta encontrar o Python padrão do Windows (não o do MSYS2)
set PYTHON_EXE=python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado no PATH.
    pause
    exit
)

:: 2. Garante que o PIP esteja instalado e atualizado
echo [INFO] Verificando instalador de pacotes...
%PYTHON_EXE% -m ensurepip
%PYTHON_EXE% -m pip install --upgrade pip

:: 3. Instala as bibliotecas necessarias
echo [INFO] Verificando bibliotecas...
%PYTHON_EXE% -m pip install pyserial pandas streamlit

:: 4. Ajusta o diretório de trabalho para a pasta onde o .bat está
cd /d "%~dp0"

:: 5. Executa o Coletor
echo [INFO] Iniciando Coletor...
:: Se o .bat está na pasta AmazonRain, o comando correto é:
start /b python scripts\coletor.py

:: 6. Executa o Dashboard
echo [INFO] Abrindo Dashboard...
python -m streamlit run scripts\dashboard.py

echo ======================================================
echo SISTEMA EM EXECUCAO!
echo ======================================================
pause