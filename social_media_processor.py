#!/usr/bin/env python3
"""
Procesador de Datos de Redes Sociales
PROYECTO ACADÉMICO - Solo para fines educativos

Este módulo procesa los datos extraídos de redes sociales:
- Limpieza de texto
- Detección de idioma
- Clasificación por categorías
- Análisis de sentimiento básico
"""

import re
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Análisis de sentimiento
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    logger.warning("⚠️ TextBlob no disponible, usando análisis básico de sentimiento")

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    logger.warning("⚠️ VADER no disponible, usando análisis básico de sentimiento")


class SocialMediaProcessor:
    """
    Procesador de datos de redes sociales
    
    Incluye funciones para limpiar, clasificar y analizar contenido
    extraído de redes sociales.
    """
    
    def __init__(self):
        """Inicializar el procesador"""
        # Inicializar analizadores de sentimiento
        self.vader_analyzer = None
        if VADER_AVAILABLE:
            try:
                self.vader_analyzer = SentimentIntensityAnalyzer()
                logger.info("✅ VADER Sentiment Analyzer inicializado")
            except Exception as e:
                logger.warning(f"⚠️ Error inicializando VADER: {e}")
        
        # Palabras clave para categorización MEJORADA
        self.category_keywords = {
            'tecnología': [
                'tecnología', 'tecnologia', 'tech', 'software', 'app', 'aplicación', 'aplicacion',
                'programación', 'programacion', 'código', 'codigo', 'python', 'java', 'javascript',
                'IA', 'inteligencia artificial', 'AI', 'machine learning', 'deep learning',
                'blockchain', 'crypto', 'bitcoin', 'ethereum', 'nft', 'startup', 'innovación', 'innovacion',
                'digital', 'cibernético', 'cibernetico', 'hacker', 'desarrollador', 'developer',
                'cloud', 'nube', 'servidor', 'server', 'algoritmo', 'data science', 'big data'
            ],
            'deportes': [
                'deporte', 'fútbol', 'futbol', 'football', 'soccer', 'baloncesto', 'basketball',
                'basquet', 'tenis', 'tennis', 'natación', 'natacion', 'atletismo', 'olímpicos', 'olimpicos',
                'mundial', 'champions', 'liga', 'equipo', 'jugador', 'partido', 'gol', 'victoria',
                'campeonato', 'torneo', 'estadio', 'entrenador', 'coach', 'atleta', 'competencia',
                'olimpiadas', 'copa', 'final', 'semifinal', 'playoff'
            ],
            'política': [
                'política', 'politica', 'político', 'politico', 'gobierno', 'gobierno',
                'presidente', 'congreso', 'elecciones', 'voto', 'votar', 'votación', 'votacion',
                'partido político', 'democracia', 'derecho', 'ley', 'norma', 'legislación', 'legislacion',
                'parlamento', 'senado', 'diputado', 'ministro', 'ministra', 'alcalde', 'gobernador',
                'candidato', 'campaña', 'campana', 'elección', 'eleccion', 'referéndum', 'referendum'
            ],
            'entretenimiento': [
                'cine', 'película', 'pelicula', 'movie', 'actor', 'actriz', 'director',
                'música', 'musica', 'canción', 'cancion', 'artista', 'concierto', 'tour',
                'televisión', 'television', 'serie', 'show', 'programa', 'reality', 'talent show',
                'celebridad', 'famoso', 'famosos', 'red carpet', 'premio', 'oscar', 'grammy',
                'festival', 'carnaval', 'espectáculo', 'espectaculo', 'comedia', 'drama', 'thriller'
            ],
            'negocios': [
                'negocio', 'empresa', 'empresarial', 'business', 'comercio', 'comercial',
                'mercado', 'economía', 'economia', 'finanzas', 'inversión', 'inversion',
                'acciones', 'bolsa', 'stock', 'trading', 'forex', 'criptomoneda', 'crypto',
                'marketing', 'ventas', 'cliente', 'consumidor', 'producto', 'servicio',
                'startup', 'emprendimiento', 'CEO', 'CTO', 'CFO', 'director', 'gerente'
            ],
            'salud': [
                'salud', 'médico', 'medico', 'hospital', 'enfermedad', 'enfermo',
                'tratamiento', 'medicina', 'doctor', 'paciente', 'cura', 'terapia',
                'vacuna', 'virus', 'pandemia', 'epidemia', 'bienestar', 'fitness',
                'nutrición', 'nutricion', 'dieta', 'ejercicio', 'clínica', 'clinica',
                'cirugía', 'cirugia', 'medicamento', 'farmacia', 'salud mental'
            ],
            'general': []  # Categoría por defecto
        }
        
        # Palabras para análisis de sentimiento
        self.positive_words = [
            'bueno', 'buena', 'excelente', 'genial', 'fantástico', 'fantastico',
            'maravilloso', 'perfecto', 'amor', 'feliz', 'alegría', 'alegria',
            'éxito', 'exito', 'ganar', 'victoria', 'mejor', 'increíble', 'increible',
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'perfect',
            'love', 'happy', 'success', 'win', 'best', 'incredible'
        ]
        
        self.negative_words = [
            'malo', 'mala', 'terrible', 'horrible', 'triste', 'deprimido',
            'fracaso', 'perder', 'derrota', 'peor', 'odio', 'ira', 'enojado',
            'problema', 'error', 'fallo', 'mal', 'malo',
            'bad', 'terrible', 'horrible', 'sad', 'depressed', 'failure',
            'lose', 'defeat', 'worst', 'hate', 'angry', 'problem', 'error'
        ]
    
    def clean_text(self, text: str, remove_urls: bool = True, remove_mentions: bool = False) -> str:
        """
        Limpiar texto del tweet
        
        Args:
            text: Texto original
            remove_urls: Si True, remueve URLs
            remove_mentions: Si True, remueve menciones (@username)
        
        Returns:
            Texto limpio
        """
        if not text:
            return ""
        
        cleaned = text.strip()
        
        # Remover URLs
        if remove_urls:
            cleaned = re.sub(r'http\S+|www\.\S+', '', cleaned, flags=re.IGNORECASE)
        
        # Remover menciones
        if remove_mentions:
            cleaned = re.sub(r'@\w+', '', cleaned)
        
        # Remover espacios múltiples
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Remover caracteres especiales excesivos
        cleaned = re.sub(r'[^\w\s#.,!?¿¡]', '', cleaned)
        
        return cleaned.strip()
    
    def detect_language(self, text: str) -> str:
        """
        Detectar idioma básico del texto
        
        Args:
            text: Texto a analizar
        
        Returns:
            Código de idioma ('es', 'en', 'unknown')
        """
        if not text:
            return 'unknown'
        
        text_lower = text.lower()
        
        # Palabras comunes en español
        spanish_words = ['el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se',
                        'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para']
        
        # Palabras comunes en inglés
        english_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were']
        
        spanish_count = sum(1 for word in spanish_words if word in text_lower)
        english_count = sum(1 for word in english_words if word in text_lower)
        
        if spanish_count > english_count:
            return 'es'
        elif english_count > spanish_count:
            return 'en'
        else:
            return 'unknown'
    
    def categorize_tweet(self, text: str) -> str:
        """
        Clasificar tweet por categoría (MEJORADO con scoring ponderado)
        
        Args:
            text: Texto del tweet
        
        Returns:
            Categoría detectada
        """
        if not text or not isinstance(text, str):
            return 'general'
        
        text_lower = text.lower()
        category_scores = {}
        
        # Calcular puntuación por categoría (ponderado por frecuencia)
        for category, keywords in self.category_keywords.items():
            if category == 'general':
                continue
            
            score = 0
            # Contar ocurrencias de cada palabra clave
            for keyword in keywords:
                # Ponderar por frecuencia: más ocurrencias = mayor score
                occurrences = text_lower.count(keyword)
                score += occurrences
            
            if score > 0:
                category_scores[category] = score
        
        # Retornar categoría con mayor puntuación
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            # Solo retornar si el score es significativo (al menos 2 puntos)
            if category_scores[best_category] >= 2:
                return best_category
        
        return 'general'
    
    def analyze_sentiment(self, text: str) -> str:
        """
        Análisis de sentimiento usando VADER (preferido) o TextBlob (fallback)
        
        Args:
            text: Texto a analizar
        
        Returns:
            'positive', 'negative', o 'neutral'
        """
        if not text or not isinstance(text, str):
            return 'neutral'
        
        text = text.strip()
        if len(text) < 3:
            return 'neutral'
        
        # Priorizar VADER (mejor para redes sociales)
        if self.vader_analyzer:
            try:
                scores = self.vader_analyzer.polarity_scores(text)
                compound = scores['compound']
                
                # Umbrales: positivo > 0.05, negativo < -0.05, neutral en medio
                if compound > 0.05:
                    return 'positive'
                elif compound < -0.05:
                    return 'negative'
                else:
                    return 'neutral'
            except Exception as e:
                logger.debug(f"⚠️ Error con VADER, usando fallback: {e}")
        
        # Fallback: TextBlob
        if TEXTBLOB_AVAILABLE:
            try:
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity
                
                # Umbrales: positivo > 0.05, negativo < -0.05, neutral en medio
                if polarity > 0.05:
                    return 'positive'
                elif polarity < -0.05:
                    return 'negative'
                else:
                    return 'neutral'
            except Exception as e:
                logger.debug(f"⚠️ Error con TextBlob, usando análisis básico: {e}")
        
        # Fallback final: análisis básico por palabras clave
        text_lower = text.lower()
        
        # Contar palabras positivas y negativas
        positive_count = sum(1 for word in self.positive_words if word in text_lower)
        negative_count = sum(1 for word in self.negative_words if word in text_lower)
        
        # Determinar sentimiento
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def process_tweet(self, tweet: Dict, 
                     clean_text: bool = True,
                     detect_lang: bool = True,
                     categorize: bool = True,
                     analyze_sentiment_flag: bool = True) -> Dict:
        """
        Procesar un tweet completo con todas las funciones
        
        Args:
            tweet: Diccionario con datos del tweet
            clean_text: Si True, limpia el texto
            detect_lang: Si True, detecta idioma
            categorize: Si True, clasifica por categoría
            analyze_sentiment_flag: Si True, analiza sentimiento
        
        Returns:
            Tweet procesado con campos adicionales
        """
        # IMPORTANTE: Preservar TODOS los campos originales, especialmente image_url
        processed = tweet.copy()
        
        original_text = tweet.get('text', '')
        
        # Limpiar texto
        if clean_text:
            processed['cleaned_text'] = self.clean_text(original_text)
        else:
            processed['cleaned_text'] = original_text
        
        # Detectar idioma
        if detect_lang:
            processed['detected_language'] = self.detect_language(original_text)
        
        # Clasificar
        if categorize:
            processed['category'] = self.categorize_tweet(original_text)
        
        # Analizar sentimiento
        if analyze_sentiment_flag:
            processed['sentiment'] = self.analyze_sentiment(original_text)
        
        # Timestamp de procesamiento
        processed['processed_at'] = datetime.now().isoformat()
        
        # IMPORTANTE: Preservar TODOS los campos originales, especialmente image_url y video_url
        # Asegurar que image_url se preserve (si existe)
        if 'image_url' in tweet:
            processed['image_url'] = tweet['image_url']
        elif 'image_url' not in processed:
            # Si no está en el original, asegurar que esté presente como None
            processed['image_url'] = None
        
        # Preservar video_url (para Facebook)
        if 'video_url' in tweet:
            processed['video_url'] = tweet['video_url']
        elif 'video_url' not in processed:
            processed['video_url'] = None
        
        # Log para debug
        if processed.get('image_url'):
            logger.debug(f"✅ Post procesado tiene image_url: {processed.get('image_url')[:50]}...")
        if processed.get('video_url'):
            logger.debug(f"✅ Post procesado tiene video_url: {processed.get('video_url')[:50]}...")
        
        return processed
    
    def process_batch(self, tweets: List[Dict], **kwargs) -> List[Dict]:
        """
        Procesar un lote de tweets
        
        Args:
            tweets: Lista de tweets a procesar
            **kwargs: Argumentos adicionales para process_tweet
        
        Returns:
            Lista de tweets procesados
        """
        processed_tweets = []
        
        for tweet in tweets:
            try:
                processed = self.process_tweet(tweet, **kwargs)
                processed_tweets.append(processed)
            except Exception as e:
                logger.error(f"❌ Error procesando tweet: {e}")
                processed_tweets.append(tweet)  # Mantener original si falla
        
        return processed_tweets


