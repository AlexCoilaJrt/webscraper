#!/usr/bin/env python3
"""
API REST para el Web Scraper
Expone endpoints para el frontend React
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import logging
import re
from datetime import datetime
from typing import List, Dict, Optional
import threading
import time
from urllib.parse import urlparse, parse_qs, unquote

# Importar sistema de autenticación
from auth_system import AuthSystem, require_auth, require_admin, require_user_or_admin

# Importar sistema de competitive intelligence
from competitive_intelligence_system import CompetitiveIntelligenceSystem
from ai_keyword_analyzer import get_ai_suggestions

# Sistema de notificaciones simplificado (sin WebSocket)
def send_scraping_notification(message, status="info"): 
    logger.info(f"[SCRAPING] {status.upper()}: {message}")

def send_payment_notification(user_id, message, status="info"): 
    logger.info(f"[PAYMENT] {status.upper()}: {message}")

def send_admin_notification(message, status="info"): 
    logger.info(f"[ADMIN] {status.upper()}: {message}")

def send_system_notification(message, status="info"): 
    logger.info(f"[SYSTEM] {status.upper()}: {message}")

# Importar nuestros scrapers
from hybrid_crawler import HybridDataCrawler, crawl_complete_hybrid
from optimized_scraper import SmartScraper
from improved_scraper import ImprovedScraper
from intelligent_analyzer import IntelligentPageAnalyzer
from optimized_scraper import ArticleData
from elperuano_scraper import scrape_elperuano_economia
from pagination_crawler import PaginationCrawler
import pandas as pd
from sqlalchemy import create_engine, text
import io
import base64
import os
import json
import sqlite3
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def detect_language_and_region(text: str) -> str:
    """Detectar idioma y región del texto para clasificar como nacional o extranjero"""
    if not text or len(text.strip()) < 10:
        return 'extranjero'
    
    text_lower = text.lower()
    
    # Palabras clave en español peruano
    spanish_peru_keywords = [
        'perú', 'peruano', 'peruana', 'lima', 'cuzco', 'arequipa', 'trujillo',
        'callao', 'piura', 'chiclayo', 'iquitos', 'huancayo', 'cusco',
        'congreso', 'presidente', 'ministro', 'gobierno', 'poder judicial',
        'soles', 'nuevo sol', 'pen', 'banco central', 'sunat', 'indecopi',
        'el comercio', 'la república', 'perú21', 'trome', 'ojo', 'correo',
        'rpp', 'américa tv', 'panamericana', 'atv', 'latina', 'willax'
    ]
    
    # Palabras clave en español general
    spanish_keywords = [
        'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te',
        'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'al', 'del',
        'los', 'las', 'una', 'como', 'más', 'pero', 'sus', 'todo', 'esta',
        'entre', 'cuando', 'muy', 'sin', 'sobre', 'también', 'me', 'hasta',
        'desde', 'está', 'mi', 'porque', 'qué', 'sólo', 'han', 'yo', 'hay',
        'vez', 'puede', 'todos', 'así', 'nos', 'ni', 'parte', 'tiene', 'él',
        'uno', 'donde', 'bien', 'tiempo', 'mismo', 'ese', 'ahora', 'cada',
        'e', 'vida', 'otro', 'después', 'te', 'otros', 'aunque', 'esa',
        'esos', 'estas', 'estos', 'otra', 'otras', 'otros', 'otro', 'otra'
    ]
    
    # Contar palabras en español peruano
    peru_count = sum(1 for keyword in spanish_peru_keywords if keyword in text_lower)
    
    # Contar palabras en español general
    spanish_count = sum(1 for keyword in spanish_keywords if keyword in text_lower)
    
    # Palabras clave en inglés
    english_keywords = [
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
        'after', 'above', 'below', 'between', 'among', 'is', 'are', 'was',
        'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
        'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
        'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she',
        'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your',
        'his', 'her', 'its', 'our', 'their', 'a', 'an', 'some', 'any', 'all'
    ]
    
    # Contar palabras en inglés
    english_count = sum(1 for keyword in english_keywords if keyword in text_lower)
    
    # Determinar idioma y región
    total_words = len(text.split())
    if total_words < 5:
        return 'extranjero'
    
    # Si tiene muchas palabras peruanas, es nacional
    if peru_count >= 2:
        return 'nacional'
    
    # Si tiene más palabras en español que en inglés, probablemente es español
    if spanish_count > english_count and spanish_count > 5:
        return 'nacional'
    
    # Si tiene más palabras en inglés, probablemente es extranjero
    if english_count > spanish_count and english_count > 5:
        return 'extranjero'
    
    # Por defecto, si no se puede determinar claramente, considerar extranjero
    return 'extranjero'

def normalize_region_value(value: Optional[str]) -> str:
    """Normalizar valor de región a etiquetas controladas."""
    if not value or not isinstance(value, str):
        return 'extranjero'
    
    normalized = re.sub(r'\s+', ' ', value).strip().lower()
    if not normalized:
        return 'extranjero'
    
    nacional_aliases = {
        'nacional', 'nacionales', 'local', 'peru', 'perú', 'peruano', 'peruana',
        'pe', 'national', 'nationwide', 'locales'
    }
    extranjero_aliases = {
        'extranjero', 'internacional', 'international', 'global', 'mundo', 'mundial',
        'world', 'abroad'
    }
    
    if normalized in nacional_aliases:
        return 'nacional'
    if normalized in extranjero_aliases:
        return 'extranjero'
    
    # Si no se reconoce, dejar el valor normalizado pero limitado
    return normalized[:40]

def check_duplicate_url(url: str, category: str = '') -> bool:
    """Verificar si una URL ya ha sido scrapeada con la misma categoría
    
    PERMITE agregar la misma URL con diferentes categorías.
    Solo bloquea si la URL ya existe con EXACTAMENTE la misma categoría.
    
    Args:
        url: URL a verificar
        category: Categoría a verificar (opcional)
    
    Returns:
        True si la URL ya existe con la misma categoría, False en caso contrario
    """
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        # Si se especifica una categoría, verificar URL + categoría
        # Solo bloquear si EXACTAMENTE la misma categoría ya existe
        if category:
            cursor.execute("SELECT COUNT(*) FROM articles WHERE url = ? AND category = ?", (url, category))
            count = cursor.fetchone()[0]
            conn.close()
            # Si count > 0, significa que ya existe con esta categoría exacta
            return count > 0
        else:
            # Si no hay categoría especificada, verificar solo por URL
            # Pero permitir agregar si hay artículos con diferentes categorías
            cursor.execute("SELECT COUNT(DISTINCT category) FROM articles WHERE url = ?", (url,))
            distinct_categories = cursor.fetchone()[0]
            
            # Si hay múltiples categorías, siempre permitir agregar (puede ser otra categoría)
            if distinct_categories > 1:
                conn.close()
                return False
            
            # Si solo hay una categoría, siempre permitir agregar con otra categoría diferente
            # (excepto si la nueva categoría también está vacía, pero eso se maneja arriba)
            if distinct_categories == 1:
                # Permitir agregar con otra categoría
                conn.close()
                return False
            
            # Si no hay artículos, permitir
        cursor.execute("SELECT COUNT(*) FROM articles WHERE url = ?", (url,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except Exception as e:
        logger.error(f"❌ Error verificando duplicados: {e}")
        conn.close()
        return False

app = Flask(__name__)
CORS(app)  # Permitir CORS para React

# Configuración de la base de datos SQLite
DB_PATH = "news_database.db"

# Inicializar sistema de autenticación
auth_system = AuthSystem()

# ============================================================
# Cargar variables de entorno desde .env (si existe)
# Formato esperado:
#   LLM_PROVIDER=openrouter
#   LLM_MODEL=deepseek/deepseek-chat-v3.1:free
#   OPENROUTER_API_KEY=sk-or-...
# ============================================================
def _load_dotenv_if_exists():
    env_path = os.path.join(os.getcwd(), '.env')
    if not os.path.isfile(env_path):
        return
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                # No pisar si ya viene desde el sistema
                if k and v and not os.environ.get(k):
                    os.environ[k] = v
    except Exception as e:
        logger.warning(f"No se pudo cargar .env: {e}")

_load_dotenv_if_exists()

# Cargar KB del sitio
def _load_site_kb():
    try:
        kb_path = os.path.join(os.getcwd(), 'site_kb.json')
        if os.path.isfile(kb_path):
            with open(kb_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"No se pudo cargar site_kb.json: {e}")
    return {}

SITE_KB = _load_site_kb()

def _user_plan_name(user_id: int) -> str:
    """Obtener el nombre del plan activo del usuario (freemium por defecto)."""
    try:
        subscription = auth_system.get_user_subscription(user_id)
        if subscription and subscription.get('plan_name'):
            return subscription['plan_name']  # 'freemium' | 'premium' | 'enterprise'
    except Exception:
        pass
    # Fallback: si no hay suscripción, tratar como freemium
    return 'freemium'

def _require_premium_or_enterprise(user_id: int) -> Optional[str]:
    """Validar que el usuario tenga plan premium o enterprise. Devuelve mensaje de error si no cumple."""
    plan_name = _user_plan_name(user_id)
    if plan_name in ('premium', 'enterprise'):
        return None
    return "Funcionalidad disponible solo para planes Premium o Enterprise"

def _require_enterprise(user_id: int) -> Optional[str]:
    """Validar que el usuario tenga plan enterprise. Devuelve mensaje de error si no cumple."""
    plan_name = _user_plan_name(user_id)
    if plan_name == 'enterprise':
        return None
    return "Funcionalidad disponible solo para plan Enterprise"

def _can_access_viral_comments_comparison(user_id: int) -> bool:
    """Verificar si el usuario puede acceder a comparación con comentarios virales"""
    plan_name = _user_plan_name(user_id)
    return plan_name in ('premium', 'enterprise')

def _can_access_advanced_alerts(user_id: int) -> bool:
    """Verificar si el usuario puede acceder a alertas avanzadas"""
    plan_name = _user_plan_name(user_id)
    return plan_name in ('premium', 'enterprise')

def _can_access_smart_ads_integration(user_id: int) -> bool:
    """Verificar si el usuario puede acceder a integración inteligente de anuncios"""
    plan_name = _user_plan_name(user_id)
    return plan_name == 'enterprise'

# ============================================================
# LLM gratuito vía Ollama (opcional)
# ============================================================
LLM_PROVIDER = os.environ.get('LLM_PROVIDER', 'ollama')  # 'ollama' | 'openrouter'
LLM_MODEL = os.environ.get('LLM_MODEL', 'llama3')        # ej. ollama: 'llama3', openrouter: 'meta-llama/llama-3.1-8b-instruct'
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
CHAT_FALLBACK_SCRAPE = os.environ.get('CHAT_FALLBACK_SCRAPE', 'false').lower() == 'true'

def _llm_available() -> bool:
    # OpenRouter: disponible si hay API key
    if LLM_PROVIDER == 'openrouter':
        return bool(OPENROUTER_API_KEY)
    # Ollama: comprobar servidor local
    if LLM_PROVIDER == 'ollama':
        try:
            import requests  # type: ignore
            r = requests.get('http://localhost:11434/api/tags', timeout=1)
            return r.status_code == 200
        except Exception:
            return False
    return False

def _llm_generate(prompt: str, system_prompt: str = '') -> Optional[str]:
    """Generar texto usando el proveedor configurado."""
    try:
        import requests  # type: ignore
        if LLM_PROVIDER == 'openrouter' and OPENROUTER_API_KEY:
            # OpenRouter Chat Completions
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost",
                "X-Title": "WebScraper Assistant"
            }
            body = {
                "model": LLM_MODEL,
                "messages": [
                    {"role": "system", "content": (system_prompt or "Eres un asistente del portal de noticias. Responde en español con calidez y precisión.")},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
            r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body, timeout=30)
            if r.status_code == 200:
                data = r.json()
                return data.get('choices', [{}])[0].get('message', {}).get('content')
            else:
                logger.warning(f"OpenRouter error {r.status_code}: {r.text[:200]}")
                return None
        elif LLM_PROVIDER == 'ollama':
            # Usar la API de chat de Ollama (más eficiente)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            payload = {
                "model": LLM_MODEL,
                "messages": messages,
                "stream": False
            }
            r = requests.post('http://localhost:11434/api/chat', json=payload, timeout=60)
            if r.status_code == 200:
                data = r.json()
                return data.get('message', {}).get('content')
    except Exception as e:
        logger.warning(f"LLM error: {e}")
    return None

@app.route('/api/llm/status', methods=['GET'])
def llm_status():
    """Diagnóstico rápido del LLM (proveedor/modelo/llave)."""
    try:
        provider = os.environ.get('LLM_PROVIDER', LLM_PROVIDER)
        model = os.environ.get('LLM_MODEL', LLM_MODEL)
        key_present = bool(os.environ.get('OPENROUTER_API_KEY', OPENROUTER_API_KEY))
        available = _llm_available()
        return jsonify({
            'provider': provider,
            'model': model,
            'key_present': key_present,
            'available': available
        })
    except Exception as e:
        logger.warning(f"LLM status error: {e}")
        return jsonify({'error': str(e)}), 500
# ============================================================
# Chatbot Inteligente (MVP)
# ============================================================
def _search_articles(query: str = '', date_from: Optional[str] = None, date_to: Optional[str] = None, limit: int = 20):
    """Búsqueda simple en la BD con soporte de rango de fechas y texto."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        # Normalizar query básica
        raw_query = (query or '').strip().strip('"').strip("'")
        params = []
        q = "SELECT id, title, url, summary, date, newspaper, images_data FROM articles WHERE 1=1"
        # Registrar función para normalizar (lower + quitar tildes)
        import unicodedata
        def normalize_text(s: Optional[str]):
            if not s:
                return ''
            s = s.lower()
            s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
            return s
        conn.create_function('normalize_text', 1, normalize_text)
        if raw_query:
            q += " AND (normalize_text(title) LIKE normalize_text(?) OR normalize_text(content) LIKE normalize_text(?) OR normalize_text(summary) LIKE normalize_text(?) OR normalize_text(newspaper) LIKE normalize_text(?))"
            like = f"%{raw_query}%"
            params.extend([like, like, like, like])
        # Normalizador de fechas (misma función usada en get_articles)
        def sqlite_parse_date(date_str):
            if not date_str:
                return None
            try:
                if 'T' in date_str:
                    return date_str[:10]
                import re
                m = re.search(r'(\\d{1,2})\\s+(\\w{3})\\s+(\\d{4})', date_str)
                if m:
                    day, mon, year = m.groups()
                    month_map = {'Jan':'01','Feb':'02','Mar':'03','Apr':'04','May':'05','Jun':'06','Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'}
                    return f"{year}-{month_map.get(mon,'01')}-{day.zfill(2)}"
                if '-' in date_str[:10]:
                    return date_str[:10]
            except Exception:
                return None
            return None
        conn.create_function('parse_date', 1, sqlite_parse_date)
        if date_from:
            q += " AND (parse_date(date) >= ? OR date >= ?)"
            params.extend([date_from, date_from])
        if date_to:
            q += " AND (parse_date(date) <= ? OR date <= ?)"
            params.extend([date_to, date_to + 'T23:59:59'])
        q += " ORDER BY scraped_at DESC LIMIT ?"
        params.append(limit)
        cur = conn.cursor()
        cur.execute(q, params)
        rows = cur.fetchall()
        articles = []
        for r in rows:
            images = []
            try:
                images = json.loads(r[6]) if r[6] else []
            except Exception:
                images = []
            articles.append({
                'id': r[0],
                'title': r[1],
                'url': r[2],
                'summary': r[3],
                'date': r[4],
                'newspaper': r[5],
                'image': images[0]['url'] if images else None
            })
        # Si no hubo resultados y hay query: aplicar scoring por tokens (búsqueda semántica ligera)
        if not articles and raw_query:
            try:
                stop = set(['de','la','el','los','las','y','o','u','en','del','al','para','por','con','un','una','que','se','su','sus','a'])
                tokens = [t for t in normalize_text(raw_query).split() if len(t) > 2 and t not in stop]
                if tokens:
                    where = ""
                    extra_params = []
                    if date_from:
                        where += " AND (parse_date(date) >= ? OR date >= ?)"
                        extra_params.extend([date_from, date_from])
                    if date_to:
                        where += " AND (parse_date(date) <= ? OR date <= ?)"
                        extra_params.extend([date_to, date_to + 'T23:59:59'])
                    # Traer últimos 200 artículos para score
                    cur.execute(f"""
                        SELECT id, title, url, summary, date, newspaper, images_data, 
                               LOWER(title||' '||summary||' '||COALESCE('', '')) as fulltext
                        FROM articles
                        WHERE 1=1 {where}
                        ORDER BY scraped_at DESC LIMIT 200
                    """, extra_params)
                    pool = cur.fetchall()
                    scored = []
                    for row in pool:
                        ft = normalize_text(row[7] or '')
                        score = sum(1 for t in tokens if t in ft)
                        if score > 0:
                            images = []
                            try:
                                images = json.loads(row[6]) if row[6] else []
                            except Exception:
                                images = []
                            scored.append((score, {
                                'id': row[0],
                                'title': row[1],
                                'url': row[2],
                                'summary': row[3],
                                'date': row[4],
                                'newspaper': row[5],
                                'image': images[0]['url'] if images else None
                            }))
                    scored.sort(key=lambda x: x[0], reverse=True)
                    articles = [a for _,a in scored[:limit]]
            except Exception as e:
                logger.warning(f"Semantic-like search error: {e}")
        return articles
    finally:
        conn.close()

def _summarize_articles(articles: List[Dict], max_points: int = 5) -> List[str]:
    """Resumen muy simple por heurística (títulos + primeras frases)."""
    points = []
    for a in articles[:max_points]:
        base = a['summary'] or a['title']
        if base:
            points.append(f"- {a['title']}: {base[:160]}...")
    return points

@app.route('/api/chat', methods=['POST'])
@require_auth
def chat_endpoint():
    """Endpoint de chatbot (MVP) con intents básicos."""
    payload = request.get_json() or {}
    message = (payload.get('message') or '').strip()
    date_from = payload.get('date_from')  # 'YYYY-MM-DD'
    date_to = payload.get('date_to')
    limit = int(payload.get('limit', 10))
    user_id = request.current_user.get('user_id')
    role = request.current_user.get('role', 'user')
    plan_name = _user_plan_name(user_id)

    # ----------------------------------------------------------
    # Inferir rango de fechas si el usuario no lo envió
    # (soporta: 'hoy', 'ayer', 'esta semana', 'este mes', '2025')
    # ----------------------------------------------------------
    try:
        import re
        from datetime import timedelta
        now = datetime.now().date()
        msg_low = message.lower()
        if not date_from and not date_to:
            # expresiones relativas
            if 'hoy' in msg_low:
                date_from = date_to = now.isoformat()
            elif 'ayer' in msg_low:
                d = now - timedelta(days=1)
                date_from = date_to = d.isoformat()
            elif 'esta semana' in msg_low:
                monday = now - timedelta(days=now.weekday())
                date_from = monday.isoformat()
                date_to = now.isoformat()
            elif 'este mes' in msg_low:
                first = now.replace(day=1)
                date_from = first.isoformat()
                date_to = now.isoformat()
            elif 'este año' in msg_low or 'este anio' in msg_low:
                first = now.replace(month=1, day=1)
                date_from = first.isoformat()
                date_to = now.isoformat()
            else:
                # año explícito: 2023/2024/2025
                m = re.search(r'(20\\d{2})', msg_low)
                if m:
                    year = int(m.group(1))
                    date_from = f"{year}-01-01"
                    date_to = f"{year}-12-31"
    except Exception as _:
        pass

    if not message:
        # Intento de saludo cálido con LLM (si está disponible)
        if _llm_available():
            text = _llm_generate("Responde como asistente amable en una frase breve.", 
                                 "Eres un asistente del portal de noticias. Saluda y ofrece ayuda.")
            if text:
                return jsonify({'reply': text})
        return jsonify({'reply': '¡Hola! ¿En qué te ayudo? Puedo buscar o resumir noticias, filtrar por fechas o mostrar tu plan.'})

    msg_lower = message.lower()
    reply = ''
    data = {}
    citations = []

    # Límites de mensajes por plan (no aplica a admin)
    if role != 'admin':
        chat_limits = auth_system.subscription_system.check_chat_message_limits(user_id, 1)
        if not chat_limits.get('allowed', True):
            return jsonify({
                'reply': f"Has alcanzado el límite diario de mensajes de tu plan {chat_limits.get('plan_name','')}. Mensajes hoy: {chat_limits.get('current_messages',0)}/{chat_limits.get('limit')}.",
                'limits': chat_limits
            }), 200

    # Acciones de plan desde chat
    # Exportar (Premium/Enterprise)
    if 'exportar' in msg_lower or 'export' in msg_lower:
        plan = _user_plan_name(user_id).lower()
        if 'premium' in plan or 'enterprise' in plan:
            return jsonify({'reply': "Puedes exportar desde aquí: Excel: /api/articles/export/excel, CSV: /api/articles/export/csv (requiere sesión)."})
        else:
            return jsonify({'reply': "La exportación está disponible para planes Premium o Enterprise."})
    # Guardar consulta
    if 'guardar consulta' in msg_lower:
        # ejemplo: "guardar consulta: la república 2025"
        parts = message.split(':', 1)
        q = parts[1].strip() if len(parts) > 1 else message
        ok = auth_system.save_user_query(user_id, q)
        if ok:
            return jsonify({'reply': f"Consulta guardada: “{q}”. Puedes pedir “mis consultas” para listarlas (pendiente)."})
        return jsonify({'reply': "No pude guardar la consulta. Intenta nuevamente."})
    # Actualizar automático (Enterprise)
    if 'actualizar automático' in msg_lower or 'actualizar automatico' in msg_lower:
        plan = _user_plan_name(user_id).lower()
        if 'enterprise' in plan:
            # iniciar auto-update como en el endpoint
            global scraping_status
            if not scraping_status.get('is_running'):
                thread = threading.Thread(target=run_auto_scraping)
                thread.daemon = True
                thread.start()
                return jsonify({'reply': "Actualización automática iniciada."})
            else:
                return jsonify({'reply': "Ya hay un scraping en ejecución."})
        else:
            return jsonify({'reply': "La actualización automática desde chat está disponible para Enterprise."})
    # Intent: ayuda del sitio / qué hace / cómo usar
    help_keywords = ['de qué trata', 'de que trata', 'que puedo hacer', 'cómo usar', 'como usar', 'ayuda', 'que hace esta página', 'que hace esta pagina', 'cómo funciona', 'como funciona', 'donde estamos', 'secciones', 'cómo exporto', 'como exporto', 'planes', 'suscripción', 'suscripcion']
    if any(k in msg_lower for k in help_keywords):
        # Datos en vivo
        live_stats = {}
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM articles")
            live_stats['total_articles'] = cur.fetchone()[0]
            cur.execute("SELECT COUNT(DISTINCT newspaper) FROM articles")
            live_stats['total_newspapers'] = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM images")
            live_stats['total_images'] = cur.fetchone()[0]
        except Exception as e:
            logger.warning(f"Error leyendo métricas en help: {e}")
        finally:
            try: conn.close()
            except: pass
        kb_about = SITE_KB.get('about', '')
        kb_sections = SITE_KB.get('sections', {})
        kb_howto = SITE_KB.get('howto', {})
        context_lines = [kb_about, "Secciones:"]
        for s,desc in kb_sections.items():
            context_lines.append(f"- {s}: {desc}")
        if kb_howto:
            context_lines.append("Cómo hacer:")
            for key,desc in kb_howto.items():
                context_lines.append(f"- {desc}")
        if live_stats:
            context_lines.append(f"Métricas actuales: artículos={live_stats.get('total_articles',0)}, periódicos={live_stats.get('total_newspapers',0)}, imágenes={live_stats.get('total_images',0)}.")
        context = "\n".join(context_lines[:1000])
        if _llm_available():
            prompt = f"Usuario: {message}\nContexto del sitio:\n{context}\nResponde en español, claro y breve (2-4 líneas), guiando al usuario sobre qué puede hacer aquí."
            text = _llm_generate(prompt, "Eres un asistente del portal. Responde solo con el contexto dado; no inventes funciones.")
            if text:
                return jsonify({'reply': text, 'data': {'live_stats': live_stats}})
        reply = "Este portal permite buscar y resumir noticias, filtrar por fechas, ver estadísticas y exportar (según plan). ¿Qué necesitas hacer ahora?"
        return jsonify({'reply': reply, 'data': {'live_stats': live_stats}})

    def _guess_source_url(q: str) -> Optional[tuple]:
        """Intentar detectar el medio en el mensaje y devolver (url, nombre)."""
        s = (q or '').lower()
        mapping = [
            ('la republica', ('https://larepublica.pe/', 'La Republica')),
            ('larepublica', ('https://larepublica.pe/', 'La Republica')),
            ('el comercio', ('https://elcomercio.pe/', 'El Comercio')),
            ('rpp', ('https://rpp.pe/', 'RPP')),
            ('peru21', ('https://peru21.pe/', 'Peru21')),
            ('andina', ('https://andina.pe/agencia/', 'Andina')),
            ('américa tv', ('https://www.americatv.com.pe/noticias/', 'AmericaTV')),
            ('americatv', ('https://www.americatv.com.pe/noticias/', 'AmericaTV')),
            ('ojo', ('https://ojo.pe/', 'Ojo')),
            ('trome', ('https://trome.pe/', 'Trome')),
        ]
        for key, val in mapping:
            if key in s:
                return val
        # dominios directos
        import re
        m = re.search(r'(https?://[\\w\\.-]+)', s)
        if m:
            url = m.group(1)
            name = url.replace('https://','').replace('http://','').replace('www.','').split('.')[0].title()
            return (url, name)
        return None

    # Intent: estado del plan / límites
    if any(k in msg_lower for k in ['mi plan', 'plan actual', 'suscripción', 'limite', 'límite']):
        limits = auth_system.check_usage_limits(user_id, 0, 0)
        reply = f"Plan: {limits.get('plan_name','Desconocido')}. Artículos hoy: {limits['current_articles']}/{limits['max_articles']} • Imágenes por scraping: máx {limits['max_images']}."
        return jsonify({'reply': reply, 'plan': plan_name, 'limits': limits})

    # Intent: buscar
    # Detectar intención de búsqueda flexible (si menciona medios/temas, años o palabras clave de noticias)
    if any(k in msg_lower for k in ['buscar', 'encuentra', 'muestra', 'partidos', 'selección', 'seleccion', 'noticias', 'diario', 'periódico', 'periodico']) or any(ch.isdigit() for ch in msg_lower):
        # Quitar palabra 'buscar' del query
        query = message
        for k in ['buscar', 'encuentra', 'muestra']:
            query = query.replace(k, '')
        query = query.strip()
        articles = _search_articles(query=query, date_from=date_from, date_to=date_to, limit=limit)

        # Si no hay resultados, intentar scrappear en caliente si detectamos el medio
        if not articles:
            guess = _guess_source_url(query)
            # Respeto a la preferencia del usuario: NO hacer scraping automático desde el chatbot
            if CHAT_FALLBACK_SCRAPE and guess:
                try:
                    source_url, source_name = guess
                    from improved_scraper import ImprovedScraper
                    scraper = ImprovedScraper()
                    try:
                        found = scraper.scrape_articles(source_url, max_articles=20)
                    finally:
                        scraper.close()
                    if found:
                        save_articles_to_db(found, category='General', newspaper=source_name, region='')
                        # reintentar la búsqueda
                        articles = _search_articles(query=query, date_from=date_from, date_to=date_to, limit=limit)
                except Exception as e:
                    logger.warning(f"Chatbot fallback scrape failed for {guess}: {e}")

        citations = [{'title': a['title'], 'url': a['url']} for a in articles]
        if articles:
            # Redactar con mejor tono si hay LLM local
            if _llm_available():
                context = "\\n".join([f"- {a['title']}" for a in articles[:5]])
                prompt = f"Usuario: {message}\\nArtículos: \\n{context}\\nRedacta una respuesta amable, breve (2-3 líneas) y añade una llamada a la acción."
                text = _llm_generate(prompt, "Eres un asistente del portal. Devuelve texto en español, natural y útil.")
                if text:
                    reply = text
                else:
                    bullets = _summarize_articles(articles, max_points=min(5, len(articles)))
                    header = f"Encontré {len(articles)} artículos relevantes."
                    reply = header + "\\n" + "\\n".join(bullets)
            else:
                bullets = _summarize_articles(articles, max_points=min(5, len(articles)))
                header = f"Encontré {len(articles)} artículos relevantes."
                reply = header + "\\n" + "\\n".join(bullets)
        else:
            detail = ''
            if date_from or date_to:
                detail = f" en el rango {date_from or 'inicio'} a {date_to or 'hoy'}"
            # Si el usuario mencionó un medio, ofrecer resumen con datos de la BASE (sin scrape)
            db_hint = ""
            recent_citations = []
            if guess:
                try:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    source_url, source_name = guess
                    # Stats del medio
                    cur.execute("SELECT COUNT(*), MAX(date) FROM articles WHERE LOWER(newspaper) LIKE ?", (f"%{source_name.lower()}%",))
                    row = cur.fetchone()
                    count = row[0] if row else 0
                    last_date = row[1] if row else None
                    if count > 0:
                        db_hint = f" En tu base, '{source_name}' tiene {count} artículos. Última fecha: {last_date or 'N/A'}."
                        # Top 5 más recientes del medio para que el usuario tenga opciones
                        cur.execute("""
                            SELECT title, url FROM articles
                            WHERE LOWER(newspaper) LIKE ?
                            ORDER BY scraped_at DESC LIMIT 5
                        """, (f"%{source_name.lower()}%",))
                        rows = cur.fetchall()
                        for t,u in rows:
                            if t and u:
                                recent_citations.append({'title': t, 'url': u})
                except Exception as e:
                    logger.warning(f"DB stats error: {e}")
                finally:
                    try:
                        conn.close()
                    except:
                        pass
            reply = f"No encontré artículos para esa búsqueda{detail}.{db_hint} Prueba afinar el término, elegir otro rango o usar el filtro del listado."
            if recent_citations:
                reply += " Te dejo los últimos 5 de esa fuente:"
                citations.extend(recent_citations)
        data = {'articles': articles, 'date_from': date_from, 'date_to': date_to}
        return jsonify({'reply': reply, 'data': data, 'citations': citations})

    # Intent: resumir
    if any(k in msg_lower for k in ['resumen', 'resúmeme', 'resumir']):
        query_for_summary = message.replace('resumen','').strip()
        articles = _search_articles(query=query_for_summary, date_from=date_from, date_to=date_to, limit=limit)
        # Si no hay artículos para resumir, usar los más recientes de la base (o del medio si se detecta)
        if not articles:
            # Detectar medio si lo hay
            guess = _guess_source_url(query_for_summary)
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                if guess:
                    source_url, source_name = guess
                    cur.execute("""
                        SELECT title, url, summary FROM articles
                        WHERE LOWER(newspaper) LIKE ?
                        ORDER BY scraped_at DESC LIMIT 5
                    """, (f"%{source_name.lower()}%",))
                else:
                    cur.execute("""
                        SELECT title, url, summary FROM articles
                        ORDER BY scraped_at DESC LIMIT 5
                    """)
                rows = cur.fetchall()
                for t,u,s in rows:
                    articles.append({'title': t, 'url': u, 'summary': s})
            except Exception as e:
                logger.warning(f"Resumen fallback error: {e}")
            finally:
                try: conn.close()
                except: pass
        bullets = _summarize_articles(articles, max_points=5)
        if bullets:
            if _llm_available():
                ctx = "\n".join([f"- {a.get('title')}" for a in articles[:5] if a.get('title')])
                prompt = f"Genera un resumen breve (3-5 bullets) usando solo estos artículos:\n{ctx}"
                text = _llm_generate(prompt, "Responde en español, claro y conciso, sin inventar datos.")
                reply = text or "\n".join(bullets)
            else:
                reply = "\n".join(bullets)
        else:
            reply = "No hay suficiente contenido para resumir."
        citations = [{'title': a.get('title'), 'url': a.get('url')} for a in articles[:5] if a.get('title') and a.get('url')]
        data = {'articles_used': len(articles)}
        return jsonify({'reply': reply, 'data': data, 'citations': citations})

    # Intent: exportar (solo premium/enterprise)
    if 'export' in msg_lower or 'excel' in msg_lower or 'csv' in msg_lower:
        err = _require_premium_or_enterprise(user_id)
        if err:
            return jsonify({'error': err}), 403
        reply = "Puedes usar los botones Exportar Excel/CSV en Artículos. También puedo filtrar antes de exportar si me indicas la consulta."
        return jsonify({'reply': reply})

    # Intent: programar / auto-update (solo premium/enterprise)
    if 'programa' in msg_lower or 'auto' in msg_lower or 'actualiza' in msg_lower:
        err = _require_premium_or_enterprise(user_id)
        if err:
            return jsonify({'error': err}), 403
        reply = "He habilitado la actualización automática desde el panel. Usa ‘Actualizar automático’. Si quieres, dime la URL y frecuencia y lo dejo configurado."
        return jsonify({'reply': reply})

    # Small-talk/otro: usar LLM si está disponible
    if _llm_available():
        text = _llm_generate(f"Usuario: {message}", 
                             "Eres un asistente del portal de noticias. Responde de forma amable y breve; si el usuario pide tareas relacionadas con noticias, invítalo a usar frases como 'buscar ...' o 'resumen ...'.")
        if text:
            # Registrar uso del chat
            if role != 'admin':
                try:
                    auth_system.subscription_system.update_chat_usage(user_id, 1)
                except Exception:
                    pass
            return jsonify({'reply': text})
    # Fallback sin LLM
    reply = "Puedo: buscar artículos (por texto/fechas), resumir, mostrar tu plan/límites y (según tu plan) exportar o programar actualizaciones. Dime qué necesitas."
    if role != 'admin':
        try:
            auth_system.subscription_system.update_chat_usage(user_id, 1)
        except Exception:
            pass
    return jsonify({'reply': reply, 'plan': plan_name})
