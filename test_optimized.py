#!/usr/bin/env python3
"""
Script de prueba para el scraper optimizado
"""

import time
from optimized_scraper import SmartScraper, articles_to_dataframe

def test_optimized_scraper():
    """Probar el scraper optimizado con diferentes configuraciones"""
    
    print("🧪 Probando Scraper Optimizado...")
    
    # Configuraciones de prueba
    test_configs = [
        {"max_workers": 5, "max_articles": 10, "name": "Pequeño (10 artículos, 5 workers)"},
        {"max_workers": 10, "max_articles": 50, "name": "Mediano (50 artículos, 10 workers)"},
        {"max_workers": 20, "max_articles": 100, "name": "Grande (100 artículos, 20 workers)"}
    ]
    
    base_url = "https://elcomercio.pe/politica/"
    
    for config in test_configs:
        print(f"\n🚀 Probando: {config['name']}")
        
        scraper = SmartScraper(max_workers=config['max_workers'])
        
        try:
            start_time = time.time()
            
            articles = scraper.crawl_and_scrape_parallel(
                base_url,
                max_articles=config['max_articles'],
                extract_images=False  # Sin imágenes para prueba rápida
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"✅ Completado en {duration:.2f} segundos")
            print(f"📊 Artículos extraídos: {len(articles)}")
            print(f"⚡ Velocidad: {len(articles)/duration:.2f} artículos/segundo")
            
            # Mostrar algunos ejemplos
            if articles:
                print("\n📰 Primeros 3 artículos:")
                for i, article in enumerate(articles[:3]):
                    print(f"  {i+1}. {article.title[:60]}...")
                    print(f"     📰 {article.newspaper} | 📅 {article.date[:10] if article.date else 'N/A'}")
                    print(f"     👤 {article.author[:30] if article.author else 'N/A'}")
                    print()
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        finally:
            scraper.close()
    
    print("\n🎉 Pruebas completadas!")

if __name__ == "__main__":
    test_optimized_scraper()
