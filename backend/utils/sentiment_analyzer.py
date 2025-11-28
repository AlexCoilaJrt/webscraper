"""
Sistema avanzado de análisis de sentimientos para noticias
Incluye detección de polaridad, emociones, polarización y evolución temporal
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import json

logger = logging.getLogger(__name__)

# Intentar importar librerías de análisis de sentimientos
VADER_AVAILABLE = False
TEXTBLOB_AVAILABLE = False
EMOTION_ANALYZER = None

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    vader_analyzer = SentimentIntensityAnalyzer()
    VADER_AVAILABLE = True
    logger.info("✅ VADER sentiment analyzer cargado")
except ImportError:
    logger.warning("⚠️ VADER no disponible, usando análisis básico")
    vader_analyzer = None

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
    logger.info("✅ TextBlob disponible como fallback")
except ImportError:
    logger.warning("⚠️ TextBlob no disponible")
    TextBlob = None


class SentimentAnalyzer:
    """Analizador avanzado de sentimientos para noticias"""
    
    def __init__(self):
        self.vader_analyzer = vader_analyzer if VADER_AVAILABLE else None
        
        # Diccionarios de palabras para emociones
        self.emotion_keywords = {
            'anger': ['enojo', 'rabia', 'ira', 'furia', 'indignación', 'molesto', 'molesta', 
                     'enojado', 'enojada', 'furioso', 'furiosa', 'indignado', 'indignada',
                     'angry', 'furious', 'rage', 'outrage', 'annoyed'],
            'joy': ['alegría', 'felicidad', 'contento', 'contenta', 'feliz', 'regocijo',
                   'júbilo', 'euforia', 'celebration', 'joy', 'happy', 'glad', 'excited'],
            'fear': ['miedo', 'temor', 'ansiedad', 'preocupación', 'pánico', 'terror',
                    'asustado', 'asustada', 'nervioso', 'nerviosa', 'alerta',
                    'fear', 'afraid', 'worried', 'anxious', 'panic', 'terror'],
            'sadness': ['tristeza', 'triste', 'melancolía', 'depresión', 'desánimo',
                       'desesperanza', 'lamentable', 'sad', 'depressed', 'sorrow'],
            'surprise': ['sorpresa', 'sorprendido', 'sorprendida', 'asombro', 'impacto',
                        'inesperado', 'inesperada', 'surprise', 'shocked', 'amazed'],
            'disgust': ['asco', 'repugnancia', 'desagrado', 'odio', 'repulsión',
                       'disgust', 'hate', 'repulsed']
        }
        
        # Palabras para polarización
        self.polarization_keywords = {
            'extreme_positive': ['excelente', 'perfecto', 'fantástico', 'maravilloso', 
                                'increíble', 'extraordinario', 'sobresaliente'],
            'extreme_negative': ['terrible', 'horrible', 'catastrófico', 'desastroso',
                                'tragedia', 'escándalo', 'corrupción']
        }
    
    def analyze_sentiment(self, text: str) -> Dict:
        """
        Analizar sentimiento de un texto
        Retorna: {
            'polarity': 'positive' | 'negative' | 'neutral',
            'score': float (-1 a 1),
            'confidence': float (0 a 1),
            'emotions': Dict de emociones detectadas,
            'polarization': 'high' | 'medium' | 'low'
        }
        """
        if not text or not isinstance(text, str) or len(text.strip()) < 10:
            return {
                'polarity': 'neutral',
                'score': 0.0,
                'confidence': 0.0,
                'emotions': {},
                'polarization': 'low'
            }
        
        text_clean = text.strip()
        text_lower = text_clean.lower()
        
        # Análisis de polaridad usando VADER o TextBlob
        polarity_score = 0.0
        confidence = 0.0
        
        if self.vader_analyzer:
            try:
                scores = self.vader_analyzer.polarity_scores(text_clean)
                polarity_score = scores['compound']  # -1 a 1
                confidence = abs(polarity_score)  # Confianza basada en qué tan lejos de 0
            except Exception as e:
                logger.debug(f"Error con VADER: {e}")
        
        if polarity_score == 0.0 and TEXTBLOB_AVAILABLE:
            try:
                blob = TextBlob(text_clean)
                polarity_score = blob.sentiment.polarity
                confidence = abs(polarity_score)
            except Exception as e:
                logger.debug(f"Error con TextBlob: {e}")
        
        # Si aún no hay score, usar análisis básico
        if polarity_score == 0.0:
            polarity_score, confidence = self._basic_sentiment_analysis(text_lower)
        
        # Determinar polaridad
        if polarity_score > 0.05:
            polarity = 'positive'
        elif polarity_score < -0.05:
            polarity = 'negative'
        else:
            polarity = 'neutral'
        
        # Detectar emociones
        emotions = self._detect_emotions(text_lower)
        
        # Calcular polarización
        polarization = self._calculate_polarization(text_lower, abs(polarity_score))
        
        return {
            'polarity': polarity,
            'score': round(polarity_score, 3),
            'confidence': round(confidence, 3),
            'emotions': emotions,
            'polarization': polarization
        }
    
    def _basic_sentiment_analysis(self, text_lower: str) -> Tuple[float, float]:
        """Análisis básico de sentimiento usando palabras clave"""
        positive_words = ['bueno', 'excelente', 'éxito', 'crecimiento', 'mejora', 'positivo',
                         'ganancia', 'victoria', 'logro', 'avance', 'buen', 'buena', 'mejor',
                         'good', 'excellent', 'success', 'growth', 'improvement', 'positive']
        
        negative_words = ['malo', 'mal', 'problema', 'crisis', 'pérdida', 'negativo',
                         'fracaso', 'derrota', 'error', 'conflicto', 'peor', 'terrible',
                         'bad', 'problem', 'crisis', 'loss', 'negative', 'failure', 'error']
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total_words = len(text_lower.split())
        if total_words == 0:
            return 0.0, 0.0
        
        # Calcular score (-1 a 1)
        if positive_count + negative_count == 0:
            return 0.0, 0.0
        
        score = (positive_count - negative_count) / max(positive_count + negative_count, 1)
        confidence = min(abs(score) * 2, 1.0)  # Normalizar confianza
        
        return score, confidence
    
    def _detect_emotions(self, text_lower: str) -> Dict[str, float]:
        """Detectar emociones en el texto"""
        emotion_scores = {}
        
        for emotion, keywords in self.emotion_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            if matches > 0:
                # Normalizar score (0 a 1)
                emotion_scores[emotion] = min(matches / len(keywords), 1.0)
        
        return emotion_scores
    
    def _calculate_polarization(self, text_lower: str, sentiment_magnitude: float) -> str:
        """Calcular nivel de polarización"""
        # Buscar palabras extremas
        extreme_count = 0
        for keyword_list in self.polarization_keywords.values():
            extreme_count += sum(1 for keyword in keyword_list if keyword in text_lower)
        
        # Alta polarización si hay palabras extremas o sentimiento muy fuerte
        if extreme_count > 0 or sentiment_magnitude > 0.7:
            return 'high'
        elif sentiment_magnitude > 0.3 or extreme_count > 0:
            return 'medium'
        else:
            return 'low'
    
    def analyze_multiple(self, texts: List[str]) -> Dict:
        """Analizar múltiples textos y agregar resultados"""
        results = {
            'total': len(texts),
            'positive': 0,
            'negative': 0,
            'neutral': 0,
            'average_score': 0.0,
            'emotions_summary': defaultdict(float),
            'polarization_distribution': {'high': 0, 'medium': 0, 'low': 0},
            'scores': []
        }
        
        total_score = 0.0
        
        for text in texts:
            analysis = self.analyze_sentiment(text)
            
            results[analysis['polarity']] += 1
            results['scores'].append(analysis['score'])
            total_score += analysis['score']
            
            # Agregar emociones
            for emotion, score in analysis['emotions'].items():
                results['emotions_summary'][emotion] += score
            
            # Polarización
            results['polarization_distribution'][analysis['polarization']] += 1
        
        if results['total'] > 0:
            results['average_score'] = round(total_score / results['total'], 3)
            # Normalizar emociones
            for emotion in results['emotions_summary']:
                results['emotions_summary'][emotion] = round(
                    results['emotions_summary'][emotion] / results['total'], 3
                )
        
        return results


# Instancia global
sentiment_analyzer = SentimentAnalyzer()



