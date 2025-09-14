#!/usr/bin/env python3
"""
Crawler con paginación automática
Detecta y navega por todas las páginas disponibles
"""

import requests
from bs4 import BeautifulSoup
import logging
import json
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

logger = logging.getLogger(__name__)

class PaginationCrawler:
    """Crawler inteligente con paginación automática"""
    
    def __init__(self, use_selenium=True):
        self.use_selenium = use_selenium
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        self.driver = None
        if use_selenium:
            self._setup_selenium()
    
    def _setup_selenium(self):
        """Configurar Selenium WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            logger.info("✅ Selenium WebDriver configurado")
        except Exception as e:
            logger.warning(f"⚠️ Error configurando Selenium: {e}")
            self.use_selenium = False
    
    def detect_pagination_type(self, url):
        """Detectar tipo de paginación en la página"""
        try:
            if self.use_selenium and self.driver:
                return self._detect_pagination_selenium(url)
            else:
                return self._detect_pagination_requests(url)
        except Exception as e:
            logger.error(f"❌ Error detectando paginación: {e}")
            return {'type': 'none', 'pages': []}
    
    def _detect_pagination_selenium(self, url):
        """Detectar paginación usando Selenium"""
        try:
            self.driver.get(url)
            time.sleep(3)  # Esperar carga inicial
            
            pagination_info = {
                'type': 'none',
                'pages': [],
                'next_button': None,
                'load_more_button': None,
                'current_page': 1
            }
            
            # Buscar botón "VER MÁS" o "Cargar más"
            load_more_selectors = [
                "//button[contains(text(), 'VER MÁS')]",
                "//button[contains(text(), 'Cargar más')]",
                "//button[contains(text(), 'Load more')]",
                "//button[contains(text(), 'Más')]",
                "//a[contains(text(), 'VER MÁS')]",
                "//a[contains(text(), 'Cargar más')]",
                "//a[contains(text(), 'Más')]",
                "//*[contains(@class, 'load-more')]",
                "//*[contains(@class, 'ver-mas')]",
                "//*[contains(@class, 'mas')]",
                "//*[contains(@id, 'load-more')]",
                "//*[contains(@id, 'ver-mas')]",
                "//*[contains(@id, 'mas')]",
                "//*[contains(text(), 'VER MÁS')]",
                "//*[contains(text(), 'Más')]"
            ]
            
            for selector in load_more_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    if element.is_displayed():
                        pagination_info['type'] = 'load_more'
                        pagination_info['load_more_button'] = element
                        logger.info(f"✅ Botón 'VER MÁS' encontrado: {selector}")
                        break
                except NoSuchElementException:
                    continue
            
            # Buscar paginación numérica (1 2 3 >)
            pagination_selectors = [
                "//div[contains(@class, 'pagination')]",
                "//nav[contains(@class, 'pagination')]",
                "//ul[contains(@class, 'pagination')]",
                "//div[contains(@class, 'pager')]",
                "//nav[contains(@class, 'pager')]",
                "//*[contains(@class, 'page-numbers')]"
            ]
            
            for selector in pagination_selectors:
                try:
                    pagination_container = self.driver.find_element(By.XPATH, selector)
                    if pagination_container.is_displayed():
                        # Buscar enlaces de páginas
                        page_links = pagination_container.find_elements(By.TAG_NAME, "a")
                        pages = []
                        
                        for link in page_links:
                            text = link.text.strip()
                            href = link.get_attribute('href')
                            
                            if text.isdigit():
                                pages.append({
                                    'number': int(text),
                                    'url': href,
                                    'element': link
                                })
                            elif text in ['>', 'Siguiente', 'Next']:
                                pagination_info['next_button'] = link
                        
                        if pages:
                            pagination_info['type'] = 'numbered'
                            pagination_info['pages'] = sorted(pages, key=lambda x: x['number'])
                            logger.info(f"✅ Paginación numérica encontrada: {len(pages)} páginas")
                            break
                            
                except NoSuchElementException:
                    continue
            
            return pagination_info
            
        except Exception as e:
            logger.error(f"❌ Error en detección Selenium: {e}")
            return {'type': 'none', 'pages': []}
    
    def _detect_pagination_requests(self, url):
        """Detectar paginación usando requests"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            pagination_info = {
                'type': 'none',
                'pages': [],
                'next_button': None,
                'load_more_button': None,
                'current_page': 1
            }
            
            # Buscar botón "VER MÁS"
            load_more_selectors = [
                'button:contains("VER MÁS")',
                'button:contains("Cargar más")',
                'a:contains("VER MÁS")',
                'a:contains("Cargar más")',
                '.load-more',
                '.ver-mas',
                '#load-more',
                '#ver-mas'
            ]
            
            for selector in load_more_selectors:
                elements = soup.select(selector)
                if elements:
                    pagination_info['type'] = 'load_more'
                    logger.info(f"✅ Botón 'VER MÁS' encontrado: {selector}")
                    break
            
            # Buscar paginación numérica
            pagination_selectors = [
                '.pagination',
                '.pager',
                '.page-numbers',
                'nav[class*="pagination"]',
                'div[class*="pagination"]'
            ]
            
            for selector in pagination_selectors:
                pagination_container = soup.select_one(selector)
                if pagination_container:
                    page_links = pagination_container.find_all('a')
                    pages = []
                    
                    for link in page_links:
                        text = link.get_text(strip=True)
                        href = link.get('href')
                        
                        if text.isdigit():
                            pages.append({
                                'number': int(text),
                                'url': urljoin(url, href) if href else None
                            })
                        elif text in ['>', 'Siguiente', 'Next']:
                            pagination_info['next_button'] = urljoin(url, href) if href else None
                    
                    if pages:
                        pagination_info['type'] = 'numbered'
                        pagination_info['pages'] = sorted(pages, key=lambda x: x['number'])
                        logger.info(f"✅ Paginación numérica encontrada: {len(pages)} páginas")
                        break
            
            return pagination_info
            
        except Exception as e:
            logger.error(f"❌ Error en detección requests: {e}")
            return {'type': 'none', 'pages': []}
    
    def crawl_all_pages(self, url, max_articles=100, extract_articles_func=None):
        """Extraer artículos de todas las páginas disponibles"""
        all_articles = []
        seen_urls = set()
        
        try:
            logger.info(f"🔍 Iniciando crawl con paginación: {url}")
            
            # Detectar tipo de paginación
            pagination_info = self.detect_pagination_type(url)
            logger.info(f"📄 Tipo de paginación detectado: {pagination_info['type']}")
            
            if pagination_info['type'] == 'none':
                logger.info("ℹ️ No se detectó paginación, extrayendo solo página actual")
                if extract_articles_func:
                    articles = extract_articles_func(url)
                    return articles
                return []
            
            # Manejar paginación numérica (1 2 3 >)
            if pagination_info['type'] == 'numbered':
                all_articles = self._crawl_numbered_pages(
                    url, pagination_info, max_articles, extract_articles_func, seen_urls
                )
            
            # Manejar botón "VER MÁS"
            elif pagination_info['type'] == 'load_more':
                all_articles = self._crawl_load_more_pages(
                    url, pagination_info, max_articles, extract_articles_func, seen_urls
                )
            
            logger.info(f"🎉 Crawl completado: {len(all_articles)} artículos únicos extraídos")
            return all_articles
            
        except Exception as e:
            logger.error(f"❌ Error en crawl con paginación: {e}")
            return all_articles
    
    def _crawl_numbered_pages(self, base_url, pagination_info, max_articles, extract_func, seen_urls):
        """Extraer de páginas numeradas"""
        all_articles = []
        
        try:
            # Extraer página actual
            if extract_func:
                articles = extract_func(base_url)
                for article in articles:
                    if article.get('url') not in seen_urls:
                        seen_urls.add(article.get('url'))
                        all_articles.append(article)
            
            # Extraer páginas numeradas
            for page_info in pagination_info['pages']:
                if len(all_articles) >= max_articles:
                    break
                
                page_url = page_info['url']
                if not page_url:
                    continue
                
                logger.info(f"📄 Extrayendo página {page_info['number']}: {page_url}")
                
                if extract_func:
                    articles = extract_func(page_url)
                    for article in articles:
                        if article.get('url') not in seen_urls and len(all_articles) < max_articles:
                            seen_urls.add(article.get('url'))
                            all_articles.append(article)
                
                time.sleep(1)  # Pausa entre páginas
            
            return all_articles
            
        except Exception as e:
            logger.error(f"❌ Error en crawl numerado: {e}")
            return all_articles
    
    def _crawl_load_more_pages(self, url, pagination_info, max_articles, extract_func, seen_urls):
        """Extraer usando botón 'VER MÁS'"""
        all_articles = []
        
        if not self.use_selenium or not self.driver:
            logger.warning("⚠️ Selenium no disponible para botón 'VER MÁS'")
            return all_articles
        
        try:
            self.driver.get(url)
            time.sleep(3)
            
            # Extraer contenido inicial
            if extract_func:
                articles = extract_func(url)
                for article in articles:
                    if article.get('url') not in seen_urls:
                        seen_urls.add(article.get('url'))
                        all_articles.append(article)
            
            # Hacer clic en "VER MÁS" repetidamente
            max_clicks = 10  # Límite de seguridad
            clicks = 0
            
            while len(all_articles) < max_articles and clicks < max_clicks:
                try:
                    # Buscar botón "VER MÁS"
                    load_more_button = None
                    load_more_selectors = [
                        "//button[contains(text(), 'VER MÁS')]",
                        "//button[contains(text(), 'Cargar más')]",
                        "//a[contains(text(), 'VER MÁS')]",
                        "//*[contains(@class, 'load-more')]"
                    ]
                    
                    for selector in load_more_selectors:
                        try:
                            element = self.driver.find_element(By.XPATH, selector)
                            if element.is_displayed() and element.is_enabled():
                                load_more_button = element
                                break
                        except NoSuchElementException:
                            continue
                    
                    if not load_more_button:
                        logger.info("ℹ️ No se encontró más botón 'VER MÁS'")
                        break
                    
                    # Hacer clic
                    self.driver.execute_script("arguments[0].click();", load_more_button)
                    clicks += 1
                    logger.info(f"🔄 Clic #{clicks} en 'VER MÁS'")
                    
                    # Esperar carga de nuevo contenido
                    time.sleep(3)
                    
                    # Extraer nuevos artículos
                    if extract_func:
                        articles = extract_func(self.driver.current_url)
                        new_articles = 0
                        for article in articles:
                            if article.get('url') not in seen_urls and len(all_articles) < max_articles:
                                seen_urls.add(article.get('url'))
                                all_articles.append(article)
                                new_articles += 1
                        
                        if new_articles == 0:
                            logger.info("ℹ️ No se encontraron nuevos artículos")
                            break
                        
                        logger.info(f"✅ {new_articles} nuevos artículos extraídos")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error en clic #{clicks}: {e}")
                    break
            
            return all_articles
            
        except Exception as e:
            logger.error(f"❌ Error en crawl 'VER MÁS': {e}")
            return all_articles
    
    def close(self):
        """Cerrar recursos"""
        if self.driver:
            self.driver.quit()
        self.session.close()

def create_pagination_crawler(use_selenium=True):
    """Crear instancia del crawler con paginación"""
    return PaginationCrawler(use_selenium=use_selenium)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Ejemplo de uso
    crawler = create_pagination_crawler(use_selenium=True)
    try:
        # Función de ejemplo para extraer artículos
        def extract_articles_example(url):
            # Esta función debe ser implementada según el sitio específico
            return []
        
        articles = crawler.crawl_all_pages(
            "https://example.com/news",
            max_articles=50,
            extract_articles_func=extract_articles_example
        )
        print(f"Artículos extraídos: {len(articles)}")
    finally:
        crawler.close()
