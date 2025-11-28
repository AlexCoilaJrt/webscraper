"""
Sistema de Predicción de Trending Topics
Analiza patrones históricos para predecir qué temas serán virales en 24-48 horas
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import Counter, defaultdict
import re
import math

logger = logging.getLogger(__name__)

class TrendingTopicsPredictor:
    """Sistema inteligente de predicción de trending topics"""
    
    def __init__(self, db_path: str = "news_database.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializar base de datos para predicciones"""
        conn = sqlite3.connect("trending_predictions.db")
        cursor = conn.cursor()
        
        # Tabla de predicciones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                prediction_date DATETIME NOT NULL,
                topic TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                viral_potential REAL NOT NULL,
                time_to_trend INTEGER NOT NULL,
                keywords TEXT NOT NULL,
                sources TEXT NOT NULL,
                category TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de análisis de patrones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pattern_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_date DATETIME NOT NULL,
                topic TEXT NOT NULL,
                historical_mentions INTEGER NOT NULL,
                growth_rate REAL NOT NULL,
                peak_time INTEGER NOT NULL,
                viral_indicators TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de uso diario por usuario
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_predictions_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                usage_date DATE NOT NULL,
                predictions_used INTEGER DEFAULT 0,
                plan_type TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, usage_date)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Base de datos de Trending Predictor inicializada")
    
    def analyze_historical_patterns(self, days_back: int = 14) -> Dict:  # Reducido de 30 a 14 días para más velocidad
        """Analizar patrones históricos de trending topics"""
        logger.info(f"🔍 Analizando patrones históricos de {days_back} días...")
        
        try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        except Exception as e:
            logger.error(f"Error conectando a la base de datos {self.db_path}: {e}")
            return {'success': False, 'error': f'Error de conexión a la base de datos: {str(e)}'}
        
        try:
            # Obtener artículos de los últimos días (limitado a 5000 para mejor rendimiento)
        start_date = datetime.now() - timedelta(days=days_back)
        cursor.execute('''
            SELECT title, content, newspaper, scraped_at
            FROM articles 
            WHERE scraped_at >= ?
            ORDER BY scraped_at DESC
                LIMIT 5000
        ''', (start_date.strftime('%Y-%m-%d'),))
        
        articles = cursor.fetchall()
        logger.info(f"📊 Analizando {len(articles)} artículos históricos...")
            
            if len(articles) == 0:
                logger.warning("No se encontraron artículos para analizar")
                conn.close()
                return {
                    'success': False,
                    'error': 'No hay suficientes artículos históricos para analizar. Necesitas al menos algunos artículos en la base de datos.',
                    'articles_analyzed': 0
                }
        
        # Análisis de palabras clave por día
        daily_keywords = defaultdict(Counter)
        topic_momentum = defaultdict(list)
        
        for title, content, newspaper, scraped_at in articles:
            try:
                # Manejar diferentes formatos de fecha
                if 'T' in scraped_at:
                    # Formato ISO con microsegundos: 2025-09-13T18:50:19.914231
                    date_str = scraped_at.split('T')[0]  # Solo la parte de fecha
                    date = datetime.strptime(date_str, '%Y-%m-%d').date()
                else:
                    # Formato tradicional: 2025-09-13 18:50:19
                    date = datetime.strptime(scraped_at, '%Y-%m-%d %H:%M:%S').date()
                text = f"{title} {content}".lower()
                
                # Extraer palabras clave relevantes
                keywords = self._extract_trending_keywords(text)
                
                for keyword in keywords:
                    daily_keywords[date][keyword] += 1
                    topic_momentum[keyword].append(date)
                    
            except Exception as e:
                logger.error(f"Error procesando artículo: {e}")
                continue
        
            # Calcular patrones de crecimiento (FUERA del bucle)
        growth_patterns = self._calculate_growth_patterns(daily_keywords, topic_momentum)
        
            if len(growth_patterns) == 0:
                logger.warning("No se identificaron patrones de crecimiento")
                conn.close()
                return {
                    'success': False,
                    'error': 'No se pudieron identificar patrones de crecimiento. Intenta con más artículos o un rango de tiempo mayor.',
                    'articles_analyzed': len(articles),
                    'patterns_analyzed': 0
                }
            
        conn.close()
        
        logger.info(f"✅ Análisis completado: {len(growth_patterns)} patrones identificados")
        return {
            'success': True,
            'patterns_analyzed': len(growth_patterns),
            'articles_analyzed': len(articles),
            'growth_patterns': growth_patterns
        }
        except sqlite3.Error as e:
            logger.error(f"Error de base de datos: {e}")
            try:
                conn.close()
            except:
                pass
            return {'success': False, 'error': f'Error de base de datos: {str(e)}'}
        except Exception as e:
            logger.error(f"Error en análisis de patrones: {e}", exc_info=True)
            try:
                conn.close()
            except:
                pass
            return {'success': False, 'error': f'Error en análisis: {str(e)}'}
    
    def _extract_trending_keywords(self, text: str) -> List[str]:
        """Extraer palabras clave con potencial viral"""
        # Palabras de stop
        stop_words = {
            'este', 'esta', 'estos', 'estas', 'para', 'con', 'por', 'que', 'como', 'más', 'muy', 'pero', 'sin', 'bajo', 'sobre', 'entre', 'hasta', 'desde', 'hacia', 'durante', 'mediante', 'según', 'aunque', 'mientras', 'donde', 'cuando', 'porque', 'aunque', 'también', 'solo', 'solo', 'tanto', 'cada', 'todo', 'toda', 'todos', 'todas', 'alguno', 'alguna', 'algunos', 'algunas', 'ninguno', 'ninguna', 'ningunos', 'ningunas', 'otro', 'otra', 'otros', 'otras', 'mismo', 'misma', 'mismos', 'mismas', 'tal', 'tales', 'cual', 'cuales', 'cuanto', 'cuanta', 'cuantos', 'cuantas', 'mucho', 'mucha', 'muchos', 'muchas', 'poco', 'poca', 'pocos', 'pocas', 'demasiado', 'demasiada', 'demasiados', 'demasiadas', 'bastante', 'bastantes', 'suficiente', 'suficientes', 'viernes', 'miércoles', 'jueves', 'martes', 'sábado', 'domingo', 'lunes', 'semana', 'día', 'años', 'año', 'mes', 'semana', 'hora', 'minuto', 'segundo'
        }
        
        # Extraer palabras de 4+ caracteres
        words = re.findall(r'\b[a-zA-ZáéíóúñüÁÉÍÓÚÑÜ]{4,}\b', text)
        
        # Filtrar palabras relevantes
        relevant_words = []
        for word in words:
            word_lower = word.lower()
            if (word_lower not in stop_words and 
                len(word_lower) > 3 and 
                not word_lower.isdigit() and
                self._is_trending_keyword(word_lower)):
                relevant_words.append(word_lower)
        
        return relevant_words
    
    def _is_trending_keyword(self, word: str) -> bool:
        """Determinar si una palabra tiene potencial viral"""
        # Palabras que indican trending
        trending_indicators = {
            'nuevo', 'nueva', 'último', 'última', 'reciente', 'actual', 'actualidad',
            'tendencia', 'viral', 'popular', 'destacado', 'importante', 'urgente',
            'exclusivo', 'sorprendente', 'increíble', 'impactante', 'revelación',
            'escándalo', 'polémica', 'controversia', 'crisis', 'emergencia',
            'descubrimiento', 'innovación', 'tecnología', 'avance', 'logro',
            'récord', 'histórico', 'primera', 'primero', 'único', 'única'
        }
        
        # Categorías con alto potencial viral
        viral_categories = {
            'política', 'gobierno', 'presidente', 'ministro', 'congreso', 'elecciones',
            'economía', 'dólar', 'inflación', 'crisis', 'mercado', 'empresa',
            'deportes', 'fútbol', 'mundial', 'olimpiadas', 'campeonato', 'liga',
            'entretenimiento', 'celebridad', 'famoso', 'actor', 'cantante', 'película',
            'tecnología', 'internet', 'redes', 'sociales', 'app', 'digital',
            'salud', 'medicina', 'vacuna', 'enfermedad', 'pandemia', 'virus',
            'medio', 'ambiente', 'cambio', 'climático', 'contaminación', 'energía'
        }
        
        return (word in trending_indicators or 
                word in viral_categories or 
                any(indicator in word for indicator in trending_indicators))
    
    def _calculate_growth_patterns(self, daily_keywords: Dict, topic_momentum: Dict) -> Dict:
        """Calcular patrones de crecimiento de temas"""
        growth_patterns = {}
        
        for topic, dates in topic_momentum.items():
            if len(dates) < 3:  # Necesitamos al menos 3 menciones
                continue
            
            # Contar menciones por día
            daily_counts = Counter(dates)
            sorted_dates = sorted(daily_counts.keys())
            
            if len(sorted_dates) < 2:
                continue
            
            # Calcular tasa de crecimiento
            growth_rate = self._calculate_growth_rate(daily_counts, sorted_dates)
            
            # Calcular momentum
            momentum = self._calculate_momentum(daily_counts, sorted_dates)
            
            # Calcular viral potential
            viral_potential = self._calculate_viral_potential(topic, growth_rate, momentum)
            
            # Calcular tiempo estimado para trending
            time_to_trend = self._estimate_time_to_trend(growth_rate, momentum)
            
            growth_patterns[topic] = {
                'growth_rate': growth_rate,
                'momentum': momentum,
                'viral_potential': viral_potential,
                'time_to_trend_hours': time_to_trend,
                'total_mentions': len(dates),
                'peak_day': max(daily_counts, key=daily_counts.get),
                'trending_probability': min(viral_potential * 100, 95)  # Máximo 95%
            }
        
        # Ordenar por viral potential
        sorted_patterns = dict(sorted(
            growth_patterns.items(), 
            key=lambda x: x[1]['viral_potential'], 
            reverse=True
        ))
        
        return sorted_patterns
    
    def _calculate_growth_rate(self, daily_counts: Counter, sorted_dates: List) -> float:
        """Calcular tasa de crecimiento"""
        if len(sorted_dates) < 2:
            return 0.0
        
        # Calcular crecimiento promedio
        growth_rates = []
        for i in range(1, len(sorted_dates)):
            prev_count = daily_counts[sorted_dates[i-1]]
            curr_count = daily_counts[sorted_dates[i]]
            
            if prev_count > 0:
                growth_rate = (curr_count - prev_count) / prev_count
                growth_rates.append(growth_rate)
        
        return sum(growth_rates) / len(growth_rates) if growth_rates else 0.0
    
    def _calculate_momentum(self, daily_counts: Counter, sorted_dates: List) -> float:
        """Calcular momentum del tema"""
        if len(sorted_dates) < 3:
            return 0.0
        
        # Momentum basado en tendencia reciente
        recent_dates = sorted_dates[-3:]  # Últimos 3 días
        recent_counts = [daily_counts[date] for date in recent_dates]
        
        # Calcular tendencia
        if len(recent_counts) >= 2:
            momentum = (recent_counts[-1] - recent_counts[0]) / max(recent_counts[0], 1)
            return min(momentum, 5.0)  # Máximo momentum de 5.0
        
        return 0.0
    
    def _calculate_viral_potential(self, topic: str, growth_rate: float, momentum: float) -> float:
        """Calcular potencial viral de un tema"""
        base_potential = 0.3
        
        # Factores de crecimiento
        growth_factor = min(growth_rate * 0.2, 0.4)
        
        # Factores de momentum
        momentum_factor = min(momentum * 0.1, 0.3)
        
        # Factores específicos del tema
        topic_factor = self._get_topic_viral_factor(topic)
        
        viral_potential = base_potential + growth_factor + momentum_factor + topic_factor
        return min(viral_potential, 1.0)  # Máximo 1.0
    
    def _get_topic_viral_factor(self, topic: str) -> float:
        """Obtener factor viral específico del tema"""
        high_viral_topics = {
            'política', 'gobierno', 'presidente', 'elecciones', 'crisis', 'escándalo',
            'fútbol', 'mundial', 'deportes', 'celebridad', 'famoso', 'viral',
            'tecnología', 'innovación', 'descubrimiento', 'salud', 'pandemia'
        }
        
        medium_viral_topics = {
            'economía', 'mercado', 'empresa', 'entretenimiento', 'cultura',
            'medio', 'ambiente', 'educación', 'ciencia', 'investigación'
        }
        
        topic_lower = topic.lower()
        
        if any(high_topic in topic_lower for high_topic in high_viral_topics):
            return 0.3
        elif any(medium_topic in topic_lower for medium_topic in medium_viral_topics):
            return 0.15
        else:
            return 0.05
    
    def _estimate_time_to_trend(self, growth_rate: float, momentum: float) -> int:
        """Estimar tiempo en horas para que un tema se vuelva trending"""
        if growth_rate <= 0 and momentum <= 0:
            return 72  # 3 días si no hay crecimiento
        
        # Fórmula basada en crecimiento y momentum
        base_time = 48  # 2 días base
        growth_factor = max(0, 1 - growth_rate) * 24  # Reducir tiempo con crecimiento
        momentum_factor = max(0, 1 - momentum) * 12   # Reducir tiempo con momentum
        
        estimated_hours = base_time - growth_factor - momentum_factor
        return max(6, min(estimated_hours, 72))  # Entre 6 horas y 3 días
    
    def generate_predictions(self, user_id: int, limit: int = 10) -> Dict:
        """Generar predicciones de trending topics para un usuario"""
        logger.info(f"🔮 Generando {limit} predicciones para usuario {user_id}")
        
        # Verificar límites del plan
        if not self._check_user_limits(user_id):
            return {
                'success': False,
                'error': 'Límite diario de predicciones alcanzado',
                'upgrade_required': True
            }
        
        # Analizar patrones históricos
        analysis = self.analyze_historical_patterns()
        if not analysis['success']:
            return {'success': False, 'error': 'Error en análisis de patrones'}
        
        # Generar predicciones
        predictions = []
        patterns = analysis['growth_patterns']
        
        for i, (topic, data) in enumerate(list(patterns.items())[:limit]):
            prediction = {
                'topic': topic,
                'confidence_score': data['trending_probability'] / 100,
                'viral_potential': data['viral_potential'],
                'time_to_trend_hours': data['time_to_trend_hours'],
                'keywords': [topic] + self._get_related_keywords(topic),
                'sources': self._get_topic_sources(topic),
                'category': self._categorize_topic(topic),
                'trending_probability': data['trending_probability'],
                'growth_rate': data['growth_rate'],
                'momentum': data['momentum']
            }
            predictions.append(prediction)
        
        # Guardar predicciones
        try:
        self._save_predictions(user_id, predictions)
        except Exception as e:
            logger.error(f"Error guardando predicciones: {e}", exc_info=True)
            # Continuar aunque falle el guardado
        
        # Actualizar uso diario
        try:
        self._update_daily_usage(user_id)
        except Exception as e:
            logger.error(f"Error actualizando uso diario: {e}", exc_info=True)
            # Continuar aunque falle la actualización
        
        logger.info(f"✅ {len(predictions)} predicciones generadas exitosamente")
        return {
            'success': True,
            'predictions': predictions,
            'total_generated': len(predictions),
            'analysis_date': datetime.now().isoformat()
        }
    
    def _check_user_limits(self, user_id: int) -> bool:
        """Verificar límites diarios del usuario"""
        conn = sqlite3.connect("trending_predictions.db")
        cursor = conn.cursor()
        
        today = datetime.now().date()
        
        # Obtener plan del usuario (simulado - en producción vendría de la BD de usuarios)
        plan_type = "creator"  # Por defecto
        
        # Límites por plan
        limits = {
            "creator": 5,
            "influencer": 20,
            "media_company": 999999  # Ilimitado
        }
        
        daily_limit = limits.get(plan_type, 5)
        
        # Verificar uso actual
        cursor.execute('''
            SELECT predictions_used FROM daily_predictions_usage 
            WHERE user_id = ? AND usage_date = ?
        ''', (user_id, today))
        
        result = cursor.fetchone()
        current_usage = result[0] if result else 0
        
        conn.close()
        
        return current_usage < daily_limit
    
    def _get_related_keywords(self, topic: str) -> List[str]:
        """Obtener palabras clave relacionadas"""
        # Simulación de keywords relacionadas
        related_keywords = {
            'política': ['gobierno', 'presidente', 'congreso', 'elecciones'],
            'fútbol': ['mundial', 'liga', 'campeonato', 'deportes'],
            'tecnología': ['innovación', 'digital', 'internet', 'app'],
            'economía': ['mercado', 'dólar', 'inflación', 'crisis'],
            'salud': ['medicina', 'vacuna', 'enfermedad', 'pandemia']
        }
        
        topic_lower = topic.lower()
        for category, keywords in related_keywords.items():
            if category in topic_lower or any(kw in topic_lower for kw in keywords):
                return keywords[:3]  # Top 3 relacionadas
        
        return [topic]  # Fallback
    
    def _get_topic_sources(self, topic: str) -> List[str]:
        """Obtener fuentes relevantes para el tema"""
        # Simulación de fuentes basadas en el tema
        sources = ['El Comercio', 'La Republica', 'Peru21', 'Trome', 'Ojo']
        return sources[:3]  # Top 3 fuentes
    
    def _categorize_topic(self, topic: str) -> str:
        """Categorizar el tema"""
        topic_lower = topic.lower()
        
        categories = {
            'Política': ['política', 'gobierno', 'presidente', 'congreso', 'elecciones'],
            'Deportes': ['fútbol', 'mundial', 'liga', 'campeonato', 'deportes'],
            'Tecnología': ['tecnología', 'innovación', 'digital', 'internet', 'app'],
            'Economía': ['economía', 'mercado', 'dólar', 'inflación', 'crisis'],
            'Salud': ['salud', 'medicina', 'vacuna', 'enfermedad', 'pandemia'],
            'Entretenimiento': ['entretenimiento', 'celebridad', 'famoso', 'cultura'],
            'Medio Ambiente': ['medio', 'ambiente', 'cambio', 'climático', 'energía']
        }
        
        for category, keywords in categories.items():
            if any(kw in topic_lower for kw in keywords):
                return category
        
        return 'General'
    
    def _save_predictions(self, user_id: int, predictions: List[Dict]):
        """Guardar predicciones en la base de datos"""
        try:
        conn = sqlite3.connect("trending_predictions.db")
        cursor = conn.cursor()
        
        for prediction in predictions:
                try:
            cursor.execute('''
                INSERT INTO predictions 
                (user_id, prediction_date, topic, confidence_score, viral_potential, 
                 time_to_trend, keywords, sources, category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                datetime.now(),
                prediction['topic'],
                prediction['confidence_score'],
                prediction['viral_potential'],
                prediction['time_to_trend_hours'],
                json.dumps(prediction['keywords']),
                json.dumps(prediction['sources']),
                prediction['category']
            ))
                except Exception as e:
                    logger.error(f"Error guardando predicción individual: {e}")
                    continue
        
        conn.commit()
        conn.close()
        except Exception as e:
            logger.error(f"Error en _save_predictions: {e}", exc_info=True)
            raise
    
    def _update_daily_usage(self, user_id: int):
        """Actualizar uso diario del usuario"""
        try:
        conn = sqlite3.connect("trending_predictions.db")
        cursor = conn.cursor()
        
        today = datetime.now().date()
        plan_type = "creator"  # Por defecto
        
            # Primero verificar si existe un registro para hoy
            cursor.execute('''
                SELECT predictions_used FROM daily_predictions_usage 
                WHERE user_id = ? AND usage_date = ?
            ''', (user_id, today))
            
            result = cursor.fetchone()
            if result:
                # Actualizar registro existente
                new_count = result[0] + 1
                cursor.execute('''
                    UPDATE daily_predictions_usage 
                    SET predictions_used = ?
                    WHERE user_id = ? AND usage_date = ?
                ''', (new_count, user_id, today))
            else:
                # Crear nuevo registro
        cursor.execute('''
                    INSERT INTO daily_predictions_usage 
            (user_id, usage_date, predictions_used, plan_type)
                    VALUES (?, ?, 1, ?)
                ''', (user_id, today, plan_type))
        
        conn.commit()
        conn.close()
        except Exception as e:
            logger.error(f"Error en _update_daily_usage: {e}", exc_info=True)
            raise
    
    def get_user_predictions(self, user_id: int, limit: int = 20) -> Dict:
        """Obtener predicciones del usuario"""
        conn = sqlite3.connect("trending_predictions.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT topic, confidence_score, viral_potential, time_to_trend, 
                   keywords, sources, category, created_at
            FROM predictions 
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        results = cursor.fetchall()
        predictions = []
        
        for row in results:
            predictions.append({
                'topic': row[0],
                'confidence_score': row[1],
                'viral_potential': row[2],
                'time_to_trend_hours': row[3],
                'keywords': json.loads(row[4]),
                'sources': json.loads(row[5]),
                'category': row[6],
                'created_at': row[7]
            })
        
        conn.close()
        
        return {
            'success': True,
            'predictions': predictions,
            'total': len(predictions)
        }
    
    def get_daily_usage(self, user_id: int) -> Dict:
        """Obtener uso diario del usuario"""
        conn = sqlite3.connect("trending_predictions.db")
        cursor = conn.cursor()
        
        today = datetime.now().date()
        
        cursor.execute('''
            SELECT predictions_used, plan_type FROM daily_predictions_usage 
            WHERE user_id = ? AND usage_date = ?
        ''', (user_id, today))
        
        result = cursor.fetchone()
        
        if result:
            used, plan_type = result
        else:
            used, plan_type = 0, "creator"
        
        # Límites por plan
        limits = {
            "creator": 5,
            "influencer": 20,
            "media_company": 999999
        }
        
        daily_limit = limits.get(plan_type, 5)
        
        conn.close()
        
        return {
            'success': True,
            'used': used,
            'limit': daily_limit,
            'remaining': max(0, daily_limit - used),
            'plan_type': plan_type
        }
