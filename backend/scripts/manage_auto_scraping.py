#!/usr/bin/env python3
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
        
        print("\n📁 Archivos del sistema:")
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
