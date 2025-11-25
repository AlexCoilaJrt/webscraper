# 📱 Guía de Scraping de Redes Sociales - Mejorado

## 🎯 Características Principales

Este sistema mejorado de scraping de redes sociales incluye:

### ✅ **Extracción Completa de Contenido**
- **Expansión automática** de contenido colapsado ("Ver más", "Show more")
- **Texto completo** sin truncar
- **Preservación de emojis** y caracteres especiales
- **Manejo inteligente** de contenido dinámico

### ✅ **Extracción Mejorada de Imágenes/Media**
- **URLs reales** de imágenes (no placeholders)
- **Validación de URLs** para asegurar que sean accesibles
- **Filtrado de avatares** y perfiles
- **Soporte para videos** (Facebook)
- **Detección de imágenes de contenido** vs. imágenes de UI

### ✅ **Métricas Precisas**
- **Parseo mejorado** de formatos abreviados (1.2K → 1200, 5M → 5000000)
- **Selectores específicos** para likes, retweets, comentarios
- **Fallback robusto** si los selectores principales fallan

### ✅ **Categorización Inteligente**
- **Keywords expandidas** para 6 categorías principales
- **Scoring ponderado** por frecuencia de palabras clave
- **Categorías**: tecnología, deportes, política, entretenimiento, negocios, salud

### ✅ **Análisis de Sentimiento Preciso**
- **VADER Sentiment** (preferido para redes sociales)
- **TextBlob** como fallback
- **Análisis básico** como último recurso
- **Umbrales precisos**: positivo > 0.05, negativo < -0.05

### ✅ **Retry Logic y Validación**
- **3 intentos** por elemento si falla la extracción
- **Validación de datos** antes de guardar
- **Manejo robusto de errores** con logs detallados

---

## 🚀 Instalación

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

**Nuevas dependencias agregadas:**
- `textblob==0.17.1` - Análisis de sentimiento
- `vaderSentiment==3.3.2` - Análisis de sentimiento para redes sociales
- `nltk==3.8.1` - Procesamiento de lenguaje natural

### 2. Descargar Datos de NLTK (opcional)

Si usas TextBlob, necesitas descargar datos de NLTK:

```python
import nltk
nltk.download('punkt')
nltk.download('brown')
nltk.download('wordnet')
```

---

## 📖 Uso

### Ejemplo Básico - Twitter/X

```python
from social_media_scraper import TwitterScraper
from social_media_processor import SocialMediaProcessor

# Crear scraper
scraper = TwitterScraper(headless=True, delay=3)

# Scrapear desde URL
posts = scraper.scrape_from_url(
    url="https://twitter.com/search?q=tecnologia",
    max_tweets=50
)

# Procesar posts
processor = SocialMediaProcessor()
processed_posts = processor.process_batch(posts)

# Mostrar resultados
for post in processed_posts:
    print(f"Usuario: {post['username']}")
    print(f"Texto: {post['text']}")
    print(f"Imagen: {post.get('image_url', 'N/A')}")
    print(f"Likes: {post['likes']}")
    print(f"Categoría: {post['category']}")
    print(f"Sentimiento: {post['sentiment']}")
    print("-" * 60)

scraper.close()
```

### Ejemplo Básico - Facebook

```python
from social_media_scraper import FacebookScraper
from social_media_processor import SocialMediaProcessor

# Crear scraper
scraper = FacebookScraper(headless=True, delay=3)

# Scrapear desde URL
posts = scraper.scrape_from_url(
    url="https://www.facebook.com/facebook",
    max_posts=50
)

# Procesar posts
processor = SocialMediaProcessor()
processed_posts = processor.process_batch(posts)

scraper.close()
```

---

## 🔧 Selectores CSS/XPath Actualizados

### Twitter/X

