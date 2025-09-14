#!/bin/bash

# Script para configurar Git y subir a GitHub

echo "🚀 Configurando repositorio Git para Web Scraper Inteligente"
echo "============================================================"

# Inicializar Git si no existe
if [ ! -d ".git" ]; then
    echo "📁 Inicializando repositorio Git..."
    git init
else
    echo "✅ Repositorio Git ya existe"
fi

# Agregar todos los archivos
echo "📦 Agregando archivos al repositorio..."
git add .

# Commit inicial
echo "💾 Creando commit inicial..."
git commit -m "🎉 Initial commit: Web Scraper Inteligente

✨ Características:
- 🧠 Análisis inteligente de páginas web
- 🔄 Scraping automático cada 5 horas
- 📊 1,088 artículos extraídos de 13 periódicos
- 🖼️ 119 imágenes descargadas
- 📈 74 sesiones de scraping
- 🎨 Interfaz React moderna
- 📤 Exportación a Excel
- 🗄️ Base de datos SQLite

🗞️ Periódicos soportados:
- Elmundo (324 artículos)
- La Vanguardia (150 artículos)
- El Popular (129 artículos)
- Trome (110 artículos)
- Ojo (102 artículos)
- Diario Sin Fronteras (66 artículos)
- El Comercio (57 artículos)
- Y más...

🛠️ Tecnologías:
- Backend: Python, Flask, SQLite, Selenium
- Frontend: React, TypeScript, Material-UI
- Scraping: BeautifulSoup, Requests, WebDriver"

echo ""
echo "🎯 Próximos pasos:"
echo "1. Crear repositorio en GitHub:"
echo "   - Ve a https://github.com/new"
echo "   - Nombre: web-scraper-inteligente"
echo "   - Descripción: Sistema completo de web scraping con análisis inteligente"
echo "   - Marca como público"
echo ""
echo "2. Conectar repositorio local con GitHub:"
echo "   git remote add origin https://github.com/TU-USUARIO/web-scraper-inteligente.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "3. (Opcional) Crear release:"
echo "   - Ve a GitHub > Releases > Create a new release"
echo "   - Tag: v1.0.0"
echo "   - Título: Web Scraper Inteligente v1.0.0"
echo "   - Descripción: Primera versión estable con todas las funcionalidades"
echo ""
echo "✅ ¡Repositorio Git configurado exitosamente!"
echo "📋 Archivos incluidos:"
echo "   - README.md (documentación completa)"
echo "   - requirements.txt (dependencias Python)"
echo "   - .gitignore (archivos excluidos)"
echo "   - LICENSE (licencia MIT)"
echo "   - Código fuente completo"
echo "   - Configuración de scraping automático"
