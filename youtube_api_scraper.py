"""
YouTube API Scraper usando YouTube Data API v3
PROYECTO ACADÉMICO - Solo para fines educativos

Este módulo usa la API oficial de YouTube para extraer datos de forma legal y ética.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
import os
import re

logger = logging.getLogger(__name__)

# Intentar importar google-api-python-client
try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False
    logger.warning("⚠️ google-api-python-client no disponible. Instala con: pip install google-api-python-client")


class YouTubeAPIScraper:
    """
    Scraper de YouTube usando la API oficial (YouTube Data API v3)
    
    IMPORTANTE: Este código es solo para fines académicos y educativos.
    Respeta los términos de servicio de YouTube y las leyes locales.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializar el scraper de YouTube API
        
        Args:
            api_key: API Key de YouTube Data API v3 (obtener de https://console.cloud.google.com/)
        """
        if not YOUTUBE_API_AVAILABLE:
            raise ImportError("google-api-python-client no está instalado. Instala con: pip install google-api-python-client")
        
        # Obtener API key de variables de entorno si no se proporciona
        self.api_key = api_key or os.getenv('YOUTUBE_API_KEY') or os.getenv('GOOGLE_API_KEY')
        
        if not self.api_key:
            logger.warning("⚠️ API Key de YouTube no encontrada. Usa variable de entorno:")
            logger.warning("   YOUTUBE_API_KEY o GOOGLE_API_KEY")
            raise ValueError("Se requiere API Key de YouTube Data API v3")
        
        # Inicializar YouTube API
        try:
            self.youtube = build('youtube', 'v3', developerKey=self.api_key)
            logger.info("✅ YouTube API (v3) inicializado correctamente")
        except Exception as e:
            logger.error(f"❌ Error inicializando YouTube API: {e}")
            raise
    
    def _parse_duration(self, duration: str) -> str:
        """Parsear duración ISO 8601 a formato legible (ej: PT10M30S -> 10:30)"""
        try:
            if not duration:
                return "0:00"
            
            # Remover 'PT' del inicio
            duration = duration.replace('PT', '')
            
            hours = 0
            minutes = 0
            seconds = 0
            
            # Extraer horas
            if 'H' in duration:
                hours = int(duration.split('H')[0])
                duration = duration.split('H')[1]
            
            # Extraer minutos
            if 'M' in duration:
                minutes = int(duration.split('M')[0])
                duration = duration.split('M')[1]
            
            # Extraer segundos
            if 'S' in duration:
                seconds = int(duration.split('S')[0])
            
            # Formatear
            if hours > 0:
                return f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes}:{seconds:02d}"
        except:
            return "0:00"
    
    def _parse_views(self, views_str: str) -> int:
        """Parsear número de vistas (ej: '1.2M' -> 1200000)"""
        try:
            if not views_str:
                return 0
            
            # Si es un número, convertir directamente
            if isinstance(views_str, (int, float)):
                return int(views_str)
            
            views_str = str(views_str).strip().lower()
            
            # Remover caracteres no numéricos excepto k, m, b, .
            views_str = re.sub(r'[^\d.kmb]', '', views_str)
            
            if 'b' in views_str:
                number = float(views_str.replace('b', ''))
                return int(number * 1000000000)
            elif 'm' in views_str:
                number = float(views_str.replace('m', ''))
                return int(number * 1000000)
            elif 'k' in views_str:
                number = float(views_str.replace('k', ''))
                return int(number * 1000)
            else:
                return int(float(views_str))
        except:
            return 0
    
    def search_videos(self, query: str, max_results: int = 50, order: str = 'relevance') -> List[Dict]:
        """
        Buscar videos en YouTube
        
        Args:
            query: Término de búsqueda
            max_results: Número máximo de videos
            order: Orden ('relevance', 'date', 'rating', 'viewCount')
        
        Returns:
            Lista de diccionarios con datos de los videos
        """
        try:
            videos = []
            next_page_token = None
            max_pages = (max_results // 50) + 1  # YouTube permite máximo 50 por página
            
            for page in range(max_pages):
                # Buscar videos
                request = self.youtube.search().list(
                    part='snippet',
                    q=query,
                    maxResults=min(50, max_results - len(videos)),
                    type='video',
                    order=order,
                    pageToken=next_page_token
                )
                
                response = request.execute()
                
                if 'items' not in response or len(response['items']) == 0:
                    break
                
                # Obtener IDs de videos para obtener estadísticas
                video_ids = [item['id']['videoId'] for item in response['items']]
                
                # Obtener estadísticas y detalles adicionales
                stats_request = self.youtube.videos().list(
                    part='statistics,snippet,contentDetails',
                    id=','.join(video_ids)
                )
                stats_response = stats_request.execute()
                
                # Crear diccionario de estadísticas por video_id
                stats_dict = {}
                if 'items' in stats_response:
                    for stats_item in stats_response['items']:
                        stats_dict[stats_item['id']] = stats_item
                
                # Procesar videos
                for item in response['items']:
                    try:
                        video_id = item['id']['videoId']
                        snippet = item['snippet']
                        stats = stats_dict.get(video_id, {})
                        statistics = stats.get('statistics', {})
                        content_details = stats.get('contentDetails', {})
                        
                        # Extraer thumbnail (mejor calidad disponible)
                        thumbnails = snippet.get('thumbnails', {})
                        thumbnail_url = None
                        if 'high' in thumbnails:
                            thumbnail_url = thumbnails['high']['url']
                        elif 'medium' in thumbnails:
                            thumbnail_url = thumbnails['medium']['url']
                        elif 'default' in thumbnails:
                            thumbnail_url = thumbnails['default']['url']
                        
                        video_data = {
                            'id': video_id,
                            'platform': 'youtube',
                            'title': snippet.get('title', 'Sin título'),
                            'description': snippet.get('description', ''),
                            'channel': snippet.get('channelTitle', 'Unknown'),
                            'channel_id': snippet.get('channelId', ''),
                            'url': f"https://www.youtube.com/watch?v={video_id}",
                            'thumbnail': thumbnail_url,
                            'views': int(statistics.get('viewCount', 0)) if statistics.get('viewCount') else 0,
                            'likes': int(statistics.get('likeCount', 0)) if statistics.get('likeCount') else 0,
                            'comments': int(statistics.get('commentCount', 0)) if statistics.get('commentCount') else 0,
                            'duration': self._parse_duration(content_details.get('duration', '')),
                            'published_at': snippet.get('publishedAt', datetime.now().isoformat()),
                            'tags': snippet.get('tags', []),
                            'category_id': snippet.get('categoryId', ''),
                            'scraped_at': datetime.now().isoformat()
                        }
                        
                        videos.append(video_data)
                        logger.debug(f"✅ Video extraído: {video_data['title'][:50]}...")
                        
                        if len(videos) >= max_results:
                            break
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Error procesando video individual: {e}")
                        continue
                
                if len(videos) >= max_results:
                    break
                
                # Obtener token de siguiente página
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
            
            logger.info(f"✅ Extraídos {len(videos)} videos para búsqueda: '{query}'")
            return videos
            
        except HttpError as e:
            logger.error(f"❌ Error de API de YouTube: {e}")
            if e.resp.status == 403:
                logger.error("❌ Error 403: Revisa tu API Key o cuota de YouTube")
            return []
        except Exception as e:
            logger.error(f"❌ Error buscando videos: {e}")
            return []
    
    def get_channel_videos(self, channel_id: str, max_results: int = 50, order: str = 'date') -> List[Dict]:
        """
        Obtener videos de un canal específico
        
        Args:
            channel_id: ID del canal (ej: 'UCxxxxx') o username (ej: '@channelname')
            max_results: Número máximo de videos
            order: Orden ('date', 'rating', 'relevance', 'title', 'videoCount', 'viewCount')
        
        Returns:
            Lista de diccionarios con datos de los videos
        """
        try:
            original_identifier = channel_id
            channel_id = channel_id.strip()

            if channel_id.startswith('http'):
                lowered = channel_id.lower()
                if '/@' in lowered:
                    handle = lowered.split('/@', 1)[1].split('/', 1)[0].split('?', 1)[0]
                    channel_id = f'@{handle}'
                elif '/channel/' in lowered:
                    channel_id = lowered.split('/channel/', 1)[1].split('/', 1)[0].split('?', 1)[0]
                elif '/user/' in lowered:
                    channel_id = lowered.split('/user/', 1)[1].split('/', 1)[0].split('?', 1)[0]
                elif '/c/' in lowered:
                    channel_id = lowered.split('/c/', 1)[1].split('/', 1)[0].split('?', 1)[0]
                logger.info(f"ℹ️ Identificador de canal normalizado: '{original_identifier}' -> '{channel_id}'")

            # Si es username con @, extraer el ID del canal
            if channel_id.startswith('@'):
                # Buscar el canal por username
                search_request = self.youtube.search().list(
                    part='snippet',
                    q=channel_id,
                    type='channel',
                    maxResults=1
                )
                search_response = search_request.execute()
                
                if 'items' not in search_response or len(search_response['items']) == 0:
                    logger.error(f"❌ Canal no encontrado: {channel_id}")
                    return []
                
                channel_id = search_response['items'][0]['id']['channelId']
                logger.info(f"✅ Canal encontrado: {channel_id}")
            
            videos = []
            next_page_token = None
            max_pages = (max_results // 50) + 1
            
            for page in range(max_pages):
                # Buscar videos del canal
                request = self.youtube.search().list(
                    part='snippet',
                    channelId=channel_id,
                    maxResults=min(50, max_results - len(videos)),
                    order=order,
                    type='video',
                    pageToken=next_page_token
                )
                
                response = request.execute()
                
                if 'items' not in response or len(response['items']) == 0:
                    break
                
                # Obtener IDs de videos para estadísticas
                video_ids = [item['id']['videoId'] for item in response['items']]
                
                # Obtener estadísticas y detalles
                stats_request = self.youtube.videos().list(
                    part='statistics,snippet,contentDetails',
                    id=','.join(video_ids)
                )
                stats_response = stats_request.execute()
                
                # Crear diccionario de estadísticas
                stats_dict = {}
                if 'items' in stats_response:
                    for stats_item in stats_response['items']:
                        stats_dict[stats_item['id']] = stats_item
                
                # Procesar videos
                for item in response['items']:
                    try:
                        video_id = item['id']['videoId']
                        snippet = item['snippet']
                        stats = stats_dict.get(video_id, {})
                        statistics = stats.get('statistics', {})
                        content_details = stats.get('contentDetails', {})
                        
                        # Extraer thumbnail
                        thumbnails = snippet.get('thumbnails', {})
                        thumbnail_url = None
                        if 'high' in thumbnails:
                            thumbnail_url = thumbnails['high']['url']
                        elif 'medium' in thumbnails:
                            thumbnail_url = thumbnails['medium']['url']
                        elif 'default' in thumbnails:
                            thumbnail_url = thumbnails['default']['url']
                        
                        video_data = {
                            'id': video_id,
                            'platform': 'youtube',
                            'title': snippet.get('title', 'Sin título'),
                            'description': snippet.get('description', ''),
                            'channel': snippet.get('channelTitle', 'Unknown'),
                            'channel_id': snippet.get('channelId', ''),
                            'url': f"https://www.youtube.com/watch?v={video_id}",
                            'thumbnail': thumbnail_url,
                            'views': int(statistics.get('viewCount', 0)) if statistics.get('viewCount') else 0,
                            'likes': int(statistics.get('likeCount', 0)) if statistics.get('likeCount') else 0,
                            'comments': int(statistics.get('commentCount', 0)) if statistics.get('commentCount') else 0,
                            'duration': self._parse_duration(content_details.get('duration', '')),
                            'published_at': snippet.get('publishedAt', datetime.now().isoformat()),
                            'tags': snippet.get('tags', []),
                            'category_id': snippet.get('categoryId', ''),
                            'scraped_at': datetime.now().isoformat()
                        }
                        
                        videos.append(video_data)
                        
                        if len(videos) >= max_results:
                            break
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Error procesando video: {e}")
                        continue
                
                if len(videos) >= max_results:
                    break
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
            
            logger.info(f"✅ Extraídos {len(videos)} videos del canal: {channel_id}")
            return videos
            
        except HttpError as e:
            logger.error(f"❌ Error de API de YouTube: {e}")
            if e.resp.status == 403:
                logger.error("❌ Error 403: Revisa tu API Key o cuota de YouTube")
            return []
        except Exception as e:
            logger.error(f"❌ Error obteniendo videos del canal: {e}")
            return []
    
    def get_video_details(self, video_id: str) -> Optional[Dict]:
        """
        Obtener detalles completos de un video específico
        
        Args:
            video_id: ID del video (ej: 'dQw4w9WgXcQ')
        
        Returns:
            Diccionario con datos del video o None si hay error
        """
        try:
            request = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=video_id
            )
            response = request.execute()
            
            if 'items' not in response or len(response['items']) == 0:
                logger.warning(f"⚠️ Video no encontrado: {video_id}")
                return None
            
            item = response['items'][0]
            snippet = item['snippet']
            statistics = item['statistics']
            content_details = item['contentDetails']
            
            # Extraer thumbnail
            thumbnails = snippet.get('thumbnails', {})
            thumbnail_url = None
            if 'high' in thumbnails:
                thumbnail_url = thumbnails['high']['url']
            elif 'medium' in thumbnails:
                thumbnail_url = thumbnails['medium']['url']
            elif 'default' in thumbnails:
                thumbnail_url = thumbnails['default']['url']
            
            return {
                'id': video_id,
                'platform': 'youtube',
                'title': snippet.get('title', 'Sin título'),
                'description': snippet.get('description', ''),
                'channel': snippet.get('channelTitle', 'Unknown'),
                'channel_id': snippet.get('channelId', ''),
                'url': f"https://www.youtube.com/watch?v={video_id}",
                'thumbnail': thumbnail_url,
                'views': int(statistics.get('viewCount', 0)) if statistics.get('viewCount') else 0,
                'likes': int(statistics.get('likeCount', 0)) if statistics.get('likeCount') else 0,
                'comments': int(statistics.get('commentCount', 0)) if statistics.get('commentCount') else 0,
                'duration': self._parse_duration(content_details.get('duration', '')),
                'published_at': snippet.get('publishedAt', datetime.now().isoformat()),
                'tags': snippet.get('tags', []),
                'category_id': snippet.get('categoryId', ''),
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo detalles del video: {e}")
            return None

