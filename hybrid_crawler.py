"""
Crawler Híbrido para Extracción Completa de Datos e Imágenes
Combina Selenium, Requests y técnicas especializadas para extraer artículos e imágenes
"""

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

import time
import logging
import hashlib
import os
from pathlib import Path
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Tuple
from PIL import Image
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

logger = logging.getLogger(__name__)

class HybridDataCrawler:
    """Crawler híbrido especializado en extracción completa de datos e imágenes"""
    
    def __init__(self, max_workers: int = 5, headless: bool = True):
        self.max_workers = max_workers
        self.headless = headless
        self.driver = None
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
        self.image_cache = {}
        self.lock = threading.Lock()
        
    def init_selenium(self):
        """Inicializar Selenium WebDriver"""
        if self.driver:
            return
            
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("✅ Selenium WebDriver inicializado para crawler híbrido")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando Selenium: {e}")
            self.driver = None
    
    def crawl_with_selenium(self, url: str, max_images: int = 50) -> List[Dict]:
        """Crawlear usando Selenium para contenido dinámico"""
        self.init_selenium()
        if not self.driver:
            return []
        
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Scroll inteligente para cargar imágenes lazy
            self._smart_scroll_for_images()
            
            # Extraer imágenes usando JavaScript
            images = self._extract_images_with_js(url)
            
            # Filtrar y priorizar imágenes
            filtered_images = self._filter_and_prioritize_images(images, max_images)
            
            logger.info(f"🔍 Selenium: {len(filtered_images)} imágenes encontradas")
            return filtered_images
            
        except Exception as e:
            logger.error(f"❌ Error en crawl Selenium: {e}")
            return []
    
    def crawl_with_selenium_fast(self, url: str, max_images: int = 50) -> List[Dict]:
        """Crawlear usando Selenium para contenido dinámico - VERSIÓN RÁPIDA"""
        self.init_selenium()
        if not self.driver:
            return []
        
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 5).until(  # Timeout más corto
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Scroll rápido para cargar imágenes lazy
            self._fast_scroll_for_images()
            
            # Extraer imágenes usando JavaScript
            images = self._extract_images_with_js(url)
            
            # Filtrar y priorizar imágenes
            filtered_images = self._filter_and_prioritize_images(images, max_images)
            
            logger.info(f"🔍 Selenium Rápido: {len(filtered_images)} imágenes encontradas")
            return filtered_images
            
        except Exception as e:
            logger.error(f"❌ Error en crawl Selenium rápido: {e}")
            return []
    
    def crawl_with_requests(self, url: str, max_images: int = 50) -> List[Dict]:
        """Crawlear usando Requests para contenido estático"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            images = self._extract_images_from_soup(soup, url)
            
            # Filtrar y priorizar imágenes
            filtered_images = self._filter_and_prioritize_images(images, max_images)
            
            logger.info(f"🔍 Requests: {len(filtered_images)} imágenes encontradas")
            return filtered_images
            
        except Exception as e:
            logger.error(f"❌ Error en crawl Requests: {e}")
            return []
    
    def analyze_page_type(self, url: str) -> Dict[str, bool]:
        """Analizar el tipo de página para decidir el mejor método de extracción"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Detectar características de la página
            has_javascript = bool(soup.find('script'))
            has_dynamic_content = bool(soup.find(['div', 'section'], class_=lambda x: x and any(
                keyword in x.lower() for keyword in ['lazy', 'dynamic', 'ajax', 'infinite', 'scroll']
            )))
            has_spa_framework = bool(soup.find('script', string=lambda x: x and any(
                framework in x.lower() for framework in ['react', 'vue', 'angular', 'spa']
            )))
            has_lazy_images = bool(soup.find('img', {'data-src': True}) or soup.find('img', {'data-lazy': True}))
            has_pagination = bool(soup.find(['a', 'button'], string=lambda x: x and any(
                keyword in x.lower() for keyword in ['cargar más', 'ver más', 'load more', 'show more']
            )))
            
            # Detectar si es una página de noticias/artículos
            has_article_structure = bool(soup.find(['article', '.article', '.news-item', '.post', '.entry', '.content']))
            
            # Detectar sitios específicos que pueden necesitar Selenium
            domain = urlparse(url).netloc.lower()
            is_news_site = any(news_keyword in domain for news_keyword in [
                'diario', 'noticia', 'news', 'periodico', 'prensa', 'sinfronteras'
            ])
            
            # Detectar más patrones de contenido dinámico
            has_ajax_links = bool(soup.find('a', href=lambda x: x and 'ajax' in x.lower()))
            has_infinite_scroll = bool(soup.find(['div', 'section'], class_=lambda x: x and any(
                keyword in x.lower() for keyword in ['infinite', 'scroll', 'load-more', 'pagination']
            )))
            
            # Decidir qué método usar - ser más agresivo con Selenium para sitios de noticias
            needs_selenium = (
                has_javascript and (
                    has_dynamic_content or 
                    has_spa_framework or 
                    has_lazy_images or 
                    has_pagination or
                    has_ajax_links or
                    has_infinite_scroll or
                    (is_news_site and has_javascript)  # Usar Selenium para sitios de noticias con JS
                )
            )
            
            analysis = {
                'needs_selenium': needs_selenium,
                'has_javascript': has_javascript,
                'has_dynamic_content': has_dynamic_content,
                'has_spa_framework': has_spa_framework,
                'has_lazy_images': has_lazy_images,
                'has_pagination': has_pagination,
                'has_ajax_links': has_ajax_links,
                'has_infinite_scroll': has_infinite_scroll,
                'is_news_site': is_news_site,
                'has_article_structure': has_article_structure,
                'recommended_method': 'selenium' if needs_selenium else 'requests'
            }
            
            logger.info(f"🔍 Análisis de página: {analysis['recommended_method']} recomendado")
            logger.info(f"   - JavaScript: {has_javascript}, Dinámico: {has_dynamic_content}")
            logger.info(f"   - SPA: {has_spa_framework}, Lazy: {has_lazy_images}, Paginación: {has_pagination}")
            logger.info(f"   - AJAX: {has_ajax_links}, Infinite Scroll: {has_infinite_scroll}, Sitio de Noticias: {is_news_site}")
            
            return analysis
            
        except Exception as e:
            logger.warning(f"⚠️ Error analizando página: {e}")
            # Por defecto, usar Selenium si no se puede analizar
            return {
                'needs_selenium': True,
                'recommended_method': 'selenium'
            }
    
    def hybrid_crawl_articles(self, url: str, max_articles: int = 50) -> List[Dict]:
        """Crawlear híbrido inteligente - analiza la página y decide el mejor método"""
        # Analizar la página primero
        page_analysis = self.analyze_page_type(url)
        
        if page_analysis['recommended_method'] == 'requests':
            # Usar solo Requests si la página es estática
            logger.info("🚀 Usando método Requests (página estática)")
            try:
                articles = self.crawl_articles_with_requests(url, max_articles)
                if articles:
                    logger.info(f"✅ Requests exitoso: {len(articles)} artículos")
                    return articles
            except Exception as e:
                logger.warning(f"⚠️ Requests falló, intentando Selenium: {e}")
        
        # Usar Selenium para páginas dinámicas o si Requests falló
        logger.info("🔧 Usando método Selenium (página dinámica)")
        try:
            articles = self.crawl_articles_with_selenium(url, max_articles)
            if articles:
                logger.info(f"✅ Selenium exitoso: {len(articles)} artículos")
                return articles
        except Exception as e:
            logger.error(f"❌ Selenium falló: {e}")
        
        # Fallback: intentar ambos métodos
        logger.info("🔄 Fallback: intentando ambos métodos")
        all_articles = []
        
        try:
            requests_articles = self.crawl_articles_with_requests(url, max_articles)
            all_articles.extend(requests_articles)
            logger.info(f"📦 Requests fallback: {len(requests_articles)} artículos")
        except Exception as e:
            logger.warning(f"⚠️ Requests fallback falló: {e}")
        
        try:
            selenium_articles = self.crawl_articles_with_selenium_fast(url, max_articles - len(all_articles))
            all_articles.extend(selenium_articles)
            logger.info(f"🔧 Selenium fallback: {len(selenium_articles)} artículos")
        except Exception as e:
            logger.warning(f"⚠️ Selenium fallback falló: {e}")
        
        # Eliminar duplicados y limitar
        unique_articles = self._deduplicate_articles(all_articles)
        final_articles = unique_articles[:max_articles]
        
        logger.info(f"🎯 Total híbrido: {len(final_articles)} artículos únicos")
        return final_articles
    
    def hybrid_crawl_images(self, url: str, max_images: int = 50) -> List[Dict]:
        """Crawlear híbrido inteligente para imágenes - analiza y decide el mejor método"""
        # Analizar la página primero
        page_analysis = self.analyze_page_type(url)
        
        if page_analysis['recommended_method'] == 'requests' and not page_analysis.get('has_lazy_images', False):
            # Usar solo Requests si la página es estática y no tiene lazy loading
            logger.info("🚀 Usando método Requests para imágenes (página estática)")
            try:
                images = self.crawl_with_requests(url, max_images)
                if images:
                    logger.info(f"✅ Requests exitoso: {len(images)} imágenes")
                    return images
            except Exception as e:
                logger.warning(f"⚠️ Requests falló, intentando Selenium: {e}")
        
        # Usar Selenium para páginas con lazy loading o dinámicas
        logger.info("🔧 Usando método Selenium para imágenes (lazy loading detectado)")
        try:
            images = self.crawl_with_selenium(url, max_images)
            if images:
                logger.info(f"✅ Selenium exitoso: {len(images)} imágenes")
                return images
        except Exception as e:
            logger.error(f"❌ Selenium falló: {e}")
        
        # Fallback: intentar ambos métodos
        logger.info("🔄 Fallback: intentando ambos métodos para imágenes")
        all_images = []
        
        try:
            requests_images = self.crawl_with_requests(url, max_images)
            all_images.extend(requests_images)
            logger.info(f"📦 Requests fallback: {len(requests_images)} imágenes")
        except Exception as e:
            logger.warning(f"⚠️ Requests fallback falló: {e}")
        
        try:
            selenium_images = self.crawl_with_selenium_fast(url, max_images - len(all_images))
            all_images.extend(selenium_images)
            logger.info(f"🔧 Selenium fallback: {len(selenium_images)} imágenes")
        except Exception as e:
            logger.warning(f"⚠️ Selenium fallback falló: {e}")
        
        # Eliminar duplicados y limitar
        unique_images = self._deduplicate_images(all_images)
        final_images = unique_images[:max_images]
        
        logger.info(f"🎯 Total híbrido: {len(final_images)} imágenes únicas")
        return final_images
    
    def _smart_scroll_for_images(self):
        """Scroll inteligente para cargar imágenes lazy - MEJORADO"""
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            max_attempts = 10
            images_found = set()
            
            while scroll_attempts < max_attempts:
                # Scroll progresivo en pasos más pequeños
                current_scroll = 0
                scroll_step = 300  # Pasos más pequeños para imágenes
                
                while current_scroll < last_height:
                    self.driver.execute_script(f"window.scrollTo(0, {current_scroll});")
                    time.sleep(0.3)  # Pausa más corta
                    current_scroll += scroll_step
                
                # Scroll final al fondo
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)
                
                # Verificar si hay nuevo contenido
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                # Contar imágenes únicas encontradas
                current_images = self.driver.execute_script("""
                    var images = [];
                    var imgElements = document.querySelectorAll('img');
                    for (var i = 0; i < imgElements.length; i++) {
                        var img = imgElements[i];
                        if (img.src && img.src.startsWith('http') && 
                            img.naturalWidth > 100 && img.naturalHeight > 100) {
                            images.push(img.src);
                        }
                    }
                    return images;
                """)
                
                new_images = set(current_images) - images_found
                images_found.update(current_images)
                
                logger.info(f"🖼️ Scroll {scroll_attempts + 1}: {len(images_found)} imágenes únicas encontradas (+{len(new_images)} nuevas)")
                
                if new_height == last_height and len(new_images) == 0:
                    scroll_attempts += 1
                else:
                    scroll_attempts = 0
                    last_height = new_height
                
                # Si no encontramos nuevas imágenes en 3 intentos consecutivos, parar
                if scroll_attempts >= 3:
                    break
                    
            # Volver al inicio
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.5)
            
            logger.info(f"🎯 Scroll de imágenes completado: {len(images_found)} imágenes únicas detectadas")
            
        except Exception as e:
            logger.warning(f"⚠️ Error en scroll inteligente de imágenes: {e}")
    
    def _fast_scroll_for_images(self):
        """Scroll rápido para cargar imágenes lazy - VERSIÓN OPTIMIZADA"""
        try:
            # Scroll rápido (solo 2 posiciones)
            scroll_positions = [0.5, 1.0]  # Solo 50% y 100%
            
            for position in scroll_positions:
                # Scroll a posición
                self.driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {position});")
                time.sleep(0.5)  # Menos tiempo de espera
            
            # Scroll final al inicio
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.2)
            
        except Exception as e:
            logger.warning(f"⚠️ Error en scroll rápido: {e}")
    
    def _extract_images_with_js(self, base_url: str) -> List[Dict]:
        """Extraer imágenes usando JavaScript"""
        try:
            js_code = """
            var images = [];
            var allImages = document.querySelectorAll('img');
            
            for (var i = 0; i < allImages.length; i++) {
                var img = allImages[i];
                var src = img.src || img.getAttribute('data-src') || img.getAttribute('data-lazy-src');
                
                if (src && src.startsWith('http')) {
                    images.push({
                        url: src,
                        alt: img.alt || '',
                        title: img.title || '',
                        width: img.naturalWidth || img.width || 0,
                        height: img.naturalHeight || img.height || 0,
                        className: img.className || '',
                        id: img.id || ''
                    });
                }
            }
            
            return images;
            """
            
            js_images = self.driver.execute_script(js_code)
            return js_images or []
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo imágenes con JS: {e}")
            return []
    
    def _extract_images_from_soup(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extraer imágenes desde BeautifulSoup"""
        images = []
        
        try:
            img_tags = soup.find_all('img')
            
            for img in img_tags:
                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                if not src:
                    continue
                
                full_url = urljoin(base_url, src)
                
                image_info = {
                    'url': full_url,
                    'alt': img.get('alt', ''),
                    'title': img.get('title', ''),
                    'width': img.get('width', 0),
                    'height': img.get('height', 0),
                    'className': ' '.join(img.get('class', [])),
                    'id': img.get('id', '')
                }
                images.append(image_info)
                
        except Exception as e:
            logger.error(f"❌ Error extrayendo imágenes del soup: {e}")
        
        return images
    
    def _filter_and_prioritize_images(self, images: List[Dict], max_images: int) -> List[Dict]:
        """Filtrar y priorizar imágenes por relevancia"""
        if not images:
            return []
        
        # Filtrar imágenes válidas
        valid_images = []
        for img in images:
            if self._is_valid_image(img):
                # Calcular score de relevancia
                score = self._calculate_image_score(img)
                img['relevance_score'] = score
                valid_images.append(img)
        
        # Ordenar por relevancia
        valid_images.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return valid_images[:max_images]
    
    def _is_valid_image(self, img: Dict) -> bool:
        """Verificar si una imagen es válida"""
        try:
            url = img.get('url', '')
            if not url or len(url) < 10:
                return False
            
            # Verificar extensión
            parsed_url = urlparse(url)
            path = parsed_url.path.lower()
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
            
            has_valid_extension = any(path.endswith(ext) for ext in valid_extensions)
            has_image_pattern = any(pattern in url.lower() for pattern in [
                '/image/', '/img/', '/photo/', '/picture/', '/media/',
                'image=', 'img=', 'photo=', 'picture='
            ])
            
            return has_valid_extension or has_image_pattern
            
        except:
            return False
    
    def _calculate_image_score(self, img: Dict) -> int:
        """Calcular score de relevancia de imagen"""
        score = 0
        
        # Score por tamaño
        width = int(img.get('width', 0))
        height = int(img.get('height', 0))
        
        if width > 300 and height > 200:
            score += 10
        elif width > 200 and height > 150:
            score += 5
        
        # Score por alt text
        alt_text = img.get('alt', '').lower()
        if any(keyword in alt_text for keyword in ['noticia', 'imagen', 'foto', 'foto principal']):
            score += 15
        
        # Score por clase CSS
        class_name = img.get('className', '').lower()
        if any(keyword in class_name for keyword in ['main', 'featured', 'principal', 'hero', 'cover']):
            score += 20
        
        # Score por ID
        img_id = img.get('id', '').lower()
        if any(keyword in img_id for keyword in ['main', 'featured', 'principal']):
            score += 10
        
        # Score por URL
        url = img.get('url', '').lower()
        if any(keyword in url for keyword in ['/noticias/', '/imagenes/', '/fotos/', '/media/']):
            score += 5
        
        return score
    
    def _crawl_subcategories(self, base_url: str, max_images: int) -> List[Dict]:
        """Crawlear subcategorías para encontrar más imágenes"""
        subcategory_images = []
        
        try:
            # Subcategorías comunes
            subcategories = [
                'ultimas-noticias', 'noticias-recientes', 'galeria',
                'fotos', 'imagenes', 'multimedia', 'fotogaleria'
            ]
            
            parsed_url = urlparse(base_url)
            base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            for subcat in subcategories:
                try:
                    subcat_url = f"{base_domain}/{subcat}/"
                    response = self.session.get(subcat_url, timeout=5)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        images = self._extract_images_from_soup(soup, subcat_url)
                        subcategory_images.extend(images)
                        
                        if len(subcategory_images) >= max_images:
                            break
                            
                except Exception as e:
                    logger.debug(f"Error en subcategoría {subcat}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error crawleando subcategorías: {e}")
        
        return subcategory_images[:max_images]
    
    def _deduplicate_images(self, images: List[Dict]) -> List[Dict]:
        """Eliminar imágenes duplicadas"""
        seen_urls = set()
        unique_images = []
        
        for img in images:
            url = img.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_images.append(img)
        
        return unique_images
    
    def download_images_parallel(self, images: List[Dict], output_dir: str = "scraped_images") -> List[Dict]:
        """Descargar imágenes en paralelo"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        downloaded_images = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Enviar tareas de descarga
            future_to_image = {
                executor.submit(self._download_single_image, img, output_path): img 
                for img in images
            }
            
            # Procesar resultados
            for future in as_completed(future_to_image):
                img = future_to_image[future]
                try:
                    result = future.result()
                    if result:
                        downloaded_images.append(result)
                        logger.info(f"✅ Imagen descargada: {result['filename']}")
                except Exception as e:
                    logger.error(f"❌ Error descargando imagen {img.get('url', '')}: {e}")
        
        logger.info(f"🎉 Descarga completada: {len(downloaded_images)}/{len(images)} imágenes")
        return downloaded_images
    
    def _download_single_image(self, img: Dict, output_path: Path) -> Optional[Dict]:
        """Descargar una sola imagen"""
        try:
            url = img['url']
            
            # Generar nombre único
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            parsed_url = urlparse(url)
            original_name = os.path.basename(parsed_url.path)
            
            if not original_name or '.' not in original_name:
                original_name = f"image_{url_hash}.jpg"
            
            # Determinar extensión
            ext = os.path.splitext(original_name)[1].lower()
            if not ext or ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
                ext = '.jpg'
            
            filename = f"{url_hash}_{original_name}"
            if not filename.endswith(ext):
                filename += ext
            
            file_path = output_path / filename
            
            # Descargar imagen
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Verificar que sea realmente una imagen
            content_type = response.headers.get('content-type', '').lower()
            if not content_type.startswith('image/'):
                return None
            
            # Guardar imagen
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Verificar que se guardó correctamente
            if file_path.exists() and file_path.stat().st_size > 0:
                # Obtener información de la imagen
                try:
                    with Image.open(file_path) as pil_img:
                        width, height = pil_img.size
                        format_name = pil_img.format
                except:
                    width, height = 0, 0
                    format_name = 'unknown'
                
                return {
                    'local_path': str(file_path),
                    'url': url,
                    'filename': filename,
                    'alt_text': img.get('alt', ''),
                    'title': img.get('title', ''),
                    'width': width,
                    'height': height,
                    'format': format_name,
                    'size_bytes': file_path.stat().st_size,
                    'relevance_score': img.get('relevance_score', 0)
                }
            
        except Exception as e:
            logger.error(f"Error descargando imagen {url}: {e}")
        
        return None
    
    def crawl_articles_with_requests(self, url: str, max_articles: int = 50) -> List[Dict]:
        """Crawlear artículos usando Requests"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = self._extract_articles_from_soup(soup, url)
            
            # Filtrar y priorizar artículos
            filtered_articles = self._filter_and_prioritize_articles(articles, max_articles)
            
            logger.info(f"🔍 Requests: {len(filtered_articles)} artículos encontrados")
            return filtered_articles
            
        except Exception as e:
            logger.error(f"❌ Error en crawl Requests: {e}")
            return []
    
    def crawl_articles_with_selenium(self, url: str, max_articles: int = 50) -> List[Dict]:
        """Crawlear artículos usando Selenium"""
        self.init_selenium()
        if not self.driver:
            return []
        
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Scroll inteligente para cargar contenido
            self._smart_scroll_for_content()
            
            # Extraer artículos usando JavaScript
            articles = self._extract_articles_with_js(url)
            
            # Filtrar y priorizar artículos
            filtered_articles = self._filter_and_prioritize_articles(articles, max_articles)
            
            logger.info(f"🔍 Selenium: {len(filtered_articles)} artículos encontrados")
            return filtered_articles
            
        except Exception as e:
            logger.error(f"❌ Error en crawl Selenium: {e}")
            return []
    
    def crawl_articles_with_selenium_fast(self, url: str, max_articles: int = 50) -> List[Dict]:
        """Crawlear artículos usando Selenium - VERSIÓN RÁPIDA"""
        self.init_selenium()
        if not self.driver:
            return []
        
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 5).until(  # Timeout más corto
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Scroll rápido (solo 2 posiciones)
            self._fast_scroll_for_content()
            
            # Extraer artículos usando JavaScript
            articles = self._extract_articles_with_js(url)
            
            # Filtrar y priorizar artículos
            filtered_articles = self._filter_and_prioritize_articles(articles, max_articles)
            
            logger.info(f"🔍 Selenium Rápido: {len(filtered_articles)} artículos encontrados")
            return filtered_articles
            
        except Exception as e:
            logger.error(f"❌ Error en crawl Selenium rápido: {e}")
            return []
    
    def _smart_scroll_for_content(self):
        """Scroll inteligente para cargar contenido lazy - MEJORADO"""
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            max_attempts = 20  # Más intentos para sitios de noticias
            articles_found = set()
            
            while scroll_attempts < max_attempts:
                # Scroll progresivo en pasos más pequeños
                current_scroll = 0
                scroll_step = 500
                
                while current_scroll < last_height:
                    self.driver.execute_script(f"window.scrollTo(0, {current_scroll});")
                    time.sleep(0.5)  # Pausa más corta
                    current_scroll += scroll_step
                
                # Scroll final al fondo
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Verificar si hay nuevo contenido
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                # Contar artículos únicos encontrados
                current_articles = self.driver.execute_script("""
                    var articles = [];
                    var selectors = [
                        'article', '.article', '[class*="article"]',
                        '.news-item', '.post', '.entry', '.noticia',
                        '[class*="news"]', '[class*="post"]', '[class*="entry"]', '[class*="noticia"]',
                        'h1 a', 'h2 a', 'h3 a', '.title a', '.headline a', '.titulo a',
                        '.card a', '.item a', '.list-item a', '.content a',
                        'a[href*="/noticia/"]', 'a[href*="/article/"]', 'a[href*="/news/"]',
                        'a[href*="/post/"]', 'a[href*="/entry/"]', 'a[href*="/articulo/"]',
                        '.news-card a', '.article-card a', '.post-card a',
                        '.story a', '.content-item a', '.news-content a',
                        '[data-testid*="article"]', '[data-testid*="news"]',
                        '.feed-item', '.timeline-item', '.stream-item'
                    ];
                    
                    for (var i = 0; i < selectors.length; i++) {
                        var elements = document.querySelectorAll(selectors[i]);
                        for (var j = 0; j < elements.length; j++) {
                            var element = elements[j];
                            var link = element.tagName === 'A' ? element : element.querySelector('a');
                            if (link && link.href) {
                                articles.push(link.href);
                            }
                        }
                    }
                    return articles;
                """)
                
                new_articles = set(current_articles) - articles_found
                articles_found.update(current_articles)
                
                logger.info(f"📊 Scroll {scroll_attempts + 1}: {len(articles_found)} artículos únicos encontrados (+{len(new_articles)} nuevos)")
                
                if new_height == last_height and len(new_articles) == 0:
                    scroll_attempts += 1
                else:
                    scroll_attempts = 0
                    last_height = new_height
                
                # Intentar hacer clic en botones "cargar más"
                if len(new_articles) == 0:
                    if self._detect_and_click_load_more():
                        time.sleep(3)  # Esperar a que cargue el contenido
                        continue
                
                # Si no encontramos nuevos artículos en 3 intentos consecutivos, parar
                if scroll_attempts >= 3:
                    break
                    
            # Volver al inicio
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            logger.info(f"🎯 Scroll completado: {len(articles_found)} artículos únicos detectados")
            
        except Exception as e:
            logger.warning(f"⚠️ Error en scroll inteligente: {e}")
    
    def _detect_and_click_load_more(self):
        """Detectar y hacer clic en botones de 'cargar más' o 'ver más'"""
        try:
            load_more_selectors = [
                'button[class*="load"]', 'button[class*="more"]', 'button[class*="show"]',
                'a[class*="load"]', 'a[class*="more"]', 'a[class*="show"]',
                '.load-more', '.show-more', '.view-more', '.see-more',
                '[data-testid*="load"]', '[data-testid*="more"]',
                'button:contains("Cargar más")', 'button:contains("Ver más")',
                'button:contains("Show more")', 'button:contains("Load more")',
                'a:contains("Cargar más")', 'a:contains("Ver más")',
                'a:contains("Show more")', 'a:contains("Load more")'
            ]
            
            for selector in load_more_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            try:
                                self.driver.execute_script("arguments[0].click();", element)
                                logger.info(f"🔄 Clic en botón 'cargar más': {selector}")
                                time.sleep(2)
                                return True
                            except Exception as e:
                                logger.debug(f"No se pudo hacer clic en {selector}: {e}")
                                continue
                except Exception as e:
                    logger.debug(f"Error con selector {selector}: {e}")
                    continue
            
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ Error detectando botones de cargar más: {e}")
            return False
    
    def _fast_scroll_for_content(self):
        """Scroll rápido para cargar contenido lazy - VERSIÓN OPTIMIZADA"""
        try:
            # Scroll rápido (solo 2 posiciones)
            scroll_positions = [0.5, 1.0]  # Solo 50% y 100%
            
            for position in scroll_positions:
                # Scroll a posición
                self.driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {position});")
                time.sleep(0.5)  # Menos tiempo de espera
            
            # Scroll final al inicio
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.2)
            
        except Exception as e:
            logger.warning(f"⚠️ Error en scroll rápido: {e}")
    
    def _extract_articles_with_js(self, base_url: str) -> List[Dict]:
        """Extraer artículos usando JavaScript"""
        try:
            js_code = """
            var articles = [];
            var articleSelectors = [
                // Selectores específicos para artículos reales
                'article', '.article', '[class*="article"]',
                '.news-item', '.post', '.entry', '.noticia',
                '[class*="news"]', '[class*="post"]', '[class*="entry"]', '[class*="noticia"]',
                '.news-card a', '.article-card a', '.post-card a',
                '.story a', '.content-item a', '.news-content a',
                '[data-testid*="article"]', '[data-testid*="news"]',
                '.blog-post', '.news-story', '.press-release',
                '.announcement', '.publication', '.report',
                // Selectores específicos para sitios de noticias
                '.noticia-item', '.news-block', '.article-block',
                '.content-block', '.news-container', '.article-container',
                '.post-item', '.entry-item', '.story-item',
                '.news-list-item', '.article-list-item', '.post-list-item',
                '.news-grid-item', '.article-grid-item', '.post-grid-item',
                '.news-feed-item', '.article-feed-item', '.post-feed-item',
                // Selectores adicionales para encontrar más artículos
                '.item a', '.card a', '.content a', '.headline a', '.title a',
                '.summary a', '.excerpt a', '.teaser a', '.preview a',
                'h1 a', 'h2 a', 'h3 a', 'h4 a', '.article-list a', '.news-list a',
                '.post-list a', '.story-list a', '.grid a', '.masonry a', '.feed a',
                'a[class*="article"]', 'a[class*="news"]', 'a[class*="post"]',
                'a[class*="story"]', 'a[class*="title"]', 'a[class*="headline"]',
                // Enlaces específicos de artículos
                'a[href*="/noticia/"]', 'a[href*="/article/"]', 'a[href*="/news/"]',
                'a[href*="/post/"]', 'a[href*="/entry/"]', 'a[href*="/articulo/"]',
                'a[href*="/blog/"]', 'a[href*="/story/"]', 'a[href*="/report/"]',
                'a[href*="/press/"]', 'a[href*="/announcement/"]', 'a[href*="/publication/"]',
                // Patrones de fecha
                'a[href*="/2024/"]', 'a[href*="/2025/"]', 'a[href*="/2023/"]',
                // Patrones de ID
                'a[href*="/noticia-"]', 'a[href*="/articulo-"]', 'a[href*="/post-"]'
            ];
            
            for (var i = 0; i < articleSelectors.length; i++) {
                var elements = document.querySelectorAll(articleSelectors[i]);
                for (var j = 0; j < elements.length; j++) {
                    var element = elements[j];
                    var link = element.tagName === 'A' ? element : element.querySelector('a');
                    
                    if (link && link.href) {
                        var title = link.textContent.trim() || 
                                   element.querySelector('h1, h2, h3, .title, .headline, .titulo')?.textContent.trim() || 
                                   element.textContent.trim();
                        
                        // Filtrar enlaces que parecen ser artículos - MEJORADO Y MENOS RESTRICTIVO
                        var href = link.href.toLowerCase();
                        var titleLower = title.toLowerCase();
                        
                        // Solo excluir URLs obviamente no artículos
                        var isExcluded = href.includes('/tag/') ||
                                        href.includes('/tags/') ||
                                        href.includes('/categoria/') ||
                                        href.includes('/category/') ||
                                        href.includes('/author/') ||
                                        href.includes('/autor/') ||
                                        href.includes('/etiqueta/') ||
                                        href.includes('/page/') ||
                                        href.includes('/search') ||
                                        href.includes('/wp-') ||
                                        href.includes('/seccion/') ||
                                        href.includes('/section/') ||
                                        href.includes('/archivo/') ||
                                        href.includes('/archive/') ||
                                        href.includes('/buscar/') ||
                                        href.includes('/contacto/') ||
                                        href.includes('/contact/') ||
                                        href.includes('/sobre/') ||
                                        href.includes('/about/') ||
                                        href.includes('/politica/') ||
                                        href.includes('/policy/') ||
                                        href.includes('/terminos/') ||
                                        href.includes('/terms/') ||
                                        href.includes('/privacidad/') ||
                                        href.includes('/privacy/') ||
                                        href.includes('/suscripcion/') ||
                                        href.includes('/subscription/') ||
                                        href.includes('/newsletter/') ||
                                        href.includes('/newsletters/') ||
                                        href.includes('/rss/') ||
                                        href.includes('/feed/') ||
                                        href.includes('/sitemap/') ||
                                        href.includes('/mapa/') ||
                                        href.includes('/inicio/') ||
                                        href.includes('/home/') ||
                                        href.includes('/index/') ||
                                        href.includes('/login/') ||
                                        href.includes('/register/') ||
                                        href.includes('/registro/') ||
                                        href.includes('/api/') ||
                                        href.includes('/ajax/') ||
                                        href.includes('/json/') ||
                                        href.includes('/xml/') ||
                                        href.includes('/admin/') ||
                                        href.includes('/dashboard/') ||
                                        href.includes('facebook') ||
                                        href.includes('twitter') ||
                                        href.includes('instagram') ||
                                        href.includes('youtube') ||
                                        href.includes('linkedin') ||
                                        href.includes('whatsapp') ||
                                        href.includes('telegram') ||
                                        href.includes('/404') ||
                                        href.includes('/error') ||
                                        href.includes('/not-found') ||
                                        href.includes('#') ||
                                        href.includes('javascript:') ||
                                        href.includes('mailto:') ||
                                        href.includes('tel:') ||
                                        href.includes('.pdf') ||
                                        href.includes('.doc') ||
                                        href.includes('.docx') ||
                                        href.includes('.zip') ||
                                        href.includes('.rar') ||
                                        href.includes('.jpg') ||
                                        href.includes('.jpeg') ||
                                        href.includes('.png') ||
                                        href.includes('.gif') ||
                                        href.includes('.webp') ||
                                        href.includes('.bmp') ||
                                        href.includes('.svg') ||
                                        href.includes('.mp4') ||
                                        href.includes('.mp3') ||
                                        href.includes('.css') ||
                                        href.includes('.js') ||
                                        title.length < 10; // Títulos muy cortos probablemente no son artículos
                        
                        // Validación más flexible para incluir más artículos
                        var isArticle = !isExcluded && 
                                       href.startsWith('http') &&
                                       (href.includes('/noticia/') || 
                                       href.includes('/article/') || 
                                       href.includes('/news/') || 
                                       href.includes('/post/') || 
                                       href.includes('/entry/') || 
                                       href.includes('/articulo/') ||
                                       href.includes('/blog/') ||
                                       href.includes('/story/') ||
                                       href.includes('/report/') ||
                                       href.includes('/press/') ||
                                       href.includes('/announcement/') ||
                                       href.includes('/publication/') ||
                                        // Patrones de fecha
                                        href.includes('/2024/') ||
                                        href.includes('/2025/') ||
                                        href.includes('/2023/') ||
                                        // Patrones de ID
                                        href.includes('/noticia-') ||
                                        href.includes('/articulo-') ||
                                        href.includes('/post-') ||
                                        // URLs con guiones (probablemente slugs)
                                        (href.split('/').pop().includes('-') && href.split('/').pop().length > 10) ||
                                        // URLs con números (probablemente IDs)
                                        /\d+/.test(href) ||
                                        // Títulos largos con contenido sustancial
                                        (title && title.length > 15));
                        
                        if (title && title.length > 10 && isArticle && !isExcluded) {
                            articles.push({
                                url: link.href,
                                title: title,
                                element: articleSelectors[i],
                                className: element.className || '',
                                id: element.id || ''
                            });
                        }
                    }
                }
            }
            
            return articles;
            """
            
            js_articles = self.driver.execute_script(js_code)
            return js_articles or []
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo artículos con JS: {e}")
            return []
    
    def _extract_articles_from_soup(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extraer artículos desde BeautifulSoup"""
        articles = []
        
        try:
            # Selectores para artículos - MEJORADO (solo artículos reales)
            article_selectors = [
                # Selectores específicos para artículos reales
                'article', '.article', '[class*="article"]',
                '.news-item', '.post', '.entry', '.noticia',
                '[class*="news"]', '[class*="post"]', '[class*="entry"]', '[class*="noticia"]',
                '.news-card a', '.article-card a', '.post-card a',
                '.story a', '.content-item a', '.news-content a',
                '[data-testid*="article"]', '[data-testid*="news"]',
                '.blog-post', '.news-story', '.press-release',
                '.announcement', '.publication', '.report',
                # Enlaces específicos de artículos
                'a[href*="/noticia/"]', 'a[href*="/article/"]', 'a[href*="/news/"]',
                'a[href*="/post/"]', 'a[href*="/entry/"]', 'a[href*="/articulo/"]',
                'a[href*="/blog/"]', 'a[href*="/story/"]', 'a[href*="/report/"]',
                'a[href*="/press/"]', 'a[href*="/announcement/"]', 'a[href*="/publication/"]'
            ]
            
            for selector in article_selectors:
                try:
                    elements = soup.select(selector)
                    for element in elements:
                        link = element if element.name == 'a' else element.find('a')
                        
                        if link and link.get('href'):
                            title = link.get_text().strip()
                            if not title:
                                title_element = element.find(['h1', 'h2', 'h3', 'span'], class_=['title', 'headline'])
                                if title_element:
                                    title = title_element.get_text().strip()
                                else:
                                    title = element.get_text().strip()
                            
                            if title and len(title) > 20:
                                full_url = urljoin(base_url, link['href'])
                                
                                # Filtrar enlaces que parecen ser artículos - MEJORADO
                                href = full_url.lower()
                                title_lower = title.lower()
                                
                                # Excluir categorías, navegación y enlaces no deseados
                                is_excluded = ('/categoria/' in href or
                                             '/category/' in href or
                                             '/seccion/' in href or
                                             '/section/' in href or
                                             '/tag/' in href or
                                             '/etiqueta/' in href or
                                             '/archivo/' in href or
                                             '/archive/' in href or
                                             '/buscar/' in href or
                                             '/search/' in href or
                                             '/contacto/' in href or
                                             '/contact/' in href or
                                             '/sobre/' in href or
                                             '/about/' in href or
                                             '/politica/' in href or
                                             '/policy/' in href or
                                             '/terminos/' in href or
                                             '/terms/' in href or
                                             '/privacidad/' in href or
                                             '/privacy/' in href or
                                             '/suscripcion/' in href or
                                             '/subscription/' in href or
                                             '/newsletter/' in href or
                                             '/newsletters/' in href or
                                             '/rss/' in href or
                                             '/feed/' in href or
                                             '/sitemap/' in href or
                                             '/mapa/' in href or
                                             '/inicio/' in href or
                                             '/home/' in href or
                                             '/index/' in href or
                                             '/deportes/' in href or
                                             '/politica/' in href or
                                             '/economia/' in href or
                                             '/mundo/' in href or
                                             '/sociedad/' in href or
                                             '/tecnologia/' in href or
                                             '/cultura/' in href or
                                             '/espectaculos/' in href or
                                             '/gastronomia/' in href or
                                             '/turismo/' in href or
                                             '/vida/' in href or
                                             '/tendencias/' in href or
                                             '#' in href or
                                             'javascript:' in href or
                                             'mailto:' in href or
                                             'tel:' in href or
                                             '.pdf' in href or
                                             '.doc' in href or
                                             '.zip' in href or
                                             '.jpg' in href or
                                             '.png' in href or
                                             '.gif' in href or
                                             '.css' in href or
                                             '.js' in href or
                                             'categoria' in title_lower or
                                             'category' in title_lower or
                                             'seccion' in title_lower or
                                             'section' in title_lower or
                                             'archivo' in title_lower or
                                             'archive' in title_lower or
                                             'buscar' in title_lower or
                                             'search' in title_lower or
                                             'contacto' in title_lower or
                                             'contact' in title_lower or
                                             'sobre' in title_lower or
                                             'about' in title_lower or
                                             'politica' in title_lower or
                                             'policy' in title_lower or
                                             'terminos' in title_lower or
                                             'terms' in title_lower or
                                             'privacidad' in title_lower or
                                             'privacy' in title_lower or
                                             'suscripcion' in title_lower or
                                             'subscription' in title_lower or
                                             'newsletter' in title_lower or
                                             'newsletters' in title_lower or
                                             'rss' in title_lower or
                                             'feed' in title_lower or
                                             'sitemap' in title_lower or
                                             'mapa' in title_lower or
                                             'inicio' in title_lower or
                                             'home' in title_lower or
                                             'index' in title_lower or
                                             'deportes' in title_lower or
                                             'politica' in title_lower or
                                             'economia' in title_lower or
                                             'mundo' in title_lower or
                                             'sociedad' in title_lower or
                                             'tecnologia' in title_lower or
                                             'cultura' in title_lower or
                                             'espectaculos' in title_lower or
                                             'gastronomia' in title_lower or
                                             'turismo' in title_lower or
                                             'vida' in title_lower or
                                             'tendencias' in title_lower)
                                
                                # Solo incluir si es un artículo real y no está excluido
                                is_article = (not is_excluded and 
                                            href.startswith('http') and
                                            ('/noticia/' in href or 
                                            '/article/' in href or 
                                            '/news/' in href or 
                                            '/post/' in href or 
                                            '/entry/' in href or 
                                            '/articulo/' in href or
                                            '/blog/' in href or
                                            '/story/' in href or
                                            '/report/' in href or
                                            '/press/' in href or
                                            '/announcement/' in href or
                                            '/publication/' in href or
                                             (len(title) > 20 and 
                                              '/categoria/' not in href and
                                              '/category/' not in href and
                                              '/seccion/' not in href and
                                              '/section/' not in href)))
                                
                                if is_article and not is_excluded:
                                    article_info = {
                                        'url': full_url,
                                        'title': title,
                                        'element': selector,
                                        'className': ' '.join(element.get('class', [])),
                                        'id': element.get('id', '')
                                    }
                                    articles.append(article_info)
                                
                except Exception as e:
                    logger.debug(f"Error con selector {selector}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Error extrayendo artículos del soup: {e}")
        
        return articles
    
    def _filter_and_prioritize_articles(self, articles: List[Dict], max_articles: int) -> List[Dict]:
        """Filtrar y priorizar artículos por relevancia"""
        if not articles:
            return []
        
        # Filtrar artículos válidos
        valid_articles = []
        for article in articles:
            if self._is_valid_article(article):
                # Calcular score de relevancia
                score = self._calculate_article_score(article)
                article['relevance_score'] = score
                valid_articles.append(article)
        
        # Ordenar por relevancia
        valid_articles.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return valid_articles[:max_articles]
    
    def _is_valid_article(self, article: Dict) -> bool:
        """Verificar si un artículo es válido"""
        try:
            url = article.get('url', '')
            title = article.get('title', '')
            
            if not url or not title or len(title) < 10:
                return False
            
            # Verificar que no sea una página estática
            static_patterns = [
                '/contacto', '/about', '/sobre', '/privacy', '/terms',
                '/login', '/register', '/search', '/tag/', '/category/',
                '/archivo', '/archive', '/sitemap'
            ]
            
            for pattern in static_patterns:
                if pattern in url.lower():
                    return False
            
            return True
            
        except:
            return False
    
    def _calculate_article_score(self, article: Dict) -> int:
        """Calcular score de relevancia de artículo"""
        score = 0
        
        # Score por título
        title = article.get('title', '').lower()
        if any(keyword in title for keyword in ['noticia', 'actualidad', 'última', 'breaking']):
            score += 20
        
        # Score por elemento HTML
        element = article.get('element', '').lower()
        if 'article' in element:
            score += 15
        elif 'news' in element:
            score += 10
        
        # Score por clase CSS
        class_name = article.get('className', '').lower()
        if any(keyword in class_name for keyword in ['main', 'featured', 'principal', 'hero', 'lead']):
            score += 25
        
        # Score por URL
        url = article.get('url', '').lower()
        if any(keyword in url for keyword in ['/noticias/', '/news/', '/articulo/', '/article/']):
            score += 10
        
        return score
    
    def _crawl_article_subcategories(self, base_url: str, max_articles: int) -> List[Dict]:
        """Crawlear subcategorías para encontrar más artículos"""
        subcategory_articles = []
        
        try:
            # Subcategorías comunes
            subcategories = [
                'ultimas-noticias', 'noticias-recientes', 'actualidad',
                'politica', 'economia', 'deportes', 'tecnologia',
                'mundo', 'nacional', 'local', 'internacional'
            ]
            
            parsed_url = urlparse(base_url)
            base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            for subcat in subcategories:
                try:
                    subcat_url = f"{base_domain}/{subcat}/"
                    response = self.session.get(subcat_url, timeout=5)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        articles = self._extract_articles_from_soup(soup, subcat_url)
                        subcategory_articles.extend(articles)
                        
                        if len(subcategory_articles) >= max_articles:
                            break
                            
                except Exception as e:
                    logger.debug(f"Error en subcategoría {subcat}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error crawleando subcategorías: {e}")
        
        return subcategory_articles[:max_articles]
    
    def _deduplicate_articles(self, articles: List[Dict]) -> List[Dict]:
        """Eliminar artículos duplicados"""
        seen_urls = set()
        unique_articles = []
        
        for article in articles:
            url = article.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)
        
        return unique_articles
    
    def close(self):
        """Cerrar recursos"""
        if self.driver:
            self.driver.quit()
            logger.info("🔒 Selenium WebDriver cerrado")
        
        self.session.close()
        logger.info("🔒 Session HTTP cerrada")

