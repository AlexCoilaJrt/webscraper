# Investigación: Scraping de Facebook - Mejores Prácticas 2024-2025

## 📋 Resumen de Investigación

### Problemas Identificados en el Código Actual

1. **Selectores Desactualizados**: Los selectores CSS pueden no funcionar con la nueva estructura de Facebook
2. **Tiempos de Espera Insuficientes**: Facebook necesita más tiempo para cargar contenido dinámico
3. **Falta de Manejo de Contenido Dinámico**: Facebook carga contenido de forma asíncrona
4. **Detección de Login Inadecuada**: Puede no detectar correctamente cuando el usuario está logueado

### Mejores Prácticas Encontradas

#### 1. Selectores CSS/XPath Recomendados

**Selectores Principales (Probados en 2024-2025):**

```javascript
// MÉTODO 1: Selector principal (más confiable)
document.querySelectorAll('div[role="article"]')

// MÉTODO 2: Selector por data-pagelet (Facebook interno)
document.querySelectorAll('div[data-pagelet*="FeedUnit"]')

// MÉTODO 3: Selector por estructura de post
document.querySelectorAll('div[data-pagelet*="Composer"]')

// MÉTODO 4: Selectores por clase (Facebook 2024-2025)
document.querySelectorAll('div[class*="x1y1aw1k"]')  // Post container
document.querySelectorAll('div[class*="x1n2onr6"]')  // Post wrapper
document.querySelectorAll('div[class*="x78zum5"]')   // Post content

// MÉTODO 5: Selector por texto estructurado
document.querySelectorAll('div[dir="auto"]')  // Contenido de texto
```

**Extracción de Texto:**

```javascript
// Múltiples métodos para encontrar texto del post
var textSelectors = [
    '[data-ad-preview="message"]',
    'div[data-testid="post_message"]',
    'div[dir="auto"]',
    'span[dir="auto"]',
    'div[class*="x193iq5w"]',  // Texto en posts nuevos
    'div[class*="x1y1aw1k"] span'  // Texto dentro del post
];
```

**Extracción de Imágenes:**

```javascript
// Imágenes de contenido (NO perfiles)
var imageSelectors = [
    'img[src*="fbcdn.net"]:not([src*="profile"]):not([src*="avatar"])',
    'img[src*="scontent"]:not([src*="profile"]):not([src*="avatar"])',
    'img[data-imgperflogname*="photo"]',
    'img[class*="x1ey2m1c"]'  // Imágenes de posts nuevos
];
```

#### 2. Técnicas de Espera y Sincronización

**Problema**: Facebook carga contenido de forma asíncrona con JavaScript

**Solución**:

```python
# 1. Esperar a que el DOM esté listo
WebDriverWait(driver, 20).until(
    lambda d: d.execute_script("return document.readyState") == "complete"
)

# 2. Esperar a que aparezcan elementos de posts
WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="article"]'))
)

# 3. Esperar después del scroll
time.sleep(3)  # Mínimo 3 segundos después de cada scroll

# 4. Verificar que el contenido se haya cargado
posts_before = len(driver.find_elements(By.CSS_SELECTOR, 'div[role="article"]'))
time.sleep(2)
posts_after = len(driver.find_elements(By.CSS_SELECTOR, 'div[role="article"]'))
if posts_after == posts_before:
    # No hay más posts cargando
    break
```

#### 3. Scroll Inteligente

**Estrategia de Scroll Mejorada**:

```python
def smart_scroll_facebook(driver):
    """Scroll inteligente que espera a que cargue contenido"""
    # Scroll suave
    last_height = driver.execute_script("return document.body.scrollHeight")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    
    # Esperar a que cargue nuevo contenido
    time.sleep(3)
    
    # Verificar si hay nuevo contenido
    new_height = driver.execute_script("return document.body.scrollHeight")
    
    # Si no hay cambio, intentar scroll más pequeño
    if new_height == last_height:
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(2)
    
    return new_height != last_height
```

#### 4. Detección Mejorada de Login

```python
def is_facebook_logged_in(driver):
    """Detecta si el usuario está logueado en Facebook"""
    try:
        # Verificar elementos que solo aparecen cuando estás logueado
        logged_in_indicators = [
            'div[aria-label*="Profile"]',  # Menú de perfil
            'div[role="banner"] a[aria-label*="Profile"]',  # Link de perfil
            'div[role="navigation"]',  # Navegación principal
            'div[data-pagelet="LeftRail"]',  # Barra lateral izquierda
        ]
        
        for selector in logged_in_indicators:
            if driver.find_elements(By.CSS_SELECTOR, selector):
                return True
        
        # Verificar que NO haya pantalla de login
        login_indicators = [
            'input[name="email"]',
            'input[name="pass"]',
            'button[name="login"]',
            'div[aria-label*="Log in"]',
        ]
        
        for selector in login_indicators:
            if driver.find_elements(By.CSS_SELECTOR, selector):
                return False
        
        return True  # Si no hay indicadores de login, asumir logueado
    except:
        return False
```

