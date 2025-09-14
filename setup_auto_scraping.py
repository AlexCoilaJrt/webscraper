#!/usr/bin/env python3
"""
Script para configurar scraping automático
"""

import os
import sys
import json
from datetime import datetime, timedelta

def create_auto_scraping_config():
    """Crear configuración para scraping automático"""
    
    config = {
        "auto_scraping": {
            "enabled": True,
            "schedules": [
                {
                    "name": "Noticias Matutinas",
                    "url": "https://elcomercio.pe/",
                    "method": "hybrid",
                    "max_articles": 20,
                    "max_images": 10,
                    "category": "General",
                    "newspaper": "El Comercio",
                    "region": "Nacional",
                    "cron_schedule": "0 8 * * *",  # Todos los días a las 8:00 AM
                    "enabled": True
                },
                {
                    "name": "Noticias Vespertinas",
                    "url": "https://elpopular.pe/",
                    "method": "optimized",
                    "max_articles": 15,
                    "max_images": 8,
                    "category": "General",
                    "newspaper": "El Popular",
                    "region": "Nacional",
                    "cron_schedule": "0 18 * * *",  # Todos los días a las 6:00 PM
                    "enabled": True
                },
                {
                    "name": "Noticias Diario Sin Fronteras",
                    "url": "https://diariosinfronteras.com.pe/",
                    "method": "hybrid",
                    "max_articles": 25,
                    "max_images": 15,
                    "category": "Regional",
                    "newspaper": "Diario Sin Fronteras",
                    "region": "Nacional",
                    "cron_schedule": "0 12 * * *",  # Todos los días a las 12:00 PM
                    "enabled": True
                }
            ]
        }
    }
    
    # Guardar configuración
    with open('auto_scraping_config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("✅ Configuración de scraping automático creada")
    return config

def create_cron_script():
    """Crear script para ejecutar desde cron"""
    
    script_content = '''#!/bin/bash
# Script de scraping automático
# Ejecutar desde cron job

# Cambiar al directorio del proyecto
cd /Users/usuario/Documents/scraping\ 2

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Ejecutar scraping automático
python auto_scraper.py

# Log de ejecución
echo "$(date): Scraping automático ejecutado" >> auto_scraping.log
'''
    
    with open('run_auto_scraping.sh', 'w') as f:
        f.write(script_content)
    
    # Hacer ejecutable
    os.chmod('run_auto_scraping.sh', 0o755)
    
    print("✅ Script de cron creado: run_auto_scraping.sh")

def create_auto_scraper():
    """Crear el script principal de scraping automático"""
    
    script_content = '''#!/usr/bin/env python3
"""
Scraper automático - Ejecuta scraping programado
"""

import json
import requests
import logging
from datetime import datetime
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_scraping.log'),
        logging.StreamHandler()
    ]
)

def load_config():
    """Cargar configuración de scraping automático"""
    try:
        with open('auto_scraping_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error("❌ Archivo de configuración no encontrado")
        return None

def execute_scraping(schedule):
    """Ejecutar scraping para una programación específica"""
    try:
        logging.info(f"🚀 Iniciando scraping: {schedule['name']}")
        
        # Preparar datos para la API
        data = {
            "url": schedule["url"],
            "max_articles": schedule["max_articles"],
            "max_images": schedule["max_images"],
            "method": schedule["method"],
            "download_images": True,
            "category": schedule["category"],
            "newspaper": schedule["newspaper"],
            "region": schedule["region"]
        }
        
        # Llamar a la API
        response = requests.post(
            "http://localhost:5001/api/start-scraping",
            json=data,
            timeout=300  # 5 minutos timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            logging.info(f"✅ Scraping completado: {schedule['name']}")
            logging.info(f"   - Artículos: {result.get('status', {}).get('articles_found', 0)}")
            logging.info(f"   - Imágenes: {result.get('status', {}).get('images_found', 0)}")
            return True
        else:
            logging.error(f"❌ Error en scraping {schedule['name']}: {response.status_code}")
            return False
            
    except Exception as e:
        logging.error(f"❌ Error ejecutando scraping {schedule['name']}: {e}")
        return False

def main():
    """Función principal"""
    logging.info("🕐 Iniciando scraping automático")
    
    # Cargar configuración
    config = load_config()
    if not config:
        return
    
    auto_config = config.get("auto_scraping", {})
    if not auto_config.get("enabled", False):
        logging.info("⏸️ Scraping automático deshabilitado")
        return
    
    # Ejecutar cada programación
    schedules = auto_config.get("schedules", [])
    successful = 0
    failed = 0
    
    for schedule in schedules:
        if schedule.get("enabled", False):
            if execute_scraping(schedule):
                successful += 1
            else:
                failed += 1
            
            # Esperar entre ejecuciones para no sobrecargar
            time.sleep(30)
    
    logging.info(f"📊 Resumen: {successful} exitosos, {failed} fallidos")
    logging.info("🏁 Scraping automático completado")

if __name__ == "__main__":
    main()
'''
    
    with open('auto_scraper.py', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("✅ Script de scraping automático creado: auto_scraper.py")

def show_cron_instructions():
    """Mostrar instrucciones para configurar cron"""
    
    instructions = """
🔧 INSTRUCCIONES PARA CONFIGURAR CRON JOBS:

1. 📝 Abrir crontab:
   crontab -e

2. 📅 Agregar estas líneas (ajusta los horarios según necesites):
   
   # Scraping automático - Noticias matutinas (8:00 AM)
   0 8 * * * /Users/usuario/Documents/scraping\\ 2/run_auto_scraping.sh
   
   # Scraping automático - Noticias vespertinas (6:00 PM)
   0 18 * * * /Users/usuario/Documents/scraping\\ 2/run_auto_scraping.sh
   
   # Scraping automático - Diario Sin Fronteras (12:00 PM)
   0 12 * * * /Users/usuario/Documents/scraping\\ 2/run_auto_scraping.sh

3. 💾 Guardar y salir (Ctrl+X, luego Y, luego Enter)

4. ✅ Verificar que se guardó:
   crontab -l

📋 FORMATO DE CRON:
   minuto hora día mes día_semana comando
   
   Ejemplos:
   - 0 8 * * *     = Todos los días a las 8:00 AM
   - 0 */6 * * *   = Cada 6 horas
   - 30 9 * * 1-5  = Lunes a Viernes a las 9:30 AM
   - 0 0 1 * *     = Primer día de cada mes a medianoche

🔍 VERIFICAR LOGS:
   tail -f auto_scraping.log
"""
    
    print(instructions)

def main():
    """Función principal"""
    print("🚀 Configurando scraping automático...")
    
    # Crear archivos necesarios
    create_auto_scraping_config()
    create_cron_script()
    create_auto_scraper()
    
    # Mostrar instrucciones
    show_cron_instructions()
    
    print("\n✅ ¡Configuración completada!")
    print("📁 Archivos creados:")
    print("   - auto_scraping_config.json (configuración)")
    print("   - auto_scraper.py (script principal)")
    print("   - run_auto_scraping.sh (script de cron)")
    print("   - auto_scraping.log (logs)")

if __name__ == "__main__":
    main()

