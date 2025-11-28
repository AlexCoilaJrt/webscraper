#!/usr/bin/env python3
"""
Sistema de Web Scraping de Redes Sociales
PROYECTO ACADÉMICO - Solo para fines educativos

Este módulo permite extraer datos públicos de Twitter/X para análisis educativo.
Incluye medidas responsables: delays, límites de requests, y disclaimers éticos.
"""

import time
import re
import logging
import requests
import html
from typing import List, Dict, Optional
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import json
import random
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REDDIT_REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01"
}

# Intentar importar scrapers de Reddit
try:
    from reddit_api_scraper import RedditAPIScraper
    REDDIT_API_AVAILABLE = True
except ImportError:
    REDDIT_API_AVAILABLE = False
    logger.info("ℹ️ Reddit API scraper no disponible")

try:
    from reddit_selenium_scraper import RedditSeleniumScraper
    REDDIT_SELENIUM_AVAILABLE = True
except ImportError:
    REDDIT_SELENIUM_AVAILABLE = False
    logger.info("ℹ️ Reddit Selenium scraper no disponible")

# Intentar importar scrapers de YouTube
try:
    from youtube_api_scraper import YouTubeAPIScraper
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False
    logger.info("ℹ️ YouTube API scraper no disponible")

try:
    from youtube_selenium_scraper import YouTubeSeleniumScraper
    YOUTUBE_SELENIUM_AVAILABLE = True
except ImportError:
    YOUTUBE_SELENIUM_AVAILABLE = False
    logger.info("ℹ️ YouTube Selenium scraper no disponible")

# Intentar importar undetected-chromedriver (más difícil de detectar)
try:
    import undetected_chromedriver as uc
    UC_AVAILABLE = True
except ImportError:
    UC_AVAILABLE = False
    logger.warning("⚠️ undetected-chromedriver no disponible, usando Selenium estándar")

# Intentar importar Playwright (alternativa más moderna)
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.info("ℹ️ Playwright no disponible, usando solo Selenium")


