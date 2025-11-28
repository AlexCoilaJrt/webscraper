import sqlite3
import json
import re
from collections import Counter
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

# Base de datos de palabras clave por periódico (basada en análisis real)
NEWSPAPER_KEYWORDS = {
    'El Comercio': ['mundial', 'comercio', 'trump', 'kirk', 'charlie', 'contra', 'años', 'mundo', 'estados', 'unidos', 'tras'],
    'La Republica': ['años', 'científicos', 'estudio', 'vida', 'china', 'tierra', 'investigación', 'tecnología', 'ciencia', 'mundo'],
    'Peru21': ['peru21', 'noticias', 'investigación', 'política', 'sociedad', 'perú', 'lima', 'nacional', 'gobierno', 'país'],
    'El Peruano': ['gobierno', 'oficial', 'decretos', 'leyes', 'estado', 'perú', 'nacional', 'ministerio', 'presidente', 'congreso'],
    'La Vanguardia': ['kirk', 'trump', 'contra', 'charlie', 'bolsonaro', 'presidente', 'política', 'drones', 'asesinato', 'estados'],
    'Elmundo': ['años', 'rusia', 'madrid', 'después', 'ucrania', 'constelación', 'guerra', 'europa', 'españa', 'internacional'],
    'El Popular': ['lima', 'selección', 'mundial', 'perú', 'deportivo', 'años', 'tras', 'alianza', 'futbol', 'deportes'],
    'Nytimes': ['trump', 'biden', 'america', 'united', 'states', 'president', 'white', 'house', 'congress', 'senate'],
    'Diario Sin Fronteras': ['arequipa', 'puno', 'juliaca', 'tacna', 'cuzco', 'sur', 'perú', 'región', 'andina', 'sierra'],
    'Ojo': ['mundo', 'estados', 'unidos', 'perú', 'dólares', 'millones', 'mujer', 'hombre', 'familia', 'vida'],
    'Trome': ['trome', 'redacción', 'predicciones', 'salud', 'amor', 'perú', 'dinero', 'katty', 'horóscopo', 'familia'],
    'Andina': ['perú', 'peruano', 'andina', 'lima', 'elecciones', 'nacional', 'gobierno', 'estado', 'país', 'nación'],
    'America': ['país', 'violencia', 'seguridad', 'nacional', 'perú', 'sociedad', 'problema', 'solución', 'gobierno', 'estado'],
    'Dario Sin Fronteras': ['bolivia', 'perú', 'frontera', 'internacional', 'relaciones', 'país', 'gobierno', 'diplomacia', 'nacional', 'estado'],
    'El popular': ['perú', 'nacional', 'lima', 'chicharrón', 'mundial', 'educación', 'temas', 'sociedad', 'cultura', 'tradición']
}

# Base de datos de dominios correctos por periódico
NEWSPAPER_DOMAINS = {
    'El Comercio': 'elcomercio.pe',
    'La Republica': 'larepublica.pe',
    'Peru21': 'peru21.pe',
    'El Peruano': 'elperuano.pe',
    'La Vanguardia': 'lavanguardia.com',
    'Elmundo': 'elmundo.es',
    'El Popular': 'elpopular.pe',
    'Nytimes': 'nytimes.com',
    'Diario Sin Fronteras': 'diariosinfronteras.com.pe',
    'Ojo': 'ojo.pe',
    'Trome': 'trome.com',
    'Andina': 'andina.pe',
    'America': 'americatv.com.pe',
    'Dario Sin Fronteras': 'diariosinfronteras.com.pe',
    'El popular': 'elpopular.pe'
}

