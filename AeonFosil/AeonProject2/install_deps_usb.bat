@echo off
title INSTALAR DEPENDENCIAS NO PENDRIVE
color 0B

echo ==================================================
echo   INSTALADOR DE DEPENDENCIAS (MODO PORTATIL)
echo ==================================================

:: 1. Descobre onde estamos
set "AEON_DIR=%~dp0"
pushd "%AEON_DIR%.."
set "USB_ROOT=%CD%"
popd

:: 2. Define caminho do Python Portatil
set "PYTHON_EXE=%USB_ROOT%\Python\python.exe"

if not exist "%PYTHON_EXE%" (
    color 0C
    echo [ERRO] Python portatil nao encontrado em:
    echo %PYTHON_EXE%
    echo.
    echo Certifique-se de que extraiu o WinPython e renomeou a pasta
    echo interna (que contem python.exe) para 'Python' na raiz do pendrive.
    pause
    exit /b
)

echo [INFO] Usando Python em: %PYTHON_EXE%
echo [INFO] Instalando bibliotecas do requirements.txt...

"%PYTHON_EXE%" -m pip install --no-warn-script-location -r "%AEON_DIR%requirements.txt"

echo.
echo ==================================================
echo      INSTALACAO CONCLUIDA!
echo ==================================================
pause