#### 5. Extracción Completa con JavaScript

**Script JavaScript Optimizado**:

```javascript
function extractFacebookPosts() {
    var posts = [];
    
    // Buscar todos los posts posibles
    var articleElements = document.querySelectorAll('div[role="article"]');
    
    // Si no encuentra, usar selectores alternativos
    if (articleElements.length === 0) {
        articleElements = document.querySelectorAll('div[data-pagelet*="FeedUnit"]');
    }
    
    for (var i = 0; i < articleElements.length; i++) {
        var article = articleElements[i];
        var post = {};
        
        // Extraer texto con múltiples métodos
        var textSelectors = [
            '[data-ad-preview="message"]',
            'div[data-testid="post_message"]',
            'div[dir="auto"]',
            'span[dir="auto"]'
        ];
        
        for (var j = 0; j < textSelectors.length; j++) {
            var textElem = article.querySelector(textSelectors[j]);
            if (textElem && textElem.textContent.trim().length > 20) {
                post.text = textElem.textContent.trim();
                break;
            }
        }
        
        // Extraer imagen
        var images = article.querySelectorAll('img[src*="fbcdn.net"]:not([src*="profile"]):not([src*="avatar"])');
        if (images.length > 0) {
            post.image = images[0].src;
        }
        
        // Extraer username
        var usernameElem = article.querySelector('strong, h2 a, h3 a, a[role="link"] span');
        if (usernameElem) {
            post.username = usernameElem.textContent.trim();
        }
        
        // Extraer URL del post
        var linkElem = article.querySelector('a[href*="/posts/"], a[href*="/permalink/"]');
        if (linkElem) {
            post.url = linkElem.href;
        }
        
        // Solo agregar si tiene texto válido
        if (post.text && post.text.length > 15) {
            posts.push(post);
        }
    }
    
    return posts;
}
```

### Recomendaciones de Implementación

#### 1. Orden de Prioridad para Extracción

1. **Primero**: Intentar con `div[role="article"]` (más confiable)
2. **Segundo**: `div[data-pagelet*="FeedUnit"]` (Facebook interno)
3. **Tercero**: Selectores por clase (Facebook 2024-2025)
4. **Último**: Búsqueda genérica por estructura

#### 2. Tiempos de Espera Recomendados

- **Después del login**: 15-20 segundos
- **Después de cargar página**: 8-10 segundos
- **Después de cada scroll**: 3-5 segundos
- **Timeout total**: 5-10 minutos

#### 3. Manejo de Errores

```python
try:
    # Intentar extracción
    posts = extract_posts()
except Exception as e:
    logger.error(f"Error en extracción: {e}")
    # Intentar método alternativo
    posts = extract_posts_alternative()
```

#### 4. Validación de Posts

```python
def validate_post(post):
    """Valida que un post sea real y no duplicado"""
    # Verificar que tenga texto
    if not post.get('text') or len(post.get('text', '')) < 15:
        return False
    
    # Verificar que no sea duplicado
    if post.get('text') in seen_posts:
        return False
    
    # Verificar que la imagen sea válida (si existe)
    if post.get('image_url'):
        if 'profile' in post['image_url'] or 'avatar' in post['image_url']:
            return False
    
    return True
```

### Consideraciones Legales y Éticas

⚠️ **IMPORTANTE**: 
- Este código es SOLO para fines académicos y educativos
- Facebook prohíbe el scraping no autorizado en sus Términos de Servicio
- Respeta siempre las políticas de Facebook y las leyes de privacidad
- Solo extrae datos públicos disponibles sin login
- Considera usar la Graph API oficial cuando sea posible

### Métodos Alternativos

1. **Graph API de Facebook**: Método oficial pero requiere autenticación y permisos
2. **RSS Feeds**: Algunas páginas de Facebook ofrecen feeds RSS
3. **Herramientas de terceros**: Siempre verificar términos de servicio

### Próximos Pasos

1. ✅ Implementar selectores mejorados
2. ✅ Aumentar tiempos de espera
3. ✅ Mejorar detección de login
4. ✅ Implementar scroll inteligente
5. ✅ Agregar validación de posts
6. ✅ Mejorar manejo de errores















