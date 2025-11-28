#!/usr/bin/env python3
"""
Scraper específico para El Peruano usando Selenium
Maneja contenido dinámico y paginación
"""

import logging
import json
from datetime import datetime
from urllib.parse import urljoin, urlparse
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

class ElPeruanoSeleniumScraper:
    """Scraper específico para El Peruano usando Selenium"""
    
    def __init__(self):
        self.driver = None
        self._setup_selenium()
    
    def _setup_selenium(self):
        """Configurar Selenium WebDriver"""
        try:
            chrome_options = Options()
            # chrome_options.add_argument('--headless')  # Comentado para debugging
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            service = Service('/usr/local/bin/chromedriver')
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.set_page_load_timeout(30)
            logger.info("✅ Selenium WebDriver configurado para El Peruano")
        except Exception as e:
            logger.error(f"❌ Error configurando Selenium: {e}")
            raise
    
    def scrape_economia_with_pagination(self, max_articles=50):
        """Scraper específico para la sección de economía con paginación"""
        url = "https://elperuano.pe/economia"
        
        try:
            logger.info(f"🔍 Scrapeando El Peruano - Economía con Selenium: {url}")
            self.driver.get(url)
            time.sleep(5)  # Esperar carga inicial
            
            all_articles = []
            seen_urls = set()
            page_count = 0
            max_pages = 10  # Límite de seguridad
            
            while len(all_articles) < max_articles and page_count < max_pages:
                page_count += 1
                logger.info(f"📄 Procesando página {page_count}")
                
                # Extraer artículos de la página actual
                articles = self._extract_articles_from_current_page()
                new_articles = 0
                
                for article in articles:
                    if article.get('url') not in seen_urls and len(all_articles) < max_articles:
                        seen_urls.add(article.get('url'))
                        all_articles.append(article)
                        new_articles += 1
                
                logger.info(f"✅ {new_articles} nuevos artículos extraídos de página {page_count}")
                
                # Buscar y hacer clic en "VER MÁS" o siguiente página
                if not self._navigate_to_next_page():
                    logger.info("ℹ️ No se encontró más contenido, finalizando")
                    break
                
                time.sleep(3)  # Pausa entre páginas
            
            logger.info(f"🎉 Total artículos extraídos: {len(all_articles)}")
            return all_articles
            
        except Exception as e:
            logger.error(f"❌ Error scrapeando El Peruano: {e}")
            return []
    
    def _extract_articles_from_current_page(self):
        """Extraer artículos de la página actual"""
        articles = []
        
        try:
            # Esperar a que cargue el contenido
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Buscar artículos usando múltiples estrategias
            article_selectors = [
                # Selectores específicos para El Peruano
                "article",
                ".noticia",
                ".articulo", 
                ".news-item",
                ".content-item",
                "div[class*='noticia']",
                "div[class*='articulo']",
                "div[class*='news']",
                "div[class*='content']",
                # Selectores más genéricos
                "h2 a",
                "h3 a", 
                "h4 a",
                ".title a",
                ".headline a",
                "a[href*='/noticia']",
                "a[href*='/articulo']",
                "a[href*='/economia']",
                # Selectores más amplios
                "a[href*='elperuano.pe']",
                ".entry-title a",
                ".post-title a"
            ]
            
            found_links = set()
            
            for selector in article_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    logger.info(f"🔍 Selector '{selector}': {len(elements)} elementos encontrados")
                    
                    for element in elements:
                        try:
                            # Si es un enlace directo
                            if element.tag_name == 'a':
                                link = element.get_attribute('href')
                                title = element.text.strip()
                            # Si es un contenedor con enlace
                            else:
                                link_elem = element.find_element(By.TAG_NAME, "a")
                                if link_elem:
                                    link = link_elem.get_attribute('href')
                                    title = link_elem.text.strip()
                                else:
                                    continue
                            
                            if not link or not title or len(title) < 10:
                                continue
                            
                            # Filtrar enlaces no relevantes
                            if any(skip in link.lower() for skip in ['javascript:', 'mailto:', '#', 'facebook', 'twitter', 'instagram', 'youtube']):
                                continue
                            
                            # Evitar duplicados
                            if link in found_links:
                                continue
                            found_links.add(link)
                            
                            # Extraer contenido del artículo
                            article_data = self._extract_article_content_selenium(link, title)
                            if article_data:
                                articles.append(article_data)
                                logger.info(f"✅ Artículo extraído: {title[:50]}...")
                                
                        except Exception as e:
                            logger.warning(f"⚠️ Error procesando elemento: {e}")
                            continue
                    
                    if len(articles) > 0:  # Si encontramos artículos, no necesitamos más selectores
                        break
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error con selector '{selector}': {e}")
                    continue
            
            logger.info(f"📄 Artículos extraídos de página actual: {len(articles)}")
            return articles
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo artículos: {e}")
            return []
    
    def _navigate_to_next_page(self):
        """Navegar a la siguiente página"""
        try:
            # Buscar botón "VER MÁS" o enlaces de paginación
            next_selectors = [
                "//button[contains(text(), 'VER MÁS')]",
                "//button[contains(text(), 'Cargar más')]",
                "//button[contains(text(), 'Más')]",
                "//a[contains(text(), 'VER MÁS')]",
                "//a[contains(text(), 'Cargar más')]",
                "//a[contains(text(), 'Más')]",
                "//a[contains(text(), 'Siguiente')]",
                "//a[contains(text(), '>')]",
                "//*[contains(@class, 'load-more')]",
                "//*[contains(@class, 'ver-mas')]",
                "//*[contains(@class, 'pagination')]//a[contains(text(), '>')]",
                "//*[contains(@class, 'pager')]//a[contains(text(), '>')]"
            ]
            
            for selector in next_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    if element.is_displayed() and element.is_enabled():
                        # Hacer scroll hasta el elemento
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                        time.sleep(1)
                        
                        # Hacer clic
                        self.driver.execute_script("arguments[0].click();", element)
                        logger.info(f"🔄 Navegando a siguiente página: {selector}")
                        time.sleep(3)  # Esperar carga
                        return True
                        
                except NoSuchElementException:
                    continue
                except Exception as e:
                    logger.warning(f"⚠️ Error con selector '{selector}': {e}")
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error navegando a siguiente página: {e}")
            return False
    
    def _extract_article_content_selenium(self, url, title):
        """Extraer contenido de un artículo específico usando Selenium"""
        try:
            # Abrir artículo en nueva pestaña
            self.driver.execute_script(f"window.open('{url}', '_blank');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            time.sleep(2)
            
            # Extraer contenido
            content = ""
            content_selectors = [
                '.articulo-contenido',
                '.noticia-contenido', 
                '.article-content',
                '.content',
                '.texto',
                'article',
                '.main-content',
                'div[class*="contenido"]',
                'div[class*="texto"]',
                '.entry-content',
                '.post-content'
            ]
            
            for selector in content_selectors:
                try:
                    content_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if content_elem:
                        content = content_elem.text.strip()
                        break
                except NoSuchElementException:
                    continue
            
            # Si no se encuentra contenido específico, usar todo el body
            if not content:
                try:
                    body = self.driver.find_element(By.TAG_NAME, 'body')
                    content = body.text.strip()
                except:
                    content = ""
            
            # Limpiar contenido
            content = re.sub(r'\s+', ' ', content)
            content = content[:2000]  # Limitar tamaño
            
            # Extraer autor
            author = ""
            author_selectors = ['.autor', '.author', '.byline', '[class*="autor"]']
            for selector in author_selectors:
                try:
                    author_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if author_elem:
                        author = author_elem.text.strip()
                        break
                except NoSuchElementException:
                    continue
            
            # Extraer fecha
            date = ""
            date_selectors = ['.fecha', '.date', '.fecha-publicacion', '[class*="fecha"]']
            for selector in date_selectors:
                try:
                    date_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if date_elem:
                        date = date_elem.text.strip()
                        break
                except NoSuchElementException:
                    continue
            
            # Extraer imágenes
            images = []
            try:
                img_elements = self.driver.find_elements(By.TAG_NAME, 'img')
                for img in img_elements:
                    img_src = img.get_attribute('src')
                    if img_src:
                        images.append(img_src)
            except:
                pass
            
            # Crear resumen
            summary = content[:200] + "..." if len(content) > 200 else content
            
            # Cerrar pestaña y volver a la principal
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            
            return {
                'title': title,
                'content': content,
                'summary': summary,
                'author': author,
                'date': date,
                'url': url,
                'newspaper': 'El Peruano',
                'category': 'Economía',
                'images_found': len(images),
                'images_downloaded': 0,
                'images_data': images,
                'scraped_at': datetime.now().isoformat(),
                'article_id': f"elperuano_{hash(url)}"
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo artículo {url}: {e}")
            # Asegurar que volvemos a la pestaña principal
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
            return None
    
    def close(self):
        """Cerrar WebDriver"""
        if self.driver:
            self.driver.quit()

def scrape_elperuano_economia_selenium(max_articles=50):
    """Función principal para scrapear El Peruano - Economía con Selenium"""
    scraper = ElPeruanoSeleniumScraper()
    try:
        articles = scraper.scrape_economia_with_pagination(max_articles)
        return articles
    finally:
        scraper.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    articles = scrape_elperuano_economia_selenium(10)
    print(f"Artículos extraídos: {len(articles)}")
    for article in articles:
        print(f"- {article['title']}")

