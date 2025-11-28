#!/usr/bin/env python3
"""
Configuración simple de MySQL para Web Scraper
"""

import mysql.connector
import sqlite3
import os
import sys

def try_mysql_connection():
    """Intentar diferentes configuraciones de MySQL"""
    configs = [
        # Sin contraseña
        {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': '',
            'database': 'noticias_db',
            'charset': 'utf8mb4'
        },
        # Con contraseña común
        {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': 'root',
            'database': 'noticias_db',
            'charset': 'utf8mb4'
        },
        # Con contraseña admin
        {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': 'admin',
            'database': 'noticias_db',
            'charset': 'utf8mb4'
        },
        # Con contraseña 123456
        {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': '123456',
            'database': 'noticias_db',
            'charset': 'utf8mb4'
        }
    ]
    
    for i, config in enumerate(configs):
        try:
            print(f"🔍 Probando configuración {i+1}...")
            
            # Probar conexión sin base de datos
            test_config = config.copy()
            del test_config['database']
            
            conn = mysql.connector.connect(**test_config)
            cursor = conn.cursor()
            cursor.execute("SHOW DATABASES")
            databases = [db[0] for db in cursor.fetchall()]
            
            cursor.close()
            conn.close()
            
            print(f"✅ ¡Conexión exitosa con configuración {i+1}!")
            print(f"   Usuario: {config['user']}")
            print(f"   Contraseña: {'(vacía)' if not config['password'] else config['password']}")
            print(f"   Bases de datos disponibles: {', '.join(databases)}")
            
            return config
            
        except mysql.connector.Error as e:
            print(f"❌ Configuración {i+1} falló: {e}")
            continue
    
    return None

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

def update_api_server(config):
    """Actualizar api_server.py para usar MySQL"""
    try:
        # Leer el archivo actual
        with open('api_server.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Crear la nueva configuración
        mysql_config = f"""
# Configuración MySQL
MYSQL_CONFIG = {{
    'host': '{config['host']}',
    'port': {config['port']},
    'user': '{config['user']}',
    'password': '{config['password']}',
    'database': '{config['database']}',
    'charset': 'utf8mb4'
}}

# Cambiar de SQLite a MySQL
DB_PATH = f"mysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
"""
        
        # Reemplazar la configuración de base de datos
        if 'DB_PATH = "news_database.db"' in content:
            content = content.replace('DB_PATH = "news_database.db"', f'DB_PATH = f"mysql://{config["user"]}:{config["password"]}@{config["host"]}:{config["port"]}/{config["database"]}"')
        
        # Agregar la configuración MySQL al inicio
        if 'MYSQL_CONFIG' not in content:
            # Encontrar donde agregar la configuración
            import_lines = content.find('import sqlite3')
            if import_lines != -1:
                content = content[:import_lines] + mysql_config + '\n' + content[import_lines:]
        
        # Escribir el archivo actualizado
        with open('api_server.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ api_server.py actualizado para usar MySQL")
        return True
        
    except Exception as e:
        print(f"❌ Error actualizando api_server.py: {e}")
        return False

def main():
    print("🚀 Configuración Automática de MySQL")
    print("=" * 40)
    
    # Paso 1: Probar conexiones
    print("\n1️⃣ Probando conexiones MySQL...")
    config = try_mysql_connection()
    
    if not config:
        print("\n❌ No se pudo conectar a MySQL con ninguna configuración.")
        print("\n🔧 Soluciones posibles:")
        print("   1. Verificar que MySQL esté corriendo: brew services start mysql")
        print("   2. Configurar contraseña de root: mysql_secure_installation")
        print("   3. Usar un usuario diferente")
        return False
    
    # Paso 2: Crear base de datos y tablas
    print(f"\n2️⃣ Creando base de datos y tablas...")
    if not create_database_and_tables(config):
        return False
    
    # Paso 3: Migrar datos
    print(f"\n3️⃣ Migrando datos de SQLite...")
    if not migrate_data(config):
        return False
    
    # Paso 4: Actualizar api_server.py
    print(f"\n4️⃣ Actualizando api_server.py...")
    if not update_api_server(config):
        return False
    
    print(f"\n🎉 ¡Configuración MySQL completada!")
    print(f"\n📋 Resumen:")
    print(f"   🗄️ Base de datos: {config['database']}")
    print(f"   🏠 Host: {config['host']}:{config['port']}")
    print(f"   👤 Usuario: {config['user']}")
    print(f"   🔑 Contraseña: {'(vacía)' if not config['password'] else config['password']}")
    
    print(f"\n🔄 Próximos pasos:")
    print(f"   1. Reiniciar el backend: pkill -f 'python api_server.py' && python api_server.py")
    print(f"   2. Probar la aplicación")
    
    return True

if __name__ == "__main__":
    main()
