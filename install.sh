#!/bin/bash
set -e

echo "=========================================="
echo "   🤖 ESKMC MEDIA BOT - INSTALADOR"
echo "=========================================="
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no encontrado."
    echo "🔗 Instala Python3 desde: https://python.org/downloads"
    exit 1
fi

echo "✅ Python3 detectado: $(python3 --version)"

# Crear entorno virtual
echo "📦 Creando entorno virtual..."
python3 -m venv venv

# Activar entorno virtual
echo "🚀 Activando entorno virtual..."
source venv/bin/activate

# Actualizar pip
echo "⬆️  Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias
echo "📥 Instalando dependencias..."
pip install -r requirements.txt

# Crear carpetas necesarias
echo "📁 Creando estructura de carpetas..."
mkdir -p data logs

# Crear .env si no existe
if [ ! -f .env ]; then
    echo "⚙️  Creando archivo .env..."
    cp .env.example .env
    echo ""
    echo "=========================================="
    echo "   ⚠️  CONFIGURACION NECESARIA"
    echo "=========================================="
    echo ""
    echo "Abre el archivo .env con un editor de texto"
    echo "y completa las siguientes variables:"
    echo ""
    echo "    DISCORD_TOKEN=tu_token_aqui"
    echo "    GUILD_ID=id_de_tu_servidor"
    echo "    MEDIA_MANAGER_ROLE_ID=id_del_rol_manager"
    echo "    MEDIA_STAFF_ROLE_ID=id_del_rol_staff"
    echo "    LOG_CHANNEL_ID=id_canal_logs"
    echo ""
    echo "Para obtener estos IDs:"
    echo "1. Activa Modo Desarrollador en Discord (Ajustes > Avanzado)"
    echo "2. Click derecho en servidor/canal/rol > 'Copiar ID'"
    echo ""
    read -p "Presiona ENTER para continuar..."
else
    echo "✅ Archivo .env ya existe."
fi

echo ""
echo "=========================================="
echo "   ✅ INSTALACION COMPLETADA"
echo "=========================================="
echo ""
echo "Para iniciar el bot:"
echo "   1. Edita el archivo .env con tus datos"
echo "   2. Ejecuta: ./iniciar.sh"
echo ""
