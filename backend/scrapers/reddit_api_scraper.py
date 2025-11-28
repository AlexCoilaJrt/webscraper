"""
Reddit API Scraper usando PRAW (Python Reddit API Wrapper)
PROYECTO ACADÉMICO - Solo para fines educativos

Este módulo usa la API oficial de Reddit para extraer datos de forma legal y ética.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)

# Intentar importar PRAW
try:
    import praw
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False
    logger.warning("⚠️ PRAW no disponible. Instala con: pip install praw")


class RedditAPIScraper:
    """
    Scraper de Reddit usando la API oficial (PRAW)
    
    IMPORTANTE: Este código es solo para fines académicos y educativos.
    Respeta los términos de servicio de Reddit y las leyes locales.
    """
    
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None, user_agent: Optional[str] = None):
        """
        Inicializar el scraper de Reddit API
        
        Args:
            client_id: Client ID de Reddit (obtener de https://www.reddit.com/prefs/apps)
            client_secret: Client Secret de Reddit
            user_agent: User agent personalizado (ej: "MyApp/1.0 by MyUsername")
        """
        if not PRAW_AVAILABLE:
            raise ImportError("PRAW no está instalado. Instala con: pip install praw")
        
        # Obtener credenciales de variables de entorno si no se proporcionan
        self.client_id = client_id or os.getenv('REDDIT_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('REDDIT_CLIENT_SECRET')
        self.user_agent = user_agent or os.getenv('REDDIT_USER_AGENT') or 'AcademicScraper/1.0 by AcademicUser'
        
        if not self.client_id or not self.client_secret:
            logger.warning("⚠️ Credenciales de Reddit no encontradas. Usa variables de entorno:")
            logger.warning("   REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT")
            raise ValueError("Se requieren client_id y client_secret de Reddit")
        
        # Inicializar PRAW
        try:
            self.reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
            )
            logger.info("✅ Reddit API (PRAW) inicializado correctamente")
        except Exception as e:
            logger.error(f"❌ Error inicializando Reddit API: {e}")
            raise
    
    def get_subreddit_posts(self, subreddit_name: str, limit: int = 100, sort: str = 'hot') -> List[Dict]:
        """
        Obtener posts de un subreddit
        
        Args:
            subreddit_name: Nombre del subreddit (ej: 'python', 'technology')
            limit: Número máximo de posts a extraer
            sort: Orden de posts ('hot', 'new', 'top', 'rising')
        
        Returns:
            Lista de diccionarios con datos de los posts
        """
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Obtener posts según el orden especificado
            if sort == 'hot':
                posts_generator = subreddit.hot(limit=limit)
            elif sort == 'new':
                posts_generator = subreddit.new(limit=limit)
            elif sort == 'top':
                posts_generator = subreddit.top(limit=limit, time_filter='all')
            elif sort == 'rising':
                posts_generator = subreddit.rising(limit=limit)
            else:
                posts_generator = subreddit.hot(limit=limit)
            
            results = []
            for post in posts_generator:
                try:
                    # Extraer autor (username) - MEJORADO
                    author = 'Unknown'
                    if post.author:
                        try:
                            author = str(post.author.name) if hasattr(post.author, 'name') else str(post.author)
                        except:
                            author = str(post.author) if post.author else 'Unknown'
                    
                    # Extraer título del post (siempre existe)
                    title = post.title if hasattr(post, 'title') and post.title else ''
                    
                    # Extraer contenido del post (selftext) - solo si existe
                    content = ''
                    if hasattr(post, 'selftext') and post.selftext:
                        content = post.selftext
                    # Si no hay contenido, usar título como contenido
                    if not content:
                        content = title
                    
                    # NO usar título como contenido si ya hay selftext
                    # El título ya está en el campo 'title'
                    
                    # Extraer imagen si existe - MEJORADO
                    image_url = None
                    if post.url:
                        # Verificar si es una imagen directa
                        if post.url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.gifv')):
                            image_url = post.url
                        # Verificar si es un post de imagen de Reddit
                        elif 'redd.it' in post.url or 'i.redd.it' in post.url:
                            image_url = post.url
                        # Verificar si tiene preview de imagen (mejor calidad)
                        elif hasattr(post, 'preview') and post.preview:
                            try:
                                images = post.preview.get('images', [])
                                if images and len(images) > 0:
                                    # Intentar obtener la imagen de mayor resolución
                                    source = images[0].get('source', {})
                                    if source and source.get('url'):
                                        image_url = source['url']
                                    # Fallback a variants si existe
                                    elif 'variants' in images[0]:
                                        variants = images[0]['variants']
                                        if variants:
                                            # Buscar la mejor variante
                                            for variant_name, variant_data in variants.items():
                                                if variant_data and 'source' in variant_data:
                                                    image_url = variant_data['source'].get('url')
                                                    if image_url:
                                                        break
                            except Exception as e:
                                logger.debug(f"⚠️ Error extrayendo preview de imagen: {e}")
                                pass
                    
                    # Extraer métricas - MEJORADO
                    score = post.score if hasattr(post, 'score') else 0
                    upvotes = post.ups if hasattr(post, 'ups') else score
                    downvotes = post.downs if hasattr(post, 'downs') else 0
                    num_comments = post.num_comments if hasattr(post, 'num_comments') else 0
                    
                    # Extraer subreddit - asegurar que no se duplique
                    subreddit = subreddit_name
                    if hasattr(post, 'subreddit'):
                        try:
                            subreddit_obj = post.subreddit
                            if hasattr(subreddit_obj, 'display_name'):
                                subreddit = subreddit_obj.display_name
                            else:
                                subreddit = str(subreddit_obj)
                        except:
                            subreddit = subreddit_name
                    
                    post_data = {
                        'id': post.id,
                        'platform': 'reddit',
                        'title': title,  # Título del post
                        'content': content,  # Contenido del post (selftext o título)
                        'author': author,  # Username del autor
                        'subreddit': subreddit,  # Nombre del subreddit (sin duplicar)
                        'score': score,
                        'upvotes': upvotes,
                        'downvotes': downvotes,
                        'comments': num_comments,
                        'url': post.url if hasattr(post, 'url') else '',
                        'permalink': f"https://reddit.com{post.permalink}" if hasattr(post, 'permalink') else '',
                        'created_at': datetime.fromtimestamp(post.created_utc).isoformat() if hasattr(post, 'created_utc') else datetime.now().isoformat(),
                        'flair': post.link_flair_text if hasattr(post, 'link_flair_text') else None,
                        'image_url': image_url,
                        'is_video': post.is_video if hasattr(post, 'is_video') else False,
                        'is_self': post.is_self if hasattr(post, 'is_self') else False,
                        'scraped_at': datetime.now().isoformat()
                    }
                    
                    results.append(post_data)
                    logger.debug(f"✅ Post extraído: {post.title[:50]}...")
                    
                    if len(results) >= limit:
                        break
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error extrayendo post individual: {e}")
                    continue
            
            logger.info(f"✅ Extraídos {len(results)} posts de r/{subreddit_name}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo posts de r/{subreddit_name}: {e}")
            return []
    
    def search_posts(self, query: str, subreddit: Optional[str] = None, limit: int = 100, sort: str = 'relevance') -> List[Dict]:
        """
        Buscar posts en Reddit
        
        Args:
            query: Término de búsqueda
            subreddit: Subreddit específico (opcional, busca en todo Reddit si es None)
            limit: Número máximo de posts
            sort: Orden ('relevance', 'hot', 'top', 'new', 'comments')
        
        Returns:
            Lista de diccionarios con datos de los posts
        """
        try:
            results = []
            
            if subreddit:
                # Buscar en subreddit específico
                subreddit_obj = self.reddit.subreddit(subreddit)
                posts = subreddit_obj.search(query, limit=limit, sort=sort)
            else:
                # Buscar en todo Reddit
                posts = self.reddit.subreddit('all').search(query, limit=limit, sort=sort)
            
            for post in posts:
                try:
                    # Extraer imagen si existe
                    image_url = None
                    if post.url:
                        if post.url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                            image_url = post.url
                        elif 'redd.it' in post.url or 'i.redd.it' in post.url:
                            image_url = post.url
                    
                    content = post.selftext if hasattr(post, 'selftext') else ''
                    if not content and post.title:
                        content = post.title
                    
                    post_data = {
                        'id': post.id,
                        'platform': 'reddit',
                        'title': post.title,
                        'content': content,
                        'author': str(post.author) if post.author else 'Unknown',
                        'subreddit': subreddit or 'all',
                        'score': post.score,
                        'upvotes': post.ups if hasattr(post, 'ups') else post.score,
                        'downvotes': post.downs if hasattr(post, 'downs') else 0,
                        'comments': post.num_comments,
                        'url': post.url,
                        'permalink': f"https://reddit.com{post.permalink}",
                        'created_at': datetime.fromtimestamp(post.created_utc).isoformat() if hasattr(post, 'created_utc') else datetime.now().isoformat(),
                        'flair': post.link_flair_text if hasattr(post, 'link_flair_text') else None,
                        'image_url': image_url,
                        'scraped_at': datetime.now().isoformat()
                    }
                    
                    results.append(post_data)
                    
                    if len(results) >= limit:
                        break
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error en post de búsqueda: {e}")
                    continue
            
            logger.info(f"✅ Encontrados {len(results)} posts para búsqueda: '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error buscando posts: {e}")
            return []

