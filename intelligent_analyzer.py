#!/usr/bin/env python3
"""
Analizador inteligente de páginas web
Examina la página y sugiere el mejor método de scraping
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re
import json
import logging
from datetime import datetime
import time

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class IntelligentPageAnalyzer:
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
    
    def analyze_page(self, url):
        """Analizar página y sugerir el mejor método de scraping"""
        try:
            logging.info(f"🔍 Analizando página: {url}")
            
            # Obtener la página
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Análisis completo
            analysis = {
                'url': url,
                'domain': urlparse(url).netloc,
                'timestamp': datetime.now().isoformat(),
                'page_size': len(response.content),
                'response_time': response.elapsed.total_seconds(),
                'status_code': response.status_code,
                'content_type': response.headers.get('content-type', ''),
                'analysis': self._analyze_content(soup, url, response),
                'recommendation': None,
                'confidence': 0,
                'alternative_methods': []
            }
            
            # Generar recomendación
            recommendation = self._generate_recommendation(analysis)
            analysis['recommendation'] = recommendation['method']
            analysis['confidence'] = recommendation['confidence']
            analysis['alternative_methods'] = recommendation['alternatives']
            analysis['reasoning'] = recommendation['reasoning']
            
            logging.info(f"✅ Análisis completado: {analysis['recommendation']} (confianza: {analysis['confidence']}%)")
            
            return analysis
            
        except Exception as e:
            logging.error(f"❌ Error analizando página: {e}")
            return {
                'url': url,
                'error': str(e),
                'recommendation': 'improved',
                'confidence': 50,
                'reasoning': 'Error en análisis, usando método por defecto'
            }
    
    def _analyze_content(self, soup, url, response):
        """Analizar el contenido de la página"""
        analysis = {
            'javascript_detected': False,
            'dynamic_content': False,
            'spa_framework': False,
            'lazy_loading': False,
            'pagination': False,
            'ajax_requests': False,
            'infinite_scroll': False,
            'news_site': False,
            'article_links': 0,
            'image_count': 0,
            'form_count': 0,
            'iframe_count': 0,
            'script_count': 0,
            'css_frameworks': [],
            'meta_tags': {},
            'page_structure': {},
            'performance_indicators': {}
        }
        
        # Detectar JavaScript
        scripts = soup.find_all('script')
        analysis['script_count'] = len(scripts)
        
        if scripts:
            analysis['javascript_detected'] = True
            
            # Detectar frameworks SPA
            script_text = ' '.join([script.get_text() for script in scripts if script.get_text()])
            spa_frameworks = ['react', 'vue', 'angular', 'svelte', 'next.js', 'nuxt']
            for framework in spa_frameworks:
                if framework.lower() in script_text.lower():
                    analysis['spa_framework'] = True
                    analysis['css_frameworks'].append(framework)
                    break
        
        # Detectar contenido dinámico
        dynamic_indicators = [
            'data-src', 'data-lazy', 'lazy', 'loading="lazy"',
            'onclick', 'onload', 'onchange', 'addEventListener'
        ]
        
        for indicator in dynamic_indicators:
            if soup.find(attrs={indicator.split('=')[0]: True}):
                analysis['dynamic_content'] = True
                if 'lazy' in indicator:
                    analysis['lazy_loading'] = True
                break
        
        # Detectar paginación
        pagination_selectors = [
            '.pagination', '.pager', '.page-nav', '.paging',
            'a[href*="page="]', 'a[href*="p="]', 'a[href*="/page/"]',
            '.next', '.prev', '.page-numbers'
        ]
        
        for selector in pagination_selectors:
            if soup.select(selector):
                analysis['pagination'] = True
                break
        
        # Detectar infinite scroll
        infinite_indicators = [
            'infinite', 'scroll', 'load-more', 'show-more',
            'data-infinite', 'data-scroll'
        ]
        
        for indicator in infinite_indicators:
            if soup.find(string=re.compile(indicator, re.I)):
                analysis['infinite_scroll'] = True
                break
        
        # Detectar AJAX
        ajax_indicators = [
            'ajax', 'fetch', 'XMLHttpRequest', 'axios',
            'data-ajax', 'data-fetch'
        ]
        
        for indicator in ajax_indicators:
            if soup.find(string=re.compile(indicator, re.I)):
                analysis['ajax_requests'] = True
                break
        
        # Detectar sitio de noticias
        news_indicators = [
            'article', 'news', 'noticia', 'post', 'story',
            'headline', 'titular', 'breaking', 'última hora'
        ]
        
        for indicator in news_indicators:
            if soup.find(class_=re.compile(indicator, re.I)):
                analysis['news_site'] = True
                break
        
        # Contar enlaces de artículos
        article_selectors = [
            'article a', '.article a', '.news-item a', '.post a',
            'h1 a', 'h2 a', 'h3 a', '.title a', '.headline a',
            'a[href*="/noticia/"]', 'a[href*="/articulo/"]', 'a[href*="/post/"]'
        ]
        
        article_links = set()
        for selector in article_selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href and len(href) > 20:
                    article_links.add(href)
        
        analysis['article_links'] = len(article_links)
        
        # Contar imágenes
        images = soup.find_all('img')
        analysis['image_count'] = len(images)
        
        # Contar formularios
        forms = soup.find_all('form')
        analysis['form_count'] = len(forms)
        
        # Contar iframes
        iframes = soup.find_all('iframe')
        analysis['iframe_count'] = len(iframes)
        
        # Analizar meta tags
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                analysis['meta_tags'][name] = content
        
        # Analizar estructura de página
        analysis['page_structure'] = {
            'has_header': bool(soup.find('header') or soup.find(class_=re.compile('header', re.I))),
            'has_nav': bool(soup.find('nav') or soup.find(class_=re.compile('nav', re.I))),
            'has_main': bool(soup.find('main') or soup.find(class_=re.compile('main', re.I))),
            'has_footer': bool(soup.find('footer') or soup.find(class_=re.compile('footer', re.I))),
            'has_sidebar': bool(soup.find(class_=re.compile('sidebar', re.I))),
            'has_aside': bool(soup.find('aside'))
        }
        
        # Indicadores de rendimiento
        analysis['performance_indicators'] = {
            'large_page': len(response.content) > 500000,  # > 500KB
            'many_scripts': len(scripts) > 10,
            'many_images': len(images) > 50,
            'complex_structure': len(soup.find_all()) > 1000,
            'external_resources': len(soup.find_all('link', rel='stylesheet')) > 5
        }
        
        return analysis
    
    def _generate_recommendation(self, analysis):
        """Generar recomendación basada en el análisis"""
        content_analysis = analysis['analysis']
        confidence = 0
        reasoning = []
        alternatives = []
        
        # Puntuación para cada método
        scores = {
            'improved': 0,
            'hybrid': 0,
            'optimized': 0,
            'selenium': 0,
            'requests': 0
        }
        
        # Análisis de JavaScript
        if content_analysis['javascript_detected']:
            scores['selenium'] += 30
            scores['hybrid'] += 20
            reasoning.append("JavaScript detectado")
            
            if content_analysis['spa_framework']:
                scores['selenium'] += 25
                scores['hybrid'] += 15
                reasoning.append("Framework SPA detectado")
        
        # Análisis de contenido dinámico
        if content_analysis['dynamic_content']:
            scores['selenium'] += 25
            scores['hybrid'] += 20
            scores['improved'] += 10
            reasoning.append("Contenido dinámico detectado")
            
            if content_analysis['lazy_loading']:
                scores['selenium'] += 20
                scores['hybrid'] += 15
                reasoning.append("Lazy loading detectado")
        
        # Análisis de paginación
        if content_analysis['pagination']:
            scores['optimized'] += 15
            scores['hybrid'] += 10
            reasoning.append("Paginación detectada")
        
        # Análisis de infinite scroll
        if content_analysis['infinite_scroll']:
            scores['selenium'] += 20
            scores['hybrid'] += 15
            reasoning.append("Infinite scroll detectado")
        
        # Análisis de AJAX
        if content_analysis['ajax_requests']:
            scores['selenium'] += 15
            scores['hybrid'] += 10
            reasoning.append("Requests AJAX detectados")
        
        # Análisis de sitio de noticias
        if content_analysis['news_site']:
            scores['improved'] += 20
            scores['optimized'] += 15
            reasoning.append("Sitio de noticias detectado")
        
        # Análisis de enlaces de artículos
        article_count = content_analysis['article_links']
        if article_count > 50:
            scores['optimized'] += 20
            scores['improved'] += 15
            reasoning.append(f"Muchos artículos detectados ({article_count})")
        elif article_count > 20:
            scores['improved'] += 15
            scores['optimized'] += 10
            reasoning.append(f"Artículos moderados detectados ({article_count})")
        elif article_count > 0:
            scores['improved'] += 10
            reasoning.append(f"Algunos artículos detectados ({article_count})")
        else:
            scores['selenium'] += 10
            scores['hybrid'] += 5
            reasoning.append("Pocos artículos detectados, puede necesitar JavaScript")
        
        # Análisis de rendimiento
        perf = content_analysis['performance_indicators']
        if perf['large_page']:
            scores['optimized'] += 10
            scores['improved'] += 5
            reasoning.append("Página grande detectada")
        
        if perf['many_scripts']:
            scores['selenium'] += 10
            scores['hybrid'] += 5
            reasoning.append("Muchos scripts detectados")
        
        if perf['complex_structure']:
            scores['optimized'] += 10
            scores['improved'] += 5
            reasoning.append("Estructura compleja detectada")
        
        # Bonificaciones especiales
        if not content_analysis['javascript_detected'] and not content_analysis['dynamic_content']:
            scores['improved'] += 25
            scores['requests'] += 20
            reasoning.append("Contenido estático detectado")
        
        if content_analysis['news_site'] and article_count > 20:
            scores['improved'] += 15
            reasoning.append("Sitio de noticias con buen contenido")
        
        # Determinar método recomendado
        best_method = max(scores, key=scores.get)
        best_score = scores[best_method]
        
        # Calcular confianza
        total_score = sum(scores.values())
        if total_score > 0:
            confidence = int((best_score / total_score) * 100)
        
        # Generar alternativas
        sorted_methods = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        alternatives = [method for method, score in sorted_methods[1:3] if score > 0]
        
        # Ajustar recomendación basada en confianza
        if confidence < 60:
            # Si la confianza es baja, usar método más conservador
            if best_method in ['selenium', 'hybrid']:
                best_method = 'improved'
                confidence = 70
                reasoning.append("Confianza baja, usando método conservador")
        
        return {
            'method': best_method,
            'confidence': confidence,
            'alternatives': alternatives,
            'reasoning': reasoning,
            'scores': scores
        }
    
    def get_method_description(self, method):
        """Obtener descripción del método"""
        descriptions = {
            'improved': {
                'name': 'Mejorado',
                'description': 'Método robusto sin Selenium, ideal para contenido estático y sitios de noticias',
                'pros': ['Rápido', 'Estable', 'Sin dependencias de navegador', 'Ideal para noticias'],
                'cons': ['Limitado con JavaScript complejo'],
                'best_for': 'Sitios de noticias, blogs, contenido estático'
            },
            'hybrid': {
                'name': 'Híbrido',
                'description': 'Combina Selenium y Requests automáticamente para máximo rendimiento',
                'pros': ['Versátil', 'Automático', 'Buen rendimiento', 'Maneja contenido dinámico'],
                'cons': ['Más lento que métodos puros'],
                'best_for': 'Sitios mixtos, contenido dinámico moderado'
            },
            'optimized': {
                'name': 'Optimizado',
                'description': 'Usa cache y paralelismo para máximo rendimiento en sitios grandes',
                'pros': ['Muy rápido', 'Paralelo', 'Cache inteligente', 'Ideal para sitios grandes'],
                'cons': ['Requiere más recursos', 'Complejo'],
                'best_for': 'Sitios grandes, muchos artículos, paginación'
            },
            'selenium': {
                'name': 'Selenium',
                'description': 'Para contenido dinámico y JavaScript complejo',
                'pros': ['Maneja JavaScript', 'Contenido dinámico', 'Interactivo'],
                'cons': ['Lento', 'Requiere navegador', 'Consume recursos'],
                'best_for': 'SPAs, contenido dinámico, JavaScript pesado'
            },
            'requests': {
                'name': 'Requests',
                'description': 'Rápido para contenido estático',
                'pros': ['Muy rápido', 'Ligero', 'Simple'],
                'cons': ['No maneja JavaScript', 'Limitado'],
                'best_for': 'Contenido estático, sitios simples'
            }
        }
        
        return descriptions.get(method, descriptions['improved'])
    
    def close(self):
        """Cerrar sesión"""
        self.session.close()

def test_analyzer():
    """Probar el analizador inteligente"""
    analyzer = IntelligentPageAnalyzer()
    
    # URLs de prueba
    test_urls = [
        "https://elcomercio.pe/",
        "https://elpopular.pe/",
        "https://peru21.pe/",
        "https://diariosinfronteras.com.pe/",
        "https://github.com/",
        "https://stackoverflow.com/"
    ]
    
    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"🔍 ANALIZANDO: {url}")
        print(f"{'='*60}")
        
        analysis = analyzer.analyze_page(url)
        
        if 'error' in analysis:
            print(f"❌ Error: {analysis['error']}")
            continue
        
        print(f"📊 ANÁLISIS:")
        print(f"   • Dominio: {analysis['domain']}")
        print(f"   • Tamaño: {analysis['page_size']:,} bytes")
        print(f"   • Tiempo de respuesta: {analysis['response_time']:.2f}s")
        print(f"   • JavaScript: {'✅' if analysis['analysis']['javascript_detected'] else '❌'}")
        print(f"   • Contenido dinámico: {'✅' if analysis['analysis']['dynamic_content'] else '❌'}")
        print(f"   • SPA Framework: {'✅' if analysis['analysis']['spa_framework'] else '❌'}")
        print(f"   • Lazy loading: {'✅' if analysis['analysis']['lazy_loading'] else '❌'}")
        print(f"   • Paginación: {'✅' if analysis['analysis']['pagination'] else '❌'}")
        print(f"   • Infinite scroll: {'✅' if analysis['analysis']['infinite_scroll'] else '❌'}")
        print(f"   • Sitio de noticias: {'✅' if analysis['analysis']['news_site'] else '❌'}")
        print(f"   • Enlaces de artículos: {analysis['analysis']['article_links']}")
        print(f"   • Imágenes: {analysis['analysis']['image_count']}")
        print(f"   • Scripts: {analysis['analysis']['script_count']}")
        
        print(f"\n🎯 RECOMENDACIÓN:")
        print(f"   • Método: {analysis['recommendation'].upper()}")
        print(f"   • Confianza: {analysis['confidence']}%")
        print(f"   • Razones: {', '.join(analysis['reasoning'])}")
        
        if analysis['alternative_methods']:
            print(f"   • Alternativas: {', '.join(analysis['alternative_methods'])}")
        
        # Mostrar descripción del método
        method_info = analyzer.get_method_description(analysis['recommendation'])
        print(f"\n📋 DESCRIPCIÓN DEL MÉTODO:")
        print(f"   • Nombre: {method_info['name']}")
        print(f"   • Descripción: {method_info['description']}")
        print(f"   • Mejor para: {method_info['best_for']}")
    
    analyzer.close()

if __name__ == "__main__":
    test_analyzer()
