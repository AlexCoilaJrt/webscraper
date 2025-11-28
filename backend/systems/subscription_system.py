import sqlite3
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import json

class SubscriptionSystem:
    def __init__(self, db_path: str = "subscription_database.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializar base de datos de suscripciones"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de planes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                price REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                max_articles_per_day INTEGER NOT NULL,
                max_images_per_scraping INTEGER NOT NULL,
                max_users INTEGER NOT NULL,
                max_competitors INTEGER NOT NULL DEFAULT 1,
                features TEXT NOT NULL, -- JSON string
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de suscripciones de usuarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'active', -- active, expired, cancelled
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date TIMESTAMP,
                payment_code TEXT UNIQUE,
                payment_verified BOOLEAN DEFAULT 0,
                payment_verification_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (plan_id) REFERENCES plans (id)
            )
        ''')
        
        # Tabla de códigos de pago
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                plan_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                status TEXT DEFAULT 'pending', -- pending, paid, expired, cancelled
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                payment_proof TEXT, -- URL o texto del comprobante
                verified_by INTEGER, -- ID del admin que verificó
                verified_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (plan_id) REFERENCES plans (id)
            )
        ''')
        
        # Tabla de límites de uso diario
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date DATE NOT NULL,
                articles_scraped INTEGER DEFAULT 0,
                images_downloaded INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, date)
            )
        ''')
        # Uso del chatbot por día
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date DATE NOT NULL,
                messages INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, date)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Crear planes por defecto
        self.create_default_plans()
    
    def create_default_plans(self):
        """Crear planes por defecto"""
        plans = [
            {
                'name': 'freemium',
                'display_name': 'Plan Gratuito',
                'price': 0.0,
                'max_articles_per_day': 50,
                'max_images_per_scraping': 10,
                'max_users': 1,
                'max_competitors': 1,
                'features': json.dumps([
                    '50 artículos por día',
                    '10 imágenes por scraping',
                    'Chat básico (30 mensajes/día)',
                    'Búsqueda y resumen básicos',
                    'Estadísticas básicas (listas y KPIs simples)',
                    'Análisis de sentimientos básico (sin comparación con comentarios)',
                    'Competitive Intelligence: 1 competidor',
                    'Trending Predictor: 0 predicciones/día',
                    '1 usuario por cuenta',
                    'Sin exportación ni auto‑update',
                    'Soporte por email'
                ])
            },
            {
                'name': 'premium',
                'display_name': 'Plan Premium',
                'price': 29.0,
                'max_articles_per_day': 500,
                'max_images_per_scraping': 100,
                'max_users': 5,
                'max_competitors': 5,
                'features': json.dumps([
                    '500 artículos por día',
                    '100 imágenes por scraping',
                    'Chat avanzado (200 mensajes/día)',
                    'Resumen combinado y explicaciones guiadas',
                    'Estadísticas avanzadas (gráficos y comparativas)',
                    'Análisis de sentimientos con comparación noticias vs comentarios virales',
                    'Alertas básicas de sentimiento negativo',
                    'Exportación Excel/CSV (UI y chat)',
                    'Consultas guardadas desde el chat',
                    'Competitive Intelligence: hasta 5 competidores',
                    'Trending Predictor: 5 predicciones/día',
                    'Hasta 5 usuarios por cuenta',
                    'Scraping programado (auto‑update desde UI)',
                    'Soporte prioritario'
                ])
            },
            {
                'name': 'enterprise',
                'display_name': 'Plan Enterprise',
                'price': 99.0,
                'max_articles_per_day': -1, # Ilimitado
                'max_images_per_scraping': -1, # Ilimitado
                'max_users': -1, # Ilimitado
                'max_competitors': 20,
                'features': json.dumps([
                    'Artículos ilimitados',
                    'Imágenes ilimitadas',
                    'Chat sin límites y acciones completas',
                    'Exportación y auto‑update desde chat',
                    'Consultas guardadas + alertas por email',
                    'Competitive Intelligence: hasta 20 competidores',
                    'Trending Predictor: 20 predicciones/día',
                    'Usuarios ilimitados',
                    'API completa e integración con webhooks',
                    'Análisis de sentimientos avanzado completo',
                    'Comparación noticias vs comentarios virales en tiempo real',
                    'Alertas avanzadas de sentimiento negativo con notificaciones',
                    'Integración inteligente de anuncios basada en sentimiento',
                    'Soporte 24/7'
                ])
            }
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for plan in plans:
            cursor.execute('''
                INSERT OR IGNORE INTO plans 
                (name, display_name, price, max_articles_per_day, max_images_per_scraping, max_users, max_competitors, features)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                plan['name'],
                plan['display_name'],
                plan['price'],
                plan['max_articles_per_day'],
                plan['max_images_per_scraping'],
                plan['max_users'],
                plan.get('max_competitors', 1),
                plan['features']
            ))
        
        conn.commit()
        conn.close()
    
    def get_all_plans(self) -> List[Dict]:
        """Obtener todos los planes disponibles"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, display_name, price, currency, max_articles_per_day, 
                   max_images_per_scraping, max_users, features, is_active
            FROM plans WHERE is_active = 1
            ORDER BY price ASC
        ''')
        
        plans = []
        for row in cursor.fetchall():
            plans.append({
                'id': row[0],
                'name': row[1],
                'display_name': row[2],
                'price': row[3],
                'currency': row[4],
                'max_articles_per_day': row[5],
                'max_images_per_scraping': row[6],
                'max_users': row[7],
                'features': json.loads(row[8]),
                'is_active': bool(row[9])
            })
        
        conn.close()
        return plans
    
    def get_plan_by_id(self, plan_id: int) -> Optional[Dict]:
        """Obtener plan por ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, display_name, price, currency, max_articles_per_day, 
                   max_images_per_scraping, max_users, features, is_active
            FROM plans WHERE id = ?
        ''', (plan_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'display_name': row[2],
                'price': row[3],
                'currency': row[4],
                'max_articles_per_day': row[5],
                'max_images_per_scraping': row[6],
                'max_users': row[7],
                'features': json.loads(row[8]),
                'is_active': bool(row[9])
            }
        return None
    
    def get_plan_by_name(self, plan_name: str) -> Optional[Dict]:
        """Obtener plan por nombre"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, display_name, price, currency, max_articles_per_day, 
                   max_images_per_scraping, max_users, features, is_active
            FROM plans WHERE name = ?
        ''', (plan_name,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'display_name': row[2],
                'price': row[3],
                'currency': row[4],
                'max_articles_per_day': row[5],
                'max_images_per_scraping': row[6],
                'max_users': row[7],
                'features': json.loads(row[8]),
                'is_active': bool(row[9])
            }
        return None
    
    def create_user_subscription(self, user_id: int, plan_id: int) -> int:
        """Crear suscripción para un usuario"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Desactivar suscripciones anteriores
        cursor.execute('''
            UPDATE user_subscriptions 
            SET status = 'inactive', end_date = CURRENT_TIMESTAMP 
            WHERE user_id = ? AND status = 'active'
        ''', (user_id,))
        
        # Crear nueva suscripción
        cursor.execute('''
            INSERT INTO user_subscriptions (user_id, plan_id, status, start_date)
            VALUES (?, ?, 'active', CURRENT_TIMESTAMP)
        ''', (user_id, plan_id))
        
        subscription_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return subscription_id
    
    def get_user_subscription(self, user_id: int) -> Optional[Dict]:
        """Obtener suscripción activa del usuario"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT us.id, us.plan_id, us.status, us.start_date, us.end_date,
                   p.name, p.display_name, p.max_articles_per_day, 
                   p.max_images_per_scraping, p.max_users, p.features
            FROM user_subscriptions us
            JOIN plans p ON us.plan_id = p.id
            WHERE us.user_id = ? AND us.status = 'active'
            ORDER BY us.start_date DESC
            LIMIT 1
        ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'plan_id': row[1],
                'status': row[2],
                'start_date': row[3],
                'end_date': row[4],
                'plan_name': row[5],
                'plan_display_name': row[6],
                'max_articles_per_day': row[7],
                'max_images_per_scraping': row[8],
                'max_users': row[9],
                'features': json.loads(row[10])
            }
        return None
    
    def create_payment_code(self, user_id: int, plan_id: int) -> Dict:
        """Crear código de pago único"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Obtener información del plan
        cursor.execute('SELECT price, currency FROM plans WHERE id = ?', (plan_id,))
        plan = cursor.fetchone()
        
        if not plan:
            conn.close()
            raise ValueError("Plan no encontrado")
        
        # Generar código único
        code = f"PAY-{secrets.token_hex(8).upper()}"
        
        # Fecha de expiración (7 días)
        expires_at = datetime.now() + timedelta(days=7)
        
        cursor.execute('''
            INSERT INTO payment_codes 
            (code, user_id, plan_id, amount, currency, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (code, user_id, plan_id, plan[0], plan[1], expires_at))
        
        payment_code_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            'id': payment_code_id,
            'code': code,
            'amount': plan[0],
            'currency': plan[1],
            'expires_at': expires_at.isoformat()
        }
    
    def verify_payment(self, payment_code: str, admin_user_id: int, payment_proof: str = None) -> bool:
        """Verificar pago y activar suscripción"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Obtener información del código de pago
        cursor.execute('''
            SELECT id, user_id, plan_id, amount, status, expires_at
            FROM payment_codes 
            WHERE code = ? AND status = 'pending'
        ''', (payment_code,))
        
        payment = cursor.fetchone()
        if not payment:
            conn.close()
            return False
        
        payment_id, user_id, plan_id, amount, status, expires_at = payment
        
        # Verificar que no haya expirado
        if datetime.fromisoformat(expires_at) < datetime.now():
            cursor.execute('''
                UPDATE payment_codes SET status = 'expired' WHERE id = ?
            ''', (payment_id,))
            conn.commit()
            conn.close()
            return False
        
        # Marcar pago como verificado
        cursor.execute('''
            UPDATE payment_codes 
            SET status = 'paid', payment_proof = ?, verified_by = ?, verified_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (payment_proof, admin_user_id, payment_id))
        
        # Obtener información del plan
        cursor.execute('SELECT max_articles_per_day, max_images_per_scraping, max_users FROM plans WHERE id = ?', (plan_id,))
        plan_info = cursor.fetchone()
        
        # Desactivar suscripción anterior si existe
        cursor.execute('''
            UPDATE user_subscriptions SET status = 'cancelled' 
            WHERE user_id = ? AND status = 'active'
        ''', (user_id,))
        
        # Crear nueva suscripción
        end_date = datetime.now() + timedelta(days=30)  # 30 días de suscripción
        
        cursor.execute('''
            INSERT INTO user_subscriptions 
            (user_id, plan_id, status, start_date, end_date, payment_code, payment_verified, payment_verification_date)
            VALUES (?, ?, 'active', CURRENT_TIMESTAMP, ?, ?, 1, CURRENT_TIMESTAMP)
        ''', (user_id, plan_id, end_date, payment_code))
        
        conn.commit()
        conn.close()
        return True
    
    def check_usage_limits(self, user_id: int, articles_count: int = 0, images_count: int = 0) -> Dict:
        """Verificar límites de uso del usuario"""
        subscription = self.get_user_subscription(user_id)
        
        if not subscription:
            # Usuario sin suscripción activa - usar plan freemium
            freemium_plan = self.get_plan_by_name('freemium')
            if not freemium_plan:
                return {'allowed': False, 'reason': 'No hay plan disponible'}
            subscription = freemium_plan
        
        # Verificar límites diarios
        today = datetime.now().date()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT articles_scraped, images_downloaded 
            FROM daily_usage 
            WHERE user_id = ? AND date = ?
        ''', (user_id, today))
        
        usage = cursor.fetchone()
        if not usage:
            # Crear registro de uso para hoy
            cursor.execute('''
                INSERT INTO daily_usage (user_id, date, articles_scraped, images_downloaded)
                VALUES (?, ?, 0, 0)
            ''', (user_id, today))
            conn.commit()
            current_articles = 0
            current_images = 0
        else:
            current_articles = usage[0]
            current_images = usage[1]
        
        conn.close()
        
        # Verificar límites
        max_articles = subscription['max_articles_per_day']
        max_images = subscription['max_images_per_scraping']
        
        articles_allowed = max_articles == -1 or (current_articles + articles_count) <= max_articles
        images_allowed = max_images == -1 or (current_images + images_count) <= max_images
        
        return {
            'allowed': articles_allowed and images_allowed,
            'current_articles': current_articles,
            'current_images': current_images,
            'max_articles': max_articles,
            'max_images': max_images,
            'plan_name': subscription.get('plan_display_name', subscription.get('display_name', 'Plan Desconocido')),
            'reason': None if (articles_allowed and images_allowed) else 'Límite de uso excedido'
        }
    
    def update_usage(self, user_id: int, articles_count: int = 0, images_count: int = 0):
        """Actualizar uso diario del usuario"""
        today = datetime.now().date()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO daily_usage (user_id, date, articles_scraped, images_downloaded)
            VALUES (?, ?, 
                COALESCE((SELECT articles_scraped FROM daily_usage WHERE user_id = ? AND date = ?), 0) + ?,
                COALESCE((SELECT images_downloaded FROM daily_usage WHERE user_id = ? AND date = ?), 0) + ?
            )
        ''', (user_id, today, user_id, today, articles_count, user_id, today, images_count))
        
        conn.commit()
        conn.close()
    
    def get_plan_by_name(self, plan_name: str) -> Optional[Dict]:
        """Obtener plan por nombre"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, display_name, price, currency, max_articles_per_day, 
                   max_images_per_scraping, max_users, features
            FROM plans WHERE name = ? AND is_active = 1
        ''', (plan_name,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'display_name': row[2],
                'price': row[3],
                'currency': row[4],
                'max_articles_per_day': row[5],
                'max_images_per_scraping': row[6],
                'max_users': row[7],
                'features': json.loads(row[8])
            }
        return None
    
    def get_pending_payments(self) -> List[Dict]:
        """Obtener pagos pendientes para administradores"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Obtener información de usuarios desde la base de datos de autenticación
        auth_conn = sqlite3.connect("auth_database.db")
        auth_cursor = auth_conn.cursor()
        
        cursor.execute('''
            SELECT pc.id, pc.code, pc.user_id, pc.plan_id, pc.amount, pc.currency,
                   pc.created_at, pc.expires_at, pc.payment_proof, p.display_name
            FROM payment_codes pc
            JOIN plans p ON pc.plan_id = p.id
            WHERE pc.status = 'pending' AND pc.expires_at > CURRENT_TIMESTAMP
            ORDER BY pc.created_at DESC
        ''')
        
        payments = []
        for row in cursor.fetchall():
            # Obtener username desde la base de datos de autenticación
            auth_cursor.execute('SELECT username FROM users WHERE id = ?', (row[2],))
            user_result = auth_cursor.fetchone()
            username = user_result[0] if user_result else f"Usuario {row[2]}"
            
            payments.append({
                'id': row[0],
                'code': row[1],
                'user_id': row[2],
                'plan_id': row[3],
                'amount': row[4],
                'currency': row[5],
                'created_at': row[6],
                'expires_at': row[7],
                'payment_proof': row[8],
                'username': username,
                'plan_name': row[9]
            })
        
        conn.close()
        auth_conn.close()
        return payments
    
    def get_user_payment_codes(self, user_id: int) -> List[Dict]:
        """Obtener códigos de pago del usuario"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT pc.id, pc.code, pc.amount, pc.currency, pc.status, 
                   pc.created_at, pc.expires_at, p.display_name
            FROM payment_codes pc
            JOIN plans p ON pc.plan_id = p.id
            WHERE pc.user_id = ?
            ORDER BY pc.created_at DESC
        ''', (user_id,))
        
        codes = []
        for row in cursor.fetchall():
            codes.append({
                'id': row[0],
                'code': row[1],
                'amount': row[2],
                'currency': row[3],
                'status': row[4],
                'created_at': row[5],
                'expires_at': row[6],
                'plan_name': row[7]
            })
        
        conn.close()
        return codes

    # ====== Límites de Chatbot por Plan ======
    def check_chat_message_limits(self, user_id: int, messages_to_add: int = 1) -> Dict:
        """Verificar si el usuario puede enviar más mensajes hoy según su plan."""
        subscription = self.get_user_subscription(user_id)
        plan_name = (subscription or {}).get('plan_name') or (subscription or {}).get('name') or 'freemium'
        plan_lower = str(plan_name).lower()
        if 'enterprise' in plan_lower:
            limit = -1  # ilimitado
        elif 'premium' in plan_lower:
            limit = 200
        else:
            limit = 30
        today = datetime.now().date()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT messages FROM chat_usage WHERE user_id = ? AND date = ?', (user_id, today))
        row = cursor.fetchone()
        current = row[0] if row else 0
        conn.close()
        allowed = True if limit == -1 else (current + messages_to_add) <= limit
        return {
            'allowed': allowed,
            'current_messages': current,
            'limit': limit,
            'plan_name': 'Enterprise' if limit == -1 else ('Premium' if limit == 200 else 'Freemium')
        }

    def update_chat_usage(self, user_id: int, messages_to_add: int = 1):
        """Incrementar contador de mensajes del día para el usuario."""
        today = datetime.now().date()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO chat_usage (user_id, date, messages)
            VALUES (
                ?, ?,
                COALESCE((SELECT messages FROM chat_usage WHERE user_id = ? AND date = ?), 0) + ?
            )
        ''', (user_id, today, user_id, today, messages_to_add))
        conn.commit()
        conn.close()
