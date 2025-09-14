#!/usr/bin/env python3
"""
Script de prueba para verificar que MySQL funciona correctamente
"""

import pandas as pd
import json
from sqlalchemy import create_engine, text

def test_mysql_connection():
    """Probar conexión y guardado en MySQL"""
    
    print("🧪 Probando conexión y guardado en MySQL...")
    
    try:
        # Conectar a MySQL
        engine = create_engine('mysql+mysqlconnector://root@localhost:3306/noticias_db')
        
        # Crear tabla de prueba
        create_table_query = """
            CREATE TABLE IF NOT EXISTS test_articles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title TEXT NOT NULL,
                content LONGTEXT,
                images_data LONGTEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        
        with engine.connect() as conn:
            conn.execute(text(create_table_query))
            conn.commit()
            print("✅ Tabla de prueba creada")
        
        # Crear datos de prueba
        test_data = {
            'title': ['Artículo de prueba 1', 'Artículo de prueba 2'],
            'content': ['Contenido de prueba 1', 'Contenido de prueba 2'],
            'images_data': [
                json.dumps([{'url': 'test1.jpg', 'alt': 'Imagen 1'}]),
                json.dumps([{'url': 'test2.jpg', 'alt': 'Imagen 2'}])
            ]
        }
        
        df = pd.DataFrame(test_data)
        
        # Guardar en MySQL
        df.to_sql('test_articles', engine, if_exists='append', index=False)
        print("✅ Datos de prueba guardados")
        
        # Verificar que se guardaron
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) as count FROM test_articles"))
            count = result.fetchone()[0]
            print(f"✅ Verificación: {count} registros en la tabla")
        
        # Limpiar tabla de prueba
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE test_articles"))
            conn.commit()
            print("✅ Tabla de prueba eliminada")
        
        print("\n🎉 ¡MySQL funciona perfectamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_mysql_connection()
