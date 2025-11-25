#!/bin/bash

# Script para forzar reinicio completo de la aplicación

echo "🧹 Limpieza completa y reinicio forzado..."
echo "=========================================="

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 1. Matar todos los procesos
print_status "Matando todos los procesos de la aplicación..."
pkill -f "react-scripts\|api_server\|websocket_server" 2>/dev/null
sleep 3

# 2. Limpiar caché del frontend
print_status "Limpiando caché del frontend..."
cd frontend
rm -rf node_modules/.cache
rm -rf build
npm cache clean --force
cd ..

# 3. Limpiar caché del navegador (instrucciones)
print_status "Limpiando caché del navegador..."
echo "📱 IMPORTANTE: Cierra completamente tu navegador y ábrelo de nuevo"
echo "   O usa una ventana de incógnito/privada"

# 4. Reiniciar aplicación
print_status "Reiniciando aplicación..."
./start_app.sh


















