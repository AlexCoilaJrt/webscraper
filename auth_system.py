#!/usr/bin/env python3
"""
Sistema de Autenticación y Autorización
Maneja usuarios, roles y sesiones
"""

import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from functools import wraps
from flask import request, jsonify, current_app
import sqlite3
import os
from subscription_system import SubscriptionSystem

# Configuración
SECRET_KEY = "web_scraper_secret_key_2024"  # En producción usar variable de entorno
JWT_EXPIRATION_HOURS = 24

class AuthSystem:
    def __init__(self, db_path: str = "auth_database.db"):
        self.db_path = db_path
        self.subscription_system = SubscriptionSystem()
        self.init_database()
        self.create_default_admin()
    
    def init_database(self):
        """Inicializar base de datos de autenticación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de usuarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # Tabla de sesiones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        # Tabla de consultas guardadas del chatbot
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS saved_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                query TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Tabla de permisos disponibles (features/secciones de la aplicación)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de permisos de usuario (relación muchos a muchos)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                permission_id INTEGER NOT NULL,
                granted_by INTEGER,
                granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (permission_id) REFERENCES permissions (id),
                FOREIGN KEY (granted_by) REFERENCES users (id),
                UNIQUE(user_id, permission_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Crear permisos por defecto
        self.create_default_permissions()
    
    def create_default_permissions(self):
        """Crear permisos por defecto del sistema"""
        default_permissions = [
            {'code': 'view_dashboard', 'name': 'Ver Dashboard', 'description': 'Acceso al dashboard principal', 'category': 'Navegación'},
            {'code': 'view_articles', 'name': 'Ver Artículos', 'description': 'Acceso a la lista de artículos', 'category': 'Contenido'},
            {'code': 'view_images', 'name': 'Ver Imágenes', 'description': 'Acceso a la galería de imágenes', 'category': 'Contenido'},
            {'code': 'view_analytics', 'name': 'Ver Análisis', 'description': 'Acceso a análisis y estadísticas', 'category': 'Análisis'},
            {'code': 'view_sentiments', 'name': 'Ver Análisis de Sentimientos', 'description': 'Acceso al análisis de sentimientos', 'category': 'Análisis'},
            {'code': 'view_ads', 'name': 'Ver Anuncios', 'description': 'Acceso a gestión de anuncios', 'category': 'Anuncios'},
            {'code': 'view_subscriptions', 'name': 'Ver Suscripciones', 'description': 'Acceso a planes y suscripciones', 'category': 'Suscripciones'},
            {'code': 'view_social_media', 'name': 'Ver Redes Sociales', 'description': 'Acceso a redes sociales', 'category': 'Redes Sociales'},
            {'code': 'view_users', 'name': 'Ver Usuarios', 'description': 'Acceso a gestión de usuarios', 'category': 'Administración'},
            {'code': 'manage_scraping', 'name': 'Gestionar Scraping', 'description': 'Iniciar/detener scraping', 'category': 'Administración'},
            {'code': 'manage_database', 'name': 'Gestionar Base de Datos', 'description': 'Configurar y limpiar BD', 'category': 'Administración'},
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for perm in default_permissions:
            cursor.execute('''
                INSERT OR IGNORE INTO permissions (code, name, description, category)
                VALUES (?, ?, ?, ?)
            ''', (perm['code'], perm['name'], perm['description'], perm['category']))
        
        conn.commit()
        conn.close()
    
    def create_default_admin(self):
        """Crear usuario administrador por defecto"""
        admin_username = "admin"
        admin_password = "AdminSecure2024!"  # Contraseña por defecto para el frontend
        admin_email = "admin@webscraper.com"
        
        if not self.user_exists(admin_username):
            self.create_user(admin_username, admin_email, admin_password, "admin")
            # Otorgar todos los permisos al admin por defecto
            admin_user = self.get_user_by_username(admin_username)
            if admin_user:
                self.grant_all_permissions_to_user(admin_user['id'])
            print(f"✅ Usuario administrador creado: {admin_username} / {admin_password}")
        else:
            # Si el usuario ya existe, verificar y actualizar la contraseña si es diferente
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash FROM users WHERE username = ?", (admin_username,))
            result = cursor.fetchone()
            conn.close()
            
            if result and not self.verify_password(admin_password, result[0]):
                print("⚠️ Usuario admin ya existe, actualizando contraseña...")
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                password_hash = self.hash_password(admin_password)
                cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (password_hash, admin_username))
                conn.commit()
                conn.close()
                print("✅ Contraseña actualizada")
            else:
                print("✅ Credenciales verificadas correctamente")
    
    def hash_password(self, password: str) -> str:
        """Hashear contraseña con salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{password_hash.hex()}"
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verificar contraseña"""
        try:
            salt, hash_part = password_hash.split(':')
            password_hash_check = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return password_hash_check.hex() == hash_part
        except:
            return False
    
    def create_user(self, username: str, email: str, password: str, role: str = "user") -> bool:
        """Crear nuevo usuario"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, role))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    # -----------------------------------------------------------------
    # Métodos auxiliares de suscripciones (delegan en SubscriptionSystem)
    # -----------------------------------------------------------------
    def get_all_plans(self) -> List[Dict[str, Any]]:
        """Obtener todos los planes de suscripción disponibles"""
        return self.subscription_system.get_all_plans()
    
    def get_user_subscription(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Obtener la suscripción activa del usuario"""
        return self.subscription_system.get_user_subscription(user_id)
    
    def create_payment_code(self, user_id: int, plan_id: int) -> Dict[str, Any]:
        """Crear un código de pago para el usuario"""
        return self.subscription_system.create_payment_code(user_id, plan_id)
    
    def check_usage_limits(self, user_id: int, articles_count: int = 0, images_count: int = 0) -> Dict[str, Any]:
        """Verificar los límites de uso del usuario"""
        return self.subscription_system.check_usage_limits(user_id, articles_count, images_count)
    
    def user_exists(self, username: str) -> bool:
        """Verificar si el usuario existe"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        
        conn.close()
        return result is not None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Autenticar usuario"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, password_hash, role, is_active
            FROM users WHERE username = ? AND is_active = 1
        ''', (username,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user and self.verify_password(password, user[3]):
            # Obtener información de suscripción
            subscription = self.subscription_system.get_user_subscription(user[0])
            
            user_data = {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'role': user[4],
                'is_active': user[5],
                'subscription': subscription
            }
            
            # Actualizar último login
            self.update_last_login(user[0])
            
            return user_data
        return None
    
    def generate_token(self, user_data: Dict[str, Any]) -> str:
        """Generar JWT token"""
        payload = {
            'user_id': user_data['id'],
            'username': user_data['username'],
            'role': user_data['role'],
            'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verificar y decodificar token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Obtener usuario por nombre de usuario"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, role, is_active, created_at, last_login
                FROM users WHERE username = ?
            ''', (username,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'role': user[3],
                    'is_active': bool(user[4]),
                    'created_at': user[5],
                    'last_login': user[6]
                }
            return None
        except Exception as e:
            print(f"Error obteniendo usuario: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Obtener usuario por ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, role, is_active, created_at, last_login
            FROM users WHERE id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'role': user[3],
                'is_active': user[4],
                'created_at': user[5],
                'last_login': user[6]
            }
        return None
    
    def update_last_login(self, user_id: int):
        """Actualizar último login"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET last_login = ? WHERE id = ?
        ''', (datetime.now().isoformat(), user_id))
        
        conn.commit()
        conn.close()
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Obtener todos los usuarios"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, role, is_active, created_at, last_login
            FROM users ORDER BY created_at DESC
        ''')
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'role': row[3],
                'is_active': row[4],
                'created_at': row[5],
                'last_login': row[6]
            })
        
        conn.close()
        return users
    
    def save_user_query(self, user_id: int, query: str) -> bool:
        """Guardar una consulta del usuario."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO saved_queries (user_id, query) VALUES (?, ?)', (user_id, query.strip()))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    
    def update_user_password(self, user_id: int, new_password: str) -> bool:
        """Actualizar contraseña del usuario"""
        try:
            import hashlib
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Hashear la nueva contraseña
            password_hash = hashlib.sha256(new_password.encode()).hexdigest()
            
            cursor.execute('''
                UPDATE users SET password_hash = ? WHERE id = ?
            ''', (password_hash, user_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error actualizando contraseña: {e}")
            return False
    
    def update_user_role(self, user_id: int, new_role: str) -> bool:
        """Actualizar rol de usuario"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users SET role = ? WHERE id = ?
            ''', (new_role, user_id))
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except:
            return False
    
    # ========== MÉTODOS DE PERMISOS ==========
    
    def get_all_permissions(self) -> List[Dict]:
        """Obtener todos los permisos disponibles"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, code, name, description, category, is_active
                FROM permissions
                WHERE is_active = 1
                ORDER BY category, name
            ''')
            
            permissions = []
            for row in cursor.fetchall():
                permissions.append({
                    'id': row[0],
                    'code': row[1],
                    'name': row[2],
                    'description': row[3],
                    'category': row[4],
                    'is_active': bool(row[5])
                })
            
            conn.close()
            return permissions
        except Exception as e:
            print(f"Error obteniendo permisos: {e}")
            return []
    
    def get_user_permissions(self, user_id: int) -> List[str]:
        """Obtener códigos de permisos de un usuario"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT p.code
                FROM permissions p
                INNER JOIN user_permissions up ON p.id = up.permission_id
                WHERE up.user_id = ? AND p.is_active = 1
            ''', (user_id,))
            
            permissions = [row[0] for row in cursor.fetchall()]
            conn.close()
            return permissions
        except Exception as e:
            print(f"Error obteniendo permisos de usuario: {e}")
            return []
    
    def has_permission(self, user_id: int, permission_code: str) -> bool:
        """Verificar si un usuario tiene un permiso específico"""
        # Los administradores tienen todos los permisos
        user = self.get_user_by_id(user_id)
        if user and user.get('role') == 'admin':
            return True
        
        permissions = self.get_user_permissions(user_id)
        return permission_code in permissions
    
    def grant_permission(self, user_id: int, permission_id: int, granted_by: int) -> bool:
        """Otorgar un permiso a un usuario"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO user_permissions (user_id, permission_id, granted_by)
                VALUES (?, ?, ?)
            ''', (user_id, permission_id, granted_by))
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error otorgando permiso: {e}")
            return False
    
    def revoke_permission(self, user_id: int, permission_id: int) -> bool:
        """Revocar un permiso de un usuario"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM user_permissions
                WHERE user_id = ? AND permission_id = ?
            ''', (user_id, permission_id))
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error revocando permiso: {e}")
            return False
    
    def set_user_permissions(self, user_id: int, permission_ids: List[int], granted_by: int) -> bool:
        """Establecer permisos de un usuario (reemplaza los existentes)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Eliminar permisos actuales
            cursor.execute('DELETE FROM user_permissions WHERE user_id = ?', (user_id,))
            
            # Agregar nuevos permisos
            for perm_id in permission_ids:
                cursor.execute('''
                    INSERT INTO user_permissions (user_id, permission_id, granted_by)
                    VALUES (?, ?, ?)
                ''', (user_id, perm_id, granted_by))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error estableciendo permisos: {e}")
            return False
    
    def grant_all_permissions_to_user(self, user_id: int) -> bool:
        """Otorgar todos los permisos a un usuario (útil para admin)"""
        try:
            permissions = self.get_all_permissions()
            permission_ids = [p['id'] for p in permissions]
            return self.set_user_permissions(user_id, permission_ids, user_id)
        except Exception as e:
            print(f"Error otorgando todos los permisos: {e}")
            return False
    
    def deactivate_user(self, user_id: int) -> bool:
        """Desactivar usuario"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users SET is_active = 0 WHERE id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except:
            return False


# Decoradores para protección de rutas
def require_auth(f):
    """Decorador para requerir autenticación"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Buscar token en headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer TOKEN
            except IndexError:
                return jsonify({'error': 'Token malformado'}), 401
        
        if not token:
            return jsonify({'error': 'Token requerido'}), 401
        
        # Verificar token
        auth_system = AuthSystem()
        payload = auth_system.verify_token(token)
        
        if not payload:
            return jsonify({'error': 'Token inválido o expirado'}), 401
        
        # Agregar información del usuario al request
        request.current_user = payload
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_admin(f):
    """Decorador para requerir rol de administrador"""
    @wraps(f)
    @require_auth
    def decorated_function(*args, **kwargs):
        if request.current_user.get('role') != 'admin':
            return jsonify({'error': 'Acceso denegado. Se requiere rol de administrador'}), 403
        return f(*args, **kwargs)
    
    return decorated_function


def require_user_or_admin(f):
    """Decorador para requerir usuario o admin"""
    @wraps(f)
    @require_auth
    def decorated_function(*args, **kwargs):
        role = request.current_user.get('role')
        if role not in ['user', 'admin']:
            return jsonify({'error': 'Acceso denegado'}), 403
        return f(*args, **kwargs)
    
    return decorated_function
