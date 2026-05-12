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

:: Cria o ambiente virtual se ainda não existir
set "VENV_DIR=%SRC_DIR%venv"
if not exist "%VENV_DIR%" (
    echo [INFO] Criando ambiente virtual...
    %PYTHON_EXE% -m venv "%VENV_DIR%"
)

:: Ativa o ambiente virtual
call "%VENV_DIR%\Scripts\activate.bat"

:: Instala dependências dentro do venv
echo [INFO] Verificando dependências...
pip install -r "%SCRIPTS_DIR%\requirements.txt" --quiet

:: Define caminhos absolutos a partir da pasta do .bat
set "SRC_DIR=%~dp0"
set "SCRIPTS_DIR=%SRC_DIR%scripts"
set "COLETOR=%SCRIPTS_DIR%\coletor.py"
set "DASHBOARD=%SCRIPTS_DIR%\dashboard.py"
set "DADOS_DIR=%SRC_DIR%dados"

:: Garante que a pasta de dados existe
if not exist "%DADOS_DIR%" mkdir "%DADOS_DIR%"

:: Inicia o Coletor em segundo plano
echo [INFO] Iniciando Coletor...
start /b %PYTHON_EXE% "%COLETOR%"

:: Inicia o Dashboard
echo [INFO] Abrindo Dashboard...
%PYTHON_EXE% -m streamlit run "%DASHBOARD%"

echo ======================================================
echo SISTEMA EM EXECUCAO!
echo ======================================================
pause