| Elemento | Selector |
|----------|----------|
| **Texto del tweet** | `div[data-testid="tweetText"]` o `span[data-testid="tweetText"]` |
| **Autor** | `a[href*="/user"]` o `span` con `@username` |
| **Likes** | `span[data-testid="like"]` o `button[data-testid="like"]` |
| **Retweets** | `span[data-testid="retweet"]` o `button[data-testid="retweet"]` |
| **Respuestas** | `span[data-testid="reply"]` o `button[data-testid="reply"]` |
| **Imágenes** | `div[data-testid*="media"] img` o `img[src*="pbs.twimg.com"]` |
| **Posts** | `article[data-testid="tweet"]` |

### Facebook

| Elemento | Selector |
|----------|----------|
| **Texto del post** | `div[data-ad-preview="message"]` o `div[data-testid="post_message"]` |
| **Autor** | `a[href*="/pages/"]` o `span.x1lliihq.x1plvlek` |
| **Reacciones** | `span[aria-label*="reaction"]` o texto con "like", "me gusta" |
| **Comentarios** | `span[aria-label*="comment"]` o texto con "comment", "comentario" |
| **Compartidos** | `span[aria-label*="share"]` o texto con "share", "compartir" |
| **Imágenes** | `img[src*="fbcdn.net"]` o `img[data-visualcompletion="media-vc-image"]` |
| **Posts** | `div[data-pagelet]` o `div[role="article"]` |

---

## 🧪 Testing

### Ejecutar Script de Prueba

```bash
python test_social_media_extraction.py
```

Este script valida:
- ✅ Contenido completo sin truncar
- ✅ URLs de imágenes válidas (no null)
- ✅ Métricas numéricas correctas
- ✅ Categoría relevante
- ✅ Sentimiento preciso

---

## 🔍 Troubleshooting Común

### ❌ Problema: "No se extraen posts"

**Causas posibles:**
1. **Requiere autenticación**: Twitter/Facebook bloquean el acceso sin login
2. **Selectores desactualizados**: Las plataformas cambian su HTML frecuentemente
3. **Timeout**: La página no carga a tiempo

**Soluciones:**
- Verificar que la URL sea pública y accesible
- Aumentar el delay: `scraper = TwitterScraper(delay=5)`
- Verificar logs para ver qué selectores están fallando
- Intentar con modo no-headless para ver qué está pasando: `headless=False`

### ❌ Problema: "image_url: null"

**Causas posibles:**
1. El post no tiene imagen
2. La imagen está cargada dinámicamente (lazy loading)
3. Los selectores de imagen no funcionan

**Soluciones:**
- Verificar que el post realmente tenga imagen
- Aumentar tiempo de espera antes de extraer: `time.sleep(5)`
- Hacer scroll para cargar imágenes lazy: `driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")`
- Revisar logs para ver si se detectan imágenes pero se filtran

### ❌ Problema: "Métricas incorrectas (0 o muy altas)"

**Causas posibles:**
1. Formato abreviado no se parsea correctamente ("1.2K" → 1200)
2. Selectores de métricas no funcionan
3. Métricas están en otro formato

**Soluciones:**
- Verificar que el parseo de métricas funcione: `scraper._parse_metric("1.2K")` debe retornar `1200`
- Revisar HTML del post para ver el formato real de las métricas
- Usar fallback de búsqueda por contexto si selectores específicos fallan

### ❌ Problema: "Categoría siempre es 'general'"

**Causas posibles:**
1. El texto no contiene palabras clave conocidas
2. El texto está muy corto o truncado
3. Las palabras clave no coinciden

**Soluciones:**
- Verificar que el texto completo se extraiga (no truncado)
- Agregar más palabras clave a `category_keywords` en `social_media_processor.py`
- Reducir el umbral de scoring: cambiar `>= 2` a `>= 1` en `categorize_tweet`

### ❌ Problema: "Sentimiento siempre es 'neutral'"

**Causas posibles:**
1. VADER/TextBlob no están instalados
2. El texto es muy corto
3. El texto no tiene palabras con carga emocional