class TwitterScraper:
    """
    Scraper educativo para Twitter/X
    
    IMPORTANTE: Este código es solo para fines académicos y educativos.
    Respeta los términos de servicio de Twitter/X y las leyes locales.
    """
    
    def __init__(self, headless: bool = True, delay: int = 5):
        """
        Inicializar el scraper de Twitter
        
        Args:
            headless: Si True, ejecuta el navegador en modo headless
            delay: Delay entre requests en segundos (mínimo 3 para ser responsable)
        """
        self.delay = max(delay, 3)  # Mínimo 3 segundos por ética
        self.headless = headless
        self.driver = None
        self._setup_driver()
        
    def _simulate_human_typing(self, element, text):
        """
        Simular escritura humana escribiendo cada carácter uno por uno
        con delays aleatorios de 0.1 a 0.3 segundos
        """
        try:
            element.clear()
            for char in text:
                element.send_keys(char)
                # Delay aleatorio entre 0.1 y 0.3 segundos
                time.sleep(random.uniform(0.1, 0.3))
        except Exception as e:
            logger.warning(f"⚠️ Error simulando escritura humana: {e}")
            # Fallback: escribir normal
            element.clear()
            element.send_keys(text)
    
    def _setup_driver(self):
        """Configurar el driver con mejor anti-detección - Prioridad: undetected-chromedriver"""
        try:
            # PRIORIDAD 1: Intentar undetected-chromedriver (más difícil de detectar)
            if UC_AVAILABLE:
                try:
                    logger.info("🔧 Intentando usar undetected-chromedriver para Twitter/X (más difícil de detectar)...")
                    options = uc.ChromeOptions()
                    
                    # FORZAR modo visible para permitir login manual
                    # NO usar headless para Twitter/X
                    if self.headless:
                        logger.warning("⚠️ ⚠️ ⚠️ headless=True pero FORZANDO modo visible para permitir login")
                        logger.info("👁️ El navegador se abrirá VISIBLE para que puedas hacer login si es necesario")
                        # NO agregar --headless para que sea visible
                    # else:
                    #     logger.info("✅ Navegador en modo VISIBLE (headless=False)")
                    
                    options.add_argument('--no-sandbox')
                    options.add_argument('--disable-dev-shm-usage')
                    options.add_argument('--disable-blink-features=AutomationControlled')
                    options.add_argument('--disable-features=IsolateOrigins,site-per-process')
                    
                    # User agent realista
                    options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                    
                    # Preferencias
                    prefs = {
                        "credentials_enable_service": False,
                        "profile.password_manager_enabled": False,
                        "profile.default_content_setting_values.notifications": 2
                    }
                    options.add_experimental_option("prefs", prefs)
                    
                    self.driver = uc.Chrome(options=options, version_main=None, use_subprocess=True)
                    logger.info("✅ ✅ ✅ undetected-chromedriver configurado para Twitter/X (más difícil de detectar)")
                    logger.info("👁️ 👁️ 👁️ NAVEGADOR VISIBLE - Deberías ver una ventana de Chrome ahora")
                    # Asegurar que la ventana esté visible y enfocada
                    try:
                        self.driver.maximize_window()
                        logger.info("✅ Ventana maximizada para mejor visibilidad")
                    except:
                        pass
                    return
                    
                except Exception as uc_error:
                    logger.warning(f"⚠️ undetected-chromedriver falló: {uc_error}, usando Chrome estándar...")
            
            # PRIORIDAD 2: Chrome estándar con anti-detección
            logger.info("🔧 Usando Chrome estándar con técnicas anti-detección...")
            chrome_options = Options()
            
            # FORZAR modo visible para permitir login manual
            # NO usar headless para Twitter/X
            if self.headless:
                logger.warning("⚠️ ⚠️ ⚠️ headless=True pero FORZANDO modo visible para permitir login")
                logger.info("👁️ El navegador se abrirá VISIBLE para que puedas hacer login si es necesario")
                # NO agregar --headless para que sea visible
            # else:
            #     logger.info("✅ Navegador en modo VISIBLE (headless=False)")
            
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-features=IsolateOrigins,site-per-process')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            prefs = {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
                "profile.default_content_setting_values.notifications": 2
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            logger.info("👁️ 👁️ 👁️ NAVEGADOR VISIBLE - Deberías ver una ventana de Chrome ahora")
            # Asegurar que la ventana esté visible y enfocada
            try:
                self.driver.maximize_window()
                logger.info("✅ Ventana maximizada para mejor visibilidad")
            except:
                pass
            
            # Técnicas anti-detección avanzadas
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['es-ES', 'es', 'en-US', 'en']})")
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            logger.info("✅ Driver de Chrome configurado con técnicas anti-detección")
            
        except Exception as e:
            logger.error(f"❌ Error configurando driver: {e}")
            raise
    
    def _try_requests_method(self, url: str, max_tweets: int = 50) -> Optional[List[Dict]]:
        """
        Intentar extraer tweets usando requests directamente (método alternativo)
        A veces funciona mejor que Selenium para contenido público
        """
        try:
            logger.info(f"🔍 Intentando método alternativo (requests) para: {url}")
            
            # Headers más sofisticados para parecer un navegador real
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
            }
            
            session = requests.Session()
            session.headers.update(headers)
            
            # Intentar obtener la página
            response = session.get(url, timeout=15, allow_redirects=True)
            
            if response.status_code != 200:
                logger.warning(f"⚠️ Método requests falló: Status {response.status_code}")
                return None
            
            # Verificar si requiere autenticación
            if any(x in response.text for x in ['Sign in', 'Iniciar sesión', 'login', 'sign in']):
                logger.warning("⚠️ Método requests detectó que requiere autenticación")
                return None
            
            # Parsear HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Intentar encontrar tweets
            tweet_elements = soup.find_all('article', {'data-testid': 'tweet'})
            
            if not tweet_elements:
                tweet_elements = soup.find_all('article')
            
            if not tweet_elements:
                logger.warning("⚠️ No se encontraron tweets con método requests")
                return None
            
            logger.info(f"✅ Método requests encontró {len(tweet_elements)} elementos potenciales")
            
            # Extraer tweets
            tweets = []
            for elem in tweet_elements[:max_tweets]:
                tweet_data = self._extract_tweet_data(elem)
                if tweet_data and tweet_data.get('text'):
                    tweets.append(tweet_data)
            
            if tweets:
                logger.info(f"✅ ✅ Método requests extrajo {len(tweets)} tweets REALES!")
                return tweets
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Método requests falló: {e}")
            return None
    
    def scrape_from_url(self, url: str, max_tweets: int = 50) -> List[Dict]:
        """
        Scraping desde una URL de Twitter/X
        
        Args:
            url: URL de Twitter/X (perfil, página, etc.)
            max_tweets: Máximo de tweets a extraer (máx 50 para no sobrecargar)
        
        Returns:
            Lista de diccionarios con datos de tweets
        """
        # Sin límite para fines académicos - el usuario puede especificar cualquier cantidad
        if max_tweets < 1:
            max_tweets = 10  # Mínimo 1 tweet
        
        tweets = []
        url = url.strip()
        
        # Normalizar URL
        if not url.startswith('http'):
            if url.startswith('twitter.com') or url.startswith('x.com'):
                url = 'https://' + url
            else:
                url = 'https://twitter.com/' + url.lstrip('/')
        
        try:
            logger.info(f"🔍 Scrapeando desde URL: {url}")
            
            # PRIMERO: Intentar método alternativo con requests (más rápido, a veces funciona)
            try:
                tweets_requests = self._try_requests_method(url, max_tweets)
                if tweets_requests and len(tweets_requests) > 0:
                    logger.info(f"🎉 🎉 🎉 MÉTODO ALTERNATIVO EXITOSO: {len(tweets_requests)} tweets REALES extraídos!")
                    return tweets_requests[:max_tweets]
            except Exception as e:
                logger.info(f"ℹ️ Método alternativo no disponible, usando Selenium: {e}")
            
            # SEGUNDO: Intentar con Selenium
            logger.info(f"🔍 Intentando con Selenium...")
            
            # Configurar timeout más largo
            self.driver.set_page_load_timeout(60)  # 60 segundos para cargar página
            self.driver.implicitly_wait(20)  # Esperar hasta 20 segundos para elementos
            
            # Intentar cargar la página con retry
            for attempt in range(3):
                try:
                    self.driver.get(url)
                    logger.info(f"✅ Página cargada: {url} (intento {attempt + 1})")
                    break
                except Exception as e:
                    if attempt < 2:
                        logger.warning(f"⚠️ Intento {attempt + 1} falló: {e}, reintentando...")
                        time.sleep(3)
                        continue
                    else:
                        raise
            
            time.sleep(self.delay)  # Delay responsable
            
            # Verificar si la página cargó correctamente
            page_source = self.driver.page_source
            
            # Verificar si requiere autenticación - PERO NO RETORNAR VACÍO INMEDIATAMENTE
            # Intentar extraer contenido visible aunque haya pantalla de login
            requires_auth = any([
                'Sign in' in page_source,
                'Iniciar sesión' in page_source,
                'Inicia sesión' in page_source,
                'login' in page_source.lower(),
                'sign in' in page_source.lower(),
                'signin' in page_source.lower(),
                'You need to log in' in page_source,
                'Necesitas iniciar sesión' in page_source,
                'Join Twitter' in page_source,
                'Únete a Twitter' in page_source
            ])
            
            if requires_auth:
                if not self.headless:
                    logger.warning("⚠️ ⚠️ ⚠️ Twitter/X muestra pantalla de LOGIN")
                    logger.info("🔑 Si estás viendo el navegador, puedes hacer login manualmente ahora")
                    logger.info("⏳ Esperando 30 segundos para que puedas hacer login si es necesario...")
                    time.sleep(30)  # Esperar 30 segundos para login manual
                    # Verificar si ya se hizo login
                    page_source_after = self.driver.page_source
                    requires_auth_after = any([
                        'Sign in' in page_source_after,
                        'Iniciar sesión' in page_source_after,
                        'Inicia sesión' in page_source_after,
                        'login' in page_source_after.lower(),
                        'sign in' in page_source_after.lower(),
                    ])
                    if not requires_auth_after:
                        logger.info("✅ ✅ ✅ Login detectado! Continuando con extracción...")
                    else:
                        logger.warning("⚠️ Aún muestra pantalla de login, continuando de todas formas...")
                else:
                    logger.warning("⚠️ Twitter/X muestra pantalla de login (modo headless)")
                    logger.info("ℹ️ Algunas páginas públicas pueden tener contenido visible sin login")
                # NO retornar vacío - continuar intentando extraer
            
            # Guardar HTML inicial ANTES de hacer scrolls (por si el driver se cierra)
            logger.info("💾 Guardando HTML inicial...")
            initial_html = self.driver.page_source
            
            # Esperar tiempo inicial MÍNIMO
            logger.info("⏳ Esperando a que cargue el contenido inicial (3s)...")
            time.sleep(3)  # Reducido a 3 segundos
            
            # PRIORIDAD: Intentar extraer tweets INMEDIATAMENTE con JavaScript (más rápido)
            logger.info("🔍 🔍 🔍 EXTRAYENDO TWEETS INMEDIATAMENTE CON JAVASCRIPT...")
            try:
                # Usar JavaScript para extraer tweets directamente del DOM (más rápido que Selenium)
                tweets_js = self.driver.execute_script("""
                    var tweets = [];
                    var articles = document.querySelectorAll('article[data-testid="tweet"]');
                    if (articles.length === 0) {
                        articles = document.querySelectorAll('article');
                    }
                    if (articles.length === 0) {
                        articles = document.querySelectorAll('div[role="article"]');
                    }
                    
                    for (var i = 0; i < Math.min(articles.length, 200); i++) {
                        var article = articles[i];
                        
                        // Extraer texto
                        var textElem = article.querySelector('[data-testid="tweetText"]');
                        if (!textElem) {
                            var spans = article.querySelectorAll('span[dir="auto"]');
                            for (var j = spans.length - 1; j >= 0; j--) {
                                if (spans[j].textContent.trim().length > 20) {
                                    textElem = spans[j];
                                    break;
                                }
                            }
                        }
                        
                        if (textElem && textElem.textContent.trim().length > 20) {
                            // Extraer imagen
                            var img = article.querySelector('img[src*="pbs.twimg.com"]:not([src*="profile"])');
                            
                            // Extraer username
                            var username = '@RPPNoticias';
                            var userLink = article.querySelector('a[href*="/RPPNoticias"]');
                            if (userLink) {
                                var userSpan = userLink.querySelector('span');
                                if (userSpan) {
                                    username = '@' + userSpan.textContent.trim().replace('@', '');
                                }
                            }
                            
                            // Extraer URL del tweet
                            var tweetUrl = '';
                            var timeElem = article.querySelector('time');
                            if (timeElem) {
                                var link = timeElem.closest('a');
                                if (link) {
                                    tweetUrl = link.href;
                                }
                            }
                            
                            tweets.push({
                                text: textElem.textContent.trim(),
                                image: img ? img.src : null,
                                username: username,
                                url: tweetUrl
                            });
                        }
                    }
                    return tweets;
                """)
                
                if tweets_js and len(tweets_js) > 0:
                    logger.info(f"✅ ✅ ✅ JAVASCRIPT ENCONTRÓ {len(tweets_js)} TWEETS INMEDIATAMENTE!")
                    # Extraer TODOS los tweets encontrados, no solo hasta max_tweets
                    for js_tweet in tweets_js:
                        if js_tweet.get('text') and len(js_tweet.get('text', '')) > 20:
                            tweet_data = {
                                'platform': 'twitter',
                                'username': js_tweet.get('username', '@RPPNoticias'),
                                'text': js_tweet.get('text', ''),
                                'cleaned_text': js_tweet.get('text', '').strip(),
                                'image_url': js_tweet.get('image'),
                                'video_url': None,
                                'url': js_tweet.get('url', ''),
                                'date': datetime.now().isoformat(),
                                'created_at': datetime.now().isoformat(),
                                'likes': 0,
                                'retweets': 0,
                                'replies': 0,
                                'hashtags': re.findall(r'#\w+', js_tweet.get('text', '')),
                                'scraped_at': datetime.now().isoformat()
                            }
                            tweets.append(tweet_data)
                            logger.info(f"✅ Tweet {len(tweets)} REAL extraído (JS rápido): {js_tweet.get('text', '')[:60]}...")
                    
                    if tweets and len(tweets) > 0:
                        logger.info(f"✅ ✅ ✅ EXTRACCIÓN RÁPIDA CON JAVASCRIPT EXITOSA: {len(tweets)} tweets REALES!")
                        # NO retornar todavía - continuar con scrolls para obtener MÁS tweets
                        logger.info(f"📜 Continuando con scrolls para obtener MÁS tweets (actualmente: {len(tweets)})...")
                        # NO cerrar driver todavía, continuar con scrolls
                else:
                    logger.warning("⚠️ JavaScript no encontró tweets, intentando con Selenium...")
            except Exception as e:
                logger.warning(f"⚠️ Método JavaScript rápido falló: {e}, intentando Selenium...")
            
            # Hacer scrolls MÚLTIPLES para cargar MÁS contenido
            logger.info("📜 Haciendo scrolls MÚLTIPLES para cargar MÁS tweets...")
            tweets_before_scrolls = len(tweets)
            for i in range(10):  # 10 scrolls para cargar más tweets
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # Esperar entre scrolls
                # Después de cada 3 scrolls, intentar extraer más tweets
                if (i + 1) % 3 == 0:
                    try:
                        # Intentar extraer más tweets con JavaScript después de scrolls
                        more_tweets_js = self.driver.execute_script("""
                            var tweets = [];
                            var articles = document.querySelectorAll('article[data-testid="tweet"]');
                            if (articles.length === 0) {
                                articles = document.querySelectorAll('article');
                            }
                            for (var i = 0; i < articles.length; i++) {
                                var article = articles[i];
                                var textElem = article.querySelector('[data-testid="tweetText"]');
                                if (!textElem) {
                                    var spans = article.querySelectorAll('span[dir="auto"]');
                                    for (var j = spans.length - 1; j >= 0; j--) {
                                        if (spans[j].textContent.trim().length > 20) {
                                            textElem = spans[j];
                                            break;
                                        }
                                    }
                                }
                                if (textElem && textElem.textContent.trim().length > 20) {
                                    var img = article.querySelector('img[src*="pbs.twimg.com"]:not([src*="profile"])');
                                    var username = '@RPPNoticias';
                                    var userLink = article.querySelector('a[href*="/RPPNoticias"]');
                                    if (userLink) {
                                        var userSpan = userLink.querySelector('span');
                                        if (userSpan) {
                                            username = '@' + userSpan.textContent.trim().replace('@', '');
                                        }
                                    }
                                    var tweetUrl = '';
                                    var timeElem = article.querySelector('time');
                                    if (timeElem) {
                                        var link = timeElem.closest('a');
                                        if (link) {
                                            tweetUrl = link.href;
                                        }
                                    }
                                    tweets.push({
                                        text: textElem.textContent.trim(),
                                        image: img ? img.src : null,
                                        username: username,
                                        url: tweetUrl
                                    });
                                }
                            }
                            return tweets;
                        """)
                        
                        if more_tweets_js:
                            new_tweets_count = 0
                            for js_tweet in more_tweets_js:
                                if js_tweet.get('text') and len(js_tweet.get('text', '')) > 20:
                                    # Verificar duplicados
                                    is_duplicate = any(
                                        existing.get('text') == js_tweet.get('text', '') 
                                        for existing in tweets
                                    )
                                    if not is_duplicate:
                                        tweet_data = {
                                            'platform': 'twitter',
                                            'username': js_tweet.get('username', '@RPPNoticias'),
                                            'text': js_tweet.get('text', ''),
                                            'cleaned_text': js_tweet.get('text', '').strip(),
                                            'image_url': js_tweet.get('image'),
                                            'video_url': None,
                                            'url': js_tweet.get('url', ''),
                                            'date': datetime.now().isoformat(),
                                            'created_at': datetime.now().isoformat(),
                                            'likes': 0,
                                            'retweets': 0,
                                            'replies': 0,
                                            'hashtags': re.findall(r'#\w+', js_tweet.get('text', '')),
                                            'scraped_at': datetime.now().isoformat()
                                        }
                                        tweets.append(tweet_data)
                                        new_tweets_count += 1
                            
                            if new_tweets_count > 0:
                                logger.info(f"✅ Extraídos {new_tweets_count} tweets adicionales después de scroll {i+1} (total: {len(tweets)})")
                    except Exception as e:
                        logger.debug(f"⚠️ Error extrayendo tweets después de scroll: {e}")
            
            tweets_after_scrolls = len(tweets)
            if tweets_after_scrolls > tweets_before_scrolls:
                logger.info(f"✅ ✅ ✅ Después de scrolls: {tweets_after_scrolls - tweets_before_scrolls} tweets nuevos (total: {tweets_after_scrolls})")
            
            time.sleep(2)  # Esperar después de scrolls
            
            # PRIORIDAD: Intentar extraer tweets con Selenium después de scrolls
            logger.info("🔍 🔍 🔍 BUSCANDO TWEETS CON SELENIUM DESPUÉS DE SCROLLS...")
            try:
                # Buscar tweets usando Selenium - MÚLTIPLES INTENTOS
                tweet_elements_selenium = []
                
                # Intentar múltiples selectores en orden de prioridad
                selectors_to_try = [
                    'article[data-testid="tweet"]',
                    'article[role="article"]',
                    'article',
                    'div[data-testid="tweet"]',
                    'div[role="article"]'
                ]
                
                for selector in selectors_to_try:
                    try:
                        tweet_elements_selenium = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if tweet_elements_selenium:
                            logger.info(f"✅ ✅ ✅ Encontrados {len(tweet_elements_selenium)} elementos con selector '{selector}'!")
                            break
                    except Exception as e:
                        logger.debug(f"⚠️ Selector '{selector}' falló: {e}")
                        continue
                
                if tweet_elements_selenium:
                    logger.info(f"✅ ✅ ✅ Encontrados {len(tweet_elements_selenium)} tweets con SELENIUM DIRECTO!")
                    # Extraer tweets directamente con Selenium
                    for tweet_elem in tweet_elements_selenium[:max_tweets]:
                        try:
                            # Extraer texto
                            text_elem = tweet_elem.find_elements(By.CSS_SELECTOR, '[data-testid="tweetText"]')
                            if not text_elem:
                                text_elem = tweet_elem.find_elements(By.CSS_SELECTOR, 'span[dir="auto"]')
                            
                            text = ""
                            if text_elem:
                                # Combinar todos los textos
                                text_parts = [elem.text.strip() for elem in text_elem if elem.text.strip()]
                                text = ' '.join(text_parts)
                            
                            # Si no hay texto suficiente, intentar obtener todo el texto del elemento
                            if not text or len(text) < 20:
                                text = tweet_elem.text.strip()
                                # Limpiar texto (remover botones, métricas, etc.)
                                lines = text.split('\n')
                                # Buscar la línea más larga que probablemente sea el contenido
                                text = max([line for line in lines if len(line) > 30], key=len, default=text)
                            
                            if text and len(text) > 20:
                                # Extraer username
                                username = "@RPPNoticias"  # Default
                                try:
                                    user_links = tweet_elem.find_elements(By.CSS_SELECTOR, 'a[href*="/"]')
                                    for link in user_links:
                                        href = link.get_attribute('href')
                                        if href and '/RPPNoticias' in href:
                                            username_elem = link.find_elements(By.CSS_SELECTOR, 'span')
                                            if username_elem:
                                                username = '@' + username_elem[-1].text.strip().replace('@', '')
                                                break
                                except:
                                    pass
                                
                                # Extraer imagen
                                image_url = None
                                try:
                                    img_elem = tweet_elem.find_elements(By.CSS_SELECTOR, 'img[src*="pbs.twimg.com"]')
                                    if img_elem:
                                        for img in img_elem:
                                            src = img.get_attribute('src')
                                            if src and 'pbs.twimg.com' in src and 'profile' not in src.lower():
                                                image_url = src
                                                break
                                except:
                                    pass
                                
                                # Extraer métricas
                                likes = 0
                                retweets = 0
                                replies = 0
                                try:
                                    # Buscar botones de interacción
                                    like_btn = tweet_elem.find_elements(By.CSS_SELECTOR, '[data-testid="like"]')
                                    if like_btn:
                                        like_text = like_btn[0].text
                                        likes = self._parse_metric(like_text)
                                    
                                    retweet_btn = tweet_elem.find_elements(By.CSS_SELECTOR, '[data-testid="retweet"]')
                                    if retweet_btn:
                                        retweet_text = retweet_btn[0].text
                                        retweets = self._parse_metric(retweet_text)
                                    
                                    reply_btn = tweet_elem.find_elements(By.CSS_SELECTOR, '[data-testid="reply"]')
                                    if reply_btn:
                                        reply_text = reply_btn[0].text
                                        replies = self._parse_metric(reply_text)
                                except:
                                    pass
                                
                                # Extraer URL del tweet
                                tweet_url = ""
                                try:
                                    time_elem = tweet_elem.find_elements(By.CSS_SELECTOR, 'time')
                                    if time_elem:
                                        parent_link = time_elem[0].find_element(By.XPATH, './ancestor::a')
                                        tweet_url = parent_link.get_attribute('href')
                                except:
                                    pass
                                
                                # Crear tweet data
                                tweet_data = {
                                    'platform': 'twitter',
                                    'username': username,
                                    'text': text,
                                    'cleaned_text': text.strip(),
                                    'image_url': image_url,
                                    'video_url': None,
                                    'url': tweet_url,
                                    'date': datetime.now().isoformat(),
                                    'created_at': datetime.now().isoformat(),
                                    'likes': likes,
                                    'retweets': retweets,
                                    'replies': replies,
                                    'hashtags': re.findall(r'#\w+', text),
                                    'scraped_at': datetime.now().isoformat()
                                }
                                
                                # Verificar duplicados
                                is_duplicate = any(
                                    existing.get('text') == tweet_data.get('text') 
                                    for existing in tweets
                                )
                                if not is_duplicate:
                                    tweets.append(tweet_data)
                                    tweets_extracted += 1
                                    logger.info(f"✅ ✅ Tweet {tweets_extracted}/{max_tweets} REAL extraído: {text[:60]}...")
                                    if image_url:
                                        logger.info(f"   🖼️ Imagen REAL encontrada: {image_url[:60]}...")
                        except Exception as e:
                            logger.debug(f"⚠️ Error extrayendo tweet individual: {e}")
                            continue
                    
                    if tweets and len(tweets) > 0:
                        logger.info(f"✅ ✅ ✅ EXTRACCIÓN DIRECTA CON SELENIUM EXITOSA: {len(tweets)} tweets REALES!")
                        # Cerrar driver antes de retornar para evitar problemas de conexión
                        try:
                            self.driver.quit()
                        except:
                            pass
                        return tweets[:max_tweets]
            except Exception as e:
                logger.warning(f"⚠️ Método directo con Selenium falló: {e}")
                # Si hay un error de conexión, intentar extraer lo que podamos antes de que se cierre
                if 'Connection' in str(e) or 'refused' in str(e):
                    logger.warning("⚠️ Driver se cerró prematuramente, intentando extraer del HTML guardado...")
                    try:
                        # Intentar extraer del page_source que ya tenemos
                        page_source = self.driver.page_source if self.driver else None
                        if page_source:
                            soup = BeautifulSoup(page_source, 'html.parser')
                            tweet_elements = soup.find_all('article', {'data-testid': 'tweet'})
                            if not tweet_elements:
                                tweet_elements = soup.find_all('article')
                            
                            for tweet_elem in tweet_elements[:max_tweets]:
                                tweet_data = self._extract_tweet_data(tweet_elem)
                                if tweet_data and tweet_data.get('text') and len(tweet_data.get('text', '')) > 20:
                                    is_duplicate = any(existing.get('text') == tweet_data.get('text') for existing in tweets)
                                    if not is_duplicate:
                                        tweets.append(tweet_data)
                                        logger.info(f"✅ Tweet REAL extraído (HTML de respaldo): {tweet_data.get('text', '')[:60]}...")
                            
                            if tweets and len(tweets) > 0:
                                logger.info(f"✅ ✅ ✅ Extraídos {len(tweets)} tweets del HTML de respaldo!")
                                return tweets[:max_tweets]
                    except Exception as e2:
                        logger.warning(f"⚠️ Extracción de respaldo también falló: {e2}")
                logger.info("ℹ️ Continuando con método HTML estándar...")
            
            # Si ya tenemos tweets de la extracción directa, continuar con scrolls para más
            if len(tweets) > 0:
                logger.info(f"✅ Ya tenemos {len(tweets)} tweets, haciendo scrolls para obtener más...")
            
            # Scroll y extracción de tweets (método HTML como respaldo)
            tweets_extracted = len(tweets)  # Empezar con los que ya tenemos
            scroll_attempts = 0
            max_scrolls = 30  # Aumentado a 30 scrolls para cargar MÁS contenido
            
            while tweets_extracted < max_tweets and scroll_attempts < max_scrolls:
                # Esperar a que carguen los tweets - con múltiples selectores
                try:
                    WebDriverWait(self.driver, 15).until(
                        EC.any_of(
                            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="tweet"]')),
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'article')),
                            EC.presence_of_element_located((By.CSS_SELECTOR, '[role="article"]'))
                        )
                    )
                except TimeoutException:
                    logger.warning("⚠️ No se encontraron tweets con selectores estándar, intentando scroll...")
                    # Intentar scroll para cargar contenido
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)
                
                # Obtener HTML de la página
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # Extraer tweets del HTML - múltiples selectores
                tweet_elements = soup.find_all('article', {'data-testid': 'tweet'})
                
                # Si no encuentra con el selector estándar, intentar otros
                if not tweet_elements:
                    # Intentar con selectores más generales
                    tweet_elements = soup.find_all('article')
                    logger.info(f"Encontrados {len(tweet_elements)} elementos article alternativos")
                    
                    # Si aún no hay, intentar con divs que contengan data-testid
                    if not tweet_elements:
                        tweet_elements = soup.find_all('div', {'data-testid': True})
                        logger.info(f"Encontrados {len(tweet_elements)} elementos div con data-testid")
                
                # Intentar extraer tweets de cualquier elemento encontrado
                for tweet_element in tweet_elements:
                    if tweets_extracted >= max_tweets:
                        break
                    
                    tweet_data = self._extract_tweet_data(tweet_element)
                    if tweet_data and tweet_data.get('text'):
                        # Verificar que no sea duplicado
                        is_duplicate = any(
                            existing.get('text') == tweet_data.get('text') 
                            for existing in tweets
                        )
                        if not is_duplicate:
                            tweets.append(tweet_data)
                            tweets_extracted += 1
                            logger.info(f"✅ Tweet {tweets_extracted}/{max_tweets} extraído: {tweet_data.get('text', '')[:50]}...")
                
                # Scroll para cargar más tweets
                if tweets_extracted < max_tweets:
                    # Hacer scroll múltiple para cargar más contenido
                    for _ in range(2):
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2)
                    time.sleep(self.delay)  # Delay responsable entre scrolls
                    scroll_attempts += 1
                else:
                    break  # Si ya tenemos suficientes tweets, salir
            
            logger.info(f"✅ Total de tweets extraídos hasta ahora: {len(tweets)}")
            
            # Si no se encontraron tweets, intentar extraer del HTML inicial guardado
            if len(tweets) == 0:
                logger.warning("⚠️ No se encontraron tweets con métodos activos, intentando extraer del HTML inicial guardado...")
                try:
                    soup = BeautifulSoup(initial_html, 'html.parser')
                    tweet_elements = soup.find_all('article', {'data-testid': 'tweet'})
                    if not tweet_elements:
                        tweet_elements = soup.find_all('article')
                    
                    logger.info(f"📊 HTML inicial tiene {len(tweet_elements)} elementos article")
                    
                    for tweet_elem in tweet_elements[:max_tweets]:
                        tweet_data = self._extract_tweet_data(tweet_elem)
                        if tweet_data and tweet_data.get('text') and len(tweet_data.get('text', '')) > 20:
                            is_duplicate = any(existing.get('text') == tweet_data.get('text') for existing in tweets)
                            if not is_duplicate:
                                tweets.append(tweet_data)
                                logger.info(f"✅ Tweet REAL extraído (HTML inicial): {tweet_data.get('text', '')[:60]}...")
                    
                    if tweets and len(tweets) > 0:
                        logger.info(f"✅ ✅ ✅ Extraídos {len(tweets)} tweets del HTML inicial guardado!")
                except Exception as e:
                    logger.warning(f"⚠️ Extracción del HTML inicial falló: {e}")
            
            if tweets and len(tweets) > 0:
                # Limitar al máximo solicitado solo al final
                final_tweets = tweets[:max_tweets] if len(tweets) > max_tweets else tweets
                logger.info(f"✅ ✅ ✅ TOTAL FINAL: {len(tweets)} tweets encontrados, retornando {len(final_tweets)} tweets REALES")
                # Log algunos tweets para verificar
                for i, tweet in enumerate(final_tweets[:5], 1):
                    logger.info(f"   Tweet {i}: {tweet.get('text', '')[:80]}...")
                    if tweet.get('image_url'):
                        logger.info(f"      🖼️ Imagen REAL: {tweet.get('image_url', '')[:60]}...")
                
                # Cerrar driver antes de retornar
                try:
                    self.driver.quit()
                    logger.info("✅ Driver cerrado correctamente")
                except:
                    pass
                
                return final_tweets
            else:
                logger.warning(f"⚠️ ⚠️ ⚠️ No se pudieron extraer tweets REALES de {url}")
                logger.warning(f"⚠️ Twitter/X puede requerir autenticación para ver este contenido")
                
                # Cerrar driver antes de retornar
                try:
                    self.driver.quit()
                except:
                    pass
            
            return tweets
            
        except Exception as e:
            logger.error(f"❌ Error en scraping desde URL: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return tweets
    
    def search_tweets(self, 
                     query: str, 
                     max_tweets: int = 50,
                     filter_language: Optional[str] = None) -> List[Dict]:
        """
        Buscar tweets públicos según parámetros
        
        Args:
            query: Hashtag o palabra clave a buscar
            max_tweets: Máximo de tweets a extraer (máx 50 para no sobrecargar)
            filter_language: Filtrar por idioma (ej: 'es', 'en')
        
        Returns:
            Lista de diccionarios con datos de tweets
        """
        # Sin límite para fines académicos
        if max_tweets < 1:
            max_tweets = 10  # Mínimo 1 tweet
        
        tweets = []
        query = query.strip()
        
        # Limpiar query: remover # si está presente (se agregará en la URL)
        if query.startswith('#'):
            query = query[1:]
        
        try:
            # Construir URL de búsqueda
            search_url = f"https://twitter.com/search?q={query}&src=typed_query&f=live"
            if filter_language:
                search_url += f"&lang={filter_language}"
            
            logger.info(f"🔍 Buscando tweets con query: {query}")
            logger.info(f"📋 URL: {search_url}")
            
            # Configurar timeout
            self.driver.set_page_load_timeout(30)  # 30 segundos máximo para cargar página
            self.driver.implicitly_wait(10)  # Esperar hasta 10 segundos para elementos
            
            self.driver.get(search_url)
            logger.info(f"✅ Página de búsqueda cargada")
            time.sleep(self.delay)  # Delay responsable
            
            # Verificar si la página cargó correctamente
            page_source = self.driver.page_source
            if 'Sign in' in page_source or 'Iniciar sesión' in page_source or 'login' in page_source.lower() or 'Inicia sesión' in page_source:
                logger.warning("⚠️ Twitter/X requiere autenticación. Intentando continuar...")
                # Intentar seguir de todas formas por si hay contenido visible
                time.sleep(2)  # Dar tiempo para que cargue lo que pueda
            
            # Scroll y extracción de tweets
            tweets_extracted = 0
            scroll_attempts = 0
            max_scrolls = 10  # Límite de scrolls
            
            while tweets_extracted < max_tweets and scroll_attempts < max_scrolls:
                # Esperar a que carguen los tweets
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="tweet"]'))
                    )
                except TimeoutException:
                    logger.warning("⚠️ No se encontraron tweets con selector estándar, intentando métodos alternativos...")
                    # Intentar scroll para cargar contenido
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)
                
                # Obtener HTML de la página
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # Extraer tweets del HTML - múltiples selectores
                tweet_elements = soup.find_all('article', {'data-testid': 'tweet'})
                
                # Si no encuentra con el selector estándar, intentar otros
                if not tweet_elements:
                    # Intentar con selectores más generales
                    tweet_elements = soup.find_all('article')
                    logger.info(f"Encontrados {len(tweet_elements)} elementos article alternativos")
                    
                    # Si aún no hay, intentar con divs que contengan data-testid
                    if not tweet_elements:
                        tweet_elements = soup.find_all('div', {'data-testid': True})
                        logger.info(f"Encontrados {len(tweet_elements)} elementos div con data-testid")
                
                # Intentar extraer tweets de cualquier elemento encontrado
                for tweet_element in tweet_elements:
                    if tweets_extracted >= max_tweets:
                        break
                    
                    tweet_data = self._extract_tweet_data(tweet_element)
                    if tweet_data and tweet_data.get('text'):
                        # Verificar que no sea duplicado
                        is_duplicate = any(
                            existing.get('text') == tweet_data.get('text') 
                            for existing in tweets
                        )
                        if not is_duplicate:
                            tweets.append(tweet_data)
                            tweets_extracted += 1
                            logger.info(f"✅ Tweet {tweets_extracted}/{max_tweets} extraído: {tweet_data.get('text', '')[:50]}...")
                
                # Scroll para cargar más tweets
                if tweets_extracted < max_tweets:
                    # Hacer scroll múltiple para cargar más contenido
                    for _ in range(2):
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2)
                    time.sleep(self.delay)  # Delay responsable entre scrolls
                    scroll_attempts += 1
                else:
                    break  # Si ya tenemos suficientes tweets, salir
            
            logger.info(f"✅ Total de tweets extraídos: {len(tweets)}")
            return tweets
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda de tweets: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return tweets
        finally:
            # Cerrar driver después de un delay
            time.sleep(2)
    
    def _extract_tweet_data(self, tweet_element) -> Optional[Dict]:
        """
        Extraer datos de un elemento de tweet - Versión mejorada con múltiples métodos
        
        Args:
            tweet_element: Elemento BeautifulSoup del tweet
        
        Returns:
            Diccionario con datos del tweet o None si hay error
        """
        try:
            # ===== MÉTODO 1: Extraer texto completo del tweet (MEJORADO) =====
            text = ""
            
            # Selector estándar - PRIORITARIO
            text_elem = tweet_element.find('div', {'data-testid': 'tweetText'})
            if text_elem:
                # Obtener todo el texto, incluyendo spans anidados
                text = text_elem.get_text(separator=' ', strip=True)
                # Remover "Show more" o "Ver más" del texto si está presente
                text = re.sub(r'\s*(Show more|Ver más|Read more)\s*$', '', text, flags=re.IGNORECASE)
            
            # Si no funcionó, intentar con span
            if not text or len(text) < 10:
                text_spans = tweet_element.find_all('span', {'data-testid': 'tweetText'})
                if text_spans:
                    # Combinar todos los spans de texto
                    text_parts = [span.get_text(strip=True) for span in text_spans if span.get_text(strip=True)]
                    text = ' '.join(text_parts)
                    # Remover "Show more" del texto
                    text = re.sub(r'\s*(Show more|Ver más|Read more)\s*$', '', text, flags=re.IGNORECASE)
            
            # Si aún no funciona, buscar cualquier span con texto largo (MEJORADO)
            if not text or len(text) < 10:
                all_spans = tweet_element.find_all('span')
                candidate_texts = []
                for span in all_spans:
                    span_text = span.get_text(strip=True)
                    # Filtrar textos muy cortos o que parecen UI
                    if (len(span_text) > 30 and 
                        not span_text.startswith('@') and 
                        '·' not in span_text and
                        not span_text.lower() in ['show more', 'ver más', 'read more', 'reply', 'retweet', 'like']):
                        candidate_texts.append(span_text)
                
                # Si hay múltiples candidatos, usar el más largo (probablemente el contenido principal)
                if candidate_texts:
                    text = max(candidate_texts, key=len)
            
            # Si aún no hay texto, intentar con divs (MEJORADO)
            if not text or len(text) < 10:
                all_divs = tweet_element.find_all('div')
                candidate_divs = []
                for div in all_divs:
                    div_text = div.get_text(separator=' ', strip=True)
                    # Filtrar por tamaño razonable y contenido
                    if (len(div_text) > 30 and len(div_text) < 5000 and  # Tamaño razonable
                        any(c.isalpha() for c in div_text)):  # Debe tener letras
                        candidate_divs.append(div_text)
                
                # Usar el texto más largo que no sea duplicado
                if candidate_divs:
                    # Remover duplicados y usar el más largo
                    unique_texts = []
                    for t in candidate_divs:
                        if t not in unique_texts and len(t) > 30:
                            unique_texts.append(t)
                    if unique_texts:
                        text = max(unique_texts, key=len)
            
            # Limpiar espacios múltiples y caracteres extra
            if text:
                text = re.sub(r'\s+', ' ', text).strip()
            
            # ===== MÉTODO 2: Extraer username (múltiples métodos) =====
            username = ""
            
            # Método 1: Buscar enlaces con patrones de usuario
            user_links = tweet_element.find_all('a', href=re.compile(r'/([\w]+)$'))
            for link in user_links:
                href = link.get('href', '')
                # Excluir hashtags y otros enlaces especiales
                if href and not any(x in href for x in ['/hashtag/', '/i/', '/search', '/settings']):
                    username = '@' + href.lstrip('/')
                    break
            
            # Método 2: Buscar texto que empiece con @
            if not username:
                text_elements = tweet_element.find_all(string=re.compile(r'@[\w]+'))
                for elem in text_elements:
                    if elem.strip().startswith('@'):
                        username = elem.strip()
                        break
            
            # Método 3: Buscar en atributos aria-label
            if not username:
                aria_labels = tweet_element.find_all(attrs={'aria-label': re.compile(r'@[\w]+')})
                if aria_labels:
                    username = aria_labels[0].get('aria-label', '')
            
            # ===== MÉTODO 3: Extraer fecha =====
            date_str = ""
            time_elem = tweet_element.find('time')
            if time_elem:
                date_str = time_elem.get('datetime', '')
                if not date_str:
                    date_str = time_elem.get_text(strip=True)
            
            # Si no hay fecha, intentar con atributos data-time
            if not date_str:
                time_attrs = tweet_element.find_all(attrs={'data-time': True})
                if time_attrs:
                    date_str = time_attrs[0].get('data-time', '')
            
            # ===== MÉTODO 4: Extraer métricas (likes, retweets, replies) - MEJORADO =====
            likes = 0
            retweets = 0
            replies = 0
            
            # Selectores específicos para métricas de Twitter/X
            # Likes
            like_selectors = [
                ('span', {'data-testid': 'like'}),
                ('button', {'data-testid': 'like'}),
                ('div', {'aria-label': re.compile(r'like|me gusta', re.I)}),
            ]
            
            # Retweets
            retweet_selectors = [
                ('span', {'data-testid': 'retweet'}),
                ('button', {'data-testid': 'retweet'}),
                ('div', {'aria-label': re.compile(r'retweet|retuite', re.I)}),
            ]
            
            # Replies
            reply_selectors = [
                ('span', {'data-testid': 'reply'}),
                ('button', {'data-testid': 'reply'}),
                ('div', {'aria-label': re.compile(r'reply|respuesta', re.I)}),
            ]
            
            # Extraer likes
            for tag, attrs in like_selectors:
                elements = tweet_element.find_all(tag, attrs)
                for elem in elements:
                    elem_text = elem.get_text(strip=True)
                    metric_value = self._parse_metric(elem_text)
                    if metric_value > 0:
                        likes = metric_value
                        break
                if likes > 0:
                    break
            
            # Extraer retweets
            for tag, attrs in retweet_selectors:
                elements = tweet_element.find_all(tag, attrs)
                for elem in elements:
                    elem_text = elem.get_text(strip=True)
                    metric_value = self._parse_metric(elem_text)
                    if metric_value > 0:
                        retweets = metric_value
                        break
                if retweets > 0:
                    break
            
            # Extraer replies
            for tag, attrs in reply_selectors:
                elements = tweet_element.find_all(tag, attrs)
                for elem in elements:
                    elem_text = elem.get_text(strip=True)
                    metric_value = self._parse_metric(elem_text)
                    if metric_value > 0:
                        replies = metric_value
                        break
                if replies > 0:
                    break
            
            # Fallback: Buscar en spans genéricos si no se encontraron con selectores específicos
            if likes == 0 or retweets == 0 or replies == 0:
                all_spans = tweet_element.find_all('span')
                for span in all_spans:
                    span_text = span.get_text(strip=True)
                    parent = span.find_parent()
                    parent_text = parent.get_text().lower() if parent else ""
                    parent_aria = parent.get('aria-label', '').lower() if parent else ""
                    combined_context = parent_text + ' ' + parent_aria
                    
                    # Intentar parsear el número
                    metric_value = self._parse_metric(span_text)
                    
                    if metric_value > 0:
                        # Determinar qué tipo de métrica es basado en contexto
                        if likes == 0 and any(keyword in combined_context for keyword in ['like', 'me gusta', 'favorit', 'gusta']):
                            likes = metric_value
                        elif retweets == 0 and any(keyword in combined_context for keyword in ['retweet', 'retuite', 'retuit']):
                            retweets = metric_value
                        elif replies == 0 and any(keyword in combined_context for keyword in ['reply', 'respuesta', 'comentar', 'responder']):
                            replies = metric_value
            
            # ===== MÉTODO 5: Extraer hashtags =====
            hashtags = []
            hashtag_links = tweet_element.find_all('a', href=re.compile(r'/hashtag/'))
            for link in hashtag_links:
                hashtag = link.get_text(strip=True)
                if hashtag.startswith('#'):
                    hashtags.append(hashtag)
                elif hashtag:
                    hashtags.append('#' + hashtag)
            
            # También buscar hashtags en el texto
            if text:
                hashtag_pattern = r'#\w+'
                found_hashtags = re.findall(hashtag_pattern, text)
                for tag in found_hashtags:
                    if tag not in hashtags:
                        hashtags.append(tag)
            
            # ===== MÉTODO 6: Extraer URL del tweet =====
            tweet_url = ""
            tweet_link = tweet_element.find('a', href=re.compile(r'/[\w]+/status/\d+'))
            if tweet_link:
                href = tweet_link.get('href', '')
                if href.startswith('http'):
                    tweet_url = href
                else:
                    tweet_url = "https://twitter.com" + href
            
            # ===== MÉTODO 7: Extraer imagen del tweet (MEJORADO con validación) =====
            image_url = None
            
            # Buscar imágenes en el tweet - PRIORIZAR IMÁGENES DE CONTENIDO
            # Método 1: Buscar en divs con data-testid específicos de media
            media_elements = tweet_element.find_all('div', {'data-testid': re.compile(r'.*media|.*image|.*photo')})
            for media_elem in media_elements:
                img = media_elem.find('img')
                if img:
                    img_src = img.get('src', '') or img.get('data-src', '') or img.get('data-lazy-src', '')
                    if img_src and ('pbs.twimg.com' in img_src or 'twimg.com' in img_src):
                        # Validar URL
                        if self._validate_image_url(img_src):
                            # Limpiar parámetros de la URL para obtener imagen de mejor calidad
                            if '?' in img_src:
                                base_url = img_src.split('?')[0]
                                # Intentar obtener versión de mejor calidad
                                image_url = base_url + '?format=jpg&name=large'
                            else:
                                image_url = img_src
                            break
            
            # Método 2: Buscar tags img directamente (filtrar avatares)
            if not image_url:
                img_tags = tweet_element.find_all('img')
                content_images = []
                for img in img_tags:
                    img_src = img.get('src', '') or img.get('data-src', '') or img.get('data-lazy-src', '')
                    if img_src and ('pbs.twimg.com' in img_src or 'twimg.com' in img_src):
                        # Filtrar imágenes de perfil/avatar (suelen ser pequeñas o tener patrones específicos)
                        is_avatar = (
                            'profile_images' in img_src or
                            'avatar' in img_src.lower() or
                            'profile' in img_src.lower() or
                            img_src.count('/') > 8  # URLs de perfil suelen tener más niveles
                        )
                        if not is_avatar and self._validate_image_url(img_src):
                            content_images.append(img_src)
                
                # Si hay imágenes de contenido, usar la primera válida
                if content_images:
                    image_url = content_images[0]
                    # Intentar obtener mejor calidad
                    if '?' in image_url:
                        base_url = image_url.split('?')[0]
                        image_url = base_url + '?format=jpg&name=large'
            
            # Método 3: Buscar en elementos con background-image
            if not image_url:
                all_elements = tweet_element.find_all(attrs={'style': re.compile(r'background-image')})
                for elem in all_elements:
                    style = elem.get('style', '')
                    url_match = re.search(r'url\(["\']?([^"\']+)["\']?\)', style)
                    if url_match:
                        img_url = url_match.group(1)
                        if ('pbs.twimg.com' in img_url or 'twimg.com' in img_url) and self._validate_image_url(img_url):
                            image_url = img_url
                            break
            
            # Validar URL final antes de retornar
            if image_url and not self._validate_image_url(image_url):
                logger.debug(f"⚠️ URL de imagen no válida, descartando: {image_url[:50]}...")
                image_url = None
            
            # Construir objeto de datos
            tweet_data = {
                'platform': 'twitter',
                'username': username or 'unknown',
                'text': text,
                'date': date_str or datetime.now().isoformat(),
                'likes': likes,
                'retweets': retweets,
                'replies': replies,
                'hashtags': hashtags,
                'url': tweet_url,
                'image_url': image_url,  # Agregar imagen extraída
                'scraped_at': datetime.now().isoformat()
            }
            
            # Retornar si tiene texto o al menos username
            return tweet_data if (text or username != 'unknown') else None
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo datos del tweet: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return None
    
    def _expand_collapsed_content(self, driver, post_element_selenium=None, retries: int = 3) -> bool:
        """
        Expandir contenido colapsado ("Ver más", "Read more", "Show more")
        
        Args:
            driver: Selenium WebDriver
            post_element_selenium: Elemento Selenium del post (opcional)
            retries: Número de intentos
        
        Returns:
            True si se expandió contenido, False en caso contrario
        """
        try:
            # Selectores para botones "Ver más" / "Read more"
            expand_selectors = [
                "//span[contains(text(), 'Ver más')]",
                "//span[contains(text(), 'Show more')]",
                "//span[contains(text(), 'Read more')]",
                "//button[contains(text(), 'Ver más')]",
                "//button[contains(text(), 'Show more')]",
                "//button[contains(text(), 'Read more')]",
                "//a[contains(text(), 'Ver más')]",
                "//a[contains(text(), 'Show more')]",
                "//a[contains(text(), 'Read more')]",
                "//div[@data-testid='tweetText']//span[contains(text(), 'Show')]",
                "//div[contains(@class, 'tweet-text')]//span[contains(text(), 'more')]",
                "//*[contains(@class, 'expand')]",
                "//*[contains(@class, 'show-more')]",
                "//*[@role='button' and contains(text(), 'more')]",
            ]
            
            for attempt in range(retries):
                for selector in expand_selectors:
                    try:
                        # Si se proporciona un elemento específico, buscar dentro de él
                        if post_element_selenium:
                            elements = post_element_selenium.find_elements(By.XPATH, selector)
                        else:
                            elements = driver.find_elements(By.XPATH, selector)
                        
                        for element in elements:
                            try:
                                # Verificar que el elemento sea visible y clickeable
                                if element.is_displayed() and element.is_enabled():
                                    # Scroll hasta el elemento
                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                    time.sleep(0.5)
                                    
                                    # Intentar hacer clic
                                    driver.execute_script("arguments[0].click();", element)
                                    logger.debug(f"✅ Contenido expandido con selector: {selector[:50]}...")
                                    time.sleep(1)  # Esperar a que se expanda
                                    return True
                            except Exception as e:
                                logger.debug(f"⚠️ No se pudo expandir con selector {selector}: {e}")
                                continue
                    except Exception as e:
                        logger.debug(f"⚠️ Error con selector {selector}: {e}")
                        continue
                
                # Si no se encontró nada, esperar un poco antes de reintentar
                if attempt < retries - 1:
                    time.sleep(1)
            
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ Error expandiendo contenido colapsado: {e}")
            return False
    
    def _validate_image_url(self, url: str) -> bool:
        """
        Validar que una URL de imagen sea accesible y válida
        
        Args:
            url: URL de la imagen
        
        Returns:
            True si la URL es válida, False en caso contrario
        """
        if not url or not isinstance(url, str):
            return False
        
        # Verificar formato básico de URL
        if not url.startswith(('http://', 'https://')):
            return False
        
        # Verificar que no sea una imagen de placeholder o demo
        invalid_patterns = [
            'picsum.photos',
            'placeholder',
            'unsplash.com/source',
            'via.placeholder.com',
            'dummyimage.com',
            'loremflickr.com',
            'fakeimg.pl'
        ]
        
        if any(pattern in url.lower() for pattern in invalid_patterns):
            logger.debug(f"⚠️ URL de imagen parece ser placeholder: {url[:50]}...")
            return False
        
        # Verificar que sea de un dominio conocido de la plataforma
        valid_patterns = [
            'pbs.twimg.com',  # Twitter
            'twimg.com',      # Twitter
            'fbcdn.net',      # Facebook
            'scontent',       # Facebook CDN
            'facebook.com'
        ]
        
        if any(pattern in url for pattern in valid_patterns):
            return True
        
        # Si no es de un dominio conocido pero parece válida, aceptarla
        return True
    
    def _parse_metric(self, metric_str: str) -> int:
        """
        Parsear métricas con formato K, M, B mejorado (ej: "1.2K" -> 1200, "5M" -> 5000000)
        
        Args:
            metric_str: String con la métrica (ej: "1.2K", "500", "2.5M", "1.5K")
        
        Returns:
            Número entero de la métrica
        """
        try:
            if not metric_str or not isinstance(metric_str, str):
                return 0
            
            # Limpiar el string
            metric_str = metric_str.strip().replace(',', '').replace(' ', '').upper()
            
            if not metric_str:
                return 0
            
            # Manejar formato K (miles)
            if 'K' in metric_str:
                number_str = metric_str.replace('K', '').replace('K', '')
                try:
                    number = float(number_str)
                    return int(number * 1000)
                except ValueError:
                    return 0
            
            # Manejar formato M (millones)
            elif 'M' in metric_str:
                number_str = metric_str.replace('M', '').replace('M', '')
                try:
                    number = float(number_str)
                    return int(number * 1000000)
                except ValueError:
                    return 0
            
            # Manejar formato B (billones)
            elif 'B' in metric_str:
                number_str = metric_str.replace('B', '').replace('B', '')
                try:
                    number = float(number_str)
                    return int(number * 1000000000)
                except ValueError:
                    return 0
            
            # Manejar números normales
            else:
                try:
                    return int(float(metric_str))
                except ValueError:
                    return 0
                    
        except Exception as e:
            logger.debug(f"⚠️ Error parseando métrica '{metric_str}': {e}")
            return 0
    
    def close(self):
        """Cerrar el driver del navegador"""
        if self.driver:
            self.driver.quit()
            logger.info("✅ Driver cerrado correctamente")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


