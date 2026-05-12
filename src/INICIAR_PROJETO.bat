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
set "PID_FILE=%DADOS_DIR%\coletor.pid"

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

:: 4. Cria o ambiente virtual se ainda nao existir
if not exist "%VENV_DIR%" (
    echo [INFO] Criando ambiente virtual...
    %PYTHON_EXE% -m venv "%VENV_DIR%"
)

:: 5. Ativa o ambiente virtual
call "%VENV_DIR%\Scripts\activate.bat"

:: 6. Instala dependencias
echo [INFO] Verificando dependencias...
pip install -r "%SCRIPTS_DIR%\requirements.txt" --quiet

:: 7. Inicia o Coletor e salva o PID dele
echo [INFO] Iniciando Coletor...
start /b python "%COLETOR%"

:: Captura o PID do processo python recem criado
for /f "tokens=2" %%a in ('tasklist /fi "imagename eq python.exe" /fo list ^| findstr "PID"') do (
    set COLETOR_PID=%%a
    goto :pid_capturado
)
:pid_capturado
echo %COLETOR_PID% > "%PID_FILE%"
echo [INFO] Coletor iniciado com PID: %COLETOR_PID%

:: 8. Inicia o Dashboard (bloqueia aqui ate CTRL+C)
echo [INFO] Abrindo Dashboard...
echo [INFO] Pressione CTRL+C para encerrar o sistema completo.
python -m streamlit run "%DASHBOARD%"

:: 9. Quando o dashboard encerra, mata o coletor
echo.
echo [INFO] Dashboard encerrado. Parando o Coletor...
if exist "%PID_FILE%" (
    set /p SAVED_PID=<"%PID_FILE%"
    taskkill /PID %SAVED_PID% /F >nul 2>nul
    del "%PID_FILE%"
    echo [INFO] Coletor encerrado com segurança.
) else (
    echo [AVISO] Arquivo PID nao encontrado. Encerrando todos os processos python...
    taskkill /IM python.exe /F >nul 2>nul
)

echo ======================================================
echo SISTEMA ENCERRADO.
echo ======================================================
pause