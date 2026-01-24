@echo off
title AEON - MODO PORTATIL (USB)
color 0A

echo ==================================================
echo      INICIANDO AEON VIA PENDRIVE
echo ==================================================

:: 1. Descobre onde estamos (Raiz do Projeto no USB)
set "AEON_DIR=%~dp0"
:: Define a raiz do Pendrive (uma pasta acima do projeto)
pushd "%AEON_DIR%.."
set "USB_ROOT=%CD%"
popd

:: 2. Configura caminhos do Python Portatil e Ollama
:: Estrutura esperada no Pendrive:
::  [USB]:\AeonProject\  (O codigo)
::  [USB]:\Python\       (WinPython ou Python Embed)
::  [USB]:\Ollama\       (ollama.exe)
::  [USB]:\AeonData\     (Onde ficarao os modelos pesados)

set "PYTHON_EXE=%USB_ROOT%\Python\python.exe"
set "OLLAMA_EXE=%USB_ROOT%\Ollama\ollama.exe"
set "OLLAMA_MODELS=%USB_ROOT%\AeonData\ollama_models"
set "VSCODE_EXE=%USB_ROOT%\VSCode\Code.exe"

:: Verifica Python
if not exist "%PYTHON_EXE%" (
    color 0C
    echo [ERRO CRITICO] Python nao encontrado em:
    echo %PYTHON_EXE%
    echo.
    echo ESTRUTURA NECESSARIA NO PENDRIVE:
    echo   [Raiz]\AeonProject\  (Esta pasta)
    echo   [Raiz]\Python\       (Copie a pasta do python do WinPython para ca)
    echo   [Raiz]\Ollama\       (Copie ollama.exe para ca)
    echo   [Raiz]\VSCode\       (Opcional: VS Code Portatil)
    echo.
    pause
    exit
)

:: Adiciona Ollama ao PATH temporario desta sessao
set "PATH=%USB_ROOT%\Ollama;%PATH%"
set "OLLAMA_MODELS=%OLLAMA_MODELS%"

:: 3. Inicia o Servidor Ollama (Cerebro Local) apontando para o USB
if exist "%OLLAMA_EXE%" (
    echo [BOOT] Iniciando Servidor Ollama...
    :: Cria a pasta de modelos se nao existir
    if not exist "%OLLAMA_MODELS%" mkdir "%OLLAMA_MODELS%"
    :: Inicia em background
    start "Ollama Server USB" /B "%OLLAMA_EXE%" serve
) else (
    echo [AVISO] Ollama nao encontrado. Modo offline indisponivel.
)

:MENU
cls
echo ==================================================
echo      AEON PORTATIL - MENU PRINCIPAL
echo ==================================================
echo.
echo  [1] Iniciar Aeon (Assistente)
if exist "%VSCODE_EXE%" echo  [2] Abrir Projeto no VS Code (Dev Mode)
echo  [3] Sair
echo.
set /p op="Escolha: "

if "%op%"=="1" goto RUN_AEON
if "%op%"=="2" goto RUN_CODE
if "%op%"=="3" exit
goto MENU

:RUN_CODE
start "" "%VSCODE_EXE%" "%AEON_DIR%"
goto MENU

:RUN_AEON
echo [BOOT] Executando Main...
"%PYTHON_EXE%" "%AEON_DIR%main.py"
pause
goto MENU