class FacebookScraper:
    """
    Scraper educativo para Facebook
    
    IMPORTANTE: Este código es solo para fines académicos y educativos.
    Respeta los términos de servicio de Facebook y las leyes locales.
    
    Ahora intenta usar Graph API primero (más confiable), luego Selenium como fallback.
    """
    
    def __init__(self, headless: bool = True, delay: int = 5, access_token: Optional[str] = None):
        """
        Inicializar el scraper de Facebook
        
        Args:
            headless: Si True, ejecuta el navegador en modo headless
            delay: Delay entre requests en segundos (mínimo 3 para ser responsable)
            access_token: Token de acceso de Facebook Graph API (opcional)
        """
        self.delay = max(delay, 3)  # Mínimo 3 segundos por ética
        self.headless = headless
        self.driver = None
        self.access_token = access_token
        self._setup_driver()
        
        # Intentar cargar Graph API scraper
        self.graph_scraper = None
        try:
            from facebook_graph_scraper import FacebookGraphScraper
            if self.access_token:
                self.graph_scraper = FacebookGraphScraper(self.access_token)
                logger.info("✅ Graph API scraper disponible")
            else:
                # Intentar obtener de variables de entorno
                import os
                env_token = os.getenv('FACEBOOK_ACCESS_TOKEN') or os.getenv('FB_ACCESS_TOKEN')
                if env_token:
                    self.graph_scraper = FacebookGraphScraper(env_token)
                    logger.info("✅ Graph API scraper disponible (desde env)")
                else:
                    logger.info("ℹ️ Graph API no disponible (sin token), usando Selenium como fallback")
        except ImportError:
            logger.warning("⚠️ facebook_graph_scraper no disponible, usando solo Selenium")
        except Exception as e:
            logger.warning(f"⚠️ Error cargando Graph API scraper: {e}, usando Selenium")
    
    def _simulate_human_typing(self, element, text):
        """
        Simular escritura humana escribiendo cada carácter uno por uno
        con delays aleatorios de 0.1 a 0.3 segundos
        """
        try:
            element.clear()
            for char in text:
                element.send_keys(char)
                # Delay aleatorio entre 0.1 y 0.3 segundos
                time.sleep(random.uniform(0.1, 0.3))
        except Exception as e:
            logger.warning(f"⚠️ Error simulando escritura humana: {e}")
            # Fallback: escribir normal
            element.clear()
            element.send_keys(text)
    
    def _setup_driver(self):
        """
        Configurar el driver con mejor anti-detección
        Prioridad: undetected-chromedriver > Playwright > Edge > Chrome
        """
        try:
            # PRIORIDAD 1: Intentar undetected-chromedriver (más difícil de detectar)
            if UC_AVAILABLE:
                try:
                    logger.info("🔧 Intentando usar undetected-chromedriver (más difícil de detectar)...")
                    options = uc.ChromeOptions()
                    
                    # FORZAR modo visible para permitir login manual
                    # NO usar headless para Facebook
                    if self.headless:
                        logger.warning("⚠️ ⚠️ ⚠️ headless=True pero FORZANDO modo visible para permitir login")
                        logger.info("👁️ El navegador se abrirá VISIBLE para que puedas hacer login si es necesario")
                        # NO agregar --headless para que sea visible
                    
                    options.add_argument('--no-sandbox')
                    options.add_argument('--disable-dev-shm-usage')
                    options.add_argument('--disable-blink-features=AutomationControlled')
                    options.add_argument('--disable-features=IsolateOrigins,site-per-process')
                    
                    # User agent realista
                    options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                    
                    # Preferencias
                    prefs = {
                        "credentials_enable_service": False,
                        "profile.password_manager_enabled": False,
                        "profile.default_content_setting_values.notifications": 2
                    }
                    options.add_experimental_option("prefs", prefs)
                    
                    self.driver = uc.Chrome(options=options, version_main=None, use_subprocess=True)
                    logger.info("✅ ✅ ✅ undetected-chromedriver configurado correctamente (más difícil de detectar)")
                    logger.info("👁️ 👁️ 👁️ NAVEGADOR VISIBLE - Deberías ver una ventana de Chrome ahora")
                    # Asegurar que la ventana esté visible y enfocada
                    try:
                        self.driver.maximize_window()
                        logger.info("✅ Ventana maximizada para mejor visibilidad")
                    except:
                        pass
                    return
                    
                except Exception as uc_error:
                    logger.warning(f"⚠️ undetected-chromedriver falló: {uc_error}, usando método alternativo...")
            
            # PRIORIDAD 2: Intentar Edge (mejor que Chrome para Facebook)
            try:
                logger.info("🔧 Intentando usar Edge...")
                edge_options = EdgeOptions()
                
                # FORZAR modo visible para permitir login manual
                # NO usar headless para Facebook
                if self.headless:
                    logger.warning("⚠️ ⚠️ ⚠️ headless=True pero FORZANDO modo visible para permitir login")
                    logger.info("👁️ El navegador se abrirá VISIBLE para que puedas hacer login si es necesario")
                    # NO agregar --headless para que sea visible
                
                # Opciones avanzadas anti-detección
                edge_options.add_argument('--no-sandbox')
                edge_options.add_argument('--disable-dev-shm-usage')
                edge_options.add_argument('--disable-blink-features=AutomationControlled')
                edge_options.add_argument('--disable-features=IsolateOrigins,site-per-process')
                edge_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
                edge_options.add_experimental_option('useAutomationExtension', False)
                
                # User agent realista
                edge_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0')
                
                # Preferencias
                prefs = {
                    "credentials_enable_service": False,
                    "profile.password_manager_enabled": False,
                    "profile.default_content_setting_values.notifications": 2
                }
                edge_options.add_experimental_option("prefs", prefs)
                
                # Usar Edge Chromium Driver
                service = EdgeService(EdgeChromiumDriverManager().install())
                self.driver = webdriver.Edge(service=service, options=edge_options)
                
                logger.info("👁️ 👁️ 👁️ NAVEGADOR VISIBLE - Deberías ver una ventana de Edge ahora")
                # Asegurar que la ventana esté visible y enfocada
                try:
                    self.driver.maximize_window()
                    logger.info("✅ Ventana maximizada para mejor visibilidad")
                except:
                    pass
                
                # Técnicas anti-detección avanzadas
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
                self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['es-ES', 'es', 'en-US', 'en']})")
                
                logger.info("✅ Driver de Edge configurado correctamente")
                return
                
            except Exception as edge_error:
                logger.warning(f"⚠️ Edge no disponible: {edge_error}, usando Chrome...")
            
            # PRIORIDAD 3: Fallback a Chrome estándar
            logger.info("🔧 Usando Chrome estándar como fallback...")
            chrome_options = Options()
            
            # FORZAR modo visible para permitir login manual
            # NO usar headless para Facebook
            if self.headless:
                logger.warning("⚠️ ⚠️ ⚠️ headless=True pero FORZANDO modo visible para permitir login")
                logger.info("👁️ El navegador se abrirá VISIBLE para que puedas hacer login si es necesario")
                # NO agregar --headless para que sea visible
            
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            prefs = {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
                "profile.default_content_setting_values.notifications": 2
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            logger.info("👁️ 👁️ 👁️ NAVEGADOR VISIBLE - Deberías ver una ventana de Chrome ahora")
            # Asegurar que la ventana esté visible y enfocada
            try:
                self.driver.maximize_window()
                logger.info("✅ Ventana maximizada para mejor visibilidad")
            except:
                pass
            
            # Técnicas anti-detección
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['es-ES', 'es', 'en-US', 'en']})")
            
            logger.info("✅ Driver de Chrome configurado")
            
        except Exception as e:
            logger.error(f"❌ Error configurando driver: {e}")
            raise
    
    def _try_requests_method(self, url: str, max_posts: int = 50) -> Optional[List[Dict]]:
        """
        Intentar extraer posts usando requests directamente (método alternativo)
        A veces funciona mejor que Selenium para contenido público de Facebook
        """
        try:
            logger.info(f"🔍 Intentando método alternativo (requests) para Facebook: {url}")
            
            # Headers más sofisticados para parecer un navegador real
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
                'Referer': 'https://www.facebook.com/',
            }
            
            session = requests.Session()
            session.headers.update(headers)
            
            # Intentar obtener la página con retry
            for attempt in range(3):
                try:
                    response = session.get(url, timeout=30, allow_redirects=True)
                    if response.status_code == 200:
                        break
                    elif attempt < 2:
                        logger.info(f"⚠️ Intento {attempt + 1} falló con status {response.status_code}, reintentando...")
                        time.sleep(2)
                        continue
                    else:
                        logger.warning(f"⚠️ Método requests falló: Status {response.status_code}")
                        return None
                except Exception as e:
                    if attempt < 2:
                        logger.info(f"⚠️ Intento {attempt + 1} falló: {e}, reintentando...")
                        time.sleep(2)
                        continue
                    else:
                        logger.warning(f"⚠️ Método requests falló después de 3 intentos: {e}")
                        return None
            
            # Verificar si requiere autenticación
            page_text = response.text.lower()
            if any(x in page_text for x in ['sign in', 'iniciar sesión', 'login', 'log in', 'you must log in']):
                logger.warning("⚠️ Método requests detectó que requiere autenticación")
                return None
            
            # Parsear HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Intentar encontrar posts de Facebook con métodos más agresivos
            posts = []
            post_elements = []
            
            # Buscar posts con múltiples selectores (más agresivo)
            all_divs = soup.find_all('div')
            for div in all_divs:
                # Buscar divs que parezcan posts
                text_content = div.get_text(strip=True)
                has_facebook_content = any(
                    'fbcdn.net' in str(div) or 
                    'facebook.com' in str(div) or
                    'scontent' in str(div) or
                    'data-pagelet' in str(div) or
                    'role="article"' in str(div)
                )
                
                if len(text_content) > 50 and has_facebook_content:
                    # Verificar que no sea duplicado
                    if div not in post_elements:
                        post_elements.append(div)
            
            # También buscar con selectores específicos
            post_elements.extend(soup.find_all('div', {'data-pagelet': True}))
            post_elements.extend(soup.find_all('div', {'role': 'article'}))
            post_elements.extend(soup.find_all('div', {'data-ad-preview': 'message'}))
            
            # Eliminar duplicados
            seen = set()
            unique_elements = []
            for elem in post_elements:
                elem_id = id(elem)
                if elem_id not in seen:
                    seen.add(elem_id)
                    unique_elements.append(elem)
            
            logger.info(f"📊 Encontrados {len(unique_elements)} elementos potenciales con requests")
            
            for elem in unique_elements[:max_posts * 3]:
                if len(posts) >= max_posts:
                    break
                try:
                    post_data = self._extract_post_data(elem)
                    if post_data:
                        text = post_data.get('text', '').strip()
                        image_url = post_data.get('image_url', '')
                        
                        # Rechazar imágenes simuladas
                        if image_url and any(pattern in image_url.lower() for pattern in [
                            'picsum.photos', 'unsplash', 'placeholder'
                        ]):
                            continue
                        
                        # Validar que tenga contenido significativo
                        if text and len(text) > 20:
                            posts.append(post_data)
                        elif image_url and ('fbcdn.net' in image_url or 'scontent' in image_url):
                            posts.append(post_data)
                except Exception as e:
                    logger.debug(f"⚠️ Error extrayendo post: {e}")
                    continue
            
            if posts:
                logger.info(f"✅ Método requests extrajo {len(posts)} posts REALES")
                return posts
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Método requests falló: {e}")
            return None
    
    def _close_popups(self):
        """Cierra popups de cookies y login"""
        try:
            # Buscar y cerrar popup de cookies
            cookie_buttons = [
                (By.XPATH, "//button[contains(text(), 'Allow all cookies')]"),
                (By.XPATH, "//button[contains(text(), 'Permitir todas las cookies')]"),
                (By.XPATH, "//button[@data-cookiebanner='accept_button']"),
                (By.XPATH, "//div[@aria-label='Close']"),
                (By.XPATH, "//button[contains(text(), 'Aceptar')]"),
                (By.XPATH, "//button[contains(text(), 'Accept')]"),
                (By.CSS_SELECTOR, "[aria-label='Close']"),
                (By.CSS_SELECTOR, "[data-cookiebanner='accept_button']"),
            ]
            
            for by, selector in cookie_buttons:
                try:
                    button = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    button.click()
                    time.sleep(1)
                    logger.info("✅ Popup cerrado")
                    break
                except:
                    continue
        except:
            pass
    
    def _extract_visible_posts_selenium(self, max_posts: int = 50) -> List[Dict]:
        """Extrae todos los posts visibles usando Selenium directamente"""
        new_posts = []
        
        try:
            # Selectores para posts de Facebook (actualizados 2025)
            post_selectors = [
                "div[role='article']",
                "div.x1yztbdb.x1n2onr6.xh8yej3.x1ja2u2z",
                "div[data-pagelet*='FeedUnit']",
                "div[data-pagelet]",
                "div[data-ad-preview='message']",
            ]
            
            posts_elements = []
            for selector in post_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        posts_elements = elements
                        logger.info(f"✅ Encontrados {len(elements)} elementos con selector: {selector}")
                        break
                except:
                    continue
            
            if not posts_elements:
                logger.warning("⚠️ No se encontraron elementos de posts con selectores estándar")
                return []
            
            for post_element in posts_elements:
                try:
                    if len(new_posts) >= max_posts:
                        break
                    
                    # Extraer datos del post usando el método mejorado
                    post_data = self._extract_post_data_selenium_direct(post_element)
                    
                    if post_data and post_data.get('text') and len(post_data.get('text', '').strip()) > 20:
                        # Evitar duplicados
                        is_duplicate = any(
                            existing.get('text') == post_data.get('text') or
                            (existing.get('url') and post_data.get('url') and existing.get('url') == post_data.get('url'))
                            for existing in new_posts
                        )
                        
                        if not is_duplicate:
                            new_posts.append(post_data)
                            logger.debug(f"  ✓ Post extraído: {post_data.get('text', '')[:50]}...")
                
                except Exception as e:
                    logger.debug(f"⚠️ Error extrayendo post individual: {e}")
                    continue
            
            return new_posts
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo posts visibles: {e}")
            return []
    
    def _extract_post_data_selenium_direct(self, post_element) -> Optional[Dict]:
        """Extrae datos de un elemento post usando Selenium directamente"""
        try:
            # Extraer texto del post con múltiples selectores
            text_selectors = [
                "div[data-ad-preview='message']",
                "div.xdj266r.x11i5rnm.xat24cr.x1mh8g0r",
                "div[dir='auto'][style*='text-align']",
                "div[data-testid='post_message']",
                "span[dir='auto']",
            ]
            
            content = ""
            for selector in text_selectors:
                try:
                    text_element = post_element.find_element(By.CSS_SELECTOR, selector)
                    content = text_element.text.strip()
                    if content and len(content) > 20:
                        break
                except:
                    continue
            
            if not content or len(content) < 20:
                return None
            
            # Extraer imagen
            image_url = None
            try:
                img_selectors = [
                    "img[data-visualcompletion='media-vc-image']",
                    "img[src*='fbcdn.net']",
                    "img[src*='scontent']",
                ]
                
                for selector in img_selectors:
                    try:
                        img_element = post_element.find_element(By.CSS_SELECTOR, selector)
                        img_src = img_element.get_attribute('src')
                        if img_src and ('fbcdn.net' in img_src or 'scontent' in img_src):
                            # Filtrar imágenes de perfil
                            if not any(x in img_src.lower() for x in ['profile', 'avatar', 'picture', 'rsrc']):
                                image_url = img_src
                                break
                    except:
                        continue
            except:
                pass
            
            # Extraer métricas
            metrics = self._extract_metrics_selenium(post_element)
            
            # Extraer URL del post
            post_url = ""
            try:
                link_element = post_element.find_element(By.CSS_SELECTOR, "a[href*='/posts/']")
                post_url = link_element.get_attribute('href')
            except:
                try:
                    # Buscar cualquier enlace que contenga el ID del post
                    links = post_element.find_elements(By.CSS_SELECTOR, "a[href*='facebook.com']")
                    for link in links:
                        href = link.get_attribute('href')
                        if '/posts/' in href or '/permalink/' in href:
                            post_url = href
                            break
                except:
                    pass
            
            # Extraer username/autor
            username = "Página de Facebook"
            try:
                name_elements = post_element.find_elements(By.CSS_SELECTOR, "strong, a[role='link'] span")
                for elem in name_elements:
                    name_text = elem.text.strip()
                    if name_text and len(name_text) > 2 and len(name_text) < 50:
                        username = name_text
                        break
            except:
                pass
            
            return {
                'platform': 'facebook',
                'username': username,
                'text': content,
                'cleaned_text': content.strip(),
                'image_url': image_url,
                'video_url': None,
                'url': post_url,
                'date': datetime.now().isoformat(),
                'created_at': datetime.now().isoformat(),
                'likes': metrics.get('likes', 0),
                'comments': metrics.get('comments', 0),
                'shares': metrics.get('shares', 0),
                'retweets': 0,
                'replies': metrics.get('comments', 0),
                'hashtags': re.findall(r'#\w+', content),
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.debug(f"⚠️ Error extrayendo datos del post: {e}")
            return None
    
    def _extract_metrics_selenium(self, post_element) -> Dict:
        """Extrae métricas usando Selenium directamente"""
        metrics = {
            'likes': 0,
            'comments': 0,
            'shares': 0,
        }
        
        try:
            # Buscar texto con métricas
            element_text = post_element.text
            
            # Buscar números seguidos de palabras clave
            if 'like' in element_text.lower() or 'reacciones' in element_text.lower() or 'me gusta' in element_text.lower():
                metrics['likes'] = self._parse_metric_from_text(element_text, 'like')
            
            if 'comment' in element_text.lower() or 'comentarios' in element_text.lower():
                metrics['comments'] = self._parse_metric_from_text(element_text, 'comment')
            
            if 'share' in element_text.lower() or 'compartir' in element_text.lower() or 'compartidos' in element_text.lower():
                metrics['shares'] = self._parse_metric_from_text(element_text, 'share')
        
        except:
            pass
        
        return metrics
    
    def _parse_metric_from_text(self, text: str, metric_type: str) -> int:
        """Extrae valor de métrica del texto"""
        try:
            # Buscar patrones como "1.2K likes", "500 Me gusta", etc.
            patterns = {
                'like': [
                    r'([\d,\.]+[KkMm]?)\s*(?:like|reacciones|me gusta|gusta)',
                    r'(\d+[KkMm]?)\s*(?:👍|❤️)',
                ],
                'comment': [
                    r'([\d,\.]+[KkMm]?)\s*(?:comment|comentarios|comentar)',
                    r'(\d+[KkMm]?)\s*(?:💬|💭)',
                ],
                'share': [
                    r'([\d,\.]+[KkMm]?)\s*(?:share|compartir|compartidos)',
                    r'(\d+[KkMm]?)\s*(?:📤|↗️)',
                ],
            }
            
            for pattern in patterns.get(metric_type, []):
                match = re.search(pattern, text.lower())
                if match:
                    return self._parse_metric(match.group(1))
            
            return 0
        except:
            return 0
    
    def scrape_from_url(self, url: str, max_posts: int = 50, use_manual_login: bool = False) -> List[Dict]:
        """
        Scrapea posts de Facebook desde una URL
        
        Si use_manual_login=True, usa el nuevo scraper con login manual
        """
        if use_manual_login:
            try:
                from facebook_manual_scraper import scrape_facebook_page
                logger.info("🔧 Usando scraper con login manual (NUEVO)")
                # Esperar 60 segundos para login cuando se ejecuta desde servidor web
                # (0 = usar input() interactivo, pero no funciona desde servidor)
                posts = scrape_facebook_page(url, max_posts, wait_for_login_seconds=60)
                
                # Convertir formato al formato esperado por el sistema
                formatted_posts = []
                for post in posts:
                    formatted_posts.append({
                        'platform': 'facebook',
                        'username': post.get('author', 'Página de Facebook'),
                        'text': post.get('content', ''),
                        'cleaned_text': post.get('content', '').strip(),
                        'image_url': post.get('image_url'),
                        'video_url': None,
                        'url': post.get('url', ''),
                        'date': post.get('created_at', datetime.now().isoformat()),
                        'created_at': post.get('created_at', datetime.now().isoformat()),
                        'likes': post.get('metrics', {}).get('likes', 0),
                        'comments': post.get('metrics', {}).get('comments', 0),
                        'shares': post.get('metrics', {}).get('shares', 0),
                        'retweets': 0,
                        'replies': 0,
                        'hashtags': re.findall(r'#\w+', post.get('content', '')),
                        'scraped_at': datetime.now().isoformat()
                    })
                
                logger.info(f"✅ ✅ ✅ SCRAPER MANUAL: {len(formatted_posts)} posts REALES extraídos")
                return formatted_posts
            except Exception as e:
                logger.error(f"❌ Error con scraper manual: {e}")
                logger.info("🔄 Intentando con método automático...")
        
        # Método original (automático)
        return self._scrape_from_url_original(url, max_posts)
    
    def _scrape_from_url_original(self, url: str, max_posts: int = 50) -> List[Dict]:
        """
        Scraping desde una URL de Facebook (página, perfil, post)
        SIN TOKEN - Usa solo Selenium y requests
        
        Args:
            url: URL de Facebook (página, perfil, post)
            max_posts: Máximo de posts a extraer
        
        Returns:
            Lista de diccionarios con datos de posts
        """
        if max_posts < 1:
            max_posts = 10
        
        posts = []
        url = url.strip()
        
        # Normalizar URL
        if not url.startswith('http'):
            if url.startswith('facebook.com'):
                url = 'https://' + url
            else:
                url = 'https://facebook.com/' + url.lstrip('/')
        
        logger.info(f"🔍 Scrapeando Facebook SIN TOKEN desde URL: {url}")
        
        # PRIMERO: Intentar método requests (más rápido)
        try:
            requests_posts = self._try_requests_method(url, max_posts)
            if requests_posts and len(requests_posts) > 0:
                logger.info(f"✅ Método requests exitoso, usando {len(requests_posts)} posts")
                return requests_posts
        except Exception as e:
            logger.debug(f"⚠️ Método requests no funcionó: {e}, usando Selenium")
        
        try:
            logger.info(f"🔍 Scrapeando Facebook con SELENIUM (sin token) desde URL: {url}")
            
            # Verificar que el driver esté activo y reiniciar si es necesario
            driver_ok = False
            for retry in range(3):
                try:
                    self.driver.current_url
                    driver_ok = True
                    break
                except (WebDriverException, AttributeError, Exception) as e:
                    logger.warning(f"⚠️ Driver no está activo (intento {retry + 1}/3): {e}")
                    try:
                        if self.driver:
                            self.driver.quit()
                    except:
                        pass
                    time.sleep(2)
                    self._setup_driver()
            
            if not driver_ok:
                logger.error("❌ No se pudo establecer conexión con el driver después de 3 intentos")
                return []
            
            # Configurar timeout más largo
            self.driver.set_page_load_timeout(60)
            self.driver.implicitly_wait(20)
            
            # Intentar cargar la página con retry
            for attempt in range(3):
                try:
                    self.driver.get(url)
                    logger.info(f"✅ Página de Facebook cargada: {url} (intento {attempt + 1})")
                    break
                except Exception as e:
                    if attempt < 2:
                        logger.warning(f"⚠️ Intento {attempt + 1} falló: {e}, reintentando...")
                        time.sleep(3)
                        continue
                    else:
                        raise
            
            # Esperar a que cargue completamente
            time.sleep(5)
            
            # Cerrar popups de cookies/login
            logger.info("🔍 Cerrando popups...")
            self._close_popups()
            time.sleep(2)
            
            # Verificar si requiere autenticación - PERO intentar extraer de todas formas
            page_source = self.driver.page_source
            requires_auth = any([
                'Log in' in page_source,
                'Iniciar sesión' in page_source,
                'login' in page_source.lower(),
                'sign in' in page_source.lower(),
                'You must log in' in page_source
            ])
            
            if requires_auth:
                if not self.headless:
                    logger.warning("⚠️ ⚠️ ⚠️ Facebook muestra pantalla de LOGIN")
                    logger.info("🔑 Si estás viendo el navegador, puedes hacer login manualmente ahora")
                    logger.info("⏳ Esperando 45 segundos para que puedas hacer login...")
                    
                    # Esperar con verificación periódica para detectar login más rápido
                    login_detected = False
                    for check in range(9):  # 9 checks de 5 segundos = 45 segundos máximo
                        time.sleep(5)  # Verificar cada 5 segundos
                        try:
                            page_source_check = self.driver.page_source
                            requires_auth_check = any([
                                'Log in' in page_source_check,
                                'Iniciar sesión' in page_source_check,
                                'login' in page_source_check.lower(),
                                'sign in' in page_source_check.lower(),
                            ])
                            if not requires_auth_check:
                                logger.info(f"✅ ✅ ✅ LOGIN DETECTADO! Esperando 15 segundos para que cargue el feed completamente... (verificación {check + 1}/9)")
                                login_detected = True
                                time.sleep(15)  # AUMENTADO: 15 segundos después de detectar login (investigación recomienda 15-20s)
                                break
                        except:
                            pass
                    
                    if not login_detected:
                        logger.warning("⚠️ No se detectó login, continuando de todas formas...")
                else:
                    logger.warning("⚠️ Facebook muestra pantalla de login (modo headless), pero intentando extraer contenido público de todas formas...")
                logger.info("ℹ️ Intentando extraer posts públicos disponibles...")
            
            # Guardar HTML inicial ANTES de hacer scrolls (por si el driver se cierra)
            logger.info("💾 Guardando HTML inicial...")
            initial_html = self.driver.page_source
            
            # Esperar tiempo inicial MÍNIMO - AUMENTADO según investigación (10-15s recomendado)
            logger.info("⏳ Esperando a que cargue el contenido inicial (12s)...")
            time.sleep(12)  # AUMENTADO: 12 segundos (investigación recomienda 10-15s para contenido dinámico)
            
            # PRIORIDAD: Intentar extraer posts INMEDIATAMENTE con JavaScript (más rápido)
            logger.info("🔍 🔍 🔍 EXTRAYENDO POSTS DE FACEBOOK INMEDIATAMENTE CON JAVASCRIPT...")
            try:
                # Verificar que el driver esté activo antes de ejecutar JavaScript
                try:
                    current_url_check = self.driver.current_url
                    logger.info(f"✅ Driver activo, URL actual: {current_url_check[:50]}...")
                except Exception as e:
                    logger.error(f"❌ Driver no está activo antes de extraer con JS: {e}")
                    return []
                
                # Usar JavaScript para extraer posts directamente del DOM (más rápido que Selenium)
                # MEJORADO: Más selectores y mejor extracción
                posts_js = self.driver.execute_script("""
                    var posts = [];
                    
                    // Buscar elementos de posts de Facebook con MÚLTIPLES selectores
                    var articleElements = [];
                    
                    // MÉTODO 1: div[role="article"] (más común y confiable según investigación)
                    var articles1 = document.querySelectorAll('div[role="article"]');
                    if (articles1.length > 0) {
                        articleElements = Array.from(articles1);
                        console.log('✅ Encontrados ' + articleElements.length + ' elementos con div[role="article"]');
                    }
                    
                    // MÉTODO 2: div[data-pagelet*="FeedUnit"] (Facebook interno - según investigación)
                    if (articleElements.length === 0) {
                        var articles2 = document.querySelectorAll('div[data-pagelet*="FeedUnit"]');
                        if (articles2.length > 0) {
                            articleElements = Array.from(articles2);
                            console.log('✅ Encontrados ' + articleElements.length + ' elementos con data-pagelet*="FeedUnit"');
                        }
                    }
                    
                    // MÉTODO 3: div[data-pagelet*="Composer"] (estructura de post - según investigación)
                    if (articleElements.length === 0) {
                        var articles3_composer = document.querySelectorAll('div[data-pagelet*="Composer"]');
                        if (articles3_composer.length > 0) {
                            articleElements = Array.from(articles3_composer);
                            console.log('✅ Encontrados ' + articleElements.length + ' elementos con data-pagelet*="Composer"');
                        }
                    }
                    
                    // MÉTODO 4: div[data-ad-preview="message"] - MEJORADO
                    if (articleElements.length === 0) {
                        var articles3 = document.querySelectorAll('div[data-ad-preview="message"]');
                        if (articles3.length > 0) {
                            articleElements = Array.from(articles3);
                            console.log('✅ Encontrados ' + articleElements.length + ' elementos con data-ad-preview="message"');
                        }
                    }
                    
                    // MÉTODO 5: Selectores por clase (Facebook 2024-2025 - según investigación)
                    if (articleElements.length === 0) {
                        var articles5 = document.querySelectorAll('div[class*="x1y1aw1k"], div[class*="x1n2onr6"], div[class*="x78zum5"]');
                        var filtered5 = [];
                        for (var a5 = 0; a5 < articles5.length; a5++) {
                            var txt = articles5[a5].textContent || '';
                            // Filtrar: debe tener texto largo Y imagen (según investigación)
                            if (txt.length > 50 && articles5[a5].querySelector('img[src*="fbcdn.net"], img[src*="scontent"]')) {
                                filtered5.push(articles5[a5]);
                            }
                        }
                        if (filtered5.length > 0) {
                            articleElements = filtered5;
                            console.log('✅ Encontrados ' + articleElements.length + ' elementos con selectores nuevos de Facebook 2024-2025');
                        }
                    }
                    
                    // Selector 4: div que contiene posts (último recurso)
                    if (articleElements.length === 0) {
                        var allDivs = document.querySelectorAll('div');
                        for (var d = 0; d < allDivs.length; d++) {
                            var div = allDivs[d];
                            var text = div.textContent || '';
                            var hasImage = div.querySelector('img[src*="fbcdn.net"], img[src*="scontent"]');
                            if (text.length > 50 && hasImage && !div.querySelector('a[href*="/profile"]')) {
                                articleElements.push(div);
                                if (articleElements.length >= 50) break;
                            }
                        }
                    }
                    
                    console.log('📊 Encontrados ' + articleElements.length + ' elementos potenciales de posts');
                    
                    for (var i = 0; i < Math.min(articleElements.length, 200); i++) {
                        var article = articleElements[i];
                        
                        // Extraer texto con MÚLTIPLES métodos
                        var textElem = null;
                        var text = '';
                        
                        // Extracción de texto mejorada según investigación (múltiples métodos)
                        // Método 1: data-ad-preview="message" (más específico)
                        textElem = article.querySelector('[data-ad-preview="message"]');
                        if (textElem) {
                            text = textElem.textContent.trim();
                        }
                        
                        // Método 2: div[data-testid="post_message"] (nuevo formato)
                        if (!text || text.length < 15) {
                            textElem = article.querySelector('div[data-testid="post_message"]');
                            if (textElem) {
                                text = textElem.textContent.trim();
                            }
                        }
                        
                        // Método 3: div[dir="auto"] con texto largo (según investigación)
                        if (!text || text.length < 15) {
                            var divsAuto = article.querySelectorAll('div[dir="auto"]');
                            var longestDivText = '';
                            for (var k = 0; k < divsAuto.length; k++) {
                                var txt = divsAuto[k].textContent.trim();
                                // Seleccionar el texto más largo (según investigación)
                                if (txt.length > longestDivText.length && txt.length > 15) {
                                    longestDivText = txt;
                                    textElem = divsAuto[k];
                                }
                            }
                            if (longestDivText) text = longestDivText;
                        }
                        
                        // Método 4: span[dir="auto"] con texto largo
                        if (!text || text.length < 15) {
                            var spans = article.querySelectorAll('span[dir="auto"]');
                            var longestText = '';
                            for (var j = 0; j < spans.length; j++) {
                                var txt = spans[j].textContent.trim();
                                if (txt.length > longestText.length && txt.length > 15) {
                                    longestText = txt;
                                    textElem = spans[j];
                                }
                            }
                            if (longestText) text = longestText;
                        }
                        
                        // Método 5: Selectores nuevos de Facebook 2024-2025 (según investigación)
                        if (!text || text.length < 15) {
                            var newTextSelectors = [
                                'div[class*="x193iq5w"]',
                                'div[class*="x1y1aw1k"] span',
                                'div[class*="x1n2onr6"] span'
                            ];
                            for (var ns = 0; ns < newTextSelectors.length; ns++) {
                                var newTextElem = article.querySelector(newTextSelectors[ns]);
                                if (newTextElem) {
                                    var newTxt = newTextElem.textContent.trim();
                                    if (newTxt.length > text.length && newTxt.length > 15) {
                                        text = newTxt;
                                        textElem = newTextElem;
                                    }
                                }
                            }
                        }
                        
                        // Si tenemos texto válido, extraer el post - REDUCIDO umbral a 15 caracteres
                        if (text && text.length > 15) {
                            // Extraer imagen (priorizar imágenes de contenido)
                            var img = null;
                            var allImgs = article.querySelectorAll('img');
                            for (var imgIdx = 0; imgIdx < allImgs.length; imgIdx++) {
                                var imgSrc = allImgs[imgIdx].src || '';
                                if (imgSrc && (imgSrc.includes('fbcdn.net') || imgSrc.includes('scontent')) 
                                    && !imgSrc.includes('profile') && !imgSrc.includes('avatar')) {
                                    img = imgSrc;
                                    break;
                                }
                            }
                            
                            // Extraer username/autor
                            var username = 'Página de Facebook';
                            var nameElem = article.querySelector('strong') || 
                                          article.querySelector('a[role="link"] span') ||
                                          article.querySelector('h3 a') ||
                                          article.querySelector('h2 a');
                            if (nameElem) {
                                username = nameElem.textContent.trim();
                            }
                            
                            // Extraer URL del post
                            var postUrl = '';
                            var linkElem = article.querySelector('a[href*="/posts/"]') ||
                                          article.querySelector('a[href*="/permalink/"]') ||
                                          article.querySelector('a[aria-label*="post"]');
                            if (linkElem) {
                                postUrl = linkElem.href;
                            }
                            
                            posts.push({
                                text: text,
                                image: img,
                                username: username,
                                url: postUrl
                            });
                        }
                    }
                    
                    console.log('✅ Extraídos ' + posts.length + ' posts válidos');
                    return posts;
                """)
                
                if posts_js and len(posts_js) > 0:
                    logger.info(f"✅ ✅ ✅ JAVASCRIPT ENCONTRÓ {len(posts_js)} POSTS INMEDIATAMENTE!")
                    for js_post in posts_js:
                        # REDUCIDO umbral a 15 caracteres para capturar más posts
                        if js_post.get('text') and len(js_post.get('text', '')) > 15:
                            # Verificar duplicados
                            is_duplicate = any(
                                existing.get('text') == js_post.get('text', '') 
                                for existing in posts
                            )
                            if not is_duplicate:
                                post_data = {
                                    'platform': 'facebook',
                                    'username': js_post.get('username', 'Página de Facebook'),
                                    'text': js_post.get('text', ''),
                                    'cleaned_text': js_post.get('text', '').strip(),
                                    'image_url': js_post.get('image'),
                                    'video_url': None,
                                    'url': js_post.get('url', ''),
                                    'date': datetime.now().isoformat(),
                                    'created_at': datetime.now().isoformat(),
                                    'likes': 0,
                                    'comments': 0,
                                    'shares': 0,
                                    'retweets': 0,
                                    'replies': 0,
                                    'hashtags': re.findall(r'#\w+', js_post.get('text', '')),
                                    'scraped_at': datetime.now().isoformat()
                                }
                                posts.append(post_data)
                                logger.info(f"✅ Post {len(posts)} REAL extraído (JS rápido): {js_post.get('text', '')[:60]}...")
                    
                    if posts and len(posts) > 0:
                        logger.info(f"✅ ✅ ✅ EXTRACCIÓN RÁPIDA CON JAVASCRIPT EXITOSA: {len(posts)} posts REALES!")
                        # NO retornar todavía - continuar con scrolls para obtener MÁS posts
                        logger.info(f"📜 Continuando con scrolls para obtener MÁS posts (actualmente: {len(posts)})...")
                else:
                    logger.warning("⚠️ JavaScript no encontró posts, intentando con Selenium...")
            except Exception as e:
                logger.warning(f"⚠️ Método JavaScript rápido falló: {e}, intentando Selenium...")
            
            # Hacer scrolls MÚLTIPLES para cargar MÁS contenido - OPTIMIZADO
            logger.info("📜 Haciendo scrolls MÚLTIPLES para cargar MÁS posts...")
            posts_before_scrolls = len(posts)
            
            # Verificar que el driver esté activo antes de hacer scrolls
            try:
                self.driver.current_url
            except Exception as e:
                logger.error(f"❌ Driver no está activo antes de hacer scrolls: {e}")
                if posts and len(posts) > 0:
                    logger.info(f"✅ Retornando {len(posts)} posts que ya tenemos...")
                    return posts[:max_posts] if len(posts) > max_posts else posts
                return []
            
            for i in range(20):  # AUMENTADO a 20 scrolls (similar a Twitter que hace 30)
                # Verificar driver antes de cada scroll
                try:
                    self.driver.current_url
                except Exception as e:
                    logger.warning(f"⚠️ Driver se cerró durante scrolls: {e}")
                    break
                
                try:
                    # SCROLL INTELIGENTE: Verificar posts antes y después del scroll (según investigación)
                    posts_before_scroll = len(posts)
                    last_height = self.driver.execute_script("return document.body.scrollHeight")
                    
                    self._smooth_scroll()
                    logger.info(f"📜 Scroll {i+1}/20 realizado...")
                    
                    # Esperar según investigación (3-5 segundos recomendado)
                    time.sleep(3)  # AUMENTADO: 3 segundos (investigación recomienda 3-5s)
                    
                    # Verificar si hay nuevo contenido
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        logger.info(f"⚠️ No hay más contenido después del scroll {i+1}, intentando scroll más pequeño...")
                        self.driver.execute_script("window.scrollBy(0, 500);")
                        time.sleep(2)
                except Exception as e:
                    logger.warning(f"⚠️ Error en scroll {i+1}: {e}")
                    break
                
                # Después de CADA scroll, intentar extraer más posts (más frecuente - similar a Twitter)
                # Cambiado de cada 2 scrolls a cada scroll para obtener más posts
                if True:  # Extraer después de cada scroll
                    try:
                        # Intentar extraer más posts con JavaScript después de scrolls
                        more_posts_js = self.driver.execute_script("""
                            var posts = [];
                            var articleElements = document.querySelectorAll('div[role="article"]');
                            if (articleElements.length === 0) {
                                articleElements = document.querySelectorAll('div[data-ad-preview="message"]');
                            }
                            for (var i = 0; i < articleElements.length; i++) {
                                var article = articleElements[i];
                                var textElem = article.querySelector('[data-ad-preview="message"]') || 
                                               article.querySelector('div[data-testid="post_message"]') ||
                                               article.querySelector('div[dir="auto"]');
                                if (!textElem) {
                                    var spans = article.querySelectorAll('span[dir="auto"]');
                                    for (var j = spans.length - 1; j >= 0; j--) {
                                        if (spans[j].textContent.trim().length > 20) {
                                            textElem = spans[j];
                                            break;
                                        }
                                    }
                                }
                                if (textElem && textElem.textContent.trim().length > 20) {
                                    var img = article.querySelector('img[src*="fbcdn.net"]:not([src*="profile"])') ||
                                              article.querySelector('img[src*="scontent"]:not([src*="profile"])');
                                    var username = 'Página de Facebook';
                                    var nameElem = article.querySelector('strong') || 
                                                  article.querySelector('a[role="link"] span');
                                    if (nameElem) {
                                        username = nameElem.textContent.trim();
                                    }
                                    var postUrl = '';
                                    var linkElem = article.querySelector('a[href*="/posts/"]');
                                    if (linkElem) {
                                        postUrl = linkElem.href;
                                    }
                                    posts.push({
                                        text: textElem.textContent.trim(),
                                        image: img ? img.src : null,
                                        username: username,
                                        url: postUrl
                                    });
                                }
                            }
                            return posts;
                        """)
                        
                        if more_posts_js:
                            new_posts_count = 0
                            for js_post in more_posts_js:
                                if js_post.get('text') and len(js_post.get('text', '')) > 20:
                                    # Verificar duplicados
                                    is_duplicate = any(
                                        existing.get('text') == js_post.get('text', '') 
                                        for existing in posts
                                    )
                                    if not is_duplicate:
                                        post_data = {
                                            'platform': 'facebook',
                                            'username': js_post.get('username', 'Página de Facebook'),
                                            'text': js_post.get('text', ''),
                                            'cleaned_text': js_post.get('text', '').strip(),
                                            'image_url': js_post.get('image'),
                                            'video_url': None,
                                            'url': js_post.get('url', ''),
                                            'date': datetime.now().isoformat(),
                                            'created_at': datetime.now().isoformat(),
                                            'likes': 0,
                                            'comments': 0,
                                            'shares': 0,
                                            'retweets': 0,
                                            'replies': 0,
                                            'hashtags': re.findall(r'#\w+', js_post.get('text', '')),
                                            'scraped_at': datetime.now().isoformat()
                                        }
                                        posts.append(post_data)
                                        new_posts_count += 1
                            
                            if new_posts_count > 0:
                                logger.info(f"✅ Extraídos {new_posts_count} posts adicionales después de scroll {i+1} (total: {len(posts)})")
                    except Exception as e:
                        logger.debug(f"⚠️ Error extrayendo posts después de scroll: {e}")
            
            posts_after_scrolls = len(posts)
            if posts_after_scrolls > posts_before_scrolls:
                logger.info(f"✅ ✅ ✅ Después de scrolls: {posts_after_scrolls - posts_before_scrolls} posts nuevos (total: {posts_after_scrolls})")
            
            # Si ya tenemos suficientes posts, retornar inmediatamente Y CERRAR NAVEGADOR
            if posts and len(posts) >= max_posts:
                logger.info(f"✅ ✅ ✅ Ya tenemos {len(posts)} posts (suficiente), CERRANDO NAVEGADOR y retornando inmediatamente...")
                final_posts = posts[:max_posts]
                # CERRAR NAVEGADOR INMEDIATAMENTE
                try:
                    logger.info("🔒 Cerrando navegador...")
                    self.driver.quit()
                    logger.info("✅ Navegador cerrado correctamente")
                except Exception as e:
                    logger.warning(f"⚠️ Error cerrando navegador: {e}")
                return final_posts
            
            # Si tenemos al menos 5 posts, retornar y cerrar (no esperar tanto)
            if posts and len(posts) >= 5 and max_posts > 10:
                logger.info(f"✅ Tenemos {len(posts)} posts (mínimo 5), continuando pero con límite de tiempo reducido...")
            
            time.sleep(1)  # Reducido a 1 segundo después de scrolls
            
            # Scroll y extracción de posts con técnica mejorada - OPTIMIZADO
            posts_extracted = len(posts)  # Empezar con los que ya tenemos
            scroll_attempts = 0
            max_scrolls = 20  # Reducido a 20 scrolls (antes 30) para ser más rápido pero suficiente
            
            # MÉTODO MEJORADO: Extraer posts usando Selenium directamente
            logger.info("🔍 Extrayendo posts usando método Selenium mejorado...")
            all_posts = []
            
            while posts_extracted < max_posts * 2 and scroll_attempts < max_scrolls:
                try:
                    # Verificar que el driver esté activo y reiniciar si es necesario
                    try:
                        self.driver.current_url
                    except (WebDriverException, AttributeError, Exception) as e:
                        logger.warning(f"⚠️ Driver se cerró durante el scraping: {e}, reintentando...")
                        try:
                            if self.driver:
                                self.driver.quit()
                        except:
                            pass
                        time.sleep(2)
                        self._setup_driver()
                        # Intentar recargar la página
                        try:
                            self.driver.get(url)
                            time.sleep(5)
                            self._close_popups()
                        except:
                            logger.error("❌ No se pudo recargar la página, terminando scraping")
                            break
                    
                    # Extraer posts visibles usando Selenium directamente
                    new_posts = self._extract_visible_posts_selenium(max_posts - posts_extracted)
                    
                    # Agregar posts nuevos
                    for post in new_posts:
                        # Verificar duplicados
                        is_duplicate = any(
                            existing.get('text') == post.get('text') or
                            (existing.get('url') and post.get('url') and existing.get('url') == post.get('url'))
                            for existing in all_posts
                        )
                        
                        if not is_duplicate:
                            all_posts.append(post)
                            posts_extracted += 1
                            logger.info(f"✅ Post {posts_extracted}/{max_posts} extraído: {post.get('text', '')[:50]}...")
                    
                    # Scroll para cargar más posts - OPTIMIZADO
                    if posts_extracted < max_posts:  # Continuar solo hasta tener lo solicitado (más rápido)
                        logger.info(f"📜 Scroll {scroll_attempts + 1}/{max_scrolls} - Posts encontrados: {posts_extracted}/{max_posts}")
                        
                        # Verificar si el driver sigue activo antes de hacer scroll
                        try:
                            self.driver.current_url
                        except Exception as e:
                            logger.error(f"❌ Driver no está activo, terminando extracción: {e}")
                            break
                        
                        # Scroll suave más rápido
                        try:
                            for _ in range(2):  # Solo 2 scrolls por iteración (antes 3)
                                scroll_result = self._smooth_scroll()
                                if not scroll_result:
                                    logger.warning("⚠️ Scroll falló, puede que el driver se haya cerrado")
                                    break
                                time.sleep(random.uniform(0.8, 1.5))  # Reducido tiempo
                        except Exception as e:
                            logger.warning(f"⚠️ Error en scroll: {e}, continuando...")
                            break
                        scroll_attempts += 1
                    else:
                        logger.info(f"✅ Ya tenemos {posts_extracted} posts (suficiente), terminando y cerrando navegador...")
                        break
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error en scroll {scroll_attempts + 1}: {e}")
                    scroll_attempts += 1
                    time.sleep(2)
                    continue
                
                # Extraer posts - múltiples selectores mejorados (PRIORIZAR CONTENIDO REAL)
                post_elements = []
                
                # Selector 1: data-pagelet (más específico de Facebook) - MÁS IMPORTANTE
                # Buscar todos los elementos con data-pagelet y filtrar los que parecen posts
                all_pagelets = soup.find_all('div', {'data-pagelet': True})
                if all_pagelets:
                    # Filtrar pagelets que parecen posts (tienen texto significativo o imágenes)
                    for pagelet in all_pagelets:
                        text_len = len(pagelet.get_text(strip=True))
                        has_img = pagelet.find('img') is not None
                        has_link = pagelet.find('a', href=re.compile(r'/posts/|/photo|/video')) is not None
                        # Un post típico tiene texto > 50 caracteres o tiene imagen/enlace
                        if (text_len > 50) or (has_img and has_link) or (text_len > 30 and has_link):
                            post_elements.append(pagelet)
                    if post_elements:
                        logger.info(f"📊 Encontrados {len(post_elements)} posts con data-pagelet (filtrados de {len(all_pagelets)})")
                
                # Selector 2: role="article" (estructura HTML5 estándar)
                if not post_elements or len(post_elements) < 3:
                    article_elements = soup.find_all('div', {'role': 'article'})
                    if article_elements:
                        # Filtrar artículos que parecen posts reales
                        for article in article_elements:
                            text_len = len(article.get_text(strip=True))
                            if text_len > 50:  # Solo posts con contenido significativo
                                post_elements.append(article)
                        if post_elements:
                            logger.info(f"📊 Encontrados {len(post_elements)} posts con role='article'")
                
                # Selector 3: data-ad-preview (posts de páginas públicas)
                if not post_elements or len(post_elements) < 3:
                    ad_preview_elements = soup.find_all('div', {'data-ad-preview': 'message'})
                    if ad_preview_elements:
                        # Estos son posts de páginas públicas, agregar todos
                        post_elements.extend(ad_preview_elements)
                        logger.info(f"📊 Encontrados {len(ad_preview_elements)} posts con data-ad-preview")
                
                # Selector 4: Buscar divs con estructura específica de posts de Facebook
                if not post_elements or len(post_elements) < 3:
                    # Buscar divs que contengan estructura típica: texto + imagen + enlace a post
                    potential_posts = soup.find_all('div')
                    for div in potential_posts:
                        # Verificar estructura de post
                        has_text = len(div.get_text(strip=True)) > 50
                        has_facebook_img = div.find('img', src=re.compile(r'fbcdn\.net|scontent')) is not None
                        has_post_link = div.find('a', href=re.compile(r'/posts/|/permalink/')) is not None
                        # Si tiene las características de un post, agregarlo
                        if has_text and (has_facebook_img or has_post_link):
                            # Verificar que no sea duplicado
                            if div not in post_elements:
                                post_elements.append(div)
                    if post_elements:
                        logger.info(f"📊 Encontrados {len(post_elements)} posts por estructura de contenido")
                
                # Selector 5: Buscar por estructura de contenido (más agresivo)
                if not post_elements or len(post_elements) < 3:
                    logger.info("🔍 Buscando posts por estructura de contenido (método agresivo)...")
                    all_divs = soup.find_all('div')
                    for div in all_divs:
                        # Buscar divs que contengan elementos típicos de posts
                        has_img = div.find('img', src=re.compile(r'fbcdn\.net|scontent|facebook\.com')) is not None
                        has_text = len(div.get_text(strip=True)) > 50
                        has_link = div.find('a', href=re.compile(r'/posts/|/photo|/video|/permalink/')) is not None
                        # Si tiene imagen de Facebook, texto y enlace, probablemente es un post
                        if has_text and (has_img or has_link):
                            # Verificar que no sea duplicado
                            if div not in post_elements:
                                post_elements.append(div)
                    if post_elements:
                        logger.info(f"📊 Encontrados {len(post_elements)} posts por estructura de contenido")
                
                # Selector 6: Buscar elementos que contengan URLs de Facebook (último recurso)
                if not post_elements or len(post_elements) < 3:
                    logger.info("🔍 Buscando posts por URLs de Facebook (método exhaustivo)...")
                    all_divs = soup.find_all('div')
                    for div in all_divs:
                        # Buscar divs que contengan enlaces a posts de Facebook
                        links = div.find_all('a', href=re.compile(r'facebook\.com/.*/posts|facebook\.com/.*/photo|facebook\.com/.*/video|facebook\.com/.*/permalink'))
                        text_content = div.get_text(strip=True)
                        if links and len(text_content) > 30:
                            # Verificar que no sea duplicado
                            if div not in post_elements:
                                post_elements.append(div)
                    if post_elements:
                        logger.info(f"📊 Encontrados {len(post_elements)} posts por URLs de Facebook")
                
                logger.info(f"📊 Encontrados {len(post_elements)} elementos potenciales de posts")
                
                # Procesar posts encontrados
                for post_element in post_elements:
                    if posts_extracted >= max_posts:
                        break
                    
                    post_data = self._extract_post_data(post_element)
                    # Validar que el post tenga contenido significativo
                    if post_data:
                        text = post_data.get('text', '').strip()
                        image_url = post_data.get('image_url', '')
                        video_url = post_data.get('video_url', '')
                        
                        # Un post válido debe tener texto > 20 caracteres O imagen/video real
                        is_valid = False
                        if text and len(text) > 20:
                            is_valid = True
                        elif image_url and ('fbcdn.net' in image_url or 'scontent' in image_url):
                            is_valid = True
                        elif video_url and ('fbcdn.net' in video_url or 'facebook.com' in video_url):
                            is_valid = True
                        
                        if is_valid:
                            # VALIDACIÓN CRÍTICA: Rechazar posts con imágenes simuladas
                            image_url = post_data.get('image_url', '')
                            if image_url:
                                is_demo = any(pattern in image_url.lower() for pattern in [
                                    'picsum.photos', 'unsplash', 'placeholder', 'via.placeholder', 
                                    'dummyimage', 'loremflickr', 'placehold', 'dummy'
                                ])
                                if is_demo:
                                    logger.warning(f"   ❌ ❌ ❌ POST RECHAZADO: Imagen simulada detectada: {image_url[:60]}...")
                                    continue  # RECHAZAR este post completamente
                            
                            # Verificar duplicados por texto y URL
                            is_duplicate = any(
                                existing.get('text') == post_data.get('text') or
                                (existing.get('url') and post_data.get('url') and existing.get('url') == post_data.get('url'))
                                for existing in posts
                            )
                            if not is_duplicate:
                                all_posts.append(post_data)
                                posts_extracted += 1
                                logger.info(f"✅ Post {posts_extracted}/{max_posts} extraído: {text[:50] if text else 'Sin texto'}...")
                                if image_url:
                                    # Verificar que sea imagen real de Facebook
                                    is_real = 'fbcdn.net' in image_url or ('facebook.com' in image_url and 'scontent' in image_url)
                                    if is_real:
                                        logger.info(f"   🖼️ ✅ Imagen REAL de Facebook: {image_url[:60]}...")
                                    else:
                                        logger.warning(f"   ⚠️ Imagen de origen desconocido: {image_url[:60]}...")
                                if video_url:
                                    logger.info(f"   🎥 Video encontrado: {video_url[:50]}...")
                
                # Scroll para cargar más posts - CONTINUAR aunque tengamos posts
                if posts_extracted < max_posts * 2:  # Continuar hasta tener el doble de lo solicitado
                    # Scroll suave múltiple para cargar más contenido
                    for _ in range(3):  # 3 scrolls por iteración
                        self._smooth_scroll()
                        time.sleep(random.uniform(1, 2))
                    time.sleep(self.delay)
                    scroll_attempts += 1
                else:
                    logger.info(f"✅ Ya tenemos {posts_extracted} posts (más del doble de {max_posts} solicitados)")
                    break
            
            # Si no se encontraron suficientes posts, hacer scroll profundo - OPTIMIZADO
            if posts_extracted < max_posts:
                logger.warning(f"⚠️ Solo se encontraron {posts_extracted} posts, haciendo scroll profundo (rápido)...")
                
                for i in range(5):  # Reducido a 5 scrolls (antes 10)
                    self._smooth_scroll()
                    time.sleep(random.uniform(1, 2))  # Reducido tiempo
                    
                    # Extraer posts después de cada scroll con JavaScript (más rápido)
                    try:
                        quick_posts_js = self.driver.execute_script("""
                            var posts = [];
                            var articles = document.querySelectorAll('div[role="article"]');
                            for (var i = 0; i < Math.min(articles.length, 50); i++) {
                                var article = articles[i];
                                var textElem = article.querySelector('[data-ad-preview="message"]') || 
                                               article.querySelector('div[dir="auto"]');
                                if (textElem && textElem.textContent.trim().length > 20) {
                                    var img = article.querySelector('img[src*="fbcdn.net"]:not([src*="profile"])');
                                    posts.push({
                                        text: textElem.textContent.trim(),
                                        image: img ? img.src : null
                                    });
                                }
                            }
                            return posts;
                        """)
                        
                        if quick_posts_js:
                            for js_post in quick_posts_js:
                                if js_post.get('text') and len(js_post.get('text', '')) > 20:
                                    is_duplicate = any(
                                        existing.get('text') == js_post.get('text', '')
                                        for existing in all_posts
                                    )
                                    if not is_duplicate:
                                        post_data = {
                                            'platform': 'facebook',
                                            'username': 'Página de Facebook',
                                            'text': js_post.get('text', ''),
                                            'cleaned_text': js_post.get('text', '').strip(),
                                            'image_url': js_post.get('image'),
                                            'video_url': None,
                                            'url': '',
                                            'date': datetime.now().isoformat(),
                                            'created_at': datetime.now().isoformat(),
                                            'likes': 0,
                                            'comments': 0,
                                            'shares': 0,
                                            'retweets': 0,
                                            'replies': 0,
                                            'hashtags': re.findall(r'#\w+', js_post.get('text', '')),
                                            'scraped_at': datetime.now().isoformat()
                                        }
                                        all_posts.append(post_data)
                                        posts_extracted += 1
                                        if posts_extracted >= max_posts:
                                            break
                    except:
                        pass
                    
                    if posts_extracted >= max_posts:
                        break
            
            # Agregar posts de JavaScript a all_posts si existen
            if posts:
                # Combinar posts de JavaScript con posts de Selenium
                for post in posts:
                    is_duplicate = any(
                        existing.get('text') == post.get('text') 
                        for existing in all_posts
                    )
                    if not is_duplicate:
                        all_posts.append(post)
            
            # Limitar al máximo solicitado solo al final
            final_posts = all_posts[:max_posts] if len(all_posts) > max_posts else all_posts
            logger.info(f"✅ ✅ ✅ TOTAL FINAL: {len(all_posts)} posts encontrados, retornando {len(final_posts)} posts REALES")
            
            # CERRAR NAVEGADOR INMEDIATAMENTE antes de retornar
            logger.info("🔒 🔒 🔒 CERRANDO NAVEGADOR INMEDIATAMENTE...")
            try:
                self.driver.quit()
                logger.info("✅ ✅ ✅ Navegador cerrado correctamente")
            except Exception as e:
                logger.warning(f"⚠️ Error cerrando navegador: {e}")
                # Intentar cerrar con fuerza
                try:
                    import os
                    import signal
                    if hasattr(self.driver, 'service') and self.driver.service.process:
                        os.kill(self.driver.service.process.pid, signal.SIGTERM)
                except:
                    pass
            
            posts = final_posts
            logger.info(f"✅ Total de posts de Facebook extraídos: {len(posts)}")
            return posts
            
        except Exception as e:
            logger.error(f"❌ Error en scraping de Facebook desde URL: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return posts
    
    def _smooth_scroll(self):
        """Scroll suave para simular comportamiento humano - con verificación de driver activo"""
        try:
            # Verificar que el driver esté activo antes de hacer scroll
            try:
                self.driver.current_url
            except Exception:
                logger.warning("⚠️ Driver no está activo, no se puede hacer scroll")
                return False
            
            # Scroll incremental en lugar de saltar al final
            scroll_pause_time = random.uniform(0.5, 1.5)
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Scroll gradual
            current_position = self.driver.execute_script("return window.pageYOffset")
            scroll_amount = random.randint(300, 800)
            new_position = current_position + scroll_amount
            
            self.driver.execute_script(f"window.scrollTo(0, {new_position});")
            time.sleep(scroll_pause_time)
            
            # A veces hacer scroll hacia arriba un poco (comportamiento humano)
            if random.random() < 0.2:
                self.driver.execute_script(f"window.scrollTo(0, {new_position - random.randint(50, 200)});")
                time.sleep(random.uniform(0.3, 0.8))
                self.driver.execute_script(f"window.scrollTo(0, {new_position});")
                time.sleep(scroll_pause_time)
            
        except Exception as e:
            logger.warning(f"⚠️ Error en scroll suave: {e}")
            # Fallback a scroll simple
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    
    def _extract_post_data(self, post_element) -> Optional[Dict]:
        """
        Extraer datos de un post de Facebook con técnicas mejoradas
        Extrae: texto, imágenes/videos, likes, comments, shares, fecha, URL
        """
        try:
            # ===== EXTRACCIÓN DE TEXTO (múltiples métodos) =====
            text = ""
            
            # Método 1: data-testid='post_message'
            text_elem = post_element.find('div', {'data-testid': 'post_message'})
            if text_elem:
                text = text_elem.get_text(strip=True)
            
            # Método 2: data-ad-preview="message"
            if not text:
                text_elem = post_element.find('div', {'data-ad-preview': 'message'})
                if text_elem:
                    text = text_elem.get_text(strip=True)
            
            # Método 3: Buscar en spans con texto largo (más de 30 caracteres)
            if not text:
                all_spans = post_element.find_all('span')
                for span in all_spans:
                    span_text = span.get_text(strip=True)
                    # Filtrar textos muy cortos o que parecen UI
                    if len(span_text) > 30 and len(span_text) < 5000:
                        # Verificar que no sea solo números o símbolos
                        if any(c.isalpha() for c in span_text):
                            text = span_text
                            break
            
            # Método 4: Buscar en divs con texto considerable
            if not text:
                all_divs = post_element.find_all('div')
                for div in all_divs:
                    div_text = div.get_text(strip=True)
                    if len(div_text) > 30 and len(div_text) < 5000:
                        if any(c.isalpha() for c in div_text):
                            # Verificar que no sea duplicado de otros elementos
                            if div_text != text:
                                text = div_text
                                break
            
            # ===== EXTRACCIÓN DE USERNAME/AUTOR =====
            username = ""
            
            # Método 1: Buscar enlaces con patrones de usuario/página
            user_links = post_element.find_all('a', href=re.compile(r'/([\w\.]+)/?$|/pages/|/profile\.php'))
            for link in user_links:
                href = link.get('href', '')
                link_text = link.get_text(strip=True)
                if link_text and len(link_text) > 0:
                    username = link_text
                    break
            
            # Método 2: Buscar en atributos aria-label
            if not username:
                aria_labels = post_element.find_all(attrs={'aria-label': True})
                for elem in aria_labels:
                    aria_label = elem.get('aria-label', '')
                    if 'page' in aria_label.lower() or 'profile' in aria_label.lower():
                        # Extraer nombre de la etiqueta aria
                        username = aria_label.split('(')[0].strip()
                        break
            
            if not username:
                username = "Facebook User"
            
            # ===== EXTRACCIÓN DE FECHA =====
            date_str = ""
            
            # Método 1: Buscar enlaces con timestamps
            time_links = post_element.find_all('a', href=re.compile(r'/posts/|/photos/|/videos/'))
            for link in time_links:
                href = link.get('href', '')
                if '/posts/' in href or '/photos/' in href or '/videos/' in href:
                    # Extraer timestamp de la URL si está disponible
                    date_str = datetime.now().isoformat()
                    break
            
            # Método 2: Buscar elementos time o con atributos datetime
            time_elem = post_element.find('time')
            if time_elem:
                date_str = time_elem.get('datetime', '') or time_elem.get('title', '')
            
            if not date_str:
                date_str = datetime.now().isoformat()
            
            # ===== EXTRACCIÓN DE MÉTRICAS (likes, comments, shares) - MEJORADA =====
            likes = 0
            comments = 0
            shares = 0
            
            # Obtener todo el texto del elemento para análisis
            all_text = post_element.get_text()
            
            # Buscar patrones de métricas más específicos
            # Likes: buscar patrones como "1.2K likes", "500 Me gusta", etc.
            likes_patterns = [
                r'(\d+[KMB]?)\s*(?:like|me gusta|gusta)',
                r'(\d+[KMB]?)\s*(?:👍|❤️)',
                r'like[s]?:\s*(\d+[KMB]?)',
                r'me gusta[s]?:\s*(\d+[KMB]?)'
            ]
            for pattern in likes_patterns:
                match = re.search(pattern, all_text.lower())
                if match:
                    likes = self._parse_metric(match.group(1))
                    break
            
            # Comments: buscar patrones de comentarios
            comments_patterns = [
                r'(\d+[KMB]?)\s*(?:comment|comentario|comentar)',
                r'(\d+[KMB]?)\s*(?:💬|💭)',
                r'comment[s]?:\s*(\d+[KMB]?)',
                r'comentario[s]?:\s*(\d+[KMB]?)'
            ]
            for pattern in comments_patterns:
                match = re.search(pattern, all_text.lower())
                if match:
                    comments = self._parse_metric(match.group(1))
                    break
            
            # Shares: buscar patrones de compartir
            shares_patterns = [
                r'(\d+[KMB]?)\s*(?:share|compartir|comparte)',
                r'(\d+[KMB]?)\s*(?:📤|↗️)',
                r'share[s]?:\s*(\d+[KMB]?)',
                r'compartir:\s*(\d+[KMB]?)'
            ]
            for pattern in shares_patterns:
                match = re.search(pattern, all_text.lower())
                if match:
                    shares = self._parse_metric(match.group(1))
                    break
            
            # ===== EXTRACCIÓN DE IMÁGENES Y VIDEOS - MEJORADA =====
            image_url = None
            video_url = None
            
            # Método 1: Buscar imágenes en img tags - PRIORIZAR IMÁGENES DE CONTENIDO
            img_tags = post_element.find_all('img')
            
            # Separar imágenes por tipo
            profile_images = []
            content_images = []
            all_images = []
            
            for img in img_tags:
                img_src = img.get('src', '') or img.get('data-src', '') or img.get('data-image', '') or img.get('data-lazy-src', '')
                if not img_src:
                    continue
                
                # Filtrar imágenes de Facebook CDN
                if 'fbcdn.net' in img_src or 'facebook.com' in img_src:
                    # Identificar imágenes de perfil (suelen ser pequeñas o tener ciertos patrones)
                    is_profile = (
                        '/rsrc.php/' in img_src or
                        'profile' in img_src.lower() or
                        'avatar' in img_src.lower() or
                        'picture' in img_src.lower() or
                        img_src.count('/') > 8  # URLs de perfil suelen tener más niveles
                    )
                    
                    if is_profile:
                        profile_images.append(img_src)
                    else:
                        # Imágenes de contenido (posts)
                        if 'scontent' in img_src or 'fbstatic' in img_src:
                            content_images.append(img_src)
                            all_images.append(img_src)
            
            # Priorizar imágenes de contenido (más grandes) - IMÁGENES REALES DE POSTS
            if content_images:
                # Filtrar mejor: buscar imágenes que sean realmente del contenido del post
                # Las imágenes de posts de Facebook suelen tener patrones específicos:
                # - scontent-*.fbcdn.net (CDN de Facebook)
                # - No tienen "profile", "avatar", "picture" en la URL
                # - Tienen dimensiones en el nombre o parámetros
                
                # Priorizar imágenes que parecen ser del contenido principal
                main_content_images = []
                for img in content_images:
                    # Filtrar imágenes que claramente son del contenido
                    if 'scontent' in img:
                        # Verificar que no sea imagen de perfil o avatar
                        if not any(x in img.lower() for x in ['profile', 'avatar', 'picture', 'rsrc']):
                            # Verificar que tenga dimensiones típicas de imágenes de posts
                            # Las imágenes de posts suelen tener parámetros como _o, _n, o dimensiones
                            if any(x in img for x in ['_o.', '_n.', '&width=', '&height=', '/scontent']):
                                main_content_images.append(img)
                
                if main_content_images:
                    # Seleccionar la imagen más grande (priorizar originales)
                    # _o.jpg = original, _n.jpg = normal, buscar las que no tienen sufijo pequeño
                    large_images = [img for img in main_content_images if '_o.' in img or '_n.' in img]
                    if large_images:
                        image_url = large_images[0]
                    else:
                        # Usar la primera imagen de contenido principal
                        image_url = main_content_images[0]
                    
                    # Limpiar parámetros para obtener mejor calidad
                    if image_url and '?' in image_url:
                        base_url = image_url.split('?')[0]
                        # Si tiene sufijo de tamaño, mantenerlo (es la versión original)
                        if '_o.' in base_url:
                            image_url = base_url
                        elif '_n.' in base_url:
                            image_url = base_url
                        else:
                            # Mantener parámetros que pueden indicar calidad
                            image_url = image_url
                else:
                    # Si no encontramos imágenes principales, usar la primera de contenido
                    # pero asegurarnos de que no sea de perfil
                    filtered = [img for img in content_images if not any(x in img.lower() for x in ['profile', 'avatar', 'picture', 'rsrc'])]
                    if filtered:
                        image_url = filtered[0]
                    else:
                        image_url = content_images[0]
            
            # Método 2: Buscar en elementos con data attributes específicos de Facebook
            if not image_url:
                # Facebook a veces usa data attributes para imágenes
                data_img_elements = post_element.find_all(attrs={'data-img': True})
                for elem in data_img_elements:
                    img_src = elem.get('data-img', '')
                    if img_src and ('fbcdn.net' in img_src or 'facebook.com' in img_src):
                        if 'scontent' in img_src and not any(x in img_src for x in ['/rsrc.php/', 'profile', 'avatar']):
                            image_url = img_src
                            break
            
            # Método 3: Buscar en enlaces de fotos/videos
            if not image_url:
                photo_links = post_element.find_all('a', href=re.compile(r'/photo|/photos|/video'))
                for link in photo_links:
                    # Buscar imagen dentro del enlace
                    img_in_link = link.find('img')
                    if img_in_link:
                        img_src = img_in_link.get('src', '') or img_in_link.get('data-src', '') or img_in_link.get('data-lazy-src', '')
                        if img_src and ('fbcdn.net' in img_src or 'facebook.com' in img_src):
                            if 'scontent' in img_src and not any(x in img_src for x in ['/rsrc.php/', 'profile', 'avatar']):
                                image_url = img_src
                                break
            
            # Método 4: Buscar videos y usar poster como imagen si no hay imagen
            video_tags = post_element.find_all('video')
            for video in video_tags:
                video_src = video.get('src', '') or video.get('data-src', '')
                if video_src and ('fbcdn.net' in video_src or 'facebook.com' in video_src):
                    video_url = video_src
                    # Si no hay imagen, intentar usar el poster del video
                    video_poster = video.get('poster', '') or video.get('data-poster', '')
                    if not image_url and video_poster:
                        if 'scontent' in video_poster and not any(x in video_poster.lower() for x in ['profile', 'avatar', 'picture', 'rsrc']):
                            image_url = video_poster
                            logger.debug(f"✅ Imagen encontrada en poster de video: {video_poster[:50]}...")
                    break
            
            # Método 5: Buscar en elementos con background-image (imágenes de fondo del post)
            if not image_url:
                bg_elements = post_element.find_all(attrs={'style': re.compile(r'background-image')})
                for elem in bg_elements:
                    style = elem.get('style', '')
                    url_match = re.search(r'url\(["\']?([^"\']+)["\']?\)', style)
                    if url_match:
                        bg_url = url_match.group(1)
                        if ('fbcdn.net' in bg_url or 'facebook.com' in bg_url) and 'scontent' in bg_url:
                            # Verificar que no sea imagen de perfil
                            if not any(x in bg_url.lower() for x in ['profile', 'avatar', 'picture', 'rsrc']):
                                image_url = bg_url
                                logger.debug(f"✅ Imagen encontrada en background-image: {bg_url[:50]}...")
                                break
            
            # ===== EXTRACCIÓN DE URL DEL POST =====
            post_url = ""
            
            # Buscar enlaces a posts específicos
            post_links = post_element.find_all('a', href=re.compile(r'/posts/|/photos/|/videos/|/permalink/'))
            for link in post_links:
                href = link.get('href', '')
                if href:
                    if href.startswith('http'):
                        post_url = href
                    else:
                        post_url = "https://facebook.com" + href
                    break
            
            # Si no se encontró URL específica, construir una genérica
            if not post_url and username != "Facebook User":
                username_clean = username.replace(' ', '').lower()
                post_url = f"https://facebook.com/{username_clean}/posts/{random.randint(1000000000, 9999999999)}"
            
            # ===== CONSTRUIR OBJETO DE DATOS =====
            post_data = {
                'platform': 'facebook',
                'username': username,
                'text': text,
                'date': date_str,
                'likes': likes,
                'comments': comments,
                'shares': shares,
                'retweets': 0,  # Facebook no tiene retweets
                'replies': comments,  # Usar comments como replies
                'hashtags': re.findall(r'#\w+', text),
                'url': post_url,
                'image_url': image_url,  # Imagen extraída
                'video_url': video_url,  # Video extraído (si existe)
                'scraped_at': datetime.now().isoformat()
            }
            
            # Retornar si tiene texto o al menos imagen/video
            return post_data if (text or image_url or video_url) else None
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo datos del post de Facebook: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return None
    
    def _parse_metric(self, metric_str: str) -> int:
        """Parsear métricas con formato K, M, B"""
        try:
            metric_str = metric_str.strip().upper()
            if 'K' in metric_str:
                return int(float(metric_str.replace('K', '')) * 1000)
            elif 'M' in metric_str:
                return int(float(metric_str.replace('M', '')) * 1000000)
            elif 'B' in metric_str:
                return int(float(metric_str.replace('B', '')) * 1000000000)
            else:
                return int(metric_str)
        except:
            return 0
    
    def close(self):
        """Cerrar el driver del navegador"""
        if self.driver:
            self.driver.quit()
            logger.info("✅ Driver de Facebook cerrado correctamente")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


class RedditScraper:
    """
    Scraper educativo para Reddit
    
    IMPORTANTE: Este código es solo para fines académicos y educativos.
    Respeta los términos de servicio de Reddit y las leyes locales.
    
    Intenta usar API oficial (PRAW) primero, luego Selenium como fallback.
    """
    
    def __init__(self, headless: bool = True, use_api: bool = True):
        """
        Inicializar el scraper de Reddit
        
        Args:
            headless: Si True, ejecuta el navegador en modo headless (solo Selenium)
            use_api: Si True, intenta usar API primero (requiere credenciales)
        """
        self.headless = headless
        self.use_api = use_api
        self.api_scraper = None
        self.selenium_scraper = None
        
        # Intentar inicializar API scraper
        if use_api and REDDIT_API_AVAILABLE:
            try:
                import os
                client_id = os.getenv('REDDIT_CLIENT_ID')
                client_secret = os.getenv('REDDIT_CLIENT_SECRET')
                user_agent = os.getenv('REDDIT_USER_AGENT')
                
                if client_id and client_secret:
                    self.api_scraper = RedditAPIScraper(client_id, client_secret, user_agent)
                    logger.info("✅ Reddit API scraper inicializado")
                else:
                    logger.info("ℹ️ Credenciales de Reddit no encontradas, usando Selenium como fallback")
            except Exception as e:
                logger.warning(f"⚠️ Error inicializando API scraper: {e}, usando Selenium")
        
        # Inicializar Selenium scraper como fallback
        if REDDIT_SELENIUM_AVAILABLE:
            try:
                self.selenium_scraper = RedditSeleniumScraper(headless=headless)
                logger.info("✅ Reddit Selenium scraper disponible como fallback")
            except Exception as e:
                logger.warning(f"⚠️ Error inicializando Selenium scraper: {e}")
    
    def scrape_subreddit(self, subreddit_name: str, max_posts: int = 100, sort: str = 'hot') -> List[Dict]:
        """
        Scrapear posts de un subreddit
        
        Args:
            subreddit_name: Nombre del subreddit (ej: 'python', 'technology')
            max_posts: Número máximo de posts
            sort: Orden ('hot', 'new', 'top', 'rising')
        
        Returns:
            Lista de diccionarios con datos de los posts
        """
        # Intentar API primero
        if self.api_scraper:
            try:
                logger.info(f"📡 Intentando extraer posts de r/{subreddit_name} usando API...")
                posts = self.api_scraper.get_subreddit_posts(subreddit_name, max_posts, sort)
                if posts and len(posts) > 0:
                    logger.info(f"✅ ✅ ✅ API EXITOSA: {len(posts)} posts extraídos de r/{subreddit_name}")
                    return posts
                else:
                    logger.warning(f"⚠️ API no retornó posts, intentando Selenium...")
            except Exception as e:
                logger.warning(f"⚠️ Error con API: {e}, intentando Selenium...")

        # Intentar fallback con endpoints JSON públicos de Reddit
        json_posts = self._scrape_subreddit_json(subreddit_name, max_posts, sort)
        if json_posts and len(json_posts) > 0:
            logger.info(f"✅ ✅ ✅ JSON EXITOSO: {len(json_posts)} posts extraídos de r/{subreddit_name}")
            return json_posts
        
        # Fallback a Selenium
        if self.selenium_scraper:
            try:
                logger.info(f"🌐 Intentando extraer posts de r/{subreddit_name} usando Selenium...")
                posts = self.selenium_scraper.scrape_subreddit(subreddit_name, max_posts, sort)
                if posts and len(posts) > 0:
                    logger.info(f"✅ ✅ ✅ SELENIUM EXITOSO: {len(posts)} posts extraídos de r/{subreddit_name}")
                    return posts
            except Exception as e:
                logger.error(f"❌ Error con Selenium: {e}")
        
        logger.error(f"❌ No se pudieron extraer posts de r/{subreddit_name}")
        return []
    
    def search_posts(self, query: str, subreddit: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """
        Buscar posts en Reddit
        
        Args:
            query: Término de búsqueda
            subreddit: Subreddit específico (opcional)
            limit: Número máximo de posts
        
        Returns:
            Lista de diccionarios con datos de los posts
        """
        # Intentar API primero
        if self.api_scraper:
            try:
                logger.info(f"📡 Buscando posts con query: '{query}' usando API...")
                posts = self.api_scraper.search_posts(query, subreddit, limit)
                if posts and len(posts) > 0:
                    logger.info(f"✅ ✅ ✅ API EXITOSA: {len(posts)} posts encontrados")
                    return posts
            except Exception as e:
                logger.warning(f"⚠️ Error con API: {e}")

        # Intentar fallback con endpoints JSON públicos de Reddit
        json_posts = self._search_posts_json(query, subreddit, limit)
        if json_posts and len(json_posts) > 0:
            logger.info(f"✅ ✅ ✅ JSON EXITOSO: {len(json_posts)} posts encontrados")
            return json_posts
        
        if self.selenium_scraper:
            try:
                logger.info(f"🌐 Buscando posts con Selenium para query: '{query}'...")
                posts = self.selenium_scraper.search_posts(query, max_posts=limit, subreddit=subreddit)
                if posts and len(posts) > 0:
                    logger.info(f"✅ ✅ ✅ SELENIUM EXITOSO: {len(posts)} posts encontrados")
                    return posts
                else:
                    logger.warning("⚠️ Selenium no obtuvo resultados para la búsqueda")
            except Exception as e:
                logger.error(f"❌ Error con Selenium en búsqueda: {e}")
        
        # Fallback final: usar requests + BeautifulSoup sobre old.reddit.com
        try:
            logger.info(f"🌐 Intentando búsqueda con requests para query: '{query}'...")
            posts = self._search_posts_requests(query, subreddit, limit)
            if posts and len(posts) > 0:
                logger.info(f"✅ ✅ ✅ Requests EXITOSO: {len(posts)} posts encontrados")
                return posts
        except Exception as e:
            logger.error(f"❌ Error en fallback requests para búsqueda de Reddit: {e}")
        
        logger.error(f"❌ No se pudieron obtener resultados para búsqueda en Reddit")
        return []
    
    def close(self):
        """Cerrar recursos"""
        if self.selenium_scraper:
            try:
                self.selenium_scraper.close()
            except:
                pass
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def _fetch_reddit_json(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Realiza una petición a los endpoints JSON públicos de Reddit"""
        try:
            response = requests.get(
                url,
                headers=REDDIT_REQUEST_HEADERS,
                params=params or {},
                timeout=20
            )
            if response.status_code == 200:
                return response.json()
            logger.warning(f"⚠️ Petición JSON a Reddit retornó status {response.status_code} para URL: {response.url}")
        except Exception as e:
            logger.error(f"❌ Error consultando Reddit JSON ({url}): {e}")
        return None

    def _clean_reddit_media_url(self, url: Optional[str]) -> Optional[str]:
        if not url or not isinstance(url, str):
            return None
        cleaned = html.unescape(url.strip())
        if cleaned.startswith('//'):
            cleaned = f"https:{cleaned}"
        return cleaned

    def _normalize_reddit_json_post(self, data: Dict) -> Optional[Dict]:
        """Normaliza la estructura de un post obtenido vía JSON"""
        if not data:
            return None

        try:
            post_id = data.get('id') or data.get('name')
            if not post_id:
                return None

            title = html.unescape((data.get('title') or '').strip())
            selftext = html.unescape((data.get('selftext') or '').strip())
            author = data.get('author') or 'unknown'
            subreddit = data.get('subreddit') or 'all'

            created_utc = data.get('created_utc')
            if created_utc:
                created_at = datetime.utcfromtimestamp(created_utc).isoformat()
            else:
                created_at = datetime.utcnow().isoformat()

            permalink = data.get('permalink') or data.get('url') or ''
            if permalink and permalink.startswith('/'):
                permalink = f"https://www.reddit.com{permalink}"
            permalink = self._clean_reddit_media_url(permalink)

            image_url = None
            video_url = None

            post_hint = data.get('post_hint') or ''
            url_overridden = data.get('url_overridden_by_dest') or data.get('url')

            if post_hint == 'image' and url_overridden:
                image_url = self._clean_reddit_media_url(url_overridden)
            elif data.get('preview', {}).get('images'):
                try:
                    preview_image = data['preview']['images'][0]['source']['url']
                    image_url = self._clean_reddit_media_url(preview_image)
                except Exception:
                    image_url = None
            elif data.get('thumbnail') and data.get('thumbnail_width', 0):
                image_url = self._clean_reddit_media_url(data.get('thumbnail'))

            media = data.get('media') or data.get('secure_media') or {}
            reddit_video = media.get('reddit_video') if isinstance(media, dict) else None
            if reddit_video and isinstance(reddit_video, dict):
                video_url = self._clean_reddit_media_url(reddit_video.get('fallback_url'))
            elif url_overridden and any(url_overridden.endswith(ext) for ext in ('.mp4', '.gif', '.gifv', '.webm')):
                video_url = self._clean_reddit_media_url(url_overridden)

            return {
                'id': post_id,
                'platform': 'reddit',
                'title': title,
                'content': selftext or title,
                'author': author,
                'subreddit': subreddit,
                'score': data.get('score', 0),
                'upvotes': data.get('ups', data.get('score', 0)),
                'downvotes': data.get('downs', 0),
                'comments': data.get('num_comments', 0),
                'num_comments': data.get('num_comments', 0),
                'permalink': permalink,
                'url': permalink,
                'image_url': image_url,
                'video_url': video_url,
                'created_at': created_at,
                'scraped_at': datetime.utcnow().isoformat(),
                'flair': data.get('link_flair_text'),
                'stickied': data.get('stickied', False),
                'is_self': data.get('is_self', False)
            }
        except Exception as e:
            logger.debug(f"⚠️ Error normalizando post de Reddit: {e}")
            return None

    def _extract_posts_from_listing(self, listing: Optional[Dict], limit: int, seen_ids: set) -> List[Dict]:
        posts: List[Dict] = []
        if not listing:
            return posts

        children = listing.get('data', {}).get('children', [])
        for child in children:
            if not isinstance(child, dict):
                continue
            data = child.get('data', {})
            if not data or data.get('stickied'):
                continue
            normalized = self._normalize_reddit_json_post(data)
            if not normalized:
                continue
            post_id = normalized.get('id')
            if post_id and post_id in seen_ids:
                continue
            if post_id:
                seen_ids.add(post_id)
            posts.append(normalized)
            if len(posts) >= limit:
                break

        return posts

    def _scrape_subreddit_json(self, subreddit_name: str, max_posts: int, sort: str) -> List[Dict]:
        if not subreddit_name:
            return []

        sort_clean = sort if sort in {'hot', 'new', 'top', 'rising', 'controversial'} else 'hot'
        base_url = f"https://www.reddit.com/r/{subreddit_name}/{sort_clean}.json" if sort_clean != 'hot' else f"https://www.reddit.com/r/{subreddit_name}.json"

        collected: List[Dict] = []
        after = None
        attempts = 0
        seen_ids: set = set()

        while len(collected) < max_posts and attempts < 5:
            params = {
                'limit': min(100, max_posts - len(collected))
            }
            if after:
                params['after'] = after

            listing = self._fetch_reddit_json(base_url, params)
            if not listing:
                break

            new_posts = self._extract_posts_from_listing(listing, max_posts - len(collected), seen_ids)
            if not new_posts:
                break

            collected.extend(new_posts)
            after = listing.get('data', {}).get('after')
            attempts += 1

            if not after:
                break

            time.sleep(1)  # Evitar rate-limits

        return collected[:max_posts]

    def _search_posts_json(self, query: str, subreddit: Optional[str], limit: int) -> List[Dict]:
        if not query or len(query.strip()) == 0:
            return []

        collected: List[Dict] = []
        after = None
        attempts = 0
        seen_ids: set = set()

        base_url = "https://www.reddit.com/search.json"

        while len(collected) < limit and attempts < 5:
            params = {
                'q': query,
                'limit': min(100, limit - len(collected)),
                'sort': 'new',
                'type': 'link'
            }
            if subreddit:
                params['restrict_sr'] = 'on'
                params['sr'] = subreddit
            if after:
                params['after'] = after

            listing = self._fetch_reddit_json(base_url, params)
            if not listing:
                break

            new_posts = self._extract_posts_from_listing(listing, limit - len(collected), seen_ids)
            if not new_posts:
                break

            collected.extend(new_posts)
            after = listing.get('data', {}).get('after')
            attempts += 1

            if not after:
                break

            time.sleep(1)  # Evitar rate-limits

        return collected[:limit]

    def _search_posts_requests(self, query: str, subreddit: Optional[str], limit: int) -> List[Dict]:
        """Fallback de búsqueda usando requests + BeautifulSoup sobre old.reddit.com"""
        if not query or len(query.strip()) == 0:
            return []

        from urllib.parse import quote_plus

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Safari/537.36'
        }

        query_clean = quote_plus(query.strip())
        if subreddit:
            url = f"https://old.reddit.com/r/{subreddit}/search/?q={query_clean}&restrict_sr=on&sort=new"
        else:
            url = f"https://old.reddit.com/search/?q={query_clean}&sort=new"

        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code != 200:
                logger.warning(f"⚠️ Búsqueda requests devolvió status {response.status_code} para URL: {url}")
                return []
        except Exception as e:
            logger.error(f"❌ Error realizando request de búsqueda a Reddit: {e}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        results = soup.select('div.search-result')
        posts: List[Dict] = []

        for result in results:
            if len(posts) >= limit:
                break

            classes = result.get('class', [])
            if any('search-result-subreddit' in cls for cls in classes):
                # Omitir resultados que solo son subreddits/usuarios
                continue

            try:
                title_elem = result.select_one('a.search-title')
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)
                post_url = title_elem['href'] if title_elem.has_attr('href') else ''

                subreddit_name = subreddit or ''
                subreddit_elem = result.select_one('a.search-subreddit-link')
                if subreddit_elem:
                    subreddit_text = subreddit_elem.get_text(strip=True)
                    if subreddit_text.startswith('r/'):
                        subreddit_name = subreddit_text.replace('r/', '').strip()
                    else:
                        subreddit_name = subreddit_text

                author = 'Unknown'
                author_elem = result.select_one('a.search-author')
                if author_elem:
                    author = author_elem.get_text(strip=True)

                score = 0
                score_elem = result.select_one('span.search-score')
                if score_elem:
                    score = self._parse_reddit_score_text(score_elem.get_text(strip=True))

                comments = 0
                comments_elem = result.select_one('a.search-comments')
                if comments_elem:
                    comments = self._parse_reddit_comment_text(comments_elem.get_text(strip=True))

                created_at = datetime.now().isoformat()
                time_elem = result.select_one('time')
                if time_elem and time_elem.has_attr('datetime'):
                    created_at = time_elem['datetime']

                image_url = None
                thumb_elem = result.select_one('a.thumbnail img')
                if thumb_elem and thumb_elem.has_attr('src'):
                    img_src = thumb_elem['src']
                    if img_src and 'default' not in img_src.lower():
                        if 'thumbs.redditmedia.com' in img_src:
                            image_url = img_src.replace('_b.jpg', '.jpg').replace('_thumb', '')
                        else:
                            image_url = img_src

                content = ''
                body_elem = result.select_one('div.search-result-body') or result.select_one('div.search-result-content')
                if body_elem:
                    content = body_elem.get_text(strip=True)
                if not content or len(content) < 5:
                    content = title

                posts.append({
                    'id': result.get('data-fullname') or post_url or title,
                    'platform': 'reddit',
                    'title': title,
                    'content': content,
                    'author': author,
                    'subreddit': subreddit_name or 'all',
                    'score': score,
                    'upvotes': score,
                    'downvotes': 0,
                    'comments': comments,
                    'url': post_url,
                    'permalink': post_url,
                    'created_at': created_at,
                    'image_url': image_url,
                    'scraped_at': datetime.now().isoformat()
                })

            except Exception as e:
                logger.debug(f"⚠️ Error procesando resultado de búsqueda (requests): {e}")
                continue

        return posts

    def _parse_reddit_score_text(self, text: str) -> int:
        """Parsear texto de score obtenido vía requests"""
        if not text:
            return 0
        text = text.lower()
        match = re.search(r'(\d+[\.,]?\d*)([km]?)', text)
        if not match:
            return 0
        number = float(match.group(1).replace(',', '.'))
        suffix = match.group(2)
        if suffix == 'k':
            number *= 1000
        elif suffix == 'm':
            number *= 1000000
        return int(number)

    def _parse_reddit_comment_text(self, text: str) -> int:
        """Parsear texto de comentarios obtenido vía requests"""
        if not text:
            return 0
        match = re.search(r'(\d+[\.,]?\d*)([km]?)', text.lower())
        if not match:
            return 0
        number = float(match.group(1).replace(',', '.'))
        suffix = match.group(2)
        if suffix == 'k':
            number *= 1000
        elif suffix == 'm':
            number *= 1000000
        return int(number)


class YouTubeScraper:
    """
    Scraper educativo para YouTube.

    Intenta utilizar primero la API oficial (cuando hay API key disponible)
    y utiliza Selenium como fallback para canales sin API.
    """

    def __init__(self, headless: bool = True, use_api: bool = True):
        self.headless = headless
        self.use_api = use_api
        self.api_scraper = None
        self.selenium_scraper = None

        if use_api and YOUTUBE_API_AVAILABLE:
            try:
                import os
                api_key = os.getenv('YOUTUBE_API_KEY') or os.getenv('GOOGLE_API_KEY')
                if api_key:
                    self.api_scraper = YouTubeAPIScraper(api_key)
                    logger.info("✅ YouTube API scraper inicializado")
                else:
                    logger.info("ℹ️ API key de YouTube no encontrada, usando Selenium como fallback")
            except Exception as e:
                logger.warning(f"⚠️ Error inicializando YouTubeAPIScraper: {e}")

        if YOUTUBE_SELENIUM_AVAILABLE:
            try:
                self.selenium_scraper = YouTubeSeleniumScraper(headless=headless)
                logger.info("✅ YouTube Selenium scraper disponible como fallback")
            except Exception as e:
                logger.warning(f"⚠️ Error inicializando YouTube Selenium scraper: {e}")

    def get_channel_videos(self, channel_identifier: str, max_results: int = 50) -> List[Dict]:
        if self.api_scraper:
            try:
                videos = self.api_scraper.get_channel_videos(channel_identifier, max_results)
                if videos:
                    logger.info(f"✅ API devolvió {len(videos)} videos para {channel_identifier}")
                    return videos
            except Exception as e:
                logger.warning(f"⚠️ Error usando API de YouTube: {e}. Probando Selenium")

        if self.selenium_scraper:
            try:
                return self.selenium_scraper.scrape_channel(channel_identifier, max_results)
            except Exception as e:
                logger.error(f"❌ Error usando Selenium para YouTube: {e}")

        logger.error("❌ No se pudieron obtener videos del canal")
        return []

    def search_videos(self, query: str, max_results: int = 50) -> List[Dict]:
        if self.api_scraper:
            try:
                videos = self.api_scraper.search_videos(query, max_results)
                if videos:
                    logger.info(f"✅ API devolvió {len(videos)} resultados para búsqueda '{query}'")
                    return videos
            except Exception as e:
                logger.warning(f"⚠️ Error usando API de YouTube para búsqueda: {e}")

        if self.selenium_scraper:
            try:
                return self.selenium_scraper.search_videos(query, max_results)
            except Exception as e:
                logger.error(f"❌ Error usando Selenium para búsqueda en YouTube: {e}")

        logger.error("❌ No se pudieron buscar videos en YouTube")
        return []

    def close(self):
        if self.selenium_scraper:
            try:
                self.selenium_scraper.close()
            except Exception:
                pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def scrape_twitter(query: str, 
                   max_tweets: int = 50,
                   filter_language: Optional[str] = None,
                   headless: bool = True) -> List[Dict]:
    """
    Función helper para scraping rápido de Twitter
    
    Args:
        query: Hashtag o palabra clave
        max_tweets: Máximo de tweets (máx 50)
        filter_language: Idioma (ej: 'es', 'en')
        headless: Modo headless
    
    Returns:
        Lista de tweets extraídos
    """
    with TwitterScraper(headless=headless) as scraper:
        return scraper.search_tweets(query, max_tweets, filter_language)


if __name__ == "__main__":
    """
    Ejemplo de uso educativo
    
    IMPORTANTE: Este código es solo para fines académicos.
    """
    print("=" * 60)
    print("🔬 PROYECTO ACADÉMICO - Web Scraping de Twitter/X")
    print("=" * 60)
    print("⚠️  DISCLAIMER: Solo para fines educativos y aprendizaje")
    print("=" * 60)
    print()
    
    # Ejemplo: Scraping de 20 tweets sobre tecnología
    try:
        tweets = scrape_twitter(
            query="#tecnologia",
            max_tweets=20,
            filter_language="es",
            headless=True
        )
        
        print(f"\n✅ Tweets extraídos: {len(tweets)}\n")
        
        # Mostrar primeros 3 tweets como ejemplo
        for i, tweet in enumerate(tweets[:3], 1):
            print(f"📱 Tweet {i}:")
            print(f"   Usuario: {tweet.get('username', 'N/A')}")
            print(f"   Texto: {tweet.get('text', 'N/A')[:100]}...")
            print(f"   Likes: {tweet.get('likes', 0)}")
            print(f"   Retweets: {tweet.get('retweets', 0)}")
            print(f"   Hashtags: {', '.join(tweet.get('hashtags', []))}")
            print()
        
        print("=" * 60)
        print("✅ Scraping completado exitosamente")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Asegúrate de tener ChromeDriver instalado y en PATH")

