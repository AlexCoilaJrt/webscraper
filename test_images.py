#!/usr/bin/env python3
"""
Script de prueba para verificar que las imágenes se extraen y muestran correctamente
"""

import json
import os
from pathlib import Path

def test_image_data():
    """Probar datos de imágenes extraídas"""
    
    print("🧪 Probando datos de imágenes...")
    
    # Buscar archivos de imágenes descargadas
    images_dir = Path("scraped_images")
    if not images_dir.exists():
        print("❌ No se encontró el directorio de imágenes")
        return
    
    print(f"📁 Directorio de imágenes: {images_dir.absolute()}")
    
    # Contar imágenes descargadas
    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.webp']:
        image_files.extend(images_dir.rglob(ext))
    
    print(f"🖼️ Total de imágenes encontradas: {len(image_files)}")
    
    # Mostrar estructura de directorios
    print("\n📂 Estructura de directorios:")
    for article_dir in images_dir.iterdir():
        if article_dir.is_dir():
            article_images = list(article_dir.glob('*'))
            print(f"  📁 {article_dir.name}: {len(article_images)} imágenes")
            for img in article_images[:3]:  # Mostrar máximo 3
                size = img.stat().st_size
                print(f"    🖼️ {img.name} ({size} bytes)")
    
    # Crear datos de prueba para verificar JSON
    test_data = {
        'local_path': str(image_files[0]) if image_files else 'test.jpg',
        'url': 'https://example.com/test.jpg',
        'alt_text': 'Imagen de prueba',
        'width': 800,
        'height': 600,
        'size_bytes': 50000
    }
    
    # Probar serialización JSON
    try:
        json_str = json.dumps([test_data], ensure_ascii=False)
        print(f"\n✅ JSON serializado correctamente: {len(json_str)} caracteres")
        
        # Probar deserialización
        parsed_data = json.loads(json_str)
        print(f"✅ JSON parseado correctamente: {len(parsed_data)} elementos")
        
    except Exception as e:
        print(f"❌ Error con JSON: {e}")
    
    print("\n🎉 Prueba de imágenes completada!")

if __name__ == "__main__":
    test_image_data()
