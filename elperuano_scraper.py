#!/usr/bin/env python3
"""
Scraper específico para El Peruano
Optimizado para la estructura del diario oficial
"""

import requests
from bs4 import BeautifulSoup
import logging
import json
from datetime import datetime
from urllib.parse import urljoin, urlparse
import time
import re
from pagination_crawler import PaginationCrawler

logger = logging.getLogger(__name__)

class ElPeruanoScraper:
    """Scraper específico para El Peruano"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def scrape_economia(self, max_articles=10, use_pagination=True):
        """Scraper específico para la sección de economía de El Peruano con paginación"""
        url = "https://elperuano.pe/economia"
        
        try:
            logger.info(f"🔍 Scrapeando El Peruano - Economía: {url}")
            
            if use_pagination:
                # Usar crawler con paginación
                pagination_crawler = PaginationCrawler(use_selenium=True)
                try:
                    articles = pagination_crawler.crawl_all_pages(
                        url=url,
                        max_articles=max_articles,
                        extract_articles_func=self._extract_articles_from_page
                    )
                    logger.info(f"🎉 Total artículos extraídos con paginación: {len(articles)}")
                    return articles
                finally:
                    pagination_crawler.close()
            else:
                # Método original sin paginación
                return self._extract_articles_from_page(url, max_articles)
            
        except Exception as e:
            logger.error(f"❌ Error scrapeando El Peruano: {e}")
            return []
    
    def _extract_articles_from_page(self, url, max_articles=10):
        """Extraer artículos de una página específica"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # Buscar artículos en diferentes selectores específicos de El Peruano
            article_selectors = [
                # Selectores específicos para El Peruano
                'article',
                '.noticia',
                '.articulo',
                '.news-item',
                '.content-item',
                'div[class*="noticia"]',
                'div[class*="articulo"]',
                'div[class*="news"]',
                'div[class*="content"]',
                # Selectores más genéricos
                'h2 a',
                'h3 a',
                'h4 a',
                '.title a',
                '.headline a',
                'a[href*="/noticia"]',
                'a[href*="/articulo"]',
                'a[href*="/economia"]'
            ]
            
            found_links = set()
            
            for selector in article_selectors:
                elements = soup.select(selector)
                logger.info(f"🔍 Selector '{selector}': {len(elements)} elementos encontrados")
                
                for element in elements:
                    try:
                        # Si es un enlace directo
                        if element.name == 'a':
                            link = element.get('href')
                            title = element.get_text(strip=True)
                        # Si es un contenedor con enlace
                        else:
                            link_elem = element.find('a')
                            if link_elem:
                                link = link_elem.get('href')
                                title = link_elem.get_text(strip=True)
                            else:
                                continue
                        
                        if not link or not title or len(title) < 10:
                            continue
                            
                        # Convertir a URL absoluta
                        if link.startswith('/'):
                            link = urljoin(url, link)
                        elif not link.startswith('http'):
                            link = urljoin(url, link)
                        
                        # Filtrar enlaces no relevantes
                        if any(skip in link.lower() for skip in ['javascript:', 'mailto:', '#', 'facebook', 'twitter', 'instagram']):
                            continue
                        
                        # Evitar duplicados
                        if link in found_links:
                            continue
                        found_links.add(link)
                        
                        # Extraer contenido del artículo
                        article_data = self._extract_article_content(link, title)
                        if article_data:
                            articles.append(article_data)
                            logger.info(f"✅ Artículo extraído: {title[:50]}...")
                            
                        if len(articles) >= max_articles:
                            break
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Error procesando elemento: {e}")
                        continue
                
                if len(articles) >= max_articles:
                    break
            
            logger.info(f"📄 Artículos extraídos de página: {len(articles)}")
            return articles
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo artículos de página: {e}")
            return []
    
    def _extract_article_content(self, url, title):
        """Extraer contenido de un artículo específico"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extraer contenido del artículo
            content_selectors = [
                '.articulo-contenido',
                '.noticia-contenido',
                '.article-content',
                '.content',
                '.texto',
                'article',
                '.main-content',
                'div[class*="contenido"]',
                'div[class*="texto"]'
            ]
            
            content = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.get_text(strip=True)
                    break
            
            # Si no se encuentra contenido específico, usar todo el body
            if not content:
                body = soup.find('body')
                if body:
                    # Remover scripts, styles, etc.
                    for script in body(["script", "style", "nav", "header", "footer"]):
                        script.decompose()
                    content = body.get_text(strip=True)
            
            # Limpiar contenido
            content = re.sub(r'\s+', ' ', content)
            content = content[:2000]  # Limitar tamaño
            
            # Extraer autor
            author = ""
            author_selectors = ['.autor', '.author', '.byline', '[class*="autor"]']
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    author = author_elem.get_text(strip=True)
                    break
            
            # Extraer fecha
            date = ""
            date_selectors = ['.fecha', '.date', '.fecha-publicacion', '[class*="fecha"]']
            for selector in date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem:
                    date = date_elem.get_text(strip=True)
                    break
            
            # Extraer imágenes
            images = []
            img_elements = soup.find_all('img')
            for img in img_elements:
                img_src = img.get('src')
                if img_src:
                    if img_src.startswith('/'):
                        img_src = urljoin(url, img_src)
                    images.append(img_src)
            
            # Crear resumen
            summary = content[:200] + "..." if len(content) > 200 else content
            
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
            return None
    
    def close(self):
        """Cerrar sesión"""
        self.session.close()

def scrape_elperuano_economia(max_articles=10, use_pagination=True):
    """Función principal para scrapear El Peruano - Economía con paginación"""
    scraper = ElPeruanoScraper()
    try:
        articles = scraper.scrape_economia(max_articles, use_pagination)
        return articles
    finally:
        scraper.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    articles = scrape_elperuano_economia(5)
    print(f"Artículos extraídos: {len(articles)}")
    for article in articles:
        print(f"- {article['title']}")
