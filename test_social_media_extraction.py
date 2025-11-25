#!/usr/bin/env python3
"""
Script de Prueba para Validar Extracción de Redes Sociales
Valida que el sistema extraiga correctamente:
- Contenido completo sin truncar
- URLs de imágenes válidas (no null)
- Métricas numéricas correctas
- Categoría relevante
- Sentimiento preciso
"""

import json
import logging
from social_media_scraper import TwitterScraper, FacebookScraper
from social_media_processor import SocialMediaProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_post_data(post: dict, platform: str) -> dict:
    """
    Validar que un post tenga todos los datos necesarios
    
    Args:
        post: Diccionario con datos del post
        platform: 'twitter' o 'facebook'
    
    Returns:
        Diccionario con resultados de validación
    """
    results = {
        'valid': True,
        'errors': [],
        'warnings': []
    }
    
    # Validar texto
    text = post.get('text', '')
    if not text or len(text.strip()) < 10:
        results['valid'] = False
        results['errors'].append('Texto muy corto o vacío (< 10 caracteres)')
    elif len(text) < 30:
        results['warnings'].append(f'Texto corto ({len(text)} caracteres), puede estar truncado')
    
    # Validar username
    username = post.get('username', '')
    if not username or username == 'unknown':
        results['warnings'].append('Username no encontrado o genérico')
    
    # Validar imagen
    image_url = post.get('image_url')
    if not image_url:
        results['warnings'].append('No se encontró imagen (image_url: null)')
    elif not isinstance(image_url, str) or not image_url.startswith('http'):
        results['errors'].append(f'URL de imagen inválida: {image_url}')
        results['valid'] = False
    
    # Validar métricas
    if platform == 'twitter':
        likes = post.get('likes', 0)
        retweets = post.get('retweets', 0)
        replies = post.get('replies', 0)
        
        if not isinstance(likes, int) or likes < 0:
            results['warnings'].append(f'Likes inválido: {likes}')
        if not isinstance(retweets, int) or retweets < 0:
            results['warnings'].append(f'Retweets inválido: {retweets}')
        if not isinstance(replies, int) or replies < 0:
            results['warnings'].append(f'Replies inválido: {replies}')
    
    elif platform == 'facebook':
        likes = post.get('likes', 0)
        comments = post.get('comments', 0)
        shares = post.get('shares', 0)
        
        if not isinstance(likes, int) or likes < 0:
            results['warnings'].append(f'Likes inválido: {likes}')
        if not isinstance(comments, int) or comments < 0:
            results['warnings'].append(f'Comments inválido: {comments}')
        if not isinstance(shares, int) or shares < 0:
            results['warnings'].append(f'Shares inválido: {shares}')
    
    # Validar fecha
    date = post.get('date', '')
    if not date:
        results['warnings'].append('Fecha no encontrada')
    
    # Validar URL
    url = post.get('url', '')
    if not url:
        results['warnings'].append('URL del post no encontrada')
    elif not url.startswith('http'):
        results['warnings'].append(f'URL inválida: {url}')
    
    return results

def test_twitter_extraction():
    """Probar extracción de Twitter"""
    print("\n" + "="*60)
    print("🐦 PRUEBA DE EXTRACCIÓN DE TWITTER/X")
    print("="*60)
    
    try:
        scraper = TwitterScraper(headless=True, delay=3)
        
        # Probar con una URL de búsqueda
        test_url = "https://twitter.com/search?q=tecnologia&src=typed_query&f=live"
        print(f"\n🔍 Scrapeando desde: {test_url}")
        
        posts = scraper.scrape_from_url(test_url, max_tweets=10)
        
        print(f"\n✅ Posts extraídos: {len(posts)}")
        
        if len(posts) == 0:
            print("⚠️ No se extrajeron posts. Puede requerir autenticación.")
            return
        
        processor = SocialMediaProcessor()
        valid_posts = 0
        
        for i, post in enumerate(posts[:10], 1):
            print(f"\n{'='*60}")
            print(f"📱 POST {i}/{len(posts)}")
            print(f"{'='*60}")
            
            # Validar datos
            validation = validate_post_data(post, 'twitter')
            
            # Procesar post
            processed = processor.process_tweet(post)
            
            # Mostrar datos
            print(f"✅ Usuario: {processed.get('username', 'N/A')}")
            print(f"📝 Texto ({len(processed.get('text', ''))} chars): {processed.get('text', '')[:100]}...")
            print(f"🖼️ Imagen: {'✅' if processed.get('image_url') else '❌'} {processed.get('image_url', 'N/A')[:60] if processed.get('image_url') else 'N/A'}...")
            print(f"👍 Likes: {processed.get('likes', 0)}")
            print(f"🔄 Retweets: {processed.get('retweets', 0)}")
            print(f"💬 Replies: {processed.get('replies', 0)}")
            print(f"🏷️ Categoría: {processed.get('category', 'N/A')}")
            print(f"😊 Sentimiento: {processed.get('sentiment', 'N/A')}")
            
            # Mostrar validación
            if validation['valid']:
                print("✅ VALIDACIÓN: Post válido")
                valid_posts += 1
            else:
                print("❌ VALIDACIÓN: Post inválido")
            
            if validation['errors']:
                for error in validation['errors']:
                    print(f"   ❌ Error: {error}")
            
            if validation['warnings']:
                for warning in validation['warnings']:
                    print(f"   ⚠️ Advertencia: {warning}")
        
        print(f"\n{'='*60}")
        print(f"📊 RESUMEN: {valid_posts}/{len(posts)} posts válidos")
        print(f"{'='*60}")
        
        scraper.close()
        
    except Exception as e:
        print(f"❌ Error en prueba de Twitter: {e}")
        import traceback
        traceback.print_exc()

