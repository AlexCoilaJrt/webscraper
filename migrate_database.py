#!/usr/bin/env python3
"""
Script para migrar la base de datos y agregar la columna max_competitors
"""

import sqlite3
import os

def migrate_database():
    """Migrar la base de datos para agregar max_competitors"""
    db_path = "subscription_database.db"
    
    if not os.path.exists(db_path):
        print("❌ Base de datos de suscripciones no encontrada")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar si la columna ya existe
        cursor.execute("PRAGMA table_info(plans)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'max_competitors' not in columns:
            print("📊 Agregando columna max_competitors a la tabla plans...")
            cursor.execute("ALTER TABLE plans ADD COLUMN max_competitors INTEGER NOT NULL DEFAULT 1")
            print("✅ Columna agregada exitosamente")
            
            # Actualizar los planes existentes
            print("🔄 Actualizando planes existentes...")
            
            # Plan gratuito
            cursor.execute("UPDATE plans SET max_competitors = 1 WHERE name = 'freemium'")
            
            # Plan premium
            cursor.execute("UPDATE plans SET max_competitors = 5 WHERE name = 'premium'")
            
            # Plan enterprise
            cursor.execute("UPDATE plans SET max_competitors = 20 WHERE name = 'enterprise'")
            
            print("✅ Planes actualizados")
        else:
            print("✅ Columna max_competitors ya existe")
        
        conn.commit()
        conn.close()
        
        print("🎉 Migración completada exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en la migración: {e}")
        return False

if __name__ == "__main__":
    success = migrate_database()
    if success:
        print("\n🚀 Ahora puedes ejecutar: python init_competitive_intelligence.py")
    else:
        print("\n❌ Error en la migración")

















