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
import re

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
        # Permitir usar un archivo de configuración temporal desde variable de entorno
        config_path = os.environ.get('AUTO_SCRAPING_CONFIG', 'auto_scraping_config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"❌ Archivo de configuración no encontrado: {config_path}")
        return None

def normalize_region_value(value):
    if not value or not isinstance(value, str):
        return 'extranjero'
    normalized = re.sub(r'\s+', ' ', value).strip().lower()
    if not normalized:
        return 'extranjero'
    
    nacional_aliases = {
        'nacional', 'nacionales', 'local', 'peru', 'perú', 'peruano', 'peruana',
        'pe', 'national', 'nationwide', 'locales'
    }
    extranjero_aliases = {
        'extranjero', 'internacional', 'international', 'global', 'mundo', 'mundial',
        'world', 'abroad'
    }
    
    if normalized in nacional_aliases:
        return 'nacional'
    if normalized in extranjero_aliases:
        return 'extranjero'
    
    return normalized[:40]

def save_articles_to_db(articles, category='', newspaper='', region=''):
    """Guardar artículos en la base de datos SQLite"""
    try:
        import sqlite3
        from datetime import datetime
        
        manual_category_raw = category.strip() if isinstance(category, str) else ''
        manual_category = ' '.join(manual_category_raw.split()) if manual_category_raw else ''
        if manual_category and len(manual_category) > 80:
            manual_category = manual_category[:80]

        manual_region = normalize_region_value(region)

        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS excluded_newspapers (
                newspaper TEXT PRIMARY KEY,
                excluded_at TEXT NOT NULL
            )
        """)
        
        if newspaper:
            cursor.execute("DELETE FROM excluded_newspapers WHERE newspaper = ?", (newspaper,))
        
        for article in articles:
            # Generar article_id usando el mismo método que improved_scraper.py
            article_url = article.get('url', '')
            article_id = article.get('article_id', '')
            
            # Si no hay article_id, generarlo basado en la URL normalizada
            if not article_id and article_url:
                import hashlib
                from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
                
                # Normalizar URL (igual que en improved_scraper.py)
                try:
                    parsed = urlparse(article_url)
                    path = parsed.path.rstrip('/')
                    if not path:
                        path = '/'
                    
                    # Quitar parámetros de tracking comunes
                    query_params = parse_qs(parsed.query, keep_blank_values=True)
                    tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
                                     'fbclid', 'gclid', 'ref', 'source', 'campaign', 'medium']
                    filtered_params = {k: v for k, v in query_params.items() if k.lower() not in tracking_params}
                    query = urlencode(filtered_params, doseq=True) if filtered_params else ''
                    
                    normalized_url = urlunparse((
                        parsed.scheme,
                        parsed.netloc.lower(),
                        path,
                        parsed.params,
                        query,
                        ''  # Quitar fragment
                    ))
                    
                    # Generar ID basado en URL normalizada
                    url_hash = hashlib.md5(normalized_url.encode()).hexdigest()[:12]
                    article_id = f"article_{url_hash}"
                except Exception as e:
                    logging.warning(f"⚠️ Error generando article_id: {e}")
                    article_id = f"auto_{hash(article_url) % 1000000000000:012d}"
            
            # Si aún no hay article_id, usar hash del título
            if not article_id:
                import hashlib
                title = article.get('title', '')
                if title:
                    title_hash = hashlib.md5(title.encode()).hexdigest()[:12]
                    article_id = f"article_{title_hash}"
                else:
                    article_id = f"auto_{hash(str(article)) % 1000000000000:012d}"
            
            # Verificar si el artículo ya existe por article_id o URL
            cursor.execute("SELECT id FROM articles WHERE article_id = ? OR url = ?", (article_id, article_url))
            existing = cursor.fetchone()
            
            # Preparar datos de imágenes
            images_data = article.get('images_data', [])
            if not isinstance(images_data, list):
                images_data = []
            images_json = json.dumps(images_data) if images_data else "[]"
            images_found = len(images_data) if images_data else article.get('images_found', 0)
            images_downloaded = min(article.get('images_downloaded', 0), images_found)
            
            if existing:
                # Actualizar artículo existente
                cursor.execute("""
                    UPDATE articles SET
                    title = ?, content = ?, summary = ?, author = ?, date = ?, 
                    category = ?, newspaper = ?, url = ?,
                    images_found = ?, images_downloaded = ?, images_data = ?, 
                    scraped_at = ?, region = ?, user_category = ?
                    WHERE article_id = ? OR url = ?
                """, (
                    article.get('title', ''),
                    article.get('content', ''),
                    article.get('summary', ''),
                    article.get('author', ''),
                    article.get('published_date', ''),
                    manual_category or category or 'General',
                    newspaper,
                    article_url,
                    images_found,
                    images_downloaded,
                    images_json,
                    datetime.now().isoformat(),
                    manual_region,
                    manual_category,
                    article_id,
                    article_url
                ))
            else:
                # Insertar nuevo artículo
                cursor.execute("""
                    INSERT INTO articles (
                        title, content, summary, author, date, category, newspaper, url, 
                        images_found, images_downloaded, images_data, scraped_at, article_id, region, user_category
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    article.get('title', ''),
                    article.get('content', ''),
                    article.get('summary', ''),
                    article.get('author', ''),
                    article.get('published_date', ''),
                    manual_category or category or 'General',
                    newspaper,
                    article_url,
                    images_found,
                    images_downloaded,
                    images_json,
                    datetime.now().isoformat(),
                    article_id,
                    manual_region,
                    manual_category
                ))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        logging.error(f"❌ Error guardando en base de datos: {e}")
        return False

