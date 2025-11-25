"""
Facebook Scraper con Login Manual
Implementación completa según especificaciones
"""

import time
import random
import re
import json
import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_chrome_driver() -> webdriver.Chrome:
    """
    Configura ChromeDriver con opciones anti-detección EXACTAS
    """
    logger.info("🔧 Configurando ChromeDriver con anti-detección...")
    
    chrome_options = Options()
    
    # User-Agent realista de Chrome 120+ en Windows
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')
    
    # Argumentos requeridos
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    
    # Desactivar automation
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Tamaño de ventana 1920x1080
    chrome_options.add_argument('--window-size=1920,1080')
    
    # NO usar modo headless (debe verse el navegador)
    # No agregar --headless
    
    # Preferencias adicionales
    prefs = {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.default_content_setting_values.notifications": 2
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    # Crear servicio
    service = Service(ChromeDriverManager().install())
    
    # Crear driver
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Ocultar navigator.webdriver con JavaScript
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    logger.info("✅ ChromeDriver configurado correctamente")
    return driver


def verificar_login(driver: webdriver.Chrome) -> bool:
    """
    Verifica que el login fue exitoso buscando elemento con selector [aria-label="Facebook"]
    """
    try:
        # Esperar a que cargue la página
        time.sleep(3)
        
        # Buscar elemento que indica login exitoso
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-label="Facebook"]'))
            )
            logger.info("✅ Login verificado: elemento [aria-label='Facebook'] encontrado")
            return True
        except:
            # Intentar otros selectores que indican login
            try:
                # Buscar barra de navegación (solo visible cuando estás logueado)
                nav = driver.find_element(By.CSS_SELECTOR, 'div[role="navigation"]')
                if nav:
                    logger.info("✅ Login verificado: barra de navegación encontrada")
                    return True
            except:
                pass
            
            # Verificar que NO haya pantalla de login
            try:
                login_input = driver.find_element(By.CSS_SELECTOR, 'input[name="email"]')
                if login_input:
                    logger.warning("⚠️ Aún se muestra pantalla de login")
                    return False
            except:
                pass
            
            # Si no hay indicadores de login, asumir que está logueado
            current_url = driver.current_url
            if 'facebook.com' in current_url and 'login' not in current_url.lower():
                logger.info("✅ Login verificado: URL no contiene 'login'")
                return True
            
            return False
    except Exception as e:
        logger.error(f"❌ Error verificando login: {e}")
        return False


def parse_metric_value(text: str) -> int:
    """
    Convierte '5.2K' a 5200, '1.5M' a 1500000
    """
    try:
        # Buscar números en el texto
        match = re.search(r'([\d,\.]+)\s*([KkMm]?)', text)
        if not match:
            return 0
        
        number = match.group(1).replace(',', '.')
        multiplier = match.group(2).upper()
        
        value = float(number)
        
        if multiplier == 'K':
            return int(value * 1000)
        elif multiplier == 'M':
            return int(value * 1000000)
        else:
            return int(value)
    except:
        return 0


def categorize_post(text: str) -> str:
    """
    Categoriza posts por palabras clave
    """
    text_lower = text.lower()
    
    categorias = {
        'tecnologia': ['tecnología', 'tech', 'digital', 'software', 'app', 'internet', 'ia', 'inteligencia artificial'],
        'negocios': ['negocio', 'empresa', 'comercio', 'mercado', 'economía', 'venta', 'precio', 'inversión'],
        'deportes': ['deporte', 'fútbol', 'campeonato', 'equipo', 'partido', 'liga', 'gol'],
        'politica': ['política', 'gobierno', 'elección', 'presidente', 'congreso', 'ley'],
        'entretenimiento': ['música', 'cine', 'película', 'artista', 'show', 'concierto', 'festival'],
        'salud': ['salud', 'médico', 'hospital', 'enfermedad', 'tratamiento', 'covid'],
        'educacion': ['educación', 'universidad', 'colegio', 'estudiante', 'profesor', 'curso']
    }
    
    for categoria, palabras in categorias.items():
        if any(palabra in text_lower for palabra in palabras):
            return categoria
    
    return 'noticias'


def es_comentario(article_element) -> bool:
    """
    Verifica si un elemento es un comentario en lugar de un post principal
    """
    try:
        # CRITERIOS PARA DETECTAR COMENTARIOS:
        
        # 1. Verificar si está dentro de una sección de comentarios
        parent_html = article_element.get_attribute('outerHTML') or ''
        if any(marker in parent_html.lower() for marker in [
            'comment', 'comentario', 'reply', 'respuesta',
            'commentlist', 'comment-list', 'ufi', 'ufi_'
        ]):
            return True
        
        # 2. Verificar si tiene estructura de comentario (no tiene botones principales)
        try:
            # Los posts principales tienen botones "Me gusta", "Comentar", "Compartir"
            has_main_buttons = (
                article_element.find_elements(By.XPATH, ".//span[contains(text(), 'Me gusta')]") or
                article_element.find_elements(By.XPATH, ".//span[contains(text(), 'Comentar')]") or
                article_element.find_elements(By.XPATH, ".//span[contains(text(), 'Compartir')]") or
                article_element.find_elements(By.XPATH, ".//span[contains(text(), 'Like')]") or
                article_element.find_elements(By.XPATH, ".//span[contains(text(), 'Comment')]") or
                article_element.find_elements(By.XPATH, ".//span[contains(text(), 'Share')]")
            )
            if not has_main_buttons:
                # Si no tiene botones principales, probablemente es un comentario
                # Verificar si tiene estructura de "Responder" que es típica de comentarios
                has_reply_button = (
                    article_element.find_elements(By.XPATH, ".//span[contains(text(), 'Responder')]") or
                    article_element.find_elements(By.XPATH, ".//span[contains(text(), 'Reply')]")
                )
                if has_reply_button:
                    return True
        except:
            pass
        
        # 3. Verificar si el texto es muy corto (comentarios suelen ser más cortos)
        try:
            text = article_element.text.strip()
            # Si el texto es muy corto y no tiene imagen, probablemente es comentario
            if len(text) < 30:
                has_image = article_element.find_elements(By.CSS_SELECTOR, "img[data-visualcompletion='media-vc-image']")
                if not has_image:
                    return True
        except:
            pass
        
        # 4. Verificar si está dentro de un contenedor de comentarios
        try:
            # Buscar si algún ancestro tiene atributos de comentario
            parent = article_element.find_element(By.XPATH, "./..")
            parent_class = parent.get_attribute('class') or ''
            if any(marker in parent_class.lower() for marker in ['comment', 'ufi', 'reply']):
                return True
        except:
            pass
        
        return False
    except:
        return False


