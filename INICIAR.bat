@echo off
chcp 65001 >nul
title EskMC Media Bot
color 0B
cls

echo ==========================================
echo    ESKMC MEDIA BOT
echo ==========================================
echo.

if not exist venv (
    echo [ERROR] Entorno virtual no encontrado.
    echo Ejecuta primero: instalar.bat
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
python main.py

echo.
echo [AVISO] El bot se ha detenido.
pause
