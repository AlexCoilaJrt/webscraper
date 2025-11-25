#!/usr/bin/env python3
"""
SCRAPER DE FACEBOOK - MÉTODO OFICIAL CON GRAPH API

Este método usa la API oficial de Facebook (más confiable y legal)

IMPORTANTE: Este código es solo para fines académicos y educativos.
Respeta los términos de servicio de Facebook y las leyes locales.
"""

import requests
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FacebookGraphScraper:
    """
    Scraper de Facebook usando Graph API oficial
    """
    
    def __init__(self, access_token: Optional[str] = None):
        """
        Inicializar el scraper de Facebook Graph API
        
        Args:
            access_token: Token de acceso de Facebook (opcional, puede estar en env)
        """
        self.access_token = access_token or self._get_access_token_from_env()
        self.base_url = "https://graph.facebook.com/v18.0"
        
        if not self.access_token:
            logger.warning("⚠️ No se proporcionó Access Token. El scraping puede fallar.")
            logger.info("💡 Para obtener un token: https://developers.facebook.com/apps/")
    
    def _get_access_token_from_env(self) -> Optional[str]:
        """Obtener access token de variables de entorno"""
        import os
        return os.getenv('FACEBOOK_ACCESS_TOKEN') or os.getenv('FB_ACCESS_TOKEN')
    
    def get_page_id(self, page_username: str) -> Optional[Dict]:
        """
        Obtiene el ID de la página desde su username
        
        Args:
            page_username: Nombre de usuario de la página (ej: 'elcomercio.pe')
        
        Returns:
            Diccionario con información de la página o None si hay error
        """
        if not self.access_token:
            logger.error("❌ No hay Access Token configurado")
            return None
        
        # Limpiar el username (remover https://, facebook.com, etc.)
        page_username = page_username.replace('https://', '').replace('http://', '')
        page_username = page_username.replace('www.facebook.com/', '').replace('facebook.com/', '')
        page_username = page_username.replace('fb.com/', '').replace('m.facebook.com/', '')
        page_username = page_username.strip('/')
        
        url = f"{self.base_url}/{page_username}"
        params = {
            'fields': 'id,name,followers_count,username',
            'access_token': self.access_token
        }
        
        try:
            logger.info(f"🔍 Obteniendo información de la página: {page_username}")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            page_data = response.json()
            
            logger.info(f"✅ Página encontrada: {page_data.get('name')} (ID: {page_data.get('id')})")
            return page_data
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error("❌ Access Token inválido o expirado")
                logger.error("💡 Obtén un nuevo token en: https://developers.facebook.com/tools/explorer/")
            elif e.response.status_code == 404:
                logger.error(f"❌ Página no encontrada: {page_username}")
                logger.error("💡 Verifica que el nombre de usuario sea correcto")
            else:
                logger.error(f"❌ Error HTTP obteniendo página: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error obteniendo página: {e}")
            return None
    
    def get_posts(self, page_id: str, limit: int = 100) -> List[Dict]:
        """
        Extrae posts de una página de Facebook
        
        Args:
            page_id: ID de la página de Facebook
            limit: Número máximo de posts a extraer
        
        Returns:
            Lista de diccionarios con datos de posts
        """
        if not self.access_token:
            logger.error("❌ No hay Access Token configurado")
            return []
        
        url = f"{self.base_url}/{page_id}/posts"
        
        params = {
            'fields': 'id,message,created_time,full_picture,permalink_url,shares,reactions.summary(true),comments.summary(true)',
            'limit': min(limit, 100),  # Facebook limita a 100 por request
            'access_token': self.access_token
        }
        
        all_posts = []
        
        try:
            logger.info(f"📥 Extrayendo hasta {limit} posts de la página {page_id}...")
            
            while len(all_posts) < limit:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if 'data' not in data or len(data['data']) == 0:
                    logger.info("ℹ️ No hay más posts disponibles")
                    break
                
                for post in data['data']:
                    if len(all_posts) >= limit:
                        break
                    processed_post = self.process_post(post)
                    all_posts.append(processed_post)
                    logger.debug(f"✅ Post extraído: {processed_post.get('id')}")
                
                logger.info(f"📊 Extraídos {len(all_posts)}/{limit} posts...")
                
                # Paginación
                if 'paging' in data and 'next' in data['paging']:
                    url = data['paging']['next']
                    params = {}  # Los parámetros ya están en la URL next
                else:
                    break
            
            logger.info(f"✅ Total de posts extraídos: {len(all_posts)}")
            return all_posts
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error("❌ Access Token inválido o expirado")
            elif e.response.status_code == 403:
                logger.error("❌ No tienes permisos para acceder a esta página")
                logger.error("💡 Necesitas permisos: pages_read_engagement, pages_show_list")
            else:
                logger.error(f"❌ Error HTTP extrayendo posts: {e}")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error extrayendo posts: {e}")
            return []
    
    def process_post(self, post: Dict) -> Dict:
        """
        Procesa y estructura los datos del post en el formato esperado
        
        Args:
            post: Diccionario con datos del post de Facebook Graph API
        
        Returns:
            Diccionario con datos procesados en formato estándar
        """
        # Extraer métricas
        reactions = post.get('reactions', {})
        reactions_summary = reactions.get('summary', {})
        likes = reactions_summary.get('total_count', 0)
        
        comments_data = post.get('comments', {})
        comments_summary = comments_data.get('summary', {})
        comments = comments_summary.get('total_count', 0)
        
        shares_data = post.get('shares', {})
        shares = shares_data.get('count', 0)
        
        # Extraer texto
        message = post.get('message', 'Sin texto')
        
        return {
            'id': post.get('id', ''),
            'platform': 'facebook',
            'username': 'Página de Facebook',  # Se puede mejorar extrayendo el nombre de la página
            'text': message,
            'cleaned_text': message.strip(),
            'image_url': post.get('full_picture', None),
            'video_url': None,  # Los videos requieren campo adicional
            'url': post.get('permalink_url', ''),
            'date': post.get('created_time', datetime.now().isoformat()),
            'created_at': post.get('created_time', datetime.now().isoformat()),
            'likes': likes,
            'comments': comments,
            'shares': shares,
            'retweets': 0,  # Facebook no tiene retweets
            'replies': comments,  # Usar comments como replies
            'hashtags': self._extract_hashtags(message),
            'category': self.categorize_post(message),
            'sentiment': 'neutral',  # Se procesará después
            'detected_language': 'unknown',  # Se detectará después
            'scraped_at': datetime.now().isoformat()
        }
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extraer hashtags del texto"""
        import re
        hashtags = re.findall(r'#\w+', text)
        return hashtags
    
    def categorize_post(self, text: str) -> str:
        """
        Categoriza el post por palabras clave
        
        Args:
            text: Texto del post
        
        Returns:
            Categoría del post
        """
        if not text:
            return 'general'
        
        text_lower = text.lower()
        
        categorias = {
            'tecnología': ['tecnología', 'tech', 'digital', 'software', 'app', 'internet', 'cibernético', 'innovación'],
            'negocios': ['negocio', 'empresa', 'comercio', 'mercado', 'economía', 'venta', 'finanzas', 'empresarial'],
            'deportes': ['deporte', 'fútbol', 'campeonato', 'equipo', 'partido', 'atleta', 'competencia'],
            'política': ['política', 'gobierno', 'elección', 'presidente', 'congreso', 'democracia', 'elección'],
            'entretenimiento': ['música', 'cine', 'película', 'artista', 'show', 'concierto', 'espectáculo'],
            'salud': ['salud', 'médico', 'hospital', 'enfermedad', 'tratamiento', 'cuidado'],
            'educación': ['educación', 'escuela', 'universidad', 'estudiante', 'aprendizaje', 'académico']
        }
        
        for categoria, palabras in categorias.items():
            if any(palabra in text_lower for palabra in palabras):
                return categoria
        
        return 'general'
    
    def scrape_from_url(self, url: str, max_posts: int = 50) -> List[Dict]:
        """
        Scraping desde una URL de Facebook usando Graph API
        
        Args:
            url: URL de Facebook (página, perfil, post)
            max_posts: Máximo de posts a extraer
        
        Returns:
            Lista de diccionarios con datos de posts
        """
        if not self.access_token:
            logger.error("❌ No hay Access Token configurado para Graph API")
            logger.error("💡 Configura el token en variables de entorno o pasa el parámetro")
            return []
        
        # Extraer username de la URL
        page_username = url.replace('https://', '').replace('http://', '')
        page_username = page_username.replace('www.facebook.com/', '').replace('facebook.com/', '')
        page_username = page_username.replace('fb.com/', '').replace('m.facebook.com/', '')
        page_username = page_username.strip('/')
        
        # Si la URL tiene /posts/ o /photos/, extraer el username de antes
        if '/' in page_username:
            page_username = page_username.split('/')[0]
        
        logger.info(f"🔍 Scrapeando Facebook con Graph API: {page_username}")
        
        # Obtener información de la página
        page_info = self.get_page_id(page_username)
        
        if not page_info:
            logger.error("❌ No se pudo obtener la información de la página")
            return []
        
        # Extraer posts
        page_id = page_info['id']
        posts = self.get_posts(page_id, limit=max_posts)
        
        if posts:
            logger.info(f"✅ ✅ ✅ GRAPH API EXITOSO: {len(posts)} posts REALES extraídos")
            return posts
        else:
            logger.warning("⚠️ No se pudieron extraer posts")
            return []


# ====================== FUNCIÓN DE CONVENIENCIA ======================

def create_graph_scraper(access_token: Optional[str] = None) -> Optional[FacebookGraphScraper]:
    """
    Crear instancia del scraper Graph API
    
    Args:
        access_token: Token de acceso (opcional, se puede obtener de env)
    
    Returns:
        Instancia del scraper o None si no hay token
    """
    scraper = FacebookGraphScraper(access_token)
    
    if not scraper.access_token:
        logger.warning("⚠️ No se proporcionó Access Token")
        logger.info("💡 Para usar Graph API:")
        logger.info("   1. Obtén un token en: https://developers.facebook.com/tools/explorer/")
        logger.info("   2. Configura FACEBOOK_ACCESS_TOKEN en variables de entorno")
        logger.info("   3. O pasa el token al crear el scraper")
        return None
    
    return scraper