# Funciones de conveniencia para uso directo
def crawl_articles_hybrid(url: str, max_articles: int = 50) -> List[Dict]:
    """
    Función de conveniencia para crawlear artículos de forma híbrida
    
    Args:
        url: URL a crawlear
        max_articles: Máximo número de artículos a extraer
    
    Returns:
        Lista de diccionarios con información de los artículos
    """
    crawler = HybridDataCrawler()
    
    try:
        # Crawlear artículos
        articles = crawler.hybrid_crawl_articles(url, max_articles)
        return articles
        
    finally:
        crawler.close()

def crawl_images_hybrid(url: str, max_images: int = 50, download: bool = True, output_dir: str = "scraped_images") -> List[Dict]:
    """
    Función de conveniencia para crawlear imágenes de forma híbrida
    
    Args:
        url: URL a crawlear
        max_images: Máximo número de imágenes a extraer
        download: Si descargar las imágenes
        output_dir: Directorio de salida para las imágenes
    
    Returns:
        Lista de diccionarios con información de las imágenes
    """
    crawler = HybridDataCrawler()
    
    try:
        # Crawlear imágenes
        images = crawler.hybrid_crawl_images(url, max_images)
        
        if download and images:
            # Descargar imágenes
            downloaded_images = crawler.download_images_parallel(images, output_dir)
            return downloaded_images
        else:
            return images
            
    finally:
        crawler.close()