def extraer_post(article_element, driver: webdriver.Chrome, page_name: str) -> Optional[Dict]:
    """
    Extrae datos de un post desde un WebElement (article)
    MEJORADO: Más selectores y umbrales más flexibles
    FILTRA COMENTARIOS: Solo extrae posts principales del feed (MENOS AGRESIVO)
    USA JAVASCRIPT: Extracción directa del DOM para mejor precisión
    """
    try:
        # FILTRAR COMENTARIOS: Verificar si es un comentario (PERO SER MENOS AGRESIVO)
        # Solo filtrar comentarios obvios, aceptar el resto
        try:
            if es_comentario(article_element):
                # Verificar una vez más que realmente sea comentario
                article_text = article_element.text[:100] if article_element.text else ""
                if len(article_text) > 50:  # Si tiene mucho texto, puede ser un post válido
                    logger.debug("⚠️ Marcado como comentario pero tiene mucho texto, aceptando de todos modos...")
                else:
                    logger.debug("⚠️ Elemento descartado: es un comentario, no un post principal")
                    return None
        except:
            # Si hay error verificando, aceptar el post de todos modos
            pass
        
        # USAR JAVASCRIPT PARA EXTRACCIÓN PRECISA
        try:
            # Obtener el ID único del elemento para usar en JavaScript
            element_id = article_element.get_attribute('id') or ''
            if not element_id:
                # Si no tiene ID, usar JavaScript para encontrarlo
                element_html = article_element.get_attribute('outerHTML')[:200]
            
            # Extraer usando JavaScript directamente del DOM
            js_result = driver.execute_script("""
                var article = arguments[0];
                var result = {
                    text: '',
                    image: null,
                    url: '',
                    likes: 0,
                    comments: 0,
                    shares: 0
                };
                
                // TEXTO - Múltiples métodos
                var textSelectors = [
                    '[data-ad-preview="message"]',
                    'div[data-testid="post_message"]',
                    'div[dir="auto"]',
                    'span[dir="auto"]'
                ];
                
                for (var i = 0; i < textSelectors.length; i++) {
                    var textElem = article.querySelector(textSelectors[i]);
                    if (textElem) {
                        var txt = textElem.textContent.trim();
                        if (txt.length > result.text.length && txt.length > 15) {
                            result.text = txt;
                        }
                    }
                }
                
                // Si no hay texto, buscar todos los divs y tomar el más largo
                if (!result.text || result.text.length < 15) {
                    var divs = article.querySelectorAll('div[dir="auto"], span[dir="auto"]');
                    var longestText = '';
                    for (var d = 0; d < divs.length; d++) {
                        var txt = divs[d].textContent.trim();
                        if (txt.length > longestText.length && txt.length > 15) {
                            longestText = txt;
                        }
                    }
                    if (longestText) result.text = longestText;
                }
                
                // IMAGEN - Múltiples métodos mejorados (MEJORADO PARA LAZY LOADING)
                // Método 1: data-visualcompletion (más específico) - MEJORADO
                var img1 = article.querySelector('img[data-visualcompletion="media-vc-image"]');
                if (img1) {
                    // Intentar src primero, luego data-src (lazy loading)
                    var src1 = img1.src || img1.getAttribute('src') || img1.getAttribute('data-src') || '';
                    // También intentar activar lazy loading haciendo scroll al elemento
                    if (!src1 || src1.includes('data:image')) {
                        try {
                            img1.scrollIntoView({behavior: 'smooth', block: 'center'});
                            // Esperar un momento para que cargue
                            setTimeout(function() {}, 100);
                            src1 = img1.src || img1.getAttribute('src') || img1.getAttribute('data-src') || '';
                        } catch(e) {}
                    }
                    if (src1 && (src1.includes('fbcdn.net') || src1.includes('scontent') || src1.includes('facebook.com')) && 
                        !src1.includes('profile') && !src1.includes('avatar') &&
                        !src1.includes('sticker') && !src1.includes('emoji') &&
                        !src1.includes('data:image')) {
                        result.image = src1;
                    }
                }
                
                // Método 2: Buscar todas las imágenes y filtrar - MEJORADO PARA LAZY LOADING
                if (!result.image) {
                    var imgs = article.querySelectorAll('img');
                    var bestImage = null;
                    var bestSize = 0;
                    
                    for (var imgIdx = 0; imgIdx < imgs.length; imgIdx++) {
                        var img = imgs[imgIdx];
                        // MEJORADO: Buscar en src, data-src, y activar lazy loading
                        var src = img.src || img.getAttribute('src') || img.getAttribute('data-src') || '';
                        
                        // Si no hay src válido, intentar activar lazy loading
                        if (!src || src.includes('data:image') || src.length < 10) {
                            try {
                                img.scrollIntoView({behavior: 'smooth', block: 'center'});
                                setTimeout(function() {}, 50);
                                src = img.src || img.getAttribute('src') || img.getAttribute('data-src') || '';
                            } catch(e) {}
                        }
                        
                        // Validar URL
                        if (src && src.length > 10 && (src.includes('fbcdn.net') || src.includes('scontent') || src.includes('facebook.com'))) {
                            // Filtrar imágenes de perfil/avatar/stickers
                            var isInvalid = (
                                src.includes('profile') || 
                                src.includes('avatar') || 
                                src.includes('sticker') || 
                                src.includes('emoji') ||
                                src.includes('sprite') ||
                                src.includes('icon') ||
                                src.includes('data:image')
                            );
                            
                            if (!isInvalid) {
                                // Obtener dimensiones
                                var w = parseInt(img.width) || parseInt(img.naturalWidth) || parseInt(img.getAttribute('width')) || 0;
                                var h = parseInt(img.height) || parseInt(img.naturalHeight) || parseInt(img.getAttribute('height')) || 0;
                                var size = w * h;
                                
                                // Preferir imágenes grandes (contenido real) - UMBRAL REDUCIDO
                                if (size > bestSize || (w > 150 || h > 150)) {  // Reducido de 200 a 150
                                    bestImage = src;
                                    bestSize = size;
                                    if (w > 300 || h > 300) {  // Reducido de 400 a 300
                                        result.image = src; // Imagen grande, usar directamente
                                        break;
                                    }
                                }
                            }
                        }
                    }
                    
                    if (!result.image && bestImage) {
                        result.image = bestImage;
                    }
                }
                
                // Método 3: Buscar en elementos específicos de Facebook
                if (!result.image) {
                    var imgSelectors = [
                        'img[src*="fbcdn.net"][src*="v/t39"]',
                        'img[src*="scontent"][src*="v/t39"]',
                        'img[data-imgperflogname="feedCoverPhoto"]',
                        'img[role="img"][src*="fbcdn"]',
                        'img[src*="/photos/"]',
                        'img[src*="/photo.php"]'
                    ];
                    
                    for (var selIdx = 0; selIdx < imgSelectors.length; selIdx++) {
                        try {
                            var img = article.querySelector(imgSelectors[selIdx]);
                            if (img && img.src) {
                                var src = img.src;
                                if (!src.includes('profile') && !src.includes('avatar') && 
                                    !src.includes('sticker') && !src.includes('emoji')) {
                                    result.image = src;
                                    break;
                                }
                            }
                        } catch(e) {
                            continue;
                        }
                    }
                }
                
                // URL DEL POST
                var links = article.querySelectorAll('a[href*="/posts/"], a[href*="/permalink/"], a[href*="/story.php"]');
                for (var l = 0; l < links.length; l++) {
                    var href = links[l].href || '';
                    if (href && (href.includes('/posts/') || href.includes('/permalink/') || href.includes('/story.php'))) {
                        result.url = href;
                        break;
                    }
                }
                
                // MÉTRICAS - Buscar en spans y texto
                var allText = article.textContent || '';
                
                // LIKES - Buscar patrones
                var likesMatch = allText.match(/(\\d+[KMB]?)\\s*(?:like|me gusta|gusta|reaccion)/i);
                if (!likesMatch) {
                    likesMatch = allText.match(/(\\d+[KMB]?)\\s*👍/);
                }
                if (!likesMatch) {
                    likesMatch = allText.match(/(\\d+[KMB]?)\\s*❤️/);
                }
                if (likesMatch) {
                    var numStr = likesMatch[1];
                    var num = numStr.replace(/K/g, '000').replace(/M/g, '000000').replace(/B/g, '000000000');
                    result.likes = parseInt(num) || 0;
                }
                
                // COMMENTS - Buscar patrones
                var commentsMatch = allText.match(/(\\d+[KMB]?)\\s*(?:comment|comentario|comentar)/i);
                if (!commentsMatch) {
                    commentsMatch = allText.match(/(\\d+[KMB]?)\\s*💬/);
                }
                if (commentsMatch) {
                    var numStr = commentsMatch[1];
                    var num = numStr.replace(/K/g, '000').replace(/M/g, '000000');
                    result.comments = parseInt(num) || 0;
                }
                
                // SHARES - Buscar patrones
                var sharesMatch = allText.match(/(\\d+[KMB]?)\\s*(?:share|compartir|comparte)/i);
                if (!sharesMatch) {
                    sharesMatch = allText.match(/(\\d+[KMB]?)\\s*📤/);
                }
                if (sharesMatch) {
                    var numStr = sharesMatch[1];
                    var num = numStr.replace(/K/g, '000').replace(/M/g, '000000');
                    result.shares = parseInt(num) || 0;
                }
                
                // Buscar en aria-labels
                var ariaElems = article.querySelectorAll('[aria-label]');
                for (var a = 0; a < ariaElems.length; a++) {
                    var aria = (ariaElems[a].getAttribute('aria-label') || '').toLowerCase();
                    var ariaNum = aria.match(/(\\d+[KMB]?)/);
                    if (ariaNum) {
                        var numStr = ariaNum[1];
                        var num = numStr.replace(/K/g, '000').replace(/M/g, '000000');
                        var val = parseInt(num) || 0;
                        if ((aria.includes('like') || aria.includes('gusta')) && val > result.likes) {
                            result.likes = val;
                        }
                        if ((aria.includes('comment') || aria.includes('comentario')) && val > result.comments) {
                            result.comments = val;
                        }
                        if ((aria.includes('share') || aria.includes('compartir')) && val > result.shares) {
                            result.shares = val;
                        }
                    }
                }
                
                return result;
            """, article_element)
            
            if js_result and js_result.get('text') and len(js_result.get('text', '').strip()) > 10:
                # Usar datos de JavaScript
                content = js_result.get('text', '').strip()
                image_url = js_result.get('image')
                post_url = js_result.get('url', '')
                metrics = {
                    'likes': js_result.get('likes', 0),
                    'comments': js_result.get('comments', 0),
                    'shares': js_result.get('shares', 0),
                    'retweets': 0
                }
                
                # Si no hay imagen en JS, intentar con Selenium como fallback
                if not image_url:
                    logger.debug(f"⚠️ JS no encontró imagen, intentando con Selenium...")
                    try:
                        # Buscar imagen con Selenium
                        img_elements = article_element.find_elements(By.TAG_NAME, "img")
                        for img in img_elements:
                            src = img.get_attribute('src') or img.get_attribute('data-src') or ''
                            if src and ('fbcdn.net' in src or 'scontent' in src):
                                if not any(x in src.lower() for x in ['profile', 'avatar', 'sticker', 'emoji', 'icon']):
                                    image_url = src
                                    logger.debug(f"✅ Imagen encontrada con Selenium fallback: {src[:50]}...")
                                    break
                    except:
                        pass
                
                logger.info(f"✅ Post extraído con JS: texto={len(content)} chars, imagen={'✅' if image_url else '❌'}, likes={metrics['likes']}, comments={metrics['comments']}")
                
                return {
                    'id': f"fb_{int(time.time() * 1000)}_{random.randint(1000, 9999)}",
                    'platform': 'facebook',
                    'author': page_name,
                    'content': content,
                    'image_url': image_url,
                    'url': post_url,
                    'created_at': datetime.now().isoformat(),
                    'metrics': metrics,
                    'category': categorize_post(content),
                    'sentiment': 'neutral'
                }
        except Exception as js_error:
            logger.debug(f"⚠️ Error en extracción JS, usando método Selenium: {js_error}")
        
        # FALLBACK: Método Selenium tradicional
        # TEXTO - MÚLTIPLES MÉTODOS
        content = ""
        
        try:
            # Buscar "Ver más" y expandir
            ver_mas = article_element.find_element(By.XPATH, ".//div[@role='button' and contains(text(), 'Ver más')]")
            driver.execute_script("arguments[0].click();", ver_mas)
            time.sleep(0.5)
        except:
            pass
        
        # MÉTODO 1: div[dir="auto"] (más común)
        text_divs = article_element.find_elements(By.XPATH, ".//div[@dir='auto']")
        for div in text_divs:
            texto = div.text.strip()
            if len(texto) > 10:  # REDUCIDO de 20 a 10
                content += texto + " "
        
        # MÉTODO 2: span[dir="auto"] (si no hay div)
        if len(content.strip()) < 10:
            text_spans = article_element.find_elements(By.XPATH, ".//span[@dir='auto']")
            for span in text_spans:
                texto = span.text.strip()
                if len(texto) > 10:
                    content += texto + " "
        
        # MÉTODO 3: data-ad-preview="message"
        if len(content.strip()) < 10:
            try:
                msg_elem = article_element.find_element(By.CSS_SELECTOR, '[data-ad-preview="message"]')
                texto = msg_elem.text.strip()
                if len(texto) > 10:
                    content = texto  # Usar este texto directamente
            except:
                pass
        
        # MÉTODO 4: data-testid="post_message"
        if len(content.strip()) < 10:
            try:
                msg_elem = article_element.find_element(By.CSS_SELECTOR, '[data-testid="post_message"]')
                texto = msg_elem.text.strip()
                if len(texto) > 10:
                    content = texto
            except:
                pass
        
        # MÉTODO 5: Todo el texto del article (último recurso)
        if len(content.strip()) < 10:
            try:
                full_text = article_element.text.strip()
                # Filtrar líneas muy cortas o que parecen botones
                lines = [line.strip() for line in full_text.split('\n') if len(line.strip()) > 10]
                if lines:
                    content = ' '.join(lines[:5])  # Tomar las primeras 5 líneas
            except:
                pass
        
        content = content.strip()
        
        # ACEPTAR posts con al menos 5 caracteres O con imagen (MUY PERMISIVO)
        if not content or len(content.strip()) < 5:
            # Si tiene imagen, aceptar aunque el texto sea corto
            try:
                img = article_element.find_element(By.CSS_SELECTOR, "img[data-visualcompletion='media-vc-image']")
                if img:
                    # Si tiene imagen, usar texto mínimo o placeholder
                    if not content or len(content.strip()) < 3:
                        content = "Post con imagen"  # Placeholder mínimo
                    logger.debug(f"✅ Post con imagen encontrado, texto: {content[:30]}...")
            except:
                # Intentar buscar cualquier imagen
                try:
                    imgs = article_element.find_elements(By.TAG_NAME, "img")
                    for img in imgs:
                        src = img.get_attribute('src') or ''
                        if src and ('fbcdn.net' in src or 'scontent' in src):
                            if not any(x in src.lower() for x in ['profile', 'avatar', 'sticker', 'emoji']):
                                if not content or len(content.strip()) < 3:
                                    content = "Post con imagen"
                                logger.debug(f"✅ Post con imagen alternativa encontrado")
                                break
                except:
                    pass
                
                # Si después de todo no hay contenido ni imagen, usar texto mínimo del article
                if not content or len(content.strip()) < 3:
                    try:
                        # Intentar obtener cualquier texto del article
                        full_text = article_element.text.strip()
                        if len(full_text) > 3:
                            # Tomar las primeras líneas significativas
                            lines = [line.strip() for line in full_text.split('\n') if len(line.strip()) > 3]
                            if lines:
                                content = ' '.join(lines[:3])  # Primeras 3 líneas
                                logger.debug(f"✅ Usando texto mínimo del article: {content[:50]}...")
                            else:
                                logger.debug(f"⚠️ Post rechazado: sin contenido suficiente")
                                return None
                        else:
                            logger.debug(f"⚠️ Post rechazado: sin contenido suficiente")
                            return None
                    except:
                        logger.debug(f"⚠️ Post rechazado: sin contenido suficiente")
                        return None
        
        # IMAGEN - MÚLTIPLES MÉTODOS MEJORADOS
        image_url = None
        try:
            # MÉTODO 1: data-visualcompletion='media-vc-image' (más específico) - MEJORADO PARA LAZY LOADING
            try:
                img = article_element.find_element(By.CSS_SELECTOR, "img[data-visualcompletion='media-vc-image']")
                # MEJORADO: Buscar en src, data-src, y activar lazy loading
                image_url = img.get_attribute('src') or img.get_attribute('data-src') or ''
                
                # Si no hay src válido o es data:image, intentar activar lazy loading
                if not image_url or image_url.startswith('data:image') or len(image_url) < 10:
                    try:
                        # Hacer scroll al elemento para activar lazy loading
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", img)
                        time.sleep(0.5)  # Esperar a que cargue
                        image_url = img.get_attribute('src') or img.get_attribute('data-src') or ''
                    except:
                        pass
                
                if image_url and len(image_url) > 10 and ('fbcdn.net' in image_url or 'scontent' in image_url or 'facebook.com' in image_url):
                    if not any(x in image_url.lower() for x in ['profile', 'avatar', 'sticker', 'emoji', 'icon']) and not image_url.startswith('data:image'):
                        logger.info(f"✅ Imagen encontrada (método 1): {image_url[:50]}...")
            except:
                pass
            
            # MÉTODO 1.5: Buscar todas las imágenes con data-visualcompletion
            if not image_url:
                try:
                    imgs = article_element.find_elements(By.CSS_SELECTOR, "img[data-visualcompletion]")
                    for img in imgs:
                        src = img.get_attribute('src') or img.get_attribute('data-src') or ''
                        if src and ('fbcdn.net' in src or 'scontent' in src):
                            if not any(x in src.lower() for x in ['profile', 'avatar', 'sticker', 'emoji', 'icon']):
                                image_url = src
                                logger.info(f"✅ Imagen encontrada (método 1.5): {src[:50]}...")
                                break
                except:
                    pass
            
            # MÉTODO 2: Imágenes grandes (no thumbnails) - MEJORADO PARA LAZY LOADING
            if not image_url:
                try:
                    imgs = article_element.find_elements(By.TAG_NAME, "img")
                    best_image = None
                    best_size = 0
                    
                    for img in imgs:
                        # MEJORADO: Buscar en src, data-src, y activar lazy loading
                        src = img.get_attribute('src') or img.get_attribute('data-src') or ''
                        
                        # Si no hay src válido, intentar activar lazy loading
                        if not src or src.startswith('data:image') or len(src) < 10:
                            try:
                                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", img)
                                time.sleep(0.3)  # Esperar a que cargue
                                src = img.get_attribute('src') or img.get_attribute('data-src') or ''
                            except:
                                continue
                        
                        if not src or len(src) < 10:
                            continue
                            
                        width = img.get_attribute('width') or img.get_attribute('naturalWidth') or '0'
                        height = img.get_attribute('height') or img.get_attribute('naturalHeight') or '0'
                        
                        # Validar que sea imagen de contenido (no perfil)
                        if (('fbcdn.net' in src or 'scontent' in src or 'facebook.com' in src) and
                            not any(x in src.lower() for x in ['profile', 'avatar', 'sticker', 'emoji', 'icon', 'sprite']) and
                            not src.startswith('data:image')):
                            # Preferir imágenes grandes (probablemente contenido) - UMBRAL REDUCIDO
                            try:
                                w = int(width) if str(width).isdigit() else 0
                                h = int(height) if str(height).isdigit() else 0
                                size = w * h
                                
                                if size > best_size or (w > 150 or h > 150):  # Reducido de 200 a 150
                                    best_image = src
                                    best_size = size
                                    if w > 300 or h > 300:  # Reducido de 400 a 300
                                        image_url = src
                                        logger.info(f"✅ Imagen encontrada (método 2, muy grande {w}x{h}): {src[:50]}...")
                                        break
                            except:
                                # Si no hay dimensiones, usar la primera imagen válida
                                if not best_image:
                                    best_image = src
                    
                    if not image_url and best_image:
                        image_url = best_image
                        logger.info(f"✅ Imagen encontrada (método 2, mejor opción): {best_image[:50]}...")
                except Exception as e:
                    logger.debug(f"⚠️ Error en método 2 de imágenes: {e}")
                    pass
            
            # MÉTODO 3: Buscar en elementos de imagen específicos de Facebook - MEJORADO
            if not image_url:
                try:
                    img_selectors = [
                        "img[src*='fbcdn.net'][src*='v/t39']",  # Imágenes de contenido
                        "img[src*='scontent'][src*='v/t39']",
                        "img[data-imgperflogname='feedCoverPhoto']",
                        "img[role='img'][src*='fbcdn']",
                        "img[src*='/photos/']",
                        "img[src*='/photo.php']",
                        "img[src*='fbcdn'][src*='.jpg']",
                        "img[src*='fbcdn'][src*='.png']",
                        "img[src*='scontent'][src*='.jpg']",
                        "img[src*='scontent'][src*='.png']"
                    ]
                    for selector in img_selectors:
                        try:
                            imgs = article_element.find_elements(By.CSS_SELECTOR, selector)
                            for img in imgs:
                                src = img.get_attribute('src') or img.get_attribute('data-src') or ''
                                if src and not any(x in src.lower() for x in ['profile', 'avatar', 'sticker', 'emoji', 'icon']):
                                    image_url = src
                                    logger.info(f"✅ Imagen encontrada (método 3, {selector}): {src[:50]}...")
                                    break
                            if image_url:
                                break
                        except:
                            continue
                except Exception as e:
                    logger.debug(f"⚠️ Error en método 3 de imágenes: {e}")
                    pass
            
            # MÉTODO 4: JavaScript directo como último recurso - MEJORADO PARA LAZY LOADING
            if not image_url:
                try:
                    js_img = driver.execute_script("""
                        var article = arguments[0];
                        var imgs = article.querySelectorAll('img');
                        for (var i = 0; i < imgs.length; i++) {
                            var img = imgs[i];
                            // MEJORADO: Buscar en src, data-src, y activar lazy loading
                            var src = img.src || img.getAttribute('src') || img.getAttribute('data-src') || '';
                            
                            // Si no hay src válido, intentar activar lazy loading
                            if (!src || src.includes('data:image') || src.length < 10) {
                                try {
                                    img.scrollIntoView({behavior: 'smooth', block: 'center'});
                                    // Esperar un momento
                                    setTimeout(function() {}, 100);
                                    src = img.src || img.getAttribute('src') || img.getAttribute('data-src') || '';
                                } catch(e) {}
                            }
                            
                            if (src && src.length > 10 && (src.includes('fbcdn.net') || src.includes('scontent'))) {
                                if (!src.includes('profile') && !src.includes('avatar') && 
                                    !src.includes('sticker') && !src.includes('emoji') &&
                                    !src.includes('icon') && !src.includes('sprite') &&
                                    !src.includes('data:image')) {
                                    var w = parseInt(img.width) || parseInt(img.naturalWidth) || 0;
                                    var h = parseInt(img.height) || parseInt(img.naturalHeight) || 0;
                                    // UMBRAL REDUCIDO: Aceptar imágenes más pequeñas
                                    if (w > 150 || h > 150 || src.includes('/photos/') || src.includes('/photo.php')) {
                                        return src;
                                    }
                                }
                            }
                        }
                        return null;
                    """, article_element)
                    if js_img:
                        image_url = js_img
                        logger.info(f"✅ Imagen encontrada (método 4, JavaScript): {js_img[:50]}...")
                except:
                    pass
                    
        except Exception as e:
            logger.debug(f"⚠️ Error extrayendo imagen: {e}")
        
        if not image_url:
            logger.debug(f"⚠️ No se encontró imagen para este post")
        
        # MÉTRICAS - MÚLTIPLES MÉTODOS MEJORADOS
        metrics = {'likes': 0, 'comments': 0, 'shares': 0, 'retweets': 0}
        
        try:
            # Obtener todo el texto del article para análisis
            all_text = article_element.text
            
            # MÉTODO 1: Buscar métricas en spans específicos
            spans = article_element.find_elements(By.TAG_NAME, "span")
            for span in spans:
                texto = span.text.strip()
                texto_lower = texto.lower()
                
                # LIKES
                if any(word in texto_lower for word in ['like', 'reaccion', 'me gusta', 'gusta']):
                    valor = parse_metric_value(texto)
                    if valor > metrics['likes']:
                        metrics['likes'] = valor
                
                # COMMENTS
                elif any(word in texto_lower for word in ['comment', 'comentario', 'comentar']):
                    valor = parse_metric_value(texto)
                    if valor > metrics['comments']:
                        metrics['comments'] = valor
                
                # SHARES
                elif any(word in texto_lower for word in ['share', 'compartir', 'comparte']):
                    valor = parse_metric_value(texto)
                    if valor > metrics['shares']:
                        metrics['shares'] = valor
            
            # MÉTODO 2: Buscar con patrones regex en todo el texto
            if metrics['likes'] == 0:
                likes_patterns = [
                    r'(\d+[KMB]?)\s*(?:like|me gusta|gusta|reaccion)',
                    r'(\d+[KMB]?)\s*👍',
                    r'(\d+[KMB]?)\s*❤️',
                ]
                for pattern in likes_patterns:
                    match = re.search(pattern, all_text.lower())
                    if match:
                        metrics['likes'] = parse_metric_value(match.group(1))
                        break
            
            if metrics['comments'] == 0:
                comments_patterns = [
                    r'(\d+[KMB]?)\s*(?:comment|comentario|comentar)',
                    r'(\d+[KMB]?)\s*💬',
                    r'(\d+[KMB]?)\s*comentario',
                ]
                for pattern in comments_patterns:
                    match = re.search(pattern, all_text.lower())
                    if match:
                        metrics['comments'] = parse_metric_value(match.group(1))
                        break
            
            if metrics['shares'] == 0:
                shares_patterns = [
                    r'(\d+[KMB]?)\s*(?:share|compartir|comparte)',
                    r'(\d+[KMB]?)\s*📤',
                ]
                for pattern in shares_patterns:
                    match = re.search(pattern, all_text.lower())
                    if match:
                        metrics['shares'] = parse_metric_value(match.group(1))
                        break
            
            # MÉTODO 3: Buscar en elementos con aria-label
            try:
                aria_elements = article_element.find_elements(By.CSS_SELECTOR, '[aria-label]')
                for elem in aria_elements:
                    aria_label = elem.get_attribute('aria-label') or ''
                    aria_lower = aria_label.lower()
                    
                    # LIKES
                    if 'like' in aria_lower or 'gusta' in aria_lower or 'reaccion' in aria_lower:
                        valor = parse_metric_value(aria_label)
                        if valor > metrics['likes']:
                            metrics['likes'] = valor
                    
                    # COMMENTS
                    elif 'comment' in aria_lower or 'comentario' in aria_lower:
                        valor = parse_metric_value(aria_label)
                        if valor > metrics['comments']:
                            metrics['comments'] = valor
                    
                    # SHARES
                    elif 'share' in aria_lower or 'compartir' in aria_lower:
                        valor = parse_metric_value(aria_label)
                        if valor > metrics['shares']:
                            metrics['shares'] = valor
            except:
                pass
            
            logger.debug(f"📊 Métricas extraídas: Likes={metrics['likes']}, Comments={metrics['comments']}, Shares={metrics['shares']}")
            
        except Exception as e:
            logger.debug(f"⚠️ Error extrayendo métricas: {e}")
        
        # URL DEL POST - MÚLTIPLES MÉTODOS
        post_url = ""
        try:
            # MÉTODO 1: Buscar enlaces con /posts/ o /permalink/
            try:
                links = article_element.find_elements(By.XPATH, ".//a[contains(@href, '/posts/') or contains(@href, '/permalink/')]")
                for link in links:
                    href = link.get_attribute('href') or ''
                    if href and ('/posts/' in href or '/permalink/' in href):
                        post_url = href
                        if not post_url.startswith('http'):
                            post_url = f"https://www.facebook.com{post_url}"
                        logger.debug(f"✅ URL encontrada (método 1): {post_url[:50]}...")
                        break
            except:
                pass
            
            # MÉTODO 2: Buscar enlaces con timestamp o ID de post
            if not post_url:
                try:
                    links = article_element.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        href = link.get_attribute('href') or ''
                        # URLs de posts de Facebook tienen estructura específica
                        if (href and ('facebook.com' in href) and 
                            ('/posts/' in href or '/permalink/' in href or 
                             '/story.php' in href or '/photo.php' in href)):
                            post_url = href
                            logger.debug(f"✅ URL encontrada (método 2): {post_url[:50]}...")
                            break
                except:
                    pass
            
            # MÉTODO 3: Construir URL desde data-utime o ID del post
            if not post_url:
                try:
                    # Buscar atributos que contengan IDs de posts
                    post_id_attrs = article_element.find_elements(By.XPATH, ".//*[@data-utime or @data-post-id or @id]")
                    for elem in post_id_attrs:
                        post_id = (elem.get_attribute('data-utime') or 
                                  elem.get_attribute('data-post-id') or 
                                  elem.get_attribute('id') or '')
                        if post_id and post_id.isdigit():
                            # Intentar construir URL (puede no ser exacta, pero es mejor que nada)
                            post_url = f"https://www.facebook.com/{page_name}/posts/{post_id}"
                            logger.debug(f"✅ URL construida (método 3): {post_url[:50]}...")
                            break
                except:
                    pass
        except Exception as e:
            logger.debug(f"⚠️ Error extrayendo URL: {e}")
        
        return {
            'id': f"fb_{int(time.time() * 1000)}_{random.randint(1000, 9999)}",
            'platform': 'facebook',
            'author': page_name,
            'content': content,
            'image_url': image_url,
            'url': post_url,
            'created_at': datetime.now().isoformat(),
            'metrics': metrics,
            'category': categorize_post(content),
            'sentiment': 'neutral'
        }
    
    except Exception as e:
        logger.error(f"❌ Error extrayendo post: {e}")
        return None


