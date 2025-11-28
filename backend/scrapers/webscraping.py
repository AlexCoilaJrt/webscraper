# requirements.txt
"""
streamlit
requests
beautifulsoup4
pandas
plotly
schedule
python-dateutil
mysql-connector-python
psycopg2-binary
openpyxl
xlsxwriter
sqlalchemy
selenium
webdriver-manager
"""

import streamlit as st
import requests
from bs4 import BeautifulSoup
import sqlite3
import schedule
import time
import threading
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
from urllib.parse import urljoin, urlparse
import re

# Importar el crawler híbrido
try:
    from hybrid_crawler import HybridDataCrawler, crawl_complete_hybrid
    HYBRID_CRAWLER_AVAILABLE = True
except ImportError:
    HYBRID_CRAWLER_AVAILABLE = False
    st.warning("⚠️ Crawler híbrido no disponible. Instalando dependencias...")
import json
from typing import Dict, List, Optional
import logging
import io
import base64
import os
from pathlib import Path
from PIL import Image
import hashlib

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Importar el scraper optimizado
try:
    from optimized_scraper import SmartScraper, articles_to_dataframe
    OPTIMIZED_SCRAPER_AVAILABLE = True
except ImportError:
    OPTIMIZED_SCRAPER_AVAILABLE = False

# Imports para bases de datos
try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

try:
    import psycopg2
    from psycopg2 import Error as PostgreSQLError
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False