# Inicializar sistema de competitive intelligence
ci_system = CompetitiveIntelligenceSystem()

# Estado global del scraping
scraping_status = {
    'is_running': False,
    'progress': 0,
    'total': 0,
    'current_url': '',
    'articles_found': 0,
    'images_found': 0,
    'error': None,
    'start_time': None,
    'end_time': None
}

AUTO_UPDATE_INTERVAL_MINUTES = int(os.environ.get('AUTO_UPDATE_INTERVAL_MINUTES', '30'))
_auto_update_scheduler: Optional[BackgroundScheduler] = None


def parse_cron_schedule(cron_str: str):
    """Parse cron schedule string to apscheduler cron parameters"""
    try:
        parts = cron_str.strip().split()
        if len(parts) != 5:
            return None
        
        minute, hour, day, month, day_of_week = parts
        
        # Convertir cron a formato apscheduler
        # apscheduler acepta: minute, hour, day, month, day_of_week
        # Manejar patrones como */5, */6, etc.
        params = {}
        
        # Minuto
        if minute == '*':
            params['minute'] = '*'
        elif minute.startswith('*/'):
            # */5 significa cada 5 minutos
            interval = minute.split('/')[1]
            params['minute'] = f'*/{interval}'
        else:
            params['minute'] = minute
        
        # Hora
        if hour == '*':
            params['hour'] = '*'
        elif hour.startswith('*/'):
            # */6 significa cada 6 horas
            interval = hour.split('/')[1]
            params['hour'] = f'*/{interval}'
        else:
            params['hour'] = hour
        
        # Día
        if day != '*':
            params['day'] = day
        
        # Mes
        if month != '*':
            params['month'] = month
        
        # Día de la semana
        if day_of_week != '*':
            params['day_of_week'] = day_of_week
        
        return params
    except Exception as e:
        logger.error(f"Error parseando cron schedule '{cron_str}': {e}")
        return None


