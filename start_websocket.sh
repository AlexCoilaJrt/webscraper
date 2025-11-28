#!/bin/bash

# Script para iniciar el servidor WebSocket
echo "🚀 Iniciando servidor WebSocket..."

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no está instalado"
    exit 1
fi

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    echo "📦 Activando entorno virtual..."
    source venv/bin/activate
fi

# Instalar dependencias si es necesario
echo "📋 Verificando dependencias..."
pip install -r requirements.txt

# Iniciar servidor WebSocket
echo "🌐 Iniciando servidor WebSocket en puerto 8765..."
python3 backend/core/websocket_server.py


