**Soluciones:**
- Verificar instalación: `pip install vaderSentiment textblob`
- Verificar que el texto se extraiga completo
- Probar manualmente: `analyzer = SentimentIntensityAnalyzer(); analyzer.polarity_scores("I love this!")`

### ❌ Problema: "Error: 'WebDriver' no encontrado"

**Causas posibles:**
1. ChromeDriver/EdgeDriver no está instalado
2. webdriver-manager no puede descargar el driver

**Soluciones:**
- Instalar webdriver-manager: `pip install webdriver-manager`
- Verificar que Chrome/Edge esté instalado
- Usar versión específica: `ChromeDriverManager(version="120.0.0.0").install()`

### ❌ Problema: "Timeout en carga de página"

**Causas posibles:**
1. Conexión lenta
2. La página tarda mucho en cargar
3. Hay demasiados elementos que cargar

**Soluciones:**
- Aumentar timeout: `driver.set_page_load_timeout(60)`
- Reducir max_posts para pruebas: `max_posts=10`
- Usar delays más largos: `delay=5`

---

## 📊 Estructura de Datos Extraídos

```python
{
    "platform": "twitter" | "facebook",
    "username": "@username" o "Page Name",
    "text": "Texto completo del post...",
    "cleaned_text": "Texto limpio sin URLs...",
    "date": "2025-01-15T10:30:00",
    "likes": 1992,
    "retweets": 0,  # Solo Twitter
    "replies": 293,  # Twitter
    "comments": 293,  # Facebook
    "shares": 150,  # Facebook
    "hashtags": ["#tecnologia", "#IA"],
    "url": "https://twitter.com/user/status/123456",
    "image_url": "https://pbs.twimg.com/media/...",
    "video_url": "https://fbcdn.net/...",  # Solo Facebook
    "category": "tecnología",
    "sentiment": "positive" | "negative" | "neutral",
    "detected_language": "es" | "en" | "unknown",
    "scraped_at": "2025-01-15T10:30:00",
    "processed_at": "2025-01-15T10:30:05"
}
```

---

## 🎯 Mejores Prácticas

1. **Usar delays apropiados**: Mínimo 3 segundos entre requests
2. **Validar datos extraídos**: Siempre verificar que los datos sean correctos
3. **Manejar errores**: Usar try-except para manejar errores gracefully
4. **Logs detallados**: Usar logging para debugging
5. **Respetar ToS**: Solo scrapear contenido público y respetar términos de servicio
6. **Rate limiting**: No hacer demasiados requests en poco tiempo

---

## 📝 Notas Importantes

- ⚠️ **Solo para fines académicos**: Este código es para aprendizaje y educación
- ⚠️ **Respeta los ToS**: Twitter y Facebook tienen políticas estrictas sobre scraping
- ⚠️ **Autenticación**: Mucho contenido requiere autenticación para acceder
- ⚠️ **Selectores cambian**: Las plataformas actualizan su HTML frecuentemente
- ⚠️ **Rate limiting**: No abuses del sistema para evitar bloqueos

---

## 🔄 Actualizaciones Recientes

### v2.0 - Mejoras Principales

- ✅ Expansión automática de contenido colapsado
- ✅ Validación de URLs de imágenes
- ✅ Parseo mejorado de métricas (K, M, B)
- ✅ Selectores CSS/XPath actualizados
- ✅ Análisis de sentimiento con VADER/TextBlob
- ✅ Categorización mejorada con keywords expandidas
- ✅ Retry logic para elementos que fallan
- ✅ Script de prueba para validación

---

## 📞 Soporte

Si encuentras problemas:
1. Revisa los logs para ver errores específicos
2. Ejecuta el script de prueba: `python test_social_media_extraction.py`
3. Verifica que todas las dependencias estén instaladas
4. Revisa esta guía de troubleshooting

---

**¡Happy Scraping! 🚀**















