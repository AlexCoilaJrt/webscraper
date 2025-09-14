#!/usr/bin/env python3
"""
Scraper mejorado que funciona sin Selenium
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import json
import logging
from datetime import datetime
import time

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ImprovedScraper:
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
    
    def scrape_articles(self, url, max_articles=20):
        """Extraer artículos de una URL"""
        try:
            logging.info(f"🔍 Scraping: {url}")
            
            # Obtener la página
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            base_domain = urlparse(url).netloc
            
            # Buscar enlaces de artículos
            article_links = self._find_article_links(soup, url, base_domain)
            
            logging.info(f"📄 Encontrados {len(article_links)} enlaces de artículos")
            
            # Procesar artículos
            articles = []
            for i, link in enumerate(article_links[:max_articles]):
                try:
                    article = self._scrape_article(link)
                    if article:
                        articles.append(article)
                        logging.info(f"✅ Artículo {i+1}/{max_articles}: {article['title'][:50]}...")
                    
                    # Pausa entre requests
                    time.sleep(0.5)
                    
                except Exception as e:
                    logging.warning(f"⚠️ Error procesando artículo {link}: {e}")
                    continue
            
            logging.info(f"🎉 Scraping completado: {len(articles)} artículos extraídos")
            return articles
            
        except Exception as e:
            logging.error(f"❌ Error en scraping: {e}")
            return []
    
    def _find_article_links(self, soup, base_url, base_domain):
        """Encontrar enlaces de artículos"""
        links = set()
        
        # Selectores específicos para artículos
        selectors = [
            'article a[href]',
            '.article a[href]',
            '.news-item a[href]',
            '.post a[href]',
            '.story a[href]',
            '.entry a[href]',
            'h1 a[href]',
            'h2 a[href]',
            'h3 a[href]',
            '.title a[href]',
            '.headline a[href]',
            'a[href*="/noticia/"]',
            'a[href*="/articulo/"]',
            'a[href*="/post/"]',
            'a[href*="/news/"]',
            'a[href*="/story/"]',
            'a[href*="/article/"]',
            'a[href*="/blog/"]',
            'a[href*="/2024/"]',
            'a[href*="/2025/"]',
            'a[href*="/2023/"]',
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if self._is_valid_article_url(full_url, base_domain):
                        links.add(full_url)
        
        # Si no encontramos suficientes, usar método más amplio
        if len(links) < 10:
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if self._is_valid_article_url(full_url, base_domain):
                        links.add(full_url)
        
        return list(links)
    
    def _is_valid_article_url(self, url, base_domain):
        """Validar si una URL es un artículo válido"""
        try:
            parsed = urlparse(url)
            
            # Debe ser del mismo dominio
            if parsed.netloc != base_domain:
                return False
            
            # Excluir patrones no deseados
            exclude_patterns = [
                '/tag/', '/tags/', '/category/', '/categories/',
                '/author/', '/page/', '/search/', '/login/', '/register/',
                '/contact/', '/about/', '/privacy/', '/terms/',
                '/rss/', '/feed/', '/sitemap/', '/admin/',
                '.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.gif',
                '#', 'javascript:', 'mailto:', 'tel:',
                '/wp-admin/', '/wp-content/', '/wp-includes/',
                '/static/', '/assets/', '/css/', '/js/',
            ]
            
            for pattern in exclude_patterns:
                if pattern in url.lower():
                    return False
            
            # Debe tener al menos 20 caracteres
            if len(url) < 20:
                return False
            
            # Patrones que indican artículo
            article_patterns = [
                r'/\d{4}/\d{2}/\d{2}/',  # Fecha
                r'/\d{4}/\d{2}/',        # Año/mes
                r'/noticia/', r'/articulo/', r'/post/', r'/news/',
                r'/story/', r'/article/', r'/blog/', r'/entry/',
                r'-\d+$',                # Termina con número
                r'[a-z]+-[a-z]+-[a-z]+', # Slug con guiones
            ]
            
            for pattern in article_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    return True
            
            # Si tiene al menos 3 segmentos en el path
            path_segments = [s for s in parsed.path.split('/') if s]
            if len(path_segments) >= 3:
                return True
            
            return False
            
        except Exception:
            return False
    
    def _scrape_article(self, url):
        """Extraer contenido de un artículo individual"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extraer título
            title = self._extract_title(soup)
            if not title or len(title) < 10:
                return None
            
            # Extraer contenido
            content = self._extract_content(soup)
            
            # Extraer autor
            author = self._extract_author(soup)
            
            # Extraer fecha
            published_date = self._extract_date(soup)
            
            # Extraer imágenes
            images = self._extract_images(soup, url)
            
            return {
                'title': title,
                'content': content,
                'url': url,
                'summary': content[:200] + '...' if len(content) > 200 else content,
                'author': author,
                'published_date': published_date,
                'scraped_at': datetime.now().isoformat(),
                'images_found': len(images),
                'images_downloaded': 0,
                'images_data': images
            }
            
        except Exception as e:
            logging.warning(f"⚠️ Error extrayendo artículo {url}: {e}")
            return None
    
    def _extract_title(self, soup):
        """Extraer título del artículo"""
        selectors = [
            'h1.entry-title',
            'h1.post-title',
            'h1.article-title',
            'h1.news-title',
            'h1.story-title',
            'h1',
            '.entry-title',
            '.post-title',
            '.article-title',
            '.news-title',
            '.story-title',
            '.title',
            '.headline',
            'title'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text().strip()
                if title and len(title) > 10:
                    return title
        
        return ""
    
    def _extract_content(self, soup):
        """Extraer contenido del artículo"""
        selectors = [
            '.entry-content',
            '.post-content',
            '.article-content',
            '.news-content',
            '.story-content',
            '.content',
            'article',
            '.post-body',
            '.article-body',
            '.news-body',
            '.story-body'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                # Remover scripts y estilos
                for script in element(["script", "style"]):
                    script.decompose()
                
                content = element.get_text()
                content = re.sub(r'\s+', ' ', content).strip()
                
                if content and len(content) > 100:
                    return content
        
        return ""
    
    def _extract_author(self, soup):
        """Extraer autor del artículo"""
        selectors = [
            '.author',
            '.byline',
            '.post-author',
            '.article-author',
            '.news-author',
            '.story-author',
            '[rel="author"]',
            '.author-name',
            '.by-author'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                author = element.get_text().strip()
                if author:
                    return author
        
        return ""
    
    def _extract_date(self, soup):
        """Extraer fecha del artículo"""
        selectors = [
            '.date',
            '.published',
            '.post-date',
            '.article-date',
            '.news-date',
            '.story-date',
            'time[datetime]',
            '.timestamp',
            '.publish-date'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                # Buscar atributo datetime
                datetime_attr = element.get('datetime')
                if datetime_attr:
                    return datetime_attr
                
                # O usar el texto
                date_text = element.get_text().strip()
                if date_text:
                    return date_text
        
        return datetime.now().isoformat()
    
    def _extract_images(self, soup, base_url):
        """Extraer imágenes del artículo"""
        images = []
        
        selectors = [
            'img[src]',
            'img[data-src]',
            'img[data-lazy]',
            '.article-image img',
            '.post-image img',
            '.news-image img',
            '.story-image img'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for img in elements:
                src = img.get('src') or img.get('data-src') or img.get('data-lazy')
                if src:
                    full_url = urljoin(base_url, src)
                    
                    # Validar que sea una imagen
                    if any(ext in full_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                        images.append({
                            'url': full_url,
                            'alt': img.get('alt', ''),
                            'title': img.get('title', '')
                        })
        
        return images[:5]  # Máximo 5 imágenes por artículo
    
    def close(self):
        """Cerrar sesión"""
        self.session.close()

def test_scraper():
    """Probar el scraper mejorado"""
    scraper = ImprovedScraper()
    
    # URLs de prueba
    test_urls = [
        "https://elcomercio.pe/",
        "https://elpopular.pe/",
        "https://peru21.pe/",
        "https://diariosinfronteras.com.pe/"
    ]
    
    for url in test_urls:
        print(f"\n🔍 Probando: {url}")
        articles = scraper.scrape_articles(url, max_articles=5)
        print(f"✅ Extraídos: {len(articles)} artículos")
        
        for i, article in enumerate(articles, 1):
            print(f"  {i}. {article['title'][:60]}...")
    
    scraper.close()

if __name__ == "__main__":
    test_scraper()

