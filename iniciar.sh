#!/bin/bash

echo "🤖 Iniciando EskMC Media Bot..."
echo ""

if [ ! -d "venv" ]; then
    echo "❌ Entorno virtual no encontrado."
    echo "Ejecuta primero: ./install.sh"
    exit 1
fi

source venv/bin/activate
python3 main.py

echo ""
echo "⚠️ El bot se ha detenido."
read -p "Presiona ENTER para salir..."