from sqlalchemy import create_engine
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageManager:
    """Gestor especializado para extracción y descarga de imágenes"""
    
    def __init__(self, base_dir: str = "scraped_images"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        
    def extract_images_from_soup(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extraer URLs de imágenes de un BeautifulSoup"""
        images = []
        
        # Buscar todas las etiquetas img
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            try:
                # Obtener src
                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                if not src:
                    continue
                
                # Convertir a URL absoluta
                full_url = urljoin(base_url, src)
                
                # Verificar si es una imagen válida
                if self._is_valid_image_url(full_url):
                    image_info = {
                        'url': full_url,
                        'alt_text': img.get('alt', ''),
                        'title': img.get('title', ''),
                        'width': img.get('width', ''),
                        'height': img.get('height', ''),
                        'class': ' '.join(img.get('class', [])),
                        'src_original': src
                    }
                    images.append(image_info)
                    
            except Exception as e:
                logger.warning(f"Error procesando imagen: {e}")
                continue
        
        logger.info(f"🖼️ Encontradas {len(images)} imágenes en la página")
        return images
    
    def _is_valid_image_url(self, url: str) -> bool:
        """Verificar si la URL es una imagen válida"""
        try:
            parsed = urlparse(url)
            path = parsed.path.lower()
            
            # Verificar extensión
            has_image_extension = any(path.endswith(ext) for ext in self.supported_formats)
            
            # Verificar si contiene patrones de imagen
            has_image_patterns = any(pattern in url.lower() for pattern in [
                '/image/', '/img/', '/photo/', '/picture/', '/media/',
                'image=', 'img=', 'photo=', 'picture='
            ])
            
            return has_image_extension or has_image_patterns
            
        except:
            return False
    
    def download_image(self, image_info: Dict, article_id: str = None) -> Optional[str]:
        """Descargar imagen y guardarla localmente"""
        try:
            url = image_info['url']
            
            # Crear directorio para el artículo
            if article_id:
                article_dir = self.base_dir / article_id
                article_dir.mkdir(exist_ok=True)
            else:
                article_dir = self.base_dir
            
            # Generar nombre único para la imagen
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            parsed_url = urlparse(url)
            original_name = os.path.basename(parsed_url.path)
            
            if not original_name or '.' not in original_name:
                original_name = f"image_{url_hash}.jpg"
            
            # Determinar extensión
            ext = os.path.splitext(original_name)[1].lower()
            if not ext or ext not in self.supported_formats:
                ext = '.jpg'
            
            filename = f"{url_hash}_{original_name}"
            if not filename.endswith(ext):
                filename += ext
            
            file_path = article_dir / filename
            
            # Descargar imagen
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()
            
            # Verificar que sea realmente una imagen
            content_type = response.headers.get('content-type', '').lower()
            if not content_type.startswith('image/'):
                logger.warning(f"URL no es una imagen: {url}")
                return None
            
            # Guardar imagen
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Verificar que la imagen se guardó correctamente
            if file_path.exists() and file_path.stat().st_size > 0:
                logger.info(f"✅ Imagen descargada: {filename}")
                return str(file_path)
            else:
                logger.error(f"❌ Error guardando imagen: {filename}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error descargando imagen {url}: {e}")
            return None
    
    def get_image_info(self, image_path: str) -> Dict:
        """Obtener información de una imagen descargada"""
        try:
            with Image.open(image_path) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'size_bytes': os.path.getsize(image_path)
                }
        except Exception as e:
            logger.error(f"Error obteniendo info de imagen {image_path}: {e}")
            return {}
    
    def cleanup_old_images(self, days_old: int = 30):
        """Limpiar imágenes antiguas"""
        try:
            cutoff_time = time.time() - (days_old * 24 * 60 * 60)
            removed_count = 0
            
            for file_path in self.base_dir.rglob('*'):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    removed_count += 1
            
            logger.info(f"🧹 Limpiadas {removed_count} imágenes antiguas")
            
        except Exception as e:
            logger.error(f"Error limpiando imágenes: {e}")

class SeleniumManager:
    """Gestor de Selenium para web scraping avanzado"""
    
    def __init__(self, headless=True, wait_time=10):
        self.headless = headless
        self.wait_time = wait_time
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Configurar y inicializar el driver de Chrome"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Instalar ChromeDriver automáticamente
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Ejecutar script para ocultar webdriver
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("✅ Selenium WebDriver inicializado correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando Selenium: {e}")
            self.driver = None
    
    def get_page(self, url: str) -> BeautifulSoup:
        """Obtener página web usando Selenium - MEJORADO PARA CONTENIDO DINÁMICO"""
        if not self.driver:
            logger.error("Driver no disponible")
            return None
        
        try:
            self.driver.get(url)
            
            # Esperar a que la página cargue completamente
            WebDriverWait(self.driver, min(self.wait_time, 10)).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Scroll progresivo para cargar contenido lazy
            self._progressive_scroll()
            
            # Obtener HTML y crear BeautifulSoup
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            logger.info(f"✅ Página cargada exitosamente: {url}")
            return soup
            
        except TimeoutException:
            logger.error(f"⏱️ Timeout cargando página: {url}")
            return None
        except Exception as e:
            logger.error(f"❌ Error cargando página {url}: {e}")
            return None
    
    def _progressive_scroll(self):
        """Scroll progresivo para cargar contenido lazy-loaded"""
        try:
            # Obtener altura inicial
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Scroll progresivo
            scroll_positions = [0.25, 0.5, 0.75, 1.0]  # 25%, 50%, 75%, 100%
            
            for position in scroll_positions:
                # Scroll a la posición
                self.driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {position});")
                time.sleep(1.5)  # Esperar a que cargue contenido
                
                # Verificar si hay más contenido
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height > last_height:
                    last_height = new_height
                    logger.info(f"🔄 Contenido adicional detectado en scroll {position*100}%")
            
            # Scroll final al inicio
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.5)
            
        except Exception as e:
            logger.warning(f"⚠️ Error en scroll progresivo: {e}")
            # Fallback: scroll simple
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
    
    def find_article_links(self, soup: BeautifulSoup, base_url: str, max_links: int = 100) -> List[str]:
        """Encontrar enlaces de artículos en la página - MEJORADO"""
        if not soup:
            return []
        
        links = []
        seen_urls = set()
        
        # Selectores expandidos para detectar más enlaces
        link_selectors = [
            # Patrones específicos de noticias
            'a[href*="/noticia/"]',
            'a[href*="/articulo/"]', 
            'a[href*="/nota/"]',
            'a[href*="/post/"]',
            'a[href*="/news/"]',
            'a[href*="/story/"]',
            'a[href*="/article/"]',
            
            # Patrones de fecha
            'a[href*="/2024/"]',
            'a[href*="/2025/"]',
            'a[href*="/2023/"]',
            
            # Patrones de ID numérico
            'a[href*="/noticia-"]',
            'a[href*="/articulo-"]',
            'a[href*="/post-"]',
            
            # Selectores estructurales
            'article a',
            '.article a',
            '.news a',
            '.post a',
            '.story a',
            '.entry a',
            '.item a',
            '.card a',
            '.content a',
            
            # Títulos con enlaces
            'h1 a', 'h2 a', 'h3 a', 'h4 a',
            
            # Selectores específicos de sitios populares
            '.title a',
            '.headline a',
            '.summary a',
            '.excerpt a',
            '.teaser a',
            '.preview a',
            
            # Listas de artículos
            '.article-list a',
            '.news-list a',
            '.post-list a',
            '.story-list a',
            
            # Grids y layouts modernos
            '.grid a',
            '.masonry a',
            '.feed a',
            '.timeline a',
            
            # Enlaces con clases específicas
            'a[class*="article"]',
            'a[class*="news"]',
            'a[class*="post"]',
            'a[class*="story"]',
            'a[class*="title"]',
            'a[class*="headline"]'
        ]
        
        # Buscar con todos los selectores
        for selector in link_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    href = element.get('href')
                    if href:
                        full_url = urljoin(base_url, href)
                        
                        if (self._is_article_url_improved(full_url, base_url) and 
                            full_url not in seen_urls and 
                            len(links) < max_links):
                            links.append(full_url)
                            seen_urls.add(full_url)
            except Exception as e:
                logger.debug(f"Error con selector {selector}: {e}")
                continue
        
        # Búsqueda adicional: todos los enlaces con texto relevante
        try:
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                if len(links) >= max_links:
                    break
                    
                href = link.get('href')
                text = link.get_text().strip()
                
                # Solo procesar enlaces con texto sustancial
                if href and len(text) > 10:
                    full_url = urljoin(base_url, href)
                    
                    if (self._is_article_url_improved(full_url, base_url) and 
                        full_url not in seen_urls):
                        links.append(full_url)
                        seen_urls.add(full_url)
        except Exception as e:
            logger.debug(f"Error en búsqueda adicional: {e}")
        
        logger.info(f"🔍 Encontrados {len(links)} enlaces de artículos")
        return links
    
    def _is_article_url_improved(self, url: str, base_url: str) -> bool:
        """Verificar si la URL es probablemente un artículo - MEJORADO"""
        parsed_base = urlparse(base_url)
        parsed_url = urlparse(url)
        
        # Debe ser del mismo dominio
        if parsed_url.netloc != parsed_base.netloc:
            return False
        
        # URLs muy cortas probablemente no son artículos
        if len(url) < 20:
            return False
        
        # Patrones que indican artículo (expandidos)
        article_patterns = [
            # Patrones de fecha
            r'/\d{4}/\d{2}/\d{2}/',  # 2024/01/15
            r'/\d{4}/\d{2}/',        # 2024/01
            r'/\d{4}/',              # 2024
            
            # Patrones de contenido específicos
            r'/noticia/',
            r'/articulo/',
            r'/nota/',
            r'/post/',
            r'/news/',
            r'/story/',
            r'/article/',
            r'/entry/',
            r'/blog/',
            r'/report/',
            r'/press/',
            r'/announcement/',
            r'/publication/',
            
            # Patrones de ID
            r'/noticia-\d+',
            r'/articulo-\d+',
            r'/post-\d+',
            r'/news-\d+',
            
            # Patrones de slug (palabras con guiones) - más específicos
            r'[a-z]+-[a-z]+-[a-z]+-[a-z]+',  # 4 palabras mínimo
            r'[a-z]+-[a-z]+-[a-z]+-[a-z]+-[a-z]+',  # 5 palabras
            
            # Patrones específicos de sitios
            r'/\d{4}/\d{2}/\d{2}/[a-z-]+',  # fecha + slug
            r'/[a-z-]+/\d{4}/\d{2}/\d{2}',  # slug + fecha
        ]
        
        url_lower = url.lower()
        
        # Verificar patrones positivos
        has_article_pattern = any(re.search(pattern, url_lower) for pattern in article_patterns)
        
        # Excluir patrones negativos (expandidos)
        exclude_patterns = [
            # Navegación y categorías
            r'/categoria/', r'/category/', r'/tag/', r'/tags/', r'/etiqueta/',
            r'/author/', r'/authors/', r'/autor/', r'/autores/',
            r'/search/', r'/buscar/', r'/busqueda/',
            r'/page/', r'/pagina/', r'/p/',
            r'/seccion/', r'/section/', r'/archivo/', r'/archive/',
            
            # Páginas estáticas
            r'/inicio/', r'/home/', r'/contacto/', r'/contact/',
            r'/about/', r'/acerca/', r'/sobre/',
            r'/privacy/', r'/privacidad/', r'/terms/', r'/terminos/',
            r'/login/', r'/register/', r'/registro/',
            r'/suscripcion/', r'/subscription/', r'/newsletter/', r'/newsletters/',
            r'/rss/', r'/feed/', r'/sitemap/', r'/mapa/',
            
            # Categorías específicas de noticias
            r'/deportes/', r'/politica/', r'/economia/', r'/mundo/', r'/sociedad/',
            r'/tecnologia/', r'/cultura/', r'/espectaculos/', r'/gastronomia/',
            r'/turismo/', r'/vida/', r'/tendencias/', r'/opinion/', r'/editorial/',
            r'/columnas/', r'/blogs/', r'/foros/', r'/comentarios/',
            r'/calendario/', r'/eventos/', r'/galeria/', r'/videos/', r'/podcast/',
            r'/radio/', r'/tv/', r'/streaming/', r'/live/', r'/en-vivo/', r'/directo/',
            
            # Archivos y recursos
            r'\.(jpg|jpeg|png|gif|webp|bmp|svg|pdf|doc|docx|zip|rar|mp4|mp3)$',
            
            # APIs y servicios
            r'/api/', r'/ajax/', r'/json/', r'/xml/',
            
            # Redes sociales y externos
            r'facebook', r'twitter', r'instagram', r'youtube',
            r'linkedin', r'whatsapp', r'telegram',
            
            # Patrones de error
            r'/404', r'/error', r'/not-found',
        ]
        
        has_exclude_pattern = any(re.search(pattern, url_lower) for pattern in exclude_patterns)
        
        # Verificaciones adicionales
        path = parsed_url.path
        
        # No debe ser solo la raíz
        if path in ['/', '']:
            return False
        
        # No debe tener muchos parámetros (probablemente filtros)
        if len(parsed_url.query) > 50:
            return False
        
        # Debe tener al menos 2 segmentos en el path
        path_segments = [seg for seg in path.split('/') if seg]
        if len(path_segments) < 1:
            return False
        
        return has_article_pattern and not has_exclude_pattern
    
    def _find_additional_links(self, url: str, max_additional: int) -> List[str]:
        """Métodos adicionales para encontrar enlaces cuando el método principal falla"""
        additional_links = []
        
        try:
            # Método 1: Buscar en páginas de paginación
            pagination_links = self._find_pagination_links(url)
            for page_url in pagination_links[:3]:  # Solo las primeras 3 páginas
                try:
                    page_soup = self.get_page(page_url)
                    if page_soup:
                        page_links = self.find_article_links(page_soup, url, max_additional)
                        additional_links.extend(page_links)
                        if len(additional_links) >= max_additional:
                            break
                except Exception as e:
                    logger.debug(f"Error en página de paginación {page_url}: {e}")
                    continue
            
            # Método 2: Buscar enlaces con JavaScript (para sitios SPA)
            js_links = self._find_js_links(url)
            additional_links.extend(js_links)
            
            # Método 3: Buscar en sitemaps si están disponibles
            sitemap_links = self._find_sitemap_links(url)
            additional_links.extend(sitemap_links)
            
        except Exception as e:
            logger.debug(f"Error en métodos adicionales: {e}")
        
        # Limpiar duplicados y limitar
        unique_links = list(dict.fromkeys(additional_links))  # Mantiene orden
        return unique_links[:max_additional]
    
    def _find_pagination_links(self, base_url: str) -> List[str]:
        """Encontrar enlaces de paginación"""
        pagination_links = []
        
        try:
            soup = self.get_page(base_url)
            if not soup:
                return pagination_links
            
            # Selectores comunes de paginación
            pagination_selectors = [
                'a[href*="page="]',
                'a[href*="p="]',
                'a[href*="/page/"]',
                'a[href*="/p/"]',
                '.pagination a',
                '.pager a',
                '.page-nav a',
                '.paging a',
                'a[class*="page"]',
                'a[class*="next"]',
                'a[class*="more"]'
            ]
            
            for selector in pagination_selectors:
                try:
                    elements = soup.select(selector)
                    for element in elements:
                        href = element.get('href')
                        if href:
                            full_url = urljoin(base_url, href)
                            if full_url not in pagination_links:
                                pagination_links.append(full_url)
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"Error buscando paginación: {e}")
        
        return pagination_links[:5]  # Máximo 5 páginas
    
    def _find_js_links(self, url: str) -> List[str]:
        """Encontrar enlaces generados por JavaScript"""
        js_links = []
        
        try:
            if not self.driver:
                return js_links
            
            # Ejecutar JavaScript para encontrar enlaces dinámicos
            js_code = """
            var links = [];
            var allLinks = document.querySelectorAll('a[href]');
            for (var i = 0; i < allLinks.length; i++) {
                var href = allLinks[i].href;
                if (href && href.includes(window.location.hostname)) {
                    links.push(href);
                }
            }
            return links;
            """
            
            js_links = self.driver.execute_script(js_code)
            if js_links:
                # Filtrar enlaces válidos
                valid_links = []
                for link in js_links:
                    if self._is_article_url_improved(link, url):
                        valid_links.append(link)
                js_links = valid_links
                
        except Exception as e:
            logger.debug(f"Error en búsqueda JS: {e}")
        
        return js_links[:20]  # Máximo 20 enlaces JS
    
    def _find_sitemap_links(self, url: str) -> List[str]:
        """Buscar enlaces en sitemaps XML"""
        sitemap_links = []
        
        try:
            # URLs comunes de sitemap
            sitemap_urls = [
                urljoin(url, '/sitemap.xml'),
                urljoin(url, '/sitemap_index.xml'),
                urljoin(url, '/sitemaps.xml'),
                urljoin(url, '/sitemap-news.xml'),
                urljoin(url, '/sitemap-articles.xml')
            ]
            
            for sitemap_url in sitemap_urls:
                try:
                    response = requests.get(sitemap_url, timeout=10)
                    if response.status_code == 200:
                        # Parsear XML simple
                        content = response.text
                        import re
                        urls = re.findall(r'<loc>(.*?)</loc>', content)
                        
                        for found_url in urls:
                            if self._is_article_url_improved(found_url, url):
                                sitemap_links.append(found_url)
                                if len(sitemap_links) >= 50:  # Límite
                                    break
                        
                        if sitemap_links:
                            break  # Si encontramos enlaces, no buscar más sitemaps
                            
                except Exception as e:
                    logger.debug(f"Error en sitemap {sitemap_url}: {e}")
                    continue
                    
        except Exception as e:
            logger.debug(f"Error buscando sitemaps: {e}")
        
        return sitemap_links[:30]  # Máximo 30 enlaces de sitemap
    
    def close(self):
        """Cerrar el driver de Selenium"""
        if self.driver:
            self.driver.quit()
            logger.info("🔒 Selenium WebDriver cerrado")

class DatabaseManager:
    """Gestor universal de bases de datos"""
    
    def __init__(self, db_type="sqlite", **kwargs):
        self.db_type = db_type
        self.connection_params = kwargs
        self.engine = None
        self.init_connection()
    
    def init_connection(self):
        """Inicializar conexión según el tipo de base de datos"""
        try:
            if self.db_type == "sqlite":
                db_path = self.connection_params.get('db_path', 'news_database.db')
                self.engine = create_engine(f'sqlite:///{db_path}')
            
            elif self.db_type == "mysql" and MYSQL_AVAILABLE:
                connection_string = (
                    f"mysql+mysqlconnector://{self.connection_params['user']}:"
                    f"{self.connection_params['password']}@{self.connection_params['host']}:"
                    f"{self.connection_params.get('port', 3306)}/{self.connection_params['database']}"
                )
                self.engine = create_engine(connection_string)
            
            elif self.db_type == "postgresql" and POSTGRESQL_AVAILABLE:
                connection_string = (
                    f"postgresql://{self.connection_params['user']}:"
                    f"{self.connection_params['password']}@{self.connection_params['host']}:"
                    f"{self.connection_params.get('port', 5432)}/{self.connection_params['database']}"
                )
                self.engine = create_engine(connection_string)
            
            self.create_tables()
            
        except Exception as e:
            st.error(f"Error conectando a la base de datos: {e}")
            logger.error(f"Database connection error: {e}")
    
    def create_tables(self):
        """Crear tablas necesarias"""
        if self.engine is None:
            return
        
        try:
            # Crear tabla de artículos
            if self.db_type == "sqlite":
                articles_query = """
                    CREATE TABLE IF NOT EXISTS articles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        date TEXT,
                        author TEXT,
                        summary TEXT,
                        content TEXT,
                        original_url TEXT UNIQUE,
                        category TEXT,
                        newspaper TEXT,
                        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        images_found INTEGER DEFAULT 0,
                        images_downloaded INTEGER DEFAULT 0,
                        images_data TEXT
                    )
                """
                
                stats_query = """
                    CREATE TABLE IF NOT EXISTS scraping_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        newspaper TEXT,
                        category TEXT,
                        articles_found INTEGER,
                        scraping_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
            else:
                # Para MySQL y PostgreSQL
                articles_query = """
                    CREATE TABLE IF NOT EXISTS articles (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        title TEXT NOT NULL,
                        date TEXT,
                        author TEXT,
                        summary TEXT,
                        content LONGTEXT,
                        original_url TEXT UNIQUE,
                        category TEXT,
                        newspaper TEXT,
                        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        images_found INT DEFAULT 0,
                        images_downloaded INT DEFAULT 0,
                        images_data LONGTEXT
                    )
                """
                
                stats_query = """
                    CREATE TABLE IF NOT EXISTS scraping_stats (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        newspaper TEXT,
                        category TEXT,
                        articles_found INT,
                        scraping_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
            
            with self.engine.connect() as conn:
                # Ejecutar las consultas usando text() para SQLAlchemy 2.0+
                from sqlalchemy import text
                conn.execute(text(articles_query))
                conn.execute(text(stats_query))
                conn.commit()
                
            logger.info("✅ Tablas creadas exitosamente")
                
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
    
    def save_articles_bulk(self, articles_df: pd.DataFrame):
        """Guardar múltiples artículos en la base de datos"""
        if self.engine is None:
            return False
        
        try:
            # Preparar los datos para MySQL
            df_clean = articles_df.copy()
            
            # Convertir listas y diccionarios a JSON strings para MySQL
            for col in df_clean.columns:
                if df_clean[col].dtype == 'object':
                    df_clean[col] = df_clean[col].apply(
                        lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (list, dict)) else str(x) if pd.notna(x) else None
                    )
            
            # Asegurar que las columnas de imágenes existan
            if 'images_found' not in df_clean.columns:
                df_clean['images_found'] = 0
            if 'images_downloaded' not in df_clean.columns:
                df_clean['images_downloaded'] = 0
            if 'images_data' not in df_clean.columns:
                df_clean['images_data'] = '[]'
            
            # Convertir a int las columnas numéricas
            df_clean['images_found'] = pd.to_numeric(df_clean['images_found'], errors='coerce').fillna(0).astype(int)
            df_clean['images_downloaded'] = pd.to_numeric(df_clean['images_downloaded'], errors='coerce').fillna(0).astype(int)
            
            # Guardar en la base de datos
            df_clean.to_sql('articles', self.engine, if_exists='append', index=False, method='multi')
            logger.info(f"✅ {len(df_clean)} artículos guardados en la base de datos")
            return True
            
        except Exception as e:
            logger.error(f"Error saving articles: {e}")
            # Intentar guardar uno por uno si falla el bulk
            try:
                for idx, row in df_clean.iterrows():
                    row_df = pd.DataFrame([row])
                    row_df.to_sql('articles', self.engine, if_exists='append', index=False)
                logger.info(f"✅ {len(df_clean)} artículos guardados uno por uno")
                return True
            except Exception as e2:
                logger.error(f"Error saving articles individually: {e2}")
                return False
    
    def get_articles_df(self, category: str = None, newspaper: str = None, limit: int = None):
        """Obtener artículos como DataFrame"""
        if self.engine is None:
            return pd.DataFrame()
        
        try:
            query = "SELECT * FROM articles WHERE 1=1"
            params = {}
            
            if category:
                query += " AND category = %(category)s"
                params['category'] = category
            
            if newspaper:
                query += " AND newspaper = %(newspaper)s"
                params['newspaper'] = newspaper
            
            query += " ORDER BY scraped_at DESC"
            
            if limit:
                query += f" LIMIT {limit}"
            
            return pd.read_sql(query, self.engine, params=params)
            
        except Exception as e:
            logger.error(f"Error retrieving articles: {e}")
            return pd.DataFrame()

class AdvancedScraper:
    """Scraper avanzado con Selenium integrado y extracción de imágenes"""
    
    def __init__(self):
        self.selenium_manager = None
        self.image_manager = ImageManager()
        self.init_selenium()
    
    def init_selenium(self):
        """Inicializar Selenium de forma lazy"""
        if not self.selenium_manager:
            self.selenium_manager = SeleniumManager(headless=True, wait_time=10)
    
    def analyze_page_structure(self, url: str) -> Dict:
        """Analizar estructura de la página usando Selenium"""
        self.init_selenium()
        
        soup = self.selenium_manager.get_page(url)
        if not soup:
            return {}
        
        structure = {
            'title_selectors': self._find_title_selectors(soup),
            'date_selectors': self._find_date_selectors(soup),
            'author_selectors': self._find_author_selectors(soup),
            'content_selectors': self._find_content_selectors(soup),
            'site_name': self._extract_site_name(soup, url)
        }
        
        return structure
    
    def _find_title_selectors(self, soup: BeautifulSoup) -> List[str]:
        """Encontrar selectores de título optimizados"""
        selectors = []
        
        # Buscar títulos por prioridad
        priority_selectors = [
            'h1[class*="title"]', 'h1[class*="headline"]', 'h1[class*="header"]',
            '.title h1', '.headline h1', '.header h1',
            'article h1', '.article h1', '.post h1',
            'h1', 'h2[class*="title"]', '.entry-title'
        ]
        
        for selector in priority_selectors:
            try:
                element = soup.select_one(selector)
                if element and len(element.get_text().strip()) > 10:
                    selectors.append(selector)
            except:
                pass
        
        return selectors or ['h1', 'title']
    
    def _find_date_selectors(self, soup: BeautifulSoup) -> List[str]:
        """Encontrar selectores de fecha"""
        return [
            'time[datetime]', '[datetime]', 'time',
            '[class*="date"]', '[class*="time"]', '[class*="published"]',
            '.meta time', '.article-meta time', '.post-meta time'
        ]
    
    def _find_author_selectors(self, soup: BeautifulSoup) -> List[str]:
        """Encontrar selectores de autor"""
        return [
            '[class*="author"]', '[rel="author"]', '[class*="byline"]',
            '[class*="writer"]', '.meta [class*="author"]',
            '.article-author', '.post-author'
        ]
    
    def _find_content_selectors(self, soup: BeautifulSoup) -> List[str]:
        """Encontrar selectores de contenido"""
        return [
            '.article-body', '.entry-content', '.post-content',
            '[class*="content"]', 'article .content', '.article-text',
            '.post-body', '.news-content', 'article p'
        ]
    
    def _extract_site_name(self, soup: BeautifulSoup, url: str) -> str:
        """Extraer nombre del sitio"""
        # Intentar desde meta tags
        meta_selectors = [
            'meta[property="og:site_name"]',
            'meta[name="application-name"]',
            'meta[name="site"]'
        ]
        
        for selector in meta_selectors:
            element = soup.select_one(selector)
            if element and element.get('content'):
                return element['content']
        
        # Desde el título
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text()
            parts = re.split(r'[-|–—]', title)
            if len(parts) > 1:
                return parts[-1].strip()
        
        # Desde el dominio
        domain = urlparse(url).netloc
        return domain.replace('www.', '').split('.')[0].title()
    
    def scrape_single_article(self, url: str, structure: Dict = None, extract_images: bool = True, max_images_per_article: int = 10) -> Optional[Dict]:
        """Extraer datos de un artículo usando Selenium con imágenes opcionales"""
        self.init_selenium()
        
        soup = self.selenium_manager.get_page(url)
        if not soup:
            return None
        
        if not structure:
            structure = self.analyze_page_structure(url)
        
        try:
            # Generar ID único para el artículo
            article_id = hashlib.md5(url.encode()).hexdigest()[:12]
            
            article = {
                'original_url': url,
                'title': self._extract_by_selectors(soup, structure.get('title_selectors', [])),
                'date': self._extract_by_selectors(soup, structure.get('date_selectors', [])),
                'author': self._extract_by_selectors(soup, structure.get('author_selectors', [])),
                'content': self._extract_content_advanced(soup, structure.get('content_selectors', [])),
                'newspaper': structure.get('site_name', 'Desconocido'),
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'article_id': article_id
            }
            
            # Generar resumen
            article['summary'] = self._generate_summary(article['content'])
            
            # Extraer imágenes si está habilitado
            if extract_images:
                try:
                    images_info = self.image_manager.extract_images_from_soup(soup, url)
                    article['images_found'] = len(images_info)
                    
                    # Descargar imágenes principales (límite configurable)
                    downloaded_images = []
                    for i, img_info in enumerate(images_info[:max_images_per_article]):
                        # Filtrar mejor las imágenes relevantes
                        alt_text = img_info.get('alt_text', '').lower()
                        img_class = img_info.get('class', '').lower()
                        img_url = img_info.get('url', '').lower()
                        
                        # Descargar más imágenes - filtro menos restrictivo
                        is_relevant = (
                            any(keyword in alt_text for keyword in ['noticia', 'imagen', 'foto', 'foto principal', 'photo', 'picture', 'image']) or
                            any(keyword in img_class for keyword in ['main', 'featured', 'principal', 'hero', 'content', 'article', 'news']) or
                            any(keyword in img_url for keyword in ['/noticias/', '/imagenes/', '/fotos/', '/images/', '/photos/', '/media/']) or
                            not alt_text  # Si no tiene alt_text, intentar descargar
                        )
                        
                        # Descargar si es relevante O si no tiene alt_text (más permisivo)
                        if is_relevant:
                            local_path = self.image_manager.download_image(img_info, article_id)
                            if local_path:
                                img_data = self.image_manager.get_image_info(local_path)
                                downloaded_images.append({
                                    'local_path': local_path,
                                    'url': img_info['url'],
                                    'alt_text': img_info.get('alt_text', ''),
                                    'width': img_data.get('width', 0),
                                    'height': img_data.get('height', 0),
                                    'size_bytes': img_data.get('size_bytes', 0)
                                })
                    
                    article['images_downloaded'] = len(downloaded_images)
                    # Convertir a JSON string para MySQL
                    article['images_data'] = json.dumps(downloaded_images, ensure_ascii=False)
                    
                except Exception as e:
                    logger.warning(f"Error extrayendo imágenes: {e}")
                    article['images_found'] = 0
                    article['images_downloaded'] = 0
                    article['images_data'] = '[]'
            else:
                article['images_found'] = 0
                article['images_downloaded'] = 0
                article['images_data'] = '[]'
            
            logger.info(f"✅ Artículo extraído: {article['title'][:50]}... (Imágenes: {article['images_downloaded']})")
            return article
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo artículo {url}: {e}")
            return None
    
    def _extract_by_selectors(self, soup: BeautifulSoup, selectors: List[str]) -> str:
        """Extraer texto usando selectores con prioridad"""
        for selector in selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().strip()
                    if text and len(text) > 3:
                        # Para fechas, intentar extraer datetime
                        if 'datetime' in selector and element.get('datetime'):
                            return element['datetime']
                        return text
            except:
                continue
        
        return "No disponible"
    
    def _extract_content_advanced(self, soup: BeautifulSoup, selectors: List[str]) -> str:
        """Extraer contenido con limpieza avanzada"""
        content_parts = []
        
        for selector in selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    # Limpiar elementos no deseados
                    for unwanted in element(['script', 'style', 'nav', 'footer', 'aside', 
                                           'advertisement', '.ad', '.ads', '.social-share']):
                        unwanted.decompose()
                    
                    text = element.get_text().strip()
                    if len(text) > 50:  # Contenido sustancial
                        content_parts.append(text)
                        break  # Usar el primer contenido válido encontrado
            except:
                continue
        
        if content_parts:
            full_content = '\n\n'.join(content_parts)
            return full_content  # No limitar el contenido
        
        return "Contenido no disponible"
    
    def _generate_summary(self, content: str, max_length: int = 200) -> str:
        """Generar resumen inteligente"""
        if len(content) <= max_length:
            return content
        
        # Dividir en oraciones
        sentences = re.split(r'[.!?]+', content)
        summary = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(summary + sentence) <= max_length and len(sentence) > 10:
                summary += sentence + ". "
            else:
                break
        
        return summary.strip() + "..." if summary else content[:max_length] + "..."
    
    def crawl_and_scrape(self, url: str, max_articles: int = 20, progress_callback=None, extract_images: bool = True, max_images_per_article: int = 10, pause_time: float = 0.5) -> List[Dict]:
        """Crawlear y extraer múltiples artículos con imágenes opcionales - OPTIMIZADO"""
        self.init_selenium()
        
        # Obtener la página principal
        soup = self.selenium_manager.get_page(url)
        if not soup:
            return []
        
        # Encontrar enlaces de artículos
        article_links = self.selenium_manager.find_article_links(soup, url, max_articles)
        
        # Si no se encuentran suficientes enlaces, intentar métodos adicionales
        if len(article_links) < max_articles // 2:
            logger.info("🔄 Pocos enlaces encontrados, intentando métodos adicionales...")
            additional_links = self._find_additional_links(url, max_articles - len(article_links))
            article_links.extend(additional_links)
        
        if not article_links:
            logger.warning("🔍 No se encontraron enlaces de artículos")
            return []
        
        # Analizar estructura una vez
        structure = self.analyze_page_structure(url)
        
        # Extraer artículos con optimizaciones
        articles = []
        total_images_downloaded = 0
        
        # Procesar en lotes para mejor rendimiento
        batch_size = 5
        for batch_start in range(0, len(article_links), batch_size):
            batch_links = article_links[batch_start:batch_start + batch_size]
            
            for i, link in enumerate(batch_links):
                current_index = batch_start + i + 1
                if progress_callback:
                    progress_callback(current_index, len(article_links))
                
                article = self.scrape_single_article(link, structure, extract_images, max_images_per_article)
                if article:
                    articles.append(article)
                    total_images_downloaded += article.get('images_downloaded', 0)
                
                # Pausa configurable para mejor rendimiento
                time.sleep(pause_time)
            
            # Pausa más larga entre lotes
            if batch_start + batch_size < len(article_links):
                time.sleep(2)
        
        logger.info(f"🎉 Extracción completada: {len(articles)} artículos, {total_images_downloaded} imágenes descargadas")
        return articles
    
    def close(self):
        """Cerrar recursos"""
        if self.selenium_manager:
            self.selenium_manager.close()

class ExportManager:
    """Gestor de exportaciones a diferentes formatos"""
    
    @staticmethod
    def to_excel(df: pd.DataFrame, filename: str = "news_export.xlsx") -> bytes:
        """Exportar a Excel con formato profesional"""
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Noticias', index=False)
            
            # Formatear el Excel
            workbook = writer.book
            worksheet = writer.sheets['Noticias']
            
            # Estilos
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            
            # Aplicar formato al header
            for cell in worksheet[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center")
            
            # Ajustar ancho de columnas
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        return output.getvalue()
    
    @staticmethod
    def to_csv(df: pd.DataFrame) -> str:
        """Exportar a CSV"""
        return df.to_csv(index=False)
    
    @staticmethod
    def to_json(df: pd.DataFrame) -> str:
        """Exportar a JSON"""
        import json
        # Convertir DataFrame a dict y luego a JSON con ensure_ascii=False
        data_dict = df.to_dict(orient='records')
        return json.dumps(data_dict, indent=2, ensure_ascii=False)

def main():
    st.set_page_config(
        page_title="🕷️ Web Scraper Universal",
        page_icon="🕷️",
        layout="wide"
    )
    
    # Estilos CSS globales para el diseño moderno
    st.markdown("""
    <style>
    /* Estilos globales para el diseño moderno */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        color: white;
        text-align: center;
    }
    
    .main-header h1 {
        color: white !important;
        margin: 0;
        font-size: 2.5rem;
    }
    
    .main-header p {
        color: rgba(255,255,255,0.9) !important;
        margin: 10px 0 0 0;
        font-size: 1.1rem;
    }
    
    /* Mejorar las tarjetas de artículos */
    .article-card {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        background-color: #ffffff;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    
    .article-card:hover {
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }
    
    .article-category {
        background: linear-gradient(45deg, #ffd700, #ffed4e);
        color: #000;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: bold;
        text-transform: uppercase;
        display: inline-block;
        margin-bottom: 15px;
        letter-spacing: 0.5px;
        box-shadow: 0 2px 4px rgba(255,215,0,0.3);
    }
    
    .article-title {
        font-size: 18px;
        font-weight: bold;
        color: #000;
        line-height: 1.4;
        margin-bottom: 15px;
        font-family: 'Georgia', serif;
        flex-grow: 1;
    }
    
    .article-meta {
        font-size: 13px;
        color: #666;
        margin-bottom: 10px;
        font-style: italic;
    }
    
    /* Botones mejorados */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Navegación de páginas */
    .page-nav {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        margin: 20px 0;
        border: 1px solid #e9ecef;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .article-card {
            margin-bottom: 15px;
            padding: 15px;
        }
        
        .article-title {
            font-size: 16px;
        }
        
        .article-category {
            font-size: 10px;
            padding: 4px 8px;
        }
    }
    
    /* Mejorar el selector de página */
    .stSelectbox > div > div {
        background-color: #f8f9fa;
        border-radius: 8px;
    }
    
    /* Estilo para los filtros */
    .filter-section {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        border: 1px solid #e9ecef;
    }
    
    /* Mejorar las métricas */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    /* Estilo para el header de la aplicación */
    .app-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 15px;
        margin-bottom: 30px;
        color: white;
        text-align: center;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
    }
    
    .app-header h1 {
        color: white !important;
        margin: 0;
        font-size: 3rem;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .app-header p {
        color: rgba(255,255,255,0.9) !important;
        margin: 15px 0 0 0;
        font-size: 1.2rem;
        font-weight: 300;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🕷️ Web Scraper Universal")
    st.markdown("**Extrae contenido de cualquier sitio web (incluso con JavaScript) y exporta a múltiples formatos**")
    
    # Inicializar session state
    if 'scraped_data' not in st.session_state:
        st.session_state.scraped_data = pd.DataFrame()
    
    if 'scraper' not in st.session_state:
        st.session_state.scraper = AdvancedScraper()
    
    # Sidebar - Configuración
    st.sidebar.title("⚙️ Configuración de Scraping")
    
    # URL de entrada
    st.sidebar.subheader("🌐 URL Objetivo")
    input_url = st.sidebar.text_input(
        "Ingresa la URL a scrapear:", 
        placeholder="https://elcomercio.pe/politica/",
        help="Puede ser una página específica o una sección de noticias"
    )
    
    # Modo de scraping
    st.sidebar.subheader("🔧 Modo de Extracción")
    
    # Opciones de scraping
    scraping_options = ["📄 Artículo Individual", "🕷️ Múltiples Artículos"]
    
    # Agregar opción híbrida si está disponible
    if HYBRID_CRAWLER_AVAILABLE:
        scraping_options.append("🚀 Crawler Híbrido")
    
    scraping_mode = st.sidebar.radio(
        "Selecciona el modo:",
        scraping_options,
        help="Individual: una sola página | Múltiples: busca varios artículos de una sección | Híbrido: método avanzado con mejor detección"
    )
    
    # Información adicional para el modo híbrido
    if scraping_mode == "🚀 Crawler Híbrido":
        st.sidebar.info("""
        🚀 **Crawler Híbrido Avanzado**
        
        ✅ **Ventajas:**
        - Mejor detección de artículos
        - Múltiples métodos de extracción
        - Optimizado para sitios complejos
        - Extracción de imágenes mejorada
        
        ⚡ **Modos disponibles:**
        - Rápido: Prioriza velocidad
        - Completo: Máxima cobertura
        """)
    
    # Modo de procesamiento (definido ANTES de su uso)
    processing_mode = "🔧 Estándar (Selenium, hasta 100 artículos)"  # Valor por defecto
    
    if OPTIMIZED_SCRAPER_AVAILABLE:
        processing_mode = st.sidebar.selectbox(
            "⚙️ Modo de procesamiento:",
            ["🚀 Ultra-Rápido (Paralelo, 2000+ artículos)", "🔧 Estándar (Selenium, hasta 100 artículos)"],
            help="Ultra-Rápido: Requests + Paralelismo | Estándar: Selenium tradicional"
        )
    else:
        st.sidebar.warning("⚠️ Scraper optimizado no disponible, usando modo estándar")
    
    # Configuraciones adicionales
    if scraping_mode == "🕷️ Múltiples Artículos":
        # Límite dinámico según el modo de procesamiento
        if processing_mode == "🚀 Ultra-Rápido (Paralelo, 2000+ artículos)":
            max_articles = st.sidebar.slider(
                "Máximo de artículos:", 
                min_value=5, 
                max_value=2000, 
                value=100,
                help="Modo ultra-rápido: hasta 2000 artículos"
            )
        else:
            max_articles = st.sidebar.slider(
                "Máximo de artículos:", 
                min_value=5, 
                max_value=100, 
                value=20,
            help="Cantidad máxima de artículos a extraer"
        )
    
    elif scraping_mode == "🚀 Crawler Híbrido":
        # Configuración para crawler híbrido
        max_articles = st.sidebar.slider(
            "Máximo de artículos:", 
            min_value=5, 
            max_value=200, 
            value=50,
            help="Cantidad máxima de artículos a extraer con crawler híbrido"
        )
        
        # Modo de velocidad para crawler híbrido
        hybrid_speed = st.sidebar.radio(
            "Modo de velocidad:",
            ["⚡ Rápido (Requests + Selenium mínimo)", "🔍 Completo (Todos los métodos)"],
            help="Rápido: Prioriza Requests, usa Selenium solo si es necesario | Completo: Usa todos los métodos disponibles"
        )
        
        # Modo debug para crawler híbrido
        hybrid_debug = st.sidebar.checkbox(
            "🐛 Modo Debug",
            value=False,
            help="Mostrar información detallada del proceso de extracción"
        )
    
    # Valor por defecto para max_articles si no se define
    if 'max_articles' not in locals():
        max_articles = 20
    
    # Categoría personalizada
    custom_category = st.sidebar.text_input(
        "Categoría personalizada:", 
        placeholder="ej: política, deportes, tecnología",
        help="Etiqueta para organizar tus artículos"
    )
    
    # Opciones avanzadas
    with st.sidebar.expander("⚙️ Opciones Avanzadas"):
        show_browser = st.checkbox(
            "Mostrar navegador durante scraping", 
            value=False,
            help="Útil para debugging, pero más lento"
        )
        
        wait_time = st.slider(
            "Tiempo de espera (segundos):", 
            min_value=5, 
            max_value=30, 
            value=10,
            help="Tiempo máximo para cargar cada página"
        )
        
        extract_images = st.checkbox(
            "🖼️ Extraer y descargar imágenes", 
            value=True,
            help="Descarga imágenes encontradas en los artículos"
        )
        
        max_images_per_article = st.slider(
            "Máximo de imágenes por artículo:", 
            min_value=1, 
            max_value=10, 
            value=3,
            help="Límite de imágenes a descargar por artículo"
        )
        
        # Modo de velocidad
        speed_mode = st.selectbox(
            "🚀 Modo de velocidad:",
            ["⚡ Rápido (menos imágenes, más velocidad)", "🖼️ Completo (más imágenes, más lento)", "🎯 Equilibrado"],
            help="Rápido: 3 imágenes, 0.5s pausa | Completo: 5 imágenes, 1s pausa | Equilibrado: 3 imágenes, 0.7s pausa"
        )
        
    
    # Botón principal de scraping
    scraping_button = st.sidebar.button(
        "🚀 Iniciar Extracción", 
        type="primary",
        use_container_width=True
    )
    
    # Ejecutar scraping
    if scraping_button and input_url:
        # Configurar Selenium según opciones
        if hasattr(st.session_state.scraper, 'selenium_manager') and st.session_state.scraper.selenium_manager:
            st.session_state.scraper.close()
        
        st.session_state.scraper.selenium_manager = SeleniumManager(
            headless=not show_browser, 
            wait_time=wait_time
        )
        
        with st.spinner("🔄 Inicializando navegador y analizando sitio web..."):
            
            if scraping_mode == "📄 Artículo Individual":
                # Scraping individual
                article = st.session_state.scraper.scrape_single_article(input_url, extract_images=extract_images, max_images_per_article=max_images_per_article)
                
                if article:
                    article['category'] = custom_category or "general"
                    df = pd.DataFrame([article])
                    st.session_state.scraped_data = pd.concat([st.session_state.scraped_data, df], ignore_index=True)
                    
                    images_msg = f" y {article.get('images_downloaded', 0)} imágenes" if extract_images else ""
                    st.sidebar.success(f"✅ ¡Artículo extraído exitosamente{images_msg}!")
                    st.balloons()
                else:
                    st.sidebar.error("❌ Error extrayendo el artículo. Verifica la URL.")
            
            elif scraping_mode == "🚀 Crawler Híbrido":
                # Crawler híbrido
                if hybrid_speed == "⚡ Rápido (Requests + Selenium mínimo)":
                    st.info("⚡ Ejecutando crawler híbrido RÁPIDO...")
                else:
                    st.info("🔍 Ejecutando crawler híbrido COMPLETO...")
                
                try:
                    # Usar el crawler híbrido
                    fast_mode = hybrid_speed == "⚡ Rápido (Requests + Selenium mínimo)"
                    
                    if hybrid_debug:
                        st.info("🐛 Modo Debug activado - Mostrando información detallada...")
                        debug_container = st.container()
                        with debug_container:
                            st.write("**🔍 Información de Debug:**")
                            st.write(f"- URL: {input_url}")
                            st.write(f"- Modo: {'Rápido' if fast_mode else 'Completo'}")
                            st.write(f"- Máximo artículos: {max_articles}")
                            st.write(f"- Máximo imágenes: {max_images_per_article}")
                            st.write(f"- Descargar imágenes: {extract_images}")
                    
                    articles, images = crawl_complete_hybrid(
                        url=input_url,
                        max_articles=max_articles,
                        max_images=max_images_per_article,
                        download_images=extract_images,
                        output_dir="scraped_images",
                        fast_mode=fast_mode
                    )
                    
                    if hybrid_debug:
                        with debug_container:
                            st.write("**📊 Resultados del Debug:**")
                            st.write(f"- Artículos encontrados: {len(articles)}")
                            st.write(f"- Imágenes encontradas: {len(images)}")
                            if articles:
                                st.write("**📰 Primeros artículos:**")
                                for i, article in enumerate(articles[:3]):
                                    st.write(f"{i+1}. {article.get('title', 'Sin título')[:50]}...")
                            if images:
                                st.write("**🖼️ Primeras imágenes:**")
                                for i, img in enumerate(images[:3]):
                                    st.write(f"{i+1}. {img.get('filename', 'Sin nombre')}")
                    
                    if articles:
                        st.sidebar.success(f"✅ Crawler híbrido completado: {len(articles)} artículos, {len(images)} imágenes")
                        
                        # Convertir artículos a formato compatible
                        hybrid_articles = []
                        for article in articles:
                            article_data = {
                                'title': article.get('title', ''),
                                'url': article.get('url', ''),
                                'content': '',  # El crawler híbrido no extrae contenido completo
                                'summary': '',  # Agregar columna summary
                                'author': '',
                                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'category': custom_category or 'Híbrido',
                                'newspaper': urlparse(input_url).netloc,  # Usar 'newspaper' en lugar de 'source'
                                'images_downloaded': len(images),
                                'original_url': article.get('url', ''),
                                'relevance_score': article.get('relevance_score', 0)
                            }
                            hybrid_articles.append(article_data)
                        
                        # Agregar a los datos
                        df = pd.DataFrame(hybrid_articles)
                        st.session_state.scraped_data = pd.concat([st.session_state.scraped_data, df], ignore_index=True)
                        
                        # Mostrar resultados detallados
                        display_hybrid_results(articles, images)
                        
                        st.balloons()
                    else:
                        st.sidebar.error("❌ No se encontraron artículos con el crawler híbrido")
                        
                except Exception as e:
                    st.sidebar.error(f"❌ Error en crawler híbrido: {str(e)}")
            
            else:
                # Extracción de múltiples artículos
                progress_bar = st.sidebar.progress(0)
                status_text = st.sidebar.empty()
                
                def update_progress(current, total):
                    progress = current / total
                    progress_bar.progress(progress)
                    status_text.text(f"Procesando artículo {current}/{total}")
                
                # Aplicar configuración de velocidad
                if speed_mode == "⚡ Rápido (menos imágenes, más velocidad)":
                    max_images = 3
                    pause_time = 0.3
                elif speed_mode == "🖼️ Completo (más imágenes, más lento)":
                    max_images = 5
                    pause_time = 1.0
                else:  # Equilibrado
                    max_images = 3
                    pause_time = 0.7
                
                # Elegir método de scraping
                if processing_mode == "🚀 Ultra-Rápido (Paralelo, 2000+ artículos)" and OPTIMIZED_SCRAPER_AVAILABLE:
                    # Usar scraper optimizado
                    st.info("🚀 Usando modo Ultra-Rápido con procesamiento paralelo...")
                    
                    # Configurar scraper optimizado
                    max_workers = min(20, max_articles // 10)  # Ajustar workers según cantidad
                    optimized_scraper = SmartScraper(max_workers=max_workers)
                    
                    try:
                        # Convertir artículos optimizados a formato estándar
                        optimized_articles = optimized_scraper.crawl_and_scrape_parallel(
                            input_url,
                            max_articles=max_articles,
                            progress_callback=update_progress,
                            extract_images=extract_images
                        )
                        
                        # Convertir a formato estándar
                        articles = []
                        for opt_article in optimized_articles:
                            article = {
                                'title': opt_article.title,
                                'content': opt_article.content,
                                'summary': opt_article.summary,
                                'author': opt_article.author,
                                'date': opt_article.date,
                                'category': opt_article.category,
                                'newspaper': opt_article.newspaper,
                                'original_url': opt_article.url,
                                'images_found': opt_article.images_found,
                                'images_downloaded': opt_article.images_downloaded,
                                'images_data': opt_article.images_data,
                                'scraped_at': opt_article.scraped_at,
                                'article_id': opt_article.article_id
                            }
                            articles.append(article)
                        
                        optimized_scraper.close()
                        
                    except Exception as e:
                        st.error(f"❌ Error en modo ultra-rápido: {e}")
                        st.info("🔄 Cambiando a modo estándar...")
                        # Fallback a modo estándar
                        articles = st.session_state.scraper.crawl_and_scrape(
                            input_url, 
                            max_articles, 
                            progress_callback=update_progress,
                            extract_images=extract_images,
                            max_images_per_article=max_images,
                            pause_time=pause_time
                        )
                else:
                    # Usar scraper estándar
                    articles = st.session_state.scraper.crawl_and_scrape(
                        input_url, 
                        max_articles, 
                        progress_callback=update_progress,
                        extract_images=extract_images,
                        max_images_per_article=max_images,
                        pause_time=pause_time
                    )
                
                if articles:
                    # Agregar categoría a todos los artículos
                    for article in articles:
                        article['category'] = custom_category or "general"
                    
                    df = pd.DataFrame(articles)
                    st.session_state.scraped_data = pd.concat([st.session_state.scraped_data, df], ignore_index=True)
                    
                    total_images = sum(article.get('images_downloaded', 0) for article in articles)
                    images_msg = f" y {total_images} imágenes" if extract_images else ""
                    st.sidebar.success(f"✅ ¡{len(articles)} artículos extraídos exitosamente{images_msg}!")
                    st.balloons()
                else:
                    st.sidebar.error("❌ No se pudieron extraer artículos. Verifica la URL o intenta con modo individual.")
                
                progress_bar.empty()
                status_text.empty()
    
    elif scraping_button and not input_url:
        st.sidebar.warning("⚠️ Por favor ingresa una URL válida")
    
    # Mostrar contenido principal
    if not st.session_state.scraped_data.empty:
        # Métricas principales
        st.header("📊 Resumen de Extracción")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("📰 Total Artículos", len(st.session_state.scraped_data))
        with col2:
            st.metric("🌐 Sitios Web", st.session_state.scraped_data['newspaper'].nunique())
        with col3:
            st.metric("🏷️ Categorías", st.session_state.scraped_data['category'].nunique())
        with col4:
            total_images = st.session_state.scraped_data.get('images_downloaded', pd.Series([0])).sum()
            st.metric("🖼️ Imágenes", total_images)
        with col5:
            latest_scrape = st.session_state.scraped_data['scraped_at'].max()
            st.metric("⏰ Último Scraping", latest_scrape[:16] if latest_scrape else "N/A")
        
        # Filtros dinámicos
        st.subheader("🔍 Filtros de Búsqueda")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            newspapers = ["Todos"] + sorted(st.session_state.scraped_data['newspaper'].unique().tolist())
            selected_newspaper = st.selectbox("📰 Filtrar por Sitio Web:", newspapers)
        
        with col2:
            categories = ["Todas"] + sorted(st.session_state.scraped_data['category'].unique().tolist())
            selected_category = st.selectbox("🏷️ Filtrar por Categoría:", categories)
        
        with col3:
            search_term = st.text_input("🔍 Buscar en títulos:", placeholder="Ingresa término de búsqueda")
        
        # Aplicar filtros
        filtered_data = st.session_state.scraped_data.copy()
        
        if selected_newspaper != "Todos":
            filtered_data = filtered_data[filtered_data['newspaper'] == selected_newspaper]
        
        if selected_category != "Todas":
            filtered_data = filtered_data[filtered_data['category'] == selected_category]
        
        if search_term:
            filtered_data = filtered_data[
                filtered_data['title'].str.contains(search_term, case=False, na=False)
            ]
        
        st.info(f"📊 Mostrando {len(filtered_data)} de {len(st.session_state.scraped_data)} artículos")
        
        # Tabs principales
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📰 Artículos", 
            "📊 Análisis Visual", 
            "💾 Exportar Datos", 
            "🗄️ Base de Datos", 
            "⚙️ Configuración"
        ])
        
        with tab1:
            st.header("📰 Lista de Artículos Extraídos")
            
            if not filtered_data.empty:
                # Mostrar artículos en cards expandibles (diseño original)
                for idx, article in filtered_data.iterrows():
                    with st.expander(
                        f"📄 {article['title'][:80]}{'...' if len(article['title']) > 80 else ''}"
                    ):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.markdown(f"**🏷️ Categoría:** {article['category']}")
                            st.markdown(f"**🌐 Sitio:** {article['newspaper']}")
                            st.markdown(f"**✍️ Autor:** {article['author']}")
                            
                            # Mostrar información de imágenes
                            if 'images_downloaded' in article and article['images_downloaded'] > 0:
                                st.markdown(f"**🖼️ Imágenes:** {article['images_downloaded']} descargadas")
                                
                                # Mostrar imágenes si están disponibles
                                if 'images_data' in article and article['images_data']:
                                    st.markdown("**📸 Imágenes del artículo:**")
                                    
                                    # Parsear JSON si es string
                                    try:
                                        if isinstance(article['images_data'], str):
                                            images_list = json.loads(article['images_data'])
                                        else:
                                            images_list = article['images_data']
                                        
                                        for i, img_data in enumerate(images_list[:3]):  # Mostrar máximo 3
                                            try:
                                                if isinstance(img_data, dict) and 'local_path' in img_data:
                                                    if os.path.exists(img_data['local_path']):
                                                        st.image(img_data['local_path'], 
                                                               caption=f"{img_data.get('alt_text', 'Imagen')} ({img_data.get('width', 0)}x{img_data.get('height', 0)})",
                                                               width=200)
                                                    else:
                                                        st.write(f"❌ Imagen no encontrada: {img_data['local_path']}")
                                            except Exception as e:
                                                st.write(f"❌ Error mostrando imagen {i+1}: {e}")
                                    except Exception as e:
                                        st.write(f"❌ Error parseando datos de imágenes: {e}")
                            
                            st.markdown("**📝 Resumen:**")
                            st.write(article['summary'])
                            
                            # Mostrar contenido completo en un expander
                            if article['content']:
                                with st.expander("📖 Ver contenido completo", expanded=False):
                                    st.markdown(article['content'])
                        
                        with col2:
                            st.markdown(f"**📅 Fecha:** {article['date']}")
                            st.markdown(f"**⏰ Extraído:** {article['scraped_at'][:16]}")
                            
                            if st.button("🔗 Ver Original", key=f"link_{idx}"):
                                link_val = article['original_url'] if 'original_url' in article else article.get('url', '')
                                st.write(f"🌐 **URL:** {link_val}")
                            
                            # Botón para abrir en nueva pestaña
                            link_val = article['original_url'] if 'original_url' in article else article.get('url', '')
                            st.markdown(
                                f"[🔗 Abrir Original]({link_val})",
                                unsafe_allow_html=True
                            )
            else:
                st.info("🔍 No se encontraron artículos con los filtros seleccionados.")
        
        with tab2:
            st.header("📊 Análisis Visual de Datos")
            
            if not filtered_data.empty:
                # Gráfico 1: Artículos por sitio web
                st.subheader("📰 Distribución por Sitio Web")
                site_counts = filtered_data['newspaper'].value_counts()
                
                fig1 = px.bar(
                    x=site_counts.values,
                    y=site_counts.index,
                    orientation='h',
                    title="Cantidad de Artículos por Sitio Web",
                    labels={'x': 'Número de Artículos', 'y': 'Sitio Web'},
                    color=site_counts.values,
                    color_continuous_scale='viridis'
                )
                fig1.update_layout(height=400)
                st.plotly_chart(fig1, use_container_width=True)
                
                # Gráfico 2: Distribución por categorías
                st.subheader("🏷️ Distribución por Categorías")
                cat_counts = filtered_data['category'].value_counts()
                
                fig2 = px.pie(
                    values=cat_counts.values,
                    names=cat_counts.index,
                    title="Distribución por Categoría",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig2.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig2, use_container_width=True)
                
                # Gráfico 3: Timeline de extracción
                st.subheader("⏰ Timeline de Extracción")
                timeline_data = filtered_data.copy()
                timeline_data['date_only'] = pd.to_datetime(timeline_data['scraped_at'], format='mixed').dt.date
                timeline_counts = timeline_data['date_only'].value_counts().sort_index()
                
                fig3 = px.line(
                    x=timeline_counts.index,
                    y=timeline_counts.values,
                    title="Artículos Extraídos por Fecha",
                    labels={'x': 'Fecha', 'y': 'Número de Artículos'},
                    markers=True
                )
                fig3.update_layout(height=400)
                st.plotly_chart(fig3, use_container_width=True)
                
                # Tabla de estadísticas
                st.subheader("📋 Estadísticas Detalladas")
                stats_df = filtered_data.groupby(['newspaper', 'category']).size().reset_index()
                stats_df.columns = ['Sitio Web', 'Categoría', 'Cantidad de Artículos']
                st.dataframe(stats_df, use_container_width=True)
                
            else:
                st.info("📊 No hay datos suficientes para generar análisis visual.")
        
        with tab3:
            st.header("💾 Exportar Datos")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("📁 Formatos Disponibles")
                
                if not filtered_data.empty:
                    # Botón Excel
                    excel_data = ExportManager.to_excel(filtered_data)
                    st.download_button(
                        label="📗 Descargar Excel (.xlsx)",
                        data=excel_data,
                        file_name=f"noticias_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        help="Archivo Excel con formato profesional"
                    )
                    
                    # Botón CSV
                    csv_data = ExportManager.to_csv(filtered_data)
                    st.download_button(
                        label="📄 Descargar CSV",
                        data=csv_data,
                        file_name=f"noticias_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        help="Archivo CSV compatible con Excel y análisis de datos"
                    )
                    
                    # Botón JSON
                    json_data = ExportManager.to_json(filtered_data)
                    st.download_button(
                        label="📋 Descargar JSON",
                        data=json_data,
                        file_name=f"noticias_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        help="Formato JSON para desarrollo web y APIs"
                    )
                else:
                    st.warning("⚠️ No hay datos para exportar. Ejecuta primero el scraping.")
            
            with col2:
                st.subheader("👁️ Vista Previa")
                if not filtered_data.empty:
                    preview_columns = ['title', 'newspaper', 'category', 'author', 'date']
                    available_columns = [col for col in preview_columns if col in filtered_data.columns]
                    st.dataframe(
                        filtered_data[available_columns].head(10),
                        use_container_width=True,
                        hide_index=True
                    )
                    st.caption(f"Mostrando las primeras 10 filas de {len(filtered_data)} registros totales")
                else:
                    st.info("📋 No hay datos para mostrar vista previa")
        
        with tab4:
            st.header("🗄️ Guardar en Base de Datos")
            
            db_type = st.selectbox(
                "Seleccionar tipo de base de datos:",
                ["SQLite (Local)", "MySQL (Remoto/Local)", "PostgreSQL (Remoto/Local)"],
                help="SQLite es más fácil para comenzar, MySQL y PostgreSQL para producción"
            )
            
            if db_type == "SQLite (Local)":
                st.subheader("💾 Configuración SQLite")
                db_file = st.text_input(
                    "Nombre del archivo de base de datos:", 
                    value="news_database.db",
                    help="Se creará automáticamente si no existe"
                )
                
                if st.button("💾 Guardar en SQLite", type="primary"):
                    if not filtered_data.empty:
                        try:
                            db_manager = DatabaseManager("sqlite", db_path=db_file)
                            if db_manager.save_articles_bulk(filtered_data):
                                st.success(f"✅ {len(filtered_data)} artículos guardados exitosamente en {db_file}")
                                st.info(f"📍 Ubicación: {os.path.abspath(db_file)}")
                            else:
                                st.error("❌ Error guardando los datos")
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
                    else:
                        st.warning("⚠️ No hay datos para guardar")
            
            elif db_type == "MySQL (Remoto/Local)":
                            if not MYSQL_AVAILABLE:
                                st.error("❌ MySQL connector no disponible. Instala con: `pip install mysql-connector-python`")
                            else:
                                st.subheader("🐬 Configuración MySQL")
        
                                col1, col2 = st.columns(2)
                            with col1:
                                mysql_host = st.text_input("Host:", value="localhost", help="IP o dominio del servidor MySQL")
                                mysql_user = st.text_input("Usuario:", help="Usuario de la base de datos")
                                mysql_password = st.text_input("Contraseña:", type="password", help="Déjalo vacío si tu MySQL no tiene password")
        
                            with col2:
                                mysql_database = st.text_input("Nombre de BD:", help="Base de datos donde guardar")
                                mysql_port = st.number_input("Puerto:", value=3306, min_value=1, max_value=65535)
                            
                            # Botón para probar conexión
                            if st.button("🔍 Probar Conexión MySQL", type="secondary"):
                                if mysql_host and mysql_user and mysql_database:
                                    try:
                                        with st.spinner("🔄 Probando conexión..."):
                                            if mysql_password:
                                                test_manager = DatabaseManager(
                                                    "mysql",
                                                    host=mysql_host,
                                                    user=mysql_user,
                                                    password=mysql_password,
                                                    database=mysql_database,
                                                    port=mysql_port
                                                )
                                            else:
                                                test_manager = DatabaseManager(
                                                    "mysql",
                                                    host=mysql_host,
                                                    user=mysql_user,
                                                    password="",
                                                    database=mysql_database,
                                                    port=mysql_port
                                                )
                                        st.success("✅ Conexión exitosa a MySQL!")
                                    except Exception as e:
                                        error_msg = str(e)
                                        if "Access denied" in error_msg:
                                            st.error("❌ Error de autenticación. Prueba:")
                                            st.error("• Dejar contraseña vacía")
                                            st.error("• Usar usuario diferente")
                                        else:
                                            st.error(f"❌ Error de conexión: {e}")
                                else:
                                    st.warning("⚠️ Completa Host, Usuario y Base de datos")
        
                            if st.button("💾 Guardar en MySQL", type="primary"):
                            # 👉 Validamos solo host, user y database (password opcional)
                                if mysql_host and mysql_user and mysql_database:
                                    if not filtered_data.empty:
                                        try:
                                            with st.spinner("🔄 Conectando a MySQL..."):
                                                # Si no hay contraseña, usar conexión sin password
                                                if mysql_password:
                                                    db_manager = DatabaseManager(
                                                        "mysql",
                                                        host=mysql_host,
                                                        user=mysql_user,
                                                        password=mysql_password,
                                                        database=mysql_database,
                                                        port=mysql_port
                                                    )
                                                else:
                                                    # Conexión sin contraseña
                                                    db_manager = DatabaseManager(
                                                        "mysql",
                                                        host=mysql_host,
                                                        user=mysql_user,
                                                        password="",  # Contraseña vacía explícita
                                                        database=mysql_database,
                                                        port=mysql_port
                                                    )
                            
                                            if db_manager.save_articles_bulk(filtered_data):
                                                st.success(f"✅ {len(filtered_data)} artículos guardados en MySQL")
                                            else:
                                                st.error("❌ Error guardando los datos")
                                        except Exception as e:
                                            error_msg = str(e)
                                            if "Access denied" in error_msg:
                                                st.error("❌ Error de autenticación MySQL. Verifica:")
                                                st.error("• Usuario y contraseña correctos")
                                                st.error("• Usuario tiene permisos en la base de datos")
                                                st.error("• Base de datos existe")
                                            elif "Can't connect" in error_msg:
                                                st.error("❌ No se puede conectar a MySQL. Verifica:")
                                                st.error("• MySQL está ejecutándose")
                                                st.error("• Host y puerto correctos")
                                            else:
                                                st.error(f"❌ Error de conexión MySQL: {e}")
                                else:
                                    st.warning("⚠️ No hay datos para guardar")
                            else:
                                st.warning("⚠️ Completa al menos Host, Usuario y Base de datos")

            
            elif db_type == "PostgreSQL (Remoto/Local)":
                if not POSTGRESQL_AVAILABLE:
                    st.error("❌ PostgreSQL connector no disponible. Instala con: `pip install psycopg2-binary`")
                else:
                    st.subheader("🐘 Configuración PostgreSQL")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        pg_host = st.text_input("Host:", value="localhost", help="IP o dominio del servidor PostgreSQL")
                        pg_user = st.text_input("Usuario:", help="Usuario de PostgreSQL")
                        pg_password = st.text_input("Contraseña:", type="password")
                    
                    with col2:
                        pg_database = st.text_input("Nombre de BD:", help="Base de datos donde guardar")
                        pg_port = st.number_input("Puerto:", value=5432, min_value=1, max_value=65535)
                    
                    if st.button("💾 Guardar en PostgreSQL", type="primary"):
                        if all([pg_host, pg_user, pg_password, pg_database]):
                            if not filtered_data.empty:
                                try:
                                    with st.spinner("🔄 Conectando a PostgreSQL..."):
                                        db_manager = DatabaseManager(
                                            "postgresql",
                                            host=pg_host,
                                            user=pg_user,
                                            password=pg_password,
                                            database=pg_database,
                                            port=pg_port
                                        )
                                        
                                        if db_manager.save_articles_bulk(filtered_data):
                                            st.success(f"✅ {len(filtered_data)} artículos guardados en PostgreSQL")
                                        else:
                                            st.error("❌ Error guardando los datos")
                                except Exception as e:
                                    st.error(f"❌ Error de conexión PostgreSQL: {e}")
                            else:
                                st.warning("⚠️ No hay datos para guardar")
                        else:
                            st.warning("⚠️ Completa todos los campos de conexión")
        
        with tab5:
            st.header("⚙️ Configuración y Herramientas")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🗑️ Gestión de Datos")
                
                if st.button("🗑️ Limpiar Todos los Datos", type="secondary"):
                    st.session_state.scraped_data = pd.DataFrame()
                    st.success("✅ Todos los datos han sido eliminados")
                    st.rerun()
                
                st.markdown("---")
                
                st.subheader("📊 Información del Sistema")
                st.write(f"**Total de artículos en memoria:** {len(st.session_state.scraped_data)}")
                st.write(f"**Sitios web únicos:** {st.session_state.scraped_data['newspaper'].nunique() if not st.session_state.scraped_data.empty else 0}")
                st.write(f"**Categorías únicas:** {st.session_state.scraped_data['category'].nunique() if not st.session_state.scraped_data.empty else 0}")
                
            with col2:
                st.subheader("🔧 Estado de Selenium")
                
                if hasattr(st.session_state.scraper, 'selenium_manager') and st.session_state.scraper.selenium_manager:
                    st.success("✅ Selenium WebDriver activo")
                    
                    if st.button("🔄 Reiniciar WebDriver"):
                        st.session_state.scraper.close()
                        st.session_state.scraper.selenium_manager = SeleniumManager()
                        st.success("✅ WebDriver reiniciado")
                        st.rerun()
                else:
                    st.info("💤 Selenium WebDriver no inicializado")
                
                st.markdown("---")
                
                st.subheader("🆘 Solución de Problemas")
                with st.expander("❓ Problemas Comunes"):
                    st.markdown("""
                    **Si el scraping falla:**
                    - Verifica que la URL sea válida y accesible
                    - Algunos sitios requieren más tiempo de carga
                    - Intenta con el navegador visible (desmarcar headless)
                    
                    **Si no encuentra artículos:**
                    - El sitio puede tener una estructura diferente
                    - Prueba con el modo "Artículo Individual" primero
                    - Algunos sitios bloquean bots automáticos
                    
                    **Para mejor rendimiento:**
                    - Usa modo headless (navegador oculto)
                    - Limita el número de artículos en extracción múltiple
                    - Cierra y reinicia el WebDriver ocasionalmente
                    """)
        
        # Botón global para cerrar Selenium
        st.sidebar.markdown("---")
        if st.sidebar.button("🔒 Cerrar WebDriver", help="Liberar recursos de Selenium"):
            if hasattr(st.session_state.scraper, 'selenium_manager'):
                st.session_state.scraper.close()
                st.session_state.scraper.selenium_manager = None
                st.sidebar.success("✅ WebDriver cerrado correctamente")
    
    else:
        # Página de bienvenida
        st.markdown("""
        ## 🎯 ¿Qué hace esta herramienta?
        
        Este **Web Scraper Universal** puede extraer contenido de **cualquier sitio web**, 
        incluso aquellos que usan JavaScript y contenido dinámico.
        
        ### ✨ Características principales:
        
        - 🕷️ **Selenium integrado**: Funciona con sitios web complejos
        - 📄 **Extracción inteligente**: Títulos, fechas, autores, contenido
        - 🔄 **Extracción múltiple**: Encuentra múltiples artículos de una sección  
        - 📊 **Análisis visual**: Gráficos interactivos de los datos
        - 💾 **Múltiples exportaciones**: Excel, CSV, JSON
        - 🗄️ **Base de datos**: SQLite, MySQL, PostgreSQL
        
        ### 🚀 ¿Cómo empezar?
        
        1. **Ingresa una URL** en el sidebar (puede ser una noticia específica o una sección)
        2. **Selecciona el modo** de extracción:
           - 📄 **Individual**: Una sola página
           - 🕷️ **Automático**: Busca múltiples artículos
        3. **Personaliza** la categoría si lo deseas
        4. **Presiona "Iniciar Extracción"** y espera los resultados
        5. **Explora** los datos en las diferentes pestañas
        6. **Exporta** o **guarda** según necesites
        
        ### 📋 Ejemplos de URLs que puedes probar:
        
        ```
        https://elcomercio.pe/politica/
        https://gestion.pe/economia/
        https://rpp.pe/peru/
        https://larepublica.pe/deportes/
        https://elmundo.es/deportes.html
        ```
        
        ### 🔧 Ventajas de usar Selenium:
        
        - ✅ **Funciona con JavaScript**: Sitios modernos y dinámicos
        - ✅ **Contenido completo**: Ve lo mismo que un usuario real
        - ✅ **Anti-detección**: Simula comportamiento humano
        - ✅ **Versatilidad**: Compatible con cualquier sitio web
        
        ---
        
        💡 **Tip**: Comienza con una URL específica en modo "Artículo Individual" 
        para probar si el sitio funciona correctamente.
        """)
        
        # Información adicional en columnas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            ### 🎯 Casos de Uso
            - 📰 Monitoreo de noticias
            - 🔍 Investigación de mercado  
            - 📊 Análisis de contenido
            - 🏢 Inteligencia competitiva
            - 📈 Tendencias y análisis
            """)
        
        with col2:
            st.markdown("""
            ### 💾 Formatos Soportados
            - 📗 **Excel** (formato profesional)
            - 📄 **CSV** (análisis de datos)
            - 📋 **JSON** (desarrollo web)
            - 🗄️ **SQLite** (local)
            - 🐬 **MySQL** (servidor)
            - 🐘 **PostgreSQL** (servidor)
            """)
        
        with col3:
            st.markdown("""
            ### 🛡️ Características Avanzadas
            - 🤖 **Anti-detección** automática
            - ⏱️ **Timeouts** configurables
            - 🔄 **Reintentos** automáticos
            - 📱 **Responsive** design
            - 🎨 **Interfaz** intuitiva
            - 🚀 **Alto rendimiento**
            """)

# Agregar import faltante
import os

def display_hybrid_results(articles, images):
    """Mostrar resultados del crawler híbrido"""
    st.subheader("🚀 Resultados del Crawler Híbrido")
    
    # Métricas generales
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Artículos Encontrados", len(articles))
    
    with col2:
        st.metric("Imágenes Descargadas", len(images))
    
    with col3:
        avg_score = sum(article.get('relevance_score', 0) for article in articles) / len(articles) if articles else 0
        st.metric("Score Promedio", f"{avg_score:.1f}")
    
    # Lista de artículos
    st.subheader("📰 Artículos Encontrados")
    
    for i, article in enumerate(articles[:10]):  # Mostrar solo los primeros 10
        with st.expander(f"{i+1}. {article.get('title', 'Sin título')[:80]}..."):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**URL:** {article.get('url', 'N/A')}")
                st.write(f"**Elemento:** {article.get('element', 'N/A')}")
                st.write(f"**Clase:** {article.get('className', 'N/A')}")
            
            with col2:
                st.metric("Relevancia", article.get('relevance_score', 0))
    
    # Imágenes descargadas
    if images:
        st.subheader("🖼️ Imágenes Descargadas")
        
        # Mostrar información de las imágenes
        image_data = []
        for img in images[:20]:  # Mostrar solo las primeras 20
            image_data.append({
                'Archivo': img.get('filename', 'N/A'),
                'Tamaño': f"{img.get('width', 0)}x{img.get('height', 0)}",
                'Formato': img.get('format', 'N/A'),
                'Tamaño (KB)': f"{img.get('size_bytes', 0) / 1024:.1f}",
                'Score': img.get('relevance_score', 0)
            })
        
        if image_data:
            df_images = pd.DataFrame(image_data)
            st.dataframe(df_images, use_container_width=True)
        
        # Mostrar algunas imágenes
        st.subheader("🖼️ Vista Previa de Imágenes")
        cols = st.columns(4)
        
        for i, img in enumerate(images[:8]):  # Mostrar solo las primeras 8
            with cols[i % 4]:
                try:
                    if img.get('local_path') and os.path.exists(img['local_path']):
                        st.image(img['local_path'], caption=img.get('filename', ''), use_container_width=True)
                except Exception:
                    # Silenciar errores de imágenes - no mostrar nada si no se puede cargar
                    pass

if __name__ == "__main__":
    main()