def extraer_posts(driver: webdriver.Chrome, max_posts: int, page_name: str = "Página de Facebook", progress_callback=None) -> List[Dict]:
    """
    Extrae posts usando el algoritmo EXACTO especificado
    """
    posts_extraidos = []
    posts_ids_vistos = set()
    scrolls_sin_nuevos_posts = 0
    max_scrolls_sin_cambios = 3  # REDUCIDO: 3 (antes 5) para terminar más rápido cuando no hay contenido
    
    logger.info(f"📥 Iniciando extracción de hasta {max_posts} posts...")
    logger.info(f"📊 Posts actuales: {len(posts_extraidos)}/{max_posts}")
    
    iteration = 0
    max_iterations = 200  # AUMENTADO: Muchas más iteraciones para extraer más posts
    
    while len(posts_extraidos) < max_posts and iteration < max_iterations:
        iteration += 1
        logger.info(f"\n{'='*60}")
        logger.info(f"🔄 ITERACIÓN {iteration} - Posts actuales: {len(posts_extraidos)}/{max_posts}")
        logger.info(f"{'='*60}")
        
        try:
            # Esperar un momento antes de buscar posts (para que carguen)
            time.sleep(1.0)  # REDUCIDO: 1.0 segundo (antes 1.5) para ser más rápido
            
            # 1. Buscar todos los articles visibles - MÚLTIPLES SELECTORES
            articles = []
            
            # Selector principal - FILTRAR solo del feed principal (no comentarios)
            all_articles = driver.find_elements(By.CSS_SELECTOR, 'div[role="article"]')
            
            # FILTRAR COMENTARIOS: Solo posts del feed principal
            articles = []
            for article in all_articles:
                try:
                    # Verificar que NO sea un comentario
                    if not es_comentario(article):
                        # Verificar que tenga estructura de post principal (botones de interacción)
                        has_interaction = (
                            article.find_elements(By.XPATH, ".//span[contains(text(), 'Me gusta')]") or
                            article.find_elements(By.XPATH, ".//span[contains(text(), 'Comentar')]") or
                            article.find_elements(By.XPATH, ".//span[contains(text(), 'Compartir')]") or
                            article.find_elements(By.XPATH, ".//span[contains(text(), 'Like')]") or
                            article.find_elements(By.XPATH, ".//span[contains(text(), 'Comment')]") or
                            article.find_elements(By.XPATH, ".//span[contains(text(), 'Share')]") or
                            article.find_elements(By.CSS_SELECTOR, '[data-pagelet*="FeedUnit"]')  # Posts del feed
                        )
                        if has_interaction:
                            articles.append(article)
                except:
                    continue
            
            logger.info(f"📊 Selector 1 (div[role='article']): {len(all_articles)} total, {len(articles)} posts principales (filtrados comentarios)")
            
            if not articles or len(articles) < 3:
                # Selector alternativo 1 - FeedUnit es específico del feed principal
                all_articles2 = driver.find_elements(By.CSS_SELECTOR, 'div[data-pagelet*="FeedUnit"]')
                # Filtrar comentarios
                articles2 = []
                for article in all_articles2:
                    if not es_comentario(article):
                        articles2.append(article)
                if articles2:
                    articles = articles2
                    logger.info(f"📊 Selector 2 (data-pagelet*='FeedUnit'): {len(all_articles2)} total, {len(articles2)} posts principales")
            
            if not articles or len(articles) < 3:
                # Selector alternativo 2 - Filtrar comentarios
                all_articles3 = driver.find_elements(By.CSS_SELECTOR, 'div[data-ad-preview="message"]')
                articles3 = []
                for article in all_articles3:
                    if not es_comentario(article):
                        articles3.append(article)
                if articles3:
                    articles = articles3
                    logger.info(f"📊 Selector 3 (data-ad-preview='message'): {len(all_articles3)} total, {len(articles3)} posts principales")
            
            if not articles or len(articles) < 3:
                # Selector alternativo 3 - por clase común de Facebook
                articles4 = driver.find_elements(By.CSS_SELECTOR, 'div[class*="x1y1aw1k"], div[class*="x1n2onr6"]')
                if articles4:
                    articles = articles4
                    logger.info(f"📊 Selector 4 (clases comunes): {len(articles4)} articles")
            
                    # Intentar también con JavaScript para encontrar más posts (FILTRANDO comentarios)
                    if not articles or len(articles) < 5:
                        try:
                            js_articles = driver.execute_script("""
                                var allArticles = document.querySelectorAll('div[role="article"]');
                                var mainPosts = [];
                                for (var i = 0; i < allArticles.length; i++) {
                                    var article = allArticles[i];
                                    var html = article.outerHTML || '';
                                    var text = article.textContent || '';
                                    
                                    // Filtrar comentarios
                                    var isComment = false;
                                    
                                    // Verificar si está en sección de comentarios
                                    if (html.toLowerCase().includes('comment') || 
                                        html.toLowerCase().includes('comentario') ||
                                        html.toLowerCase().includes('reply') ||
                                        html.toLowerCase().includes('ufi_')) {
                                        isComment = true;
                                    }
                                    
                                    // Verificar si tiene botones principales de post
                                    var hasMainButtons = (
                                        text.includes('Me gusta') || text.includes('Comentar') || 
                                        text.includes('Compartir') || text.includes('Like') ||
                                        text.includes('Comment') || text.includes('Share')
                                    );
                                    
                                    // Verificar si tiene estructura de feed principal
                                    var hasFeedUnit = article.closest('[data-pagelet*="FeedUnit"]') !== null;
                                    
                                    // Solo incluir si es post principal (no comentario)
                                    if (!isComment && (hasMainButtons || hasFeedUnit)) {
                                        mainPosts.push(article);
                                    }
                                }
                                return mainPosts.length;
                            """)
                            logger.info(f"📊 JavaScript encuentra: {js_articles} posts principales (filtrados comentarios)")
                            
                            if js_articles > len(articles):
                                # Re-búsqueda con filtrado
                                all_articles_js = driver.find_elements(By.CSS_SELECTOR, 'div[role="article"]')
                                articles = []
                                for article in all_articles_js:
                                    if not es_comentario(article):
                                        articles.append(article)
                                logger.info(f"📊 Re-búsqueda después de JS: {len(articles)} posts principales")
                        except:
                            pass
            
            logger.info(f"📊 ✅ TOTAL: {len(articles)} articles encontrados para procesar")
            
            if len(articles) == 0:
                logger.warning("⚠️ ⚠️ ⚠️ NO SE ENCONTRARON ARTICLES - Haciendo scroll y esperando...")
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(5)
                continue
            
            # 2. Extraer datos de cada article
            nuevos_posts_en_esta_iteracion = 0
            logger.info(f"🔍 Procesando {len(articles)} articles...")
            
            for idx, article in enumerate(articles):
                try:
                    # ID ÚNICO basado en contenido del post (más estable y menos restrictivo)
                    try:
                        # Intentar extraer texto único del post (más texto para mejor hash)
                        article_text = article.text[:500] if article.text else ""
                        article_html = article.get_attribute('innerHTML')[:200] if article.get_attribute('innerHTML') else ""
                        
                        # Generar hash del contenido para ID único
                        content_hash = hashlib.md5((article_text + article_html + str(idx)).encode('utf-8')).hexdigest()[:16]
                        
                        # También intentar obtener ID de Facebook si existe
                        fb_id = None
                        try:
                            fb_id = article.get_attribute('data-pagelet') or article.get_attribute('data-ft') or article.get_attribute('id')
                        except:
                            pass
                        
                        # Usar ID de Facebook si está disponible, sino usar hash + idx
                        if fb_id and len(fb_id) > 5:
                            post_id = f"fb_{fb_id}_{content_hash}"
                        else:
                            post_id = f"fb_{content_hash}_{idx}_{iteration}"  # Agregar iteration para más unicidad
                    except Exception as e:
                        logger.debug(f"⚠️ Error generando ID: {e}")
                        # Fallback: usar timestamp + índice + iteración
                        post_id = f"post_{int(time.time() * 1000)}_{idx}_{iteration}_{random.randint(1000, 9999)}"
                    
                    # Verificar si ya procesamos este post (SOLO si tenemos MUCHOS posts vistos)
                    if len(posts_ids_vistos) > 50 and post_id in posts_ids_vistos:
                        logger.debug(f"⚠️ Article {idx+1} ya procesado (ID: {post_id[:20]}...), saltando...")
                        continue  # Ya procesado
                    
                    posts_ids_vistos.add(post_id)
                    logger.info(f"📋 ✅ Nuevo post detectado (ID: {post_id[:30]}...) - Total vistos: {len(posts_ids_vistos)}")
                    
                    logger.debug(f"🔍 Procesando article {idx+1}/{len(articles)}...")
                    
                    # Extraer datos del post
                    post_data = extraer_post(article, driver, page_name)
                    
                    # VALIDAR que el post tenga contenido (MUY PERMISIVO - mínimo 5 caracteres)
                    if post_data and post_data.get('content') and len(post_data.get('content', '').strip()) >= 5:
                        # Verificar duplicados SOLO si tenemos MUCHOS posts (evitar filtrado agresivo)
                        if len(posts_extraidos) > 30:  # Solo verificar duplicados después de 30 posts
                            content_text = post_data.get('content', '').strip()
                            content_hash = hashlib.md5(content_text.encode('utf-8')).hexdigest()[:16]
                            
                            # Verificar contra posts ya extraídos (solo últimos 50 posts)
                            existing_hashes = []
                            for p in posts_extraidos[-50:]:  # Solo verificar últimos 50 posts
                                existing_content = p.get('content', '').strip() or p.get('text', '').strip()
                                if existing_content and len(existing_content) > 30:  # Solo comparar textos muy largos
                                    existing_hashes.append(hashlib.md5(existing_content.encode('utf-8')).hexdigest()[:16])
                            
                            if content_hash in existing_hashes:
                                logger.debug(f"⚠️ Post duplicado detectado (hash: {content_hash}), saltando...")
                                continue
                        
                        # AÑADIR POST (sin filtros agresivos)
                        posts_extraidos.append(post_data)
                        nuevos_posts_en_esta_iteracion += 1
                        
                        # Log detallado de todos los campos
                        image_status = "✅ CON IMAGEN" if post_data.get('image_url') else "❌ SIN IMAGEN"
                        metrics_status = f"Likes:{post_data.get('metrics', {}).get('likes', 0)} Comments:{post_data.get('metrics', {}).get('comments', 0)} Shares:{post_data.get('metrics', {}).get('shares', 0)}"
                        url_status = "✅ CON URL" if post_data.get('url') else "❌ SIN URL"
                        
                        logger.info(f"✅ ✅ ✅ Post {len(posts_extraidos)} EXTRAÍDO:")
                        logger.info(f"   📝 Texto: {post_data['content'][:60]}...")
                        logger.info(f"   📸 {image_status}")
                        logger.info(f"   📊 {metrics_status}")
                        logger.info(f"   🔗 {url_status}")
                        
                        if len(posts_extraidos) >= max_posts:
                            logger.info(f"✅ ✅ ✅ LÍMITE ALCANZADO: {max_posts} posts extraídos")
                            break
                    else:
                        # Log para debug si no se extrajo
                        try:
                            preview_text = article.text[:100] if article.text else "sin texto"
                            logger.debug(f"⚠️ Article {idx+1} no extraído - Preview: {preview_text[:50]}...")
                        except:
                            logger.debug(f"⚠️ Article {idx+1} no extraído (error al obtener preview)")
                except Exception as e:
                    logger.warning(f"⚠️ Error procesando article {idx+1}: {e}")
                    import traceback
                    logger.debug(f"Traceback: {traceback.format_exc()}")
                    continue
            
            logger.info(f"📊 Iteración {iteration}: {nuevos_posts_en_esta_iteracion} nuevos posts extraídos (Total: {len(posts_extraidos)})")
            
            # Callback de progreso si está disponible (para retornar posts parciales)
            if progress_callback and callable(progress_callback):
                try:
                    progress_callback(posts_extraidos.copy())
                except:
                    pass
            
            # 3. Verificar si hay nuevos posts usando scroll inteligente
            # Detectar si hay más contenido disponible
            last_height = driver.execute_script("return document.body.scrollHeight")
            nuevos_articles = len(driver.find_elements(By.CSS_SELECTOR, 'div[role="article"]'))
            logger.info(f"📊 Articles después de extracción: {nuevos_articles} (antes: {len(articles)})")
            
            # Verificar si hay nuevos posts
            if nuevos_posts_en_esta_iteracion == 0:
                scrolls_sin_nuevos_posts += 1
                logger.warning(f"⚠️ No se extrajeron posts nuevos en esta iteración ({scrolls_sin_nuevos_posts}/{max_scrolls_sin_cambios * 3})")
                
                # Si tenemos pocos posts, ser persistente pero no infinito
                if len(posts_extraidos) < max_posts:
                    logger.info(f"📊 Solo tenemos {len(posts_extraidos)}/{max_posts} posts, continuando...")
                    # No resetear el contador, pero continuar
                else:
                    # Si ya tenemos suficientes posts, ser más estricto
                    if scrolls_sin_nuevos_posts >= max_scrolls_sin_cambios * 2:
                        logger.warning(f"⚠️ Ya tenemos {len(posts_extraidos)} posts (suficientes), no hay más contenido")
                        break
            else:
                scrolls_sin_nuevos_posts = 0  # Resetear contador si encontramos posts nuevos
                logger.info(f"✅ Se encontraron {nuevos_posts_en_esta_iteracion} posts nuevos, continuando...")
            
            # 6. Salir si no hay más contenido (scroll inteligente) - MÁS RÁPIDO
            # Verificar si la altura de la página cambió después de scrolls
            if scrolls_sin_nuevos_posts >= max_scrolls_sin_cambios * 2:  # REDUCIDO: 2 (antes 3) para terminar más rápido
                # Hacer un scroll final para verificar
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_height = driver.execute_script("return document.body.scrollHeight")
                
                if new_height == last_height and nuevos_posts_en_esta_iteracion == 0:
                    logger.warning(f"⚠️ ⚠️ ⚠️ No hay más contenido disponible (altura no cambió)")
                logger.info(f"📊 Posts extraídos hasta ahora: {len(posts_extraidos)}")
                break
            
            # Salir si ya tenemos suficientes
            if len(posts_extraidos) >= max_posts:
                logger.info(f"✅ ✅ ✅ LÍMITE ALCANZADO: {max_posts} posts extraídos")
                break
            
            # 3. Scroll inteligente RÁPIDO que detecta cuando no hay más contenido
            logger.info(f"📜 Haciendo scroll inteligente para cargar más posts...")
            
            # Obtener altura inicial
            last_height_before_scroll = driver.execute_script("return document.body.scrollHeight")
            
            # Scroll inteligente: hacer scroll y verificar si hay nuevo contenido (OPTIMIZADO)
            scroll_attempts = 0
            max_scroll_attempts = 2  # REDUCIDO: 2 intentos (antes 3) para ser más rápido
            
            while scroll_attempts < max_scroll_attempts:
                # Scroll hasta el final
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)  # REDUCIDO: 1.5 segundos (antes 2.0) para ser más rápido
                
                # Verificar si hay nuevo contenido
                new_height = driver.execute_script("return document.body.scrollHeight")
                
                if new_height == last_height_before_scroll:
                    # No hay más contenido, intentar scroll más pequeño
                    driver.execute_script("window.scrollBy(0, 500);")
                    time.sleep(1.0)  # REDUCIDO: 1.0 segundo (antes 1.5)
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    
                    if new_height == last_height_before_scroll:
                        # Realmente no hay más contenido
                        logger.info(f"📊 No hay más contenido disponible (altura: {new_height})")
                        break
                
                last_height_before_scroll = new_height
                scroll_attempts += 1
                
                # Scroll suave hacia arriba y abajo para activar lazy loading (solo si no es el último intento)
                if scroll_attempts < max_scroll_attempts:
                    driver.execute_script("window.scrollBy(0, -200);")
                    time.sleep(0.3)  # REDUCIDO: 0.3 segundos (antes 0.5)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1.0)  # REDUCIDO: 1.0 segundo (antes 1.5)
            
            # Scroll final para asegurar que todo esté visible
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.0)  # REDUCIDO: 1.0 segundo (antes 1.5)
            
            logger.info(f"✅ Scroll inteligente completado")
            
        except Exception as e:
            logger.error(f"❌ Error en bucle de extracción: {e}")
            break
    
    logger.info(f"✅ ✅ ✅ Extracción completada: {len(posts_extraidos)} posts REALES extraídos")
    
    # Si no se extrajeron posts, intentar con JavaScript como último recurso
    if len(posts_extraidos) == 0:
        logger.warning("⚠️ ⚠️ ⚠️ No se extrajeron posts con Selenium, intentando con JavaScript...")
        try:
            js_posts = driver.execute_script("""
                var posts = [];
                var articles = document.querySelectorAll('div[role="article"]');
                for (var i = 0; i < Math.min(articles.length, 50); i++) {
                    var article = articles[i];
                    var text = '';
                    var textElem = article.querySelector('[data-ad-preview="message"]') || 
                                   article.querySelector('div[dir="auto"]') ||
                                   article.querySelector('span[dir="auto"]');
                    if (textElem) {
                        text = textElem.textContent.trim();
                    }
                    if (text.length > 10) {
                        var img = article.querySelector('img[src*="fbcdn.net"]:not([src*="profile"])');
                        posts.push({
                            text: text,
                            image: img ? img.src : null
                        });
                    }
                }
                return posts;
            """)
            
            if js_posts and len(js_posts) > 0:
                logger.info(f"✅ JavaScript encontró {len(js_posts)} posts, convirtiendo...")
                for js_post in js_posts:
                    post_data = {
                        'id': f"fb_{int(time.time() * 1000)}_{random.randint(1000, 9999)}",
                        'platform': 'facebook',
                        'author': page_name,
                        'content': js_post.get('text', ''),
                        'cleaned_text': js_post.get('text', '').strip(),
                        'image_url': js_post.get('image'),
                        'url': '',
                        'created_at': datetime.now().isoformat(),
                        'metrics': {'likes': 0, 'comments': 0, 'shares': 0, 'retweets': 0},
                        'category': categorize_post(js_post.get('text', '')),
                        'sentiment': 'neutral'
                    }
                    posts_extraidos.append(post_data)
                logger.info(f"✅ ✅ ✅ {len(posts_extraidos)} posts extraídos con JavaScript!")
        except Exception as e:
            logger.error(f"❌ Error en extracción JavaScript: {e}")
    
    return posts_extraidos