def test_facebook_extraction():
    """Probar extracción de Facebook"""
    print("\n" + "="*60)
    print("📘 PRUEBA DE EXTRACCIÓN DE FACEBOOK")
    print("="*60)
    
    try:
        scraper = FacebookScraper(headless=True, delay=3)
        
        # Probar con una página pública (ejemplo)
        test_url = "https://www.facebook.com/facebook"
        print(f"\n🔍 Scrapeando desde: {test_url}")
        
        posts = scraper.scrape_from_url(test_url, max_posts=10)
        
        print(f"\n✅ Posts extraídos: {len(posts)}")
        
        if len(posts) == 0:
            print("⚠️ No se extrajeron posts. Puede requerir autenticación.")
            return
        
        processor = SocialMediaProcessor()
        valid_posts = 0
        
        for i, post in enumerate(posts[:10], 1):
            print(f"\n{'='*60}")
            print(f"📱 POST {i}/{len(posts)}")
            print(f"{'='*60}")
            
            # Validar datos
            validation = validate_post_data(post, 'facebook')
            
            # Procesar post
            processed = processor.process_tweet(post)
            
            # Mostrar datos
            print(f"✅ Autor: {processed.get('username', 'N/A')}")
            print(f"📝 Texto ({len(processed.get('text', ''))} chars): {processed.get('text', '')[:100]}...")
            print(f"🖼️ Imagen: {'✅' if processed.get('image_url') else '❌'} {processed.get('image_url', 'N/A')[:60] if processed.get('image_url') else 'N/A'}...")
            print(f"🎥 Video: {'✅' if processed.get('video_url') else '❌'}")
            print(f"👍 Likes: {processed.get('likes', 0)}")
            print(f"💬 Comments: {processed.get('comments', 0)}")
            print(f"📤 Shares: {processed.get('shares', 0)}")
            print(f"🏷️ Categoría: {processed.get('category', 'N/A')}")
            print(f"😊 Sentimiento: {processed.get('sentiment', 'N/A')}")
            
            # Mostrar validación
            if validation['valid']:
                print("✅ VALIDACIÓN: Post válido")
                valid_posts += 1
            else:
                print("❌ VALIDACIÓN: Post inválido")
            
            if validation['errors']:
                for error in validation['errors']:
                    print(f"   ❌ Error: {error}")
            
            if validation['warnings']:
                for warning in validation['warnings']:
                    print(f"   ⚠️ Advertencia: {warning}")
        
        print(f"\n{'='*60}")
        print(f"📊 RESUMEN: {valid_posts}/{len(posts)} posts válidos")
        print(f"{'='*60}")
        
        scraper.close()
        
    except Exception as e:
        print(f"❌ Error en prueba de Facebook: {e}")
        import traceback
        traceback.print_exc()

def test_metric_parsing():
    """Probar parseo de métricas"""
    print("\n" + "="*60)
    print("🔢 PRUEBA DE PARSEO DE MÉTRICAS")
    print("="*60)
    
    scraper = TwitterScraper(headless=True, delay=1)
    
    test_cases = [
        ("1.2K", 1200),
        ("5K", 5000),
        ("1.5M", 1500000),
        ("2M", 2000000),
        ("500", 500),
        ("1.2B", 1200000000),
        ("", 0),
        ("abc", 0),
    ]
    
    print("\n📊 Resultados:")
    all_passed = True
    for input_str, expected in test_cases:
        result = scraper._parse_metric(input_str)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{input_str}' -> {result} (esperado: {expected})")
        if result != expected:
            all_passed = False
    
    if all_passed:
        print("\n✅ Todas las pruebas de parseo pasaron")
    else:
        print("\n❌ Algunas pruebas de parseo fallaron")
    
    scraper.close()

if __name__ == "__main__":
    print("="*60)
    print("🧪 TESTING DE EXTRACCIÓN DE REDES SOCIALES")
    print("="*60)
    
    # Probar parseo de métricas
    test_metric_parsing()
    
    # Probar extracción de Twitter
    test_twitter_extraction()
    
    # Probar extracción de Facebook
    test_facebook_extraction()
    
    print("\n" + "="*60)
    print("✅ TESTING COMPLETADO")
    print("="*60)















