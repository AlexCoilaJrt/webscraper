#!/bin/bash

# 🧹 Script de Limpieza Completa y Reinicio
# Elimina TODO lo que causa problemas

echo "🧹 LIMPIEZA COMPLETA Y REINICIO"
echo "================================"

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

# 1. Matar TODOS los procesos
print_status "Matando TODOS los procesos..."
pkill -f "react-scripts\|api_server\|websocket_server\|python.*api_server\|python.*websocket" 2>/dev/null
lsof -ti:5001,5002,3000,8765 | xargs kill -9 2>/dev/null || true
sleep 3

# 2. Limpiar frontend completamente
print_status "Limpiando frontend completamente..."
cd frontend
rm -rf node_modules
rm -rf build
rm -rf .cache
rm -rf node_modules/.cache
rm -f package-lock.json
npm cache clean --force
cd ..

# 3. Reinstalar dependencias del frontend
print_status "Reinstalando dependencias del frontend..."
cd frontend
npm install --legacy-peer-deps
cd ..

# 4. Verificar que el backend esté en puerto 5002
print_status "Verificando configuración del backend..."
if grep -q "port=5002" api_server.py; then
    print_success "Backend configurado para puerto 5002"
else
    print_error "Backend NO está en puerto 5002"
fi

# 5. Verificar que el frontend apunte al puerto 5002
print_status "Verificando configuración del frontend..."
if grep -q "localhost:5002" frontend/src/services/api.ts; then
    print_success "Frontend configurado para puerto 5002"
else
    print_error "Frontend NO apunta al puerto 5002"
fi

# 6. Iniciar solo backend y frontend (SIN WebSocket)
print_status "Iniciando aplicación (SIN WebSocket)..."

# Iniciar backend
print_status "Iniciando backend..."
source venv/bin/activate
python api_server.py &
BACKEND_PID=$!
sleep 5

# Verificar backend
if curl -s http://localhost:5002/api/health > /dev/null; then
    print_success "Backend funcionando en puerto 5002"
else
    print_error "Backend NO está funcionando"
    exit 1
fi

# Iniciar frontend
print_status "Iniciando frontend..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

sleep 10

# Verificar frontend
if curl -s http://localhost:3000 > /dev/null; then
    print_success "Frontend funcionando en puerto 3000"
else
    print_error "Frontend NO está funcionando"
    exit 1
fi

echo ""
echo "🎉 ¡APLICACIÓN INICIADA CORRECTAMENTE!"
echo "======================================"
echo "📊 Frontend: http://localhost:3000"
echo "🔧 Backend: http://localhost:5002"
echo "🔑 Credenciales:"
echo "   Usuario: admin"
echo "   Contraseña: AdminSecure2024!"
echo ""
echo "📱 INSTRUCCIONES CRÍTICAS:"
echo "1. Abre http://localhost:3000"
echo "2. Presiona Ctrl+Shift+R (recarga forzada)"
echo "3. O abre una ventana de incógnito"
echo "4. Si sigue fallando, cierra COMPLETAMENTE el navegador"
echo ""
echo "Presiona Ctrl+C para detener"

# Mantener corriendo
wait


















