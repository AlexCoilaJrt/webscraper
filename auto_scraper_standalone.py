#!/usr/bin/env python3
"""
Scraper automático independiente - No requiere servidor API
"""

import json
import logging
import time
from datetime import datetime
import sys
import os

# Agregar el directorio actual al path para importar los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hybrid_crawler import HybridDataCrawler
from optimized_scraper import SmartScraper

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

def save_articles_to_db(articles, category='', newspaper='', region=''):
    """Guardar artículos en la base de datos SQLite"""
    try:
        import sqlite3
        from datetime import datetime
        
        conn = sqlite3.connect('scraping_data.db')
        cursor = conn.cursor()
        
        for article in articles:
            # Verificar si el artículo ya existe
            cursor.execute("SELECT id FROM articles WHERE url = ?", (article.get('url', ''),))
            if cursor.fetchone():
                continue  # Saltar si ya existe
            
            # Insertar nuevo artículo
            cursor.execute("""
                INSERT INTO articles (
                    title, content, url, summary, author, published_date, 
                    scraped_at, category, newspaper, region, images_found, 
                    images_downloaded, images_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                article.get('title', ''),
                article.get('content', ''),
                article.get('url', ''),
                article.get('summary', ''),
                article.get('author', ''),
                article.get('published_date', ''),
                datetime.now().isoformat(),
                category,
                newspaper,
                region,
                article.get('images_found', 0),
                article.get('images_downloaded', 0),
                json.dumps(article.get('images_data', []))
            ))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        logging.error(f"❌ Error guardando en base de datos: {e}")
        return False

def execute_scraping_standalone(schedule):
    """Ejecutar scraping independiente (sin API)"""
    try:
        logging.info(f"🚀 Iniciando scraping: {schedule['name']}")
        
        url = schedule["url"]
        method = schedule["method"]
        max_articles = schedule["max_articles"]
        max_images = schedule["max_images"]
        category = schedule["category"]
        newspaper = schedule["newspaper"]
        region = schedule["region"]
        
        articles = []
        
        if method == "hybrid":
            # Usar HybridDataCrawler
            crawler = HybridDataCrawler()
            try:
                articles = crawler.hybrid_crawl_articles(url, max_articles)
                logging.info(f"✅ HybridDataCrawler: {len(articles)} artículos encontrados")
            finally:
                crawler.close()
                
        elif method == "optimized":
            # Usar SmartScraper
            scraper = SmartScraper(max_workers=10)
            try:
                articles = scraper.crawl_and_scrape_parallel(url, max_articles=max_articles, extract_images=True)
                logging.info(f"✅ SmartScraper: {len(articles)} artículos encontrados")
            finally:
                scraper.close()
                
        elif method == "webscraping":
            # Usar método básico con requests
            import requests
            from bs4 import BeautifulSoup
            
            try:
                response = requests.get(url, timeout=30)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extraer enlaces básicos
                links = []
                for link in soup.find_all('a', href=True):
                    href = link.get('href')
                    if href and len(href) > 20:
                        links.append(href)
                
                # Crear artículos básicos
                articles = []
                for i, link in enumerate(links[:max_articles]):
                    articles.append({
                        'title': f'Artículo {i+1}',
                        'url': link,
                        'content': '',
                        'summary': '',
                        'author': '',
                        'published_date': datetime.now().isoformat(),
                        'images_found': 0,
                        'images_downloaded': 0,
                        'images_data': []
                    })
                
                logging.info(f"✅ Método básico: {len(articles)} artículos encontrados")
            except Exception as e:
                logging.error(f"❌ Error en método básico: {e}")
                articles = []
        
        # Guardar en base de datos
        if articles:
            if save_articles_to_db(articles, category, newspaper, region):
                logging.info(f"✅ {len(articles)} artículos guardados en base de datos")
            else:
                logging.error("❌ Error guardando artículos en base de datos")
        
        logging.info(f"✅ Scraping completado: {schedule['name']} - {len(articles)} artículos")
        return True
        
    except Exception as e:
        logging.error(f"❌ Error ejecutando scraping {schedule['name']}: {e}")
        return False

def main():
    """Función principal"""
    logging.info("🕐 Iniciando scraping automático independiente")
    
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
            if execute_scraping_standalone(schedule):
                successful += 1
            else:
                failed += 1
            
            # Esperar entre ejecuciones para no sobrecargar
            time.sleep(30)
    
    logging.info(f"📊 Resumen: {successful} exitosos, {failed} fallidos")
    logging.info("🏁 Scraping automático completado")

if __name__ == "__main__":
    main()
