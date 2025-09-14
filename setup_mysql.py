#!/usr/bin/env python3
"""
Script para configurar MySQL y migrar datos de SQLite
"""

import mysql.connector
import sqlite3
import os
import sys
from datetime import datetime

# Configuración de MySQL
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '',  # Cambia esto por tu contraseña de MySQL
    'database': 'noticias_db',
    'charset': 'utf8mb4'
}

# Configuración de SQLite
SQLITE_DB = 'news_database.db'

def create_mysql_database():
    """Crear la base de datos MySQL"""
    try:
        # Conectar sin especificar base de datos
        config = MYSQL_CONFIG.copy()
        del config['database']
        
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        # Crear base de datos
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"✅ Base de datos '{MYSQL_CONFIG['database']}' creada exitosamente")
        
                cursor.close()
        conn.close()
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Error creando base de datos MySQL: {e}")
        return False

def create_mysql_tables():
    """Crear las tablas en MySQL"""
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        
        # Tabla articles
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
        
        # Tabla images
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
        
        # Tabla scraping_stats
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
        print(f"❌ Error creando tablas MySQL: {e}")
        return False

def migrate_data_from_sqlite():
    """Migrar datos de SQLite a MySQL"""
    try:
        # Conectar a SQLite
        sqlite_conn = sqlite3.connect(SQLITE_DB)
        sqlite_cursor = sqlite_conn.cursor()
        
        # Conectar a MySQL
        mysql_conn = mysql.connector.connect(**MYSQL_CONFIG)
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

def test_mysql_connection():
    """Probar la conexión a MySQL"""
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        
        # Contar registros
        cursor.execute("SELECT COUNT(*) FROM articles")
        articles_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM images")
        images_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM scraping_stats")
        stats_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print(f"✅ Conexión MySQL exitosa:")
        print(f"   📰 Artículos: {articles_count}")
        print(f"   🖼️ Imágenes: {images_count}")
        print(f"   📊 Estadísticas: {stats_count}")
        
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Error conectando a MySQL: {e}")
        return False

def main():
    print("🚀 Configurando MySQL para Web Scraper...")
    print("=" * 50)
    
    # Verificar si existe SQLite
    if not os.path.exists(SQLITE_DB):
        print(f"❌ No se encontró la base de datos SQLite: {SQLITE_DB}")
        return False
    
    # Paso 1: Crear base de datos
    print("\n1️⃣ Creando base de datos MySQL...")
    if not create_mysql_database():
        return False
    
    # Paso 2: Crear tablas
    print("\n2️⃣ Creando tablas MySQL...")
    if not create_mysql_tables():
        return False
    
    # Paso 3: Migrar datos
    print("\n3️⃣ Migrando datos de SQLite a MySQL...")
    if not migrate_data_from_sqlite():
        return False
    
    # Paso 4: Probar conexión
    print("\n4️⃣ Probando conexión MySQL...")
    if not test_mysql_connection():
        return False
    
    print("\n🎉 ¡Configuración MySQL completada exitosamente!")
    print("\n📝 Próximos pasos:")
    print("   1. Actualizar api_server.py para usar MySQL")
    print("   2. Instalar mysql-connector-python si no está instalado")
    print("   3. Reiniciar el backend")
    
    return True

if __name__ == "__main__":
    main()