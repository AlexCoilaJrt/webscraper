#!/usr/bin/env python3
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