def process_social_media_data(tweets: List[Dict], **kwargs) -> List[Dict]:
    """
    Función helper para procesar datos de redes sociales
    
    Args:
        tweets: Lista de tweets
        **kwargs: Argumentos adicionales
    
    Returns:
        Lista de tweets procesados
    """
    processor = SocialMediaProcessor()
    return processor.process_batch(tweets, **kwargs)


if __name__ == "__main__":
    """
    Ejemplo de uso educativo
    """
    print("=" * 60)
    print("🔬 PROYECTO ACADÉMICO - Procesador de Redes Sociales")
    print("=" * 60)
    
    # Ejemplo de tweet
    sample_tweet = {
        'platform': 'twitter',
        'username': '@usuario_ejemplo',
        'text': '¡La nueva tecnología de IA es increíble! #tecnologia #IA',
        'date': '2025-01-15',
        'likes': 100,
        'retweets': 50,
        'replies': 10,
        'hashtags': ['#tecnologia', '#IA'],
        'url': 'https://twitter.com/usuario/status/123456',
        'scraped_at': datetime.now().isoformat()
    }
    
    processor = SocialMediaProcessor()
    processed = processor.process_tweet(sample_tweet)
    
    print("\n📊 TWEET ORIGINAL:")
    print(json.dumps(sample_tweet, indent=2, ensure_ascii=False))
    
    print("\n📊 TWEET PROCESADO:")
    print(json.dumps(processed, indent=2, ensure_ascii=False))
    
    print("\n✅ Procesamiento completado")
    print("=" * 60)

