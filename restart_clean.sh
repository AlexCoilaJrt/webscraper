#!/bin/bash

echo "🧹 Limpiando y reiniciando aplicación..."

# Matar todos los procesos
echo "🛑 Deteniendo procesos..."
pkill -f "react-scripts" 2>/dev/null
pkill -f "api_server.py" 2>/dev/null
pkill -f "websocket_server.py" 2>/dev/null
sleep 2

# Limpiar cache del navegador (si es posible)
echo "🧹 Limpiando cache..."

# Limpiar cache de npm
cd frontend
rm -rf node_modules/.cache
rm -rf build
npm cache clean --force
cd ..

# Limpiar cache de Python
rm -rf __pycache__
rm -rf venv/__pycache__

# Activar entorno virtual
echo "📦 Activando entorno virtual..."
source venv/bin/activate

# Instalar dependencias
echo "📋 Verificando dependencias..."
pip install -r requirements.txt

# Iniciar WebSocket
echo "🔌 Iniciando WebSocket..."
python backend/core/websocket_server.py &
WEBSOCKET_PID=$!
sleep 2

# Iniciar Backend
echo "🚀 Iniciando Backend..."
python backend/core/api_server.py &
BACKEND_PID=$!
sleep 3

# Verificar que el backend esté funcionando
echo "🔍 Verificando backend..."
for i in {1..10}; do
    if curl -s http://localhost:5002/api/health > /dev/null; then
        echo "✅ Backend funcionando en puerto 5002"
        break
    else
        echo "⏳ Esperando backend... ($i/10)"
        sleep 1
    fi
done

# Iniciar Frontend
echo "🌐 Iniciando Frontend..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "🎉 ¡Aplicación reiniciada!"
echo "================================"
echo "📊 Frontend: http://localhost:3000"
echo "🔧 Backend: http://localhost:5002"
echo "🔌 WebSocket: ws://localhost:8765"
echo ""
echo "🔑 Credenciales:"
echo "   Usuario: admin"
echo "   Contraseña: AdminSecure2024!"
echo ""
echo "📱 IMPORTANTE:"
echo "   1. Abre http://localhost:3000"
echo "   2. Presiona Ctrl+Shift+R (recarga forzada)"
echo "   3. O F12 → Network → Disable cache → Recargar"
echo ""
echo "Presiona Ctrl+C para detener"

# Función de limpieza
cleanup() {
    echo ""
    echo "🛑 Deteniendo aplicación..."
    kill $WEBSOCKET_PID 2>/dev/null
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Mantener el script corriendo
wait


















