#!/usr/bin/env python3
"""
API REST para el Web Scraper
Expone endpoints para el frontend React
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional
import threading
import time

# Importar nuestros scrapers
from hybrid_crawler import HybridDataCrawler, crawl_complete_hybrid
from optimized_scraper import SmartScraper
from improved_scraper import ImprovedScraper
from intelligent_analyzer import IntelligentPageAnalyzer
from optimized_scraper import ArticleData
from elperuano_scraper import scrape_elperuano_economia
from pagination_crawler import PaginationCrawler
import pandas as pd
from sqlalchemy import create_engine, text
import io
import base64

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def detect_language_and_region(text: str) -> str:
    """Detectar idioma y región del texto para clasificar como nacional o extranjero"""
    if not text or len(text.strip()) < 10:
        return 'extranjero'
    
    text_lower = text.lower()
    
    # Palabras clave en español peruano
    spanish_peru_keywords = [
        'perú', 'peruano', 'peruana', 'lima', 'cuzco', 'arequipa', 'trujillo',
        'callao', 'piura', 'chiclayo', 'iquitos', 'huancayo', 'cusco',
        'congreso', 'presidente', 'ministro', 'gobierno', 'poder judicial',
        'soles', 'nuevo sol', 'pen', 'banco central', 'sunat', 'indecopi',
        'el comercio', 'la república', 'perú21', 'trome', 'ojo', 'correo',
        'rpp', 'américa tv', 'panamericana', 'atv', 'latina', 'willax'
    ]
    
    # Palabras clave en español general
    spanish_keywords = [
        'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te',
        'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'al', 'del',
        'los', 'las', 'una', 'como', 'más', 'pero', 'sus', 'todo', 'esta',
        'entre', 'cuando', 'muy', 'sin', 'sobre', 'también', 'me', 'hasta',
        'desde', 'está', 'mi', 'porque', 'qué', 'sólo', 'han', 'yo', 'hay',
        'vez', 'puede', 'todos', 'así', 'nos', 'ni', 'parte', 'tiene', 'él',
        'uno', 'donde', 'bien', 'tiempo', 'mismo', 'ese', 'ahora', 'cada',
        'e', 'vida', 'otro', 'después', 'te', 'otros', 'aunque', 'esa',
        'esos', 'estas', 'estos', 'otra', 'otras', 'otros', 'otro', 'otra'
    ]
    
    # Contar palabras en español peruano
    peru_count = sum(1 for keyword in spanish_peru_keywords if keyword in text_lower)
    
    # Contar palabras en español general
    spanish_count = sum(1 for keyword in spanish_keywords if keyword in text_lower)
    
    # Palabras clave en inglés
    english_keywords = [
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
        'after', 'above', 'below', 'between', 'among', 'is', 'are', 'was',
        'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
        'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
        'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she',
        'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your',
        'his', 'her', 'its', 'our', 'their', 'a', 'an', 'some', 'any', 'all'
    ]
    
    # Contar palabras en inglés
    english_count = sum(1 for keyword in english_keywords if keyword in text_lower)
    
    # Determinar idioma y región
    total_words = len(text.split())
    if total_words < 5:
        return 'extranjero'
    
    # Si tiene muchas palabras peruanas, es nacional
    if peru_count >= 2:
        return 'nacional'
    
    # Si tiene más palabras en español que en inglés, probablemente es español
    if spanish_count > english_count and spanish_count > 5:
        return 'nacional'
    
    # Si tiene más palabras en inglés, probablemente es extranjero
    if english_count > spanish_count and english_count > 5:
        return 'extranjero'
    
    # Por defecto, si no se puede determinar claramente, considerar extranjero
    return 'extranjero'

def check_duplicate_url(url: str) -> bool:
    """Verificar si una URL ya ha sido scrapeada"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM articles WHERE url = ?", (url,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except Exception as e:
        logger.error(f"❌ Error verificando duplicados: {e}")
        conn.close()
        return False

app = Flask(__name__)
CORS(app)  # Permitir CORS para React

# Configuración de la base de datos SQLite
DB_PATH = "news_database.db"

# Estado global del scraping
scraping_status = {
    'is_running': False,
    'progress': 0,
    'total': 0,
    'current_url': '',
    'articles_found': 0,
    'images_found': 0,
    'error': None,
    'start_time': None,
    'end_time': None
}

def get_db_connection():
    """Obtener conexión a la base de datos SQLite"""
    try:
        import sqlite3
        return sqlite3.connect(DB_PATH)
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        return None

def init_database():
    """Inicializar tablas de la base de datos SQLite"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Tabla de artículos
        create_articles_table = """
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                summary TEXT,
                author TEXT,
                date TEXT,
                category TEXT,
                newspaper TEXT,
                url TEXT NOT NULL,
                images_found INTEGER DEFAULT 0,
                images_downloaded INTEGER DEFAULT 0,
                images_data TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                article_id TEXT UNIQUE,
                region TEXT DEFAULT 'extranjero'
            )
        """
        
        # Tabla de imágenes
        create_images_table = """
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id TEXT,
                url TEXT NOT NULL,
                local_path TEXT,
                alt_text TEXT,
                title TEXT,
                width INTEGER,
                height INTEGER,
                format TEXT,
                size_bytes INTEGER,
                relevance_score INTEGER DEFAULT 0,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        
        # Tabla de estadísticas
        create_stats_table = """
            CREATE TABLE IF NOT EXISTS scraping_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                url_scraped TEXT,
                articles_found INTEGER,
                images_found INTEGER,
                images_downloaded INTEGER,
                duration_seconds INTEGER,
                method_used TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        
        cursor.execute(create_articles_table)
        cursor.execute(create_images_table)
        cursor.execute(create_stats_table)
        
        # Agregar columna 'region' si no existe
        try:
            cursor.execute("ALTER TABLE articles ADD COLUMN region TEXT DEFAULT 'extranjero'")
        except Exception:
            # La columna ya existe, no hacer nada
            pass
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Base de datos SQLite inicializada correctamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error inicializando base de datos: {e}")
        return False

@app.route('/api/health', methods=['GET'])
def health_check():
    """Verificar estado de la API"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected' if get_db_connection() else 'disconnected'
    })