class AIKeywordAnalyzer:
    """Sistema de análisis automático de palabras clave para Competitive Intelligence"""
    
    def __init__(self, db_path: str = "news_database.db"):
        self.db_path = db_path
        
    def analyze_articles_for_keywords(self, competitor_name: str, limit: int = 1000) -> Dict:
        """
        Analiza artículos existentes para sugerir palabras clave automáticamente
        
        Args:
            competitor_name: Nombre del competidor a analizar
            limit: Número máximo de artículos a analizar
            
        Returns:
            Dict con sugerencias de palabras clave y su relevancia
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Buscar artículos que mencionen el competidor
            cursor.execute('''
                SELECT title, content, newspaper, url
                FROM articles 
                WHERE (title LIKE ? OR content LIKE ?)
                ORDER BY id DESC
                LIMIT ?
            ''', (f'%{competitor_name}%', f'%{competitor_name}%', limit))
            
            articles = cursor.fetchall()
            conn.close()
            
            if not articles:
                return self._get_fallback_suggestions(competitor_name)
            
            # Analizar contenido
            all_text = " ".join([f"{article[0]} {article[1]}" for article in articles])
            
            # Extraer palabras clave
            suggestions = self._extract_keywords(all_text, competitor_name)
            
            # Calcular relevancia
            suggestions = self._calculate_relevance(suggestions, articles)
            
            return {
                'success': True,
                'competitor': competitor_name,
                'articles_analyzed': len(articles),
                'suggestions': suggestions,
                'confidence': self._calculate_confidence(suggestions)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing articles: {e}")
            return self._get_fallback_suggestions(competitor_name)
    
    def _extract_keywords(self, text: str, competitor_name: str) -> List[Dict]:
        """Extrae palabras clave relevantes del texto"""
        
        # Limpiar texto
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        # Filtrar palabras comunes
        stop_words = {
            'el', 'la', 'de', 'del', 'en', 'con', 'por', 'para', 'un', 'una', 'los', 'las',
            'que', 'se', 'no', 'es', 'son', 'fue', 'ser', 'tiene', 'tienen', 'hace', 'hacen',
            'este', 'esta', 'estos', 'estas', 'su', 'sus', 'le', 'les', 'lo', 'al', 'más',
            'como', 'pero', 'sin', 'sobre', 'entre', 'durante', 'después', 'antes', 'muy',
            'todo', 'todos', 'toda', 'todas', 'cada', 'cual', 'cuando', 'donde', 'porque',
            'también', 'solo', 'solo', 'puede', 'pueden', 'debe', 'deben', 'dice', 'dicen'
        }
        
        # Filtrar palabras relevantes
        relevant_words = [
            word for word in words 
            if len(word) > 3 and word not in stop_words and word != competitor_name.lower()
        ]
        
        # Contar frecuencia
        word_counts = Counter(relevant_words)
        
        # Crear sugerencias
        suggestions = []
        for word, count in word_counts.most_common(50):
            if count >= 2:  # Solo palabras que aparecen al menos 2 veces
                suggestions.append({
                    'keyword': word,
                    'frequency': count,
                    'relevance_score': self._calculate_word_relevance(word, competitor_name),
                    'confidence': min(count / 10, 1.0)  # Normalizar confianza
                })
        
        return suggestions
    
    def _calculate_word_relevance(self, word: str, competitor_name: str) -> float:
        """Calcula la relevancia de una palabra para el competidor"""
        
        # Palabras relacionadas con deportes (para Liga 1)
        sports_keywords = {
            'futbol', 'fútbol', 'futbolista', 'jugador', 'equipo', 'partido', 'gol',
            'liga', 'campeonato', 'torneo', 'estadio', 'entrenador', 'directiva',
            'peruano', 'peruana', 'nacional', 'internacional', 'mundial', 'copa'
        }
        
        # Palabras relacionadas con empresas
        business_keywords = {
            'empresa', 'compañía', 'corporación', 'marca', 'producto', 'servicio',
            'ventas', 'mercado', 'cliente', 'usuario', 'consumidor', 'precio',
            'competencia', 'competidor', 'innovación', 'tecnología', 'digital'
        }
        
        word_lower = word.lower()
        
        # Verificar si es palabra relacionada con deportes
        if any(sport_word in word_lower for sport_word in sports_keywords):
            return 0.9
        
        # Verificar si es palabra relacionada con negocios
        if any(business_word in word_lower for business_word in business_keywords):
            return 0.8
        
        # Verificar si contiene el nombre del competidor
        if competitor_name.lower() in word_lower:
            return 0.95
        
        # Verificar si es palabra compuesta relevante
        if len(word) > 6 and any(char.isdigit() for char in word):
            return 0.7  # Palabras con números (ej: "liga1", "2024")
        
        # Relevancia base
        return 0.5
    
    def _calculate_relevance(self, suggestions: List[Dict], articles: List) -> List[Dict]:
        """Calcula la relevancia final de las sugerencias"""
        
        for suggestion in suggestions:
            keyword = suggestion['keyword']
            
            # Contar en cuántos artículos aparece
            article_count = 0
            for article in articles:
                if keyword.lower() in f"{article[0]} {article[1]}".lower():
                    article_count += 1
            
            # Calcular relevancia final
            suggestion['article_coverage'] = article_count / len(articles)
            suggestion['final_relevance'] = (
                suggestion['relevance_score'] * 0.4 +
                suggestion['confidence'] * 0.3 +
                suggestion['article_coverage'] * 0.3
            )
        
        # Ordenar por relevancia final
        suggestions.sort(key=lambda x: x['final_relevance'], reverse=True)
        
        return suggestions[:20]  # Top 20 sugerencias
    
    def _calculate_confidence(self, suggestions: List[Dict]) -> float:
        """Calcula la confianza general del análisis"""
        
        if not suggestions:
            return 0.0
        
        # Promedio de confianza de las top 5 sugerencias
        top_suggestions = suggestions[:5]
        avg_confidence = sum(s['confidence'] for s in top_suggestions) / len(top_suggestions)
        
        return min(avg_confidence, 1.0)
    
    def _get_fallback_suggestions(self, competitor_name: str) -> Dict:
        """Sugerencias de respaldo cuando no hay artículos"""
        
        # Sugerencias genéricas basadas en el nombre
        fallback_suggestions = []
        
        if 'liga' in competitor_name.lower():
            fallback_suggestions = [
                {'keyword': 'liga 1', 'frequency': 1, 'relevance_score': 0.9, 'confidence': 0.8},
                {'keyword': 'fútbol peruano', 'frequency': 1, 'relevance_score': 0.8, 'confidence': 0.7},
                {'keyword': 'primera división', 'frequency': 1, 'relevance_score': 0.8, 'confidence': 0.7},
                {'keyword': 'campeonato peruano', 'frequency': 1, 'relevance_score': 0.7, 'confidence': 0.6}
            ]
        else:
            # Sugerencias genéricas para empresas
            fallback_suggestions = [
                {'keyword': competitor_name.lower(), 'frequency': 1, 'relevance_score': 0.9, 'confidence': 0.8},
                {'keyword': f'{competitor_name.lower()} empresa', 'frequency': 1, 'relevance_score': 0.7, 'confidence': 0.6},
                {'keyword': f'{competitor_name.lower()} marca', 'frequency': 1, 'relevance_score': 0.7, 'confidence': 0.6}
            ]
        
        return {
            'success': True,
            'competitor': competitor_name,
            'articles_analyzed': 0,
            'suggestions': fallback_suggestions,
            'confidence': 0.6,
            'fallback': True
        }
    
    def get_smart_suggestions(self, competitor_name: str, existing_keywords: List[str] = None) -> Dict:
        """
        Obtiene sugerencias inteligentes considerando palabras clave existentes
        
        Args:
            competitor_name: Nombre del competidor
            existing_keywords: Palabras clave ya configuradas
            
        Returns:
            Dict con sugerencias nuevas y mejoradas
        """
        
        suggestions = []
        existing_keywords = existing_keywords or []
        
        # 1. Sugerencias basadas en base de datos de periódicos (PRIORIDAD ALTA)
        newspaper_suggestions = self._get_newspaper_based_suggestions(competitor_name)
        suggestions.extend(newspaper_suggestions)
        
        # 2. Sugerencias contextuales inteligentes (PRIORIDAD MEDIA)
        contextual_suggestions = self._get_contextual_suggestions(competitor_name)
        suggestions.extend(contextual_suggestions)
        
        # 3. Análisis de artículos existentes (PRIORIDAD BAJA - solo si hay artículos)
        analysis = self.analyze_articles_for_keywords(competitor_name)
        if analysis['success'] and analysis['articles_analyzed'] > 0:
            article_suggestions = analysis['suggestions']
            suggestions.extend(article_suggestions)
        
        # 4. Sugerencias complementarias
        complementary = self._get_complementary_suggestions(competitor_name, existing_keywords)
        suggestions.extend(complementary)
        
        # Filtrar sugerencias que ya existen
        existing_lower = [kw.lower() for kw in existing_keywords]
        new_suggestions = [
            s for s in suggestions 
            if s['keyword'].lower() not in existing_lower
        ]
        
        # Eliminar duplicados
        seen_keywords = set()
        unique_suggestions = []
        for suggestion in new_suggestions:
            keyword_lower = suggestion['keyword'].lower()
            if keyword_lower not in seen_keywords:
                seen_keywords.add(keyword_lower)
                unique_suggestions.append(suggestion)
        
        # Asegurar que todas las sugerencias tengan final_relevance
        for suggestion in unique_suggestions:
            if 'final_relevance' not in suggestion:
                suggestion['final_relevance'] = suggestion.get('relevance_score', 0.5)
        
        # Ordenar por relevancia
        unique_suggestions.sort(key=lambda x: x['final_relevance'], reverse=True)
        
        return {
            'success': True,
            'competitor': competitor_name,
            'articles_analyzed': analysis.get('articles_analyzed', 0),
            'suggestions': unique_suggestions[:15],  # Top 15 nuevas sugerencias
            'confidence': 'high' if newspaper_suggestions else 'medium',
            'existing_keywords': existing_keywords,
            'new_suggestions_count': len(unique_suggestions)
        }
    
    def get_auto_domain_and_keywords(self, competitor_name: str) -> Dict:
        """
        Obtiene automáticamente el dominio correcto y palabras clave para cualquier competidor
        
        Args:
            competitor_name: Nombre del competidor
            
        Returns:
            Dict con dominio y palabras clave automáticas
        """
        import sqlite3
        from collections import Counter
        import re
        
        # 1. Buscar en base de datos de periódicos conocidos
        if competitor_name in NEWSPAPER_DOMAINS:
            domain = NEWSPAPER_DOMAINS[competitor_name]
            keywords = NEWSPAPER_KEYWORDS.get(competitor_name, [])
            
            return {
                'success': True,
                'domain': domain,
                'keywords': keywords,
                'source': 'predefined',
                'confidence': 'high'
            }
        
        # 2. Buscar automáticamente en la base de datos de noticias
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Buscar periódicos similares
            cursor.execute('''
                SELECT DISTINCT newspaper, url 
                FROM articles 
                WHERE newspaper LIKE ? OR newspaper LIKE ?
                LIMIT 10
            ''', (f'%{competitor_name}%', f'%{competitor_name.lower()}%'))
            
            results = cursor.fetchall()
            
            if results:
                # Extraer dominio del primer resultado
                first_url = results[0][1]
                domain = first_url.split('/')[2]  # Extraer dominio
                
                # Analizar artículos para obtener palabras clave
                cursor.execute('''
                    SELECT title, content 
                    FROM articles 
                    WHERE newspaper = ?
                    LIMIT 50
                ''', (results[0][0],))
                
                articles = cursor.fetchall()
                
                if articles:
                    # Extraer palabras clave reales
                    all_text = ' '.join([f'{title} {content}' for title, content in articles])
                    words = re.findall(r'\b[a-zA-ZáéíóúñüÁÉÍÓÚÑÜ]{4,}\b', all_text.lower())
                    
                    # Filtrar palabras relevantes
                    stop_words = {'este', 'esta', 'estos', 'estas', 'para', 'con', 'por', 'que', 'como', 'más', 'muy', 'pero', 'sin', 'bajo', 'sobre', 'entre', 'hasta', 'desde', 'hacia', 'durante', 'mediante', 'según', 'aunque', 'mientras', 'donde', 'cuando', 'porque', 'aunque', 'también', 'solo', 'solo', 'tanto', 'cada', 'todo', 'toda', 'todos', 'todas', 'alguno', 'alguna', 'algunos', 'algunas', 'ninguno', 'ninguna', 'ningunos', 'ningunas', 'otro', 'otra', 'otros', 'otras', 'mismo', 'misma', 'mismos', 'mismas', 'tal', 'tales', 'cual', 'cuales', 'cuanto', 'cuanta', 'cuantos', 'cuantas', 'mucho', 'mucha', 'muchos', 'muchas', 'poco', 'poca', 'pocos', 'pocas', 'demasiado', 'demasiada', 'demasiados', 'demasiadas', 'bastante', 'bastantes', 'suficiente', 'suficientes', 'viernes', 'miércoles', 'jueves', 'martes', 'sábado', 'domingo', 'lunes', 'semana', 'día'}
                    
                    relevant_words = [word for word in words if word not in stop_words and len(word) > 3]
                    word_freq = Counter(relevant_words)
                    top_keywords = [word for word, freq in word_freq.most_common(10)]
                    
                    conn.close()
                    
                    return {
                        'success': True,
                        'domain': domain,
                        'keywords': top_keywords,
                        'source': 'auto_detected',
                        'confidence': 'medium',
                        'newspaper_found': results[0][0]
                    }
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error en detección automática: {e}")
        
        # 3. Fallback: usar nombre del competidor como palabra clave
        return {
            'success': True,
            'domain': f"{competitor_name.lower().replace(' ', '')}.com",
            'keywords': [competitor_name.lower()],
            'source': 'fallback',
            'confidence': 'low'
        }
    
    def _get_newspaper_based_suggestions(self, competitor_name: str) -> List[Dict]:
        """Obtener sugerencias basadas en la base de datos de periódicos"""
        suggestions = []
        
        # Buscar coincidencias exactas en nombres de periódicos
        for newspaper, keywords in NEWSPAPER_KEYWORDS.items():
            if competitor_name.lower() in newspaper.lower() or newspaper.lower() in competitor_name.lower():
                for keyword in keywords[:8]:  # Top 8 keywords
                    suggestions.append({
                        'keyword': keyword,
                        'relevance_score': 0.9,
                        'source': 'newspaper_database',
                        'reason': f'Palabra clave frecuente en {newspaper}'
                    })
        
        # Si no hay coincidencia exacta, buscar palabras relacionadas
        if not suggestions:
            competitor_words = competitor_name.lower().split()
            for newspaper, keywords in NEWSPAPER_KEYWORDS.items():
                for word in competitor_words:
                    if word in newspaper.lower():
                        for keyword in keywords[:5]:  # Top 5 keywords
                            suggestions.append({
                                'keyword': keyword,
                                'relevance_score': 0.7,
                                'source': 'related_newspaper',
                                'reason': f'Relacionado con {newspaper}'
                            })
                        break
        
        return suggestions
    
    def _get_contextual_suggestions(self, competitor_name: str) -> List[Dict]:
        """Generar sugerencias contextuales inteligentes"""
        suggestions = []
        
        # Sugerencias basadas en el tipo de competidor
        competitor_lower = competitor_name.lower()
        
        if any(word in competitor_lower for word in ['peru', 'perú', 'lima']):
            suggestions.extend([
                {'keyword': 'perú', 'relevance_score': 0.8, 'source': 'contextual', 'reason': 'País principal'},
                {'keyword': 'lima', 'relevance_score': 0.7, 'source': 'contextual', 'reason': 'Capital'},
                {'keyword': 'nacional', 'relevance_score': 0.6, 'source': 'contextual', 'reason': 'Ámbito nacional'}
            ])
        
        if any(word in competitor_lower for word in ['comercio', 'economía', 'negocios']):
            suggestions.extend([
                {'keyword': 'economía', 'relevance_score': 0.8, 'source': 'contextual', 'reason': 'Tema económico'},
                {'keyword': 'negocios', 'relevance_score': 0.7, 'source': 'contextual', 'reason': 'Sector empresarial'},
                {'keyword': 'mercado', 'relevance_score': 0.6, 'source': 'contextual', 'reason': 'Contexto comercial'}
            ])
        
        if any(word in competitor_lower for word in ['deportes', 'futbol', 'fútbol', 'selección']):
            suggestions.extend([
                {'keyword': 'deportes', 'relevance_score': 0.8, 'source': 'contextual', 'reason': 'Tema deportivo'},
                {'keyword': 'futbol', 'relevance_score': 0.7, 'source': 'contextual', 'reason': 'Deporte principal'},
                {'keyword': 'selección', 'relevance_score': 0.6, 'source': 'contextual', 'reason': 'Equipo nacional'}
            ])
        
        if any(word in competitor_lower for word in ['política', 'gobierno', 'congreso']):
            suggestions.extend([
                {'keyword': 'política', 'relevance_score': 0.8, 'source': 'contextual', 'reason': 'Tema político'},
                {'keyword': 'gobierno', 'relevance_score': 0.7, 'source': 'contextual', 'reason': 'Poder ejecutivo'},
                {'keyword': 'congreso', 'relevance_score': 0.6, 'source': 'contextual', 'reason': 'Poder legislativo'}
            ])
        
        # Sugerencias genéricas de alto valor
        suggestions.extend([
            {'keyword': 'noticias', 'relevance_score': 0.5, 'source': 'generic', 'reason': 'Término general'},
            {'keyword': 'actualidad', 'relevance_score': 0.5, 'source': 'generic', 'reason': 'Término general'},
            {'keyword': 'información', 'relevance_score': 0.4, 'source': 'generic', 'reason': 'Término general'}
        ])
        
        return suggestions

    def _get_complementary_suggestions(self, competitor_name: str, existing_keywords: List[str]) -> List[Dict]:
        """Genera sugerencias complementarias basadas en palabras clave existentes"""
        
        complementary = []
        
        for keyword in existing_keywords:
            keyword_lower = keyword.lower()
            
            # Para palabras relacionadas con fútbol
            if any(word in keyword_lower for word in ['liga', 'futbol', 'fútbol']):
                complementary.extend([
                    {'keyword': 'fútbol peruano', 'frequency': 1, 'relevance_score': 0.8, 'confidence': 0.7},
                    {'keyword': 'primera división', 'frequency': 1, 'relevance_score': 0.8, 'confidence': 0.7},
                    {'keyword': 'campeonato peruano', 'frequency': 1, 'relevance_score': 0.7, 'confidence': 0.6},
                    {'keyword': 'adfp', 'frequency': 1, 'relevance_score': 0.7, 'confidence': 0.6}
                ])
            
            # Para palabras relacionadas con empresas
            elif any(word in keyword_lower for word in ['empresa', 'marca', 'producto']):
                complementary.extend([
                    {'keyword': f'{competitor_name.lower()} corporación', 'frequency': 1, 'relevance_score': 0.7, 'confidence': 0.6},
                    {'keyword': f'{competitor_name.lower()} servicios', 'frequency': 1, 'relevance_score': 0.6, 'confidence': 0.5}
                ])
        
        return complementary

# Función de utilidad para usar desde otros módulos
def get_ai_suggestions(competitor_name: str, existing_keywords: List[str] = None) -> Dict:
    """Función de utilidad para obtener sugerencias de IA"""
    analyzer = AIKeywordAnalyzer()
    return analyzer.get_smart_suggestions(competitor_name, existing_keywords)
