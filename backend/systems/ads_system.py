"""
Sistema de Gestión de Anuncios con Integración de Análisis de Sentimientos
Permite colocar anuncios inteligentemente basándose en el sentimiento del contenido
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class AdsSystem:
    """Sistema de gestión de anuncios con análisis de sentimientos"""
    
    def __init__(self, db_path: str = "news_database.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializar tablas de base de datos para anuncios"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de campañas publicitarias
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ad_campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                advertiser_id INTEGER,
                advertiser_name TEXT,
                budget REAL DEFAULT 0.0,
                daily_budget REAL DEFAULT 0.0,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                status TEXT DEFAULT 'active', -- active, paused, completed, cancelled
                target_sentiments TEXT, -- JSON: ['positive', 'neutral'] o ['all']
                target_categories TEXT, -- JSON: ['Economía', 'Tecnología']
                target_newspapers TEXT, -- JSON: ['El Comercio', 'RPP']
                exclude_negative BOOLEAN DEFAULT 1, -- Evitar contenido muy negativo
                min_sentiment_score REAL DEFAULT -1.0, -- Score mínimo permitido
                max_sentiment_score REAL DEFAULT 1.0, -- Score máximo permitido
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de anuncios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                image_url TEXT,
                click_url TEXT NOT NULL,
                display_text TEXT,
                ad_type TEXT DEFAULT 'banner', -- banner, sidebar, inline, popup
                width INTEGER DEFAULT 300,
                height INTEGER DEFAULT 250,
                weight INTEGER DEFAULT 1, -- Peso para rotación
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (campaign_id) REFERENCES ad_campaigns (id)
            )
        ''')
        
        # Tabla de métricas de anuncios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ad_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ad_id INTEGER NOT NULL,
                campaign_id INTEGER NOT NULL,
                article_id INTEGER,
                article_sentiment TEXT, -- positive, negative, neutral
                article_sentiment_score REAL,
                article_category TEXT,
                article_newspaper TEXT,
                event_type TEXT NOT NULL, -- impression, click, conversion
                user_ip TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ad_id) REFERENCES ads (id),
                FOREIGN KEY (campaign_id) REFERENCES ad_campaigns (id)
            )
        ''')
        
        # Índices para mejor rendimiento
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ad_campaigns_status ON ad_campaigns(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ads_campaign ON ads(campaign_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ads_active ON ads(is_active, campaign_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ad_metrics_ad ON ad_metrics(ad_id, created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ad_metrics_sentiment ON ad_metrics(article_sentiment, created_at)')
        
        conn.commit()
        conn.close()
        logger.info("✅ Base de datos de anuncios inicializada")
    
    def create_campaign(self, campaign_data: Dict) -> int:
        """Crear nueva campaña publicitaria"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO ad_campaigns (
                    name, description, advertiser_id, advertiser_name,
                    budget, daily_budget, start_date, end_date, status,
                    target_sentiments, target_categories, target_newspapers,
                    exclude_negative, min_sentiment_score, max_sentiment_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                campaign_data.get('name'),
                campaign_data.get('description'),
                campaign_data.get('advertiser_id'),
                campaign_data.get('advertiser_name'),
                campaign_data.get('budget', 0.0),
                campaign_data.get('daily_budget', 0.0),
                campaign_data.get('start_date'),
                campaign_data.get('end_date'),
                campaign_data.get('status', 'active'),
                json.dumps(campaign_data.get('target_sentiments', ['all'])),
                json.dumps(campaign_data.get('target_categories', [])),
                json.dumps(campaign_data.get('target_newspapers', [])),
                campaign_data.get('exclude_negative', True),
                campaign_data.get('min_sentiment_score', -1.0),
                campaign_data.get('max_sentiment_score', 1.0)
            ))
            
            campaign_id = cursor.lastrowid
            conn.commit()
            logger.info(f"✅ Campaña creada: {campaign_data.get('name')} (ID: {campaign_id})")
            return campaign_id
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Error creando campaña: {e}")
            raise
        finally:
            conn.close()
    
    def create_ad(self, ad_data: Dict) -> int:
        """Crear nuevo anuncio"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO ads (
                    campaign_id, title, description, image_url, click_url,
                    display_text, ad_type, width, height, weight, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                ad_data.get('campaign_id'),
                ad_data.get('title'),
                ad_data.get('description'),
                ad_data.get('image_url'),
                ad_data.get('click_url'),
                ad_data.get('display_text'),
                ad_data.get('ad_type', 'banner'),
                ad_data.get('width', 300),
                ad_data.get('height', 250),
                ad_data.get('weight', 1),
                ad_data.get('is_active', True)
            ))
            
            ad_id = cursor.lastrowid
            conn.commit()
            logger.info(f"✅ Anuncio creado: {ad_data.get('title')} (ID: {ad_id})")
            return ad_id
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Error creando anuncio: {e}")
            raise
        finally:
            conn.close()
    
    def get_ad_for_article(self, article_id: int, article_sentiment: str, 
                          article_sentiment_score: float, article_category: str,
                          article_newspaper: str) -> Optional[Dict]:
        """
        Obtener anuncio apropiado para un artículo basándose en sentimiento y contexto
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Obtener todas las campañas activas
            cursor.execute('''
                SELECT id, name, target_sentiments, target_categories, target_newspapers,
                       exclude_negative, min_sentiment_score, max_sentiment_score
                FROM ad_campaigns
                WHERE status = 'active'
                  AND (start_date IS NULL OR start_date <= datetime('now'))
                  AND (end_date IS NULL OR end_date >= datetime('now'))
            ''')
            
            campaigns = cursor.fetchall()
            matching_campaigns = []
            
            for camp in campaigns:
                camp_id, name, target_sentiments_json, target_categories_json, 
                target_newspapers_json, exclude_negative, min_score, max_score = camp
                
                # Verificar sentimiento
                target_sentiments = json.loads(target_sentiments_json) if target_sentiments_json else ['all']
                if 'all' not in target_sentiments and article_sentiment not in target_sentiments:
                    continue
                
                # Verificar score de sentimiento
                if article_sentiment_score < min_score or article_sentiment_score > max_score:
                    continue
                
                # Excluir contenido muy negativo si está configurado
                if exclude_negative and article_sentiment == 'negative' and article_sentiment_score < -0.3:
                    continue
                
                # Verificar categoría
                target_categories = json.loads(target_categories_json) if target_categories_json else []
                if target_categories and article_category not in target_categories:
                    continue
                
                # Verificar periódico
                target_newspapers = json.loads(target_newspapers_json) if target_newspapers_json else []
                if target_newspapers and article_newspaper not in target_newspapers:
                    continue
                
                matching_campaigns.append(camp_id)
            
            if not matching_campaigns:
                return None
            
            # Obtener anuncios de las campañas que coinciden
            placeholders = ','.join(['?'] * len(matching_campaigns))
            cursor.execute(f'''
                SELECT id, campaign_id, title, description, image_url, click_url,
                       display_text, ad_type, width, height
                FROM ads
                WHERE campaign_id IN ({placeholders})
                  AND is_active = 1
                ORDER BY weight DESC, RANDOM()
                LIMIT 1
            ''', matching_campaigns)
            
            ad = cursor.fetchone()
            if not ad:
                return None
            
            ad_id, campaign_id, title, description, image_url, click_url, \
            display_text, ad_type, width, height = ad
            
            return {
                'id': ad_id,
                'campaign_id': campaign_id,
                'title': title,
                'description': description,
                'image_url': image_url,
                'click_url': click_url,
                'display_text': display_text,
                'ad_type': ad_type,
                'width': width,
                'height': height
            }
        except Exception as e:
            logger.error(f"❌ Error obteniendo anuncio: {e}")
            return None
        finally:
            conn.close()
    
    def track_event(self, ad_id: int, campaign_id: int, event_type: str,
                   article_id: Optional[int] = None, article_sentiment: Optional[str] = None,
                   article_sentiment_score: Optional[float] = None,
                   article_category: Optional[str] = None,
                   article_newspaper: Optional[str] = None,
                   user_ip: Optional[str] = None,
                   user_agent: Optional[str] = None):
        """Registrar evento de anuncio (impresión, click, conversión)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO ad_metrics (
                    ad_id, campaign_id, article_id, article_sentiment,
                    article_sentiment_score, article_category, article_newspaper,
                    event_type, user_ip, user_agent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                ad_id, campaign_id, article_id, article_sentiment,
                article_sentiment_score, article_category, article_newspaper,
                event_type, user_ip, user_agent
            ))
            
            conn.commit()
        except Exception as e:
            logger.error(f"❌ Error registrando evento: {e}")
        finally:
            conn.close()
    
    def get_analytics(self, campaign_id: Optional[int] = None, 
                     days: int = 30) -> Dict:
        """Obtener métricas de anuncios"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            where_clause = "WHERE created_at >= datetime('now', '-' || ? || ' days')"
            params = [days]
            
            if campaign_id:
                where_clause += " AND campaign_id = ?"
                params.append(campaign_id)
            
            # Impresiones y clicks por sentimiento
            cursor.execute(f'''
                SELECT 
                    article_sentiment,
                    SUM(CASE WHEN event_type = 'impression' THEN 1 ELSE 0 END) as impressions,
                    SUM(CASE WHEN event_type = 'click' THEN 1 ELSE 0 END) as clicks,
                    SUM(CASE WHEN event_type = 'conversion' THEN 1 ELSE 0 END) as conversions
                FROM ad_metrics
                {where_clause}
                GROUP BY article_sentiment
            ''', params)
            
            by_sentiment = {}
            for row in cursor.fetchall():
                sentiment, impressions, clicks, conversions = row
                if sentiment:
                    by_sentiment[sentiment] = {
                        'impressions': impressions or 0,
                        'clicks': clicks or 0,
                        'conversions': conversions or 0,
                        'ctr': round((clicks or 0) / (impressions or 1) * 100, 2) if impressions else 0
                    }
            
            # Totales
            cursor.execute(f'''
                SELECT 
                    SUM(CASE WHEN event_type = 'impression' THEN 1 ELSE 0 END) as total_impressions,
                    SUM(CASE WHEN event_type = 'click' THEN 1 ELSE 0 END) as total_clicks,
                    SUM(CASE WHEN event_type = 'conversion' THEN 1 ELSE 0 END) as total_conversions
                FROM ad_metrics
                {where_clause}
            ''', params)
            
            totals = cursor.fetchone()
            total_impressions, total_clicks, total_conversions = totals or (0, 0, 0)
            
            return {
                'by_sentiment': by_sentiment,
                'totals': {
                    'impressions': total_impressions or 0,
                    'clicks': total_clicks or 0,
                    'conversions': total_conversions or 0,
                    'ctr': round((total_clicks or 0) / (total_impressions or 1) * 100, 2) if total_impressions else 0
                },
                'period_days': days
            }
        except Exception as e:
            logger.error(f"❌ Error obteniendo analytics: {e}")
            return {'by_sentiment': {}, 'totals': {'impressions': 0, 'clicks': 0, 'conversions': 0, 'ctr': 0}, 'period_days': days}
        finally:
            conn.close()
    
    def get_campaigns(self, status: Optional[str] = None) -> List[Dict]:
        """Obtener lista de campañas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = 'SELECT * FROM ad_campaigns'
            params = []
            
            if status:
                query += ' WHERE status = ?'
                params.append(status)
            
            query += ' ORDER BY created_at DESC'
            
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            
            campaigns = []
            for row in cursor.fetchall():
                campaign = dict(zip(columns, row))
                # Parsear JSON fields
                campaign['target_sentiments'] = json.loads(campaign.get('target_sentiments', '["all"]'))
                campaign['target_categories'] = json.loads(campaign.get('target_categories', '[]'))
                campaign['target_newspapers'] = json.loads(campaign.get('target_newspapers', '[]'))
                campaigns.append(campaign)
            
            return campaigns
        except Exception as e:
            logger.error(f"❌ Error obteniendo campañas: {e}")
            return []
        finally:
            conn.close()


# Instancia global
ads_system = AdsSystem()


