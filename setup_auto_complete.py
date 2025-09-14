#!/usr/bin/env python3
"""
Script completo para configurar scraping automático
"""

import sqlite3
import json
import os
from datetime import datetime

def create_database():
    """Crear base de datos SQLite con las tablas necesarias"""
    try:
        conn = sqlite3.connect('scraping_data.db')
        cursor = conn.cursor()
        
        # Crear tabla de artículos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                url TEXT UNIQUE,
                summary TEXT,
                author TEXT,
                published_date TEXT,
                scraped_at TEXT,
                category TEXT,
                newspaper TEXT,
                region TEXT,
                images_found INTEGER DEFAULT 0,
                images_downloaded INTEGER DEFAULT 0,
                images_data TEXT
            )
        ''')
        
        # Crear tabla de imágenes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER,
                image_url TEXT,
                filename TEXT,
                downloaded_at TEXT,
                FOREIGN KEY (article_id) REFERENCES articles (id)
            )
        ''')
        
        # Crear tabla de estadísticas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraping_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                url_scraped TEXT,
                articles_found INTEGER,
                images_found INTEGER,
                images_downloaded INTEGER,
                duration_seconds INTEGER,
                method_used TEXT,
                created_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Base de datos creada exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error creando base de datos: {e}")
        return False

def create_cron_setup():
    """Crear script para configurar cron jobs fácilmente"""
    
    script_content = '''#!/bin/bash
# Script para configurar cron jobs de scraping automático

echo "🔧 Configurando scraping automático..."

# Crear backup del crontab actual
crontab -l > crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null || echo "No hay crontab existente"

# Agregar nuevos cron jobs
(crontab -l 2>/dev/null; echo "") | crontab -
(crontab -l 2>/dev/null; echo "# Scraping automático - Noticias matutinas (8:00 AM)") | crontab -
(crontab -l 2>/dev/null; echo "0 8 * * * /Users/usuario/Documents/scraping\\ 2/run_auto_scraping.sh") | crontab -
(crontab -l 2>/dev/null; echo "") | crontab -
(crontab -l 2>/dev/null; echo "# Scraping automático - Noticias vespertinas (6:00 PM)") | crontab -
(crontab -l 2>/dev/null; echo "0 18 * * * /Users/usuario/Documents/scraping\\ 2/run_auto_scraping.sh") | crontab -
(crontab -l 2>/dev/null; echo "") | crontab -
(crontab -l 2>/dev/null; echo "# Scraping automático - Diario Sin Fronteras (12:00 PM)") | crontab -
(crontab -l 2>/dev/null; echo "0 12 * * * /Users/usuario/Documents/scraping\\ 2/run_auto_scraping.sh") | crontab -

echo "✅ Cron jobs configurados exitosamente"
echo "📋 Para ver los cron jobs configurados: crontab -l"
echo "📋 Para ver los logs: tail -f auto_scraping.log"
echo "📋 Para eliminar todos los cron jobs: crontab -r"
'''
    
    with open('setup_cron.sh', 'w') as f:
        f.write(script_content)
    
    os.chmod('setup_cron.sh', 0o755)
    print("✅ Script de configuración de cron creado: setup_cron.sh")

def create_management_script():
    """Crear script de gestión del scraping automático"""
    
    script_content = '''#!/usr/bin/env python3
"""
Script de gestión del scraping automático
"""

import json
import sys
import os

def show_status():
    """Mostrar estado del scraping automático"""
    try:
        with open('auto_scraping_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        auto_config = config.get("auto_scraping", {})
        print(f"🔄 Scraping automático: {'✅ Habilitado' if auto_config.get('enabled') else '❌ Deshabilitado'}")
        
        schedules = auto_config.get("schedules", [])
        print(f"📅 Programaciones configuradas: {len(schedules)}")
        
        for i, schedule in enumerate(schedules, 1):
            status = "✅" if schedule.get("enabled") else "❌"
            print(f"   {i}. {status} {schedule['name']} - {schedule['cron_schedule']}")
        
        # Verificar archivos
        files = [
            'auto_scraping_config.json',
            'auto_scraper_standalone.py',
            'run_auto_scraping.sh',
            'scraping_data.db'
        ]
        
        print("\\n📁 Archivos del sistema:")
        for file in files:
            exists = "✅" if os.path.exists(file) else "❌"
            print(f"   {exists} {file}")
        
    except Exception as e:
        print(f"❌ Error mostrando estado: {e}")

def enable_disable(enabled):
    """Habilitar o deshabilitar scraping automático"""
    try:
        with open('auto_scraping_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        config["auto_scraping"]["enabled"] = enabled
        
        with open('auto_scraping_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        status = "habilitado" if enabled else "deshabilitado"
        print(f"✅ Scraping automático {status}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def run_now():
    """Ejecutar scraping ahora"""
    print("🚀 Ejecutando scraping automático...")
    os.system("python auto_scraper_standalone.py")

def show_logs():
    """Mostrar logs recientes"""
    try:
        with open('auto_scraping.log', 'r') as f:
            lines = f.readlines()
            print("📋 Últimas 20 líneas del log:")
            for line in lines[-20:]:
                print(line.strip())
    except FileNotFoundError:
        print("❌ Archivo de log no encontrado")

def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("""
🔧 Gestión del Scraping Automático

Uso: python manage_auto_scraping.py [comando]

Comandos disponibles:
  status     - Mostrar estado del sistema
  enable     - Habilitar scraping automático
  disable    - Deshabilitar scraping automático
  run        - Ejecutar scraping ahora
  logs       - Mostrar logs recientes
  help       - Mostrar esta ayuda
""")
        return
    
    command = sys.argv[1].lower()
    
    if command == "status":
        show_status()
    elif command == "enable":
        enable_disable(True)
    elif command == "disable":
        enable_disable(False)
    elif command == "run":
        run_now()
    elif command == "logs":
        show_logs()
    elif command == "help":
        main()
    else:
        print(f"❌ Comando desconocido: {command}")
        print("Usa 'python manage_auto_scraping.py help' para ver comandos disponibles")

if __name__ == "__main__":
    main()
'''
    
    with open('manage_auto_scraping.py', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    os.chmod('manage_auto_scraping.py', 0o755)
    print("✅ Script de gestión creado: manage_auto_scraping.py")

def main():
    """Función principal"""
    print("🚀 Configurando scraping automático completo...")
    
    # Crear base de datos
    if not create_database():
        return
    
    # Crear scripts de gestión
    create_cron_setup()
    create_management_script()
    
    print("""
✅ ¡Configuración completada!

📋 PRÓXIMOS PASOS:

1. 🔧 Configurar cron jobs:
   ./setup_cron.sh

2. 🎮 Gestionar el sistema:
   python manage_auto_scraping.py status
   python manage_auto_scraping.py run
   python manage_auto_scraping.py logs

3. 📅 Los scraping se ejecutarán automáticamente:
   - 8:00 AM - Noticias matutinas
   - 12:00 PM - Diario Sin Fronteras  
   - 6:00 PM - Noticias vespertinas

4. 📊 Verificar resultados:
   - Logs: tail -f auto_scraping.log
   - Base de datos: scraping_data.db
   - Estado: python manage_auto_scraping.py status

🎉 ¡Tu sistema de scraping automático está listo!
""")

if __name__ == "__main__":
    main()

