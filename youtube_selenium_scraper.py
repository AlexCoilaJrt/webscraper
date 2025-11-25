"""
YouTube Selenium Scraper (Fallback)
PROYECTO ACADÉMICO - Solo para fines educativos

Este scraper usa Selenium para extraer datos de YouTube cuando la API no está disponible.
"""

import time
import random
import re
import logging
from typing import List, Dict, Optional
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

# Intentar importar undetected-chromedriver
try:
    import undetected_chromedriver as uc
    UC_AVAILABLE = True
except ImportError:
    UC_AVAILABLE = False


class YouTubeSeleniumScraper:
    """
    Scraper de YouTube usando Selenium (Fallback cuando API no está disponible)
    
    IMPORTANTE: Este código es solo para fines académicos y educativos.
    Respeta los términos de servicio de YouTube y las leyes locales.
    """
    
    def __init__(self, headless: bool = True):
        """
        Inicializar el scraper de YouTube con Selenium
        
        Args:
            headless: Si True, ejecuta el navegador en modo headless
        """
        self.headless = headless
        self.driver = None
        self._setup_driver()
    
    def _setup_driver(self):
        """Configurar el driver de Chrome con opciones anti-detección"""
        try:
            if UC_AVAILABLE:
                options = uc.ChromeOptions()
                if self.headless:
                    options.add_argument('--headless=new')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('useAutomationExtension', False)
                
                self.driver = uc.Chrome(options=options)
                logger.info("✅ Driver de YouTube configurado (undetected-chromedriver)")
            else:
                options = ChromeOptions()
                if self.headless:
                    options.add_argument('--headless=new')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('useAutomationExtension', False)
                
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                logger.info("✅ Driver de YouTube configurado (Selenium estándar)")
            
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
        except Exception as e:
            logger.error(f"❌ Error configurando driver: {e}")
            raise
    
    def _parse_views(self, views_text: str) -> int:
        """Parsear número de vistas (ej: '1.2M vistas' -> 1200000)"""
        try:
            if not views_text:
                return 0
            
            views_text = views_text.strip().lower()
            
            # Remover texto adicional
            views_text = re.sub(r'[^\d.kmb]', '', views_text)
            
            if 'b' in views_text:
                number = float(views_text.replace('b', ''))
                return int(number * 1000000000)
            elif 'm' in views_text:
                number = float(views_text.replace('m', ''))
                return int(number * 1000000)
            elif 'k' in views_text:
                number = float(views_text.replace('k', ''))
                return int(number * 1000)
            else:
                return int(float(views_text))
        except:
            return 0
    
    def _parse_duration(self, duration_text: str) -> str:
        """Parsear duración (ej: '10:30' -> '10:30')"""
        try:
            if not duration_text:
                return "0:00"
            
            # Limpiar texto
            duration_text = duration_text.strip()
            
            # Remover espacios y caracteres no válidos
            duration_text = re.sub(r'[^\d:]', '', duration_text)
            
            return duration_text if duration_text else "0:00"
        except:
            return "0:00"
    
    def scrape_channel(self, channel_url: str, max_videos: int = 100) -> List[Dict]:
        """
        Scrapear videos de un canal de YouTube
        
        Args:
            channel_url: URL del canal (ej: 'https://www.youtube.com/@channelname' o 'https://www.youtube.com/channel/UCxxxxx')
            max_videos: Número máximo de videos
        
        Returns:
            Lista de diccionarios con datos de los videos
        """
        videos = []
        
        try:
            # Asegurar que la URL apunte a la sección de videos
            if '/videos' not in channel_url and '/playlists' not in channel_url and '/about' not in channel_url:
                if channel_url.endswith('/'):
                    channel_url = f"{channel_url}videos"
                else:
                    channel_url = f"{channel_url}/videos"
            
            logger.info(f"🌐 Navegando a: {channel_url}")
            self.driver.get(channel_url)
            time.sleep(5)
            
            scrolls = 0
            max_scrolls = 50
            videos_ids_vistos = set()
            
            while len(videos) < max_videos and scrolls < max_scrolls:
                # Buscar videos visibles
                video_elements = self.driver.find_elements(By.CSS_SELECTOR, 'ytd-video-renderer, div#dismissible')
                logger.info(f"📊 Videos encontrados en página: {len(video_elements)}")
                
                for video_elem in video_elements:
                    try:
                        # Extraer título y URL
                        try:
                            title_elem = video_elem.find_element(By.CSS_SELECTOR, 'a#video-title, h3 a[href*="/watch"]')
                            title = title_elem.text.strip()
                            video_url = title_elem.get_attribute('href')
                            
                            # Extraer video ID de la URL
                            video_id = None
                            if video_url:
                                match = re.search(r'[?&]v=([^&]+)', video_url)
                                if match:
                                    video_id = match.group(1)
                                else:
                                    # Intentar extraer de path
                                    match = re.search(r'/watch/([^/?]+)', video_url)
                                    if match:
                                        video_id = match.group(1)
                            
                            if not video_id:
                                continue
                            
                            if video_id in videos_ids_vistos:
                                continue
                            
                            videos_ids_vistos.add(video_id)
                        except:
                            continue
                        
                        # Extraer canal
                        try:
                            channel_elem = video_elem.find_element(By.CSS_SELECTOR, 'ytd-channel-name a, #channel-name a, .ytd-channel-name a')
                            channel = channel_elem.text.strip()
                        except:
                            channel = "Unknown"
                        
                        # Extraer vistas y fecha
                        views = 0
                        try:
                            views_elem = video_elem.find_element(By.CSS_SELECTOR, 'span#metadata-line, span.style-scope.ytd-video-meta-block')
                            views_text = views_elem.text.strip()
                            # Extraer número de vistas (ej: "1.2M vistas hace 2 semanas")
                            views_match = re.search(r'([\d.]+[kmb]?)\s*vista', views_text.lower())
                            if views_match:
                                views = self._parse_views(views_match.group(1))
                            else:
                                # Intentar extraer cualquier número
                                numbers = re.findall(r'[\d.]+[kmb]?', views_text)
                                if numbers:
                                    views = self._parse_views(numbers[0])
                        except:
                            pass
                        
                        # Extraer thumbnail
                        thumbnail_url = None
                        try:
                            thumbnail_elem = video_elem.find_element(By.CSS_SELECTOR, 'img.yt-img-shadow, ytd-thumbnail img')
                            thumbnail_url = thumbnail_elem.get_attribute('src') or thumbnail_elem.get_attribute('data-src')
                        except:
                            pass
                        
                        # Extraer duración
                        duration = "0:00"
                        try:
                            duration_elem = video_elem.find_element(By.CSS_SELECTOR, 'span.ytd-thumbnail-overlay-time-status-renderer')
                            duration = self._parse_duration(duration_elem.text.strip())
                        except:
                            pass
                        
                        # Extraer descripción (si está disponible)
                        description = ""
                        try:
                            desc_elem = video_elem.find_element(By.CSS_SELECTOR, 'ytd-video-renderer #description-text')
                            description = desc_elem.text.strip()
                        except:
                            pass
                        
                        video_data = {
                            'id': video_id,
                            'platform': 'youtube',
                            'title': title,
                            'description': description,
                            'channel': channel,
                            'channel_id': '',
                            'url': video_url,
                            'thumbnail': thumbnail_url,
                            'views': views,
                            'likes': 0,  # No disponible sin API
                            'comments': 0,  # No disponible sin API
                            'duration': duration,
                            'published_at': datetime.now().isoformat(),
                            'tags': [],
                            'category_id': '',
                            'scraped_at': datetime.now().isoformat()
                        }
                        
                        videos.append(video_data)
                        logger.info(f"✅ Video extraído: {title[:50]}... (Vistas: {views}, Canal: {channel})")
                        
                        if len(videos) >= max_videos:
                            break
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Error extrayendo video individual: {e}")
                        continue
                
                if len(videos) >= max_videos:
                    break
                
                # Scroll para cargar más videos
                logger.info(f"📜 Scroll {scrolls + 1}/{max_scrolls} para cargar más videos...")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                scrolls += 1
            
            logger.info(f"✅ Extraídos {len(videos)} videos del canal")
            return videos
            
        except Exception as e:
            logger.error(f"❌ Error scrapeando canal: {e}")
            return []
    
    def search_videos(self, query: str, max_videos: int = 50) -> List[Dict]:
        """
        Buscar videos en YouTube
        
        Args:
            query: Término de búsqueda
            max_videos: Número máximo de videos
        
        Returns:
            Lista de diccionarios con datos de los videos
        """
        videos = []
        
        try:
            search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            logger.info(f"🌐 Buscando: {search_url}")
            self.driver.get(search_url)
            time.sleep(5)
            
            scrolls = 0
            max_scrolls = 30
            videos_ids_vistos = set()
            
            while len(videos) < max_videos and scrolls < max_scrolls:
                # Buscar videos visibles
                video_elements = self.driver.find_elements(By.CSS_SELECTOR, 'ytd-video-renderer, div#dismissible')
                logger.info(f"📊 Videos encontrados: {len(video_elements)}")
                
                for video_elem in video_elements:
                    try:
                        # Extraer título y URL
                        try:
                            title_elem = video_elem.find_element(By.CSS_SELECTOR, 'a#video-title, h3 a[href*="/watch"]')
                            title = title_elem.text.strip()
                            video_url = title_elem.get_attribute('href')
                            
                            # Extraer video ID
                            video_id = None
                            if video_url:
                                match = re.search(r'[?&]v=([^&]+)', video_url)
                                if match:
                                    video_id = match.group(1)
                            
                            if not video_id or video_id in videos_ids_vistos:
                                continue
                            
                            videos_ids_vistos.add(video_id)
                        except:
                            continue
                        
                        # Extraer canal
                        try:
                            channel_elem = video_elem.find_element(By.CSS_SELECTOR, 'ytd-channel-name a, #channel-name a')
                            channel = channel_elem.text.strip()
                        except:
                            channel = "Unknown"
                        
                        # Extraer vistas
                        views = 0
                        try:
                            views_elem = video_elem.find_element(By.CSS_SELECTOR, 'span#metadata-line')
                            views_text = views_elem.text.strip()
                            views_match = re.search(r'([\d.]+[kmb]?)\s*vista', views_text.lower())
                            if views_match:
                                views = self._parse_views(views_match.group(1))
                        except:
                            pass
                        
                        # Extraer thumbnail
                        thumbnail_url = None
                        try:
                            thumbnail_elem = video_elem.find_element(By.CSS_SELECTOR, 'img[src*="i.ytimg.com"], ytd-thumbnail img')
                            thumbnail_url = thumbnail_elem.get_attribute('src') or thumbnail_elem.get_attribute('data-src')
                        except:
                            pass
                        
                        video_data = {
                            'id': video_id,
                            'platform': 'youtube',
                            'title': title,
                            'description': '',
                            'channel': channel,
                            'channel_id': '',
                            'url': video_url,
                            'thumbnail': thumbnail_url,
                            'views': views,
                            'likes': 0,
                            'comments': 0,
                            'duration': '0:00',
                            'published_at': datetime.now().isoformat(),
                            'tags': [],
                            'category_id': '',
                            'scraped_at': datetime.now().isoformat()
                        }
                        
                        videos.append(video_data)
                        
                        if len(videos) >= max_videos:
                            break
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Error extrayendo video: {e}")
                        continue
                
                if len(videos) >= max_videos:
                    break
                
                # Scroll para cargar más
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                scrolls += 1
            
            logger.info(f"✅ Extraídos {len(videos)} videos de búsqueda: '{query}'")
            return videos
            
        except Exception as e:
            logger.error(f"❌ Error buscando videos: {e}")
            return []
    
    def close(self):
        """Cerrar el driver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("✅ Driver de YouTube cerrado")
            except:
                pass















