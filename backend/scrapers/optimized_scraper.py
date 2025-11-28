#!/usr/bin/env python3
"""
Scraper Ultra-Optimizado para 2000+ Artículos
- Paralelismo con ThreadPoolExecutor
- Selenium solo cuando es necesario
- Cache inteligente
- Extracción precisa de campos
- Descarga optimizada de imágenes
"""

import requests
import time
import json
import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
from pathlib import Path
import re
from dataclasses import dataclass
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime, timedelta
import threading
from queue import Queue
import os
from PIL import Image

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImageManager:
    """Gestor especializado para extracción y descarga de imágenes"""
    def __init__(self, base_dir: str = "scraped_images"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    
    def extract_images_from_soup(self, soup: BeautifulSoup, url: str, max_images: int = 3) -> List[Dict]:
        """Extraer imágenes del artículo"""
        if not soup:
            return []
        
        images = []
        base_domain = urlparse(url).netloc
        
        # Selectores para imágenes
        img_selectors = [
            'img[src*=".jpg"]',
            'img[src*=".jpeg"]', 
            'img[src*=".png"]',
            'img[src*=".gif"]',
            'img[src*=".webp"]',
            'img[data-src*=".jpg"]',
            'img[data-src*=".jpeg"]',
            'img[data-src*=".png"]',
            'img[data-src*=".gif"]',
            'img[data-src*=".webp"]'
        ]
        
        for selector in img_selectors:
            for img in soup.select(selector):
                if len(images) >= max_images:
                    break
                    
                img_url = img.get('src') or img.get('data-src')
                if not img_url:
                    continue
                
                # Convertir URL relativa a absoluta
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif img_url.startswith('/'):
                    img_url = f"https://{base_domain}{img_url}"
                elif not img_url.startswith('http'):
                    img_url = urljoin(url, img_url)
                
                # Validar que sea una imagen real
                if self._is_valid_image_url(img_url):
                    images.append({
                        'url': img_url,
                        'alt': img.get('alt', ''),
                        'title': img.get('title', ''),
                        'local_path': None
                    })
        
        return images[:max_images]
    
    def _is_valid_image_url(self, url: str) -> bool:
        """Validar si la URL es una imagen válida"""
        try:
            parsed = urlparse(url)
            path = parsed.path.lower()
            return any(path.endswith(ext) for ext in self.supported_formats)
        except:
            return False
    
    def download_image(self, img_data: Dict) -> Optional[str]:
        """Descargar imagen y retornar ruta local"""
        try:
            response = requests.get(img_data['url'], timeout=10, stream=True)
            response.raise_for_status()
            
            # Generar nombre único
            url_hash = hashlib.md5(img_data['url'].encode()).hexdigest()[:8]
            ext = Path(urlparse(img_data['url']).path).suffix or '.jpg'
            filename = f"{url_hash}{ext}"
            local_path = self.base_dir / filename
            
            # Descargar y guardar
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Validar que sea una imagen real
            try:
                with Image.open(local_path) as img:
                    img.verify()
                img_data['local_path'] = str(local_path)
                logger.info(f"✅ Imagen descargada: {filename}")
                return str(local_path)
            except Exception:
                local_path.unlink(missing_ok=True)
                return None
                
        except Exception as e:
            logger.warning(f"Error descargando imagen {img_data['url']}: {e}")
            return None
    
    def get_image_info(self, local_path: str) -> Dict:
        """Obtener información de la imagen"""
        try:
            with Image.open(local_path) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'size_bytes': Path(local_path).stat().st_size
                }
        except Exception:
            return {}
    
    def cleanup_old_images(self, days: int = 7):
        """Limpiar imágenes antiguas"""
        try:
            cutoff = datetime.now() - timedelta(days=days)
            for img_file in self.base_dir.glob('*'):
                if img_file.is_file() and datetime.fromtimestamp(img_file.stat().st_mtime) < cutoff:
                    img_file.unlink()
        except Exception as e:
            logger.warning(f"Error limpiando imágenes: {e}")

    def extract_main_image(self, soup: BeautifulSoup, page_url: str) -> Optional[Dict]:
        """Detectar la imagen principal del artículo usando metadatos y selectores hero."""
        if not soup:
            return None

        base_domain = urlparse(page_url).netloc

        # 1) Metadatos OG/Twitter
        meta_props = [
            ('meta[property="og:image"]', 'content'),
            ('meta[name="og:image"]', 'content'),
            ('meta[name="twitter:image"]', 'content'),
            ('meta[name="twitter:image:src"]', 'content'),
        ]
        for selector, attr in meta_props:
            tag = soup.select_one(selector)
            if tag and tag.get(attr):
                url = tag.get(attr)
                if url.startswith('//'):
                    url = 'https:' + url
                elif url.startswith('/'):
                    url = f"https://{base_domain}{url}"
                elif not url.startswith('http'):
                    url = urljoin(page_url, url)
                if self._is_valid_image_url(url):
                    return {'url': url, 'alt': '', 'title': 'og/twitter', 'local_path': None}

        # 2) JSON-LD NewsArticle
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string or '{}')
            except Exception:
                continue
            candidates = []
            if isinstance(data, dict):
                candidates.append(data)
            elif isinstance(data, list):
                candidates.extend([d for d in data if isinstance(d, dict)])
            for d in candidates:
                if d.get('@type') in ('NewsArticle', 'Article'):
                    img = d.get('image')
                    img_url = None
                    if isinstance(img, str):
                        img_url = img
                    elif isinstance(img, dict):
                        img_url = img.get('url')
                    elif isinstance(img, list) and img:
                        first = img[0]
                        if isinstance(first, str):
                            img_url = first
                        elif isinstance(first, dict):
                            img_url = first.get('url')
                    if img_url:
                        if img_url.startswith('//'):
                            img_url = 'https:' + img_url
                        elif img_url.startswith('/'):
                            img_url = f"https://{base_domain}{img_url}"
                        elif not img_url.startswith('http'):
                            img_url = urljoin(page_url, img_url)
                        if self._is_valid_image_url(img_url):
                            return {'url': img_url, 'alt': '', 'title': 'json-ld', 'local_path': None}

        # 3) Selectores hero/cover o primer img en contenido
        hero_selectors = [
            'figure.article-hero img', '.hero img', '.cover img', '.lead img', '.main-image img',
            'article img', '.post-content img', '.entry-content img'
        ]
        for selector in hero_selectors:
            img = soup.select_one(selector)
            if not img:
                continue
            url = img.get('src') or img.get('data-src')
            if not url:
                continue
            if url.startswith('//'):
                url = 'https:' + url
            elif url.startswith('/'):
                url = f"https://{base_domain}{url}"
            elif not url.startswith('http'):
                url = urljoin(page_url, url)
            low = url.lower()
            if any(bad in low for bad in ['logo', 'icon', 'avatar', 'placeholder', 'sprite', 'w-community']):
                continue
            if self._is_valid_image_url(url):
                return {'url': url, 'alt': img.get('alt', ''), 'title': img.get('title', ''), 'local_path': None}

        return None