def crawl_complete_hybrid(url: str, max_articles: int = 50, max_images: int = 50, download_images: bool = True, output_dir: str = "scraped_images", fast_mode: bool = True) -> Tuple[List[Dict], List[Dict]]:
    """
    Función de conveniencia para crawlear artículos e imágenes de forma híbrida inteligente
    
    Args:
        url: URL a crawlear
        max_articles: Máximo número de artículos a extraer
        max_images: Máximo número de imágenes a extraer
        download_images: Si descargar las imágenes
        output_dir: Directorio de salida para las imágenes
        fast_mode: Si usar modo rápido (análisis inteligente)
    
    Returns:
        Tupla con (artículos, imágenes)
    """
    crawler = HybridDataCrawler()
    
    try:
        if fast_mode:
            # Modo rápido: análisis inteligente de la página
            logger.info("🚀 Modo rápido: analizando página para decidir método óptimo")
            articles = crawler.hybrid_crawl_articles(url, max_articles)
            images = crawler.hybrid_crawl_images(url, max_images)
        else:
            # Modo completo: usar todos los métodos disponibles
            logger.info("🔍 Modo completo: usando todos los métodos disponibles")
            articles = crawler.hybrid_crawl_articles(url, max_articles)
            images = crawler.hybrid_crawl_images(url, max_images)
        
        if download_images and images:
            # Descargar imágenes
            downloaded_images = crawler.download_images_parallel(images, output_dir)
            return articles, downloaded_images
        else:
            return articles, images
            
    finally:
        crawler.close()