def load_excluded_newspapers():
    """Obtener lista de periódicos excluidos de auto-actualización"""
    try:
        import sqlite3
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS excluded_newspapers (
                newspaper TEXT PRIMARY KEY,
                excluded_at TEXT NOT NULL
            )
        """)
        cursor.execute("SELECT newspaper FROM excluded_newspapers")
        excluded = {row[0] for row in cursor.fetchall() if row[0]}
        conn.close()
        return excluded
    except Exception as e:
        logging.error(f"❌ Error cargando periódicos excluidos: {e}")
        return set()

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
        
        if method == "auto" or method == "improved":
            # Usar ImprovedScraper (método más confiable)
            from improved_scraper import ImprovedScraper
            scraper = ImprovedScraper()
            try:
                articles = scraper.scrape_articles(url, max_articles=max_articles)
                logging.info(f"✅ ImprovedScraper: {len(articles)} artículos encontrados")
                
                # Verificar imágenes extraídas
                articles_with_images = sum(1 for a in articles if a.get('images_data') and len(a.get('images_data', [])) > 0)
                total_images = sum(len(a.get('images_data', [])) for a in articles)
                logging.info(f"📷 Imágenes extraídas: {articles_with_images} artículos con imágenes ({total_images} imágenes totales)")
            finally:
                scraper.close()
                
        elif method == "hybrid":
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
        
        # Asegurar que las imágenes se extraigan correctamente
        # ImprovedScraper ya devuelve images_data como lista de diccionarios
        # Solo necesitamos asegurarnos de que haya al menos 1 imagen principal
        for article in articles:
            # Limitar a 1 imagen principal
            if 'images_data' in article and isinstance(article['images_data'], list):
                if len(article['images_data']) > 1:
                    article['images_data'] = article['images_data'][:1]
                # Asegurar que images_found refleje correctamente
                article['images_found'] = len(article['images_data']) if article['images_data'] else 0
            elif 'images_data' not in article:
                # Si no tiene images_data, inicializarlo como lista vacía
                article['images_data'] = []
                article['images_found'] = 0
            
            # Asegurar que images_downloaded no exceda images_found
            article['images_downloaded'] = min(article.get('images_downloaded', 0), article['images_found'])
        
        # Guardar en base de datos
        if articles:
            # Verificar imágenes antes de guardar
            articles_with_images = sum(1 for a in articles if a.get('images_data') and len(a.get('images_data', [])) > 0)
            total_images_found = sum(len(a.get('images_data', [])) for a in articles if a.get('images_data'))
            
            if save_articles_to_db(articles, category, newspaper, region):
                logging.info(f"✅ {len(articles)} artículos guardados en base de datos")
                logging.info(f"📷 {articles_with_images} artículos con imágenes principales ({total_images_found} imágenes totales)")
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
    
    # Periódicos excluidos por el usuario
    excluded_newspapers = load_excluded_newspapers()
    if excluded_newspapers:
        logging.info(f"⏸️ Periódicos excluidos: {', '.join(excluded_newspapers)}")
    
    # Ejecutar cada programación
    schedules = auto_config.get("schedules", [])
    successful = 0
    failed = 0
    
    for schedule in schedules:
        if schedule.get("enabled", False):
            newspaper_name = schedule.get("newspaper", "")
            if newspaper_name and newspaper_name in excluded_newspapers:
                logging.info(f"⏭️ Saltando '{newspaper_name}' (excluido por el usuario)")
                continue
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
