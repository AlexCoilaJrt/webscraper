#!/bin/bash

# 🕷️ Web Scraper - Script de Inicio Simplificado (SIN WebSocket)
# Este script inicia solo el backend y frontend

echo "🚀 Iniciando Web Scraper (Versión Simplificada)..."
echo "=================================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar mensajes
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 no está instalado"
    exit 1
fi

# Verificar si Node.js está instalado
if ! command -v node &> /dev/null; then
    print_error "Node.js no está instalado"
    exit 1
fi

# Verificar dependencias Python
print_status "Verificando dependencias Python..."
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt no encontrado"
    exit 1
fi

# Instalar dependencias Python si es necesario
if [ ! -d "venv" ]; then
    print_status "Creando entorno virtual Python..."
    python3 -m venv venv
fi

print_status "Activando entorno virtual..."
source venv/bin/activate

print_status "Instalando dependencias Python..."
pip install -r requirements.txt

# Verificar dependencias Node.js
print_status "Verificando dependencias Node.js..."
if [ ! -d "frontend/node_modules" ]; then
    print_status "Instalando dependencias Node.js..."
    cd frontend
    npm install
    cd ..
fi

# Crear directorio de imágenes si no existe
if [ ! -d "scraped_images" ]; then
    print_status "Creando directorio de imágenes..."
    mkdir scraped_images
fi

# Función para limpiar procesos al salir
cleanup() {
    print_status "Cerrando aplicaciones..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Capturar señales de interrupción
trap cleanup SIGINT SIGTERM

# Iniciar backend
print_status "Iniciando backend API..."
python backend/core/api_server.py &
BACKEND_PID=$!

# Esperar a que el backend esté listo
print_status "Esperando a que el backend esté listo..."
sleep 5

# Verificar si el backend está corriendo
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    print_error "Error iniciando el backend"
    exit 1
fi

print_success "Backend iniciado correctamente (PID: $BACKEND_PID)"

# Iniciar frontend
print_status "Iniciando frontend React..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

# Esperar a que el frontend esté listo
print_status "Esperando a que el frontend esté listo..."
sleep 10

print_success "Frontend iniciado correctamente (PID: $FRONTEND_PID)"

echo ""
echo "🎉 ¡Web Scraper iniciado correctamente!"
echo "=================================================="
echo "📊 Dashboard: http://localhost:3001"
echo "🔧 API: http://localhost:5001"
echo "🔑 Credenciales:"
echo "   Usuario: admin"
echo "   Contraseña: AdminSecure2024!"
echo "📱 IMPORTANTE:"
echo "   1. Abre http://localhost:3001"
echo "   2. Presiona Ctrl+Shift+R (recarga forzada)"
echo "   3. O F12 → Network → Disable cache → Recargar"
echo ""
echo "Presiona Ctrl+C para detener"
echo ""

# Mantener el script corriendo
wait













