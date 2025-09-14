#!/usr/bin/env python3
"""
Script interactivo para configurar MySQL
"""

import getpass
import mysql.connector
import sqlite3
import os
from datetime import datetime

def get_mysql_config():
    """Obtener configuración de MySQL del usuario"""
    print("🔧 Configuración de MySQL")
    print("=" * 30)
    
    host = input("Host (localhost): ").strip() or "localhost"
    port = input("Puerto (3306): ").strip() or "3306"
    user = input("Usuario (root): ").strip() or "root"
    password = getpass.getpass("Contraseña de MySQL: ")
    database = input("Nombre de base de datos (noticias_db): ").strip() or "noticias_db"
    
    return {
        'host': host,
        'port': int(port),
        'user': user,
        'password': password,
        'database': database,
        'charset': 'utf8mb4'
    }

def test_mysql_connection(config):
    """Probar conexión a MySQL"""
    try:
        # Probar conexión sin base de datos
        test_config = config.copy()
        del test_config['database']
        
        conn = mysql.connector.connect(**test_config)
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES")
        databases = [db[0] for db in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        print(f"✅ Conexión MySQL exitosa")
        print(f"📋 Bases de datos disponibles: {', '.join(databases)}")
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Error conectando a MySQL: {e}")
        return False

def create_database_and_tables(config):
    """Crear base de datos y tablas"""
    try:
        # Conectar sin especificar base de datos
        test_config = config.copy()
        del test_config['database']
        
        conn = mysql.connector.connect(**test_config)
        cursor = conn.cursor()
        
        # Crear base de datos
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"✅ Base de datos '{config['database']}' creada")
        
        cursor.close()
        conn.close()
        
        # Conectar a la nueva base de datos
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        # Crear tabla articles
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title TEXT NOT NULL,
                date TEXT,
                author TEXT,
                summary TEXT,
                content LONGTEXT,
                original_url TEXT,
                category TEXT,
                newspaper TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                images_found INT DEFAULT 0,
                images_downloaded INT DEFAULT 0,
                images_data LONGTEXT,
                article_id TEXT,
                url TEXT,
                region TEXT DEFAULT 'extranjero',
                INDEX idx_newspaper (newspaper),
                INDEX idx_category (category),
                INDEX idx_region (region),
                INDEX idx_scraped_at (scraped_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Crear tabla images
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INT AUTO_INCREMENT PRIMARY KEY,
                article_id INT,
                image_url TEXT,
                local_path TEXT,
                filename TEXT,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
                INDEX idx_article_id (article_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Crear tabla scraping_stats
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scraping_stats (
                id INT AUTO_INCREMENT PRIMARY KEY,
                url TEXT,
                method TEXT,
                articles_found INT,
                images_found INT,
                execution_time FLOAT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT,
                error_message TEXT,
                INDEX idx_timestamp (timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Tablas MySQL creadas exitosamente")
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Error creando base de datos/tablas: {e}")
        return False

def migrate_data(config):
    """Migrar datos de SQLite a MySQL"""
    sqlite_db = 'news_database.db'
    
    if not os.path.exists(sqlite_db):
        print(f"❌ No se encontró la base de datos SQLite: {sqlite_db}")
        return False
    
    try:
        # Conectar a SQLite
        sqlite_conn = sqlite3.connect(sqlite_db)
        sqlite_cursor = sqlite_conn.cursor()
        
        # Conectar a MySQL
        mysql_conn = mysql.connector.connect(**config)
        mysql_cursor = mysql_conn.cursor()
        
        # Migrar artículos
        sqlite_cursor.execute("SELECT * FROM articles")
        articles = sqlite_cursor.fetchall()
        
        print(f"📊 Migrando {len(articles)} artículos...")
        
        for article in articles:
            mysql_cursor.execute("""
                INSERT INTO articles (id, title, date, author, summary, content, original_url, 
                                    category, newspaper, scraped_at, images_found, images_downloaded, 
                                    images_data, article_id, url, region)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, article)
        
        # Migrar imágenes
        sqlite_cursor.execute("SELECT * FROM images")
        images = sqlite_cursor.fetchall()
        
        print(f"🖼️ Migrando {len(images)} imágenes...")
        
        for image in images:
            mysql_cursor.execute("""
                INSERT INTO images (id, article_id, image_url, local_path, filename, downloaded_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, image)
        
        # Migrar estadísticas
        sqlite_cursor.execute("SELECT * FROM scraping_stats")
        stats = sqlite_cursor.fetchall()
        
        print(f"📈 Migrando {len(stats)} estadísticas...")
        
        for stat in stats:
            mysql_cursor.execute("""
                INSERT INTO scraping_stats (id, url, method, articles_found, images_found, 
                                          execution_time, timestamp, status, error_message)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, stat)
        
        mysql_conn.commit()
        
        sqlite_cursor.close()
        sqlite_conn.close()
        mysql_cursor.close()
        mysql_conn.close()
        
        print("✅ Migración completada exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en la migración: {e}")
        return False

def create_config_file(config):
    """Crear archivo de configuración para el backend"""
    config_content = f'''# Configuración MySQL para Web Scraper
MYSQL_CONFIG = {{
    'host': '{config['host']}',
    'port': {config['port']},
    'user': '{config['user']}',
    'password': '{config['password']}',
    'database': '{config['database']}',
    'charset': 'utf8mb4'
}}

# Cambiar DB_PATH en api_server.py a:
# DB_PATH = "mysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
'''
    
    with open('mysql_config.py', 'w') as f:
        f.write(config_content)
    
    print("✅ Archivo mysql_config.py creado")

def main():
    print("🚀 Configurador MySQL para Web Scraper")
    print("=" * 40)
    
    # Obtener configuración
    config = get_mysql_config()
    
    # Probar conexión
    print(f"\n🔍 Probando conexión a MySQL...")
    if not test_mysql_connection(config):
        print("❌ No se pudo conectar a MySQL. Verifica las credenciales.")
        return False
    
    # Crear base de datos y tablas
    print(f"\n🏗️ Creando base de datos y tablas...")
    if not create_database_and_tables(config):
        return False
    
    # Migrar datos
    print(f"\n📦 Migrando datos de SQLite...")
    if not migrate_data(config):
        return False
    
    # Crear archivo de configuración
    print(f"\n📝 Creando archivo de configuración...")
    create_config_file(config)
    
    print(f"\n🎉 ¡Configuración MySQL completada!")
    print(f"\n📋 Resumen:")
    print(f"   🗄️ Base de datos: {config['database']}")
    print(f"   🏠 Host: {config['host']}:{config['port']}")
    print(f"   👤 Usuario: {config['user']}")
    print(f"   📁 Archivo de configuración: mysql_config.py")
    
    print(f"\n🔄 Próximos pasos:")
    print(f"   1. Actualizar api_server.py para usar MySQL")
    print(f"   2. Reiniciar el backend")
    
    return True

if __name__ == "__main__":
    main()