def guardar_posts(posts: List[Dict], page_url: str, execution_time: float):
    """
    Guarda posts en formato JSON EXACTO especificado
    """
    output = {
        "metadata": {
            "page_url": page_url,
            "total_posts": len(posts),
            "scraped_at": datetime.now().isoformat(),
            "execution_time_seconds": execution_time
        },
        "posts": posts
    }
    
    filename = f"facebook_posts_{int(time.time())}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    logger.info(f"✅ Posts guardados en: {filename}")
    return filename


def mostrar_estadisticas(posts: List[Dict]):
    """
    Muestra estadísticas de los posts extraídos
    """
    if not posts:
        logger.warning("⚠️ No hay posts para mostrar estadísticas")
        return
    
    logger.info("\n" + "="*60)
    logger.info("📊 ESTADÍSTICAS DE EXTRACCIÓN")
    logger.info("="*60)
    logger.info(f"Total de posts: {len(posts)}")
    
    # Posts con imágenes
    posts_con_imagen = sum(1 for p in posts if p.get('image_url'))
    logger.info(f"Posts con imágenes: {posts_con_imagen}")
    
    # Categorías
    categorias = {}
    for post in posts:
        cat = post.get('category', 'noticias')
        categorias[cat] = categorias.get(cat, 0) + 1
    
    logger.info("\nCategorías:")
    for cat, count in categorias.items():
        logger.info(f"  - {cat}: {count}")
    
    # Métricas promedio
    total_likes = sum(p.get('metrics', {}).get('likes', 0) for p in posts)
    total_comments = sum(p.get('metrics', {}).get('comments', 0) for p in posts)
    total_shares = sum(p.get('metrics', {}).get('shares', 0) for p in posts)
    
    logger.info(f"\nMétricas totales:")
    logger.info(f"  - Likes: {total_likes:,}")
    logger.info(f"  - Comentarios: {total_comments:,}")
    logger.info(f"  - Compartidos: {total_shares:,}")
    logger.info("="*60 + "\n")


