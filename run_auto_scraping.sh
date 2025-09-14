#!/bin/bash
# Script de scraping automático
# Ejecutar desde cron job

# Cambiar al directorio del proyecto
cd /Users/usuario/Documents/scraping\ 2

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Ejecutar scraping automático independiente
python auto_scraper_standalone.py

# Log de ejecución
echo "$(date): Scraping automático ejecutado" >> auto_scraping.log