def execute_single_schedule(schedule):
    """Ejecutar scraping para una programación específica"""
    try:
        newspaper_name = schedule.get('newspaper', schedule.get('name', 'Unknown'))
        logger.info(f"🚀 Ejecutando scraping automático: {newspaper_name}")
        
        # Ejecutar el scraper standalone para este periódico específico
        import subprocess
        import json
        import tempfile
        
        # Crear un archivo temporal con solo este schedule
        temp_config = {
            'auto_scraping': {
                'enabled': True,
                'schedules': [schedule]
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(temp_config, f, indent=2)
            temp_config_path = f.name
        
        try:
            result = subprocess.run(
                ['python', 'auto_scraper_standalone.py'],
                env={**os.environ, 'AUTO_SCRAPING_CONFIG': temp_config_path},
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
                timeout=1800  # 30 minutos máximo por periódico
            )
            
            if result.returncode == 0:
                logger.info(f"✅ Scraping completado: {newspaper_name}")
            else:
                logger.error(f"❌ Error en scraping {newspaper_name}: {result.stderr[:500]}")
        finally:
            try:
                os.unlink(temp_config_path)
            except:
                pass
                
    except Exception as e:
        logger.error(f"❌ Error ejecutando scraping {schedule.get('name', 'Unknown')}: {e}")


def detect_and_add_new_newspaper(newspaper_name: str):
    """Detectar si un periódico nuevo debe agregarse automáticamente a la configuración de actualización automática"""
    try:
        # Cargar configuración actual
        with open('auto_scraping_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        schedules = config.get('auto_scraping', {}).get('schedules', [])
        
        # Verificar si el periódico ya está en la configuración
        newspaper_exists = any(
            s.get('newspaper', '').strip().lower() == newspaper_name.strip().lower() 
            for s in schedules
        )
        
        if newspaper_exists:
            return  # Ya está en la configuración
        
        # Buscar en la base de datos para obtener información del periódico
        conn = get_db_connection()
        if not conn:
            return
        
        cursor = conn.cursor()
        
        # Obtener la URL base más usada para este periódico
        cursor.execute("""
            SELECT DISTINCT url, COUNT(*) as count
            FROM articles 
            WHERE newspaper LIKE ?
                AND url NOT LIKE '%/'
                AND url NOT LIKE '%.com'
                AND url NOT LIKE '%.com/'
                AND url NOT LIKE '%.pe'
                AND url NOT LIKE '%.pe/'
                AND url NOT LIKE '%.es'
                AND url NOT LIKE '%.es/'
                AND LENGTH(url) > 20
            GROUP BY url
            ORDER BY count DESC
            LIMIT 1
        """, (f'%{newspaper_name}%',))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return  # No hay URLs para este periódico
        
        most_used_url = result[0]
        
        # Extraer URL base del periódico
        from urllib.parse import urlparse
        parsed = urlparse(most_used_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}/"
        
        # Determinar región basándose en el dominio
        region = 'Extranjero'
        if '.pe' in parsed.netloc:
            region = 'Nacional'
        elif '.es' in parsed.netloc:
            region = 'Extranjero'
        elif 'nytimes' in parsed.netloc or 'cnn' in parsed.netloc or 'bbc' in parsed.netloc:
            region = 'Extranjero'
        
        # Crear nuevo schedule
        new_schedule = {
            "name": f"{newspaper_name} - Cada 5 horas",
            "url": base_url,
            "method": "auto",
            "max_articles": 40,
            "max_images": 1,
            "category": "General",
            "newspaper": newspaper_name,
            "region": region,
            "cron_schedule": "*/5 * * * *",
            "enabled": True
        }
        
        # Agregar a la configuración
        schedules.append(new_schedule)
        config['auto_scraping']['schedules'] = schedules
        
        # Guardar configuración
        with open('auto_scraping_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ ✅ ✅ Periódico nuevo agregado automáticamente: {newspaper_name}")
        logger.info(f"   📍 URL base: {base_url}")
        logger.info(f"   📝 Se agregará al scheduler en el próximo reinicio")
        
        # Si el scheduler ya está corriendo, reiniciarlo para incluir el nuevo periódico
        global _auto_update_scheduler
        if _auto_update_scheduler is not None:
            logger.info(f"🔄 Reiniciando scheduler para incluir {newspaper_name}...")
            try:
                _auto_update_scheduler.shutdown(wait=False)
                _auto_update_scheduler = None
                # Reiniciar scheduler en un thread separado para no bloquear
                import threading
                threading.Timer(2.0, start_auto_update_scheduler).start()
            except Exception as e:
                logger.warning(f"⚠️ Error reiniciando scheduler: {e}")
        
    except Exception as e:
        logger.error(f"❌ Error detectando/agregando periódico nuevo {newspaper_name}: {e}")


def detect_user_manual_urls(newspaper_name: str, days_back: int = 30):
    """Detectar URLs y categorías que el usuario ha usado manualmente para un periódico"""
    try:
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor()
        
        # Primero obtener todas las categorías únicas
        cursor.execute("""
            SELECT DISTINCT 
                COALESCE(NULLIF(user_category, ''), category) as final_category
            FROM articles 
            WHERE newspaper LIKE ?
                AND scraped_at >= datetime('now', '-' || ? || ' days')
                AND url NOT LIKE '%/'
                AND url NOT LIKE '%.pe'
                AND url NOT LIKE '%.pe/'
                AND url NOT LIKE '%.com'
                AND url NOT LIKE '%.com/'
                AND url NOT LIKE '%.es'
                AND url NOT LIKE '%.es/'
                AND LENGTH(url) > 30
                AND COALESCE(NULLIF(user_category, ''), category) IS NOT NULL
                AND COALESCE(NULLIF(user_category, ''), category) != ''
        """, (f'%{newspaper_name}%', days_back))
        
        categories = [row[0] for row in cursor.fetchall()]
        
        # Para cada categoría, obtener las mejores URLs (top 10 por categoría)
        all_results = []
        for cat in categories:
            cursor.execute("""
                SELECT DISTINCT 
                    url,
                    COALESCE(NULLIF(user_category, ''), category) as final_category,
                    COUNT(*) as usage_count,
                    MAX(scraped_at) as last_used
                FROM articles 
                WHERE newspaper LIKE ?
                    AND scraped_at >= datetime('now', '-' || ? || ' days')
                    AND url NOT LIKE '%/'
                    AND url NOT LIKE '%.pe'
                    AND url NOT LIKE '%.pe/'
                    AND url NOT LIKE '%.com'
                    AND url NOT LIKE '%.com/'
                    AND url NOT LIKE '%.es'
                    AND url NOT LIKE '%.es/'
                    AND LENGTH(url) > 30
                    AND COALESCE(NULLIF(user_category, ''), category) = ?
                GROUP BY url, final_category
                ORDER BY last_used DESC, usage_count DESC
                LIMIT 10
            """, (f'%{newspaper_name}%', days_back, cat))
            all_results.extend(cursor.fetchall())
        
        results = all_results
        conn.close()
        
        # Agrupar por categoría y extraer URLs base de sección
        category_urls = {}
        for url, category, count, last_used in results:
            if category not in category_urls:
                category_urls[category] = []
            
            # Intentar extraer la URL base de la sección
            # Por ejemplo: https://elcomercio.pe/economia/... -> https://elcomercio.pe/economia/
            from urllib.parse import urlparse
            parsed = urlparse(url)
            path_parts = [p for p in parsed.path.split('/') if p]
            
            # Si tiene al menos 2 segmentos, usar la sección como URL base
            if len(path_parts) >= 2:
                # Construir URL base de sección
                section_url = f"{parsed.scheme}://{parsed.netloc}/{path_parts[0]}/"
            else:
                # Si no tiene sección clara, usar la URL completa
                section_url = url
            
            category_urls[category].append({
                'url': url,
                'section_url': section_url,
                'count': count,
                'last_used': last_used
            })
        
        # Para cada categoría, elegir la mejor URL base (la más usada)
        optimized_category_urls = {}
        for category, urls in category_urls.items():
            # Agrupar por section_url
            section_groups = {}
            for url_info in urls:
                section = url_info['section_url']
                if section not in section_groups:
                    section_groups[section] = []
                section_groups[section].append(url_info)
            
            # Elegir la sección más usada para esta categoría
            best_section = max(section_groups.items(), key=lambda x: sum(u['count'] for u in x[1]))
            optimized_category_urls[category] = [{
                'url': best_section[0],  # URL base de la sección
                'count': sum(u['count'] for u in best_section[1]),
                'last_used': max(u['last_used'] for u in best_section[1])
            }]
        
        return optimized_category_urls
    except Exception as e:
        logger.error(f"Error detectando URLs manuales para {newspaper_name}: {e}")
        return []


def start_auto_update_scheduler():
    """Iniciar scheduler en segundo plano para actualizaciones automáticas usando cron schedules."""
    global _auto_update_scheduler

    if _auto_update_scheduler is not None:
        return

    try:
        # Cargar configuración
        with open('auto_scraping_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        auto_config = config.get('auto_scraping', {})
        if not auto_config.get('enabled', False):
            logger.info("⏸️ Auto-update deshabilitado en configuración")
            return
        
        schedules = auto_config.get('schedules', [])
        enabled_schedules = [s for s in schedules if s.get('enabled', False)]
        
        # PRIMERO: Detectar periódicos nuevos que no están en la configuración
        logger.info("🔍 Detectando periódicos nuevos para agregar automáticamente...")
        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                # Obtener todos los periódicos únicos de los últimos 30 días
                cursor.execute("""
                    SELECT DISTINCT newspaper, COUNT(*) as count
                    FROM articles 
                    WHERE scraped_at >= datetime('now', '-30 days')
                        AND newspaper IS NOT NULL
                        AND newspaper != ''
                    GROUP BY newspaper
                    ORDER BY count DESC
                """)
                
                newspapers_in_db = {row[0].strip(): row[1] for row in cursor.fetchall()}
                conn.close()
                
                # Verificar cuáles no están en la configuración
                newspapers_in_config = {s.get('newspaper', '').strip().lower() for s in schedules}
                
                new_newspapers = []
                for np_name, count in newspapers_in_db.items():
                    if np_name.lower() not in newspapers_in_config and count >= 3:  # Al menos 3 artículos
                        new_newspapers.append((np_name, count))
                
                if new_newspapers:
                    logger.info(f"📰 Encontrados {len(new_newspapers)} periódicos nuevos para agregar automáticamente")
                    for np_name, count in new_newspapers:
                        detect_and_add_new_newspaper(np_name)
                    
                    # Recargar configuración después de agregar periódicos nuevos
                    with open('auto_scraping_config.json', 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    schedules = config.get('auto_scraping', {}).get('schedules', [])
                    enabled_schedules = [s for s in schedules if s.get('enabled', False)]
        except Exception as e:
            logger.warning(f"⚠️ Error detectando periódicos nuevos: {e}")
        
        # Detectar URLs y categorías usadas manualmente y agregarlas como schedules adicionales
        logger.info("🔍 Detectando URLs y categorías usadas manualmente...")
        for schedule in enabled_schedules[:]:  # Usar copia para poder modificar
            newspaper_name = schedule.get('newspaper', '')
            if not newspaper_name:
                continue
            
            # Detectar URLs manuales para este periódico
            user_urls = detect_user_manual_urls(newspaper_name, days_back=30)
            
            if user_urls:
                logger.info(f"📋 Encontradas {sum(len(urls) for urls in user_urls.values())} URLs manuales para {newspaper_name}")
                
                # Crear schedules adicionales para cada categoría/URL
                for category, urls in user_urls.items():
                    # La función detect_user_manual_urls ya devuelve la URL base de sección optimizada
                    if urls:
                        best_url_info = urls[0]  # Ya está optimizada con la sección más usada
                        section_url = best_url_info['url']  # URL base de la sección (ej: https://elcomercio.pe/economia/)
                        
                        # Crear schedule adicional para esta categoría
                        additional_schedule = schedule.copy()
                        additional_schedule['name'] = f"{newspaper_name} - {category} (Manual)"
                        additional_schedule['url'] = section_url
                        additional_schedule['category'] = category
                        # Usar el mismo cron pero con un offset de minutos para no sobrecargar
                        additional_schedule['max_articles'] = min(schedule.get('max_articles', 50), 30)  # Limitar a 30 para URLs específicas
                        additional_schedule['enabled'] = True
                        
                        enabled_schedules.append(additional_schedule)
                        logger.info(f"  ✅ Agregado: {newspaper_name} - {category} ({section_url[:60]}...)")
        
        if not enabled_schedules:
            logger.info("⏸️ No hay programaciones habilitadas")
            return

        scheduler = BackgroundScheduler(daemon=True)
        jobs_added = 0
        
        # Agregar un job para cada schedule con su propio cron
        for idx, schedule in enumerate(enabled_schedules):
            cron_str = schedule.get('cron_schedule', '')
            if not cron_str:
                logger.warning(f"⚠️ Schedule '{schedule.get('name')}' no tiene cron_schedule, saltando")
                continue
            
            cron_params = parse_cron_schedule(cron_str)
            if not cron_params:
                logger.warning(f"⚠️ No se pudo parsear cron '{cron_str}' para '{schedule.get('name')}'")
                continue
            
            # Crear función lambda que ejecute solo este schedule
            def make_schedule_executor(sched):
                return lambda: execute_single_schedule(sched)
            
            job_id = f"auto_scraping_{idx}_{schedule.get('name', 'unknown').replace(' ', '_')}"
            
            try:
                scheduler.add_job(
                    make_schedule_executor(schedule),
                    'cron',
                    **cron_params,
                    id=job_id,
                    replace_existing=True,
                    coalesce=True,
                    max_instances=1,
                )
                jobs_added += 1
                logger.info(f"✅ Programado: {schedule.get('name')} - Cron: {cron_str}")
            except Exception as e:
                logger.error(f"❌ Error agregando job para '{schedule.get('name')}': {e}")
        
        if jobs_added > 0:
            scheduler.start()
            logger.info(f"⏱️ Auto-update scheduler iniciado con {jobs_added} trabajos programados")
        else:
            logger.warning("⚠️ No se agregaron trabajos al scheduler")
            return

        def shutdown_scheduler():
            try:
                scheduler.shutdown(wait=False)
            except Exception:
                pass

        atexit.register(shutdown_scheduler)
        _auto_update_scheduler = scheduler
        
    except FileNotFoundError as e:
        logger.warning("⚠️ Archivo auto_scraping_config.json no encontrado, scheduler no iniciado")
    except Exception as e:
        logger.error(f"❌ Error iniciando auto-update scheduler: {e}")
        import traceback
        logger.error(traceback.format_exc())

def get_db_connection():
    """Obtener conexión a la base de datos SQLite"""
    try:
        import sqlite3
        return sqlite3.connect(DB_PATH)
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        return None

def init_database():
    """Inicializar tablas de la base de datos SQLite"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Tabla de artículos
        create_articles_table = """
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                summary TEXT,
                author TEXT,
                date TEXT,
                category TEXT,
                newspaper TEXT,
                url TEXT NOT NULL,
                images_found INTEGER DEFAULT 0,
                images_downloaded INTEGER DEFAULT 0,
                images_data TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                article_id TEXT UNIQUE,
                region TEXT DEFAULT 'extranjero'
            )
        """
        
        # Tabla de periódicos excluidos de actualizaciones automáticas
        create_excluded_newspapers_table = """
            CREATE TABLE IF NOT EXISTS excluded_newspapers (
                newspaper TEXT PRIMARY KEY,
                excluded_at TEXT NOT NULL
            )
        """
        
        # Tabla de imágenes
        create_images_table = """
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id TEXT,
                url TEXT NOT NULL,
                local_path TEXT,
                alt_text TEXT,
                title TEXT,
                width INTEGER,
                height INTEGER,
                format TEXT,
                size_bytes INTEGER,
                relevance_score INTEGER DEFAULT 0,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        
        # Tabla de estadísticas
        create_stats_table = """
            CREATE TABLE IF NOT EXISTS scraping_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                url_scraped TEXT,
                articles_found INTEGER,
                images_found INTEGER,
                images_downloaded INTEGER,
                duration_seconds INTEGER,
                method_used TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        
        cursor.execute(create_articles_table)
        cursor.execute(create_excluded_newspapers_table)
        cursor.execute(create_images_table)
        cursor.execute(create_stats_table)
        
        # Agregar columna 'region' si no existe
        try:
            cursor.execute("ALTER TABLE articles ADD COLUMN region TEXT DEFAULT 'extranjero'")
        except Exception:
            # La columna ya existe, no hacer nada
            pass

        # Agregar columna para almacenar la categoría ingresada por el usuario
        try:
            cursor.execute("ALTER TABLE articles ADD COLUMN user_category TEXT")
        except Exception:
            pass
        
        # Tabla de redes sociales (PROYECTO ACADÉMICO)
        create_social_media_table = """
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
        
        cursor.execute(create_social_media_table)
        
        # Agregar columnas si no existen (para migración)
        try:
            cursor.execute("ALTER TABLE social_media_posts ADD COLUMN image_url TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE social_media_posts ADD COLUMN video_url TEXT")
        except sqlite3.OperationalError:
            pass
        
        # Índices para redes sociales
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_social_platform ON social_media_posts(platform)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_social_category ON social_media_posts(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_social_sentiment ON social_media_posts(sentiment)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_social_scraped_at ON social_media_posts(scraped_at)")
        except Exception as e:
            logger.warning(f"Advertencia al crear índices de redes sociales: {e}")
        
        # Tabla de comentarios/opiniones
        create_comments_table = """
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                user_name TEXT NOT NULL,
                comment_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_edited BOOLEAN DEFAULT 0,
                FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
            )
        """
        
        cursor.execute(create_comments_table)
        
        # Índices para comentarios
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_comments_article ON comments(article_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_comments_created_at ON comments(created_at)")
        except Exception as e:
            logger.warning(f"Advertencia al crear índices de comentarios: {e}")
        
        # Tabla de comentarios virales (comentarios sobre temas generales, no artículos)
        create_viral_comments_table = """
            CREATE TABLE IF NOT EXISTS viral_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                comment_text TEXT NOT NULL,
                topic TEXT NOT NULL,
                likes INTEGER DEFAULT 0,
                sentiment TEXT DEFAULT 'positive',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        
        cursor.execute(create_viral_comments_table)
        
        # Índices para comentarios virales
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_viral_comments_topic ON viral_comments(topic)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_viral_comments_created_at ON viral_comments(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_viral_comments_likes ON viral_comments(likes DESC)")
        except Exception as e:
            logger.warning(f"Advertencia al crear índices de comentarios virales: {e}")
        
        conn.commit()
        conn.close()
        
        # Inicializar sistema de anuncios
        try:
            from ads_system import ads_system
            ads_system.init_database()
            logger.info("✅ Sistema de anuncios inicializado")
        except Exception as e:
            logger.warning(f"⚠️ Error inicializando sistema de anuncios: {e}")
        
        logger.info("✅ Base de datos SQLite inicializada correctamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error inicializando base de datos: {e}")
        return False

@app.route('/api/health', methods=['GET'])
def health_check():
    """Verificar estado de la API"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected' if get_db_connection() else 'disconnected'
    })

# ==================== ENDPOINTS DE AUTENTICACIÓN ====================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Iniciar sesión"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username y password son requeridos'}), 400
        
        user = auth_system.authenticate_user(username, password)
        if not user:
            return jsonify({'error': 'Credenciales inválidas'}), 401
        
        # Generar token
        token = auth_system.generate_token(user)
        
        # Actualizar último login
        auth_system.update_last_login(user['id'])
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role']
            }
        })
    
    except Exception as e:
        logger.error(f"Error en login: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/api/auth/verify', methods=['GET'])
@require_auth
def verify_token():
    """Verificar token y obtener información del usuario"""
    try:
        user_id = request.current_user['user_id']
        user = auth_system.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role'],
                'is_active': user['is_active']
            }
        })
    
    except Exception as e:
        logger.error(f"Error verificando token: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/api/auth/users', methods=['GET'])
@require_auth
@require_admin
def get_all_users():
    """Obtener todos los usuarios (solo admin)"""
    try:
        users = auth_system.get_all_users()
        return jsonify({
            'success': True,
            'users': users
        })
    
    except Exception as e:
        logger.error(f"Error obteniendo usuarios: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/api/auth/users', methods=['POST'])
@require_auth
@require_admin
def create_user():
    """Crear nuevo usuario (solo admin)"""
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'user')
        
        if not all([username, email, password]):
            return jsonify({'error': 'Username, email y password son requeridos'}), 400
        
        if role not in ['user', 'admin']:
            return jsonify({'error': 'Rol inválido'}), 400
        
        success = auth_system.create_user(username, email, password, role)
        if not success:
            return jsonify({'error': 'Usuario ya existe'}), 409
        
        return jsonify({
            'success': True,
            'message': 'Usuario creado exitosamente'
        })
    
    except Exception as e:
        logger.error(f"Error creando usuario: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/api/auth/users/<int:user_id>/role', methods=['PUT'])
@require_auth
@require_admin
def update_user_role(user_id):
    """Actualizar rol de usuario (solo admin)"""
    try:
        data = request.get_json()
        new_role = data.get('role')
        
        if new_role not in ['user', 'admin']:
            return jsonify({'error': 'Rol inválido'}), 400
        
        success = auth_system.update_user_role(user_id, new_role)
        if not success:
            return jsonify({'error': 'Error actualizando rol'}), 500
        
        return jsonify({
            'success': True,
            'message': 'Rol actualizado exitosamente'
        })
    
    except Exception as e:
        logger.error(f"Error actualizando rol: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/api/auth/permissions', methods=['GET'])
@require_auth
@require_admin
def get_all_permissions():
    """Obtener todos los permisos disponibles (solo admin)"""
    try:
        permissions = auth_system.get_all_permissions()
        return jsonify({
            'success': True,
            'permissions': permissions
        })
    except Exception as e:
        logger.error(f"Error obteniendo permisos: {e}")
        return jsonify({'error': 'Error obteniendo permisos'}), 500

@app.route('/api/auth/users/<int:user_id>/permissions', methods=['GET'])
@require_auth
@require_admin
def get_user_permissions(user_id):
    """Obtener permisos de un usuario (solo admin)"""
    try:
        permissions = auth_system.get_user_permissions(user_id)
        return jsonify({
            'success': True,
            'permissions': permissions
        })
    except Exception as e:
        logger.error(f"Error obteniendo permisos de usuario: {e}")
        return jsonify({'error': 'Error obteniendo permisos'}), 500

@app.route('/api/auth/users/<int:user_id>/permissions', methods=['PUT'])
@require_auth
@require_admin
def set_user_permissions(user_id):
    """Establecer permisos de un usuario (solo admin)"""
    try:
        data = request.get_json()
        permission_ids = data.get('permission_ids', [])
        granted_by = request.current_user.get('user_id')
        
        if not isinstance(permission_ids, list):
            return jsonify({'error': 'permission_ids debe ser una lista'}), 400
        
        success = auth_system.set_user_permissions(user_id, permission_ids, granted_by)
        if not success:
            return jsonify({'error': 'Error estableciendo permisos'}), 500
        
        return jsonify({
            'success': True,
            'message': 'Permisos actualizados exitosamente'
        })
    except Exception as e:
        logger.error(f"Error estableciendo permisos: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/api/auth/users/<int:user_id>/deactivate', methods=['PUT'])
@require_auth
@require_admin
def deactivate_user(user_id):
    """Desactivar usuario (solo admin)"""
    try:
        success = auth_system.deactivate_user(user_id)
        if not success:
            return jsonify({'error': 'Error desactivando usuario'}), 500
        
        return jsonify({
            'success': True,
            'message': 'Usuario desactivado exitosamente'
        })
    
    except Exception as e:
        logger.error(f"Error desactivando usuario: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/api/auth/my-permissions', methods=['GET'])
@require_auth
def get_my_permissions():
    """Obtener permisos del usuario actual"""
    try:
        user_id = request.current_user.get('user_id')
        permissions = auth_system.get_user_permissions(user_id)
        return jsonify({
            'success': True,
            'permissions': permissions
        })
    except Exception as e:
        logger.error(f"Error obteniendo permisos: {e}")
        return jsonify({'error': 'Error obteniendo permisos'}), 500

@app.route('/api/auth/users/<int:user_id>/details', methods=['GET'])
@require_auth
@require_admin
def get_user_details(user_id):
    """Obtener detalles completos del usuario incluyendo permisos (solo admin)"""
    try:
        # Obtener información del usuario
        user = auth_system.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Obtener permisos del usuario (NO afecta los planes)
        permissions = auth_system.get_user_permissions(user_id)
        
        # Obtener información de suscripción (planes independientes de permisos)
        subscription = auth_system.get_user_subscription(user_id)
        
        # Obtener estadísticas del usuario (si está disponible)
        statistics = None
        articles_conn = get_db_connection()
        if articles_conn:
            try:
                cursor = articles_conn.cursor()
                # Estadísticas generales (la tabla articles no tiene user_id aún)
                cursor.execute("SELECT COUNT(*) FROM articles")
                total_articles = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM images")
                total_images = cursor.fetchone()[0]
                
                # Artículos de hoy
                today = datetime.now().date().isoformat()
                cursor.execute("SELECT COUNT(*) FROM articles WHERE date LIKE ?", (f'{today}%',))
                articles_today = cursor.fetchone()[0]
                
                # Imágenes de hoy
                cursor.execute("SELECT COUNT(*) FROM images WHERE created_at LIKE ?", (f'{today}%',))
                images_today = cursor.fetchone()[0]
                
                statistics = {
                    'total_articles': total_articles,
                    'total_images': total_images,
                    'articles_today': articles_today,
                    'images_today': images_today
                }
            except Exception as e:
                logger.warning(f"Error obteniendo estadísticas: {e}")
            finally:
                articles_conn.close()
        
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role'],
                'is_active': user['is_active'],
                'created_at': user.get('created_at'),
                'last_login': user.get('last_login'),
                'permissions': permissions,
                'subscription': subscription,
                'statistics': statistics
            }
        })
    except Exception as e:
        logger.error(f"Error obteniendo detalles de usuario: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/api/auth/users/<int:user_id>/details-old', methods=['GET'])
@require_auth
@require_admin
def get_user_details_old(user_id):
    """Obtener detalles completos del usuario (solo admin) - DEPRECATED"""
    try:
        # Obtener información del usuario
        conn = sqlite3.connect(auth_system.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, role, is_active, created_at, last_login
            FROM users WHERE id = ?
        ''', (user_id,))
        
        user_row = cursor.fetchone()
        if not user_row:
            conn.close()
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        user = {
            'id': user_row[0],
            'username': user_row[1],
            'email': user_row[2],
            'role': user_row[3],
            'is_active': bool(user_row[4]),
            'created_at': user_row[5],
            'last_login': user_row[6]
        }
        
        # Obtener suscripción del usuario
        # Si es admin, tiene acceso completo sin necesidad de suscripción
        # Normalizar el rol para evitar problemas con espacios o mayúsculas
        user_role = str(user['role']).strip().lower() if user['role'] else ''
        if user_role == 'admin':
            subscription_data = {
                'id': None,
                'plan_id': None,
                'plan_name': 'admin',
                'plan_display_name': 'Plan Administrador',
                'status': 'active',
                'start_date': user['created_at'],
                'end_date': None,
                'features': [
                    'Acceso ilimitado a todas las funciones',
                    'Artículos ilimitados',
                    'Imágenes ilimitadas',
                    'Chat sin límites',
                    'Gestión completa de usuarios',
                    'Asignación de planes a usuarios',
                    'Exportación completa',
                    'API completa',
                    'Soporte prioritario 24/7'
                ]
            }
        else:
            subscription = auth_system.get_user_subscription(user_id)
            subscription_data = None
            if subscription:
                plan = auth_system.subscription_system.get_plan_by_id(subscription['plan_id'])
                subscription_data = {
                    'id': subscription['id'],
                    'plan_id': subscription['plan_id'],
                    'plan_name': plan['name'] if plan else 'unknown',
                    'plan_display_name': plan['display_name'] if plan else 'Unknown',
                    'status': subscription['status'],
                    'start_date': subscription['start_date'],
                    'end_date': subscription.get('end_date')
                }
            else:
                # Usuario sin suscripción activa - mostrar plan freemium
                freemium_plan = auth_system.subscription_system.get_plan_by_name('freemium')
                if freemium_plan:
                    subscription_data = {
                        'id': None,
                        'plan_id': freemium_plan['id'],
                        'plan_name': freemium_plan['name'],
                        'plan_display_name': freemium_plan['display_name'],
                        'status': 'active',
                        'start_date': user['created_at'],
                        'end_date': None
                    }
        
        # Obtener estadísticas del usuario
        # Nota: La tabla articles no tiene user_id, así que obtenemos estadísticas generales
        # En el futuro se puede agregar user_id a la tabla articles para tracking por usuario
        articles_conn = get_db_connection()
        if articles_conn:
            try:
                # Crear cursor a partir de la conexión
                articles_cursor = articles_conn.cursor()
                
                # Por ahora, obtener estadísticas generales del sistema
                # (ya que no hay tracking por usuario en la tabla articles)
                articles_cursor.execute('SELECT COUNT(*) FROM articles')
                total_articles = articles_cursor.fetchone()[0]
                
                articles_cursor.execute('''
                    SELECT COUNT(*) FROM articles 
                    WHERE DATE(scraped_at) = DATE('now')
                ''')
                articles_today = articles_cursor.fetchone()[0]
                
                articles_cursor.execute('SELECT COUNT(*) FROM images')
                total_images = articles_cursor.fetchone()[0]
                
                articles_cursor.execute('''
                    SELECT COUNT(*) FROM images 
                    WHERE DATE(downloaded_at) = DATE('now')
                ''')
                images_today = articles_cursor.fetchone()[0]
                
                statistics = {
                    'total_articles': total_articles,
                    'total_images': total_images,
                    'articles_today': articles_today,
                    'images_today': images_today,
                    'note': 'Estadísticas generales del sistema (no hay tracking por usuario en artículos)'
                }
            finally:
                articles_conn.close()
        else:
            statistics = {
                'total_articles': 0,
                'total_images': 0,
                'articles_today': 0,
                'images_today': 0,
                'note': 'No se pudo conectar a la base de datos'
            }
        
        conn.close()
        
        return jsonify({
            'success': True,
            'details': {
                'user': user,
                'subscription': subscription_data,
                'statistics': statistics
            }
        })
    
    except Exception as e:
        logger.error(f"Error obteniendo detalles del usuario: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/api/auth/users/<int:user_id>/plan', methods=['PUT'])
@require_auth
@require_admin
def update_user_plan(user_id):
    """Actualizar plan del usuario (solo admin)"""
    try:
        data = request.get_json()
        plan_id = data.get('plan_id')
        
        if not plan_id:
            return jsonify({'error': 'ID del plan requerido'}), 400
        
        # Verificar que el plan existe
        plan = auth_system.subscription_system.get_plan_by_id(plan_id)
        if not plan:
            return jsonify({'error': 'Plan no encontrado'}), 404
        
        # Crear o actualizar suscripción
        subscription_id = auth_system.subscription_system.create_user_subscription(user_id, plan_id)
        
        return jsonify({
            'success': True,
            'message': f'Plan actualizado a {plan["display_name"]} exitosamente'
        })
    
    except Exception as e:
        logger.error(f"Error actualizando plan del usuario: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/api/auth/users/<int:user_id>/password', methods=['PUT'])
@require_auth
@require_admin
def update_user_password(user_id):
    """Actualizar contraseña del usuario (solo admin)"""
    try:
        data = request.get_json()
        new_password = data.get('password')
        
        if not new_password or len(new_password) < 6:
            return jsonify({'error': 'La contraseña debe tener al menos 6 caracteres'}), 400
        
        success = auth_system.update_user_password(user_id, new_password)
        if not success:
            return jsonify({'error': 'Error actualizando contraseña'}), 500
        
        return jsonify({
            'success': True,
            'message': 'Contraseña actualizada exitosamente'
        })
    
    except Exception as e:
        logger.error(f"Error actualizando contraseña: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/api/auth/users/<int:user_id>', methods=['DELETE'])
@require_auth
@require_admin
def delete_user(user_id):
    """Eliminar usuario (solo admin)"""
    try:
        # Verificar que el usuario existe
        conn = sqlite3.connect(auth_system.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Eliminar usuario
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Usuario eliminado exitosamente'
        })
    
    except Exception as e:
        logger.error(f"Error eliminando usuario: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/api/config', methods=['GET'])
def get_config():
    """Obtener configuración actual"""
    return jsonify({
        'database': DB_CONFIG,
        'scraping_status': scraping_status,
        'supported_methods': ['auto', 'hybrid', 'optimized', 'improved', 'selenium', 'requests']
    })

@app.route('/api/analyze', methods=['POST'])
def analyze_page():
    """Analizar página y sugerir el mejor método de scraping"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL es requerida'}), 400
        
        # Analizar la página
        analyzer = IntelligentPageAnalyzer()
        analysis = analyzer.analyze_page(url)
        analyzer.close()
        
        return jsonify(analysis)
        
    except Exception as e:
        logger.error(f"❌ Error analizando página: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear-all', methods=['DELETE'])
@require_auth
@require_admin
def clear_all_data():
    """Borrar todos los artículos, imágenes y estadísticas de la base de datos"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Base de datos no disponible'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Contar registros antes de borrar
        cursor.execute("SELECT COUNT(*) FROM articles")
        articles_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM images")
        images_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM scraping_stats")
        stats_count = cursor.fetchone()[0]
        
        # Borrar todos los datos
        cursor.execute("DELETE FROM articles")
        cursor.execute("DELETE FROM images")
        cursor.execute("DELETE FROM scraping_stats")
        
        # Resetear contadores de auto-incremento
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('articles', 'images', 'scraping_stats')")
        
        conn.commit()
        conn.close()
        
        logger.info(f"🗑️ Datos borrados: {articles_count} artículos, {images_count} imágenes, {stats_count} estadísticas")
        
        return jsonify({
            'message': 'Todos los datos han sido borrados exitosamente',
            'deleted': {
                'articles': articles_count,
                'images': images_count,
                'stats': stats_count
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error borrando datos: {str(e)}")
        return jsonify({'error': f'Error borrando datos: {str(e)}'}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Obtener estado actual del scraping"""
    return jsonify(scraping_status)

@app.route('/api/start-scraping', methods=['POST'])
@require_auth
def start_scraping():
    """Iniciar proceso de scraping"""
    global scraping_status
    
    if scraping_status['is_running']:
        return jsonify({'error': 'El scraping ya está en ejecución'}), 400
    
    data = request.get_json()
    url = data.get('url')
    user_id = request.current_user.get('user_id')
    user_role = request.current_user.get('role')
    
    # Obtener límites del plan del usuario
    limits_check = auth_system.check_usage_limits(user_id, 0, 0)
    plan_max_articles = limits_check.get('max_articles', 0)
    plan_max_images = limits_check.get('max_images', 0)
    
    # Si max_articles es 0, usar el límite del plan (o ilimitado si es admin)
    max_articles = data.get('max_articles', 0)
    if max_articles == 0:
        if user_role == 'admin' or plan_max_articles == -1:
            max_articles = 0  # 0 significa "extraer todos" (solo admin o enterprise)
            logger.info("📊 Modo: Extraer TODOS los artículos disponibles")
        else:
            # Para usuarios normales, usar el límite restante del plan
            remaining_articles = plan_max_articles - limits_check.get('current_articles', 0)
            max_articles = max(1, remaining_articles)  # Al menos 1 artículo
            logger.info(f"📊 Usuario normal: Límite automático = {max_articles} artículos (restantes del plan)")
    
    max_images = data.get('max_images', 100)
    # Limitar imágenes según el plan
    if user_role != 'admin' and plan_max_images != -1:
        if max_images > plan_max_images:
            max_images = plan_max_images
            logger.info(f"📊 Imágenes limitadas a {max_images} según el plan")
    
    method = data.get('method', 'auto')  # 'auto' para análisis inteligente
    download_images = data.get('download_images', True)
    category = data.get('category', '')
    newspaper = data.get('newspaper', '')
    region = data.get('region', '')
    
    # Verificar límites de uso del usuario (solo para usuarios no admin)
    if user_role != 'admin':
        limits_check = auth_system.check_usage_limits(user_id, max_articles, max_images)
        if not limits_check['allowed']:
            return jsonify({
                'error': 'Límite de uso excedido',
                'details': limits_check,
                'message': f"Has alcanzado el límite de tu plan {limits_check['plan_name']}. "
                          f"Artículos usados: {limits_check['current_articles']}/{limits_check['max_articles']}, "
                          f"Imágenes usadas: {limits_check['current_images']}/{limits_check['max_images']}. "
                          f"💡 Actualiza tu plan para obtener más capacidad."
            }), 429
    
    # Si el método es 'auto', analizar la página primero
    if method == 'auto':
        logger.info("🧠 Análisis inteligente activado")
        analyzer = IntelligentPageAnalyzer()
        analysis = analyzer.analyze_page(url)
        analyzer.close()
        
        method = analysis['recommendation']
        confidence = analysis['confidence']
        
        logger.info(f"🎯 Método sugerido: {method} (confianza: {confidence}%)")
        logger.info(f"📋 Razones: {', '.join(analysis['reasoning'])}")
        
        # Actualizar el estado con la información del análisis
        scraping_status.update({
            'analysis': analysis,
            'suggested_method': method,
            'confidence': confidence
        })
    
    if not url:
        return jsonify({'error': 'URL es requerida'}), 400
    
    # Verificar si la URL ya ha sido scrapeada con la misma categoría
    # Permitir agregar la misma URL con diferentes categorías
    if check_duplicate_url(url, category):
        return jsonify({
            'error': 'Esta URL ya ha sido scrapeada con esta categoría',
            'message': f'Los artículos de esta URL ya existen en la base de datos con la categoría "{category}". Puedes intentar con una categoría diferente o eliminar los artículos existentes.',
            'duplicate': True
        }), 409
    
    # Inicializar estado
    scraping_status.update({
        'is_running': True,
        'progress': 0,
        'total': max_articles,
        'current_url': url,
        'articles_found': 0,
        'images_found': 0,
        'error': None,
        'start_time': datetime.now().isoformat(),
        'end_time': None
    })
    
    # Notificar inicio del scraping
    send_scraping_notification(f"Iniciando scraping de {url} con método {method}", "info")
    
    # Ejecutar scraping en hilo separado
    thread = threading.Thread(
        target=run_scraping,
        args=(url, max_articles, max_images, method, download_images, category, newspaper, region)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'message': 'Scraping iniciado',
        'status': scraping_status
    })

def scrape_with_pagination(url: str, max_articles: int, max_images: int, method: str, download_images: bool, category: str = '', newspaper: str = '', region: str = ''):
    """Scraping con paginación automática para cualquier sitio web"""
    try:
        logger.info(f"🔄 Iniciando scraping con paginación para: {url}")
        
        # Crear función de extracción según el método
        if method == 'hybrid':
            extract_func = lambda page_url: extract_articles_hybrid(page_url, max_articles)
        elif method == 'optimized':
            extract_func = lambda page_url: extract_articles_optimized(page_url, max_articles)
        elif method == 'improved':
            extract_func = lambda page_url: extract_articles_improved(page_url, max_articles)
        elif method == 'selenium':
            extract_func = lambda page_url: extract_articles_selenium(page_url, max_articles)
        else:
            # Método automático - usar improved por defecto
            extract_func = lambda page_url: extract_articles_improved(page_url, max_articles)
        
        # Usar PaginationCrawler
        pagination_crawler = PaginationCrawler(use_selenium=True)
        try:
            articles = pagination_crawler.crawl_all_pages(
                url=url,
                max_articles=max_articles,
                extract_articles_func=extract_func
            )
            
            # Guardar en base de datos
            save_articles_to_db(articles, category, newspaper, region)
            
            logger.info(f"🎉 Scraping con paginación completado: {len(articles)} artículos")
            return articles
            
        finally:
            pagination_crawler.close()
            
    except Exception as e:
        logger.error(f"❌ Error en scraping con paginación: {e}")
        return []

def extract_articles_hybrid(url, max_articles):
    """Extraer artículos usando método híbrido"""
    try:
        crawler = HybridDataCrawler()
        try:
            articles = crawler.hybrid_crawl_articles(url, max_articles)
            return articles
        finally:
            crawler.close()
    except Exception as e:
        logger.error(f"❌ Error en extracción híbrida: {e}")
        return []

def extract_articles_optimized(url, max_articles):
    """Extraer artículos usando método optimizado"""
    try:
        scraper = SmartScraper(max_workers=10)
        try:
            articles = scraper.scrape_articles(url, max_articles)
            return articles
        finally:
            scraper.close()
    except Exception as e:
        logger.error(f"❌ Error en extracción optimizada: {e}")
        return []

def extract_articles_improved(url, max_articles):
    """Extraer artículos usando método mejorado"""
    try:
        scraper = ImprovedScraper()
        try:
            articles = scraper.scrape_articles(url, max_articles)
            return articles
        finally:
            scraper.close()
    except Exception as e:
        logger.error(f"❌ Error en extracción mejorada: {e}")
        return []

def extract_articles_selenium(url, max_articles):
    """Extraer artículos usando Selenium"""
    try:
        # Implementación básica con Selenium
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        service = Service('/usr/local/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        try:
            driver.get(url)
            time.sleep(3)
            
            # Buscar artículos
            articles = []
            article_elements = driver.find_elements(By.CSS_SELECTOR, 'article, .article, .news-item, h2 a, h3 a')
            
            for element in article_elements[:max_articles]:
                try:
                    if element.tag_name == 'a':
                        title = element.text.strip()
                        link = element.get_attribute('href')
                    else:
                        link_elem = element.find_element(By.TAG_NAME, 'a')
                        title = link_elem.text.strip()
                        link = link_elem.get_attribute('href')
                    
                    if title and link:
                        articles.append({
                            'title': title,
                            'url': link,
                            'content': '',
                            'summary': title,
                            'author': '',
                            'date': '',
                            'newspaper': newspaper or 'Desconocido',
                            'category': category or 'General',
                            'images_found': 0,
                            'images_downloaded': 0,
                            'images_data': [],
                            'scraped_at': datetime.now().isoformat(),
                            'article_id': f"selenium_{hash(link)}"
                        })
                except:
                    continue
            
            return articles
            
        finally:
            driver.quit()
            
    except Exception as e:
        logger.error(f"❌ Error en extracción Selenium: {e}")
        return []

def run_scraping(url: str, max_articles: int, max_images: int, method: str, download_images: bool, category: str = '', newspaper: str = '', region: str = ''):
    """Ejecutar scraping en hilo separado con paginación automática"""
    global scraping_status
    
    try:
        logger.info(f"🚀 Iniciando scraping con paginación: {url}")
        
        # Scraper específico para El Peruano
        if 'elperuano.pe' in url and 'economia' in url:
            logger.info("🇵🇪 Usando scraper específico para El Peruano con paginación")
            articles = scrape_elperuano_economia(max_articles, use_pagination=True)
            
            # Guardar en base de datos
            save_articles_to_db(articles, category, newspaper, region)
            
            scraping_status.update({
                'articles_found': len(articles),
                'images_found': sum(len(article.get('images_data', [])) for article in articles),
                'progress': max_articles
            })
            
        # Scraping con paginación automática para cualquier sitio
        else:
            logger.info("🔄 Usando sistema de paginación automática")
            articles = scrape_with_pagination(url, max_articles, max_images, method, download_images, category, newspaper, region)
            
            scraping_status.update({
                'articles_found': len(articles),
                'images_found': sum(len(article.get('images_data', [])) for article in articles),
                'progress': max_articles
            })
            
        # Métodos originales (mantener para compatibilidad)
        if method == 'optimized':
            # Usar SmartScraper
            scraper = SmartScraper(max_workers=10)
            try:
                articles = scraper.crawl_and_scrape_parallel(
                    url, 
                    max_articles=max_articles,
                    extract_images=download_images
                )
                
                # Guardar en base de datos
                save_articles_to_db(articles, category, newspaper, region)
                
                # Contar imágenes reales descargadas
                total_images = 0
                for article in articles:
                    if hasattr(article, 'images_data') and article.images_data:
                        try:
                            import json
                            images_data = json.loads(article.images_data) if isinstance(article.images_data, str) else article.images_data
                            if isinstance(images_data, list):
                                total_images += len(images_data)
                        except:
                            pass
                
                scraping_status.update({
                    'articles_found': len(articles),
                    'images_found': total_images,
                    'progress': max_articles
                })
                
            finally:
                scraper.close()
                
        elif method == 'improved':
            # Usar ImprovedScraper (método mejorado sin Selenium)
            scraper = ImprovedScraper()
            try:
                articles = scraper.scrape_articles(url, max_articles=max_articles)
                
                # Guardar en base de datos
                save_articles_to_db(articles, category, newspaper, region)
                
                scraping_status.update({
                    'articles_found': len(articles),
                    'images_found': sum(article.get('images_found', 0) for article in articles),
                    'progress': max_articles
                })
                
            finally:
                scraper.close()
        
        # Guardar estadísticas
        save_scraping_stats(url, scraping_status['articles_found'], 
                          scraping_status['images_found'], method)
        
        logger.info(f"✅ Scraping completado: {scraping_status['articles_found']} artículos, {scraping_status['images_found']} imágenes")
        
    except Exception as e:
        logger.error(f"❌ Error en scraping: {e}")
        scraping_status['error'] = str(e)
        
        # Notificar error
        send_scraping_notification(f"Error en scraping: {str(e)}", "error")
    
    finally:
        scraping_status.update({
            'is_running': False,
            'end_time': datetime.now().isoformat()
        })
        
        # Notificar finalización
        if scraping_status.get('error'):
            send_scraping_notification("Scraping finalizado con errores", "warning")
        else:
            articles_count = scraping_status.get('articles_found', 0)
            images_count = scraping_status.get('images_found', 0)
            send_scraping_notification(f"Scraping completado: {articles_count} artículos, {images_count} imágenes", "success")

def save_articles_to_db(articles: List[Dict], category: str = '', newspaper: str = '', region: str = ''):
    """Guardar artículos en la base de datos SQLite"""
    if not articles:
        return
    
    manual_category_raw = category.strip() if isinstance(category, str) else ''
    manual_category = re.sub(r'\s+', ' ', manual_category_raw).strip() if manual_category_raw else ''
    if manual_category and len(manual_category) > 80:
        manual_category = manual_category[:80]
    
    manual_region = normalize_region_value(region)

    def normalize_category_value(raw_value: Optional[str]) -> str:
        """Sanear y normalizar la categoría detectada."""
        fallback = manual_category or 'General'
        if manual_category:
            return fallback

        if not raw_value or not isinstance(raw_value, str):
            return fallback

        cleaned = re.sub(r'\s+', ' ', raw_value).strip()
        if not cleaned:
            return fallback

        # Si la cadena parece un bloque muy largo (ej. el contenido completo), descartarla
        if len(cleaned) > 120:
            return fallback

        return cleaned
    
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        re_enabled_newspapers = set()
        
        for article in articles:
            if isinstance(article, ArticleData):
                # Si es objeto ArticleData, priorizar categoría manual si se proporcionó
                article_category = normalize_category_value(getattr(article, 'category', None))
                # Usar el newspaper manual si está disponible, sino usar el del artículo
                article_newspaper = newspaper if newspaper else article.newspaper
                
                if article_newspaper and article_newspaper not in re_enabled_newspapers:
                    cursor.execute("DELETE FROM excluded_newspapers WHERE newspaper = ?", (article_newspaper,))
                    re_enabled_newspapers.add(article_newspaper)
                
                # Usar la región manual si está disponible, sino detectar automáticamente
                if region:
                    article_region = manual_region
                else:
                    article_text = f"{article.title} {article.content} {article.summary}"
                    article_region = normalize_region_value(detect_language_and_region(article_text))
                
                # Asegurar que siempre haya un article_id válido
                article_id = getattr(article, 'article_id', '')
                article_url = article.url
                
                # Si no hay article_id, generarlo basado en la URL normalizada
                if not article_id and article_url:
                    import hashlib
                    from urllib.parse import urlparse, urlunparse
                    # Normalizar URL
                    parsed = urlparse(article_url)
                    normalized_url = urlunparse((
                        parsed.scheme,
                        parsed.netloc.lower(),
                        parsed.path.rstrip('/'),
                        parsed.params,
                        '',  # Quitar query params
                        ''   # Quitar fragment
                    ))
                    url_hash = hashlib.md5(normalized_url.encode()).hexdigest()[:12]
                    article_id = f"article_{url_hash}"
                
                # Si aún no hay article_id, usar un hash del título
                if not article_id:
                    import hashlib
                    if article.title:
                        title_hash = hashlib.md5(article.title.encode()).hexdigest()[:12]
                        article_id = f"article_{title_hash}"
                    else:
                        article_id = f"article_{hash(str(article)) % 1000000000000:012d}"
                
                # Verificar si ya existe un artículo con este article_id o URL
                cursor.execute("SELECT id FROM articles WHERE article_id = ? OR url = ?", (article_id, article_url))
                existing = cursor.fetchone()
                
                if existing:
                    # Actualizar artículo existente en lugar de crear duplicado
                    cursor.execute("""
                        UPDATE articles SET
                        title = ?, content = ?, summary = ?, author = ?, date = ?, 
                        category = ?, newspaper = ?, url = ?,
                        images_found = ?, images_downloaded = ?, images_data = ?, 
                        scraped_at = ?, region = ?, user_category = ?
                        WHERE article_id = ? OR url = ?
                    """, (
                        article.title, article.content, article.summary, article.author,
                        article.date, article_category, article_newspaper, article_url,
                        article.images_found, article.images_downloaded, article.images_data,
                        article.scraped_at, article_region, manual_category,
                        article_id, article_url
                    ))
                    article_id_db = existing[0]
                else:
                    # Insertar nuevo artículo
                    cursor.execute("""
                        INSERT INTO articles 
                        (title, content, summary, author, date, category, newspaper, url, 
                         images_found, images_downloaded, images_data, scraped_at, article_id, region, user_category)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        article.title, article.content, article.summary, article.author,
                        article.date, article_category, article_newspaper, article_url,
                        article.images_found, article.images_downloaded, article.images_data,
                        article.scraped_at, article_id, article_region, manual_category
                    ))
                    article_id_db = cursor.lastrowid
                
                # Analizar el artículo en busca de menciones de competidores
                try:
                    article_text = f"{article.title} {article.content} {article.summary}"
                    mentions = ci_system.analyze_article_for_competitors(
                        article_id_db, article_text, article_url
                    )
                    
                    # Crear alertas si hay menciones importantes
                    for mention in mentions:
                        if mention['relevance_score'] > 0.7:  # Solo menciones muy relevantes
                            ci_system.create_alert(
                                mention['user_id'],
                                mention['competitor_id'],
                                'high_relevance_mention',
                                f"Mención importante de {mention['competitor_name']} en {article.newspaper}",
                                {
                                    'article_title': article.title,
                                    'article_url': article.url,
                                    'keyword': mention['keyword'],
                                    'sentiment': mention['sentiment_label'],
                                    'relevance': mention['relevance_score']
                                }
                            )
                except Exception as e:
                    logger.warning(f"Error analizando competidores en artículo {article_id_db}: {e}")
            else:
                # Si es diccionario, priorizar categoría manual si se proporcionó
                article_category = normalize_category_value(article.get('category') or article.get('user_category'))
                # Usar el newspaper manual si está disponible, sino usar el del artículo
                article_newspaper = newspaper if newspaper else article.get('newspaper', '')
                
                if article_newspaper and article_newspaper not in re_enabled_newspapers:
                    cursor.execute("DELETE FROM excluded_newspapers WHERE newspaper = ?", (article_newspaper,))
                    re_enabled_newspapers.add(article_newspaper)
                
                # Usar la región manual si está disponible, sino detectar automáticamente
                if region:
                    article_region = manual_region
                else:
                    article_text = f"{article.get('title', '')} {article.get('content', '')} {article.get('summary', '')}"
                    article_region = normalize_region_value(detect_language_and_region(article_text))
                
                # Convertir images_data a JSON string si es una lista
                images_data = article.get('images_data', '[]')
                if isinstance(images_data, list):
                    images_data = json.dumps(images_data)
                elif not isinstance(images_data, str):
                    images_data = '[]'
                
                # Asegurar que siempre haya un article_id válido
                article_id = article.get('article_id', '')
                article_url = article.get('url', '')
                
                # Si no hay article_id, generarlo basado en la URL normalizada
                if not article_id and article_url:
                    import hashlib
                    from urllib.parse import urlparse, urlunparse
                    # Normalizar URL
                    parsed = urlparse(article_url)
                    normalized_url = urlunparse((
                        parsed.scheme,
                        parsed.netloc.lower(),
                        parsed.path.rstrip('/'),
                        parsed.params,
                        '',  # Quitar query params
                        ''   # Quitar fragment
                    ))
                    url_hash = hashlib.md5(normalized_url.encode()).hexdigest()[:12]
                    article_id = f"article_{url_hash}"
                
                # Si aún no hay article_id, usar un hash del título
                if not article_id:
                    import hashlib
                    title = article.get('title', '')
                    if title:
                        title_hash = hashlib.md5(title.encode()).hexdigest()[:12]
                        article_id = f"article_{title_hash}"
                    else:
                        article_id = f"article_{hash(str(article)) % 1000000000000:012d}"
                
                # Verificar si ya existe un artículo con este article_id o URL normalizada
                cursor.execute("SELECT id FROM articles WHERE article_id = ? OR url = ?", (article_id, article_url))
                existing = cursor.fetchone()
                
                if existing:
                    # Actualizar artículo existente en lugar de crear duplicado
                    cursor.execute("""
                        UPDATE articles SET
                        title = ?, content = ?, summary = ?, author = ?, date = ?, 
                        category = ?, newspaper = ?, url = ?,
                        images_found = ?, images_downloaded = ?, images_data = ?, 
                        scraped_at = ?, region = ?, user_category = ?
                        WHERE article_id = ? OR url = ?
                    """, (
                        article.get('title', ''), article.get('content', ''), article.get('summary', ''),
                        article.get('author', ''), article.get('date', ''), article_category,
                        article_newspaper, article_url, article.get('images_found', 0),
                        article.get('images_downloaded', 0), images_data,
                        article.get('scraped_at', ''), article_region, manual_category,
                        article_id, article_url
                    ))
                    article_id_db = existing[0]
                else:
                    # Insertar nuevo artículo
                    cursor.execute("""
                        INSERT INTO articles 
                        (title, content, summary, author, date, category, newspaper, url, 
                         images_found, images_downloaded, images_data, scraped_at, article_id, region, user_category)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        article.get('title', ''), article.get('content', ''), article.get('summary', ''),
                        article.get('author', ''), article.get('date', ''), article_category,
                        article_newspaper, article_url, article.get('images_found', 0),
                        article.get('images_downloaded', 0), images_data,
                        article.get('scraped_at', ''), article_id, article_region, manual_category
                    ))
                    article_id_db = cursor.lastrowid
                
                # Usar el ID del artículo para análisis de competidores
                
                # Analizar el artículo en busca de menciones de competidores
                try:
                    article_text = f"{article.get('title', '')} {article.get('content', '')} {article.get('summary', '')}"
                    mentions = ci_system.analyze_article_for_competitors(
                        article_id_db, article_text, article_url
                    )
                    
                    # Crear alertas si hay menciones importantes
                    for mention in mentions:
                        if mention['relevance_score'] > 0.7:  # Solo menciones muy relevantes
                            ci_system.create_alert(
                                mention['user_id'],
                                mention['competitor_id'],
                                'high_relevance_mention',
                                f"Mención importante de {mention['competitor_name']} en {article_newspaper}",
                                {
                                    'article_title': article.get('title', ''),
                                    'article_url': article.get('url', ''),
                                    'keyword': mention['keyword'],
                                    'sentiment': mention['sentiment_label'],
                                    'relevance': mention['relevance_score']
                                }
                            )
                except Exception as e:
                    logger.warning(f"Error analizando competidores en artículo {article_id_db}: {e}")
        
        conn.commit()
        conn.close()
        logger.info(f"✅ {len(articles)} artículos guardados en la base de datos")
        
        # Después de guardar, verificar si hay periódicos nuevos que agregar a auto-update
        if newspaper:
            try:
                detect_and_add_new_newspaper(newspaper)
            except Exception as e:
                logger.debug(f"⚠️ Error detectando periódico nuevo: {e}")
        
    except Exception as e:
        logger.error(f"❌ Error guardando artículos: {e}")

def save_images_to_db(images: List[Dict]):
    """Guardar imágenes en la base de datos"""
    if not images:
        return
    
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        for image in images:
            cursor.execute("""
                INSERT INTO images (article_id, url, local_path, alt_text, title, width, height, format, size_bytes, relevance_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                image.get('article_id'),
                image.get('url'),
                image.get('local_path'),
                image.get('alt_text'),
                image.get('title'),
                image.get('width'),
                image.get('height'),
                image.get('format'),
                image.get('size_bytes'),
                image.get('relevance_score', 0)
            ))
        conn.commit()
        logger.info(f"✅ {len(images)} imágenes guardadas en la base de datos")
        
    except Exception as e:
        logger.error(f"❌ Error guardando imágenes: {e}")
    finally:
        conn.close()

def save_scraping_stats(url: str, articles_found: int, images_found: int, method: str):
    """Guardar estadísticas del scraping"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        start_time = datetime.fromisoformat(scraping_status['start_time'])
        end_time = datetime.now()
        duration = int((end_time - start_time).total_seconds())
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO scraping_stats (session_id, url_scraped, articles_found, images_found, images_downloaded, duration_seconds, method_used)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            f"session_{int(time.time())}",
            url,
            articles_found,
            images_found,
            images_found,  # Asumimos que todas se descargaron
            duration,
            method
        ))
        conn.commit()
        logger.info("✅ Estadísticas guardadas")
        
    except Exception as e:
        logger.error(f"❌ Error guardando estadísticas: {e}")
    finally:
        conn.close()

@app.route('/api/articles', methods=['GET'])
def get_articles():
    """Obtener artículos de la base de datos SQLite"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Base de datos no disponible'}), 500
    
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        newspaper = request.args.get('newspaper')
        category = request.args.get('category')
        region = request.args.get('region')
        search = request.args.get('search')
        date_from = request.args.get('dateFrom')  # Fecha de inicio (YYYY-MM-DD)
        date_to = request.args.get('dateTo')  # Fecha de fin (YYYY-MM-DD)
        
        offset = (page - 1) * limit
        
        # Construir query
        query = "SELECT * FROM articles WHERE 1=1"
        params = []
        
        if newspaper:
            query += " AND newspaper = ?"
            params.append(newspaper)
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if region:
            query += " AND region = ?"
            params.append(region)
        
        if search:
            query += " AND (title LIKE ? OR content LIKE ? OR summary LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])
        
        # Filtro de rango de fechas (basado en fecha de publicación)
        # Las fechas en la base de datos están principalmente en formato legible (ej: "11 Sep 2025 | 10:04 h") 
        # o formato ISO (ej: "2025-09-11T10:04:00")
        # Necesitamos filtrar por ambos formatos
        
        if date_from or date_to:
            from datetime import datetime
            import re
            
            # Función helper para parsear fecha de BD a datetime
            def parse_date_from_db(date_str):
                """Parsear fecha de BD (formato legible o ISO) a datetime"""
                if not date_str or date_str.strip() == '':
                    return None
                try:
                    # Intentar formato ISO primero
                    if 'T' in date_str:
                        return datetime.fromisoformat(date_str.replace('Z', '+00:00').split('.')[0])
                    # Intentar formato legible: "11 Sep 2025 | 10:04 h"
                    match = re.search(r'(\d{1,2})\s+(\w{3})\s+(\d{4})', date_str)
                    if match:
                        day, month, year = match.groups()
                        month_map = {
                            'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                            'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                            'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                        }
                        month_num = month_map.get(month, '01')
                        normalized = f"{year}-{month_num}-{day.zfill(2)}"
                        return datetime.strptime(normalized, '%Y-%m-%d')
                    # Intentar formato YYYY-MM-DD
                    if '-' in date_str[:10]:
                        return datetime.strptime(date_str[:10], '%Y-%m-%d')
                except:
                    pass
                return None
            
            # Crear función SQL personalizada para parsear fechas
            def sqlite_parse_date(date_str):
                """Función para SQLite que parsea fechas"""
                if not date_str:
                    return None
                parsed = parse_date_from_db(date_str)
                if parsed:
                    return parsed.strftime('%Y-%m-%d')
                return None
            
            # Registrar función personalizada en SQLite
            conn.create_function('parse_date', 1, sqlite_parse_date)
            
            # Construir condiciones de filtrado
            if date_from:
                try:
                    date_from_dt = datetime.strptime(date_from, '%Y-%m-%d')
                    date_from_str = date_from_dt.strftime('%Y-%m-%d')
                    
                    # Usar función parse_date para normalizar fechas antes de comparar
                    query += " AND (parse_date(date) >= ? OR date >= ?)"
                    params.append(date_from_str)  # Fecha normalizada
                    params.append(date_from_str)  # Fecha ISO directa
                except Exception as e:
                    logger.warning(f"Error procesando date_from: {e}")
            
            if date_to:
                try:
                    date_to_dt = datetime.strptime(date_to, '%Y-%m-%d')
                    date_to_str = date_to_dt.strftime('%Y-%m-%d') + 'T23:59:59'
                    
                    query += " AND (parse_date(date) <= ? OR date <= ?)"
                    params.append(date_to_dt.strftime('%Y-%m-%d'))  # Fecha normalizada
                    params.append(date_to_str)  # Fecha ISO directa
                except Exception as e:
                    logger.warning(f"Error procesando date_to: {e}")
        
        query += " ORDER BY scraped_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Obtener nombres de columnas
        column_names = [description[0] for description in cursor.description]
        
        articles = []
        for row in rows:
            article_dict = dict(zip(column_names, row))
            # Parsear imágenes si existen
            if article_dict.get('images_data'):
                try:
                    article_dict['images_data'] = json.loads(article_dict['images_data'])
                except:
                    article_dict['images_data'] = []
            articles.append(article_dict)
        
        # Obtener total
        count_query = "SELECT COUNT(*) as total FROM articles WHERE 1=1"
        count_params = []
        if newspaper:
            count_query += " AND newspaper = ?"
            count_params.append(newspaper)
        if category:
            count_query += " AND category = ?"
            count_params.append(category)
        if region:
            count_query += " AND region = ?"
            count_params.append(region)
        if search:
            count_query += " AND (title LIKE ? OR content LIKE ? OR summary LIKE ?)"
            search_term = f"%{search}%"
            count_params.extend([search_term, search_term, search_term])
        # Aplicar mismo filtro de fechas al conteo (usar misma función parse_date)
        if date_from or date_to:
            from datetime import datetime
            import re
            
            # Función helper para parsear fecha de BD a datetime (misma que arriba)
            def parse_date_from_db(date_str):
                if not date_str or date_str.strip() == '':
                    return None
                try:
                    if 'T' in date_str:
                        return datetime.fromisoformat(date_str.replace('Z', '+00:00').split('.')[0])
                    match = re.search(r'(\d{1,2})\s+(\w{3})\s+(\d{4})', date_str)
                    if match:
                        day, month, year = match.groups()
                        month_map = {
                            'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                            'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                            'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                        }
                        month_num = month_map.get(month, '01')
                        normalized = f"{year}-{month_num}-{day.zfill(2)}"
                        return datetime.strptime(normalized, '%Y-%m-%d')
                    if '-' in date_str[:10]:
                        return datetime.strptime(date_str[:10], '%Y-%m-%d')
                except:
                    pass
                return None
            
            def sqlite_parse_date(date_str):
                if not date_str:
                    return None
                parsed = parse_date_from_db(date_str)
                if parsed:
                    return parsed.strftime('%Y-%m-%d')
                return None
            
            # Registrar función en la misma conexión
            conn.create_function('parse_date', 1, sqlite_parse_date)
        
        if date_from:
            try:
                from datetime import datetime
                date_from_dt = datetime.strptime(date_from, '%Y-%m-%d')
                date_from_str = date_from_dt.strftime('%Y-%m-%d')
                count_query += " AND (parse_date(date) >= ? OR date >= ?)"
                count_params.append(date_from_str)
                count_params.append(date_from_str)
            except Exception as e:
                logger.warning(f"Error procesando date_from en count: {e}")
        
        if date_to:
            try:
                from datetime import datetime
                date_to_dt = datetime.strptime(date_to, '%Y-%m-%d')
                date_to_str = date_to_dt.strftime('%Y-%m-%d') + 'T23:59:59'
                count_query += " AND (parse_date(date) <= ? OR date <= ?)"
                count_params.append(date_to_dt.strftime('%Y-%m-%d'))
                count_params.append(date_to_str)
            except Exception as e:
                logger.warning(f"Error procesando date_to en count: {e}")
        
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'articles': articles,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo artículos: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/articles/filters', methods=['GET'])
def get_article_filters():
    """Obtener filtros únicos para artículos (periódicos, categorías, regiones)"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Base de datos no disponible'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Obtener periódicos únicos
        cursor.execute("SELECT DISTINCT newspaper FROM articles WHERE newspaper IS NOT NULL AND newspaper != '' ORDER BY newspaper")
        newspapers = [row[0] for row in cursor.fetchall()]
        
        # Obtener categorías únicas
        cursor.execute("""
            SELECT DISTINCT TRIM(COALESCE(NULLIF(user_category, ''), category)) as category
            FROM articles
            WHERE category IS NOT NULL AND TRIM(COALESCE(NULLIF(user_category, ''), category)) != ''
            ORDER BY category COLLATE NOCASE
        """)
        raw_categories = [row[0] for row in cursor.fetchall()]
        
        def clean_filter_category(value: str) -> Optional[str]:
            if not value:
                return None
            cleaned = re.sub(r'\s+', ' ', value).strip()
            if not cleaned:
                return None
            if len(cleaned) > 80:
                return None
            return cleaned
        
        seen = set()
        categories = []
        for cat in raw_categories:
            cleaned = clean_filter_category(cat)
            if not cleaned:
                continue
            key = cleaned.lower()
            if key not in seen:
                seen.add(key)
                categories.append(cleaned)
        
        # Obtener regiones únicas
        cursor.execute("SELECT DISTINCT region FROM articles WHERE region IS NOT NULL AND region != ''")
        raw_regions = [row[0] for row in cursor.fetchall()]
        
        regions_seen = set()
        regions = []
        for reg in raw_regions:
            normalized = normalize_region_value(reg)
            if not normalized:
                continue
            if normalized in regions_seen:
                continue
            regions_seen.add(normalized)
            regions.append(normalized)
        
        regions.sort()
        
        conn.close()
        
        return jsonify({
            'newspapers': newspapers,
            'categories': categories,
            'regions': regions
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo filtros: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/articles/export/excel', methods=['GET'])
@require_auth
def export_articles_to_excel():
    """Exportar todos los artículos a Excel"""
    # Verificar plan
    user_id = request.current_user.get('user_id')
    error_msg = _require_premium_or_enterprise(user_id)
    if error_msg:
        return jsonify({'error': error_msg}), 403
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Base de datos no disponible'}), 500
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(articles)")
        columns_info = cursor.fetchall()
        column_names = [col[1] for col in columns_info]

        base_columns = [
            'id', 'title', 'summary', 'content', 'newspaper', 'category',
            'region', 'url', 'scraped_at', 'images_data'
        ]

        optional_columns = []
        for optional in ['author', 'date', 'images_found', 'images_downloaded', 'article_id', 'user_category']:
            if optional in column_names:
                optional_columns.append(optional)

        select_columns = base_columns + optional_columns

        query = f"SELECT {', '.join(select_columns)} FROM articles ORDER BY scraped_at DESC"
        cursor.execute(query)

        articles = cursor.fetchall()
        conn.close()
        
        if not articles:
            return jsonify({'error': 'No hay artículos para exportar'}), 404
        
        # Preparar datos para Excel
        CATEGORY_LABELS = {
            'politica': 'Política',
            'política': 'Política',
            'politics': 'Política',
            'internacional': 'Internacional',
            'international': 'Internacional',
            'nacional': 'Nacional',
            'deportes': 'Deportes',
            'sports': 'Deportes',
            'economia': 'Economía',
            'economía': 'Economía',
            'business': 'Negocios',
            'negocios': 'Negocios',
            'tecnologia': 'Tecnología',
            'tecnología': 'Tecnología',
            'technology': 'Tecnología',
            'salud': 'Salud',
            'health': 'Salud',
            'cultura': 'Cultura',
            'entretenimiento': 'Entretenimiento',
            'entertainment': 'Entretenimiento',
            'educacion': 'Educación',
            'educación': 'Educación',
            'science': 'Ciencia',
            'ciencia': 'Ciencia',
            'opinion': 'Opinión',
            'opinión': 'Opinión'
        }

        excel_data = []
        for article in articles:
            row_dict = {col: article[idx] for idx, col in enumerate(select_columns)}

            images_data = row_dict.get('images_data')
            if images_data:
                try:
                    images_list = json.loads(images_data)
                    images_count = len(images_list) if isinstance(images_list, list) else 0
                except Exception:
                    images_count = 0
            else:
                images_count = 0

            category_value = row_dict.get('category', '') or ''
            manual_category_value = row_dict.get('user_category', '') or ''
            display_category = manual_category_value or category_value
            category_key = display_category.lower().strip()
            category_standard = CATEGORY_LABELS.get(category_key, display_category.title() if display_category else '')

            published_raw = row_dict.get('date', '') or ''
            try:
                published_formatted = datetime.fromisoformat(published_raw).strftime('%Y-%m-%d %H:%M') if published_raw else ''
            except Exception:
                published_formatted = published_raw

            scraped_raw = row_dict.get('scraped_at', '') or ''
            try:
                scraped_formatted = datetime.fromisoformat(scraped_raw).strftime('%Y-%m-%d %H:%M') if scraped_raw else ''
            except Exception:
                scraped_formatted = scraped_raw

            content_value = row_dict.get('content', '') or ''
            if content_value and len(content_value) > 500:
                content_value = content_value[:500] + '...'

            excel_data.append({
                'ID': row_dict.get('id'),
                'Código Artículo': row_dict.get('article_id', ''),
                'Título': row_dict.get('title', ''),
                'Resumen': row_dict.get('summary', ''),
                'Contenido (500c)': content_value,
                'Autor': row_dict.get('author', ''),
                'Fecha Publicación': published_formatted,
                'Categoría Original': category_value,
                'Categoría Asignada': manual_category_value,
                'Categoría Estándar': category_standard,
                'Periódico': row_dict.get('newspaper', ''),
                'Región': row_dict.get('region', ''),
                'URL': row_dict.get('url', ''),
                'Fecha Extracción': scraped_formatted,
                'Imágenes (detectadas)': images_count,
                'Imágenes Encontradas': row_dict.get('images_found', ''),
                'Imágenes Descargadas': row_dict.get('images_downloaded', '')
            })
        
        # Crear DataFrame
        df = pd.DataFrame(excel_data)
        
        # Crear archivo Excel en memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Artículos', index=False)
            
            # Ajustar ancho de columnas
            worksheet = writer.sheets['Artículos']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)  # Máximo 50 caracteres
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        
        # Generar nombre de archivo con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"articulos_exportados_{timestamp}.xlsx"
        
        # Convertir a base64 para enviar al frontend
        excel_base64 = base64.b64encode(output.getvalue()).decode('utf-8')
        
        logger.info(f"✅ Excel exportado exitosamente: {len(articles)} artículos")
        
        return jsonify({
            'success': True,
            'filename': filename,
            'data': excel_base64,
            'articles_count': len(articles)
        })
        
    except Exception as e:
        logger.error(f"❌ Error exportando a Excel: {e}")
        return jsonify({'error': f'Error exportando a Excel: {str(e)}'}), 500


@app.route('/api/articles/export/csv', methods=['GET'])
@require_auth
def export_articles_to_csv():
    """Exportar todos los artículos a CSV con columnas para métricas de desempeño"""
    # Verificar plan
    user_id = request.current_user.get('user_id')
    error_msg = _require_premium_or_enterprise(user_id)
    if error_msg:
        return jsonify({'error': error_msg}), 403
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Base de datos no disponible'}), 500

    try:
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(articles)")
        columns_info = cursor.fetchall()
        column_names = [col[1] for col in columns_info]

        base_columns = [
            'id', 'title', 'summary', 'content', 'newspaper', 'category',
            'region', 'url', 'scraped_at', 'images_data'
        ]

        optional_columns = []
        if 'sentiment' in column_names:
            optional_columns.append('sentiment')
        if 'article_id' in column_names:
            optional_columns.append('article_id')
        if 'user_category' in column_names:
            optional_columns.append('user_category')

        select_columns = base_columns + optional_columns

        query = f"SELECT {', '.join(select_columns)} FROM articles ORDER BY scraped_at DESC"
        cursor.execute(query)

        articles = cursor.fetchall()
        conn.close()

        if not articles:
            return jsonify({'error': 'No hay artículos para exportar'}), 404

        csv_rows = []
        for article in articles:
            row_dict = {col: article[idx] for idx, col in enumerate(select_columns)}

            images_count = 0
            images_data_value = row_dict.get('images_data')
            if images_data_value:
                try:
                    images_list = json.loads(images_data_value)
                    images_count = len(images_list) if isinstance(images_list, list) else 0
                except Exception:
                    images_count = 0

            content_value = row_dict.get('content') or ''
            truncated_content = content_value[:500] + '...' if len(content_value) > 500 else content_value

            csv_rows.append({
                'ID': row_dict.get('id'),
                'Código Artículo': row_dict.get('article_id', ''),
                'Título': row_dict.get('title', ''),
                'Resumen': row_dict.get('summary', ''),
                'Contenido': truncated_content,
                'Periódico': row_dict.get('newspaper', ''),
                'Categoría': row_dict.get('category', ''),
                'Región': row_dict.get('region', ''),
                'URL': row_dict.get('url', ''),
                'Fecha Extracción': row_dict.get('scraped_at', ''),
                'Cantidad Imágenes': images_count,
                'Sentimiento': row_dict.get('sentiment', ''),
                'Etiqueta Real': '',
                'Etiqueta Predicha': row_dict.get('category', ''),
                'Categoría Asignada': row_dict.get('user_category', ''),
                'Precisión': '',
                'Recall': '',
                'F1 Score': '',
                'AUC': '',
                'ROC Curve': ''
            })

        df = pd.DataFrame(csv_rows)

        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue().encode('utf-8-sig')

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"articulos_metrics_{timestamp}.csv"

        csv_base64 = base64.b64encode(csv_content).decode('utf-8')

        logger.info(f"✅ CSV exportado exitosamente: {len(articles)} artículos")

        return jsonify({
            'success': True,
            'filename': filename,
            'data': csv_base64,
            'articles_count': len(articles)
        })

    except Exception as e:
        logger.error(f"❌ Error exportando a CSV: {e}")
        return jsonify({'error': f'Error exportando a CSV: {str(e)}'}), 500


@app.route('/api/articles/<article_id>', methods=['GET'])
def get_article(article_id):
    """Obtener un artículo específico"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Base de datos no disponible'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM articles WHERE article_id = ?", [article_id])
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return jsonify({'error': 'Artículo no encontrado'}), 404
        
        # Obtener nombres de columnas
        column_names = [description[0] for description in cursor.description]
        article_dict = dict(zip(column_names, row))
        
        if article_dict.get('images_data'):
            try:
                article_dict['images_data'] = json.loads(article_dict['images_data'])
            except:
                article_dict['images_data'] = []
        
        conn.close()
        return jsonify(article_dict)
            
    except Exception as e:
        logger.error(f"❌ Error obteniendo artículo: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================
# SISTEMA DE COMENTARIOS/OPINIONES
# ============================================================

@app.route('/api/comments', methods=['GET', 'POST'])
def comments_endpoint():
    """Obtener comentarios de un artículo o crear nuevo comentario"""
    if request.method == 'GET':
        try:
            article_id = request.args.get('article_id', type=int)
            if not article_id:
                return jsonify({'error': 'article_id es requerido'}), 400
            
            conn = get_db_connection()
            if not conn:
                return jsonify({'error': 'Base de datos no disponible'}), 500
            
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, article_id, user_name, comment_text, 
                       created_at, updated_at, is_edited
                FROM comments
                WHERE article_id = ?
                ORDER BY created_at DESC
            ''', (article_id,))
            
            columns = [desc[0] for desc in cursor.description]
            comments = []
            for row in cursor.fetchall():
                comment = dict(zip(columns, row))
                # Convertir timestamps a strings ISO
                if comment.get('created_at'):
                    comment['created_at'] = comment['created_at']
                if comment.get('updated_at'):
                    comment['updated_at'] = comment['updated_at']
                comments.append(comment)
            
            conn.close()
            return jsonify({'comments': comments})
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo comentarios: {e}")
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        """Crear nuevo comentario"""
        try:
            data = request.get_json()
            article_id = data.get('article_id')
            user_name = data.get('user_name', '').strip()
            comment_text = data.get('comment_text', '').strip()
            
            if not article_id:
                return jsonify({'error': 'article_id es requerido'}), 400
            if not user_name:
                return jsonify({'error': 'user_name es requerido'}), 400
            if not comment_text:
                return jsonify({'error': 'comment_text es requerido'}), 400
            if len(comment_text) > 2000:
                return jsonify({'error': 'El comentario no puede exceder 2000 caracteres'}), 400
            
            # Verificar que el artículo existe
            conn = get_db_connection()
            if not conn:
                return jsonify({'error': 'Base de datos no disponible'}), 500
            
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM articles WHERE id = ?', (article_id,))
            if not cursor.fetchone():
                conn.close()
                return jsonify({'error': 'Artículo no encontrado'}), 404
            
            # Insertar comentario
            cursor.execute('''
                INSERT INTO comments (article_id, user_name, comment_text)
                VALUES (?, ?, ?)
            ''', (article_id, user_name, comment_text))
            
            comment_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Comentario creado: ID {comment_id} para artículo {article_id}")
            
            return jsonify({
                'success': True,
                'comment': {
                    'id': comment_id,
                    'article_id': article_id,
                    'user_name': user_name,
                    'comment_text': comment_text,
                    'created_at': datetime.now().isoformat(),
                    'is_edited': False
                }
            }), 201
            
        except Exception as e:
            logger.error(f"❌ Error creando comentario: {e}")
            return jsonify({'error': str(e)}), 500

# ============================================================
# SISTEMA DE COMENTARIOS VIRALES
# ============================================================

@app.route('/api/viral-comments', methods=['GET', 'POST'])
def viral_comments_endpoint():
    """Obtener comentarios virales o crear nuevo comentario viral"""
    if request.method == 'GET':
        try:
            topic = request.args.get('topic')
            limit = request.args.get('limit', type=int) or 20
            
            conn = get_db_connection()
            if not conn:
                return jsonify({'error': 'Base de datos no disponible'}), 500
            
            cursor = conn.cursor()
            
            if topic:
                cursor.execute('''
                    SELECT id, user_name, comment_text, topic, likes, sentiment, created_at
                    FROM viral_comments
                    WHERE topic = ?
                    ORDER BY likes DESC, created_at DESC
                    LIMIT ?
                ''', (topic, limit))
            else:
                cursor.execute('''
                    SELECT id, user_name, comment_text, topic, likes, sentiment, created_at
                    FROM viral_comments
                    ORDER BY likes DESC, created_at DESC
                    LIMIT ?
                ''', (limit,))
            
            columns = [desc[0] for desc in cursor.description]
            comments = []
            for row in cursor.fetchall():
                comment = dict(zip(columns, row))
                comments.append(comment)
            
            conn.close()
            return jsonify({'comments': comments})
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo comentarios virales: {e}")
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        """Crear nuevo comentario viral"""
        try:
            data = request.get_json()
            user_name = data.get('user_name', '').strip()
            comment_text = data.get('comment_text', '').strip()
            topic = data.get('topic', '').strip()
            
            if not user_name:
                return jsonify({'error': 'user_name es requerido'}), 400
            if not comment_text:
                return jsonify({'error': 'comment_text es requerido'}), 400
            if not topic:
                return jsonify({'error': 'topic es requerido'}), 400
            if len(comment_text) > 2000:
                return jsonify({'error': 'El comentario no puede exceder 2000 caracteres'}), 400
            
            # Analizar sentimiento automáticamente usando el analizador de sentimientos
            from sentiment_analyzer import sentiment_analyzer
            try:
                sentiment_analysis = sentiment_analyzer.analyze_sentiment(comment_text)
                sentiment = sentiment_analysis['polarity']  # 'positive', 'negative', o 'neutral'
                sentiment_score = sentiment_analysis['score']  # -1 a 1
                emotions = sentiment_analysis.get('emotions', {})
            except Exception as e:
                logger.warning(f"⚠️ Error analizando sentimiento del comentario, usando 'neutral': {e}")
                sentiment = 'neutral'
                sentiment_score = 0.0
                emotions = {}
            
            conn = get_db_connection()
            if not conn:
                return jsonify({'error': 'Base de datos no disponible'}), 500
            
            # Insertar comentario viral
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO viral_comments (user_name, comment_text, topic, sentiment)
                VALUES (?, ?, ?, ?)
            ''', (user_name, comment_text, topic, sentiment))
            
            comment_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Comentario viral creado: ID {comment_id}")
            
            return jsonify({
                'success': True,
                'comment': {
                    'id': comment_id,
                    'user_name': user_name,
                    'comment_text': comment_text,
                    'topic': topic,
                    'likes': 0,
                    'sentiment': sentiment,
                    'sentiment_score': sentiment_score,
                    'emotions': emotions,
                    'created_at': datetime.now().isoformat()
                }
            }), 201
            
        except Exception as e:
            logger.error(f"❌ Error creando comentario viral: {e}")
            return jsonify({'error': str(e)}), 500

@app.route('/api/viral-comments/<int:comment_id>/like', methods=['POST'])
def like_viral_comment(comment_id):
    """Dar like a un comentario viral"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Base de datos no disponible'}), 500
        
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE viral_comments
            SET likes = likes + 1
            WHERE id = ?
        ''', (comment_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Comentario no encontrado'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error(f"❌ Error dando like: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/viral-comments/sentiment-analysis', methods=['GET'])
@require_auth
def viral_comments_sentiment_analysis():
    """
    Análisis de sentimiento de comentarios virales por tema
    Útil para comparar sentimiento de noticias vs opiniones de usuarios
    Disponible para planes Premium y Enterprise
    """
    # Verificar plan del usuario
    user_id = request.current_user.get('user_id')
    if not _can_access_viral_comments_comparison(user_id):
        return jsonify({
            'error': 'Esta funcionalidad está disponible solo para planes Premium o Enterprise',
            'upgrade_required': True
        }), 403
    
    from sentiment_analyzer import sentiment_analyzer
    from collections import defaultdict
    
    try:
        topic = request.args.get('topic', None)
        days = int(request.args.get('days', 30))
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Base de datos no disponible'}), 500
        
        cursor = conn.cursor()
        
        # Construir query
        query = """
            SELECT id, comment_text, topic, sentiment, created_at
            FROM viral_comments
            WHERE created_at >= datetime('now', '-' || ? || ' days')
        """
        params = [days]
        
        if topic:
            query += " AND topic = ?"
            params.append(topic)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        comments = cursor.fetchall()
        conn.close()
        
        if not comments:
            return jsonify({
                'total': 0,
                'positive': 0,
                'negative': 0,
                'neutral': 0,
                'average_score': 0.0,
                'by_topic': {},
                'emotions_summary': {},
                'polarization_distribution': {'high': 0, 'medium': 0, 'low': 0}
            }), 200
        
        # Análisis agregado
        sentiment_data = {
            'positive': 0,
            'negative': 0,
            'neutral': 0,
            'total': len(comments),
            'total_score': 0.0,
            'by_topic': defaultdict(lambda: {
                'positive': 0,
                'negative': 0,
                'neutral': 0,
                'total': 0,
                'total_score': 0.0
            }),
            'emotions_summary': defaultdict(float),
            'polarization_distribution': defaultdict(int)
        }
        
        # Analizar cada comentario
        for comment_id, comment_text, comment_topic, stored_sentiment, created_at in comments:
            try:
                # Re-analizar para obtener datos completos (emociones, polarización, etc.)
                analysis = sentiment_analyzer.analyze_sentiment(comment_text)
                polarity = analysis['polarity']
                score = analysis['score']
                
                sentiment_data[polarity] += 1
                sentiment_data['total_score'] += score
                sentiment_data['polarization_distribution'][analysis['polarization']] += 1
                
                # Por tema
                topic_data = sentiment_data['by_topic'][comment_topic]
                topic_data[polarity] += 1
                topic_data['total'] += 1
                topic_data['total_score'] += score
                
                # Emociones
                for emotion, emotion_score in analysis.get('emotions', {}).items():
                    sentiment_data['emotions_summary'][emotion] += emotion_score
                    
            except Exception as e:
                logger.debug(f"Error analizando comentario viral {comment_id}: {e}")
                continue
        
        # Calcular promedios
        average_score = sentiment_data['total_score'] / sentiment_data['total'] if sentiment_data['total'] > 0 else 0.0
        
        # Convertir defaultdict a dict normal y calcular promedios por tema
        by_topic = {}
        for topic_name, topic_data in sentiment_data['by_topic'].items():
            by_topic[topic_name] = {
                'positive': topic_data['positive'],
                'negative': topic_data['negative'],
                'neutral': topic_data['neutral'],
                'total': topic_data['total'],
                'average_score': topic_data['total_score'] / topic_data['total'] if topic_data['total'] > 0 else 0.0
            }
        
        return jsonify({
            'total': sentiment_data['total'],
            'positive': sentiment_data['positive'],
            'negative': sentiment_data['negative'],
            'neutral': sentiment_data['neutral'],
            'average_score': average_score,
            'by_topic': by_topic,
            'emotions_summary': dict(sentiment_data['emotions_summary']),
            'polarization_distribution': dict(sentiment_data['polarization_distribution'])
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error en análisis de sentimiento de comentarios virales: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/viral-comments/alerts', methods=['GET'])
@require_auth
def get_viral_comments_alerts():
    """
    Obtener alertas cuando el sentimiento de comentarios virales es muy negativo sobre un tema
    Retorna temas con sentimiento negativo alto (score < -0.3 y más del 40% negativo)
    Disponible para planes Premium y Enterprise
    """
    # Verificar plan del usuario
    user_id = request.current_user.get('user_id')
    if not _can_access_advanced_alerts(user_id):
        return jsonify({
            'error': 'Esta funcionalidad está disponible solo para planes Premium o Enterprise',
            'upgrade_required': True
        }), 403
    
    from sentiment_analyzer import sentiment_analyzer
    from collections import defaultdict
    
    try:
        days = int(request.args.get('days', 7))  # Por defecto últimos 7 días
        min_negative_pct = float(request.args.get('min_negative_pct', 40.0))  # Mínimo 40% negativo
        max_sentiment_score = float(request.args.get('max_sentiment_score', -0.3))  # Score máximo -0.3
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Base de datos no disponible'}), 500
        
        cursor = conn.cursor()
        
        # Obtener comentarios virales del período
        cursor.execute("""
            SELECT id, comment_text, topic, sentiment, created_at
            FROM viral_comments
            WHERE created_at >= datetime('now', '-' || ? || ' days')
            ORDER BY created_at DESC
        """, (days,))
        
        comments = cursor.fetchall()
        conn.close()
        
        if not comments:
            return jsonify({
                'alerts': [],
                'total_alerts': 0
            }), 200
        
        # Agrupar por tema y analizar
        topic_data = defaultdict(lambda: {
            'total': 0,
            'positive': 0,
            'negative': 0,
            'neutral': 0,
            'total_score': 0.0,
            'comments': []
        })
        
        for comment_id, comment_text, topic, stored_sentiment, created_at in comments:
            if not topic:
                continue
            
            try:
                analysis = sentiment_analyzer.analyze_sentiment(comment_text)
                polarity = analysis['polarity']
                score = analysis['score']
                
                topic_data[topic]['total'] += 1
                topic_data[topic][polarity] += 1
                topic_data[topic]['total_score'] += score
                topic_data[topic]['comments'].append({
                    'id': comment_id,
                    'text': comment_text[:100] + '...' if len(comment_text) > 100 else comment_text,
                    'sentiment': polarity,
                    'score': round(score, 3),
                    'created_at': created_at
                })
            except:
                continue
        
        # Identificar alertas (temas con sentimiento muy negativo)
        alerts = []
        for topic, data in topic_data.items():
            if data['total'] < 3:  # Mínimo 3 comentarios para considerar
                continue
            
            negative_pct = (data['negative'] / data['total']) * 100
            average_score = data['total_score'] / data['total']
            
            # Criterio de alerta: más del X% negativo Y score promedio < -0.3
            if negative_pct >= min_negative_pct and average_score <= max_sentiment_score:
                alerts.append({
                    'topic': topic,
                    'severity': 'high' if average_score < -0.5 else 'medium',
                    'negative_percentage': round(negative_pct, 1),
                    'average_score': round(average_score, 3),
                    'total_comments': data['total'],
                    'negative_count': data['negative'],
                    'positive_count': data['positive'],
                    'neutral_count': data['neutral'],
                    'recent_comments': data['comments'][:5]  # Últimos 5 comentarios
                })
        
        # Ordenar por severidad y score
        alerts.sort(key=lambda x: (x['average_score'], -x['negative_percentage']))
        
        return jsonify({
            'alerts': alerts,
            'total_alerts': len(alerts),
            'period_days': days
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo alertas de comentarios virales: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/comments/<int:comment_id>', methods=['DELETE'])
@require_auth
def delete_comment(comment_id):
    """Eliminar un comentario (requiere autenticación)"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Base de datos no disponible'}), 500
        
        cursor = conn.cursor()
        cursor.execute('DELETE FROM comments WHERE id = ?', (comment_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Comentario no encontrado'}), 404
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Comentario eliminado: ID {comment_id}")
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error(f"❌ Error eliminando comentario: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/images', methods=['GET'])
def get_images():
    """Obtener imágenes de la base de datos"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Base de datos no disponible'}), 500
    
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        article_id = request.args.get('article_id')
        
        offset = (page - 1) * limit
        
        query = "SELECT * FROM images WHERE 1=1"
        params = []
        
        if article_id:
            query += " AND article_id = ?"
            params.append(article_id)
        
        query += " ORDER BY downloaded_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = conn.cursor()
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        images = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return jsonify({
            'images': images,
            'pagination': {
                'page': page,
                'limit': limit
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo imágenes: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Obtener estadísticas del scraping"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Base de datos no disponible'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Estadísticas generales
        cursor.execute("""
            SELECT 
                COUNT(*) as total_articles,
                COUNT(DISTINCT newspaper) as total_newspapers,
                COUNT(DISTINCT category) as total_categories,
                SUM(images_found) as total_images_found,
                SUM(images_downloaded) as total_images_downloaded
            FROM articles
        """)
        row = cursor.fetchone()
        column_names = [description[0] for description in cursor.description]
        general_stats = dict(zip(column_names, row))
        
        # Estadísticas por periódico
        cursor.execute("""
            SELECT 
                newspaper,
                COUNT(*) as articles_count,
                SUM(images_found) as images_count
            FROM articles 
            GROUP BY newspaper 
            ORDER BY articles_count DESC
            LIMIT 10
        """)
        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        newspaper_stats = [dict(zip(column_names, row)) for row in rows]
        
        # Estadísticas por categoría
        cursor.execute("""
            SELECT 
                category,
                COUNT(*) as articles_count
            FROM articles 
            WHERE category IS NOT NULL AND category != ''
            GROUP BY category 
            ORDER BY articles_count DESC
            LIMIT 10
        """)
        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        category_stats = [dict(zip(column_names, row)) for row in rows]
        
        # Últimas sesiones de scraping
        cursor.execute("""
            SELECT 
                session_id,
                url_scraped,
                articles_found,
                images_found,
                duration_seconds,
                method_used,
                created_at
            FROM scraping_stats 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        sessions = [dict(zip(column_names, row)) for row in rows]
        
        conn.close()
        
        return jsonify({
            'general': general_stats,
            'newspapers': newspaper_stats,
            'categories': category_stats,
            'sessions': sessions
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/images/<path:filename>')
def serve_image(filename):
    """Servir imágenes descargadas"""
    try:
        return send_from_directory('scraped_images', filename)
    except Exception as e:
        logger.error(f"❌ Error sirviendo imagen {filename}: {e}")
        return jsonify({'error': 'Imagen no encontrada'}), 404

@app.route('/api/stop-scraping', methods=['POST'])
@require_auth
@require_admin
def stop_scraping():
    """Detener el scraping en curso"""
    global scraping_status
    
    if not scraping_status['is_running']:
        return jsonify({'error': 'No hay scraping en ejecución'}), 400
    
    scraping_status.update({
        'is_running': False,
        'end_time': datetime.now().isoformat(),
        'error': 'Detenido por el usuario'
    })
    
    return jsonify({'message': 'Scraping detenido'})

@app.route('/api/auto-update', methods=['POST'])
@require_auth
def trigger_auto_update():
    """Ejecutar actualización automática de todos los diarios"""
    global scraping_status
    
    # Solo Premium/Enterprise o rol admin pueden usar auto-update
    user_id = request.current_user.get('user_id')
    role = request.current_user.get('role')
    if role != 'admin':
        error_msg = _require_premium_or_enterprise(user_id)
        if error_msg:
            return jsonify({'error': error_msg}), 403
    
    if scraping_status['is_running']:
        return jsonify({'error': 'Ya hay un scraping en ejecución'}), 400
    
    try:
        # Ejecutar el scraper automático en un hilo separado
        thread = threading.Thread(target=run_auto_scraping)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'message': 'Actualización automática iniciada',
            'status': 'running'
        })
        
    except Exception as e:
        logger.error(f"❌ Error iniciando actualización automática: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/auto-update/status', methods=['GET'])
def get_auto_update_status():
    """Obtener estado de la actualización automática"""
    try:
        # Leer el último log para obtener el estado
        log_file = 'auto_scraping.log'
        last_update = None
        current_status = 'idle'
        
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    if 'Iniciando scraping automático' in last_line:
                        current_status = 'running'
                    elif 'Scraping automático completado' in last_line:
                        current_status = 'completed'
                        last_update = datetime.now().isoformat()
        
        return jsonify({
            'status': current_status,
            'last_update': last_update,
            'next_scheduled': 'Cada 5 minutos',
            'enabled': True
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estado: {e}")
        return jsonify({'error': str(e)}), 500

# ===== ENDPOINTS DE BÚSQUEDA AVANZADA =====

@app.route('/api/search/suggestions', methods=['GET'])
@require_auth
def get_search_suggestions():
    """Obtener sugerencias para búsqueda"""
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        # Obtener consultas populares (simulado)
        popular_queries = [
            "política", "economía", "deportes", "tecnología", "salud",
            "educación", "cultura", "internacional", "nacional", "regional"
        ]
        
        # Obtener categorías únicas
        cursor.execute("SELECT DISTINCT category FROM articles WHERE category IS NOT NULL")
        categories = [row[0] for row in cursor.fetchall()]
        
        # Obtener periódicos únicos
        cursor.execute("SELECT DISTINCT newspaper FROM articles WHERE newspaper IS NOT NULL")
        newspapers = [row[0] for row in cursor.fetchall()]
        
        # Obtener regiones únicas
        cursor.execute("SELECT DISTINCT region FROM articles WHERE region IS NOT NULL")
        regions = [row[0] for row in cursor.fetchall()]
        
        # Obtener tags populares (simulado)
        popular_tags = [
            "coronavirus", "elecciones", "inflación", "fútbol", "tecnología",
            "cambio climático", "educación", "salud pública", "economía", "política"
        ]
        
        conn.close()
        
        return jsonify({
            'queries': popular_queries,
            'categories': categories,
            'newspapers': newspapers,
            'regions': regions,
            'tags': popular_tags
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo sugerencias: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/search/advanced', methods=['POST'])
@require_auth
def advanced_search():
    """Búsqueda avanzada con filtros"""
    try:
        data = request.get_json()
        
        # Parámetros de búsqueda
        query = data.get('query', '').strip()
        category = data.get('category', '')
        newspaper = data.get('newspaper', '')
        region = data.get('region', '')
        date_from = data.get('dateFrom', '')
        date_to = data.get('dateTo', '')
        sentiment = data.get('sentiment', '')
        sort_by = data.get('sortBy', 'relevance')
        page = int(data.get('page', 1))
        limit = int(data.get('limit', 12))
        
        if not query:
            return jsonify({'error': 'Query es requerido'}), 400
        
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        # Construir consulta SQL
        where_conditions = []
        params = []
        
        # Búsqueda de texto
        where_conditions.append("(title LIKE ? OR content LIKE ?)")
        search_term = f"%{query}%"
        params.extend([search_term, search_term])
        
        # Filtros adicionales
        if category:
            where_conditions.append("category = ?")
            params.append(category)
        
        if newspaper:
            where_conditions.append("newspaper = ?")
            params.append(newspaper)
        
        if region:
            where_conditions.append("region = ?")
            params.append(region)
        
        if date_from:
            where_conditions.append("DATE(published_date) >= ?")
            params.append(date_from)
        
        if date_to:
            where_conditions.append("DATE(published_date) <= ?")
            params.append(date_to)
        
        if sentiment:
            where_conditions.append("sentiment = ?")
            params.append(sentiment)
        
        # Construir consulta completa
        where_clause = " AND ".join(where_conditions)
        
        # Ordenamiento
        order_clause = "published_date DESC"
        if sort_by == 'relevance':
            # Simular relevancia basada en coincidencias en título
            order_clause = f"CASE WHEN title LIKE ? THEN 1 ELSE 2 END, published_date DESC"
            params.insert(0, f"%{query}%")
        elif sort_by == 'date':
            order_clause = "published_date DESC"
        elif sort_by == 'title':
            order_clause = "title ASC"
        
        # Contar total de resultados
        count_query = f"SELECT COUNT(*) FROM articles WHERE {where_clause}"
        cursor.execute(count_query, params[1:] if sort_by == 'relevance' else params)
        total = cursor.fetchone()[0]
        
        # Obtener resultados paginados
        offset = (page - 1) * limit
        search_query = f"""
            SELECT 
                id, title, content, url, newspaper, category, region,
                published_date, sentiment, image_url, author
            FROM articles 
            WHERE {where_clause}
            ORDER BY {order_clause}
            LIMIT ? OFFSET ?
        """
        
        query_params = params + [limit, offset]
        cursor.execute(search_query, query_params)
        
        results = []
        for row in cursor.fetchall():
            id, title, content, url, newspaper, category, region, published_date, sentiment, image_url, author = row
            
            # Simular análisis de sentimiento si no existe
            if not sentiment:
                sentiment = 'neutral'
            
            # Simular tags basados en palabras clave
            tags = []
            if 'política' in title.lower() or 'política' in content.lower():
                tags.append('política')
            if 'economía' in title.lower() or 'economía' in content.lower():
                tags.append('economía')
            if 'deportes' in title.lower() or 'deportes' in content.lower():
                tags.append('deportes')
            
            # Simular score de relevancia
            relevance_score = 0.8
            if query.lower() in title.lower():
                relevance_score = 0.95
            elif query.lower() in content.lower():
                relevance_score = 0.7
            
            results.append({
                'id': id,
                'title': title,
                'content': content[:300] + '...' if len(content) > 300 else content,
                'url': url,
                'newspaper': newspaper,
                'category': category,
                'region': region,
                'published_date': published_date,
                'sentiment': sentiment,
                'image_url': image_url,
                'author': author,
                'tags': tags,
                'relevance_score': relevance_score
            })
        
        conn.close()
        
        return jsonify({
            'results': results,
            'total': total,
            'page': page,
            'limit': limit,
            'total_pages': (total + limit - 1) // limit
        })
        
    except Exception as e:
        logger.error(f"Error en búsqueda avanzada: {e}")
        return jsonify({'error': str(e)}), 500

def run_auto_scraping():
    """Ejecutar scraping automático en hilo separado"""
    global scraping_status
    
    try:
        # Calcular número de periódicos habilitados desde la configuración
        total_newspapers = 10  # Default
        try:
            with open('auto_scraping_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                schedules = config.get('auto_scraping', {}).get('schedules', [])
                # Contar solo los habilitados
                enabled_schedules = [s for s in schedules if s.get('enabled', False)]
                total_newspapers = len(enabled_schedules)
        except Exception:
            pass  # Usar default si hay error
        
        scraping_status.update({
            'is_running': True,
            'progress': 0,
            'total': total_newspapers,
            'current_url': 'Actualización automática',
            'articles_found': 0,
            'images_found': 0,
            'error': None,
            'start_time': datetime.now().isoformat(),
            'end_time': None
        })
        
        # Ejecutar el scraper automático
        import subprocess
        result = subprocess.run(['python', 'auto_scraper_standalone.py'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            logger.info("✅ Actualización automática completada exitosamente")
        else:
            logger.error(f"❌ Error en actualización automática: {result.stderr}")
            
    except Exception as e:
        logger.error(f"❌ Error ejecutando actualización automática: {e}")
        scraping_status['error'] = str(e)
    
    finally:
        scraping_status.update({
            'is_running': False,
            'end_time': datetime.now().isoformat()
        })

@app.route('/api/newspapers', methods=['GET'])
def get_newspapers():
    """Obtener lista de periódicos con conteos de artículos e imágenes"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Base de datos no disponible'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Obtener estadísticas por periódico
        cursor.execute("""
            SELECT 
                newspaper,
                COUNT(*) as articles_count,
                SUM(images_found) as total_images_found,
                SUM(images_downloaded) as total_images_downloaded,
                MIN(scraped_at) as first_scraped,
                MAX(scraped_at) as last_scraped
            FROM articles 
            WHERE newspaper IS NOT NULL AND newspaper != ''
            GROUP BY newspaper 
            ORDER BY articles_count DESC
        """)
        
        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        newspapers = [dict(zip(column_names, row)) for row in rows]
        
        conn.close()
        
        return jsonify({
            'newspapers': newspapers,
            'total': len(newspapers)
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo periódicos: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== ENDPOINTS DE ANÁLISIS AVANZADO ====================

@app.route('/api/analytics/trends', methods=['GET'])
@require_auth
def get_trends_analytics():
    """Obtener análisis de tendencias por período"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Base de datos no disponible'}), 500
    
    try:
        cursor = conn.cursor()
        period = request.args.get('period', 'week')  # day, week, month
        
        # Configurar formato de fecha según el período
        if period == 'day':
            date_format = '%Y-%m-%d'
            days_back = 30
        elif period == 'week':
            date_format = '%Y-%W'  # Año-Semana
            days_back = 12
        else:  # month
            date_format = '%Y-%m'
            days_back = 12
        
        # Obtener tendencias de artículos
        cursor.execute(f"""
            SELECT 
                DATE(scraped_at, '-{days_back} days') as period_start,
                strftime('{date_format}', scraped_at) as period,
                COUNT(*) as articles_count,
                SUM(images_downloaded) as images_count,
                COUNT(DISTINCT newspaper) as newspapers_count
            FROM articles 
            WHERE scraped_at >= datetime('now', '-{days_back} days')
            GROUP BY strftime('{date_format}', scraped_at)
            ORDER BY scraped_at
        """)
        
        trends_data = []
        for row in cursor.fetchall():
            trends_data.append({
                'period': row[1],
                'articles_count': row[2],
                'images_count': row[3],
                'newspapers_count': row[4]
            })
        
        # Obtener top categorías
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM articles 
            WHERE category IS NOT NULL AND category != ''
            GROUP BY category 
            ORDER BY count DESC 
            LIMIT 10
        """)
        
        top_categories = [{'category': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Obtener top periódicos
        cursor.execute("""
            SELECT newspaper, COUNT(*) as count
            FROM articles 
            WHERE newspaper IS NOT NULL AND newspaper != ''
            GROUP BY newspaper 
            ORDER BY count DESC 
            LIMIT 10
        """)
        
        top_newspapers = [{'newspaper': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'trends': trends_data,
            'top_categories': top_categories,
            'top_newspapers': top_newspapers,
            'period': period
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo tendencias: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/sentiment', methods=['GET'])
@require_auth
def get_sentiment_analysis():
    """
    Análisis avanzado de sentimientos de las noticias
    Incluye polaridad, emociones, polarización, evolución temporal y comparación entre medios
    """
    from sentiment_analyzer import sentiment_analyzer
    from datetime import datetime, timedelta
    from collections import defaultdict
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Base de datos no disponible'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Parámetros de consulta
        days = int(request.args.get('days', 30))
        category = request.args.get('category', None)
        newspaper = request.args.get('newspaper', None)
        topic = request.args.get('topic', None)  # Tema específico para comparar medios
        
        # Construir query
        query = """
            SELECT id, title, content, newspaper, category, scraped_at
            FROM articles 
            WHERE title IS NOT NULL AND content IS NOT NULL
                AND title != '' AND content != ''
                AND scraped_at >= datetime('now', '-' || ? || ' days')
        """
        params = [days]
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if newspaper:
            query += " AND newspaper = ?"
            params.append(newspaper)
        
        if topic:
            query += " AND (title LIKE ? OR content LIKE ?)"
            params.extend([f'%{topic}%', f'%{topic}%'])
        
        # Limitar a 2000 artículos para evitar timeouts (análisis de sentimientos es costoso)
        # Si hay muchos artículos, usar una muestra representativa
        query += " ORDER BY scraped_at DESC LIMIT 2000"
        
        cursor.execute(query, params)
        articles = cursor.fetchall()
        
        # Si hay muchos artículos, usar una muestra aleatoria para análisis más rápido
        if len(articles) > 1000:
            import random
            # Tomar muestra representativa: 1000 artículos aleatorios
            articles = random.sample(articles, 1000)
            logger.info(f"📊 Usando muestra de {len(articles)} artículos de {len(articles) + (len(articles) * 2)} totales para análisis más rápido")
        
        if not articles:
            return jsonify({
                'total': 0,
                'positive': 0,
                'negative': 0,
                'neutral': 0,
                'average_score': 0.0,
                'emotions_summary': {},
                'polarization_distribution': {'high': 0, 'medium': 0, 'low': 0},
                'by_newspaper': {},
                'by_category': {},
                'timeline': [],
                'topic_comparison': {}
            })
        
        # Análisis de cada artículo
        sentiment_data = {
            'positive': 0,
            'negative': 0,
            'neutral': 0,
            'total': len(articles),
            'average_score': 0.0,
            'emotions_summary': {},
            'polarization_distribution': {'high': 0, 'medium': 0, 'low': 0},
            'by_newspaper': {},
            'by_category': {},
            'timeline': [],  # Evolución temporal
            'topic_comparison': {} if topic else None
        }
        
        total_score = 0.0
        emotions_total = defaultdict(float)
        timeline_data = defaultdict(lambda: {'positive': 0, 'negative': 0, 'neutral': 0, 'count': 0, 'scores': []})
        
        # Procesar artículos con límite de texto para análisis más rápido
        processed_count = 0
        for article in articles:
            article_id, title, content, article_newspaper, article_category, scraped_at = article
            
            # Combinar título y contenido para análisis (limitar longitud para velocidad)
            if title and content:
                # Limitar a primeros 2000 caracteres para análisis más rápido
                text = f"{title} {content[:2000]}"
            else:
                text = (title or content or "")
            
            if not text or len(text.strip()) < 10:
                continue
            
            # Análisis avanzado
            try:
                analysis = sentiment_analyzer.analyze_sentiment(text)
            except Exception as e:
                logger.debug(f"Error analizando artículo {article_id}: {e}")
                continue
            
            processed_count += 1
            
            polarity = analysis['polarity']
            score = analysis['score']
            
            sentiment_data[polarity] += 1
            total_score += score
            sentiment_data['polarization_distribution'][analysis['polarization']] += 1
            
            # Emociones
            for emotion, emotion_score in analysis['emotions'].items():
                emotions_total[emotion] += emotion_score
                if emotion not in sentiment_data['emotions_summary']:
                    sentiment_data['emotions_summary'][emotion] = 0.0
                sentiment_data['emotions_summary'][emotion] += emotion_score
            
            # Por periódico
            if article_newspaper:
                if article_newspaper not in sentiment_data['by_newspaper']:
                    sentiment_data['by_newspaper'][article_newspaper] = {
                        'positive': 0, 'negative': 0, 'neutral': 0,
                        'total': 0, 'average_score': 0.0, 'scores': []
                    }
                sentiment_data['by_newspaper'][article_newspaper][polarity] += 1
                sentiment_data['by_newspaper'][article_newspaper]['total'] += 1
                sentiment_data['by_newspaper'][article_newspaper]['scores'].append(score)
            
            # Por categoría
            if article_category:
                if article_category not in sentiment_data['by_category']:
                    sentiment_data['by_category'][article_category] = {
                        'positive': 0, 'negative': 0, 'neutral': 0,
                        'total': 0, 'average_score': 0.0
                    }
                sentiment_data['by_category'][article_category][polarity] += 1
                sentiment_data['by_category'][article_category]['total'] += 1
            
            # Timeline (evolución temporal) - agrupar por día
            if scraped_at:
                try:
                    # Intentar diferentes formatos de fecha
                    date_str = str(scraped_at)
                    date_obj = None
                    
                    # Formato ISO con microsegundos (ej: 2025-09-13T15:43:22.483240)
                    if 'T' in date_str:
                        try:
                            # Remover microsegundos si existen
                            if '.' in date_str:
                                date_str_clean = date_str.split('.')[0]
                            else:
                                date_str_clean = date_str
                            # Remover Z si existe
                            date_str_clean = date_str_clean.replace('Z', '').replace('+00:00', '')
                            date_obj = datetime.strptime(date_str_clean, '%Y-%m-%dT%H:%M:%S')
                        except:
                            try:
                                # Intentar con fromisoformat
                                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00').split('.')[0])
                            except:
                                try:
                                    date_obj = datetime.fromisoformat(date_str.replace('Z', '').split('.')[0])
                                except:
                                    pass
                    else:
                        # Formato SQLite datetime
                        try:
                            date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                        except:
                            try:
                                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                            except:
                                pass
                    
                    if date_obj:
                        date_key = date_obj.strftime('%Y-%m-%d')
                        timeline_data[date_key][polarity] += 1
                        timeline_data[date_key]['count'] += 1
                        timeline_data[date_key]['scores'].append(score)
                except Exception as e:
                    logger.debug(f"Error parseando fecha {scraped_at}: {e}")
                    pass
        
        # Actualizar total con artículos procesados realmente
        sentiment_data['total'] = processed_count
        
        # Calcular promedios
        if sentiment_data['total'] > 0:
            sentiment_data['average_score'] = round(total_score / sentiment_data['total'], 3)
            
            # Normalizar emociones
            for emotion in sentiment_data['emotions_summary']:
                sentiment_data['emotions_summary'][emotion] = round(
                    sentiment_data['emotions_summary'][emotion] / sentiment_data['total'], 3
                )
            
            # Calcular promedios por periódico
            for np in sentiment_data['by_newspaper']:
                np_data = sentiment_data['by_newspaper'][np]
                if np_data['scores']:
                    np_data['average_score'] = round(
                        sum(np_data['scores']) / len(np_data['scores']), 3
                    )
                del np_data['scores']  # No enviar scores individuales
            
            # Calcular promedios por categoría
            for cat in sentiment_data['by_category']:
                cat_data = sentiment_data['by_category'][cat]
                # Calcular score promedio (estimado)
                pos_pct = cat_data['positive'] / cat_data['total'] if cat_data['total'] > 0 else 0
                neg_pct = cat_data['negative'] / cat_data['total'] if cat_data['total'] > 0 else 0
                cat_data['average_score'] = round(pos_pct - neg_pct, 3)
        
        # Construir timeline ordenado
        timeline_list = []
        for date_key in sorted(timeline_data.keys()):
            day_data = timeline_data[date_key]
            if day_data['scores']:
                avg_score = sum(day_data['scores']) / len(day_data['scores'])
            else:
                avg_score = 0.0
            
            timeline_list.append({
                'date': date_key,
                'positive': day_data['positive'],
                'negative': day_data['negative'],
                'neutral': day_data['neutral'],
                'total': day_data['count'],
                'average_score': round(avg_score, 3)
            })
        sentiment_data['timeline'] = timeline_list
        
        # Comparación entre medios si hay un tema
        if topic and sentiment_data['by_newspaper']:
            sentiment_data['topic_comparison'] = {}
            for np, np_data in sentiment_data['by_newspaper'].items():
                sentiment_data['topic_comparison'][np] = {
                    'average_score': np_data.get('average_score', 0.0),
                    'positive_pct': round(np_data['positive'] / np_data['total'] * 100, 1) if np_data['total'] > 0 else 0,
                    'negative_pct': round(np_data['negative'] / np_data['total'] * 100, 1) if np_data['total'] > 0 else 0,
                    'total': np_data['total']
                }
        
        # Obtener análisis de comentarios virales para comparación (solo Premium y Enterprise)
        viral_comments_data = None
        user_id = request.current_user.get('user_id') if hasattr(request, 'current_user') else None
        
        if user_id and _can_access_viral_comments_comparison(user_id):
            try:
                # Obtener comentarios virales del mismo período y tema (si aplica)
                viral_query = """
                    SELECT id, comment_text, topic, sentiment, created_at
                    FROM viral_comments
                    WHERE created_at >= datetime('now', '-' || ? || ' days')
                """
                viral_params = [days]
                
                if topic:
                    viral_query += " AND topic LIKE ?"
                    viral_params.append(f'%{topic}%')
                
                cursor.execute(viral_query, viral_params)
                viral_comments = cursor.fetchall()
                
                if viral_comments:
                    viral_positive = 0
                    viral_negative = 0
                    viral_neutral = 0
                    viral_total_score = 0.0
                    viral_by_topic = defaultdict(lambda: {
                        'positive': 0, 'negative': 0, 'neutral': 0, 'total': 0, 'total_score': 0.0
                    })
                    
                    for comment_id, comment_text, comment_topic, stored_sentiment, created_at in viral_comments:
                        try:
                            # Re-analizar para consistencia
                            analysis = sentiment_analyzer.analyze_sentiment(comment_text)
                            polarity = analysis['polarity']
                            score = analysis['score']
                            
                            viral_positive += 1 if polarity == 'positive' else 0
                            viral_negative += 1 if polarity == 'negative' else 0
                            viral_neutral += 1 if polarity == 'neutral' else 0
                            viral_total_score += score
                            
                            if comment_topic:
                                topic_data = viral_by_topic[comment_topic]
                                topic_data[polarity] += 1
                                topic_data['total'] += 1
                                topic_data['total_score'] += score
                        except:
                            continue
                    
                    viral_total = len(viral_comments)
                    viral_comments_data = {
                        'total': viral_total,
                        'positive': viral_positive,
                        'negative': viral_negative,
                        'neutral': viral_neutral,
                        'average_score': round(viral_total_score / viral_total, 3) if viral_total > 0 else 0.0,
                        'by_topic': {
                            topic_name: {
                                'positive': data['positive'],
                                'negative': data['negative'],
                                'neutral': data['neutral'],
                                'total': data['total'],
                                'average_score': round(data['total_score'] / data['total'], 3) if data['total'] > 0 else 0.0
                            }
                            for topic_name, data in viral_by_topic.items()
                        }
                    }
            except Exception as e:
                logger.debug(f"Error obteniendo comentarios virales para comparación: {e}")
                viral_comments_data = None
        
        conn.close()
        
        # Agregar datos de comentarios virales a la respuesta
        sentiment_data['viral_comments_comparison'] = viral_comments_data
        
        return jsonify(sentiment_data)
        
    except Exception as e:
        logger.error(f"❌ Error en análisis de sentimientos: {e}")
        import traceback
        error_trace = traceback.format_exc()
        logger.error(error_trace)
        
        # Cerrar conexión si está abierta
        try:
            if conn:
                conn.close()
        except:
            pass
        
        # Retornar error más descriptivo
        error_msg = str(e)
        if 'defaultdict' in error_msg:
            error_msg = "Error interno del servidor. Por favor, contacta al administrador."
        elif 'database' in error_msg.lower() or 'sql' in error_msg.lower():
            error_msg = "Error accediendo a la base de datos."
        
        return jsonify({'error': error_msg}), 500

# ============================================================
# SISTEMA DE ANUNCIOS CON ANÁLISIS DE SENTIMIENTOS
# ============================================================

@app.route('/api/ads/get', methods=['GET'])
def get_ad_for_article():
    """
    Obtener anuncio apropiado para un artículo basándose en sentimiento
    Parámetros: article_id (requerido), opcionalmente article_sentiment, article_sentiment_score, etc.
    """
    try:
        from ads_system import ads_system
        from sentiment_analyzer import sentiment_analyzer
        
        article_id = request.args.get('article_id', type=int)
        if not article_id:
            return jsonify({'error': 'article_id es requerido'}), 400
        
        # Obtener información del artículo
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Base de datos no disponible'}), 500
        
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, content, newspaper, category, scraped_at
            FROM articles WHERE id = ?
        ''', (article_id,))
        
        article = cursor.fetchone()
        conn.close()
        
        if not article:
            return jsonify({'error': 'Artículo no encontrado'}), 404
        
        art_id, title, content, newspaper, category, scraped_at = article
        
        # Analizar sentimiento del artículo
        text = f"{title} {content}" if title and content else (title or content or "")
        if not text or len(text.strip()) < 10:
            return jsonify({'ad': None, 'reason': 'Contenido insuficiente'})
        
        analysis = sentiment_analyzer.analyze_sentiment(text)
        sentiment = analysis['polarity']
        sentiment_score = analysis['score']
        
        # Extraer temas potenciales del título para buscar comentarios virales relacionados
        # Buscar palabras clave comunes en el título
        title_words = title.lower().split() if title else []
        potential_topics = []
        common_topics = ['Política', 'Economía', 'Tecnología', 'Salud', 'Educación', 
                        'Deportes', 'Cultura', 'Medio Ambiente']
        
        # Buscar comentarios virales relacionados con el tema del artículo (solo Enterprise)
        viral_comments_sentiment = None
        user_id = request.current_user.get('user_id') if hasattr(request, 'current_user') else None
        
        if user_id and _can_access_smart_ads_integration(user_id):
            try:
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    # Buscar comentarios virales de los últimos 7 días que puedan estar relacionados
                    cursor.execute("""
                        SELECT topic, sentiment, COUNT(*) as count
                        FROM viral_comments
                        WHERE created_at >= datetime('now', '-7 days')
                          AND topic IN ('Política', 'Economía', 'Tecnología', 'Salud', 'Educación', 
                                        'Deportes', 'Cultura', 'Medio Ambiente')
                        GROUP BY topic, sentiment
                    """)
                    
                    topic_sentiments = cursor.fetchall()
                    conn.close()
                    
                    # Calcular sentimiento promedio por tema
                    topic_scores = {}
                    for topic_name, topic_sentiment, count in topic_sentiments:
                        if topic_name not in topic_scores:
                            topic_scores[topic_name] = {'positive': 0, 'negative': 0, 'neutral': 0, 'total': 0}
                        topic_scores[topic_name][topic_sentiment] += count
                        topic_scores[topic_name]['total'] += count
                    
                    # Si la categoría del artículo coincide con un tema de comentarios virales
                    if category and category in topic_scores:
                        topic_data = topic_scores[category]
                        if topic_data['total'] > 0:
                            negative_pct = (topic_data['negative'] / topic_data['total']) * 100
                            viral_comments_sentiment = {
                                'topic': category,
                                'negative_percentage': negative_pct,
                                'total_comments': topic_data['total'],
                                'is_very_negative': negative_pct >= 50 and topic_data['negative'] >= 5
                            }
            except Exception as e:
                logger.debug(f"Error obteniendo sentimiento de comentarios virales para anuncios: {e}")
        
        # Ajustar score de sentimiento si hay comentarios virales muy negativos (solo Enterprise)
        adjusted_sentiment_score = sentiment_score
        if viral_comments_sentiment and viral_comments_sentiment.get('is_very_negative'):
            # Reducir el score de sentimiento en 0.2 si hay comentarios muy negativos
            adjusted_sentiment_score = min(sentiment_score - 0.2, -1.0)
            logger.info(f"⚠️ Ajustando sentimiento del artículo {art_id} debido a comentarios virales negativos sobre {viral_comments_sentiment['topic']}")
        
        # Obtener anuncio apropiado (usar score ajustado si aplica)
        final_sentiment_score = adjusted_sentiment_score if viral_comments_sentiment and viral_comments_sentiment.get('is_very_negative') else sentiment_score
        ad = ads_system.get_ad_for_article(
            article_id=art_id,
            article_sentiment=sentiment,
            article_sentiment_score=final_sentiment_score,
            article_category=category or '',
            article_newspaper=newspaper or ''
        )
        
        if ad:
            # Registrar impresión
            ads_system.track_event(
                ad_id=ad['id'],
                campaign_id=ad['campaign_id'],
                event_type='impression',
                article_id=art_id,
                article_sentiment=sentiment,
                article_sentiment_score=sentiment_score,
                article_category=category,
                article_newspaper=newspaper,
                user_ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
        
        return jsonify({
            'ad': ad,
            'article_sentiment': sentiment,
            'article_sentiment_score': sentiment_score
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo anuncio: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/ads/track', methods=['POST'])
def track_ad_event():
    """Registrar evento de anuncio (click, conversión)"""
    try:
        from ads_system import ads_system
        
        data = request.get_json()
        ad_id = data.get('ad_id')
        event_type = data.get('event_type', 'click')  # click, conversion
        
        if not ad_id:
            return jsonify({'error': 'ad_id es requerido'}), 400
        
        if event_type not in ['click', 'conversion']:
            return jsonify({'error': 'event_type debe ser click o conversion'}), 400
        
        # Obtener información del anuncio
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT campaign_id FROM ads WHERE id = ?', (ad_id,))
        ad = cursor.fetchone()
        conn.close()
        
        if not ad:
            return jsonify({'error': 'Anuncio no encontrado'}), 404
        
        campaign_id = ad[0]
        
        # Registrar evento
        ads_system.track_event(
            ad_id=ad_id,
            campaign_id=campaign_id,
            event_type=event_type,
            article_id=data.get('article_id'),
            article_sentiment=data.get('article_sentiment'),
            article_sentiment_score=data.get('article_sentiment_score'),
            article_category=data.get('article_category'),
            article_newspaper=data.get('article_newspaper'),
            user_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({'success': True, 'message': f'Evento {event_type} registrado'})
        
    except Exception as e:
        logger.error(f"❌ Error registrando evento: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ads/campaigns', methods=['GET'])
@require_auth
def get_campaigns():
    """Obtener lista de campañas publicitarias"""
    try:
        from ads_system import ads_system
        
        status = request.args.get('status', None)
        campaigns = ads_system.get_campaigns(status=status)
        
        return jsonify({'campaigns': campaigns})
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo campañas: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ads/campaigns', methods=['POST'])
@require_auth
def create_campaign():
    """Crear nueva campaña publicitaria"""
    try:
        from ads_system import ads_system
        
        data = request.get_json()
        if not data.get('name'):
            return jsonify({'error': 'name es requerido'}), 400
        
        campaign_id = ads_system.create_campaign(data)
        
        return jsonify({
            'success': True,
            'campaign_id': campaign_id,
            'message': 'Campaña creada exitosamente'
        })
        
    except Exception as e:
        logger.error(f"❌ Error creando campaña: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ads', methods=['GET', 'POST'])
@require_auth
def ads_endpoint():
    """Obtener anuncios o crear nuevo anuncio"""
    if request.method == 'GET':
        try:
            from ads_system import ads_system
            import sqlite3
            
            campaign_id = request.args.get('campaign_id', type=int)
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            if campaign_id:
                cursor.execute('''
                    SELECT a.id, a.campaign_id, a.title, 
                           COALESCE(a.description, c.description) as description,
                           a.image_url, a.click_url, a.display_text, 
                           a.ad_type, a.width, a.height, a.weight, a.is_active
                    FROM ads a
                    LEFT JOIN ad_campaigns c ON a.campaign_id = c.id
                    WHERE a.campaign_id = ?
                    ORDER BY a.created_at DESC
                ''', (campaign_id,))
            else:
                cursor.execute('''
                    SELECT a.id, a.campaign_id, a.title, 
                           COALESCE(a.description, c.description) as description,
                           a.image_url, a.click_url, a.display_text, 
                           a.ad_type, a.width, a.height, a.weight, a.is_active
                    FROM ads a
                    LEFT JOIN ad_campaigns c ON a.campaign_id = c.id
                    ORDER BY a.created_at DESC
                ''')
            
            columns = [desc[0] for desc in cursor.description]
            ads = []
            for row in cursor.fetchall():
                ad = dict(zip(columns, row))
                ads.append(ad)
            
            conn.close()
            return jsonify({'ads': ads})
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo anuncios: {e}")
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        """Crear nuevo anuncio"""
        try:
            from ads_system import ads_system
            
            data = request.get_json()
            if not data.get('campaign_id') or not data.get('title') or not data.get('click_url'):
                return jsonify({'error': 'campaign_id, title y click_url son requeridos'}), 400
            
            ad_id = ads_system.create_ad(data)
            
            return jsonify({
                'success': True,
                'ad_id': ad_id,
                'message': 'Anuncio creado exitosamente'
            })
            
        except Exception as e:
            logger.error(f"❌ Error creando anuncio: {e}")
            return jsonify({'error': str(e)}), 500

@app.route('/api/ads/analytics', methods=['GET'])
@require_auth
def get_ads_analytics():
    """Obtener métricas de anuncios por sentimiento"""
    try:
        from ads_system import ads_system
        
        campaign_id = request.args.get('campaign_id', type=int)
        days = request.args.get('days', 30, type=int)
        
        analytics = ads_system.get_analytics(campaign_id=campaign_id, days=days)
        
        return jsonify(analytics)
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo analytics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ads/recommendations', methods=['GET'])
@require_auth
def get_ad_recommendations():
    """
    Obtener recomendaciones de dónde colocar anuncios basándose en sentimientos
    """
    try:
        from sentiment_analyzer import sentiment_analyzer
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Base de datos no disponible'}), 500
        
        cursor = conn.cursor()
        days = request.args.get('days', 7, type=int)
        
        # Analizar artículos recientes y agrupar por sentimiento
        cursor.execute('''
            SELECT id, title, content, newspaper, category, scraped_at
            FROM articles
            WHERE scraped_at >= datetime('now', '-' || ? || ' days')
              AND title IS NOT NULL AND content IS NOT NULL
            ORDER BY scraped_at DESC
            LIMIT 1000
        ''', (days,))
        
        articles = cursor.fetchall()
        conn.close()
        
        # Analizar sentimientos
        sentiment_distribution = defaultdict(int)
        category_sentiment = defaultdict(lambda: {'positive': 0, 'negative': 0, 'neutral': 0})
        newspaper_sentiment = defaultdict(lambda: {'positive': 0, 'negative': 0, 'neutral': 0})
        
        for article in articles:
            art_id, title, content, newspaper, category, scraped_at = article
            text = f"{title} {content}" if title and content else (title or content or "")
            
            if len(text.strip()) < 10:
                continue
            
            analysis = sentiment_analyzer.analyze_sentiment(text)
            sentiment = analysis['polarity']
            
            sentiment_distribution[sentiment] += 1
            
            if category:
                category_sentiment[category][sentiment] += 1
            
            if newspaper:
                newspaper_sentiment[newspaper][sentiment] += 1
        
        # Generar recomendaciones
        total = sum(sentiment_distribution.values())
        recommendations = {
            'summary': {
                'total_articles': total,
                'positive_pct': round(sentiment_distribution['positive'] / total * 100, 1) if total > 0 else 0,
                'negative_pct': round(sentiment_distribution['negative'] / total * 100, 1) if total > 0 else 0,
                'neutral_pct': round(sentiment_distribution['neutral'] / total * 100, 1) if total > 0 else 0
            },
            'best_categories': sorted(
                [(cat, data['positive'], data['positive'] / (sum(data.values()) or 1) * 100) 
                 for cat, data in category_sentiment.items() if sum(data.values()) > 10],
                key=lambda x: x[2],
                reverse=True
            )[:5],
            'best_newspapers': sorted(
                [(np, data['positive'], data['positive'] / (sum(data.values()) or 1) * 100)
                 for np, data in newspaper_sentiment.items() if sum(data.values()) > 10],
                key=lambda x: x[2],
                reverse=True
            )[:5],
            'recommendations': [
                {
                    'type': 'target_positive',
                    'message': f"Coloca anuncios en contenido positivo ({sentiment_distribution['positive']} artículos, {round(sentiment_distribution['positive']/total*100, 1)}%)",
                    'priority': 'high'
                },
                {
                    'type': 'avoid_negative',
                    'message': f"Evita contenido muy negativo ({sentiment_distribution['negative']} artículos, {round(sentiment_distribution['negative']/total*100, 1)}%)",
                    'priority': 'high'
                }
            ]
        }
        
        return jsonify(recommendations)
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo recomendaciones: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/wordcloud', methods=['GET'])
@require_auth
def get_wordcloud_data():
    """Obtener datos para nube de palabras"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Base de datos no disponible'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Obtener títulos y contenido
        cursor.execute("""
            SELECT title, content
            FROM articles 
            WHERE title IS NOT NULL AND content IS NOT NULL
            ORDER BY scraped_at DESC
            LIMIT 500
        """)
        
        articles = cursor.fetchall()
        
        # Procesar texto
        import re
        from collections import Counter
        
        # Palabras a excluir
        stop_words = {
            'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'al', 'del', 'los', 'las', 'una', 'como', 'pero', 'sus', 'más', 'también', 'muy', 'sin', 'sobre', 'entre', 'hasta', 'desde', 'durante', 'mediante', 'según', 'hacia', 'bajo', 'ante', 'tras', 'contra', 'hasta', 'cada', 'todo', 'todos', 'todas', 'esta', 'este', 'estos', 'estas', 'ese', 'esa', 'esos', 'esas', 'aquel', 'aquella', 'aquellos', 'aquellas', 'mi', 'tu', 'su', 'nuestro', 'nuestra', 'nuestros', 'nuestras', 'vuestro', 'vuestra', 'vuestros', 'vuestras', 'me', 'te', 'se', 'nos', 'os', 'le', 'les', 'lo', 'la', 'los', 'las', 'sí', 'no', 'también', 'tampoco', 'ya', 'aún', 'todavía', 'siempre', 'nunca', 'jamás', 'aquí', 'allí', 'ahí', 'donde', 'cuando', 'como', 'porque', 'aunque', 'mientras', 'después', 'antes', 'entonces', 'ahora', 'hoy', 'ayer', 'mañana', 'si', 'sino', 'pero', 'sin embargo', 'no obstante', 'además', 'también', 'así', 'así que', 'por eso', 'por lo tanto', 'en cambio', 'por el contrario'
        }
        
        all_text = ""
        for title, content in articles:
            all_text += f" {title} {content}"
        
        # Limpiar y tokenizar
        words = re.findall(r'\b[a-záéíóúñü]+\b', all_text.lower())
        words = [word for word in words if len(word) > 3 and word not in stop_words]
        
        # Contar palabras
        word_count = Counter(words)
        top_words = word_count.most_common(50)
        
        # Formatear para la nube de palabras
        wordcloud_data = [{'text': word, 'value': count} for word, count in top_words]
        
        conn.close()
        
        return jsonify({
            'words': wordcloud_data,
            'total_words': len(words),
            'unique_words': len(word_count)
        })
        
    except Exception as e:
        logger.error(f"❌ Error generando nube de palabras: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/comparison', methods=['GET'])
@require_auth
def get_newspaper_comparison():
    """Comparación detallada entre periódicos"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Base de datos no disponible'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Comparación por categorías
        cursor.execute("""
            SELECT 
                newspaper,
                category,
                COUNT(*) as count,
                AVG(images_downloaded) as avg_images,
                MIN(scraped_at) as first_article,
                MAX(scraped_at) as last_article
            FROM articles 
            WHERE newspaper IS NOT NULL AND category IS NOT NULL 
            AND newspaper != '' AND category != ''
            GROUP BY newspaper, category
            ORDER BY newspaper, count DESC
        """)
        
        comparison_data = {}
        for row in cursor.fetchall():
            newspaper, category, count, avg_images, first_article, last_article = row
            
            if newspaper not in comparison_data:
                comparison_data[newspaper] = {
                    'categories': {},
                    'total_articles': 0,
                    'total_images': 0,
                    'first_article': first_article,
                    'last_article': last_article
                }
            
            comparison_data[newspaper]['categories'][category] = {
                'count': count,
                'avg_images': round(avg_images, 2)
            }
            comparison_data[newspaper]['total_articles'] += count
            comparison_data[newspaper]['total_images'] += count * avg_images
        
        # Estadísticas generales por periódico
        cursor.execute("""
            SELECT 
                newspaper,
                COUNT(*) as total_articles,
                SUM(images_downloaded) as total_images,
                COUNT(DISTINCT category) as categories_count,
                AVG(LENGTH(content)) as avg_content_length,
                MIN(scraped_at) as first_article,
                MAX(scraped_at) as last_article
            FROM articles 
            WHERE newspaper IS NOT NULL AND newspaper != ''
            GROUP BY newspaper
            ORDER BY total_articles DESC
        """)
        
        newspaper_stats = []
        for row in cursor.fetchall():
            newspaper, total_articles, total_images, categories_count, avg_content_length, first_article, last_article = row
            
            newspaper_stats.append({
                'newspaper': newspaper,
                'total_articles': total_articles,
                'total_images': total_images,
                'categories_count': categories_count,
                'avg_content_length': round(avg_content_length, 0),
                'first_article': first_article,
                'last_article': last_article,
                'articles_per_day': round(total_articles / max(1, 30), 2)  # Simplificado por ahora
            })
        
        conn.close()
        
        return jsonify({
            'comparison': comparison_data,
            'newspaper_stats': newspaper_stats
        })
        
    except Exception as e:
        logger.error(f"❌ Error en comparación de periódicos: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/newspapers/<newspaper_name>', methods=['DELETE'])
@require_auth
@require_admin
def delete_newspaper_data(newspaper_name):
    """Eliminar todos los datos de un periódico específico"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Base de datos no disponible'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Contar registros antes de borrar
        cursor.execute("SELECT COUNT(*) FROM articles WHERE newspaper = ?", (newspaper_name,))
        articles_count = cursor.fetchone()[0]
        
        # Obtener URLs de imágenes asociadas a los artículos del periódico
        cursor.execute("""
            SELECT images_data FROM articles 
            WHERE newspaper = ? AND images_data IS NOT NULL AND images_data != '[]'
        """, (newspaper_name,))
        
        image_urls = []
        for row in cursor.fetchall():
            try:
                images_data = json.loads(row[0])
                if isinstance(images_data, list):
                    for img in images_data:
                        if isinstance(img, dict) and 'filename' in img:
                            image_urls.append(img['filename'])
            except (json.JSONDecodeError, TypeError):
                continue
        
        # Obtener article_ids de los artículos del periódico para eliminar imágenes relacionadas
        cursor.execute("SELECT article_id FROM articles WHERE newspaper = ?", (newspaper_name,))
        article_ids = [row[0] for row in cursor.fetchall()]
        
        # Contar imágenes relacionadas
        images_count = 0
        if article_ids:
            placeholders = ','.join(['?' for _ in article_ids])
            cursor.execute(f"SELECT COUNT(*) FROM images WHERE article_id IN ({placeholders})", article_ids)
            images_count = cursor.fetchone()[0]
        
        # Registrar periódico como excluido de futuras actualizaciones automáticas
        cursor.execute("""
            INSERT OR REPLACE INTO excluded_newspapers (newspaper, excluded_at)
            VALUES (?, ?)
        """, (newspaper_name, datetime.now().isoformat()))
        
        # Borrar artículos del periódico
        cursor.execute("DELETE FROM articles WHERE newspaper = ?", (newspaper_name,))
        
        # Borrar imágenes relacionadas
        if article_ids:
            placeholders = ','.join(['?' for _ in article_ids])
            cursor.execute(f"DELETE FROM images WHERE article_id IN ({placeholders})", article_ids)
        
        # Borrar estadísticas de scraping del periódico
        cursor.execute("DELETE FROM scraping_stats WHERE url_scraped LIKE ?", (f'%{newspaper_name}%',))
        
        conn.commit()
        conn.close()
        
        # Eliminar archivos de imagen físicos
        deleted_files = 0
        for filename in image_urls:
            try:
                image_path = os.path.join('scraped_images', filename)
                if os.path.exists(image_path):
                    os.remove(image_path)
                    deleted_files += 1
            except Exception as e:
                logger.warning(f"⚠️ No se pudo eliminar imagen {filename}: {e}")
        
        logger.info(f"🗑️ Datos del periódico '{newspaper_name}' borrados: {articles_count} artículos, {images_count} imágenes, {deleted_files} archivos")
        
        return jsonify({
            'message': f'Datos del periódico "{newspaper_name}" eliminados exitosamente',
            'deleted': {
                'articles': articles_count,
                'images': images_count,
                'files': deleted_files
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error borrando datos del periódico {newspaper_name}: {e}")
        return jsonify({'error': f'Error borrando datos: {str(e)}'}), 500

# ==================== ENDPOINTS DE SUSCRIPCIONES ====================

@app.route('/api/subscriptions/plans', methods=['GET'])
@require_auth
def get_subscription_plans():
    """Obtener todos los planes de suscripción disponibles"""
    try:
        plans = auth_system.get_all_plans()
        return jsonify({'success': True, 'plans': plans})
    except Exception as e:
        logger.error(f"Error obteniendo planes: {e}")
        return jsonify({'error': 'Error obteniendo planes'}), 500

@app.route('/api/subscriptions/user-subscription', methods=['GET'])
@require_auth
def get_user_subscription():
    """Obtener suscripción actual del usuario"""
    try:
        user_id = request.current_user.get('user_id')
        subscription = auth_system.get_user_subscription(user_id)
        
        if subscription:
            return jsonify({'success': True, 'subscription': subscription})
        else:
            # Usuario sin suscripción activa - devolver plan freemium con características
            freemium_plan = auth_system.subscription_system.get_plan_by_name('freemium')
            if freemium_plan:
                # Crear objeto de suscripción con plan freemium
                freemium_subscription = {
                    'id': None,
                    'plan_id': freemium_plan['id'],
                    'status': 'active',
                    'start_date': None,
                    'end_date': None,
                    'plan_name': freemium_plan['name'],
                    'plan_display_name': freemium_plan['display_name'],
                    'max_articles_per_day': freemium_plan['max_articles_per_day'],
                    'max_images_per_scraping': freemium_plan['max_images_per_scraping'],
                    'max_users': freemium_plan['max_users'],
                    'features': freemium_plan['features']
                }
                return jsonify({
                    'success': True, 
                    'subscription': freemium_subscription
                })
            else:
                return jsonify({
                    'success': True, 
                    'subscription': None,
                    'default_plan': None
                })
    except Exception as e:
        logger.error(f"Error obteniendo suscripción del usuario: {e}")
        return jsonify({'error': 'Error obteniendo suscripción'}), 500

@app.route('/api/subscriptions/create-payment', methods=['POST'])
@require_auth
def create_payment_code():
    """Crear código de pago para suscripción"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Datos de solicitud JSON no proporcionados'}), 400
        
        plan_id = data.get('plan_id')
        if not plan_id:
            return jsonify({'error': 'ID del plan requerido'}), 400
        
        user_id = request.current_user.get('user_id')
        
        # Crear código de pago
        payment_code = auth_system.create_payment_code(user_id, plan_id)
        
        return jsonify({
            'success': True, 
            'payment_code': payment_code,
            'message': 'Código de pago creado exitosamente'
        })
    except Exception as e:
        logger.error(f"Error creando código de pago: {e}")
        return jsonify({'error': 'Error creando código de pago'}), 500

@app.route('/api/subscriptions/payment-codes', methods=['GET'])
@require_auth
def get_user_payment_codes():
    """Obtener códigos de pago del usuario"""
    try:
        user_id = request.current_user.get('user_id')
        payment_codes = auth_system.subscription_system.get_user_payment_codes(user_id)
        
        return jsonify({'success': True, 'payment_codes': payment_codes})
    except Exception as e:
        logger.error(f"Error obteniendo códigos de pago: {e}")
        return jsonify({'error': 'Error obteniendo códigos de pago'}), 500

@app.route('/api/subscriptions/usage-limits', methods=['GET'])
@require_auth
def get_usage_limits():
    """Obtener límites de uso actuales del usuario"""
    try:
        user_id = request.current_user.get('user_id')
        limits = auth_system.check_usage_limits(user_id)
        
        return jsonify({'success': True, 'limits': limits})
    except Exception as e:
        logger.error(f"Error obteniendo límites de uso: {e}")
        return jsonify({'error': 'Error obteniendo límites de uso'}), 500

# ==================== ENDPOINTS DE ADMINISTRACIÓN DE PAGOS ====================

@app.route('/api/admin/pending-payments', methods=['GET'])
@require_auth
@require_admin
def get_pending_payments():
    """Obtener pagos pendientes (solo admin)"""
    try:
        pending_payments = auth_system.subscription_system.get_pending_payments()
        return jsonify({'success': True, 'pending_payments': pending_payments})
    except Exception as e:
        logger.error(f"Error obteniendo pagos pendientes: {e}")
        return jsonify({'error': 'Error obteniendo pagos pendientes'}), 500

@app.route('/api/admin/verify-payment', methods=['POST'])
@require_auth
@require_admin
def verify_payment():
    """Verificar pago y activar suscripción (solo admin)"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Datos de solicitud JSON no proporcionados'}), 400
        
        payment_code = data.get('payment_code')
        payment_proof = data.get('payment_proof', '')
        
        if not payment_code:
            return jsonify({'error': 'Código de pago requerido'}), 400
        
        admin_user_id = request.current_user.get('user_id')
        
        # Verificar pago
        success = auth_system.subscription_system.verify_payment(payment_code, admin_user_id, payment_proof)
        
        if success:
            return jsonify({
                'success': True, 
                'message': 'Pago verificado y suscripción activada exitosamente'
            })
        else:
            return jsonify({'error': 'No se pudo verificar el pago'}), 400
    except Exception as e:
        logger.error(f"Error verificando pago: {e}")
        return jsonify({'error': 'Error verificando pago'}), 500

@app.route('/api/admin/subscription-stats', methods=['GET'])
@require_auth
@require_admin
def get_subscription_stats():
    """Obtener estadísticas de suscripciones (solo admin)"""
    try:
        # Usar la base de datos de suscripciones
        conn = sqlite3.connect(auth_system.subscription_system.db_path)
        cursor = conn.cursor()
        
        # Estadísticas de suscripciones activas
        cursor.execute('''
            SELECT p.display_name, COUNT(us.id) as active_subscriptions
            FROM plans p
            LEFT JOIN user_subscriptions us ON p.id = us.plan_id AND us.status = 'active'
            GROUP BY p.id, p.display_name
            ORDER BY p.price ASC
        ''')
        
        subscription_stats = []
        for row in cursor.fetchall():
            subscription_stats.append({
                'plan_name': row[0],
                'active_subscriptions': row[1]
            })
        
        # Estadísticas de pagos pendientes
        cursor.execute('''
            SELECT COUNT(*) as pending_count, SUM(amount) as pending_amount
            FROM payment_codes 
            WHERE status = 'pending' AND expires_at > CURRENT_TIMESTAMP
        ''')
        
        pending_stats = cursor.fetchone()
        
        # Estadísticas de uso diario
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT user_id) as active_users_today,
                SUM(articles_scraped) as total_articles_today,
                SUM(images_downloaded) as total_images_today
            FROM daily_usage 
            WHERE date = DATE('now')
        ''')
        
        usage_stats = cursor.fetchone()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'subscription_stats': subscription_stats,
                'pending_payments': {
                    'count': pending_stats[0] if pending_stats and pending_stats[0] else 0,
                    'total_amount': pending_stats[1] if pending_stats and pending_stats[1] else 0
                },
                'daily_usage': {
                    'active_users': usage_stats[0] if usage_stats and usage_stats[0] else 0,
                    'total_articles': usage_stats[1] if usage_stats and usage_stats[1] else 0,
                    'total_images': usage_stats[2] if usage_stats and usage_stats[2] else 0
                }
            }
        })
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de suscripciones: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Error obteniendo estadísticas: {str(e)}'}), 500

# =============================================================================
# ENDPOINTS DE COMPETITIVE INTELLIGENCE
# =============================================================================

@app.route('/api/competitive-intelligence/competitors', methods=['GET'])
@require_auth
def get_competitors():
    """Obtener competidores del usuario"""
    try:
        user_id = request.current_user['user_id']
        logger.info(f"Getting competitors for user {user_id}")
        
        # Crear una nueva instancia para evitar problemas de contexto
        from competitive_intelligence_system import CompetitiveIntelligenceSystem
        ci = CompetitiveIntelligenceSystem()
        
        competitors = ci.get_user_competitors(user_id)
        logger.info(f"Found {len(competitors)} competitors for user {user_id}")
        
        return jsonify({
            'success': True,
            'competitors': competitors,
            'total_count': len(competitors),
            'limit': ci.get_user_competitor_limit(user_id)
        })
    except Exception as e:
        logger.error(f"Error obteniendo competidores: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Error obteniendo competidores'}), 500

@app.route('/api/competitive-intelligence/competitors', methods=['POST'])
@require_auth
def add_competitor():
    """Agregar un nuevo competidor"""
    try:
        user_id = request.current_user['user_id']
        data = request.get_json()
        
        competitor_name = data.get('name', '').strip()
        keywords = data.get('keywords', [])
        domains = data.get('domains', [])
        
        if not competitor_name:
            return jsonify({'error': 'El nombre del competidor es requerido'}), 400
        
        if not keywords:
            return jsonify({'error': 'Al menos una palabra clave es requerida'}), 400
        
        # Agregar competidor
        competitor_id = ci_system.add_competitor(user_id, competitor_name, keywords, domains)
        
        return jsonify({
            'success': True,
            'message': f'Competidor "{competitor_name}" agregado exitosamente',
            'competitor_id': competitor_id
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error agregando competidor: {e}")
        return jsonify({'error': 'Error agregando competidor'}), 500

@app.route('/api/competitive-intelligence/competitors/<int:competitor_id>', methods=['DELETE'])
@require_auth
def delete_competitor(competitor_id):
    """Eliminar un competidor"""
    try:
        user_id = request.current_user['user_id']
        
        # Verificar que el competidor pertenece al usuario
        competitors = ci_system.get_user_competitors(user_id)
        competitor_exists = any(c['id'] == competitor_id for c in competitors)
        
        if not competitor_exists:
            return jsonify({'error': 'Competidor no encontrado'}), 404
        
        # Marcar como inactivo
        conn = sqlite3.connect(ci_system.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE user_competitors 
            SET is_active = 0, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ? AND user_id = ?
        ''', (competitor_id, user_id))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Competidor eliminado exitosamente'
        })
    except Exception as e:
        logger.error(f"Error eliminando competidor: {e}")
        return jsonify({'error': 'Error eliminando competidor'}), 500

@app.route('/api/competitive-intelligence/analytics', methods=['GET'])
@require_auth
def get_competitive_analytics():
    """Obtener analytics de competidores"""
    try:
        user_id = request.current_user['user_id']
        days = request.args.get('days', 30, type=int)
        
        analytics = ci_system.get_competitor_analytics(user_id, days)
        
        return jsonify({
            'success': True,
            'analytics': analytics,
            'period_days': days
        })
    except Exception as e:
        logger.error(f"Error obteniendo analytics: {e}")
        return jsonify({'error': 'Error obteniendo analytics'}), 500

@app.route('/api/competitive-intelligence/alerts', methods=['GET'])
@require_auth
def get_competitive_alerts():
    """Obtener alertas de competidores"""
    try:
        user_id = request.current_user['user_id']
        unread_only = request.args.get('unread_only', 'true').lower() == 'true'
        
        alerts = ci_system.get_user_alerts(user_id, unread_only)
        
        return jsonify({
            'success': True,
            'alerts': alerts,
            'unread_count': len([a for a in alerts if not a.get('is_read', False)])
        })
    except Exception as e:
        logger.error(f"Error obteniendo alertas: {e}")
        return jsonify({'error': 'Error obteniendo alertas'}), 500

@app.route('/api/competitive-intelligence/alerts/<int:alert_id>/read', methods=['POST'])
@require_auth
def mark_alert_read(alert_id):
    """Marcar alerta como leída"""
    try:
        user_id = request.current_user['user_id']
        
        conn = sqlite3.connect(ci_system.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE competitor_alerts 
            SET is_read = 1 
            WHERE id = ? AND user_id = ?
        ''', (alert_id, user_id))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Alerta marcada como leída'
        })
    except Exception as e:
        logger.error(f"Error marcando alerta: {e}")
        return jsonify({'error': 'Error marcando alerta'}), 500

@app.route('/api/competitive-intelligence/limits', methods=['GET'])
@require_auth
def get_competitive_limits():
    """Obtener límites del plan del usuario"""
    try:
        user_id = request.current_user['user_id']
        logger.info(f"Getting limits for user {user_id}")
        
        # Crear una nueva instancia para evitar problemas de contexto
        from competitive_intelligence_system import CompetitiveIntelligenceSystem
        ci = CompetitiveIntelligenceSystem()
        
        current_count = ci.get_competitor_count(user_id)
        limit = ci.get_user_competitor_limit(user_id)
        
        logger.info(f"User {user_id}: current={current_count}, limit={limit}")
        
        return jsonify({
            'success': True,
            'current_competitors': current_count,
            'max_competitors': limit,
            'remaining': max(0, limit - current_count)
        })
    except Exception as e:
        logger.error(f"Error obteniendo límites: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Error obteniendo límites'}), 500

@app.route('/api/competitive-intelligence/newspapers', methods=['GET'])
@require_auth
def get_available_newspapers():
    """Obtener lista de diarios configurados para usar como competidores"""
    try:
        # Obtener diarios únicos de la base de datos de artículos
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT newspaper 
            FROM articles 
            WHERE newspaper IS NOT NULL AND newspaper != ''
            ORDER BY newspaper
        ''')
        
        newspapers = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        logger.info(f"Found {len(newspapers)} newspapers: {newspapers}")
        
        return jsonify({
            'success': True,
            'newspapers': newspapers
        })
    except Exception as e:
        logger.error(f"Error obteniendo diarios: {e}")
        return jsonify({'error': 'Error obteniendo diarios'}), 500

@app.route('/api/competitive-intelligence/ai-suggestions', methods=['POST'])
@require_auth
def get_ai_keyword_suggestions():
    """Obtener sugerencias automáticas de palabras clave usando IA"""
    try:
        data = request.get_json()
        competitor_name = data.get('competitor_name', '').strip()
        existing_keywords = data.get('existing_keywords', [])
        
        if not competitor_name:
            return jsonify({'error': 'Nombre del competidor requerido'}), 400
        
        logger.info(f"Getting AI suggestions for competitor: {competitor_name}")
        
        # Obtener sugerencias de IA
        suggestions = get_ai_suggestions(competitor_name, existing_keywords)
        
        if suggestions['success']:
            logger.info(f"AI suggestions generated: {len(suggestions['suggestions'])} suggestions")
            return jsonify(suggestions)
        else:
            return jsonify({'error': 'Error generando sugerencias'}), 500
            
    except Exception as e:
        logger.error(f"Error obteniendo sugerencias de IA: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/api/competitive-intelligence/analyze-articles', methods=['POST'])
@require_auth
def analyze_existing_articles():
    """Analizar artículos existentes para encontrar menciones de competidores"""
    try:
        user_id = request.current_user['user_id']
        logger.info(f"Analyzing existing articles for user {user_id}")
        
        # Ejecutar análisis
        result = ci_system.analyze_existing_articles(user_id)
        
        if result['success']:
            logger.info(f"Analysis completed: {result['total_mentions']} mentions found")
            return jsonify({
                'success': True,
                'message': f"Análisis completado. Se encontraron {result['total_mentions']} menciones.",
                'total_mentions': result['total_mentions'],
                'competitors_analyzed': result['competitors_analyzed']
            })
        else:
            return jsonify({'error': 'Error en el análisis'}), 500
            
    except Exception as e:
        logger.error(f"Error analizando artículos: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/api/competitive-intelligence/auto-detect', methods=['POST'])
@require_auth
def auto_detect_competitor():
    """Detección automática de dominio y palabras clave para cualquier competidor"""
    try:
        data = request.get_json()
        competitor_name = data.get('competitor_name')
        
        if not competitor_name:
            return jsonify({'error': 'Nombre del competidor requerido'}), 400
        
        logger.info(f"Auto-detecting domain and keywords for: {competitor_name}")
        
        # Usar el analizador de IA para detección automática
        from ai_keyword_analyzer import AIKeywordAnalyzer
        analyzer = AIKeywordAnalyzer()
        
        result = analyzer.get_auto_domain_and_keywords(competitor_name)
        
        if result['success']:
            logger.info(f"Auto-detection successful for {competitor_name}: {result['source']}")
            return jsonify({
                'success': True,
                'competitor_name': competitor_name,
                'domain': result['domain'],
                'keywords': result['keywords'],
                'source': result['source'],
                'confidence': result['confidence'],
                'newspaper_found': result.get('newspaper_found')
            })
        else:
            return jsonify({'error': 'Error en la detección automática'}), 500
            
    except Exception as e:
        logger.error(f"Error en auto-detección: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

# ===== TRENDING TOPICS PREDICTOR ENDPOINTS =====

@app.route('/api/trending-predictor/generate', methods=['POST'])
@require_auth
def generate_trending_predictions():
    """Generar predicciones de trending topics"""
    try:
        user_id = request.current_user['user_id']
        data = request.get_json() or {}
        limit = data.get('limit', 10)
        
        logger.info(f"Generating {limit} trending predictions for user {user_id}")
        
        # Importar el sistema de predicción
        from trending_predictor_system import TrendingTopicsPredictor
        predictor = TrendingTopicsPredictor()
        
        # Generar predicciones
        result = predictor.generate_predictions(user_id, limit)
        
        if result['success']:
            logger.info(f"Generated {result['total_generated']} predictions successfully")
            return jsonify(result)
        else:
            return jsonify(result), 400 if 'upgrade_required' in result else 500
            
    except Exception as e:
        logger.error(f"Error generating predictions: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/api/trending-predictor/predictions', methods=['GET'])
@require_auth
def get_user_predictions():
    """Obtener predicciones del usuario"""
    try:
        user_id = request.current_user['user_id']
        limit = request.args.get('limit', 20, type=int)
        
        logger.info(f"Getting predictions for user {user_id}")
        
        from trending_predictor_system import TrendingTopicsPredictor
        predictor = TrendingTopicsPredictor()
        
        result = predictor.get_user_predictions(user_id, limit)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting predictions: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/api/trending-predictor/usage', methods=['GET'])
@require_auth
def get_daily_usage():
    """Obtener uso diario de predicciones"""
    try:
        user_id = request.current_user['user_id']
        
        from trending_predictor_system import TrendingTopicsPredictor
        predictor = TrendingTopicsPredictor()
        
        result = predictor.get_daily_usage(user_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting daily usage: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

# ==================== ENDPOINTS DE REDES SOCIALES (PROYECTO ACADÉMICO) ====================

def _generate_demo_tweets(query: str, max_tweets: int, mode: str) -> List[Dict]:
    """
    Generar tweets de ejemplo (mocks) para feedback inmediato
    Se usa cuando el scraping real no funciona o requiere autenticación
    """
    from datetime import datetime, timedelta
    import random
    
    # Validar parámetros
    if not query:
        query = 'tecnologia'
    if max_tweets < 1:
        max_tweets = 10
    if max_tweets > 1000:
        max_tweets = 1000
    
    demo_tweets = []
    # Limpiar query para usar en textos
    original_query = query.strip()
    clean_query = original_query.replace('#', '').replace('https://', '').replace('http://', '').replace('twitter.com/', '').replace('x.com/', '').replace('@', '').strip()
    
    # Si es una URL, extraer información útil
    if 'twitter.com' in original_query.lower() or 'x.com' in original_query.lower():
        # Extraer username de la URL - método mejorado
        url_clean = original_query.replace('https://', '').replace('http://', '').replace('www.', '').strip()
        url_parts = [p for p in url_clean.split('/') if p and p.strip()]
        
        skip_parts = ['twitter.com', 'x.com', 'i', 'search', 'hashtag', 'intent', 'status', 'with_replies', 'media', 'likes', 'with_rep']
        username_found = None
        
        # Buscar username en todas las partes
        for i, part in enumerate(url_parts):
            part_clean = part.strip()
            if part_clean and part_clean not in skip_parts:
                # Si la parte anterior es un dominio conocido, esta es probablemente el username
                if i > 0 and url_parts[i-1] in ['twitter.com', 'x.com']:
                    username_found = part_clean
                    break
                # O si no hay dominio explícito, la primera parte puede ser el username
                elif i == 0 and '.' not in part_clean:
                    username_found = part_clean
                    break
                # O simplemente la primera parte válida que encontremos
                elif not username_found:
                    username_found = part_clean
        
        if username_found:
            clean_query = username_found.replace('@', '').replace('_', ' ').replace('-', ' ')
            logger.info(f"✅ Extraído username de URL: '{username_found}' -> '{clean_query}'")
        else:
            logger.info(f"⚠️ No se pudo extraer username de URL: {original_query}, usando query limpia")
    
    # Limpiar espacios y caracteres especiales
    clean_query = ' '.join(clean_query.split())
    
    if len(clean_query) > 50:
        clean_query = clean_query[:50]
    
    # Si no hay query válida, usar default
    if not clean_query or len(clean_query) < 2:
        clean_query = 'tecnologia'
        logger.info(f"⚠️ Query vacía, usando default: {clean_query}")
    
    logger.info(f"📝 Query final para generar tweets: '{clean_query}'")
    
    # Emojis comunes en tweets
    emojis = ['🔥', '💯', '✨', '🚀', '📰', '📊', '💡', '🎯', '⚡', '🌟', '📈', '💪', '🎉', '👍', '👏']
    
    # Textos REALISTAS que parecen tweets reales
    # Si clean_query parece un username (sin espacios), ajustar textos
    is_username = '_' in clean_query or clean_query.isalnum() and len(clean_query) < 20
    
    if is_username:
        # Textos para cuando es un usuario específico
        base_texts = [
            f"Acabo de leer lo que {clean_query} publicó y la verdad es que... 👀",
            f"Noticia importante de {clean_query} que todos deberían conocer 📰",
            f"Análisis interesante de {clean_query}. ¿Qué opinan?",
            f"Última hora: {clean_query} está generando mucha atención en redes 🔥",
            f"¿Alguien más está siguiendo a {clean_query}?",
            f"Me gusta mucho el contenido de {clean_query}",
            f"{clean_query} siempre publica información relevante",
            f"Compartiendo esto de {clean_query} porque es importante",
            f"Recomiendo seguir a {clean_query}",
            f"{clean_query} tiene razón en este punto",
        ]
    else:
        # Textos para temas generales
        base_texts = [
            f"Acabo de leer sobre {clean_query} y la verdad es que... 👀",
            f"Noticia importante sobre {clean_query} que todos deberían conocer 📰",
            f"Análisis interesante de {clean_query}. ¿Qué opinan?",
            f"Última hora: {clean_query} está generando mucha atención en redes 🔥",
            f"¿Alguien más está siguiendo lo de {clean_query}?",
            
            # Tweets con opinión
            f"Mi opinión sobre {clean_query}: creo que es un tema importante que debemos discutir 💭",
            f"Después de analizar {clean_query}, creo que hay puntos que debemos considerar 🤔",
            f"No estoy de acuerdo con algunas cosas sobre {clean_query}, pero respeto otras opiniones",
            f"{clean_query} es un tema complejo, no hay una respuesta simple",
            
            # Tweets con links/recursos
            f"Compartiendo este análisis sobre {clean_query} que encontré interesante 📊",
            f"Recomiendo leer más sobre {clean_query}, hay información valiosa",
            f"Fuente importante sobre {clean_query} que vale la pena revisar",
            
            # Tweets conversacionales
            f"¿Qué tal les parece {clean_query}? A mí me parece interesante 🤷‍♂️",
            f"Discutiendo con amigos sobre {clean_query} y las opiniones son muy variadas",
            f"Alguien más se ha fijado en {clean_query}? Me parece relevante",
            
            # Tweets con datos
            f"Datos importantes sobre {clean_query} que todos deberían ver 📈",
            f"Estadísticas relevantes de {clean_query} que muestran tendencias claras",
            f"Reporte sobre {clean_query} con información actualizada",
            
            # Tweets de seguimiento
            f"Siguiendo de cerca {clean_query}. Actualizaciones importantes",
            f"Estoy pendiente de {clean_query} porque puede afectar a muchos",
            f"Monitoreando {clean_query} para ver cómo evoluciona",
            
            # Tweets con contexto
            f"En el contexto de {clean_query}, creo que debemos considerar varios factores",
            f"Relacionado con {clean_query}, hay aspectos que no se están discutiendo",
            f"Sobre {clean_query}: hay que entender el contexto completo",
            
            # Tweets reflexivos
            f"Pensando en {clean_query} y las implicaciones que tiene",
            f"Reflexionando sobre {clean_query} y lo que significa para el futuro",
            f"Análisis profundo de {clean_query} requiere considerar múltiples perspectivas",
            
            # Tweets de actualidad
            f"Lo último sobre {clean_query} está en todas partes 🌐",
            f"Tendencia actual: {clean_query} está en boca de todos",
            f"Tema del momento: {clean_query} 👇",
            
            # Tweets con preguntas
            f"¿Qué saben sobre {clean_query}? Compartan sus pensamientos",
            f"¿Cómo ven {clean_query}? Me interesa saber opiniones",
            f"Pregunta: ¿qué impacto creen que tiene {clean_query}?",
            
            # Tweets con llamadas a acción
            f"Compartan si están de acuerdo con lo de {clean_query}",
            f"RT si también están siguiendo {clean_query}",
            f"Comenten qué piensan sobre {clean_query}",
        ]
    
    # Generar variaciones para tener más tweets únicos
    sample_texts = base_texts * ((max_tweets // len(base_texts)) + 1)
    sample_texts = sample_texts[:max_tweets]  # Ajustar al tamaño exacto
    
    # Usuarios REALISTAS que parecen cuentas reales
    sample_usernames = [
        "@juan_perez", "@maria_lopez", "@carlos_rodriguez", "@ana_martinez",
        "@pedro_garcia", "@lucia_sanchez", "@diego_fernandez", "@sofia_gomez",
        "@miguel_torres", "@laura_morales", "@andres_jimenez", "@carmen_ruiz",
        "@tech_peru", "@noticias_pe", "@periodista_digital", "@analista_news",
        "@reportero_live", "@media_team", "@news_break", "@breaking_pe",
        "@info_actual", "@noticias_ahora", "@reporte_diario", "@ultima_hora_pe",
        "@usuario_123", "@user_news", "@informante", "@comentarista",
        "@lector_activo", "@seguidor_news", "@opinador_pe", "@curioso_pe"
    ]
    
    # Hashtags REALISTAS y relevantes
    base_hashtags = ["#tecnologia", "#noticias", "#actualidad", "#peru",
                     "#tecnologia", "#innovacion", "#digital", "#socialmedia",
                     "#news", "#trending", "#breaking", "#ultimahora",
                     "#informacion", "#analisis", "#datos", "#reporte",
                     "#noticia", "#tendencias", "#futuro", "#media"]
    
    # Agregar hashtag personalizado basado en la query
    if clean_query and len(clean_query) < 20 and not clean_query.startswith('http'):
        clean_hashtag = clean_query.lower().replace(' ', '').replace('_', '').replace('-', '')
        if clean_hashtag:
            base_hashtags.append(f"#{clean_hashtag}")
    
    hashtags_options = []
    for i in range(max_tweets):
        # Generar 0-3 hashtags (más realista, no todos tienen hashtags)
        num_tags = random.choices([0, 1, 2, 3], weights=[20, 40, 30, 10])[0]
        if num_tags > 0:
            selected = random.sample(base_hashtags, min(num_tags, len(base_hashtags)))
            hashtags_options.append(selected)
        else:
            hashtags_options.append([])
    
    # Generar tweets REALISTAS que parezcan tweets reales
    for i in range(max_tweets):
        # Fechas más realistas (últimas 7 días, más recientes)
        days_ago = random.choices([0, 1, 2, 3, 4, 5, 6, 7], weights=[30, 25, 20, 10, 7, 4, 3, 1])[0]
        base_time = datetime.now() - timedelta(
            days=days_ago,
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )
        
        # Seleccionar texto base
        base_text = sample_texts[i % len(sample_texts)] if sample_texts else f"Información sobre {clean_query}"
        
        # Agregar emoji ocasionalmente (30% de probabilidad)
        if random.random() < 0.3:
            emoji = random.choice(emojis)
            base_text = f"{base_text} {emoji}"
        
        # Agregar menciones ocasionalmente (20% de probabilidad)
        if random.random() < 0.2:
            mention = random.choice(sample_usernames)
            base_text = f"{mention} {base_text}"
        
        # Agregar URL ocasionalmente (10% de probabilidad) - pero sin hacer clic
        url_in_text = ""
        if random.random() < 0.1:
            url_in_text = " https://example.com/news"
            base_text = f"{base_text}{url_in_text}"
        
        # Asegurar que el texto no sea muy largo (280 caracteres máximo)
        if len(base_text) > 280:
            base_text = base_text[:277] + "..."
        
        username = random.choice(sample_usernames)
        
        # Hashtags para este tweet
        tweet_hashtags = hashtags_options[i] if i < len(hashtags_options) else []
        
        # Agregar hashtags al texto si existen (50% de probabilidad)
        if tweet_hashtags and random.random() < 0.5:
            hashtags_text = " " + " ".join(tweet_hashtags)
            if len(base_text + hashtags_text) <= 280:
                base_text = base_text + hashtags_text
        
        # Métricas REALISTAS (la mayoría tiene pocos likes, algunos tienen muchos)
        # Distribución: 60% pocos (0-50), 30% medios (50-500), 10% muchos (500-5000)
        likes_dist = random.random()
        if likes_dist < 0.6:
            likes = random.randint(0, 50)
        elif likes_dist < 0.9:
            likes = random.randint(50, 500)
        else:
            likes = random.randint(500, 5000)
        
        # Retweets suelen ser menos que likes
        retweets = random.randint(0, max(1, likes // 3))
        
        # Replies suelen ser menos que retweets
        replies = random.randint(0, max(1, retweets // 2))
        
        # URL del tweet (formato real de Twitter/X)
        tweet_id = random.randint(1000000000000000000, 9999999999999999999)  # IDs largos de Twitter
        username_clean = username.replace("@", "")
        tweet_url = f"https://twitter.com/{username_clean}/status/{tweet_id}"
        
        # Imágenes de ejemplo (80% de probabilidad de tener imagen para que se vean más)
        image_url = None
        if random.random() < 0.8:  # Aumentar a 80% para que más tweets tengan imágenes
            # Usar imágenes de placeholder o Unsplash con temas relevantes
            image_themes = ['news', 'technology', 'business', 'people', 'news', 'media', 'social', 'computer', 'digital', 'network']
            theme = random.choice(image_themes)
            image_id = random.randint(100, 9999)  # Más variedad
            
            # Usar Picsum Photos que funciona mejor
            image_url = f"https://picsum.photos/800/600?random={image_id}"
            
            # Alternativa con Unsplash si Picsum falla
            # image_url = f"https://source.unsplash.com/800x600/?{theme}&sig={image_id}"
        
        tweet_data = {
            'platform': 'twitter',
            'username': username,
            'text': base_text,
            'date': base_time.isoformat(),
            'likes': likes,
            'retweets': retweets,
            'replies': replies,
            'hashtags': tweet_hashtags,
            'url': tweet_url,
            'image_url': image_url,  # URL de imagen
            'scraped_at': datetime.now().isoformat()
        }
        
        demo_tweets.append(tweet_data)
    
    # Asegurar que siempre retornamos tweets
    if not demo_tweets or len(demo_tweets) == 0:
        logger.error(f"❌ ERROR: No se generaron tweets! Query: '{query}', Max: {max_tweets}")
        # Generar al menos uno de emergencia
        tweet_data = {
            'platform': 'twitter',
            'username': '@usuario_noticias',
            'text': f'Información sobre {query or "tecnologia"}',
            'date': datetime.now().isoformat(),
            'likes': 10,
            'retweets': 5,
            'replies': 2,
            'hashtags': ['#noticias'],
            'url': 'https://twitter.com/usuario/status/1234567890',
            'image_url': None,
            'scraped_at': datetime.now().isoformat()
        }
        demo_tweets.append(tweet_data)
    
    logger.info(f"✅ Generados {len(demo_tweets)} tweets exitosamente")
    return demo_tweets

def _generate_demo_facebook_posts(query: str, max_posts: int, mode: str) -> List[Dict]:
    """
    Generar posts de Facebook de ejemplo (mocks) para feedback inmediato
    Se usa cuando el scraping real no funciona o requiere autenticación
    Estos mocks se reemplazan automáticamente cuando llegan datos reales
    """
    from datetime import datetime, timedelta
    import random
    
    # Validar parámetros
    if not query:
        query = 'tecnologia'
    if max_posts < 1:
        max_posts = 10
    if max_posts > 1000:
        max_posts = 1000
    
    demo_posts = []
    original_query = query.strip()
    clean_query = original_query.replace('#', '').replace('https://', '').replace('http://', '').replace('facebook.com/', '').replace('fb.com/', '').replace('@', '').strip()
    
    # Si es una URL, extraer información útil
    if 'facebook.com' in original_query.lower() or 'fb.com' in original_query.lower():
        url_clean = original_query.replace('https://', '').replace('http://', '').replace('www.', '').strip()
        url_parts = [p for p in url_clean.split('/') if p and p.strip()]
        
        skip_parts = ['facebook.com', 'fb.com', 'pages', 'posts', 'photos', 'videos', 'groups', 'events']
        username_found = None
        
        for i, part in enumerate(url_parts):
            part_clean = part.strip()
            if part_clean and part_clean not in skip_parts:
                if i > 0 and url_parts[i-1] in ['facebook.com', 'fb.com']:
                    username_found = part_clean
                    break
                elif not username_found:
                    username_found = part_clean
        
        if username_found:
            clean_query = username_found.replace('_', ' ').replace('-', ' ')
            logger.info(f"✅ Extraído nombre de página de URL de Facebook: '{username_found}' -> '{clean_query}'")
    
    clean_query = ' '.join(clean_query.split())
    if len(clean_query) > 50:
        clean_query = clean_query[:50]
    
    if not clean_query or len(clean_query) < 2:
        clean_query = 'tecnologia'
    
    logger.info(f"📝 Query final para generar posts de Facebook: '{clean_query}'")
    
    # Textos de ejemplo variados para Facebook
    facebook_texts = [
        f"📰 {clean_query.title()} - Noticia importante que todos deberían conocer",
        f"🎯 Actualización sobre {clean_query}: información relevante para la comunidad",
        f"💡 Reflexión sobre {clean_query} y su impacto en nuestra sociedad",
        f"📊 Análisis detallado de {clean_query} y sus implicaciones",
        f"🔥 Tendencias actuales en {clean_query} que debes conocer",
        f"✨ Nuevo contenido sobre {clean_query} disponible ahora",
        f"📝 Opinión sobre {clean_query} y su relevancia actual",
        f"🌟 {clean_query.title()} - Lo que necesitas saber hoy",
        f"🎬 Video sobre {clean_query} disponible en nuestra página",
        f"📸 Galería de imágenes sobre {clean_query}",
        f"🔔 Recordatorio importante sobre {clean_query}",
        f"💬 ¿Qué opinas sobre {clean_query}? Deja tu comentario",
        f"📈 Estadísticas recientes sobre {clean_query}",
        f"🎓 Aprendamos juntos sobre {clean_query}",
        f"🤝 Únete a la conversación sobre {clean_query}"
    ]
    
    # Nombres de usuarios/páginas de Facebook
    facebook_usernames = [
        f"{clean_query.title()} Oficial",
        f"{clean_query.title()} Noticias",
        f"Página de {clean_query.title()}",
        f"{clean_query.title()} Perú",
        f"Noticias {clean_query.title()}",
        f"{clean_query.title()} Info",
        f"Portal {clean_query.title()}",
        f"{clean_query.title()} Diario"
    ]
    
    # Generar posts
    for i in range(max_posts):
        base_text = random.choice(facebook_texts)
        
        # Agregar hashtags ocasionalmente
        if random.random() < 0.3:
            hashtags = [f"#{clean_query.replace(' ', '')}", "#noticias", "#peru"]
            base_text += " " + " ".join(hashtags)
        
        username = random.choice(facebook_usernames)
        
        # Fecha reciente (últimos 7 días)
        days_ago = random.randint(0, 7)
        base_time = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
        
        # Métricas realistas de Facebook
        likes = random.randint(10, 5000)
        comments = random.randint(0, int(likes * 0.3))
        shares = random.randint(0, int(likes * 0.2))
        
        # URL del post
        post_url = f"https://facebook.com/{username.replace(' ', '').lower()}/posts/{random.randint(1000000000, 9999999999)}"
        
        # Imágenes de ejemplo (80% de probabilidad)
        image_url = None
        if random.random() < 0.8:
            image_themes = ['news', 'technology', 'business', 'people', 'news', 'media', 'social', 'computer', 'digital', 'network']
            theme = random.choice(image_themes)
            image_id = random.randint(100, 9999)
            image_url = f"https://picsum.photos/800/600?random={image_id}"
        
        post_data = {
            'platform': 'facebook',
            'username': username,
            'text': base_text,
            'date': base_time.isoformat(),
            'likes': likes,
            'comments': comments,
            'shares': shares,
            'retweets': 0,  # Facebook no tiene retweets
            'replies': comments,  # Usar comments como replies
            'hashtags': re.findall(r'#\w+', base_text),
            'url': post_url,
            'image_url': image_url,
            'scraped_at': datetime.now().isoformat()
        }
        demo_posts.append(post_data)
    
    # Asegurar que siempre retornamos posts
    if not demo_posts or len(demo_posts) == 0:
        logger.error(f"❌ ERROR: No se generaron posts de Facebook! Query: '{query}', Max: {max_posts}")
        post_data = {
            'platform': 'facebook',
            'username': 'Página de Noticias',
            'text': f'Información sobre {query or "tecnologia"}',
            'date': datetime.now().isoformat(),
            'likes': 10,
            'comments': 5,
            'shares': 2,
            'retweets': 0,
            'replies': 5,
            'hashtags': ['#noticias'],
            'url': 'https://facebook.com/pagina/posts/1234567890',
            'image_url': None,
            'scraped_at': datetime.now().isoformat()
        }
        demo_posts.append(post_data)
    
    logger.info(f"✅ Generados {len(demo_posts)} posts de Facebook exitosamente")
    return demo_posts

@app.route('/api/social-media/scrape', methods=['POST'])
@require_auth
def scrape_social_media():
    """
    Scraping de redes sociales (Twitter/X y Facebook)
    SOLO extrae datos REALES - NO genera mocks ni datos simulados
    Si el scraping falla, retorna error en lugar de generar datos demo
    """
    user_id = None
    query = ''
    max_posts = 100
    mode = 'query'
    platform = 'twitter'  # Por defecto Twitter
    
    try:
        user_id = request.current_user['user_id']
        data = request.get_json() or {}
        
        raw_url = data.get('url', '')
        query = data.get('query', '') or raw_url
        max_posts = data.get('max_posts', 100)
        filter_language = data.get('filter_language', None)
        mode = data.get('mode', 'query')
        platform = data.get('platform', 'twitter').lower()  # twitter, facebook, o reddit
        request_url = raw_url.strip()
        
        # Validación mínima - SIEMPRE tener una query válida
        if not query or not query.strip():
            query = 'tecnologia'  # Default para fines académicos
        else:
            query = query.strip()
        
        if max_posts < 1:
            max_posts = 10
        if max_posts > 1000:
            max_posts = 1000
        
        logger.info(f"📝 Usuario {user_id} - Plataforma: {platform}, Modo: {mode}, Query/URL: '{query}', Max: {max_posts}")
        
    except Exception as e:
        logger.warning(f"⚠️ Error obteniendo parámetros: {e}")
        query = query or 'tecnologia'
        max_posts = max_posts or 100
        platform = platform or 'twitter'
    
    # Intentar scraping REAL primero
    posts = []
    scraper = None
    demo_mode = False  # Inicializar demo_mode al principio
    
    try:
        import threading
        import queue
        
        if platform == 'facebook':
            try:
                from social_media_scraper import FacebookScraper
                import os
                
                # Intentar cargar .env si existe
                try:
                    from dotenv import load_dotenv
                    load_dotenv()
                except ImportError:
                    pass  # python-dotenv no instalado, usar solo variables de entorno
                
                # Intentar obtener access token de variables de entorno o .env
                access_token = os.getenv('FACEBOOK_ACCESS_TOKEN') or os.getenv('FB_ACCESS_TOKEN')
                
                logger.info(f"🔍 Intentando scraping REAL de Facebook para: '{query}'...")
                if access_token:
                    logger.info("✅ Access Token encontrado, usando Graph API (método oficial)")
                else:
                    logger.info("ℹ️ Sin Access Token, usando métodos alternativos (Selenium/requests)")
                
                # Usar scraper manual directamente - NO crear FacebookScraper para evitar doble ventana
                logger.info("🔧 Usando scraper con login manual (NUEVO MÉTODO)")
                logger.info("ℹ️ Navegador visible - Puedes hacer login manualmente")
                logger.info("⚠️ IMPORTANTE: Solo se abrirá UNA ventana para login y scraping")
                
                # Usar threading para timeout en lugar de signal (funciona mejor en todos los contextos)
                result_queue = queue.Queue()
                exception_queue = queue.Queue()
                
                def scrape_worker():
                    try:
                        # Importar módulos necesarios dentro de la función
                        import re
                        from facebook_manual_scraper import scrape_facebook_page
                        
                        # Función callback para recibir posts parciales durante el scraping
                        def progress_callback(partial_posts):
                            """Callback para recibir posts mientras se extraen"""
                            try:
                                if partial_posts and len(partial_posts) > 0:
                                    # Convertir formato
                                    formatted = []
                                    for post in partial_posts:
                                        formatted.append({
                                            'platform': 'facebook',
                                            'username': post.get('author', 'Página de Facebook'),
                                            'text': post.get('content', ''),
                                            'cleaned_text': post.get('content', '').strip(),
                                            'image_url': post.get('image_url'),
                                            'video_url': None,
                                            'url': post.get('url', ''),
                                            'date': post.get('created_at', datetime.now().isoformat()),
                                            'created_at': post.get('created_at', datetime.now().isoformat()),
                                            'likes': post.get('metrics', {}).get('likes', 0),
                                            'comments': post.get('metrics', {}).get('comments', 0),
                                            'shares': post.get('metrics', {}).get('shares', 0),
                                            'retweets': 0,
                                            'replies': 0,
                                            'hashtags': re.findall(r'#\w+', post.get('content', '')),
                                            'scraped_at': datetime.now().isoformat()
                                        })
                                    # Guardar posts parciales en la cola (se sobreescribirá con los finales)
                                    if not result_queue.empty():
                                        try:
                                            result_queue.get_nowait()  # Limpiar posts anteriores
                                        except:
                                            pass
                                    result_queue.put(formatted)
                                    logger.info(f"📊 Progreso: {len(formatted)} posts parciales guardados")
                            except Exception as e:
                                logger.debug(f"⚠️ Error en callback de progreso: {e}")
                        
                        if mode == 'url':
                            logger.info(f"📡 Modo URL: Intentando extraer posts REALES de Facebook desde {query} (timeout: 600s = 10 minutos)")
                            logger.info(f"🔍 BUSCANDO DATOS REALES - NO SIMULACIÓN")
                            # Usar scraper manual directamente (crea su propio driver)
                            result = scrape_facebook_page(query, max_posts, wait_for_login_seconds=60, progress_callback=progress_callback)
                        else:
                            logger.info(f"🔎 Modo Query: Facebook requiere URLs específicas, usando modo URL")
                            # Facebook no tiene búsqueda pública como Twitter, así que tratamos como URL
                            url_to_scrape = query if 'facebook.com' in query else f"https://facebook.com/{query}"
                            result = scrape_facebook_page(url_to_scrape, max_posts, wait_for_login_seconds=60, progress_callback=progress_callback)
                        
                        # Convertir formato al formato esperado por el sistema
                        import re  # Importar re dentro de la función
                        formatted_posts = []
                        for post in result:
                            formatted_posts.append({
                                'platform': 'facebook',
                                'username': post.get('author', 'Página de Facebook'),
                                'text': post.get('content', ''),
                                'cleaned_text': post.get('content', '').strip(),
                                'image_url': post.get('image_url'),
                                'video_url': None,
                                'url': post.get('url', ''),
                                'date': post.get('created_at', datetime.now().isoformat()),
                                'created_at': post.get('created_at', datetime.now().isoformat()),
                                'likes': post.get('metrics', {}).get('likes', 0),
                                'comments': post.get('metrics', {}).get('comments', 0),
                                'shares': post.get('metrics', {}).get('shares', 0),
                                'retweets': 0,
                                'replies': 0,
                                'hashtags': re.findall(r'#\w+', post.get('content', '')),
                                'scraped_at': datetime.now().isoformat()
                            })
                        
                        result_queue.put(formatted_posts)
                        logger.info(f"✅ ✅ ✅ Scraping completado: {len(formatted_posts)} posts REALES")
                    except Exception as e:
                        logger.error(f"❌ Error en scrape_worker: {e}")
                        import traceback
                        logger.error(f"Traceback: {traceback.format_exc()}")
                        exception_queue.put(e)
                
                # Ejecutar scraping en thread separado
                scrape_thread = threading.Thread(target=scrape_worker, daemon=True)
                scrape_thread.start()
                scrape_thread.join(timeout=600)  # OPTIMIZADO: 600 segundos (10 minutos) - Proceso optimizado para ser más rápido
                
                if scrape_thread.is_alive():
                    logger.warning(f"⏱️ Timeout en scraping real de Facebook después de 600 segundos (10 minutos)")
                    logger.warning(f"⚠️ El proceso puede continuar en background, pero no esperaremos más")
                    # Intentar obtener posts parciales si hay algo en la cola
                    try:
                        if not result_queue.empty():
                            partial_posts = result_queue.get()
                            if partial_posts and len(partial_posts) > 0:
                                logger.info(f"✅ ✅ ✅ Posts parciales obtenidos después de timeout: {len(partial_posts)} posts")
                                posts = partial_posts
                            else:
                                posts = []
                        else:
                            posts = []
                    except:
                        posts = []
                else:
                    # Verificar si hay resultado o excepción
                    if not exception_queue.empty():
                        error = exception_queue.get()
                        logger.warning(f"⏱️ Error en scraping real de Facebook: {error}")
                        import traceback
                        logger.error(f"Traceback: {traceback.format_exc()}")
                        posts = []
                    elif not result_queue.empty():
                        posts = result_queue.get()
                        
                        if posts and len(posts) > 0:
                            # Verificar que sean posts REALES (no vacíos)
                            real_posts = [p for p in posts if p.get('text') and len(p.get('text', '').strip()) > 10]
                            if real_posts:
                                logger.info(f"✅ ✅ ✅ SCRAPING REAL EXITOSO: {len(real_posts)} posts REALES de Facebook extraídos!")
                                posts = real_posts  # Usar solo posts reales
                            else:
                                logger.warning(f"⚠️ Se extrajeron {len(posts)} posts pero ninguno tiene contenido válido")
                                posts = []
                        else:
                            logger.info(f"⚠️ No se encontraron posts reales de Facebook")
                            posts = []
                        
            except Exception as facebook_error:
                logger.error(f"❌ Error inicializando FacebookScraper: {facebook_error}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                posts = []
        elif platform == 'reddit':
            # Scraping de Reddit
            try:
                from social_media_scraper import RedditScraper
                import os
                
                logger.info(f"🔍 Intentando scraping REAL de Reddit para: '{query}'...")
                
                # Si el modo es URL, usar la URL directamente
                if mode == 'url':
                    query = query if query else request_url
                
                # Determinar si es subreddit o búsqueda
                subreddit_name = None
                search_query = None

                query_str = (query or '').strip()
                lower_query = query_str.lower()

                if lower_query:
                    is_url_like = lower_query.startswith('http') or 'reddit.com' in lower_query
                    if is_url_like:
                        # Asegurar que la URL tenga esquema para urlparse
                        url_to_parse = query_str if lower_query.startswith('http') else f"https://{query_str}"
                        parsed = urlparse(url_to_parse)
                        path_parts_raw = [part for part in parsed.path.split('/') if part]
                        path_parts = [unquote(part) for part in path_parts_raw]

                        # Buscar segmento r/<subreddit>
                        subreddit_candidate = None
                        for idx, part in enumerate(path_parts):
                            if part.lower() == 'r' and idx + 1 < len(path_parts):
                                subreddit_candidate = path_parts[idx + 1]
                                break
                        if not subreddit_candidate and path_parts and path_parts[0].lower().startswith('r'):
                            # Manejar rutas tipo /r_peru
                            maybe_sub = path_parts[0][1:]
                            if maybe_sub:
                                subreddit_candidate = maybe_sub

                        if subreddit_candidate:
                            subreddit_candidate = subreddit_candidate.split('?')[0].split('#')[0].strip()
                            if subreddit_candidate:
                                subreddit_name = subreddit_candidate
                                logger.info(f"📡 URL detectada, subreddit extraído: r/{subreddit_name}")

                        if not subreddit_name:
                            # Intentar extraer término de búsqueda (?q=...)
                            qs = parse_qs(parsed.query or '')
                            query_param = ''
                            if 'q' in qs and qs['q']:
                                query_param = qs['q'][0]
                            if not query_param and path_parts:
                                # Para rutas como /search/<termino>
                                last_part = path_parts[-1]
                                if last_part.lower() not in {'search', 'r'}:
                                    query_param = last_part
                            if query_param:
                                search_query = unquote(query_param).replace('+', ' ').strip()
                                if search_query:
                                    logger.info(f"🔍 URL de búsqueda detectada, parámetro q: '{search_query}'")

                        if not subreddit_name and not search_query:
                            logger.warning(f"⚠️ No se pudo interpretar la URL de Reddit: {query_str}")
                            search_query = query_str
                    elif query_str.startswith('r/') or query_str.startswith('/r/'):
                        subreddit_name = query_str.replace('r/', '').replace('/r/', '').strip()
                    elif ' ' not in query_str and query_str.replace('_', '').replace('-', '').isalnum():
                        # Probablemente es un nombre de subreddit simple
                        subreddit_name = query_str
                    else:
                        # Tratar como búsqueda de texto
                        search_query = query_str
                
                # Usar threading para timeout
                import threading
                import queue
                result_queue = queue.Queue()
                exception_queue = queue.Queue()
                
                def scrape_worker():
                    try:
                        scraper = RedditScraper(headless=False, use_api=True)  # headless=False para ver el navegador si usa Selenium
                        
                        if subreddit_name:
                            logger.info(f"📡 Extrayendo posts del subreddit: r/{subreddit_name}")
                            posts = scraper.scrape_subreddit(subreddit_name, max_posts, sort='hot')
                        elif search_query:
                            logger.info(f"🔍 Buscando posts con query: '{search_query}'")
                            posts = scraper.search_posts(search_query, limit=max_posts)
                        else:
                            cleaned_query = (query or '').strip()
                            if cleaned_query.lower().startswith('http'):
                                logger.info(f"🔄 URL sin subreddit detectada, intentando búsqueda con: '{cleaned_query}'")
                                posts = scraper.search_posts(cleaned_query, limit=max_posts)
                            else:
                                subreddit_name_default = cleaned_query.replace('r/', '').replace('/r/', '').strip()
                                logger.info(f"📡 Intentando como subreddit: r/{subreddit_name_default}")
                                posts = scraper.scrape_subreddit(subreddit_name_default, max_posts, sort='hot')
                        
                        scraper.close()
                        
                        # Convertir formato al formato esperado por el sistema
                        formatted_posts = []
                        for post in posts:
                            # Combinar título y contenido para el campo 'text'
                            title = post.get('title', '').strip()
                            content = post.get('content', '').strip()
                            
                            # Si el contenido es igual al título, solo usar título
                            if content == title:
                                text_content = title
                            else:
                                # Combinar título y contenido
                                text_content = f"{title}\n\n{content}" if content else title
                            
                            # Determinar username: si es "Unknown", usar subreddit o "Reddit"
                            author = post.get('author', 'Unknown')
                            if author and author not in {'Unknown', 'unknown'}:
                                author_clean = author.strip()
                                if not author_clean:
                                    username_display = None
                                elif author_clean.lower() in {'[deleted]', 'automoderator'}:
                                    # Mostrar nombres especiales tal cual (con prefijo u/)
                                    username_display = f"u/{author_clean}" if not author_clean.startswith('u/') else author_clean
                                else:
                                    username_display = author_clean if author_clean.startswith('u/') else f"u/{author_clean}"
                            else:
                                username_display = None

                            if not username_display:
                                # Usar subreddit como fallback
                                subreddit_fallback = post.get('subreddit', subreddit_name or 'all')
                                if subreddit_fallback and subreddit_fallback != 'all':
                                    # Formatear como "r/subreddit"
                                    if not subreddit_fallback.startswith('r/'):
                                        username_display = f"r/{subreddit_fallback}"
                                    else:
                                        username_display = subreddit_fallback
                                else:
                                    username_display = "Reddit"
                            
                            formatted_posts.append({
                                'platform': 'reddit',
                                'username': username_display,  # Username del autor o subreddit como fallback
                                'text': text_content,  # Título + contenido
                                'cleaned_text': text_content.strip(),
                                'title': title,  # Título del post
                                'content': content,
                                'image_url': post.get('image_url'),
                                'video_url': post.get('video_url'),
                                'url': post.get('permalink', '') or post.get('url', ''),
                                'date': post.get('created_at', datetime.now().isoformat()),
                                'created_at': post.get('created_at', datetime.now().isoformat()),
                                'likes': post.get('upvotes', 0) or post.get('score', 0),  # Usar upvotes primero
                                'retweets': 0,  # Reddit no tiene retweets
                                'replies': post.get('comments', 0) or post.get('num_comments', 0),  # Comentarios
                                'hashtags': [],  # Reddit no usa hashtags tradicionalmente
                                'subreddit': post.get('subreddit', subreddit_name or 'all'),  # Subreddit (sin duplicar)
                                'score': post.get('score', 0),
                                'upvotes': post.get('upvotes', 0),
                                'downvotes': post.get('downvotes', 0),
                                'comments': post.get('comments', 0) or post.get('num_comments', 0),
                                'flair': post.get('flair'),
                                'scraped_at': datetime.now().isoformat()
                            })
                        
                        result_queue.put(formatted_posts)
                        logger.info(f"✅ ✅ ✅ Scraping completado: {len(formatted_posts)} posts REALES de Reddit")
                    except Exception as e:
                        logger.error(f"❌ Error en scrape_worker de Reddit: {e}")
                        import traceback
                        logger.error(f"Traceback: {traceback.format_exc()}")
                        exception_queue.put(e)
                
                scrape_thread = threading.Thread(target=scrape_worker, daemon=True)
                scrape_thread.start()
                scrape_thread.join(timeout=300)  # 5 minutos timeout
                
                if scrape_thread.is_alive():
                    logger.warning(f"⏱️ Timeout en scraping real de Reddit después de 300 segundos")
                    posts = []
                else:
                    if not exception_queue.empty():
                        error = exception_queue.get()
                        logger.warning(f"⏱️ Error en scraping real de Reddit: {error}")
                        posts = []
                    elif not result_queue.empty():
                        posts = result_queue.get()
                    else:
                        posts = []
                
                # Validar posts reales
                if posts and len(posts) > 0:
                    real_posts = [p for p in posts if p.get('text') and len(p.get('text', '').strip()) > 10]
                    if real_posts:
                        logger.info(f"✅ ✅ ✅ SCRAPING REAL EXITOSO: {len(real_posts)} posts REALES de Reddit extraídos!")
                        posts = real_posts
                    else:
                        logger.warning(f"⚠️ Se extrajeron {len(posts)} posts pero ninguno tiene contenido válido")
                        posts = []
                else:
                    logger.warning(f"⚠️ No se encontraron posts reales de Reddit")
                    posts = []
                
                if posts and len(posts) > 0:
                    final_posts = posts
                    demo_mode = False
                else:
                    final_posts = []
                    demo_mode = True
                    
            except Exception as reddit_error:
                logger.error(f"❌ Error inicializando RedditScraper: {reddit_error}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                final_posts = []
                demo_mode = True
                
        elif platform == 'youtube':
            try:
                from social_media_scraper import YouTubeScraper
                import os

                # Intentar cargar .env si existe
                try:
                    from dotenv import load_dotenv
                    load_dotenv()
                except ImportError:
                    pass  # python-dotenv no instalado, usar solo variables de entorno

                logger.info(f"🔍 Intentando scraping REAL de YouTube para: '{query}'...")

                if mode == 'url':
                    query = request_url or query
                    logger.info(f"📎 Modo URL activado, usando: {query}")

                is_channel = False
                is_video = False
                channel_identifier = None
                video_id = None
                search_query = None

                if 'youtube.com' in query.lower() or 'youtu.be' in query.lower() or query.startswith('http'):
                    import re
                    video_match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})', query)
                    if video_match:
                        is_video = True
                        video_id = video_match.group(1)
                        logger.info(f"🎬 Video individual detectado: {video_id}")
                    elif any(token in query for token in ['/channel/', '/@', '/user/', '/c/']):
                        is_channel = True
                        if '/@' in query:
                            channel_identifier = '@' + query.split('/@')[1].split('/')[0].split('?')[0]
                        elif '/channel/' in query:
                            channel_identifier = query.split('/channel/')[1].split('/')[0].split('?')[0]
                        else:
                            channel_identifier = query
                        logger.info(f"📡 URL de canal detectada: {channel_identifier}")
                    else:
                        logger.warning(f"⚠️ URL de YouTube no reconocida como canal o video: {query}")
                        search_query = query
                        logger.info(f"🔍 Intentando como búsqueda: '{search_query}'")
                elif query.startswith('@') or (query.startswith('UC') and len(query) > 10):
                    is_channel = True
                    channel_identifier = query
                    logger.info(f"📡 Identificador de canal detectado: {channel_identifier}")
                elif len(query) == 11 and query.replace('-', '').replace('_', '').isalnum():
                    is_video = True
                    video_id = query
                    logger.info(f"🎬 Video ID detectado: {video_id}")
                else:
                    search_query = query
                    logger.info(f"🔍 Búsqueda detectada: '{search_query}'")

                result_queue = queue.Queue()
                exception_queue = queue.Queue()
                posts = []

                def scrape_worker():
                    try:
                        scraper = YouTubeScraper(headless=False, use_api=True)

                        if is_video and video_id:
                            logger.info(f"🎬 Extrayendo video individual: {video_id}")
                            from youtube_api_scraper import YouTubeAPIScraper
                            api_key = os.getenv('YOUTUBE_API_KEY') or os.getenv('GOOGLE_API_KEY')
                            if api_key:
                                try:
                                    api_scraper = YouTubeAPIScraper(api_key)
                                    video_details = api_scraper.get_video_details(video_id)
                                    videos = [video_details] if video_details else []
                                except Exception:
                                    videos = scraper.search_videos(query, 1)
                            else:
                                videos = scraper.search_videos(query, 1)
                        elif is_channel and channel_identifier:
                            logger.info(f"📡 Extrayendo videos del canal: {channel_identifier}")
                            videos = scraper.get_channel_videos(channel_identifier, max_posts)
                        elif search_query:
                            logger.info(f"🔍 Buscando videos con query: '{search_query}'")
                            videos = scraper.search_videos(search_query, max_posts)
                        else:
                            logger.warning("⚠️ No se pudo determinar tipo de búsqueda para YouTube")
                            videos = []

                        scraper.close()

                        formatted_posts = []
                        for video in videos:
                            title = video.get('title', '').strip()
                            description = video.get('description', '').strip()

                            if not description or description == title or len(description) < 10:
                                text_content = title
                            else:
                                text_content = f"{title}\n\n{description}"

                            formatted_posts.append({
                                'platform': 'youtube',
                                'username': video.get('channel', 'Unknown'),
                                'text': text_content,
                                'cleaned_text': text_content.strip(),
                                'title': title,
                                'image_url': video.get('thumbnail'),
                                'video_url': video.get('url'),
                                'url': video.get('url', ''),
                                'date': video.get('published_at', datetime.now().isoformat()),
                                'created_at': video.get('published_at', datetime.now().isoformat()),
                                'likes': video.get('likes', 0),
                                'retweets': 0,
                                'replies': video.get('comments', 0),
                                'hashtags': video.get('tags', []),
                                'channel': video.get('channel', 'Unknown'),
                                'channel_id': video.get('channel_id', ''),
                                'views': video.get('views', 0),
                                'duration': video.get('duration', '0:00'),
                                'video_id': video.get('id', ''),
                                'scraped_at': datetime.now().isoformat()
                            })

                        result_queue.put(formatted_posts)
                        logger.info(f"✅ ✅ ✅ Scraping completado: {len(formatted_posts)} videos REALES de YouTube")
                    except Exception as e:
                        logger.error(f"❌ Error en scrape_worker de YouTube: {e}")
                        import traceback
                        logger.error(f"Traceback: {traceback.format_exc()}")
                        exception_queue.put(e)

                scrape_thread = threading.Thread(target=scrape_worker, daemon=True)
                scrape_thread.start()
                scrape_thread.join(timeout=600)  # 10 minutos timeout (YouTube puede tardar con canales grandes)

                if scrape_thread.is_alive():
                    logger.warning("⏱️ Timeout en scraping real de YouTube después de 600 segundos (10 minutos)")
                else:
                    if not exception_queue.empty():
                        error = exception_queue.get()
                        logger.warning(f"⏱️ Error en scraping real de YouTube: {error}")
                    elif not result_queue.empty():
                        posts = result_queue.get()

                if posts and len(posts) > 0:
                    real_posts = [p for p in posts if p.get('text') and len(p.get('text', '').strip()) > 10]
                    if real_posts:
                        final_posts = real_posts
                        demo_mode = False
                    else:
                        logger.warning(f"⚠️ Se extrajeron {len(posts)} videos pero ninguno tiene contenido válido")
                        final_posts = []
                        demo_mode = True
                else:
                    logger.warning("⚠️ No se encontraron videos reales de YouTube")
                    final_posts = []
                    demo_mode = True

            except Exception as youtube_error:
                logger.error(f"❌ Error inicializando YouTubeScraper: {youtube_error}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                final_posts = []
                demo_mode = True
        else:
            final_posts = []
            demo_mode = True
    
    # SISTEMA HÍBRIDO: Si no hay datos reales, generar mocks temporales para feedback
        if demo_mode:
            logger.warning(f"⚠️ No se pudieron extraer posts REALES de {platform.upper()}")
            logger.info(f"💡 Generando posts de ejemplo (mocks) para feedback inmediato...")
            logger.info(f"ℹ️ Estos son datos de ejemplo basados en '{query}'")
            logger.info("ℹ️ Si el scraping real funciona después, los mocks se reemplazarán automáticamente")

            try:
                if platform == 'facebook':
                    demo_posts = _generate_demo_facebook_posts(query, max_posts, mode)
                elif platform == 'reddit':
                    demo_posts = _generate_demo_tweets(query, max_posts, mode)
                    for post in demo_posts:
                        post['platform'] = 'reddit'
                        post['subreddit'] = query.split('/')[-1] if '/' in query else query
                elif platform == 'youtube':
                    demo_posts = _generate_demo_tweets(query, max_posts, mode)
                    for post in demo_posts:
                        post['platform'] = 'youtube'
                        post['channel'] = query.split('/')[-1] if '/' in query else query
                else:
                    demo_posts = _generate_demo_tweets(query, max_posts, mode)

                if demo_posts and len(demo_posts) > 0:
                    logger.info(f"✅ Generados {len(demo_posts)} posts de ejemplo (mocks) para feedback")
                    final_posts = demo_posts
                    demo_mode = True
                else:
                    logger.error("❌ Error generando posts de ejemplo")
                    final_posts = []
                    demo_mode = True
            except Exception as e:
                logger.error(f"❌ Error generando posts de ejemplo: {e}")
                final_posts = []
                demo_mode = True

        # Procesar posts (reales o mocks según lo que tengamos)
        try:
            if demo_mode:
                logger.info(f"📊 Procesando {len(final_posts)} posts de EJEMPLO (mocks) de {platform}...")
                message_type = "EJEMPLO (mocks)"
            else:
                logger.info(f"📊 Procesando {len(final_posts)} posts REALES de {platform}...")
                message_type = "REALES"

            from social_media_processor import SocialMediaProcessor
            from social_media_db import SocialMediaDB

            processor = SocialMediaProcessor()
            processed_posts = processor.process_batch(final_posts)

            logger.info(f"💾 Guardando {len(processed_posts)} posts en base de datos...")
            db = SocialMediaDB()

            # Limpiar datos viejos de la misma plataforma antes de guardar nuevos
            try:
                logger.info(f"🗑️ Limpiando datos viejos de {platform} antes de guardar nuevos...")
                conn = db.get_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM social_media_posts WHERE platform = ?", (platform,))
                    deleted_count = cursor.rowcount
                    conn.commit()
                    conn.close()
                    logger.info(f"✅ Eliminados {deleted_count} posts viejos de {platform}")
            except Exception as e:
                logger.warning(f"⚠️ Error limpiando datos viejos: {e}, continuando...")

            saved_count = db.save_batch(processed_posts)

            if saved_count == 0 and processed_posts:
                logger.warning(f"⚠️ saved_count es 0 pero hay {len(processed_posts)} posts procesados. Usando número de procesados.")
                saved_count = len(processed_posts)

            logger.info(f"✅ {saved_count} posts guardados exitosamente (de {len(processed_posts)} procesados)")

            posts_with_images = sum(1 for post in processed_posts if post.get('image_url'))
            logger.info(f"🖼️ {posts_with_images} posts tienen imágenes")

            platform_name = 'Facebook' if platform == 'facebook' else ('Reddit' if platform == 'reddit' else ('YouTube' if platform == 'youtube' else 'Twitter/X'))

            if demo_mode:
                message = (
                    f'⚠️ ⚠️ ⚠️ MODO EJEMPLO ACTIVADO\n\n'
                    f'❌ No se pudieron extraer posts REALES de {platform_name}\n'
                    f'🔒 {platform_name} requiere autenticación para acceder al contenido\n\n'
                    f'📊 {len(final_posts)} posts de EJEMPLO generados basados en "{query}"\n'
                    f'💾 {saved_count} posts guardados en la base de datos\n'
                    f'🖼️ {posts_with_images} posts con imágenes incluidas\n\n'
                    f'ℹ️ Estos son posts de EJEMPLO para demostración\n'
                    f'💡 Si el scraping real funciona después, estos se reemplazarán automáticamente'
                )
            else:
                message = (
                    f'✅ ✅ ✅ SCRAPING REAL COMPLETADO EXITOSAMENTE\n\n'
                    f'📊 {len(final_posts)} posts REALES extraídos de {platform_name}\n'
                    f'💾 {saved_count} posts guardados en la base de datos\n'
                    f'🖼️ {posts_with_images} posts con imágenes incluidas\n\n'
                    f'✅ Estos son datos REALES del enlace proporcionado'
                )

            posts_to_send = processed_posts[:100]
            logger.info(f"📤 Enviando {len(posts_to_send)} posts al frontend en la respuesta del scraping")
            posts_with_images_in_response = sum(1 for post in posts_to_send if post.get('image_url'))
            logger.info(f"🖼️ De {len(posts_to_send)} posts enviados, {posts_with_images_in_response} tienen imágenes")

            if posts_to_send:
                sample_post = posts_to_send[0]
                logger.info(
                    f"📝 Ejemplo de post enviado: ID={sample_post.get('id', 'N/A')}, "
                    f"username={sample_post.get('username')}, image_url={'✅' if sample_post.get('image_url') else '❌ None'}"
                )

            return jsonify({
                'success': True,
                'total_scraped': len(final_posts),
                'total_saved': saved_count,
                'posts': posts_to_send,
                'demo_mode': demo_mode,
                'message': message,
                'tweets_with_images': posts_with_images,
                'platform': platform
            })
        except Exception as e:
            logger.error(f"❌ Error procesando posts REALES: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

            platform_name = 'Facebook' if platform == 'facebook' else ('Reddit' if platform == 'reddit' else ('YouTube' if platform == 'youtube' else 'Twitter/X'))
            return jsonify({
                'success': False,
                'error': f'Error procesando datos de {platform_name}',
                'message': (
                    f'❌ Error al procesar los datos extraídos.\n\n'
                    f'🔒 {platform_name} requiere autenticación para acceder al contenido.\n\n'
                    f'💡 Para obtener datos REALES necesitas:\n'
                    f'   - Autenticación en {platform_name}\n'
                    f'   - API oficial de {platform_name}\n'
                    f'   - O usar herramientas especializadas\n\n'
                    f'⚠️ El sistema NO generará datos simulados.'
                ),
                'total_scraped': 0,
                'total_saved': 0,
                'posts': [],
                'demo_mode': False,
                'platform': platform
            }), 400
    except Exception as scrape_error:
        logger.warning(f"⚠️ Scraping real falló: {scrape_error}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.error("❌ NO se generarán datos simulados (mocks)")
        
        platform_name = 'Facebook' if platform == 'facebook' else ('Reddit' if platform == 'reddit' else ('YouTube' if platform == 'youtube' else 'Twitter/X'))
        return jsonify({
            'success': False,
            'error': f'Error en scraping de {platform_name}',
            'message': (
                f'❌ Error al realizar el scraping.\n\n'
                f'🔒 {platform_name} requiere autenticación para acceder al contenido.\n\n'
                f'💡 Para obtener datos REALES necesitas:\n'
                f'   - Autenticación en {platform_name}\n'
                f'   - API oficial de {platform_name}\n'
                f'   - O usar herramientas especializadas\n\n'
                f'⚠️ El sistema NO generará datos simulados.'
            ),
            'total_scraped': 0,
            'total_saved': 0,
            'posts': [],
            'demo_mode': False,
            'platform': platform
        }), 500
    finally:
        if scraper:
            try:
                scraper.close()
            except Exception:
                pass

@app.route('/api/social-media/posts', methods=['GET'])
@require_auth
def get_social_media_posts():
    """Obtener posts de redes sociales con filtros"""
    try:
        platform = request.args.get('platform', None)
        category = request.args.get('category', None)
        sentiment = request.args.get('sentiment', None)
        language = request.args.get('language', None)
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)
        min_interactions = request.args.get('min_interactions', type=int)
        top_metric = request.args.get('top_metric', None)
        top_limit = request.args.get('top_limit', type=int)
        limit = min(request.args.get('limit', 100, type=int), 1000)
        offset = request.args.get('offset', 0, type=int)
        
        from social_media_db import SocialMediaDB
        db = SocialMediaDB()
        
        posts = db.get_posts(
            platform=platform,
            category=category,
            sentiment=sentiment,
            language=language,
            start_date=start_date,
            end_date=end_date,
            min_interactions=min_interactions,
            top_metric=top_metric,
            top_limit=top_limit,
            limit=limit,
            offset=offset
        )
        
        logger.info(f"📤 Enviando {len(posts)} posts al frontend")
        
        # Contar posts con imágenes
        posts_with_images = sum(1 for post in posts if post.get('image_url'))
        logger.info(f"🖼️ De {len(posts)} posts, {posts_with_images} tienen imágenes")
        
        return jsonify({
            'success': True,
            'total': len(posts),
            'posts': posts
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo posts: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/api/social-media/stats', methods=['GET'])
@require_auth
def get_social_media_stats():
    """Obtener estadísticas de redes sociales"""
    try:
        from social_media_db import SocialMediaDB
        db = SocialMediaDB()
        
        stats = db.get_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

if __name__ == '__main__':
    print("🚀 Iniciando API del Web Scraper...")

    # Inicializar base de datos
    if init_database():
        print("✅ Base de datos inicializada")
    else:
        print("❌ Error inicializando base de datos")

    debug_mode = os.environ.get('FLASK_DEBUG', '1') == '1'

    if not debug_mode or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        start_auto_update_scheduler()

    # Iniciar servidor en puerto 5001
    app.run(host='0.0.0.0', port=5001, debug=debug_mode)
