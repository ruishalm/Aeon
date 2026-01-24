@echo off
title AEON - CONFIGURACAO LOCAL
color 0B
echo ==================================================
echo      INSTALANDO DEPENDENCIAS NO COMPUTADOR
echo ==================================================

echo [INFO] Atualizando o instalador (pip)...
python -m pip install --upgrade pip

echo [INFO] Instalando bibliotecas do requirements.txt...
python -m pip install --no-warn-script-location -r requirements.txt

echo.
echo ==================================================
echo      CONFIGURACAO CONCLUIDA!
echo ==================================================
pause