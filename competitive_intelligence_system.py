import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import re

class CompetitiveIntelligenceSystem:
    def __init__(self, db_path: str = "competitive_intelligence.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializar base de datos para competitive intelligence"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de competidores por usuario
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_competitors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                competitor_name TEXT NOT NULL,
                competitor_keywords TEXT NOT NULL, -- JSON array de palabras clave
                competitor_domains TEXT, -- JSON array de dominios a monitorear
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Tabla de menciones de competidores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS competitor_mentions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competitor_id INTEGER NOT NULL,
                article_id INTEGER,
                mention_text TEXT NOT NULL,
                sentiment_score REAL, -- -1 (negativo) a 1 (positivo)
                sentiment_label TEXT, -- 'positive', 'negative', 'neutral'
                source_url TEXT,
                source_domain TEXT,
                mention_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                relevance_score REAL DEFAULT 0.0, -- 0-1, qué tan relevante es la mención
                FOREIGN KEY (competitor_id) REFERENCES user_competitors (id),
                FOREIGN KEY (article_id) REFERENCES articles (id)
            )
        ''')
        
        # Tabla de análisis competitivo
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS competitor_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competitor_id INTEGER NOT NULL,
                analysis_date DATE NOT NULL,
                total_mentions INTEGER DEFAULT 0,
                positive_mentions INTEGER DEFAULT 0,
                negative_mentions INTEGER DEFAULT 0,
                neutral_mentions INTEGER DEFAULT 0,
                avg_sentiment_score REAL DEFAULT 0.0,
                top_keywords TEXT, -- JSON array
                trending_topics TEXT, -- JSON array
                competitor_rank INTEGER, -- Ranking vs otros competidores
                market_share_estimate REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (competitor_id) REFERENCES user_competitors (id)
            )
        ''')
        
        # Tabla de alertas competitivas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS competitor_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                competitor_id INTEGER NOT NULL,
                alert_type TEXT NOT NULL, -- 'mention_spike', 'negative_sentiment', 'new_topic'
                alert_message TEXT NOT NULL,
                alert_data TEXT, -- JSON con datos adicionales
                is_read BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (competitor_id) REFERENCES user_competitors (id)
            )
        ''')
        
        # Tabla de reportes automáticos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS competitor_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                report_type TEXT NOT NULL, -- 'weekly', 'monthly', 'custom'
                report_data TEXT NOT NULL, -- JSON con datos del reporte
                report_date DATE NOT NULL,
                is_sent BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Base de datos de Competitive Intelligence creada correctamente")
    
    def analyze_existing_articles(self, user_id: int = None) -> Dict:
        """Analizar todos los artículos existentes para encontrar menciones de competidores"""
        print("🔍 Iniciando análisis de artículos existentes...")
        
        # Conectar a ambas bases de datos
        ci_conn = sqlite3.connect(self.db_path)
        news_conn = sqlite3.connect("news_database.db")
        
        ci_cursor = ci_conn.cursor()
        news_cursor = news_conn.cursor()
        
        # Obtener competidores (de todos los usuarios o de un usuario específico)
        if user_id:
            ci_cursor.execute('''
                SELECT id, user_id, competitor_name, competitor_keywords, competitor_domains
                FROM user_competitors 
                WHERE is_active = 1 AND user_id = ?
            ''', (user_id,))
        else:
            ci_cursor.execute('''
                SELECT id, user_id, competitor_name, competitor_keywords, competitor_domains
                FROM user_competitors 
                WHERE is_active = 1
            ''')
        
        competitors = ci_cursor.fetchall()
        print(f"📊 Analizando {len(competitors)} competidores...")
        
        total_mentions = 0
        
        for competitor_id, comp_user_id, name, keywords_json, domains_json in competitors:
            try:
                keywords = json.loads(keywords_json) if keywords_json else []
                domains = json.loads(domains_json) if domains_json else []
                
                print(f"🏢 Analizando competidor: {name}")
                print(f"   Keywords: {keywords}")
                print(f"   Domains: {domains}")
                
                # Obtener artículos que coincidan con los dominios
                if domains:
                    domain_conditions = " OR ".join([f"url LIKE '%{domain}%'" for domain in domains])
                    query = f'''
                        SELECT id, title, content, url, newspaper
                        FROM articles 
                        WHERE ({domain_conditions})
                    '''
                else:
                    # Si no hay dominios específicos, analizar todos los artículos (limitado a últimos 10000 para mejor rendimiento)
                    query = '''
                        SELECT id, title, content, url, newspaper
                        FROM articles
                        ORDER BY id DESC
                        LIMIT 10000
                    '''
                
                news_cursor.execute(query)
                articles = news_cursor.fetchall()
                print(f"   📰 Analizando {len(articles)} artículos...")
                
                mentions_found = 0
                
                for article_id, title, content, url, newspaper in articles:
                    article_text = f"{title} {content}".lower()
                    
                    # Buscar cada palabra clave en el artículo (búsqueda más flexible)
                    for keyword in keywords:
                        keyword_lower = keyword.lower().strip()
                        if keyword_lower and keyword_lower in article_text:
                            # Verificar si ya existe esta mención para evitar duplicados
                            ci_cursor.execute('''
                                SELECT COUNT(*) FROM competitor_mentions 
                                WHERE competitor_id = ? AND article_id = ? AND mention_text LIKE ?
                            ''', (competitor_id, article_id, f'%{keyword}%'))
                            
                            if ci_cursor.fetchone()[0] > 0:
                                continue  # Ya existe, saltar
                            
                            # Calcular relevancia (simple: 1.0 si está en título, 0.5 si solo en contenido)
                            relevance = 1.0 if keyword_lower in title.lower() else 0.5
                            
                            # Análisis de sentimiento simple
                            sentiment_score = self._calculate_simple_sentiment(article_text, keyword)
                            sentiment_label = self._get_sentiment_label(sentiment_score)
                            
                            # Extraer dominio de la URL
                            source_domain = self._extract_domain(url)
                            
                            # Guardar mención
                            ci_cursor.execute('''
                                INSERT INTO competitor_mentions 
                                (competitor_id, article_id, mention_text, sentiment_score, sentiment_label, 
                                 source_url, source_domain, relevance_score)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                competitor_id, article_id, f"Mención de '{keyword}' en {newspaper}",
                                sentiment_score, sentiment_label, url, source_domain, relevance
                            ))
                            
                            mentions_found += 1
                            total_mentions += 1
                            break  # Solo contar una mención por artículo
                
                print(f"   ✅ Encontradas {mentions_found} menciones para {name}")
                
            except Exception as e:
                print(f"   ❌ Error analizando {name}: {e}")
                continue
        
        ci_conn.commit()
        ci_conn.close()
        news_conn.close()
        
        print(f"🎯 Análisis completado. Total menciones encontradas: {total_mentions}")
        return {
            "success": True,
            "total_mentions": total_mentions,
            "competitors_analyzed": len(competitors)
        }
    
    def _calculate_simple_sentiment(self, text: str, keyword: str) -> float:
        """Calcular sentimiento simple basado en palabras positivas/negativas"""
        positive_words = ['bueno', 'excelente', 'positivo', 'éxito', 'crecimiento', 'mejora', 'ganancia', 'victoria']
        negative_words = ['malo', 'mal', 'negativo', 'fracaso', 'pérdida', 'problema', 'crisis', 'derrota']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 0.3  # Positivo
        elif negative_count > positive_count:
            return -0.3  # Negativo
        else:
            return 0.0  # Neutral
    
    def _get_sentiment_label(self, score: float) -> str:
        """Convertir score de sentimiento a etiqueta"""
        if score > 0.1:
            return 'positive'
        elif score < -0.1:
            return 'negative'
        else:
            return 'neutral'
    
    def _extract_domain(self, url: str) -> str:
        """Extraer dominio de una URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return url.split('/')[2] if '//' in url else url
    
    def add_competitor(self, user_id: int, competitor_name: str, keywords: List[str], domains: List[str] = None) -> int:
        """Agregar un nuevo competidor para monitorear"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verificar límites del plan del usuario
        current_count = self.get_competitor_count(user_id)
        plan_limit = self.get_user_competitor_limit(user_id)
        
        if current_count >= plan_limit:
            raise ValueError(f"Límite de competidores alcanzado. Plan actual permite {plan_limit} competidores.")
        
        cursor.execute('''
            INSERT INTO user_competitors (user_id, competitor_name, competitor_keywords, competitor_domains)
            VALUES (?, ?, ?, ?)
        ''', (user_id, competitor_name, json.dumps(keywords), json.dumps(domains or [])))
        
        competitor_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ Competidor '{competitor_name}' agregado para usuario {user_id}")
        return competitor_id
    
    def get_competitor_count(self, user_id: int) -> int:
        """Obtener número de competidores activos del usuario"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM user_competitors 
            WHERE user_id = ? AND is_active = 1
        ''', (user_id,))
        
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_user_competitor_limit(self, user_id: int) -> int:
        """Obtener límite de competidores según el plan del usuario"""
        try:
            # Conectar directamente a la base de datos de suscripciones
            conn = sqlite3.connect("subscription_database.db")
            cursor = conn.cursor()
            
            # Obtener la suscripción activa del usuario
            cursor.execute('''
                SELECT p.max_competitors 
                FROM user_subscriptions us
                JOIN plans p ON us.plan_id = p.id
                WHERE us.user_id = ? AND us.status = 'active'
                ORDER BY us.start_date DESC
                LIMIT 1
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result[0]
            
            # Si no tiene suscripción, devolver límite del plan gratuito
            return 1
            
        except Exception as e:
            print(f"Error getting competitor limit: {e}")
            return 1  # Fallback
    
    def get_user_competitors(self, user_id: int) -> List[Dict]:
        """Obtener todos los competidores del usuario"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, competitor_name, competitor_keywords, competitor_domains, 
                   is_active, created_at, updated_at
            FROM user_competitors 
            WHERE user_id = ? AND is_active = 1
            ORDER BY created_at DESC
        ''', (user_id,))
        
        competitors = []
        for row in cursor.fetchall():
            competitors.append({
                'id': row[0],
                'name': row[1],
                'keywords': json.loads(row[2]),
                'domains': json.loads(row[3]),
                'is_active': bool(row[4]),
                'created_at': row[5],
                'updated_at': row[6]
            })
        
        conn.close()
        return competitors
    
    def analyze_article_for_competitors(self, article_id: int, article_text: str, article_url: str) -> List[Dict]:
        """Analizar un artículo en busca de menciones de competidores"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Obtener todos los competidores activos
        cursor.execute('''
            SELECT uc.id, uc.user_id, uc.competitor_name, uc.competitor_keywords
            FROM user_competitors uc
            WHERE uc.is_active = 1
        ''')
        
        mentions_found = []
        article_text_lower = article_text.lower()
        
        for row in cursor.fetchall():
            competitor_id, user_id, competitor_name, keywords_json = row
            keywords = json.loads(keywords_json)
            
            # Buscar menciones de palabras clave
            for keyword in keywords:
                if keyword.lower() in article_text_lower:
                    # Calcular relevancia
                    relevance = self.calculate_relevance(article_text, keyword, competitor_name)
                    
                    if relevance > 0.3:  # Solo menciones relevantes
                        # Analizar sentimiento
                        sentiment_score, sentiment_label = self.analyze_sentiment(article_text, keyword)
                        
                        # Guardar mención
                        cursor.execute('''
                            INSERT INTO competitor_mentions 
                            (competitor_id, article_id, mention_text, sentiment_score, sentiment_label, 
                             source_url, source_domain, relevance_score)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (competitor_id, article_id, keyword, sentiment_score, sentiment_label, 
                              article_url, self.extract_domain(article_url), relevance))
                        
                        mentions_found.append({
                            'competitor_id': competitor_id,
                            'user_id': user_id,
                            'competitor_name': competitor_name,
                            'keyword': keyword,
                            'sentiment_score': sentiment_score,
                            'sentiment_label': sentiment_label,
                            'relevance_score': relevance
                        })
        
        conn.commit()
        conn.close()
        return mentions_found
    
    def calculate_relevance(self, text: str, keyword: str, competitor_name: str) -> float:
        """Calcular relevancia de una mención (0-1)"""
        text_lower = text.lower()
        keyword_lower = keyword.lower()
        competitor_lower = competitor_name.lower()
        
        relevance = 0.0
        
        # Frecuencia de la palabra clave
        keyword_count = text_lower.count(keyword_lower)
        if keyword_count > 0:
            relevance += min(keyword_count * 0.1, 0.5)
        
        # Presencia del nombre del competidor
        if competitor_lower in text_lower:
            relevance += 0.3
        
        # Contexto empresarial (palabras relacionadas con negocios)
        business_words = ['empresa', 'compañía', 'marca', 'producto', 'servicio', 'ventas', 'mercado', 'competencia']
        for word in business_words:
            if word in text_lower:
                relevance += 0.05
        
        return min(relevance, 1.0)
    
    def analyze_sentiment(self, text: str, keyword: str) -> tuple:
        """Análisis básico de sentimiento (-1 a 1)"""
        # Palabras positivas
        positive_words = ['excelente', 'bueno', 'mejor', 'increíble', 'fantástico', 'recomiendo', 'satisfecho', 'feliz']
        # Palabras negativas
        negative_words = ['malo', 'terrible', 'horrible', 'pésimo', 'decepcionado', 'problema', 'error', 'falla']
        
        text_lower = text.lower()
        sentiment_score = 0.0
        
        # Buscar palabras positivas cerca de la keyword
        keyword_pos = text_lower.find(keyword.lower())
        if keyword_pos != -1:
            context = text_lower[max(0, keyword_pos-100):keyword_pos+100]
            
            for word in positive_words:
                if word in context:
                    sentiment_score += 0.2
            
            for word in negative_words:
                if word in context:
                    sentiment_score -= 0.2
        
        # Normalizar
        sentiment_score = max(-1.0, min(1.0, sentiment_score))
        
        if sentiment_score > 0.1:
            sentiment_label = 'positive'
        elif sentiment_score < -0.1:
            sentiment_label = 'negative'
        else:
            sentiment_label = 'neutral'
        
        return sentiment_score, sentiment_label
    
    def extract_domain(self, url: str) -> str:
        """Extraer dominio de una URL"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return url
    
    def get_competitor_analytics(self, user_id: int, days: int = 30) -> Dict:
        """Obtener analytics de competidores del usuario"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Obtener competidores del usuario
        competitors = self.get_user_competitors(user_id)
        analytics = {}
        
        for competitor in competitors:
            competitor_id = competitor['id']
            
            # Menciones en los últimos N días
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_mentions,
                    AVG(sentiment_score) as avg_sentiment,
                    SUM(CASE WHEN sentiment_label = 'positive' THEN 1 ELSE 0 END) as positive_mentions,
                    SUM(CASE WHEN sentiment_label = 'negative' THEN 1 ELSE 0 END) as negative_mentions,
                    SUM(CASE WHEN sentiment_label = 'neutral' THEN 1 ELSE 0 END) as neutral_mentions
                FROM competitor_mentions 
                WHERE competitor_id = ? 
                AND mention_date >= datetime('now', '-{} days')
            '''.format(days), (competitor_id,))
            
            row = cursor.fetchone()
            if row:
                analytics[competitor['name']] = {
                    'total_mentions': row[0] or 0,
                    'avg_sentiment': round(row[1] or 0, 2),
                    'positive_mentions': row[2] or 0,
                    'negative_mentions': row[3] or 0,
                    'neutral_mentions': row[4] or 0,
                    'sentiment_trend': self.get_sentiment_trend(competitor_id, days)
                }
        
        conn.close()
        return analytics
    
    def get_sentiment_trend(self, competitor_id: int, days: int) -> List[Dict]:
        """Obtener tendencia de sentimiento por día"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                DATE(mention_date) as date,
                AVG(sentiment_score) as avg_sentiment,
                COUNT(*) as mentions_count
            FROM competitor_mentions 
            WHERE competitor_id = ? 
            AND mention_date >= datetime('now', '-{} days')
            GROUP BY DATE(mention_date)
            ORDER BY date DESC
        '''.format(days), (competitor_id,))
        
        trend = []
        for row in cursor.fetchall():
            trend.append({
                'date': row[0],
                'sentiment': round(row[1] or 0, 2),
                'mentions': row[2] or 0
            })
        
        conn.close()
        return trend
    
    def create_alert(self, user_id: int, competitor_id: int, alert_type: str, message: str, data: Dict = None):
        """Crear una alerta para el usuario"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO competitor_alerts (user_id, competitor_id, alert_type, alert_message, alert_data)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, competitor_id, alert_type, message, json.dumps(data or {})))
        
        conn.commit()
        conn.close()
    
    def get_user_alerts(self, user_id: int, unread_only: bool = True) -> List[Dict]:
        """Obtener alertas del usuario"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT ca.id, ca.alert_type, ca.alert_message, ca.alert_data, 
                   ca.created_at, uc.competitor_name
            FROM competitor_alerts ca
            JOIN user_competitors uc ON ca.competitor_id = uc.id
            WHERE ca.user_id = ?
        '''
        
        if unread_only:
            query += ' AND ca.is_read = 0'
        
        query += ' ORDER BY ca.created_at DESC LIMIT 50'
        
        cursor.execute(query, (user_id,))
        
        alerts = []
        for row in cursor.fetchall():
            alerts.append({
                'id': row[0],
                'type': row[1],
                'message': row[2],
                'data': json.loads(row[3]) if row[3] else {},
                'created_at': row[4],
                'competitor_name': row[5]
            })
        
        conn.close()
        return alerts

# Función para inicializar el sistema
def init_competitive_intelligence():
    """Inicializar el sistema de competitive intelligence"""
    system = CompetitiveIntelligenceSystem()
    print("🚀 Sistema de Competitive Intelligence inicializado")
    return system

if __name__ == "__main__":
    # Inicializar el sistema
    ci_system = init_competitive_intelligence()
    
    # Ejemplo de uso
    print("\n📊 Ejemplo de uso:")
    print("1. Agregar competidor: ci_system.add_competitor(user_id, 'Coca Cola', ['coca cola', 'coca-cola'])")
    print("2. Obtener analytics: ci_system.get_competitor_analytics(user_id)")
    print("3. Obtener alertas: ci_system.get_user_alerts(user_id)")