def scrape_facebook_page(page_url: str, max_posts: int = 100, wait_for_login_seconds: int = 60, progress_callback=None) -> List[Dict]:
    """
    Función principal que ejecuta todo el proceso
    
    Args:
        page_url: URL de la página de Facebook
        max_posts: Máximo de posts a extraer
        wait_for_login_seconds: Segundos a esperar para login manual (0 = usar input())
    """
    start_time = time.time()
    
    logger.info("\n" + "="*60)
    logger.info("🚀 FACEBOOK SCRAPER - LOGIN MANUAL")
    logger.info("="*60 + "\n")
    
    # 1. Setup ChromeDriver con configuración anti-detección
    driver = setup_chrome_driver()
    
    try:
        # 2. Login manual - CRÍTICO: Mantener ventana abierta
        logger.info("🔐 Por favor inicia sesión en Facebook manualmente")
        logger.info("⚠️ ⚠️ ⚠️ IMPORTANTE: La ventana del navegador permanecerá abierta")
        logger.info("⚠️ ⚠️ ⚠️ NO CIERRES LA VENTANA DEL NAVEGADOR - Espera a hacer login completo")
        
        # Asegurar que la ventana esté visible y enfocada
        try:
            driver.maximize_window()
            logger.info("✅ Ventana maximizada para mejor visibilidad")
        except:
            pass
        
        # Navegar a Facebook primero
        logger.info("🌐 Abriendo Facebook...")
        driver.get("https://www.facebook.com")
        time.sleep(3)
        
        # ESPERAR login - método según contexto
        if wait_for_login_seconds == 0:
            # Modo interactivo (terminal directa)
            logger.info("✋ Cuando termines de hacer login, presiona ENTER aquí...")
            input()
            logger.info("✅ ENTER presionado, verificando login...")
        else:
            # Modo servidor web (espera fija con verificación periódica)
            logger.info(f"⏳ Esperando {wait_for_login_seconds} segundos para que hagas login...")
            logger.info("💡 Si terminas antes, el sistema detectará el login automáticamente")
            
            login_detected = False
            checks = wait_for_login_seconds // 5  # Verificar cada 5 segundos
            
            for i in range(checks):
                time.sleep(5)
                try:
                    if verificar_login(driver):
                        logger.info(f"✅ ✅ ✅ LOGIN DETECTADO! Continuando... (verificación {i+1}/{checks})")
                        login_detected = True
                        break
                except:
                    pass
            
            if not login_detected:
                logger.warning(f"⚠️ No se detectó login después de {wait_for_login_seconds} segundos")
                logger.warning("⚠️ Continuando de todas formas...")
        
        # Verificar login
        if not verificar_login(driver):
            logger.error("❌ No se detectó login.")
            logger.error("💡 Asegúrate de haber completado el login en Facebook")
            return []
        
        logger.info("✅ Login exitoso!")
        
        # 3. Navegar a la página
        logger.info(f"\n🌐 Accediendo a: {page_url}")
        driver.get(page_url)
        time.sleep(5)  # REDUCIDO: 5 segundos (antes 10) para ser más rápido
        
        # Cerrar popups si aparecen
        try:
            close_buttons = driver.find_elements(By.CSS_SELECTOR, '[aria-label="Close"], [aria-label="Cerrar"]')
            for btn in close_buttons:
                try:
                    btn.click()
                    time.sleep(1)
                except:
                    pass
        except:
            pass
        
        # Hacer scrolls iniciales RÁPIDOS para cargar contenido
        logger.info("📜 Haciendo scrolls iniciales para cargar más posts...")
        for i in range(5):  # REDUCIDO: 5 scrolls iniciales (suficiente para activar lazy loading)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.8)  # REDUCIDO: 0.8 segundos (más rápido)
            # Scroll adicional hacia arriba y abajo para activar lazy loading
            driver.execute_script("window.scrollBy(0, -200);")
            time.sleep(0.2)  # REDUCIDO: 0.2 segundos
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            if (i + 1) % 2 == 0:  # Log cada 2 scrolls
                logger.info(f"📜 Scroll inicial {i+1}/5...")
            time.sleep(0.8)  # REDUCIDO: 0.8 segundos
        logger.info("✅ Scrolls iniciales completados")
        time.sleep(2)  # REDUCIDO: 2 segundos (antes 3)
        
        # Extraer nombre de la página
        page_name = "Página de Facebook"
        try:
            name_element = driver.find_element(By.CSS_SELECTOR, 'h1, h2, [data-pagelet="ProfileTilesFeed"] h2')
            page_name = name_element.text.strip()
        except:
            pass
        
        # 4. Extraer posts
        logger.info(f"\n📥 Extrayendo hasta {max_posts} posts...\n")
        posts = extraer_posts(driver, max_posts, page_name, progress_callback=progress_callback)
        
        # 5. Guardar resultados
        execution_time = time.time() - start_time
        
        if posts:
            guardar_posts(posts, page_url, execution_time)
            mostrar_estadisticas(posts)
            return posts
        else:
            logger.warning("\n❌ No se pudieron extraer posts")
            return []
    
    except Exception as e:
        logger.error(f"❌ Error en scraping: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []
    
    finally:
        # NO cerrar el navegador inmediatamente - dar tiempo al usuario
        logger.info("\n⚠️ ⚠️ ⚠️ IMPORTANTE: El navegador se cerrará en 5 segundos...")
        logger.info("💡 Si necesitas más tiempo, puedes cerrar manualmente")
        time.sleep(5)
        logger.info("\n🔒 Cerrando navegador...")
        try:
            driver.quit()
            logger.info("✅ Navegador cerrado")
        except:
            logger.warning("⚠️ Navegador ya estaba cerrado")


def main():
    """
    Función principal para ejecutar el scraper
    """
    # Configuración
    PAGE_URL = "https://www.facebook.com/elcomercio.pe"
    MAX_POSTS = 100
    
    posts = scrape_facebook_page(PAGE_URL, MAX_POSTS)
    
    if posts:
        logger.info(f"\n✅ ✅ ✅ EXTRACCIÓN EXITOSA: {len(posts)} posts extraídos")
    else:
        logger.error("\n❌ ❌ ❌ EXTRACCIÓN FALLIDA")


if __name__ == "__main__":
    main()