@dataclass
class ArticleData:
    """Estructura de datos para un artículo"""
    title: str = ""
    content: str = ""
    summary: str = ""
    author: str = ""
    date: str = ""
    category: str = ""
    newspaper: str = ""
    url: str = ""
    images_found: int = 0
    images_downloaded: int = 0
    images_data: str = "[]"
    scraped_at: str = ""
    article_id: str = ""

class SmartScraper:
    """Scraper inteligente que usa requests por defecto y Selenium solo cuando es necesario"""
    
    def __init__(self, max_workers: int = 20, cache_days: int = 7):
        self.max_workers = max_workers
        self.cache_days = cache_days
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.cache_db = "scraper_cache.db"
        self.init_cache()
        self.selenium_driver = None
        self.selenium_lock = threading.Lock()
        self.image_manager = ImageManager()
        
    def init_cache(self):
        """Inicializar base de datos de cache"""
        conn = sqlite3.connect(self.cache_db)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                url TEXT PRIMARY KEY,
                content TEXT,
                timestamp DATETIME,
                success BOOLEAN
            )
        ''')
        conn.commit()
        conn.close()
    
    def get_cached_content(self, url: str) -> Optional[str]:
        """Obtener contenido desde cache"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT content FROM cache WHERE url = ? AND timestamp > ? AND success = 1",
            (url, datetime.now() - timedelta(days=self.cache_days))
        )
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def cache_content(self, url: str, content: str, success: bool = True):
        """Guardar contenido en cache"""
        conn = sqlite3.connect(self.cache_db)
        conn.execute(
            "INSERT OR REPLACE INTO cache (url, content, timestamp, success) VALUES (?, ?, ?, ?)",
            (url, content, datetime.now(), success)
        )
        conn.commit()
        conn.close()
    
    def get_page_content(self, url: str) -> Tuple[Optional[BeautifulSoup], str]:
        """Obtener contenido de página con fallback inteligente"""
        # 1. Intentar cache primero
        cached_content = self.get_cached_content(url)
        if cached_content:
            logger.info(f"📦 Cache hit: {url}")
            return BeautifulSoup(cached_content, 'html.parser'), "cache"
        
        # 2. Intentar con requests (rápido)
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Verificar si el contenido es válido
            if self.is_valid_content(soup, url):
                self.cache_content(url, response.text, True)
                logger.info(f"✅ Requests success: {url}")
                return soup, "requests"
            else:
                logger.warning(f"⚠️ Requests content invalid: {url}")
                
        except Exception as e:
            logger.warning(f"⚠️ Requests failed: {url} - {e}")
        
        # 3. Fallback a Selenium solo si es necesario
        try:
            soup = self.get_page_with_selenium(url)
            if soup:
                self.cache_content(url, str(soup), True)
                logger.info(f"🔧 Selenium fallback: {url}")
                return soup, "selenium"
        except Exception as e:
            logger.error(f"❌ Selenium failed: {url} - {e}")
            self.cache_content(url, "", False)
        
        return None, "failed"
    
    def is_valid_content(self, soup: BeautifulSoup, url: str) -> bool:
        """Verificar si el contenido es válido (no es página de error o bloqueo)"""
        if not soup:
            return False
        
        # Verificar elementos que indican contenido válido
        title = soup.find('title')
        if title and any(keyword in title.get_text().lower() for keyword in ['error', 'not found', 'blocked', 'access denied']):
            return False
        
        # Verificar si hay contenido principal
        main_content = soup.find(['article', 'main', 'div'], class_=re.compile(r'(content|article|main|story)', re.I))
        if main_content and len(main_content.get_text().strip()) > 100:
            return True
        
        # Verificar si hay al menos un párrafo
        paragraphs = soup.find_all('p')
        if paragraphs and len(' '.join([p.get_text() for p in paragraphs[:3]])) > 100:
            return True
        
        return False
    
    def get_page_with_selenium(self, url: str) -> Optional[BeautifulSoup]:
        """Obtener página con Selenium (solo cuando es necesario)"""
        with self.selenium_lock:
            if not self.selenium_driver:
                self.init_selenium()
            
            if not self.selenium_driver:
                return None
            
            try:
                self.selenium_driver.get(url)
                time.sleep(2)  # Espera mínima
                html = self.selenium_driver.page_source
                return BeautifulSoup(html, 'html.parser')
            except Exception as e:
                logger.error(f"Selenium error: {e}")
                return None
    
    def init_selenium(self):
        """Inicializar Selenium solo cuando sea necesario"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service
            
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            
            service = Service(ChromeDriverManager().install())
            self.selenium_driver = webdriver.Chrome(service=service, options=options)
            logger.info("🔧 Selenium inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando Selenium: {e}")
            self.selenium_driver = None
    
    def extract_article_links(self, soup: BeautifulSoup, base_url: str, max_links: int = 2000) -> List[str]:
        """Extraer enlaces de artículos de forma dinámica para múltiples sitios."""
        if not soup:
            return []

        links: set[str] = set()
        parsed_base = urlparse(base_url)
        base_domain = parsed_base.netloc

        # 0) Si la página ya es artículo (tiene h1 fuerte), incluirla
        h1 = soup.select_one('h1')
        if h1 and len(h1.get_text(strip=True)) > 10:
            links.add(base_url)

        # 1) Estrategia mejorada: múltiples enfoques para encontrar artículos
        
        # 1.1) Selectores específicos para artículos
        article_selectors = [
            'article a', '.article a', '.news-item a', '.post a', '.story a',
            '.entry a', '.item a', '.card a', '.content a', '.headline a',
            '.title a', '.summary a', '.excerpt a', '.teaser a', '.preview a',
            'h1 a', 'h2 a', 'h3 a', 'h4 a', '.article-list a', '.news-list a',
            '.post-list a', '.story-list a', '.grid a', '.masonry a', '.feed a',
            'a[class*="article"]', 'a[class*="news"]', 'a[class*="post"]',
            'a[class*="story"]', 'a[class*="title"]', 'a[class*="headline"]'
        ]
        
        for selector in article_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    href = element.get('href')
                    if href:
                        full_url = urljoin(base_url, href)
                        if self._is_valid_article_url(full_url, base_domain):
                            links.add(full_url)
                            if len(links) >= max_links:
                                break
            except Exception:
                continue
            if len(links) >= max_links:
                break
        
        # 1.2) Heurística general mejorada: todos los <a href> del mismo dominio
        if len(links) < max_links // 2:  # Solo si no encontramos suficientes
            for a in soup.find_all('a', href=True):
                href = a['href'].strip()
                if not href or href.startswith(('javascript:', 'mailto:', 'tel:')):
                    continue
                full_url = urljoin(base_url, href)
                p = urlparse(full_url)
                if p.netloc and p.netloc != base_domain:
                    continue
                
                if self._is_valid_article_url(full_url, base_domain):
                    links.add(full_url)
                    if len(links) >= max_links:
                        break

        # 2) Fallback: JSON-LD itemListElement (listados)
        if not links:
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    data = json.loads(script.string or '{}')
                except Exception:
                    continue
                blocks = data if isinstance(data, list) else [data]
                for b in blocks:
                    items = b.get('itemListElement') if isinstance(b, dict) else None
                    if not items:
                        continue
                    for it in items:
                        url = (it.get('item') or {}).get('url') if isinstance(it, dict) else None
                        if not url:
                            continue
                        full_url = urljoin(base_url, url)
                        p = urlparse(full_url)
                        if p.netloc and p.netloc != base_domain:
                            continue
                        links.add(full_url)
                        if len(links) >= max_links:
                            break
                    if len(links) >= max_links:
                        break
                if len(links) >= max_links:
                    break

        # 3) Normalizar/limitar
        norm_links = []
        seen = set()
        for u in links:
            u = u.split('#')[0]
            if u not in seen:
                seen.add(u)
                norm_links.append(u)
        return norm_links[:max_links]
    
    def _is_valid_article_url(self, url: str, base_domain: str) -> bool:
        """Validar si una URL es probablemente un artículo"""
        try:
            p = urlparse(url)
            if p.netloc != base_domain:
                return False
            
            low = url.lower()
            path = p.path or '/'
            
            # Excluir URLs obviamente no artículos
            exclude_patterns = [
                '/tag/', '/tags/', '/categoria/', '/category/', '/author/', '/autor/', '/etiqueta/',
                '/page/', '/search', '/wp-', '/seccion/', '/section/', '/archivo/', '/archive/',
                '/buscar/', '/contacto/', '/contact/', '/sobre/', '/about/', '/politica/', '/policy/',
                '/terminos/', '/terms/', '/privacidad/', '/privacy/', '/suscripcion/', '/subscription/',
                '/newsletter/', '/newsletters/', '/rss/', '/feed/', '/sitemap/', '/mapa/',
                '/inicio/', '/home/', '/index/', '/login/', '/register/', '/registro/',
                '/api/', '/ajax/', '/json/', '/xml/', '/admin/', '/dashboard/',
                'facebook', 'twitter', 'instagram', 'youtube', 'linkedin', 'whatsapp', 'telegram',
                '/404', '/error', '/not-found', '#', 'javascript:', 'mailto:', 'tel:'
            ]
            
            if any(pattern in low for pattern in exclude_patterns):
                return False
            
            # Excluir archivos
            if any(low.endswith(ext) for ext in ['.pdf', '.doc', '.docx', '.zip', '.rar', '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg', '.mp4', '.mp3']):
                return False
            
            # URLs muy cortas probablemente no son artículos
            if len(url) < 15:
                return False
            
            # Patrones que indican artículo (más permisivos)
            article_patterns = [
                # Patrones de fecha
                r'/\d{4}/\d{2}/\d{2}/',  # 2024/01/15
                r'/\d{4}/\d{2}/',        # 2024/01
                r'/\d{4}/',              # 2024
                
                # Patrones de contenido
                r'/noticia/', r'/articulo/', r'/nota/', r'/post/', r'/news/', r'/story/',
                r'/article/', r'/entry/', r'/blog/', r'/report/', r'/press/',
                
                # Patrones de ID
                r'/noticia-\d+', r'/articulo-\d+', r'/post-\d+', r'/news-\d+',
                
                # Patrones de slug (palabras con guiones) - más permisivos
                r'[a-z]+-[a-z]+',  # palabra-palabra (mínimo 2 palabras)
                r'[a-z]+-[a-z]+-[a-z]+',  # 3 palabras
                r'[a-z]+-[a-z]+-[a-z]+-[a-z]+',  # 4 palabras
                
                # Patrones específicos de sitios
                r'/\d{4}/\d{2}/\d{2}/[a-z-]+',  # fecha + slug
                r'/[a-z-]+/\d{4}/\d{2}/\d{2}',  # slug + fecha
            ]
            
            # Verificar si tiene patrón de artículo
            has_article_pattern = any(re.search(pattern, low) for pattern in article_patterns)
            
            # Si tiene patrón de artículo, es válido
            if has_article_pattern:
                return True
            
            # Si no tiene patrón específico, verificar otros criterios más permisivos
            path_segments = [seg for seg in path.split('/') if seg]
            
            # Debe tener al menos 1 segmento (más permisivo)
            if len(path_segments) < 1:
                return False
            
            # El último segmento debe tener al menos 5 caracteres (más permisivo)
            last_segment = path_segments[-1]
            if len(last_segment) >= 5:
                # Si tiene guiones, probablemente es un slug de artículo
                if '-' in last_segment:
                    return True
                # Si tiene números, probablemente es un ID de artículo
                if re.search(r'\d+', last_segment):
                    return True
            
            # Si tiene números en cualquier parte del path, probablemente es un artículo
            if re.search(r'\d+', path):
                return True
            
            # Si el path tiene más de 2 segmentos, probablemente es un artículo
            if len(path_segments) >= 2:
                return True
            
            return False
            
        except Exception:
            return False
    
    def extract_images_from_soup(self, soup: BeautifulSoup, url: str, max_images: int = 3) -> List[Dict]:
        """Extraer imágenes del artículo"""
        if not soup:
            return []
        
        images = []
        base_domain = urlparse(url).netloc
        
        # Selectores para imágenes
        img_selectors = [
            'img[src*=".jpg"]',
            'img[src*=".jpeg"]', 
            'img[src*=".png"]',
            'img[src*=".gif"]',
            'img[src*=".webp"]',
            'img[data-src*=".jpg"]',
            'img[data-src*=".jpeg"]',
            'img[data-src*=".png"]',
            'img[data-src*=".gif"]',
            'img[data-src*=".webp"]'
        ]
        
        for selector in img_selectors:
            img_elements = soup.select(selector)
            for img in img_elements:
                if len(images) >= max_images:
                    break
                    
                img_url = img.get('src') or img.get('data-src')
                if img_url:
                    full_img_url = urljoin(url, img_url)
                    parsed_img_url = urlparse(full_img_url)
                    
                    # Filtrar imágenes válidas
                    if (parsed_img_url.netloc == base_domain and
                        not any(skip in full_img_url.lower() for skip in ['logo', 'icon', 'avatar', 'default'])):
                        
                        # Descargar imagen usando ImageManager
                        try:
                            img_data = {
                                'url': full_img_url,
                                'alt': img.get('alt', ''),
                                'title': img.get('title', ''),
                                'local_path': None
                            }
                            local_path = self.image_manager.download_image(img_data)
                            if local_path:
                                img_data['local_path'] = local_path
                                images.append(img_data)
                        except Exception as e:
                            logger.warning(f"Error descargando imagen {full_img_url}: {e}")
            
            if len(images) >= max_images:
                break
        
        return images
    
    def extract_article_data(self, soup: BeautifulSoup, url: str) -> ArticleData:
        """Extraer datos del artículo con precisión mejorada"""
        article = ArticleData()
        article.url = url
        article.article_id = hashlib.md5(url.encode()).hexdigest()[:12]
        article.scraped_at = datetime.now().isoformat()
        article.newspaper = self.extract_newspaper_name(url)
        
        # Extraer título con múltiples selectores
        title_selectors = [
            'h1.title',
            'h1.headline',
            'h1.entry-title',
            'h1.post-title',
            'h1.article-title',
            'h1',
            '.title h1',
            '.headline h1',
            '.entry-title',
            '.post-title',
            '.article-title',
            'title'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem and title_elem.get_text().strip():
                article.title = title_elem.get_text().strip()
                break
        
        # Extraer contenido principal
        content_selectors = [
            '.article-content',
            '.entry-content',
            '.post-content',
            '.article-body',
            '.story-content',
            '.content',
            'article',
            '.article',
            '.noticia-content',
            '.noticia-body'
        ]
        
        content_text = ""
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Remover elementos no deseados
                for unwanted in content_elem.select('script, style, .ad, .advertisement, .social-share, .comments, .related, .sidebar'):
                    unwanted.decompose()
                
                # Extraer texto manteniendo párrafos
                paragraphs = []
                for p in content_elem.find_all(['p', 'div'], recursive=True):
                    text = p.get_text().strip()
                    if text and len(text) > 20:  # Párrafos con contenido sustancial
                        paragraphs.append(text)
                
                if paragraphs:
                    content_text = '\n\n'.join(paragraphs)
                    if len(content_text) > 200:  # Contenido suficientemente largo
                        break
        
        # Si no encontramos contenido estructurado, usar todo el texto
        if not content_text or len(content_text) < 100:
            body = soup.find('body')
            if body:
                for unwanted in body.select('script, style, .ad, .advertisement, .social-share, .comments, .related, .sidebar, nav, header, footer'):
                    unwanted.decompose()
                content_text = body.get_text().strip()
        
        article.content = content_text
        
        # Extraer resumen
        summary_selectors = [
            '.summary',
            '.excerpt',
            '.lead',
            '.intro',
            '.article-summary',
            '.noticia-summary',
            'meta[name="description"]'
        ]
        
        for selector in summary_selectors:
            summary_elem = soup.select_one(selector)
            if summary_elem:
                if selector.startswith('meta'):
                    article.summary = summary_elem.get('content', '').strip()
                else:
                    article.summary = summary_elem.get_text().strip()
                break
        
        # Si no hay resumen, crear uno del contenido
        if not article.summary and article.content:
            article.summary = article.content[:300] + "..." if len(article.content) > 300 else article.content
        
        # Extraer autor
        author_selectors = [
            '.author',
            '.byline',
            '.article-author',
            '.post-author',
            '.noticia-author',
            'meta[name="author"]',
            '[rel="author"]'
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                if selector.startswith('meta'):
                    article.author = author_elem.get('content', '').strip()
                else:
                    article.author = author_elem.get_text().strip()
                break
        
        # Extraer fecha
        date_selectors = [
            '.date',
            '.published',
            '.article-date',
            '.post-date',
            '.noticia-date',
            'time',
            'meta[property="article:published_time"]',
            'meta[name="date"]'
        ]
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                if selector.startswith('meta'):
                    article.date = date_elem.get('content', '').strip()
                else:
                    article.date = date_elem.get_text().strip()
                break
        
        # Extraer categoría
        category_selectors = [
            '.category',
            '.section',
            '.tag',
            '.breadcrumb a',
            '.article-category',
            '.noticia-category'
        ]
        
        for selector in category_selectors:
            category_elem = soup.select_one(selector)
            if category_elem:
                article.category = category_elem.get_text().strip()
                break
        
        # Si no hay categoría, extraer de la URL
        if not article.category:
            path_parts = urlparse(url).path.split('/')
            for part in path_parts:
                if part and part not in ['www', 'noticia', 'article', 'news', 'story']:
                    article.category = part.title()
                    break
        
        # Extraer solo imagen principal
        try:
            main_img = self.image_manager.extract_main_image(soup, url)
            if main_img:
                # descargar y validar peso/tamaño mínimo
                local = self.image_manager.download_image(main_img)
                if local:
                    main_img['local_path'] = local
                images = [main_img]
            else:
                images = []
            article.images_found = len(images)
            article.images_downloaded = len([img for img in images if img.get('local_path')])
            article.images_data = json.dumps(images)
        except Exception as e:
            logger.warning(f"Error extrayendo imagen principal de {url}: {e}")
            article.images_found = 0
            article.images_downloaded = 0
            article.images_data = "[]"
        
        return article
    
    def extract_newspaper_name(self, url: str) -> str:
        """Extraer nombre del periódico de la URL"""
        domain = urlparse(url).netloc
        return domain.replace('www.', '').split('.')[0].title()
    
    def process_single_article(self, url: str) -> Optional[ArticleData]:
        """Procesar un solo artículo"""
        try:
            soup, method = self.get_page_content(url)
            if not soup:
                return None
            
            article = self.extract_article_data(soup, url)
            
            # Extraer imágenes si es necesario
            if hasattr(self, 'extract_images') and self.extract_images:
                images_info = self.extract_images_from_soup(soup, url)
                article.images_found = len(images_info)
                # Aquí se puede implementar descarga de imágenes si es necesario
            
            logger.info(f"✅ Artículo procesado: {article.title[:50]}... ({method})")
            return article
            
        except Exception as e:
            logger.error(f"❌ Error procesando {url}: {e}")
            return None
    
    def crawl_and_scrape_parallel(self, base_url: str, max_articles: int = 2000, 
                                 progress_callback=None, extract_images: bool = False) -> List[ArticleData]:
        """Crawlear y extraer artículos en paralelo"""
        logger.info(f"🚀 Iniciando scraping paralelo de {max_articles} artículos")
        
        # 1. Obtener página principal y extraer enlaces
        soup, method = self.get_page_content(base_url)
        if not soup:
            logger.error("❌ No se pudo obtener la página principal")
            return []
        
        article_links = self.extract_article_links(soup, base_url, max_articles)
        logger.info(f"🔍 Encontrados {len(article_links)} enlaces de artículos")
        
        if not article_links:
            return []
        
        # 2. Procesar artículos en paralelo
        articles = []
        self.extract_images = extract_images
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Enviar todas las tareas
            future_to_url = {
                executor.submit(self.process_single_article, url): url 
                for url in article_links
            }
            
            # Procesar resultados conforme se completan
            completed = 0
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    article = future.result()
                    if article:
                        articles.append(article)
                        completed += 1
                        
                        if progress_callback:
                            progress_callback(completed, len(article_links))
                            
                        logger.info(f"📊 Progreso: {completed}/{len(article_links)} artículos procesados")
                        
                except Exception as e:
                    logger.error(f"❌ Error procesando {url}: {e}")
        
        logger.info(f"🎉 Scraping completado: {len(articles)} artículos extraídos")
        return articles
    
    def close(self):
        """Cerrar recursos"""
        if self.selenium_driver:
            self.selenium_driver.quit()
        self.session.close()

# Función de utilidad para convertir a DataFrame
def articles_to_dataframe(articles: List[ArticleData]) -> 'pd.DataFrame':
    """Convertir lista de artículos a DataFrame de pandas"""
    import pandas as pd
    
    data = []
    for article in articles:
        data.append({
            'title': article.title,
            'content': article.content,
            'summary': article.summary,
            'author': article.author,
            'date': article.date,
            'category': article.category,
            'newspaper': article.newspaper,
            'url': article.url,
            'images_found': article.images_found,
            'images_downloaded': article.images_downloaded,
            'images_data': article.images_data,
            'scraped_at': article.scraped_at,
            'article_id': article.article_id
        })
    
    return pd.DataFrame(data)

if __name__ == "__main__":
    # Ejemplo de uso
    scraper = SmartScraper(max_workers=20)
    
    try:
        articles = scraper.crawl_and_scrape_parallel(
            "https://elcomercio.pe/politica/",
            max_articles=100,
            extract_images=False
        )
        
        print(f"✅ Extraídos {len(articles)} artículos")
        for article in articles[:5]:  # Mostrar primeros 5
            print(f"📰 {article.title[:50]}... - {article.newspaper}")
            
    finally:
        scraper.close()
