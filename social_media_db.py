#!/usr/bin/env python3
"""
Gestor de Base de Datos para Redes Sociales
PROYECTO ACADÉMICO - Solo para fines educativos

Maneja la creación y gestión de tablas para almacenar datos de redes sociales.
"""

import sqlite3
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SocialMediaDB:
    """
    Gestor de base de datos para datos de redes sociales
    """
    
    def __init__(self, db_path: str = 'news_database.db'):
        """
        Inicializar conexión a base de datos
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Obtener conexión a la base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Acceso por nombre de columna
            return conn
        except Exception as e:
            logger.error(f"❌ Error conectando a la base de datos: {e}")
            return None
    
    def init_database(self):
        """Inicializar tabla de redes sociales si no existe"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Crear tabla de redes sociales
            create_table_query = """
                CREATE TABLE IF NOT EXISTS social_media_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    username TEXT NOT NULL,
                    text TEXT NOT NULL,
                    cleaned_text TEXT,
                    likes INTEGER DEFAULT 0,
                    retweets INTEGER DEFAULT 0,
                    replies INTEGER DEFAULT 0,
                    hashtags TEXT,
                    category TEXT,
                    sentiment TEXT,
                    detected_language TEXT,
                    url TEXT,
                    image_url TEXT,
                    video_url TEXT,
                    created_at TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP
                )
            """
            
            cursor.execute(create_table_query)
            
            # Crear índices para búsquedas rápidas
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_platform ON social_media_posts(platform)",
                "CREATE INDEX IF NOT EXISTS idx_category ON social_media_posts(category)",
                "CREATE INDEX IF NOT EXISTS idx_sentiment ON social_media_posts(sentiment)",
                "CREATE INDEX IF NOT EXISTS idx_scraped_at ON social_media_posts(scraped_at)",
                "CREATE INDEX IF NOT EXISTS idx_username ON social_media_posts(username)"
            ]
            
            for index_query in indexes:
                cursor.execute(index_query)
            
            conn.commit()
            logger.info("✅ Tabla de redes sociales inicializada correctamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando base de datos: {e}")
            return False
        finally:
            conn.close()
    
    def save_post(self, post: Dict) -> Optional[int]:
        """
        Guardar un post de red social
        
        Args:
            post: Diccionario con datos del post
        
        Returns:
            ID del post guardado o None si hay error
        """
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            
            # Convertir hashtags a string JSON
            hashtags_str = json.dumps(post.get('hashtags', [])) if post.get('hashtags') else None
            
            insert_query = """
                INSERT INTO social_media_posts (
                    platform, username, text, cleaned_text, likes, retweets, replies,
                    hashtags, category, sentiment, detected_language, url, image_url, video_url, created_at, processed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            values = (
                post.get('platform', 'twitter'),
                post.get('username', ''),
                post.get('text', ''),
                post.get('cleaned_text', ''),
                post.get('likes', 0),
                post.get('retweets', 0),
                post.get('replies', 0),
                hashtags_str,
                post.get('category', 'general'),
                post.get('sentiment', 'neutral'),
                post.get('detected_language', 'unknown'),
                post.get('url', ''),
                post.get('image_url', None),
                post.get('video_url', None),  # Agregar video_url
                post.get('date', ''),
                post.get('processed_at', None)
            )
            
            # Log antes de guardar para verificar image_url
            image_url_value = post.get('image_url')
            if image_url_value:
                logger.debug(f"💾 Guardando post con image_url: {image_url_value[:50]}...")
            
            cursor.execute(insert_query, values)
            conn.commit()
            
            post_id = cursor.lastrowid
            
            # Verificar que se guardó correctamente consultando la BD
            cursor.execute("SELECT image_url FROM social_media_posts WHERE id = ?", (post_id,))
            saved_image_url = cursor.fetchone()
            if saved_image_url:
                saved_url = saved_image_url[0] if isinstance(saved_image_url, tuple) else saved_image_url['image_url']
                if saved_url:
                    logger.debug(f"✅ Post {post_id} guardado con image_url en BD: {saved_url[:50]}...")
                else:
                    logger.warning(f"⚠️ Post {post_id} guardado pero image_url es NULL en BD")
            
            return post_id
            
        except Exception as e:
            logger.error(f"❌ Error guardando post: {e}")
            return None
        finally:
            conn.close()
    
    def save_batch(self, posts: List[Dict]) -> int:
        """
        Guardar múltiples posts
        
        Args:
            posts: Lista de posts a guardar
        
        Returns:
            Número de posts guardados exitosamente
        """
        if not posts:
            logger.warning("⚠️ No hay posts para guardar")
            return 0
        
        saved_count = 0
        errors = 0
        posts_with_images = 0
        
        for i, post in enumerate(posts):
            try:
                # Verificar image_url antes de guardar
                has_image = bool(post.get('image_url'))
                if has_image:
                    posts_with_images += 1
                    logger.debug(f"💾 Post {i+1}/{len(posts)} tiene image_url: {post.get('image_url')[:50]}...")
                
                post_id = self.save_post(post)
                if post_id:
                    saved_count += 1
                else:
                    errors += 1
                    logger.warning(f"⚠️ No se pudo guardar post: {post.get('text', '')[:50]}...")
            except Exception as e:
                errors += 1
                logger.error(f"❌ Error guardando post: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
        
        logger.info(f"💾 Guardados: {saved_count}, Errores: {errors}, Total procesados: {len(posts)}")
        logger.info(f"🖼️ Posts con imagen al guardar: {posts_with_images}/{len(posts)}")
        return saved_count
    
    def get_posts(self, 
                  platform: Optional[str] = None,
                  category: Optional[str] = None,
                  sentiment: Optional[str] = None,
                  language: Optional[str] = None,
                  start_date: Optional[str] = None,
                  end_date: Optional[str] = None,
                  min_interactions: Optional[int] = None,
                  top_metric: Optional[str] = None,
                  top_limit: Optional[int] = None,
                  limit: int = 100,
                  offset: int = 0) -> List[Dict]:
        """
        Obtener posts con filtros
        
        Args:
            platform: Filtrar por plataforma
            category: Filtrar por categoría
            sentiment: Filtrar por sentimiento
            language: Filtrar por idioma detectado
            start_date: Fecha mínima (formato YYYY-MM-DD)
            end_date: Fecha máxima (formato YYYY-MM-DD)
            min_interactions: Mínimo de interacciones (likes + retweets + replies)
            top_metric: Métrica para ordenar (likes, retweets, replies, engagement)
            top_limit: Límite de resultados cuando se usa top_metric
            limit: Límite de resultados
            offset: Offset para paginación
        
        Returns:
            Lista de posts
        """
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            # Construir query con filtros
            query = "SELECT *, COALESCE(NULLIF(created_at, ''), scraped_at) AS reference_date FROM social_media_posts WHERE 1=1"
            params = []
            
            if platform:
                query += " AND platform = ?"
                params.append(platform)
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            if sentiment:
                query += " AND sentiment = ?"
                params.append(sentiment)

            if language:
                query += " AND detected_language = ?"
                params.append(language)

            if start_date:
                query += " AND DATE(reference_date) >= DATE(?)"
                params.append(start_date)

            if end_date:
                query += " AND DATE(reference_date) <= DATE(?)"
                params.append(end_date)

            if isinstance(min_interactions, int):
                query += " AND (COALESCE(likes, 0) + COALESCE(retweets, 0) + COALESCE(replies, 0)) >= ?"
                params.append(min_interactions)

            allowed_metrics = {
                'likes': 'COALESCE(likes, 0)',
                'retweets': 'COALESCE(retweets, 0)',
                'replies': 'COALESCE(replies, 0)',
                'engagement': '(COALESCE(likes, 0) + COALESCE(retweets, 0) + COALESCE(replies, 0))'
            }

            order_clause = " ORDER BY reference_date DESC"
            if top_metric and top_metric in allowed_metrics:
                metric_expression = allowed_metrics[top_metric]
                order_clause = f" ORDER BY {metric_expression} DESC, reference_date DESC"

            effective_limit = top_limit if top_limit else limit
            if not effective_limit or effective_limit <= 0:
                effective_limit = limit
            
            query += f"{order_clause} LIMIT ? OFFSET ?"
            params.extend([effective_limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convertir rows a diccionarios (usando Row factory que ya está configurado)
            posts = []
            for row in rows:
                # Con row_factory = Row, podemos acceder directamente como dict
                # Usar row[key] en lugar de row.get() porque Row no tiene método .get()
                try:
                    post = {
                        'id': row['id'] if 'id' in row.keys() else None,
                        'platform': row['platform'] if 'platform' in row.keys() else 'twitter',
                        'username': row['username'] if 'username' in row.keys() else '',
                        'text': row['text'] if 'text' in row.keys() else '',
                        'cleaned_text': row['cleaned_text'] if 'cleaned_text' in row.keys() else '',
                        'likes': row['likes'] if 'likes' in row.keys() else 0,
                        'retweets': row['retweets'] if 'retweets' in row.keys() else 0,
                        'replies': row['replies'] if 'replies' in row.keys() else 0,
                        'category': row['category'] if 'category' in row.keys() else 'general',
                        'sentiment': row['sentiment'] if 'sentiment' in row.keys() else 'neutral',
                        'detected_language': row['detected_language'] if 'detected_language' in row.keys() else 'unknown',
                        'url': row['url'] if 'url' in row.keys() else '',
                        'image_url': row['image_url'] if 'image_url' in row.keys() else None,  # IMPORTANTE: puede ser None
                        'video_url': row['video_url'] if 'video_url' in row.keys() else None,  # Video URL (para Facebook)
                        'created_at': row['created_at'] if 'created_at' in row.keys() else '',
                        'scraped_at': row['scraped_at'] if 'scraped_at' in row.keys() else '',
                        'processed_at': row['processed_at'] if 'processed_at' in row.keys() else None
                    }
                except (KeyError, TypeError) as e:
                    # Si hay un error accediendo a las columnas, usar método alternativo
                    logger.warning(f"⚠️ Error accediendo a row: {e}, usando método alternativo")
                    post = dict(zip([col[0] for col in cursor.description], row))
                
                # Parsear hashtags de JSON
                hashtags_raw = post.get('hashtags') if 'hashtags' in post else None
                if not hashtags_raw and 'hashtags' in row.keys():
                    hashtags_raw = row['hashtags']
                if hashtags_raw:
                    try:
                        if isinstance(hashtags_raw, str):
                            post['hashtags'] = json.loads(hashtags_raw)
                        elif isinstance(hashtags_raw, list):
                            post['hashtags'] = hashtags_raw
                        else:
                            post['hashtags'] = []
                    except (json.JSONDecodeError, TypeError):
                        post['hashtags'] = []
                else:
                    post['hashtags'] = []
                
                # Log para debug - verificar image_url
                if post.get('image_url'):
                    logger.info(f"✅ Post {post.get('id')} tiene image_url: {post.get('image_url')[:50]}...")
                else:
                    logger.warning(f"⚠️ Post {post.get('id')} NO tiene image_url (null)")
                
                posts.append(post)
            
            return posts
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo posts: {e}")
            return []
        finally:
            conn.close()
    
    def get_stats(self) -> Dict:
        """
        Obtener estadísticas de los posts
        
        Returns:
            Diccionario con estadísticas
        """
        conn = self.get_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total de posts
            cursor.execute("SELECT COUNT(*) as total FROM social_media_posts")
            stats['total_posts'] = cursor.fetchone()['total']
            
            # Por plataforma
            cursor.execute("SELECT platform, COUNT(*) as count FROM social_media_posts GROUP BY platform")
            stats['by_platform'] = {row['platform']: row['count'] for row in cursor.fetchall()}
            
            # Por categoría
            cursor.execute("SELECT category, COUNT(*) as count FROM social_media_posts GROUP BY category")
            stats['by_category'] = {row['category']: row['count'] for row in cursor.fetchall()}
            
            # Por sentimiento
            cursor.execute("SELECT sentiment, COUNT(*) as count FROM social_media_posts GROUP BY sentiment")
            stats['by_sentiment'] = {row['sentiment']: row['count'] for row in cursor.fetchall()}
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {}
        finally:
            conn.close()

