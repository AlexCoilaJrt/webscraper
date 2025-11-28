#!/bin/bash

echo "🔄 Reiniciando sistema Web Scraper..."

# Matar todos los procesos
echo "⏹️  Deteniendo procesos existentes..."
pkill -f "react-scripts\|npm start\|python.*api_server" 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null
lsof -ti:5001 | xargs kill -9 2>/dev/null

# Esperar un momento
sleep 3

# Iniciar backend
echo "🚀 Iniciando backend..."
cd "/Users/usuario/Documents/scraping 2"
source venv/bin/activate
python backend/core/api_server.py &
BACKEND_PID=$!

# Esperar a que el backend inicie
sleep 5

# Verificar que el backend esté funcionando
if curl -s http://localhost:5001/api/health > /dev/null; then
    echo "✅ Backend iniciado correctamente"
else
    echo "❌ Error iniciando backend"
    exit 1
fi

# Iniciar frontend
echo "🎨 Iniciando frontend..."
cd "/Users/usuario/Documents/scraping 2/frontend"
BROWSER=none npm start &
FRONTEND_PID=$!

# Esperar a que el frontend inicie
sleep 15

# Verificar que el frontend esté funcionando
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend iniciado correctamente"
else
    echo "❌ Error iniciando frontend"
    exit 1
fi

echo ""
echo "🎉 Sistema iniciado correctamente!"
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend: http://localhost:5001"
echo ""
echo "🔐 Credenciales:"
echo "   Administrador: admin / AdminSecure2024!"
echo "   Usuario: usuario / usuario123"
echo ""
echo "💡 Si el navegador muestra 'You need to enable JavaScript':"
echo "   1. Presiona Ctrl+Shift+R (o Cmd+Shift+R en Mac)"
echo "   2. O abre una ventana privada/incógnito"
echo "   3. O ve a Configuración > Limpiar datos de navegación"
echo ""

# Mantener el script ejecutándose
wait




