@app.route('/api/config', methods=['GET'])
def get_config():
    """Obtener configuración actual"""
    return jsonify({
        'database': DB_CONFIG,
        'scraping_status': scraping_status,
        'supported_methods': ['auto', 'hybrid', 'optimized', 'improved', 'selenium', 'requests']
    })

@app.route('/api/analyze', methods=['POST'])
def analyze_page():
    """Analizar página y sugerir el mejor método de scraping"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL es requerida'}), 400
        
        # Analizar la página
        analyzer = IntelligentPageAnalyzer()
        analysis = analyzer.analyze_page(url)
        analyzer.close()
        
        return jsonify(analysis)
        
    except Exception as e:
        logger.error(f"❌ Error analizando página: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear-all', methods=['DELETE'])
def clear_all_data():
    """Borrar todos los artículos, imágenes y estadísticas de la base de datos"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Base de datos no disponible'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Contar registros antes de borrar
        cursor.execute("SELECT COUNT(*) FROM articles")
        articles_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM images")
        images_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM scraping_stats")
        stats_count = cursor.fetchone()[0]
        
        # Borrar todos los datos
        cursor.execute("DELETE FROM articles")
        cursor.execute("DELETE FROM images")
        cursor.execute("DELETE FROM scraping_stats")
        
        # Resetear contadores de auto-incremento
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('articles', 'images', 'scraping_stats')")
        
        conn.commit()
        conn.close()
        
        logger.info(f"🗑️ Datos borrados: {articles_count} artículos, {images_count} imágenes, {stats_count} estadísticas")
        
        return jsonify({
            'message': 'Todos los datos han sido borrados exitosamente',
            'deleted': {
                'articles': articles_count,
                'images': images_count,
                'stats': stats_count
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error borrando datos: {str(e)}")
        return jsonify({'error': f'Error borrando datos: {str(e)}'}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Obtener estado actual del scraping"""
    return jsonify(scraping_status)

@app.route('/api/start-scraping', methods=['POST'])
def start_scraping():
    """Iniciar proceso de scraping"""
    global scraping_status
    
    if scraping_status['is_running']:
        return jsonify({'error': 'El scraping ya está en ejecución'}), 400
    
    data = request.get_json()
    url = data.get('url')
    max_articles = data.get('max_articles', 50)
    max_images = data.get('max_images', 50)
    method = data.get('method', 'auto')  # 'auto' para análisis inteligente
    download_images = data.get('download_images', True)
    category = data.get('category', '')
    newspaper = data.get('newspaper', '')
    region = data.get('region', '')
    
    # Si el método es 'auto', analizar la página primero
    if method == 'auto':
        logger.info("🧠 Análisis inteligente activado")
        analyzer = IntelligentPageAnalyzer()
        analysis = analyzer.analyze_page(url)
        analyzer.close()
        
        method = analysis['recommendation']
        confidence = analysis['confidence']
        
        logger.info(f"🎯 Método sugerido: {method} (confianza: {confidence}%)")
        logger.info(f"📋 Razones: {', '.join(analysis['reasoning'])}")
        
        # Actualizar el estado con la información del análisis
        scraping_status.update({
            'analysis': analysis,
            'suggested_method': method,
            'confidence': confidence
        })
    
    if not url:
        return jsonify({'error': 'URL es requerida'}), 400
    
    # Verificar si la URL ya ha sido scrapeada
    if check_duplicate_url(url):
        return jsonify({
            'error': 'Esta URL ya ha sido scrapeada anteriormente',
            'message': 'Los artículos de esta URL ya existen en la base de datos. Si deseas extraer contenido nuevo, intenta con una URL diferente o elimina los artículos existentes.',
            'duplicate': True
        }), 409
    
    # Inicializar estado
    scraping_status.update({
        'is_running': True,
        'progress': 0,
        'total': max_articles,
        'current_url': url,
        'articles_found': 0,
        'images_found': 0,
        'error': None,
        'start_time': datetime.now().isoformat(),
        'end_time': None
    })
    
    # Ejecutar scraping en hilo separado
    thread = threading.Thread(
        target=run_scraping,
        args=(url, max_articles, max_images, method, download_images, category, newspaper, region)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'message': 'Scraping iniciado',
        'status': scraping_status
    })

def scrape_with_pagination(url: str, max_articles: int, max_images: int, method: str, download_images: bool, category: str = '', newspaper: str = '', region: str = ''):
    """Scraping con paginación automática para cualquier sitio web"""
    try:
        logger.info(f"🔄 Iniciando scraping con paginación para: {url}")
        
        # Crear función de extracción según el método
        if method == 'hybrid':
            extract_func = lambda page_url: extract_articles_hybrid(page_url, max_articles)
        elif method == 'optimized':
            extract_func = lambda page_url: extract_articles_optimized(page_url, max_articles)
        elif method == 'improved':
            extract_func = lambda page_url: extract_articles_improved(page_url, max_articles)
        elif method == 'selenium':
            extract_func = lambda page_url: extract_articles_selenium(page_url, max_articles)
        else:
            # Método automático - usar improved por defecto
            extract_func = lambda page_url: extract_articles_improved(page_url, max_articles)
        
        # Usar PaginationCrawler
        pagination_crawler = PaginationCrawler(use_selenium=True)
        try:
            articles = pagination_crawler.crawl_all_pages(
                url=url,
                max_articles=max_articles,
                extract_articles_func=extract_func
            )
            
            # Guardar en base de datos
            save_articles_to_db(articles, category, newspaper, region)
            
            logger.info(f"🎉 Scraping con paginación completado: {len(articles)} artículos")
            return articles
            
        finally:
            pagination_crawler.close()
            
    except Exception as e:
        logger.error(f"❌ Error en scraping con paginación: {e}")
        return []

def extract_articles_hybrid(url, max_articles):
    """Extraer artículos usando método híbrido"""
    try:
        crawler = HybridDataCrawler()
        try:
            articles = crawler.hybrid_crawl_articles(url, max_articles)
            return articles
        finally:
            crawler.close()
    except Exception as e:
        logger.error(f"❌ Error en extracción híbrida: {e}")
        return []

def extract_articles_optimized(url, max_articles):
    """Extraer artículos usando método optimizado"""
    try:
        scraper = SmartScraper(max_workers=10)
        try:
            articles = scraper.scrape_articles(url, max_articles)
            return articles
        finally:
            scraper.close()
    except Exception as e:
        logger.error(f"❌ Error en extracción optimizada: {e}")
        return []

def extract_articles_improved(url, max_articles):
    """Extraer artículos usando método mejorado"""
    try:
        scraper = ImprovedScraper()
        try:
            articles = scraper.scrape_articles(url, max_articles)
            return articles
        finally:
            scraper.close()
    except Exception as e:
        logger.error(f"❌ Error en extracción mejorada: {e}")
        return []

def extract_articles_selenium(url, max_articles):
    """Extraer artículos usando Selenium"""
    try:
        # Implementación básica con Selenium
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        service = Service('/usr/local/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        try:
            driver.get(url)
            time.sleep(3)
            
            # Buscar artículos
            articles = []
            article_elements = driver.find_elements(By.CSS_SELECTOR, 'article, .article, .news-item, h2 a, h3 a')
            
            for element in article_elements[:max_articles]:
                try:
                    if element.tag_name == 'a':
                        title = element.text.strip()
                        link = element.get_attribute('href')
                    else:
                        link_elem = element.find_element(By.TAG_NAME, 'a')
                        title = link_elem.text.strip()
                        link = link_elem.get_attribute('href')
                    
                    if title and link:
                        articles.append({
                            'title': title,
                            'url': link,
                            'content': '',
                            'summary': title,
                            'author': '',
                            'date': '',
                            'newspaper': newspaper or 'Desconocido',
                            'category': category or 'General',
                            'images_found': 0,
                            'images_downloaded': 0,
                            'images_data': [],
                            'scraped_at': datetime.now().isoformat(),
                            'article_id': f"selenium_{hash(link)}"
                        })
                except:
                    continue
            
            return articles
            
        finally:
            driver.quit()
            
    except Exception as e:
        logger.error(f"❌ Error en extracción Selenium: {e}")
        return []

def run_scraping(url: str, max_articles: int, max_images: int, method: str, download_images: bool, category: str = '', newspaper: str = '', region: str = ''):
    """Ejecutar scraping en hilo separado con paginación automática"""
    global scraping_status
    
    try:
        logger.info(f"🚀 Iniciando scraping con paginación: {url}")
        
        # Scraper específico para El Peruano
        if 'elperuano.pe' in url and 'economia' in url:
            logger.info("🇵🇪 Usando scraper específico para El Peruano con paginación")
            articles = scrape_elperuano_economia(max_articles, use_pagination=True)
            
            # Guardar en base de datos
            save_articles_to_db(articles, category, newspaper, region)
            
            scraping_status.update({
                'articles_found': len(articles),
                'images_found': sum(len(article.get('images_data', [])) for article in articles),
                'progress': max_articles
            })
            
        # Scraping con paginación automática para cualquier sitio
        else:
            logger.info("🔄 Usando sistema de paginación automática")
            articles = scrape_with_pagination(url, max_articles, max_images, method, download_images, category, newspaper, region)
            
            scraping_status.update({
                'articles_found': len(articles),
                'images_found': sum(len(article.get('images_data', [])) for article in articles),
                'progress': max_articles
            })
            
        # Métodos originales (mantener para compatibilidad)
        if method == 'optimized':
            # Usar SmartScraper
            scraper = SmartScraper(max_workers=10)
            try:
                articles = scraper.crawl_and_scrape_parallel(
                    url, 
                    max_articles=max_articles,
                    extract_images=download_images
                )
                
                # Guardar en base de datos
                save_articles_to_db(articles, category, newspaper, region)
                
                # Contar imágenes reales descargadas
                total_images = 0
                for article in articles:
                    if hasattr(article, 'images_data') and article.images_data:
                        try:
                            import json
                            images_data = json.loads(article.images_data) if isinstance(article.images_data, str) else article.images_data
                            if isinstance(images_data, list):
                                total_images += len(images_data)
                        except:
                            pass
                
                scraping_status.update({
                    'articles_found': len(articles),
                    'images_found': total_images,
                    'progress': max_articles
                })
                
            finally:
                scraper.close()
                
        elif method == 'improved':
            # Usar ImprovedScraper (método mejorado sin Selenium)
            scraper = ImprovedScraper()
            try:
                articles = scraper.scrape_articles(url, max_articles=max_articles)
                
                # Guardar en base de datos
                save_articles_to_db(articles, category, newspaper, region)
                
                scraping_status.update({
                    'articles_found': len(articles),
                    'images_found': sum(article.get('images_found', 0) for article in articles),
                    'progress': max_articles
                })
                
            finally:
                scraper.close()
        
        # Guardar estadísticas
        save_scraping_stats(url, scraping_status['articles_found'], 
                          scraping_status['images_found'], method)
        
        logger.info(f"✅ Scraping completado: {scraping_status['articles_found']} artículos, {scraping_status['images_found']} imágenes")
        
    except Exception as e:
        logger.error(f"❌ Error en scraping: {e}")
        scraping_status['error'] = str(e)
    
    finally:
        scraping_status.update({
            'is_running': False,
            'end_time': datetime.now().isoformat()
        })

def save_articles_to_db(articles: List[Dict], category: str = '', newspaper: str = '', region: str = ''):
    """Guardar artículos en la base de datos SQLite"""
    if not articles:
        return
    
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        for article in articles:
            if isinstance(article, ArticleData):
                # Si es objeto ArticleData, usar la categoría proporcionada si no tiene una
                article_category = article.category if article.category else category
                # Usar el newspaper manual si está disponible, sino usar el del artículo
                article_newspaper = newspaper if newspaper else article.newspaper
                
                # Usar la región manual si está disponible, sino detectar automáticamente
                if region:
                    article_region = region
                else:
                    article_text = f"{article.title} {article.content} {article.summary}"
                    article_region = detect_language_and_region(article_text)
                
                cursor.execute("""
                    INSERT OR REPLACE INTO articles 
                    (title, content, summary, author, date, category, newspaper, url, 
                     images_found, images_downloaded, images_data, scraped_at, article_id, region)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    article.title, article.content, article.summary, article.author,
                    article.date, article_category, article_newspaper, article.url,
                    article.images_found, article.images_downloaded, article.images_data,
                    article.scraped_at, article.article_id, article_region
                ))
            else:
                # Si es diccionario, usar la categoría proporcionada si no tiene una
                article_category = article.get('category', '') if article.get('category', '') else category
                # Usar el newspaper manual si está disponible, sino usar el del artículo
                article_newspaper = newspaper if newspaper else article.get('newspaper', '')
                
                # Usar la región manual si está disponible, sino detectar automáticamente
                if region:
                    article_region = region
                else:
                    article_text = f"{article.get('title', '')} {article.get('content', '')} {article.get('summary', '')}"
                    article_region = detect_language_and_region(article_text)
                
                # Convertir images_data a JSON string si es una lista
                images_data = article.get('images_data', '[]')
                if isinstance(images_data, list):
                    images_data = json.dumps(images_data)
                elif not isinstance(images_data, str):
                    images_data = '[]'
                
                cursor.execute("""
                    INSERT OR REPLACE INTO articles 
                    (title, content, summary, author, date, category, newspaper, url, 
                     images_found, images_downloaded, images_data, scraped_at, article_id, region)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    article.get('title', ''), article.get('content', ''), article.get('summary', ''),
                    article.get('author', ''), article.get('date', ''), article_category,
                    article_newspaper, article.get('url', ''), article.get('images_found', 0),
                    article.get('images_downloaded', 0), images_data,
                    article.get('scraped_at', ''), article.get('article_id', ''), article_region
                ))
        
        conn.commit()
        conn.close()
        logger.info(f"✅ {len(articles)} artículos guardados en la base de datos")
        
    except Exception as e:
        logger.error(f"❌ Error guardando artículos: {e}")

def save_images_to_db(images: List[Dict]):
    """Guardar imágenes en la base de datos"""
    if not images:
        return
    
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        for image in images:
            cursor.execute("""
                INSERT INTO images (article_id, url, local_path, alt_text, title, width, height, format, size_bytes, relevance_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                image.get('article_id'),
                image.get('url'),
                image.get('local_path'),
                image.get('alt_text'),
                image.get('title'),
                image.get('width'),
                image.get('height'),
                image.get('format'),
                image.get('size_bytes'),
                image.get('relevance_score', 0)
            ))
        conn.commit()
        logger.info(f"✅ {len(images)} imágenes guardadas en la base de datos")
        
    except Exception as e:
        logger.error(f"❌ Error guardando imágenes: {e}")
    finally:
        conn.close()

def save_scraping_stats(url: str, articles_found: int, images_found: int, method: str):
    """Guardar estadísticas del scraping"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        start_time = datetime.fromisoformat(scraping_status['start_time'])
        end_time = datetime.now()
        duration = int((end_time - start_time).total_seconds())
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO scraping_stats (session_id, url_scraped, articles_found, images_found, images_downloaded, duration_seconds, method_used)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            f"session_{int(time.time())}",
            url,
            articles_found,
            images_found,
            images_found,  # Asumimos que todas se descargaron
            duration,
            method
        ))
        conn.commit()
        logger.info("✅ Estadísticas guardadas")
        
    except Exception as e:
        logger.error(f"❌ Error guardando estadísticas: {e}")
    finally:
        conn.close()

@app.route('/api/articles', methods=['GET'])
def get_articles():
    """Obtener artículos de la base de datos SQLite"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Base de datos no disponible'}), 500
    
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        newspaper = request.args.get('newspaper')
        category = request.args.get('category')
        region = request.args.get('region')
        search = request.args.get('search')
        
        offset = (page - 1) * limit
        
        # Construir query
        query = "SELECT * FROM articles WHERE 1=1"
        params = []
        
        if newspaper:
            query += " AND newspaper = ?"
            params.append(newspaper)
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if region:
            query += " AND region = ?"
            params.append(region)
        
        if search:
            query += " AND (title LIKE ? OR content LIKE ? OR summary LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])
        
        query += " ORDER BY scraped_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Obtener nombres de columnas
        column_names = [description[0] for description in cursor.description]
        
        articles = []
        for row in rows:
            article_dict = dict(zip(column_names, row))
            # Parsear imágenes si existen
            if article_dict.get('images_data'):
                try:
                    article_dict['images_data'] = json.loads(article_dict['images_data'])
                except:
                    article_dict['images_data'] = []
            articles.append(article_dict)
        
        # Obtener total
        count_query = "SELECT COUNT(*) as total FROM articles WHERE 1=1"
        count_params = []
        if newspaper:
            count_query += " AND newspaper = ?"
            count_params.append(newspaper)
        if category:
            count_query += " AND category = ?"
            count_params.append(category)
        if region:
            count_query += " AND region = ?"
            count_params.append(region)
        if search:
            count_query += " AND (title LIKE ? OR content LIKE ? OR summary LIKE ?)"
            search_term = f"%{search}%"
            count_params.extend([search_term, search_term, search_term])
        
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'articles': articles,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo artículos: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/articles/filters', methods=['GET'])
def get_article_filters():
    """Obtener filtros únicos para artículos (periódicos, categorías, regiones)"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Base de datos no disponible'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Obtener periódicos únicos
        cursor.execute("SELECT DISTINCT newspaper FROM articles WHERE newspaper IS NOT NULL AND newspaper != '' ORDER BY newspaper")
        newspapers = [row[0] for row in cursor.fetchall()]
        
        # Obtener categorías únicas
        cursor.execute("SELECT DISTINCT category FROM articles WHERE category IS NOT NULL AND category != '' ORDER BY category")
        categories = [row[0] for row in cursor.fetchall()]
        
        # Obtener regiones únicas
        cursor.execute("SELECT DISTINCT region FROM articles WHERE region IS NOT NULL AND region != '' ORDER BY region")
        regions = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'newspapers': newspapers,
            'categories': categories,
            'regions': regions
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo filtros: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/articles/export/excel', methods=['GET'])
def export_articles_to_excel():
    """Exportar todos los artículos a Excel"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Base de datos no disponible'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Obtener todos los artículos
        cursor.execute("""
            SELECT id, title, summary, content, newspaper, category, region, 
                   url, scraped_at, images_data
            FROM articles 
            ORDER BY scraped_at DESC
        """)
        
        articles = cursor.fetchall()
        conn.close()
        
        if not articles:
            return jsonify({'error': 'No hay artículos para exportar'}), 404
        
        # Preparar datos para Excel
        excel_data = []
        for article in articles:
            # Parsear imágenes si existen
            images_count = 0
            if article[9]:  # images_data
                try:
                    images_list = json.loads(article[9])
                    images_count = len(images_list) if isinstance(images_list, list) else 0
                except:
                    images_count = 0
            
            excel_data.append({
                'ID': article[0],
                'Título': article[1] or '',
                'Resumen': article[2] or '',
                'Contenido': (article[3] or '')[:500] + '...' if article[3] and len(article[3]) > 500 else (article[3] or ''),  # Limitar contenido
                'Periódico': article[4] or '',
                'Categoría': article[5] or '',
                'Región': article[6] or '',
                'URL': article[7] or '',
                'Fecha Extracción': article[8] or '',
                'Cantidad Imágenes': images_count
            })
        
        # Crear DataFrame
        df = pd.DataFrame(excel_data)
        
        # Crear archivo Excel en memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Artículos', index=False)
            
            # Ajustar ancho de columnas
            worksheet = writer.sheets['Artículos']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)  # Máximo 50 caracteres
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        
        # Generar nombre de archivo con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"articulos_exportados_{timestamp}.xlsx"
        
        # Convertir a base64 para enviar al frontend
        excel_base64 = base64.b64encode(output.getvalue()).decode('utf-8')
        
        logger.info(f"✅ Excel exportado exitosamente: {len(articles)} artículos")
        
        return jsonify({
            'success': True,
            'filename': filename,
            'data': excel_base64,
            'articles_count': len(articles)
        })
        
    except Exception as e:
        logger.error(f"❌ Error exportando a Excel: {e}")
        return jsonify({'error': f'Error exportando a Excel: {str(e)}'}), 500

@app.route('/api/articles/<article_id>', methods=['GET'])
def get_article(article_id):
    """Obtener un artículo específico"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Base de datos no disponible'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM articles WHERE article_id = ?", [article_id])
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return jsonify({'error': 'Artículo no encontrado'}), 404
        
        # Obtener nombres de columnas
        column_names = [description[0] for description in cursor.description]
        article_dict = dict(zip(column_names, row))
        
        if article_dict.get('images_data'):
            try:
                article_dict['images_data'] = json.loads(article_dict['images_data'])
            except:
                article_dict['images_data'] = []
        
        conn.close()
        return jsonify(article_dict)
            
    except Exception as e:
        logger.error(f"❌ Error obteniendo artículo: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/images', methods=['GET'])
def get_images():
    """Obtener imágenes de la base de datos"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Base de datos no disponible'}), 500
    
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        article_id = request.args.get('article_id')
        
        offset = (page - 1) * limit
        
        query = "SELECT * FROM images WHERE 1=1"
        params = []
        
        if article_id:
            query += " AND article_id = ?"
            params.append(article_id)
        
        query += " ORDER BY downloaded_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = conn.cursor()
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        images = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return jsonify({
            'images': images,
            'pagination': {
                'page': page,
                'limit': limit
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo imágenes: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Obtener estadísticas del scraping"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Base de datos no disponible'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Estadísticas generales
        cursor.execute("""
            SELECT 
                COUNT(*) as total_articles,
                COUNT(DISTINCT newspaper) as total_newspapers,
                COUNT(DISTINCT category) as total_categories,
                SUM(images_found) as total_images_found,
                SUM(images_downloaded) as total_images_downloaded
            FROM articles
        """)
        row = cursor.fetchone()
        column_names = [description[0] for description in cursor.description]
        general_stats = dict(zip(column_names, row))
        
        # Estadísticas por periódico
        cursor.execute("""
            SELECT 
                newspaper,
                COUNT(*) as articles_count,
                SUM(images_found) as images_count
            FROM articles 
            GROUP BY newspaper 
            ORDER BY articles_count DESC
            LIMIT 10
        """)
        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        newspaper_stats = [dict(zip(column_names, row)) for row in rows]
        
        # Estadísticas por categoría
        cursor.execute("""
            SELECT 
                category,
                COUNT(*) as articles_count
            FROM articles 
            WHERE category IS NOT NULL AND category != ''
            GROUP BY category 
            ORDER BY articles_count DESC
            LIMIT 10
        """)
        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        category_stats = [dict(zip(column_names, row)) for row in rows]
        
        # Últimas sesiones de scraping
        cursor.execute("""
            SELECT 
                session_id,
                url_scraped,
                articles_found,
                images_found,
                duration_seconds,
                method_used,
                created_at
            FROM scraping_stats 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        sessions = [dict(zip(column_names, row)) for row in rows]
        
        conn.close()
        
        return jsonify({
            'general': general_stats,
            'newspapers': newspaper_stats,
            'categories': category_stats,
            'sessions': sessions
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/images/<path:filename>')
def serve_image(filename):
    """Servir imágenes descargadas"""
    try:
        return send_from_directory('scraped_images', filename)
    except Exception as e:
        logger.error(f"❌ Error sirviendo imagen {filename}: {e}")
        return jsonify({'error': 'Imagen no encontrada'}), 404

@app.route('/api/stop-scraping', methods=['POST'])
def stop_scraping():
    """Detener el scraping en curso"""
    global scraping_status
    
    if not scraping_status['is_running']:
        return jsonify({'error': 'No hay scraping en ejecución'}), 400
    
    scraping_status.update({
        'is_running': False,
        'end_time': datetime.now().isoformat(),
        'error': 'Detenido por el usuario'
    })
    
    return jsonify({'message': 'Scraping detenido'})

@app.route('/api/newspapers', methods=['GET'])
def get_newspapers():
    """Obtener lista de periódicos con conteos de artículos e imágenes"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Base de datos no disponible'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Obtener estadísticas por periódico
        cursor.execute("""
            SELECT 
                newspaper,
                COUNT(*) as articles_count,
                SUM(images_found) as total_images_found,
                SUM(images_downloaded) as total_images_downloaded,
                MIN(scraped_at) as first_scraped,
                MAX(scraped_at) as last_scraped
            FROM articles 
            WHERE newspaper IS NOT NULL AND newspaper != ''
            GROUP BY newspaper 
            ORDER BY articles_count DESC
        """)
        
        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        newspapers = [dict(zip(column_names, row)) for row in rows]
        
        conn.close()
        
        return jsonify({
            'newspapers': newspapers,
            'total': len(newspapers)
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo periódicos: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/newspapers/<newspaper_name>', methods=['DELETE'])
def delete_newspaper_data(newspaper_name):
    """Eliminar todos los datos de un periódico específico"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Base de datos no disponible'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Contar registros antes de borrar
        cursor.execute("SELECT COUNT(*) FROM articles WHERE newspaper = ?", (newspaper_name,))
        articles_count = cursor.fetchone()[0]
        
        # Obtener URLs de imágenes asociadas a los artículos del periódico
        cursor.execute("""
            SELECT images_data FROM articles 
            WHERE newspaper = ? AND images_data IS NOT NULL AND images_data != '[]'
        """, (newspaper_name,))
        
        image_urls = []
        for row in cursor.fetchall():
            try:
                images_data = json.loads(row[0])
                if isinstance(images_data, list):
                    for img in images_data:
                        if isinstance(img, dict) and 'filename' in img:
                            image_urls.append(img['filename'])
            except (json.JSONDecodeError, TypeError):
                continue
        
        # Obtener article_ids de los artículos del periódico para eliminar imágenes relacionadas
        cursor.execute("SELECT article_id FROM articles WHERE newspaper = ?", (newspaper_name,))
        article_ids = [row[0] for row in cursor.fetchall()]
        
        # Contar imágenes relacionadas
        images_count = 0
        if article_ids:
            placeholders = ','.join(['?' for _ in article_ids])
            cursor.execute(f"SELECT COUNT(*) FROM images WHERE article_id IN ({placeholders})", article_ids)
            images_count = cursor.fetchone()[0]
        
        # Borrar artículos del periódico
        cursor.execute("DELETE FROM articles WHERE newspaper = ?", (newspaper_name,))
        
        # Borrar imágenes relacionadas
        if article_ids:
            placeholders = ','.join(['?' for _ in article_ids])
            cursor.execute(f"DELETE FROM images WHERE article_id IN ({placeholders})", article_ids)
        
        # Borrar estadísticas de scraping del periódico
        cursor.execute("DELETE FROM scraping_stats WHERE url_scraped LIKE ?", (f'%{newspaper_name}%',))
        
        conn.commit()
        conn.close()
        
        # Eliminar archivos de imagen físicos
        deleted_files = 0
        for filename in image_urls:
            try:
                image_path = os.path.join('scraped_images', filename)
                if os.path.exists(image_path):
                    os.remove(image_path)
                    deleted_files += 1
            except Exception as e:
                logger.warning(f"⚠️ No se pudo eliminar imagen {filename}: {e}")
        
        logger.info(f"🗑️ Datos del periódico '{newspaper_name}' borrados: {articles_count} artículos, {images_count} imágenes, {deleted_files} archivos")
        
        return jsonify({
            'message': f'Datos del periódico "{newspaper_name}" eliminados exitosamente',
            'deleted': {
                'articles': articles_count,
                'images': images_count,
                'files': deleted_files
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error borrando datos del periódico {newspaper_name}: {e}")
        return jsonify({'error': f'Error borrando datos: {str(e)}'}), 500

if __name__ == '__main__':
    print("🚀 Iniciando API del Web Scraper...")
    
    # Inicializar base de datos
    if init_database():
        print("✅ Base de datos inicializada")
    else:
        print("❌ Error inicializando base de datos")
    
    # Iniciar servidor en puerto 5001 para evitar conflicto con AirPlay
    app.run(host='0.0.0.0', port=5001, debug=True)
