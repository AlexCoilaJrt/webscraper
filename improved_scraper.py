#!/usr/bin/env python3
"""
Scraper mejorado que funciona sin Selenium
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
import re
import json
import logging
import hashlib
from datetime import datetime
import time
from typing import List, Dict, Optional

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ImprovedScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def _normalize_url(self, url: str) -> str:
        """Normalizar URL para evitar duplicados (quitar trailing slash, parámetros de tracking, etc.)"""
        if not url:
            return url
        
        try:
            parsed = urlparse(url)
            
            # Normalizar path: quitar trailing slash excepto si es la raíz
            path = parsed.path.rstrip('/')
            if not path:
                path = '/'
            
            # Quitar parámetros de tracking comunes
            from urllib.parse import parse_qs, urlencode
            query_params = parse_qs(parsed.query, keep_blank_values=True)
            # Mantener solo parámetros importantes, excluir tracking
            tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
                             'fbclid', 'gclid', 'ref', 'source', 'campaign', 'medium']
            filtered_params = {k: v for k, v in query_params.items() if k.lower() not in tracking_params}
            
            # Reconstruir query string
            query = urlencode(filtered_params, doseq=True) if filtered_params else ''
            
            # Reconstruir URL normalizada
            normalized = urlunparse((
                parsed.scheme,
                parsed.netloc.lower(),  # Normalizar dominio a minúsculas
                path,
                parsed.params,
                query,
                ''  # Quitar fragment
            ))
            
            return normalized
        except Exception as e:
            logging.warning(f"⚠️ Error normalizando URL {url}: {e}")
            return url
    
    def _generate_article_id(self, url: str) -> str:
        """Generar un ID único para el artículo basado en la URL normalizada"""
        normalized_url = self._normalize_url(url)
        url_hash = hashlib.md5(normalized_url.encode()).hexdigest()[:12]
        return f"article_{url_hash}"
    
    def scrape_articles(self, url, max_articles=0):
        """Extraer artículos de una URL
        
        Args:
            url: URL a scrapear
            max_articles: Máximo de artículos a extraer. Si es 0 o None, extrae todos los disponibles.
        """
        try:
            logging.info(f"🔍 Scraping: {url}")
            
            parsed_url = urlparse(url)
            base_domain = parsed_url.netloc.lower()

            # Manejo especial para El Peruano (contenido dinámico vía API)
            if 'elperuano.pe' in base_domain:
                return self._scrape_elperuano_section(url, max_articles if max_articles > 0 else 1000)

            # Obtener la página
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar enlaces de artículos
            article_links = self._find_article_links(soup, url, base_domain)
            
            # Si max_articles es 0 o None, intentar encontrar todos los disponibles
            # Intentar renderizado dinámico para encontrar más enlaces
            target_count = max_articles if max_articles > 0 else 1000  # Límite alto para "todos"
            
            if len(article_links) < target_count:
                logging.info(f"⚙️ Encontrados {len(article_links)} enlaces, intentando renderizado dinámico para encontrar más...")
                rendered_html = self._render_page_with_playwright(url)
                if rendered_html:
                    soup = BeautifulSoup(rendered_html, 'html.parser')
                    new_links = self._find_article_links(soup, url, base_domain)
                    # Combinar enlaces únicos
                    article_links = list(set(article_links + new_links))
                    logging.info(f"📄 Después del renderizado: {len(article_links)} enlaces únicos encontrados")
            
            # Intentar paginación o scroll infinito si hay pocos enlaces
            if len(article_links) < 20 and 'peru21.pe' in base_domain:
                logging.info("🔄 Intentando encontrar más artículos mediante scroll...")
                more_links = self._find_more_articles_with_scroll(url, base_domain)
                if more_links:
                    article_links = list(set(article_links + more_links))
                    logging.info(f"📄 Después del scroll: {len(article_links)} enlaces totales")
            
            # Normalizar URLs para eliminar duplicados (mismo artículo con diferentes variaciones de URL)
            normalized_links = {}
            for link in article_links:
                normalized = self._normalize_url(link)
                # Mantener la primera URL encontrada para cada URL normalizada
                if normalized not in normalized_links:
                    normalized_links[normalized] = link
            
            article_links = list(normalized_links.values())
            logging.info(f"📄 Total de enlaces únicos (después de normalización): {len(article_links)}")
            
            # Determinar cuántos artículos procesar
            if max_articles > 0:
                articles_to_process = article_links[:max_articles]
                logging.info(f"📊 Procesando {len(articles_to_process)} artículos (límite: {max_articles})")
            else:
                articles_to_process = article_links
                logging.info(f"📊 Procesando TODOS los {len(articles_to_process)} artículos disponibles")
            
            # Procesar artículos
            articles = []
            total = len(articles_to_process)
            for i, link in enumerate(articles_to_process, 1):
                try:
                    article = self._scrape_article(link)
                    if article:
                        articles.append(article)
                        logging.info(f"✅ Artículo {i}/{total}: {article['title'][:50]}...")
                    
                    # Pausa entre requests
                    time.sleep(0.5)
                    
                except Exception as e:
                    logging.warning(f"⚠️ Error procesando artículo {link}: {e}")
                    continue
            
            logging.info(f"🎉 Scraping completado: {len(articles)} artículos extraídos de {len(article_links)} encontrados")
            return articles
            
        except Exception as e:
            logging.error(f"❌ Error en scraping: {e}")
            return []
    
    def _find_article_links(self, soup, base_url, base_domain):
        """Encontrar enlaces de artículos (filtrado para evitar categorías)"""
        links = set()
        
        # Lógica específica para NYTimes: páginas de sección muestran tarjetas con enlaces con fecha en la ruta
        if 'nytimes.com' in base_domain:
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href') or ''
                if not href:
                    continue
                full_url = urljoin(base_url, href)
                parsed = urlparse(full_url)
                if 'nytimes.com' not in parsed.netloc.lower():
                    continue
                path_lower = parsed.path.lower()
                # Aceptar artículos que tengan fecha en la URL
                if re.search(r'/20\\d{2}/\\d{2}/\\d{2}/', path_lower):
                    # Excluir secciones que no son artículos
                    if any(x in path_lower for x in ['/games/', '/crossword/', '/video/', '/es/']):
                        continue
                    links.add(full_url)
            # Si ya encontramos suficientes con la regla de fecha, seguimos
        
        # Lógica específica para Andina
        if 'andina.pe' in base_domain:
            # Andina usa formato: /agencia/noticia-titulo-articulo-XXXXX.aspx
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    parsed = urlparse(full_url)
                    
                    # Verificar que sea de andina.pe
                    if 'andina.pe' not in parsed.netloc.lower():
                        continue
                    
                    path = parsed.path.lower()
                    
                    # Formato de artículos de Andina: /agencia/noticia-...-XXXXX.aspx
                    if '/agencia/noticia-' in path and path.endswith('.aspx'):
                        # Verificar que tenga un ID numérico al final
                        if re.search(r'-\d+\.aspx$', path):
                            # Obtener título del enlace
                            title = link.get_text().strip()
                            # Si no hay título en el enlace, buscar en elementos relacionados
                            if not title or len(title) < 10:
                                # Buscar en el elemento padre o en elementos relacionados
                                parent = link.parent
                                if parent:
                                    # Buscar h2, h3, o span con clase title/headline
                                    title_elem = parent.find(['h2', 'h3', 'span'], class_=lambda x: x and any(kw in str(x).lower() for kw in ['title', 'headline', 'titulo']))
                                    if title_elem:
                                        title = title_elem.get_text().strip()
                                
                                # Si aún no hay título, usar el texto del enlace o del contenedor
                                if not title or len(title) < 10:
                                    title = parent.get_text().strip() if parent else ''
                            
                            # Solo agregar si tiene un título válido
                            if title and len(title) > 10:
                                links.add(full_url)
                                continue
            
            # También buscar en selectores específicos de Andina
            andina_selectors = [
                'a[href*="/agencia/noticia-"]',
                'article a[href*="noticia-"]',
                '.noticia a[href*="noticia-"]',
                '.news-item a[href*="noticia-"]',
                'h2 a[href*="noticia-"]',
                'h3 a[href*="noticia-"]',
            ]
            
            for selector in andina_selectors:
                elements = soup.select(selector)
                for element in elements:
                    href = element.get('href')
                    if href:
                        full_url = urljoin(base_url, href)
                        if 'andina.pe' in full_url and '/agencia/noticia-' in full_url.lower() and full_url.endswith('.aspx'):
                            if re.search(r'-\d+\.aspx$', full_url.lower()):
                                links.add(full_url)
        
        # Lógica específica para peru21.pe
        if 'peru21.pe' in base_domain:
            # Buscar todos los enlaces que contengan rutas de categorías (ej: /gastronomia/, /politica/, etc.)
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href')
                if href:
                    # Normalizar URL
                    full_url = urljoin(base_url, href)
                    parsed = urlparse(full_url)
                    
                    # Para peru21.pe, aceptar URLs que:
                    # - Tengan al menos 2 segmentos en el path (ej: /gastronomia/titulo-articulo/)
                    # - No sean la página de categoría misma
                    # - No contengan patrones excluidos
                    path_segments = [s for s in parsed.path.split('/') if s]
                    
                    # Debe tener al menos 2 segmentos (categoría + artículo)
                    if len(path_segments) < 2:
                        continue
                    
                    # Excluir si es solo la categoría (ej: /gastronomia/)
                    if len(path_segments) == 1:
                        continue
                    
                    # EXCLUIR páginas de autor - URLs que solo tienen nombre de persona
                    # Ej: /iris-mariscal-herrera, /jose-jeri, etc.
                    # Estas URLs típicamente tienen solo 1 segmento después de la categoría o son nombres propios
                    first_segment = path_segments[0].lower()
                    last_segment = path_segments[-1].lower()
                    
                    # Lista de categorías válidas en peru21.pe
                    valid_categories = [
                        'politica', 'gastronomia', 'deportes', 'espectaculos', 
                        'economia', 'mundo', 'tecnologia', 'cultura', 'ciencia',
                        'lima', 'peru', 'investigacion', 'videos', 'ultimas-noticias',
                        'epaper', 'opinion', 'tendencias', 'estilo', 'salud'
                    ]
                    
                    # Si el primer segmento NO es una categoría válida, probablemente es una página de autor
                    if first_segment not in valid_categories:
                        continue
                    
                    # Excluir URLs que parecen ser páginas de autor (nombres propios sin contexto de artículo)
                    # Un artículo real tiene un título descriptivo con múltiples palabras
                    # Una página de autor típicamente tiene solo el nombre (2-3 palabras)
                    if len(path_segments) == 2:
                        # Si solo hay 2 segmentos, verificar que el segundo sea un título de artículo
                        # Los títulos de artículos suelen tener múltiples palabras separadas por guiones
                        article_slug = last_segment
                        word_count = len(article_slug.split('-'))
                        # Si tiene menos de 4 palabras, probablemente es una página de autor
                        # Los nombres de personas típicamente tienen 2-3 palabras
                        # Los títulos de artículos tienen 4+ palabras
                        if word_count < 4:
                            continue
                    
                    # Validar que no sea una página de categoría o sección
                    exclude_keywords = [
                        'tag', 'author', 'autor', 'page', 'search', 'login', 'register', 
                        'contact', 'about', 'privacy', 'terms', 'rss', 'feed', 
                        'sitemap', 'admin', 'static', 'assets', 'css', 'js',
                        'noticias-de-', 'noticia-de-', 'articulos-de-', 'articulo-de-'
                    ]
                    if any(kw in href.lower() for kw in exclude_keywords):
                        continue
                    
                    # Excluir URLs que contengan solo nombres propios comunes (páginas de autor)
                    # Estos patrones indican páginas de autor, no artículos
                    author_patterns = [
                        r'^/[a-z]+/[a-z]+-[a-z]+$',  # /categoria/nombre-apellido
                        r'noticias-de-[a-z]+-[a-z]+$',  # noticias-de-nombre-apellido
                    ]
                    is_author_page = False
                    for pattern in author_patterns:
                        if re.match(pattern, parsed.path.lower()):
                            is_author_page = True
                            break
                    
                    if is_author_page:
                        continue
                    
                    # Aceptar si tiene un slug con guiones y múltiples palabras (formato típico de artículos)
                    if len(path_segments) >= 2 and '-' in last_segment:
                        # Verificar que el slug del artículo tenga al menos 4 palabras
                        # Los nombres de personas tienen 2-3 palabras, los artículos tienen 4+
                        slug_words = last_segment.split('-')
                        if len(slug_words) >= 4:  # Artículos reales tienen títulos más largos
                            links.add(full_url)
        
        # Lógica específica para AmericaTV
        if 'americatv.com.pe' in base_domain:
            # Buscar todos los enlaces
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href')
                if href:
                    # Normalizar URL
                    full_url = urljoin(base_url, href)
                    parsed = urlparse(full_url)
                    
                    # Verificar que sea del mismo dominio
                    if 'americatv.com.pe' not in parsed.netloc.lower():
                        continue
                    
                    path = parsed.path.lower()
                    path_segments = [s for s in parsed.path.split('/') if s]
                    
                    # Excluir URLs obviamente no artículos
                    if '/tag/' in path or '/tags/' in path:
                        continue
                    if '/util-e-interesante' in path:
                        continue
                    if path == '/noticias/' or path == '/noticias':
                        continue
                    if path == '/' or not path_segments:
                        continue
                    
                    # Formato 1: /noticias/categoria/titulo-nXXXXX (página principal)
                    if '/noticias/' in path and len(path_segments) >= 3:
                        last_segment = path_segments[-1].lower()
                        # Verificar que tenga un ID de artículo (n seguido de números)
                        if re.search(r'-n\d+$', last_segment):
                            links.add(full_url)
                            continue
                    
                    # Formato 2: /categoria/titulo-noticia-XXXXX (páginas de categoría)
                    # Ejemplo: /al-fondo-hay-sitio/july-revelara-jimmy-y-yesenia-secreto-alessia-avance-noticia-161404
                    if len(path_segments) >= 2:
                        last_segment = path_segments[-1].lower()
                        # Verificar que termine con "-noticia-" seguido de números
                        if re.search(r'-noticia-\d+$', last_segment):
                            links.add(full_url)
                            continue
                        
                        # También aceptar si tiene formato similar con ID numérico al final
                        # Ejemplo: /categoria/titulo-articulo-XXXXX
                        if re.search(r'-\d+$', last_segment) and len(last_segment.split('-')) >= 3:
                            # Verificar que no sea solo una categoría (muy pocas palabras)
                            slug_words = last_segment.split('-')
                            if len(slug_words) >= 4:  # Al menos 4 palabras en el slug
                                links.add(full_url)
        
        # Selectores específicos para artículos (evitando categorías)
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
            
            # Reglas específicas para NYTimes: aceptar rutas con fecha
            if 'nytimes.com' in base_domain:
                if 'nytimes.com' not in parsed.netloc.lower():
                    return False
                path_lower = parsed.path.lower()
                if re.search(r'/20\\d{2}/\\d{2}/\\d{2}/', path_lower):
                    if any(x in path_lower for x in ['/games/', '/crossword/', '/video/', '/es/']):
                        return False
                    return True
                # Dejar que continúe con validaciones generales si no tiene fecha
            
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
            
            # Reglas adicionales para dominios específicos
            if 'ojo.pe' in base_domain:
                if '/noticia' not in parsed.path:
                    return False
            
            # Reglas específicas para peru21.pe
            if 'peru21.pe' in base_domain:
                path_segments = [s for s in parsed.path.split('/') if s]
                
                # Debe tener al menos 2 segmentos (categoría + artículo)
                if len(path_segments) < 2:
                    return False
                
                # Lista de categorías válidas
                valid_categories = [
                    'politica', 'gastronomia', 'deportes', 'espectaculos', 
                    'economia', 'mundo', 'tecnologia', 'cultura', 'ciencia',
                    'lima', 'peru', 'investigacion', 'videos', 'ultimas-noticias',
                    'epaper', 'opinion', 'tendencias', 'estilo', 'salud'
                ]
                
                first_segment = path_segments[0].lower()
                last_segment = path_segments[-1].lower()
                
                # El primer segmento debe ser una categoría válida
                if first_segment not in valid_categories:
                    return False
                
                # Excluir páginas de autor - URLs con solo nombre-apellido
                # Los artículos reales tienen títulos con múltiples palabras (mínimo 4)
                # Los nombres de personas típicamente tienen 2-3 palabras
                if len(path_segments) == 2:
                    slug_words = last_segment.split('-')
                    if len(slug_words) < 4:
                        return False  # Probablemente es una página de autor
                
                # Excluir patrones de autor
                if 'noticias-de-' in url.lower() or 'noticia-de-' in url.lower():
                    return False
                
                # Excluir URLs que solo tienen nombre-apellido (páginas de autor)
                author_pattern = r'^/[a-z]+/[a-z]+-[a-z]+$'
                if re.match(author_pattern, parsed.path.lower()):
                    return False
            
            # Reglas específicas para AmericaTV
            if 'americatv.com.pe' in base_domain:
                path = parsed.path.lower()
                path_segments = [s for s in parsed.path.split('/') if s]
                
                # Excluir URLs obviamente no artículos
                if '/tag/' in path or '/tags/' in path:
                    return False
                if '/util-e-interesante' in path:
                    return False
                if path == '/noticias/' or path == '/noticias':
                    return False
                if path == '/' or not path_segments:
                    return False
                
                # Formato 1: /noticias/categoria/titulo-nXXXXX (página principal)
                if '/noticias/' in path and len(path_segments) >= 3:
                    last_segment = path_segments[-1].lower()
                    # Verificar que tenga un ID de artículo (n seguido de números)
                    if re.search(r'-n\d+$', last_segment):
                        return True
                
                # Formato 2: /categoria/titulo-noticia-XXXXX (páginas de categoría)
                if len(path_segments) >= 2:
                    last_segment = path_segments[-1].lower()
                    # Verificar que termine con "-noticia-" seguido de números
                    if re.search(r'-noticia-\d+$', last_segment):
                        return True
                    
                    # También aceptar si tiene formato similar con ID numérico al final
                    if re.search(r'-\d+$', last_segment) and len(last_segment.split('-')) >= 3:
                        slug_words = last_segment.split('-')
                        if len(slug_words) >= 4:  # Al menos 4 palabras en el slug
                            return True
                
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
    
    def _fetch_article_soup(self, url: str):
        """Intentar obtener el HTML del artículo probando variantes (por ejemplo AMP)."""
        # Para NYTimes, usar Playwright directamente desde el inicio
        if 'nytimes.com' in url.lower():
            logging.info(f"⚙️ Usando Playwright directamente para NYTimes: {url}")
            rendered_html = self._render_page_with_playwright(url)
            if rendered_html:
                try:
                    soup = BeautifulSoup(rendered_html, 'html.parser')
                    if soup and soup.find('body'):
                        return soup, url
                except Exception as e:
                    logging.debug(f"Error parseando HTML de Playwright para NYTimes: {e}")
        
        attempt_urls = []
        cleaned_url = (url or '').strip()
        if cleaned_url:
            attempt_urls.append(cleaned_url)
            
            if '?' in cleaned_url:
                amp_query_url = f"{cleaned_url}&output=amp"
            else:
                amp_query_url = f"{cleaned_url}?output=amp"
            attempt_urls.append(amp_query_url)
            
            if cleaned_url.endswith('/'):
                amp_path_url = cleaned_url + 'amp/'
            else:
                amp_path_url = cleaned_url + '/amp/'
            attempt_urls.append(amp_path_url)
        
        seen = set()
        for candidate in attempt_urls:
            if not candidate or candidate in seen:
                continue
            seen.add(candidate)
            try:
                response = self.session.get(candidate, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                if soup and soup.find('body'):
                    return soup, candidate
            except Exception as e:
                logging.debug(f"Intento fallido cargando {candidate}: {e}")
        
        # Fallback a Playwright para otros sitios
        rendered_html = self._render_page_with_playwright(url)
        if rendered_html:
            try:
                soup = BeautifulSoup(rendered_html, 'html.parser')
                if soup and soup.find('body'):
                    return soup, url
            except Exception:
                pass
        return None, None
    
    def _render_page_with_playwright(self, url: str) -> Optional[str]:
        """Renderizar página con Playwright para contenido dinámico."""
        global sync_playwright
        if sync_playwright is None:
            try:
                from playwright.sync_api import sync_playwright as _sync_playwright
                sync_playwright = _sync_playwright
            except Exception as e:
                logging.warning(f"⚠️ Playwright no disponible: {e}")
                return None
        if not sync_playwright:
            return None
        
        is_nytimes = 'nytimes.com' in url.lower()
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
                page = browser.new_page()
                
                # Para NYTimes, usar domcontentloaded y luego esperar
                if is_nytimes:
                    page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    # Esperar a que las imágenes se carguen
                    page.wait_for_timeout(3000)
                    # Hacer un scroll suave para activar lazy loading
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight / 3)")
                    page.wait_for_timeout(1000)
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                    page.wait_for_timeout(1000)
                    # Esperar a que las imágenes se carguen
                    try:
                        page.wait_for_load_state('networkidle', timeout=10000)
                    except:
                        pass  # Continuar aunque no esté completamente idle
                else:
                    page.goto(url, wait_until='networkidle', timeout=30000)
                
                html = page.content()
                browser.close()
                return html
        except Exception as e:
            logging.warning(f"⚠️ No se pudo renderizar {url} con Playwright: {e}")
            return None
    
    def _find_more_articles_with_scroll(self, url: str, base_domain: str) -> List[str]:
        """Intentar encontrar más artículos haciendo scroll en la página."""
        global sync_playwright
        if sync_playwright is None:
            try:
                from playwright.sync_api import sync_playwright as _sync_playwright
                sync_playwright = _sync_playwright
            except Exception:
                return []
        if not sync_playwright:
            return []
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
                page = browser.new_page()
                page.goto(url, wait_until='networkidle', timeout=30000)
                
                # Hacer scroll varias veces para cargar contenido dinámico
                links_found = set()
                previous_height = 0
                scroll_attempts = 0
                max_scrolls = 5
                
                while scroll_attempts < max_scrolls:
                    # Obtener enlaces actuales
                    current_html = page.content()
                    soup = BeautifulSoup(current_html, 'html.parser')
                    current_links = self._find_article_links(soup, url, base_domain)
                    links_found.update(current_links)
                    
                    # Hacer scroll hacia abajo
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(2000)  # Esperar a que cargue contenido
                    
                    # Verificar si hay más contenido
                    current_height = page.evaluate("document.body.scrollHeight")
                    if current_height == previous_height:
                        break  # No hay más contenido
                    
                    previous_height = current_height
                    scroll_attempts += 1
                
                browser.close()
                return list(links_found)
        except Exception as e:
            logging.warning(f"⚠️ Error haciendo scroll en {url}: {e}")
            return []
    
    def _scrape_article(self, url):
        """Extraer contenido de un artículo individual"""
        try:
            soup, final_url = self._fetch_article_soup(url)
            if soup is None:
                return None
            
            # Normalizar URL para evitar duplicados
            article_url = self._normalize_url(final_url or url)
            
            # Generar article_id único basado en la URL normalizada
            article_id = self._generate_article_id(article_url)
            
            # Extraer título
            title = self._extract_title(soup)
            # NYTimes puede requerir umbral menor si el título se obtiene desde <title> o meta
            is_nyt = 'nytimes.com' in article_url.lower()
            if not title or (len(title) < 10 and not is_nyt):
                return None
            
            # CRÍTICO: Extraer imágenes ANTES de extraer contenido
            # porque _extract_content modifica el soup (elimina elementos)
            images = self._extract_images(soup, article_url)
            
            # Extraer contenido
            content = self._extract_content(soup, article_url)
            
            # Si es NYTimes, Willax o el contenido es muy corto, intentar con Playwright (contenido dinámico)
            is_willax = 'willax.pe' in article_url.lower()
            is_americatv = 'americatv.com.pe' in article_url.lower()
            is_nytimes = 'nytimes.com' in article_url.lower()
            
            # NYTimes SIEMPRE requiere Playwright porque todo el contenido es dinámico
            # También intentar si el contenido es muy corto o si es Willax/AmericaTV
            if is_nytimes or is_willax or (len(content) < 100 and is_americatv) or (is_nyt and len(content) < 200):
                reason = 'NYTimes (requiere Playwright)' if is_nytimes else ('Willax detectado' if is_willax else 'Contenido corto detectado')
                logging.info(f"⚙️ {reason}, intentando con Playwright para {article_url}")
                try:
                    rendered_html = self._render_page_with_playwright(article_url)
                    if rendered_html:
                        soup_rendered = BeautifulSoup(rendered_html, 'html.parser')
                        
                        # Para NYTimes, re-extraer título y contenido del HTML renderizado
                        if is_nytimes:
                            title_rendered = self._extract_title(soup_rendered)
                            if title_rendered and len(title_rendered) > len(title):
                                title = title_rendered
                                logging.info(f"✅ Título de NYTimes extraído: {title[:80]}...")
                        
                        content_rendered = self._extract_content(soup_rendered, article_url)
                        if len(content_rendered) > len(content):
                            content = content_rendered
                            # Si no se encontraron imágenes antes, intentar con el soup renderizado
                            if not images:
                                images = self._extract_images(soup_rendered, article_url)
                            logging.info(f"✅ Contenido extraído con Playwright: {len(content)} caracteres")
                except Exception as e:
                    logging.warning(f"⚠️ Error usando Playwright: {e}")
            
            # Extraer autor
            author = self._extract_author(soup)
            
            # Extraer fecha de publicación (NO fecha de scraping)
            published_date = self._extract_date(soup, article_url)
            # Si no se encuentra fecha de publicación, usar fecha de scraping como último recurso
            if not published_date:
                published_date = datetime.now().isoformat()
            
            # NOTA: No intentar con Playwright para imágenes de Andina
            # La extracción simple funciona correctamente y Playwright está causando errores
            
            # Si no se encontraron imágenes y es NYTimes, intentar con Playwright
            if not images and 'nytimes.com' in article_url.lower():
                logging.info(f"⚙️ No se encontraron imágenes para NYTimes, intentando con Playwright para {article_url}")
                try:
                    rendered_html = self._render_page_with_playwright(article_url)
                    if rendered_html:
                        soup_rendered = BeautifulSoup(rendered_html, 'html.parser')
                        images = self._extract_images(soup_rendered, article_url)
                        if images:
                            logging.info(f"✅ Imágenes encontradas con Playwright: {len(images)}")
                except Exception as e:
                    logging.warning(f"⚠️ Error usando Playwright para imágenes de NYTimes: {e}")
            
            return {
                'title': title,
                'content': content,
                'url': article_url,
                'summary': content[:200] + '...' if len(content) > 200 else content,
                'author': author,
                'published_date': published_date,
                'scraped_at': datetime.now().isoformat(),
                'images_found': len(images),
                'images_downloaded': 0,
                'images_data': images,
                'article_id': article_id  # Agregar article_id único
            }
            
        except Exception as e:
            logging.warning(f"⚠️ Error extrayendo artículo {url}: {e}")
            return None
    
    def _extract_title(self, soup):
        """Extraer título del artículo"""
        # Lógica específica para NYTimes (prioridad alta)
        nytimes_title = soup.select_one('[data-testid="headline"]') or soup.select_one('h1[data-testid="headline"]')
        if nytimes_title:
            title = nytimes_title.get_text().strip()
            if title and len(title) > 10:
                return title
        
        # Buscar en JSON-LD structured data (NYTimes usa esto)
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict):
                    headline = data.get('headline')
                    if headline:
                        if isinstance(headline, str):
                            return headline.strip()
                        elif isinstance(headline, dict):
                            return headline.get('text', '').strip() or headline.get('name', '').strip()
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            headline = item.get('headline')
                            if headline:
                                if isinstance(headline, str):
                                    return headline.strip()
                                elif isinstance(headline, dict):
                                    return headline.get('text', '').strip() or headline.get('name', '').strip()
            except:
                continue
        
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
                    # Para NYTimes, limpiar el título (puede tener " - The New York Times" al final)
                    if 'nytimes.com' in str(soup.find('html', {}).get('lang', '')) or 'nytimes' in title.lower():
                        title = title.split(' - The New York Times')[0].split(' | The New York Times')[0].strip()
                    return title
        
        # Fallback: meta tags comunes
        meta_title = soup.find('meta', attrs={'property': 'og:title'}) or soup.find('meta', attrs={'name': 'og:title'}) \
            or soup.find('meta', attrs={'name': 'twitter:title'}) or soup.find('meta', attrs={'property': 'twitter:title'})
        if meta_title and meta_title.get('content'):
            mt = meta_title.get('content').strip()
            if mt:
                # Limpiar título de NYTimes
                if 'nytimes' in mt.lower():
                    mt = mt.split(' - The New York Times')[0].split(' | The New York Times')[0].strip()
                return mt
        
        return ""
    
    def _extract_content(self, soup, base_url=''):
        """Extraer contenido del artículo"""
        # Lógica específica para NYTimes (prioridad alta)
        is_nytimes = 'nytimes.com' in base_url.lower() if base_url else False
        if is_nytimes:
            # NYTimes usa selectores específicos con data-testid
            nytimes_content = soup.select_one('[data-testid="article-body"]') or soup.select_one('section[data-testid="article-body"]')
            if nytimes_content:
                # Remover elementos no deseados
                for elem in nytimes_content.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form', 'iframe', 'button']):
                    elem.decompose()
                
                # Buscar párrafos dentro del contenido
                paragraphs = nytimes_content.find_all('p')
                if paragraphs:
                    content_parts = []
                    for p in paragraphs:
                        text = p.get_text().strip()
                        # Filtrar párrafos muy cortos o que parecen ser metadata
                        if text and len(text) > 20:
                            content_parts.append(text)
                    
                    if content_parts:
                        content = ' '.join(content_parts)
                        content = re.sub(r'\s+', ' ', content).strip()
                        if len(content) > 100:
                            return content
                
                # Si no hay párrafos, usar todo el texto del contenedor
                all_text = nytimes_content.get_text()
                content = re.sub(r'\s+', ' ', all_text).strip()
                if len(content) > 100:
                    return content
            
            # Buscar en JSON-LD structured data
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_ld_scripts:
                try:
                    import json
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        article_body = data.get('articleBody')
                        if article_body:
                            return article_body.strip()
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                article_body = item.get('articleBody')
                                if article_body:
                                    return article_body.strip()
                except:
                    continue
        
        # Lógica específica para Andina
        is_andina = 'andina.pe' in base_url.lower() if base_url else False
        
        if is_andina:
            # Andina tiene múltiples estructuras posibles
            # Primero intentar con selectores específicos
            content_selectors = [
                'div.article-content',
                'div.noticia-content',
                'div.content',
                'article',
                'div[class*="col"][class*="s12"]',
                'div[class*="col"][class*="m8"]',
                'div[class*="col"][class*="l9"]',
                'div[class*="col"][class*="xl9"]',
            ]
            
            article_content = None
            for selector in content_selectors:
                try:
                    article_content = soup.select_one(selector)
                    if article_content:
                        text = article_content.get_text().strip()
                        if len(text) > 200:
                            break
                except:
                    continue
            
            # Si no se encontró con selectores, buscar en divs con clases específicas
            if not article_content:
                content_divs = soup.find_all('div', class_=lambda x: x and 'col' in str(x) and ('s12' in str(x) or 'm8' in str(x) or 'l9' in str(x) or 'xl9' in str(x)))
            
            for div in content_divs:
                    text = div.get_text().strip()
                    if text and len(text) > 200:
                        preview = text[:300].lower()
                        # Filtrar contenido que sea solo navegación
                        if not any(kw in preview for kw in ['bicentenario', 'perfiles', 'especiales', 'normas legales', 'turismo', 'vive andina', 'inicio', 'contacto', 'buscar']):
                            article_content = div
                            break
            
            if article_content:
                # Remover elementos no deseados
                for elem in article_content.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form', 'iframe']):
                            elem.decompose()
                
                # Remover enlaces de navegación pero mantener enlaces del contenido
                for link in article_content.find_all('a', href=True):
                    href = link.get('href', '').lower()
                    if any(kw in href for kw in ['bicentenario', 'perfiles', 'especiales', 'normas', 'turismo', 'vive', 'inicio', 'contacto', 'buscar', 'tag', 'category', 'author']):
                        link.decompose()
                
                # Remover elementos de compartir/redes sociales
                for elem in article_content.find_all(class_=lambda x: x and any(kw in str(x).lower() for kw in ['social', 'share', 'compartir', 'seguir', 'sidebar', 'related', 'ad', 'advertisement'])):
                        elem.decompose()
                
                # Buscar párrafos dentro del contenido
                paragraphs = article_content.find_all('p')
                if paragraphs:
                    content_parts = []
                    for p in paragraphs:
                        text = p.get_text().strip()
                        # Filtrar párrafos muy cortos o que parecen ser metadata
                        if text and len(text) > 30 and not any(keyword in text.lower() for keyword in ['compartir', 'seguir', 'síguenos', 'redes sociales', 'facebook', 'twitter', 'instagram', 'whatsapp', 'telegram', 'publicidad', 'anuncio']):
                            content_parts.append(text)
                    
                    if content_parts:
                        content = ' '.join(content_parts)
                        content = re.sub(r'\s+', ' ', content).strip()
                        if len(content) > 200:
                            return content
                
                # Si no hay párrafos, usar todo el texto pero filtrar
                text = article_content.get_text().strip()
                if text and len(text) > 200:
                    preview = text[:300].lower()
                    if not any(kw in preview for kw in ['bicentenario', 'perfiles', 'especiales', 'normas legales', 'turismo', 'vive andina', 'inicio', 'contacto', 'buscar']):
                        # Limpiar el texto
                        content = re.sub(r'\s+', ' ', text).strip()
                        # Remover líneas que parecen ser metadata o navegación
                        lines = content.split('\n')
                        filtered_lines = []
                        for line in lines:
                            line = line.strip()
                            if line and len(line) > 20:
                                line_lower = line.lower()
                                if not any(kw in line_lower for kw in ['bicentenario', 'perfiles', 'especiales', 'normas', 'turismo', 'vive', 'inicio', 'contacto', 'buscar', 'lo último', 'política', 'economía', 'regionales', 'videos más vistos', 'más vistos', 'videos relacionados', 'búsqueda de videos', 'compartir', 'seguir']):
                                    filtered_lines.append(line)
                        
                        if filtered_lines:
                            content = ' '.join(filtered_lines)
                            if len(content) > 200:
                                return content
            
            # Si no se encontró en divs específicos, buscar en article
            article = soup.find('article')
            if article:
                # Remover navegación
                for elem in article.find_all('a', href=lambda x: x and any(kw in str(x).lower() for kw in ['bicentenario', 'perfiles', 'especiales', 'normas', 'turismo', 'vive'])):
                    elem.decompose()
                
                text = article.get_text().strip()
                if text and len(text) > 200:
                    preview = text[:300].lower()
                    if not any(kw in preview for kw in ['bicentenario', 'perfiles', 'especiales', 'normas legales', 'turismo', 'vive andina']):
                        content = re.sub(r'\s+', ' ', text).strip()
                        if len(content) > 200:
                            return content
        
        # Lógica específica para Willax
        is_willax = 'willax.pe' in base_url.lower() if base_url else False
        
        if is_willax:
            # Willax usa estructura específica - buscar en múltiples lugares
            # Primero buscar en el contenedor principal de contenido
            content_selectors = [
                'div.entry-content',
                'div.post-content',
                'div.article-content',
                'div.content',
                'article',
                'div[class*="content"]',
                'div[class*="article"]',
                'div[class*="post"]',
                'div[class*="entry"]',
                'main',
                'div.main-content',
            ]
            
            article = None
            for selector in content_selectors:
                try:
                    article = soup.select_one(selector)
                    if article:
                        text = article.get_text().strip()
                        if len(text) > 200:  # Verificar que tenga contenido sustancial
                            break
                except:
                    continue
            
            # Si no encontramos con selectores, buscar manualmente
            if not article:
                # Buscar en divs con clases comunes de contenido
                article = soup.find('div', class_=lambda x: x and any(kw in str(x).lower() for kw in ['content', 'article', 'noticia', 'post', 'entry']))
            
            if article:
                # Remover elementos no deseados
                for elem in article.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form', 'iframe']):
                    elem.decompose()
                
                # Remover elementos de redes sociales/compartir
                for elem in article.find_all(class_=lambda x: x and any(kw in str(x).lower() for kw in ['social', 'share', 'compartir', 'seguir', 'sidebar', 'related', 'ad', 'advertisement'])):
                    elem.decompose()
                
                # Buscar párrafos dentro del contenido
                paragraphs = article.find_all('p')
                if paragraphs:
                    content_parts = []
                    for p in paragraphs:
                        # Remover elementos no deseados del párrafo
                        for unwanted in p.find_all(['script', 'style', 'a']):
                            # Solo remover enlaces de compartir
                            if unwanted.name == 'a':
                                href = unwanted.get('href', '').lower()
                                if any(kw in href for kw in ['compartir', 'share', 'seguir', 'follow', 'redes', 'social']):
                                    unwanted.decompose()
                            else:
                                unwanted.decompose()
                        
                        text = p.get_text().strip()
                        # Filtrar párrafos muy cortos o que parecen ser metadata
                        # Para Willax, aceptar párrafos más cortos (pueden tener contenido válido)
                        if text and len(text) > 20 and not any(keyword in text.lower() for keyword in ['compartir', 'seguir', 'síguenos', 'redes sociales', 'facebook', 'twitter', 'instagram', 'whatsapp', 'telegram', 'publicidad', 'anuncio']):
                            content_parts.append(text)
                    
                    if content_parts:
                        content = ' '.join(content_parts)
                        content = re.sub(r'\s+', ' ', content).strip()
                        # Para Willax, aceptar contenido más corto (mínimo 100 caracteres)
                        if len(content) > 100:
                            return content
                
                # Si no hay párrafos, buscar en divs con texto largo
                divs = article.find_all('div', recursive=True)
                content_parts = []
                for div in divs:
                    # Remover elementos no deseados del div (pero mantener enlaces dentro del contenido)
                    for unwanted in div.find_all(['script', 'style', 'button', 'form', 'iframe']):
                        unwanted.decompose()
                    
                    # Remover solo enlaces de navegación/compartir, no todos los enlaces
                    for link in div.find_all('a', href=True):
                        href = link.get('href', '').lower()
                        if any(kw in href for kw in ['compartir', 'share', 'seguir', 'follow', 'redes', 'social', 'facebook', 'twitter', 'instagram', 'whatsapp', 'telegram', 'contacto', 'contact', 'inicio', 'home']):
                            link.decompose()
                    
                    text = div.get_text().strip()
                    # Filtrar divs con texto largo que no sean metadata
                    if text and len(text) > 100:
                        text_lower = text.lower()
                        # Excluir si es solo metadata o navegación
                        if not any(keyword in text_lower for keyword in ['compartir', 'seguir', 'síguenos', 'redes sociales', 'facebook', 'twitter', 'instagram', 'whatsapp', 'telegram', 'comentarios', 'comentar', 'publicidad', 'anuncio']):
                            # Verificar que tenga contenido sustancial
                            links = div.find_all('a')
                            if len(links) < len(text) / 20:  # No más de un enlace cada 20 caracteres
                                content_parts.append(text)
                
                if content_parts:
                    # Tomar el div con más texto (probablemente el contenido principal)
                    main_content = max(content_parts, key=len)
                    content = re.sub(r'\s+', ' ', main_content).strip()
                    if len(content) > 150:
                        return content
                
                # Si no hay párrafos ni divs con contenido, usar todo el texto del artículo
                # pero filtrar metadata
                all_text = article.get_text()
                content = re.sub(r'\s+', ' ', all_text).strip()
                # Filtrar contenido que sea solo metadata
                if len(content) > 150:
                    preview = content[:400].lower() if len(content) > 400 else content.lower()
                    if not any(keyword in preview for keyword in ['compartir', 'seguir', 'síguenos', 'redes sociales', 'comentarios', 'comentar']):
                            return content
        
        # Lógica específica para AmericaTV
        # Verificar si es AmericaTV por el dominio
        is_americatv = 'americatv.com.pe' in base_url.lower() if base_url else False
        
        if is_americatv:
            # Buscar contenido en article
            article = soup.find('article')
            if article:
                # Remover elementos no deseados
                for elem in article.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                    elem.decompose()
                
                # Remover elementos con clases de redes sociales/compartir
                for elem in article.find_all(class_=lambda x: x and any(kw in str(x).lower() for kw in ['social', 'share', 'compartir', 'seguir'])):
                    elem.decompose()
                
                # Buscar párrafos dentro del artículo
                paragraphs = article.find_all('p')
                if paragraphs:
                    content_parts = []
                    for p in paragraphs:
                        text = p.get_text().strip()
                        # Filtrar párrafos muy cortos o que parecen ser metadata
                        if text and len(text) > 20 and not any(keyword in text.lower() for keyword in ['compartir', 'seguir', 'síguenos', 'redes sociales', 'facebook', 'twitter', 'instagram']):
                            content_parts.append(text)
                    
                    if content_parts:
                        content = ' '.join(content_parts)
                        content = re.sub(r'\s+', ' ', content).strip()
                        if len(content) > 100:
                            return content
                
                # Si no hay párrafos, buscar en divs con texto largo
                divs = article.find_all('div', recursive=True)
                content_parts = []
                for div in divs:
                    text = div.get_text().strip()
                    # Filtrar divs con texto largo que no sean metadata (umbral más bajo para AmericaTV)
                    if text and len(text) > 50:
                        # Verificar que no sea solo metadata o redes sociales
                        text_lower = text.lower()
                        if not any(keyword in text_lower for keyword in ['compartir', 'seguir', 'síguenos', 'redes sociales', 'facebook', 'twitter', 'instagram', 'whatsapp']):
                            # Verificar que tenga contenido sustancial (no solo enlaces)
                            links = div.find_all('a')
                            if len(links) < len(text) / 30:  # No más de un enlace cada 30 caracteres
                                content_parts.append(text)
                
                if content_parts:
                    # Tomar el div con más texto (probablemente el contenido principal)
                    main_content = max(content_parts, key=len)
                    content = re.sub(r'\s+', ' ', main_content).strip()
                    if len(content) > 50:  # Umbral más bajo para AmericaTV
                        return content
                
                # Si no hay párrafos ni divs con contenido, usar todo el texto del artículo
                # pero filtrar metadata
                all_text = article.get_text()
                content = re.sub(r'\s+', ' ', all_text).strip()
                # Filtrar contenido que sea solo metadata (verificar en los primeros 300 caracteres)
                # Umbral más bajo para AmericaTV (50 caracteres mínimo)
                if len(content) > 50:
                    preview = content[:300].lower() if len(content) > 300 else content.lower()
                    if not any(keyword in preview for keyword in ['compartir', 'seguir', 'síguenos', 'redes sociales']):
                        return content
        
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
            '.story-body',
            '.st-sidebar__content',
            '[data-analytics="content"]',
            '.amp-body',
            '.story-content__body',
            '.story__content'
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
        meta_author = soup.find('meta', attrs={'name': 'author'}) or soup.find('meta', attrs={'property': 'article:author'})
        if meta_author and meta_author.get('content'):
            return meta_author.get('content', '').strip()
        
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
    
    def _extract_date(self, soup, base_url=''):
        """Extraer fecha de publicación del artículo (NO la fecha de scraping)"""
        # Buscar en meta tags (prioridad alta)
        meta_selectors = [
            {'property': 'article:published_time'},
            {'name': 'article:published_time'},
            {'property': 'article:published'},
            {'name': 'publishdate'},
            {'name': 'date'},
            {'itemprop': 'datePublished'},
            {'property': 'og:published_time'},
            {'name': 'bi3dPubDate'},
            {'name': 'DC.date'},
            {'name': 'dcterms.date'},
        ]
        
        for meta_attrs in meta_selectors:
            meta_date = soup.find('meta', attrs=meta_attrs)
            if meta_date and meta_date.get('content'):
                date_content = meta_date.get('content').strip()
                if date_content:
                    return date_content
        
        # Buscar en JSON-LD structured data
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict):
                    date_published = data.get('datePublished') or data.get('dateCreated') or data.get('dateModified')
                    if date_published:
                        return date_published
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            date_published = item.get('datePublished') or item.get('dateCreated') or item.get('dateModified')
                            if date_published:
                                return date_published
            except:
                continue
        
        # Buscar en elementos HTML específicos
        selectors = [
            'time[datetime]',
            'time[pubdate]',
            '[datetime]',
            '.date',
            '.published',
            '.post-date',
            '.article-date',
            '.news-date',
            '.story-date',
            '.timestamp',
            '.publish-date',
            '[class*="date"]',
            '[class*="published"]',
            '[data-testid*="date"]',
            '[data-published]',
            'article time',
            '.article-meta time',
            '.post-meta time',
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                # Priorizar atributo datetime
                datetime_attr = element.get('datetime') or element.get('pubdate') or element.get('data-published')
                if datetime_attr:
                    return datetime_attr.strip()
                
                # Usar el texto si no hay atributo
                date_text = element.get_text().strip()
                if date_text and len(date_text) > 5:  # Evitar textos muy cortos
                    # Intentar parsear formato común de fecha
                    if re.search(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', date_text):
                        return date_text
        
        # Para NYTimes, buscar en selectores específicos
        if 'nytimes.com' in base_url.lower():
            nytimes_selectors = [
                '[data-testid="timestamp"]',
                '[itemprop="datePublished"]',
                '.css-1baulvz',  # Clase específica de NYTimes para fechas
            ]
            for selector in nytimes_selectors:
                element = soup.select_one(selector)
                if element:
                    datetime_attr = element.get('datetime') or element.get('content')
                    if datetime_attr:
                        return datetime_attr.strip()
                    date_text = element.get_text().strip()
                    if date_text:
                        return date_text
        
        # Intentar extraer fecha de la URL (muchos sitios incluyen fecha en la URL)
        if base_url:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(base_url)
                path_parts = [p for p in parsed.path.split('/') if p]
                # Buscar patrones de fecha como /2025/11/14/ o /2025-11-14/
                for part in path_parts:
                    # Formato YYYY-MM-DD o YYYY/MM/DD
                    date_match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', part)
                    if date_match:
                        year, month, day = date_match.groups()
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}T00:00:00"
                    # Formato YYYYMMDD
                    date_match = re.search(r'(\d{4})(\d{2})(\d{2})', part)
                    if date_match:
                        year, month, day = date_match.groups()
                        return f"{year}-{month}-{day}T00:00:00"
            except:
                pass
        
        # Si no se encuentra, devolver None en lugar de fecha actual
        # El código que llama debe manejar None apropiadamente
        return None
    
    def _extract_images(self, soup, base_url):
        """Extraer solo la imagen principal del artículo"""
        images = []
        parsed_url = urlparse(base_url)
        base_domain = parsed_url.netloc.lower()

        # Intentar primero con metadatos (og:image, twitter:image, etc.)
        meta_candidates = [
            soup.find('meta', attrs={'property': 'og:image'}),
            soup.find('meta', attrs={'name': 'og:image'}),
            soup.find('meta', attrs={'property': 'og:image:url'}),
            soup.find('meta', attrs={'name': 'og:image:url'}),
            soup.find('meta', attrs={'property': 'og:image:secure_url'}),
            soup.find('meta', attrs={'name': 'og:image:secure_url'}),
            soup.find('meta', attrs={'name': 'twitter:image'}),
            soup.find('meta', attrs={'property': 'twitter:image'}),
            soup.find('meta', attrs={'name': 'twitter:image:src'}),
            soup.find('meta', attrs={'property': 'twitter:image:src'}),
            soup.find('meta', attrs={'itemprop': 'image'}),
            soup.find('link', attrs={'rel': 'image_src'}),
        ]

        # Para Andina, NO usar meta tags directamente (pueden ser genéricos)
        # Pasar directamente a la lógica específica de Andina
        is_andina = 'andina.pe' in base_domain
        is_article_page = is_andina and '/agencia/noticia-' in base_url.lower() and base_url.endswith('.aspx')
        
        # Solo usar meta tags si NO es un artículo de Andina
        if not is_article_page:
            for meta in meta_candidates:
                if not meta:
                    continue

                src = meta.get('content') or meta.get('href')
                if not src:
                    continue

                full_url = urljoin(base_url, src)
                if self._is_valid_article_image(full_url):
                    images.append({
                        'url': full_url,
                        'alt': '',
                        'title': '',
                        'priority': 'meta'
                    })
                    return images[:1]
        
        # Lógica específica para Andina
        if 'andina.pe' in base_domain:
            # CRÍTICO: Verificar que estamos en una página de artículo individual, no de listado
            # Las páginas de artículo tienen /agencia/noticia- en la URL
            is_article_page = '/agencia/noticia-' in base_url.lower() and base_url.endswith('.aspx')
            
            if is_article_page:
                # En página de artículo individual, buscar la imagen principal
                # Buscar en todo el documento, pero priorizar imágenes cerca del contenido principal
                
                # Buscar el contenedor principal del artículo (puede estar en varios lugares)
                article_elem = soup.find('article')
                if not article_elem:
                    # Buscar en divs con clases específicas de contenido
                    article_elem = soup.find('div', class_=lambda x: x and 'col' in str(x) and ('s12' in str(x) or 'm8' in str(x) or 'l9' in str(x)))
            
                # Buscar TODAS las imágenes en el documento
                all_imgs = soup.find_all('img')
                logging.info(f"🔍 Andina: Encontradas {len(all_imgs)} imágenes en total")
                candidate_images = []
                count_portal = 0
                count_thumbnail = 0
                count_excluded = 0
                count_valid = 0
                
                for img in all_imgs:
                    src = img.get('src') or img.get('data-src') or img.get('data-lazy') or img.get('data-original') or img.get('data-img')
                    if src:
                        if not src.startswith('http'):
                            src = urljoin(base_url, src)
                        
                        # CRÍTICO: Solo considerar imágenes de portal.andina.pe
                        src_lower = src.lower()
                        
                        # Excluir imágenes genéricas del sitio (no del artículo)
                        exclude_patterns = [
                            'googleplay', 'google-play', 'logo', 'banner', 'header', 'footer', 
                            'icon', 'sprite', 'menu', 'nav', 'button', 'rumbo', 'bicentenario',
                            'elementos/edpe_',  # Elementos genéricos de Andina
                        ]
                        
                        if any(pattern in src_lower for pattern in exclude_patterns):
                            count_excluded += 1
                            continue  # Saltar esta imagen
                        
                        # Solo procesar imágenes de portal.andina.pe que sean fotografías de artículos
                        # Las imágenes de artículos están en EDPfotografia3/Thumbnail/YYYY/MM/DD/
                        # NO incluir EDPelementos que son imágenes genéricas del sitio
                        has_portal = 'portal.andina.pe' in src
                        has_thumbnail = 'edpfotografia3/thumbnail' in src_lower
                        has_elementos = 'edpelementos' in src_lower
                        
                        if has_portal:
                            count_portal += 1
                        if has_thumbnail:
                            count_thumbnail += 1
                        
                        if has_portal and has_thumbnail and not has_elementos:
                            # Verificar que sea una imagen válida
                            is_valid = self._is_valid_article_image(src, img)
                            if is_valid:
                                count_valid += 1
                                # Calcular posición: más cerca del inicio del body = más probable que sea principal
                                position = 0
                                parent = img.parent
                                body = soup.find('body')
                                while parent and parent != body:
                                    position += 1
                                    parent = parent.parent
                                
                                # Verificar si está dentro del contenedor del artículo
                                in_article = False
                                if article_elem:
                                    article_imgs = article_elem.find_all('img')
                                    in_article = img in article_imgs
                                
                                # Calcular distancia al título (si hay título)
                                distance_to_title = 9999
                                title_elem = soup.find('h1') or soup.find('h2', class_=lambda x: x and 'title' in str(x).lower())
                                if title_elem:
                                    # Contar elementos entre el título y la imagen
                                    current = img
                                    distance = 0
                                    while current and current != title_elem and distance < 100:
                                        distance += 1
                                        current = current.find_previous()
                                        if not current:
                                            break
                                    distance_to_title = distance
                                
                                # Verificar si está en un sidebar o sección relacionada (excluir)
                                # RELAJADO: Solo excluir si está claramente en un sidebar/widget
                                in_sidebar = False
                                p = img.parent
                                for _ in range(3):  # Revisar solo 3 niveles arriba (menos restrictivo)
                                    if p:
                                        classes = p.get('class', [])
                                        class_str = ' '.join(classes).lower()
                                        # Solo excluir si está claramente en un sidebar/widget, no en secciones relacionadas
                                        if any(kw in class_str for kw in ['sidebar', 'widget', 'aside']):
                                            in_sidebar = True
                                            break
                                        p = p.parent
                                    else:
                                        break
                                
                                # Incluir si NO está claramente en sidebar
                                # (permitir secciones relacionadas ya que pueden tener imágenes relevantes)
                                if not in_sidebar:
                                    candidate_images.append({
                                'url': src,
                                        'alt': img.get('alt', '') or img.get('title', ''),
                                        'title': img.get('title', '') or img.get('alt', ''),
                                        'position': position,
                                        'in_article': in_article,
                                        'distance_to_title': distance_to_title,
                                        'element': img
                                    })
                
                # Si hay candidatos, elegir la mejor
                if candidate_images:
                    # Priorizar:
                    # 1. Imágenes dentro del contenedor del artículo (in_article=True)
                    # 2. Imágenes más cerca del título (menor distance_to_title)
                    # 3. Imágenes más arriba en el documento (menor posición)
                    # 4. Imágenes con alt text descriptivo
                    candidate_images.sort(key=lambda x: (
                        not x['in_article'],      # False primero (True = dentro del artículo)
                        x['distance_to_title'],   # Más cerca del título primero
                        x['position'],             # Más arriba primero
                        -len(x['alt'])             # Con alt text (negativo para orden descendente)
                    ))
                    
                    # Tomar la mejor imagen
                    if candidate_images:
                        best_image = candidate_images[0]
                        images.append({
                            'url': best_image['url'],
                            'alt': best_image['alt'],
                            'title': best_image['title'],
                            'priority': 'andina-article-main'
                            })
                        logging.info(f"✅ Imagen principal de Andina extraída: {best_image['url'][:80]}...")
                        return images[:1]
                else:
                    logging.warning(f"⚠️ No se encontraron imágenes candidatas para Andina en {base_url}")
                    logging.info(f"   Estadísticas: {count_portal} portal, {count_thumbnail} thumbnail, {count_excluded} excluidas, {count_valid} válidas")
        
        # Lógica específica para RPP
        if 'rpp.pe' in base_domain:
            # RPP tiene imágenes en rpp-noticias.io
            # Priorizar og:image primero (ya se procesó arriba si existe)
            # Si no hay og:image o no es válido, buscar en el contenido
            
            # Buscar imágenes en el artículo
            article_elem = soup.find('article') or soup.find('main') or soup.find('div', class_=lambda x: x and ('article' in str(x).lower() or 'noticia' in str(x).lower()))
            
            if article_elem:
                # Buscar imágenes dentro del artículo
                article_imgs = article_elem.find_all('img')
                candidate_images = []
                
                for img in article_imgs:
                    src = img.get('src') or img.get('data-src') or img.get('data-lazy') or img.get('data-original')
                    if not src:
                        continue
                    
                        if not src.startswith('http'):
                            src = urljoin(base_url, src)
                        
                    src_lower = src.lower()
                    
                    # Solo considerar imágenes de rpp-noticias.io (no avatares, logos, etc.)
                    if 'rpp-noticias.io' not in src_lower:
                        continue
                    
                    # Excluir avatares, logos, iconos
                    exclude_patterns = [
                        '/avatar/', '/logo', '/icon', '/sprite', '/button',
                        'avatar', 'logo', 'icon', 'sprite', 'button'
                    ]
                    
                    if any(pattern in src_lower for pattern in exclude_patterns):
                        continue
                    
                    # Priorizar imágenes "large" que son las principales
                    # Formato: https://e.rpp-noticias.io/large/YYYY/MM/DD/...
                    # O: https://f.rpp-noticias.io/YYYY/MM/DD/...?width=1020 (imagen grande)
                    is_large = '/large/' in src_lower or 'width=1020' in src_lower or 'width=1200' in src_lower
                    is_medium = 'width=640' in src_lower or 'width=800' in src_lower
                    is_small = 'width=160' in src_lower or 'width=320' in src_lower
                    
                    # Obtener alt text para validar relevancia
                    alt_text = (img.get('alt', '') or img.get('title', '')).lower()
                    
                    # Verificar que sea una imagen válida
                    if self._is_valid_article_image(src, img):
                        # Calcular prioridad
                        priority = 0
                        if is_large:
                            priority = 3
                        elif is_medium:
                            priority = 2
                        elif is_small:
                            priority = 1
                        
                        # Aumentar prioridad si tiene alt text descriptivo
                        if alt_text and len(alt_text) > 10:
                            priority += 1
                        
                        # Verificar si está en un figure (típicamente imágenes principales)
                        in_figure = img.find_parent('figure') is not None
                        if in_figure:
                            priority += 1
                        
                        candidate_images.append({
                            'url': src,
                            'alt': img.get('alt', ''),
                            'title': img.get('title', ''),
                            'priority': priority,
                            'is_large': is_large
                        })
                
                # Si hay candidatos, elegir el mejor
                if candidate_images:
                    # Ordenar por prioridad (mayor primero)
                    candidate_images.sort(key=lambda x: (x['priority'], x['is_large']), reverse=True)
                    
                    best_image = candidate_images[0]
                    images.append({
                        'url': best_image['url'],
                        'alt': best_image['alt'],
                        'title': best_image['title'],
                        'priority': 'rpp-article-main'
                                })
                    logging.info(f"✅ Imagen principal de RPP extraída: {best_image['url'][:80]}...")
                    return images[:1]
                else:
                    # Si no hay imágenes en el artículo, usar og:image si existe y es válido
                    # (ya se procesó arriba, pero verificar que sea de rpp-noticias.io)
                    if images and len(images) > 0:
                        og_img = images[0]
                        if 'rpp-noticias.io' in og_img['url'].lower():
                            return images[:1]
            
            # Si no se encontró imagen en el artículo, usar og:image si existe
            if images and len(images) > 0:
                                return images[:1]
        
        # Lógica específica para NYTimes
        if 'nytimes.com' in base_domain:
            # NYTimes usa og:image en meta tags, pero también tiene imágenes en el artículo
            # Buscar primero en meta tags (ya se hizo arriba, pero asegurarse que funcione)
            
            # Buscar también en el JSON-LD structured data que NYTimes usa
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_ld_scripts:
                try:
                    import json
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        # Buscar image en el JSON-LD
                        image = data.get('image') or data.get('thumbnailUrl')
                        if image:
                            # image puede ser dict, str o lista
                            candidates = []
                            if isinstance(image, dict):
                                candidates.append(image.get('url') or image.get('@id'))
                            elif isinstance(image, list):
                                for it in image:
                                    if isinstance(it, dict):
                                        candidates.append(it.get('url') or it.get('@id'))
                                    elif isinstance(it, str):
                                        candidates.append(it)
                            elif isinstance(image, str):
                                candidates.append(image)
                            for cand in candidates:
                                if not cand:
                                    continue
                                full_url = urljoin(base_url, cand)
                                if self._is_valid_article_image(full_url):
                                    images.append({
                                        'url': full_url,
                                        'alt': '',
                                        'title': '',
                                        'priority': 'nytimes-jsonld'
                                    })
                                    return images[:1]
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                image = item.get('image') or item.get('thumbnailUrl')
                                if image:
                                    candidates = []
                                    if isinstance(image, dict):
                                        candidates.append(image.get('url') or image.get('@id'))
                                    elif isinstance(image, list):
                                        for it in image:
                                            if isinstance(it, dict):
                                                candidates.append(it.get('url') or it.get('@id'))
                                            elif isinstance(it, str):
                                                candidates.append(it)
                                    elif isinstance(image, str):
                                        candidates.append(image)
                                    for cand in candidates:
                                        if not cand:
                                            continue
                                        full_url = urljoin(base_url, cand)
                                        if self._is_valid_article_image(full_url):
                                            images.append({
                                                'url': full_url,
                                                'alt': '',
                                                'title': '',
                                                'priority': 'nytimes-jsonld'
                                            })
                                            return images[:1]
                except:
                    continue
            
            # Buscar en selectores específicos de NYTimes
            nytimes_selectors = [
                'article figure img',
                'article picture img',
                '.css-1qwxefa img',  # Clase específica de NYTimes para imágenes principales
                '.css-79elbk img',   # otras variantes frecuentes
                '[data-testid="article-image"] img',
                '[data-testid="lazyimage"] img',
                '[itemprop="image"] img',
                '[class*="image"] img:first-of-type',
                'figure[itemprop="image"] img',
                'picture source[type="image/jpeg"]',
            ]
            
            for selector in nytimes_selectors:
                try:
                    elements = soup.select(selector)
                    for img in elements:
                        src = None
                        
                        # Para picture source, obtener el srcset
                        if img.name == 'source':
                            srcset = img.get('srcset')
                            if srcset:
                                # Tomar la primera URL del srcset
                                src = srcset.split(',')[0].strip().split()[0]
                        else:
                            src = (img.get('src') or 
                                   img.get('data-src') or 
                                   img.get('data-srcset') or
                                   img.get('srcset'))
                        
                        if src:
                            # Manejar srcset - tomar la primera URL
                            if ' ' in src or ',' in src:
                                src = src.split()[0].split(',')[0]
                            
                            # Asegurar URL completa
                            if not src.startswith('http'):
                                src = urljoin(base_url, src)
                            
                            # Filtrar imágenes pequeñas o de navegación
                            if any(kw in src.lower() for kw in ['logo', 'icon', 'avatar', 'profile', 'thumbnail', 'thumb']):
                                continue
                            
                            # Preferir imágenes de static01.nyt.com o nytimes.com
                            if 'static01.nyt.com' in src or 'nytimes.com' in src:
                                if self._is_valid_article_image(src, img if img.name == 'img' else None):
                                    images.append({
                                        'url': src,
                                        'alt': img.get('alt', '') if img.name == 'img' else '',
                                        'title': img.get('title', '') if img.name == 'img' else '',
                                        'priority': 'nytimes'
                                    })
                                    return images[:1]
                except:
                    continue
            
            # Si no se encontró, buscar la primera imagen grande en el artículo
            article = soup.find('article')
            if article:
                all_imgs = article.find_all('img')
                for img in all_imgs:
                    src = (img.get('src') or 
                           img.get('data-src') or 
                           img.get('srcset'))
                    
                    if src:
                        # Manejar srcset
                        if ' ' in src or ',' in src:
                            src = src.split()[0].split(',')[0]
                        
                        if not src.startswith('http'):
                            src = urljoin(base_url, src)
                        
                        # Verificar dimensiones si están disponibles
                        width = img.get('width')
                        height = img.get('height')
                        
                        # Preferir imágenes grandes (más de 200px)
                        if width and height:
                            try:
                                w, h = int(width), int(height)
                                if w < 200 or h < 200:
                                    continue
                            except:
                                pass
                        
                        # Filtrar iconos/logos
                        if any(kw in src.lower() for kw in ['logo', 'icon', 'avatar', 'profile', 'thumbnail', 'thumb', 'sprite']):
                            continue
                        
                        if self._is_valid_article_image(src, img):
                            images.append({
                                'url': src,
                                'alt': img.get('alt', ''),
                                'title': img.get('title', ''),
                                'priority': 'nytimes-fallback'
                            })
                            return images[:1]
        
        # Lógica específica para AmericaTV
        if 'americatv.com.pe' in base_domain:
            # Buscar imagen principal en el artículo
            article = soup.find('article')
            if article:
                # Buscar imagen principal (típicamente la primera imagen grande)
                article_imgs = article.find_all('img')
                for img in article_imgs:
                    src = (img.get('src') or 
                           img.get('data-src') or 
                           img.get('data-lazy') or 
                           img.get('data-original'))
                    
                    if src:
                        # Filtrar imágenes pequeñas/iconos (AmericaTV usa imágenes pequeñas para iconos)
                        # Las imágenes principales suelen tener dimensiones en el nombre o ser de e-an.americatv.com.pe
                        if 'cms-' in src and ('20x20' in src or '40x40' in src):
                            continue  # Es un icono pequeño
                        
                        # Preferir imágenes de e-an.americatv.com.pe (CDN de imágenes principales)
                        if 'e-an.americatv.com.pe' in src:
                            if ',' in src:
                                src = src.split(',')[0]
                            src = src.split()[0]
                            full_url = urljoin(base_url, src)
                            
                            if self._is_valid_article_image(full_url, img):
                                images.append({
                                    'url': full_url,
                                    'alt': img.get('alt', ''),
                                    'title': img.get('title', ''),
                                    'priority': 'americatv'
                                })
                                return images[:1]
            
            # Buscar en selectores específicos de AmericaTV
            americatv_selectors = [
                'article img:first-of-type',
                '.article-image img',
                '.featured-image img',
                '.main-image img',
                'figure img:first-of-type',
            ]
            
            for selector in americatv_selectors:
                elements = soup.select(selector)
                for img in elements:
                    src = (img.get('src') or 
                           img.get('data-src') or 
                           img.get('data-lazy') or 
                           img.get('data-original'))
                    
                    if src:
                        # Filtrar iconos pequeños
                        if 'cms-' in src and ('20x20' in src or '40x40' in src):
                            continue
                        
                        if ',' in src:
                            src = src.split(',')[0]
                        src = src.split()[0]
                        full_url = urljoin(base_url, src)
                        
                        if self._is_valid_article_image(full_url, img):
                            images.append({
                                'url': full_url,
                                'alt': img.get('alt', ''),
                                'title': img.get('title', ''),
                                'priority': 'americatv'
                            })
                            return images[:1]
        
        # Lógica específica para peru21.pe
        if 'peru21.pe' in base_domain:
            # Buscar imágenes en elementos específicos de peru21.pe
            peru21_selectors = [
                '.field-name-field-image img',
                '.field-type-image img',
                '.image-field img',
                '.article-header img',
                '.nota-header img',
                '.content-header img',
                'figure img',
                '.media img',
                '.image-wrapper img',
                '[class*="image"] img',
                '[class*="imagen"] img',
                '[class*="foto"] img',
            ]
            
            for selector in peru21_selectors:
                elements = soup.select(selector)
                for img in elements:
                    # Buscar en múltiples atributos
                    src = (img.get('src') or 
                           img.get('data-src') or 
                           img.get('data-lazy') or 
                           img.get('data-original') or
                           img.get('data-srcset') or
                           img.get('data-image'))
                    
                    if src:
                        # Manejar srcset
                        if ',' in src:
                            src = src.split(',')[0]
                        src = src.split()[0]
                        full_url = urljoin(base_url, src)
                        
                        if self._is_valid_article_image(full_url, img):
                            images.append({
                                'url': full_url,
                                'alt': img.get('alt', ''),
                                'title': img.get('title', ''),
                                'priority': 'peru21'
                            })
                            return images[:1]
            
            # Buscar en todas las imágenes y filtrar por tamaño/clase
            all_imgs = soup.find_all('img')
            for img in all_imgs:
                src = (img.get('src') or 
                       img.get('data-src') or 
                       img.get('data-lazy') or 
                       img.get('data-original'))
                
                if src:
                    # Filtrar imágenes pequeñas o de iconos
                    width = img.get('width')
                    height = img.get('height')
                    img_class = ' '.join(img.get('class', [])).lower()
                    
                    # Excluir iconos, logos, avatares
                    if any(keyword in img_class for keyword in ['icon', 'logo', 'avatar', 'profile', 'sprite']):
                        continue
                    
                    # Preferir imágenes con dimensiones razonables
                    if width and height:
                        try:
                            w, h = int(width), int(height)
                            if w < 200 or h < 200:  # Muy pequeñas, probablemente iconos
                                continue
                        except:
                            pass
                    
                    if ',' in src:
                        src = src.split(',')[0]
                    src = src.split()[0]
                    full_url = urljoin(base_url, src)
                    
                    if self._is_valid_article_image(full_url, img):
                        images.append({
                            'url': full_url,
                            'alt': img.get('alt', ''),
                            'title': img.get('title', ''),
                            'priority': 'peru21-fallback'
                        })
                        return images[:1]
        
        # Selectores prioritarios para imagen principal del artículo
        main_image_selectors = [
            # Imagen principal del artículo
            '.article-image img',
            '.post-image img', 
            '.news-image img',
            '.story-image img',
            '.featured-image img',
            '.main-image img',
            '.hero-image img',
            '.lead-image img',
            '.article-header img',
            '.post-header img',
            '.entry-image img',
            '.content-image img',
            # Selectores específicos por periódico
            '.nota-principal img',
            '.noticia-principal img',
            '.articulo-principal img',
            '.main-content img',
            '.article-content img:first-of-type',
            '.post-content img:first-of-type',
            # Imágenes dentro del contenido del artículo
            '.article-body img:first-of-type',
            '.post-body img:first-of-type',
            '.entry-content img:first-of-type',
            '.content img:first-of-type'
        ]
        
        # Buscar imagen principal primero
        for selector in main_image_selectors:
            elements = soup.select(selector)
            for img in elements:
                src = img.get('src') or img.get('data-src') or img.get('data-lazy') or img.get('data-original') or img.get('data-srcset')
                if src:
                    # Manejar atributos srcset con múltiples URLs
                    if ',' in src:
                        src = src.split(',')[0]
                    src = src.split()[0]
                    full_url = urljoin(base_url, src)
                    
                    # Validar que sea una imagen válida
                    if self._is_valid_article_image(full_url, img):
                        images.append({
                            'url': full_url,
                            'alt': img.get('alt', ''),
                            'title': img.get('title', ''),
                            'priority': 'main'
                        })
                        # Solo devolver la primera imagen principal encontrada
                        return images[:1]
        
        # Si no se encuentra imagen principal, buscar cualquier imagen válida
        # PERO: Para Andina, NO usar fallback genérico (ya se procesó arriba)
        if 'andina.pe' in base_domain and '/agencia/noticia-' in base_url.lower() and base_url.endswith('.aspx'):
            # Ya se procesó la lógica específica de Andina arriba
            # Si no se encontró imagen, no usar fallback genérico
            return images[:1]
        
        fallback_selectors = [
            'img[src]',
            'img[data-src]',
            'img[data-lazy]'
        ]
        
        for selector in fallback_selectors:
            elements = soup.select(selector)
            for img in elements:
                src = img.get('src') or img.get('data-src') or img.get('data-lazy')
                if src:
                    if ',' in src:
                        src = src.split(',')[0]
                    src = src.split()[0]
                    full_url = urljoin(base_url, src)
                    
                    # Validar que sea una imagen válida y no sea de categorías/menús
                    if self._is_valid_article_image(full_url, img):
                        images.append({
                            'url': full_url,
                            'alt': img.get('alt', ''),
                            'title': img.get('title', ''),
                            'priority': 'fallback'
                        })
                        # Solo devolver la primera imagen válida encontrada
                        return images[:1]
        
        return images[:1]  # Máximo 1 imagen por artículo
    
    def _is_valid_article_image(self, url, img_element=None):
        """Validar si una URL de imagen es válida para un artículo
        
        Filtra imágenes genéricas, logos, iconos, etc.
        """
        if not url:
            return False
            
        # Verificar extensión de imagen
        if not any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
            return False

        alt_text = ''
        title_text = ''
        class_text = ''
        if img_element is not None:
            alt_text = (img_element.get('alt', '') or '').lower()
            title_text = (img_element.get('title', '') or '').lower()
            class_text = ' '.join(img_element.get('class', [])).lower()

        src_text = url.lower()

        placeholder_keywords = [
            'logo', 'placeholder', 'generic', 'avatar', 'user', 'svgto_', 'search_', 'hamburger'
        ]
        # Verificar placeholder_keywords pero excluir "default" si está en una ruta de archivo válida
        for keyword in placeholder_keywords:
            if keyword in src_text:
                return False
        
        # "default" solo es problemático si está solo o en contexto de placeholder, no en rutas como /sites/default/
        if 'default' in src_text:
            # Si "default" está en una ruta de archivo (tiene / antes y después o al final), es válido
            if '/default/' in src_text or src_text.endswith('/default'):
                pass  # Es parte de una ruta válida, continuar
            elif 'default' == src_text or 'default.' in src_text:
                return False  # Es un placeholder

        # Palabras que indican que NO es una imagen de artículo
        # NOTA: "thumbnail" puede ser parte de URLs válidas (ej: portal.andina.pe/EDPfotografia3/Thumbnail/)
        # así que solo excluir si está en alt/title/class, no en la URL
        exclude_keywords = [
            'logo', 'banner', 'advertisement', 'ad-', 'publicidad', 'sponsor',
            'menu', 'nav', 'header', 'footer', 'sidebar', 'widget',
            'icon', 'avatar', 'profile', 'user', 'social',
            'category', 'categoria', 'tag', 'etiqueta',
            'button', 'btn', 'boton', 'link', 'enlace',
            'pixel', 'tracking', 'analytics', 'stat',
            'placeholder', 'loading', 'spinner',
            'appstore', 'app-store', 'playstore', 'play-store', 'download',
            'badge', 'ribbon', 'sticker', 'decoration',
            'googleplay', 'google-play',  # Banner de Google Play
            'rumbo', 'bicentenario',  # Imágenes genéricas de Andina
            'edpelementos',  # Elementos genéricos de Andina (NO fotografías de artículos)
        ]
        # Excluir "thumbnail", "thumb", "mini", "small", "tiny" solo si están en alt/title/class, NO en URL
        # (las URLs de Andina tienen "Thumbnail" en la ruta pero son imágenes válidas)
        size_keywords = ['thumbnail', 'thumb', 'mini', 'small', 'tiny']
        for keyword in size_keywords:
            if keyword in alt_text or keyword in title_text or keyword in class_text:
                return False
        
        for keyword in exclude_keywords:
            if (keyword in alt_text or keyword in title_text or
                    keyword in class_text or keyword in src_text):
                return False

        # Palabras que indican que SÍ es una imagen de artículo
        include_keywords = [
            'article', 'articulo', 'news', 'noticia', 'story', 'historia',
            'post', 'entrada', 'content', 'contenido', 'main', 'principal',
            'featured', 'destacada', 'hero', 'lead', 'cover', 'portada',
            'image', 'imagen', 'photo', 'foto', 'picture', 'fotografia'
        ]
        for keyword in include_keywords:
            if (keyword in alt_text or keyword in title_text or
                    keyword in class_text or keyword in src_text):
                return True

        return True

    def _clean_text(self, text: Optional[str]) -> str:
        if not text:
            return ''
        return re.sub(r'\s+', ' ', text).strip()

    def _parse_ms_date(self, value: Optional[str]) -> str:
        if not value:
            return datetime.now().isoformat()
        match = re.search(r'/Date\((\d+)\)/', value)
        if not match:
            return self._clean_text(value)
        try:
            ms = int(match.group(1))
            return datetime.utcfromtimestamp(ms / 1000).isoformat()
        except Exception:
            return datetime.now().isoformat()

    def _get_elperuano_section_id(self, url: str) -> Optional[str]:
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            hidden = soup.find('input', id='se')
            if hidden and hidden.get('value'):
                return hidden['value']
        except Exception as e:
            logging.warning(f"⚠️ No se pudo obtener id de sección desde {url}: {e}")

        try:
            path = urlparse(url).path.strip('/').split('/')
            section_slug = path[0] if path else ''
            section_map = {
                'politica': '1',
                'pais': '2',
                'economia': '3',
                'mundo': '4',
                'deporte': '5',
                'cultural': '6',
                'ciencia-tecnologia': '7',
                'opinion': '8',
            }
            return section_map.get(section_slug, '3')
        except Exception:
            return '3'

    def _scrape_elperuano_section(self, url: str, max_articles: int) -> List[Dict]:
        section_id = self._get_elperuano_section_id(url)
        if not section_id:
            logging.warning("⚠️ No se pudo determinar la sección de El Peruano.")
            return []

        api_url = f"https://elperuano.pe/portal/_GetNoticiasSeccionPagingWorker?idsec={section_id}&pageIndex=1&pageSize={max(10, max_articles)}"
        try:
            response = self.session.get(api_url, timeout=30)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logging.error(f"❌ Error obteniendo datos desde API de El Peruano: {e}")
            return []

        articles: List[Dict] = []
        for item in data:
            if len(articles) >= max_articles:
                break
            try:
                title = self._clean_text(item.get('vchTitulo'))
                if not title:
                    continue

                content = self._clean_text(item.get('vchDescripcion') or item.get('vchBajada') or '')
                if not content:
                    content = self._clean_text(item.get('vchVolada') or item.get('Sumilla') or '')

                summary = self._clean_text(item.get('vchBajada') or item.get('Sumilla') or content[:200])
                article_url = urljoin("https://elperuano.pe/", (item.get('URLFriendLy') or '').lstrip('/'))
                image_url = self._clean_text(item.get('vchRutaCompletaFotografia'))
                images = []
                if image_url:
                    images.append({
                        'url': image_url,
                        'alt': title,
                        'title': title,
                        'priority': 'meta'
                    })

                articles.append({
                    'title': title,
                    'content': content,
                    'url': article_url,
                    'summary': summary if summary else content[:200],
                    'author': self._clean_text(item.get('vchCreador')),
                    'published_date': self._parse_ms_date(item.get('dtmFecha')),
                    'scraped_at': datetime.now().isoformat(),
                    'images_found': len(images),
                    'images_downloaded': 0,
                    'images_data': images
                })
            except Exception as e:
                logging.warning(f"⚠️ Error procesando nota de El Peruano: {e}")
                continue

        logging.info(f"🎉 Scraping El Peruano completado: {len(articles)} artículos extraídos")
        return articles
    
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

