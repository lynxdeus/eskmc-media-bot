@echo off
chcp 65001 >nul
title Instalador EskMC Media Bot
color 0A
cls

echo ==========================================
echo    ESKMC MEDIA BOT - INSTALADOR
echo ==========================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado.
    echo Descarga Python desde: https://python.org/downloads
    echo IMPORTANTE: Marca "Add Python to PATH" al instalar.
    pause
    exit /b 1
)

echo [OK] Python detectado.

REM Crear entorno virtual
echo [INFO] Creando entorno virtual...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] No se pudo crear el entorno virtual.
    pause
    exit /b 1
)

REM Activar entorno virtual
echo [INFO] Activando entorno virtual...
call venv\Scripts\activate.bat

REM Actualizar pip
echo [INFO] Actualizando pip...
python -m pip install --upgrade pip >nul 2>&1

REM Instalar dependencias
echo [INFO] Instalando dependencias...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Error instalando dependencias.
    pause
    exit /b 1
)

REM Crear carpetas necesarias
echo [INFO] Creando carpetas...
if not exist data mkdir data
if not exist logs mkdir logs

REM Crear .env si no existe
if not exist .env (
    echo [INFO] Creando archivo .env...
    copy .env.example .env >nul
    echo.
    echo ==========================================
    echo    CONFIGURACION NECESARIA
    echo ==========================================
    echo.
    echo Abre el archivo .env con el Bloc de notas
    echo y completa las siguientes variables:
    echo.
    echo    DISCORD_TOKEN=tu_token_aqui
    echo    GUILD_ID=id_de_tu_servidor
    echo    MEDIA_MANAGER_ROLE_ID=id_del_rol_manager
    echo    MEDIA_STAFF_ROLE_ID=id_del_rol_staff
    echo    LOG_CHANNEL_ID=id_canal_logs
    echo.
    echo Para obtener estos IDs:
    echo 1. Activa Modo Desarrollador en Discord
    echo 2. Click derecho en servidor/canal/rol - Copiar ID
    echo.
    pause
) else (
    echo [OK] Archivo .env ya existe.
)

echo.
echo ==========================================
echo    INSTALACION COMPLETADA
echo ==========================================
echo.
echo Para iniciar el bot:
echo    1. Edita el archivo .env con tus datos
echo    2. Ejecuta: INICIAR.bat
echo.
pause
