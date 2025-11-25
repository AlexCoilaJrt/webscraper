# Investigación: Scraping de Reddit - Mejores Prácticas 2024-2025

## 📋 Resumen Ejecutivo

Reddit es una plataforma de comunidades (subreddits) donde los usuarios publican contenido y comentarios. A diferencia de Facebook y Twitter/X, Reddit tiene una **API oficial muy robusta** (PRAW) que es la forma recomendada y más ética de extraer datos.

## 🎯 Métodos de Extracción

### 1. **API Oficial de Reddit (RECOMENDADO) - PRAW**

**Ventajas:**
- ✅ Legal y ético
- ✅ Estructurado y confiable
- ✅ No requiere Selenium
- ✅ Respeta límites de tasa automáticamente
- ✅ Acceso a metadatos completos

**Desventajas:**
- ⚠️ Requiere registro de aplicación
- ⚠️ Requiere autenticación (client_id, client_secret)
- ⚠️ Tiene límites de tasa (60 requests/minuto)

**Instalación:**
```bash
pip install praw
```

**Configuración:**
1. Ir a https://www.reddit.com/prefs/apps
2. Crear aplicación (tipo: "script")
3. Obtener `client_id` y `client_secret`
4. Definir `user_agent` (ej: "MyApp/1.0 by MyUsername")

**Ejemplo de Uso:**
```python
import praw

reddit = praw.Reddit(
    client_id='TU_CLIENT_ID',
    client_secret='TU_CLIENT_SECRET',
    user_agent='MyApp/1.0 by MyUsername'
)

# Obtener posts de un subreddit
subreddit = reddit.subreddit('python')
for post in subreddit.hot(limit=10):
    print(f"Título: {post.title}")
    print(f"Score: {post.score}")
    print(f"URL: {post.url}")
    print(f"Comentarios: {post.num_comments}")
```

### 2. **Web Scraping con Selenium (ALTERNATIVO)**

**Cuándo usar:**
- No tienes acceso a API
- Necesitas datos que la API no proporciona
- Solo para fines académicos

**Consideraciones:**
- ⚠️ Reddit ha implementado medidas anti-scraping
- ⚠️ Puede violar términos de servicio
- ⚠️ Menos confiable que la API
- ⚠️ Requiere más recursos (Selenium)

**Selectores CSS (2025):**
```css
/* Posts principales */
shreddit-post, article[data-testid="post-container"]
div[data-testid="post-container"]
div[class*="Post"]

/* Contenedor de post */
div[data-testid="post-container"]

/* Título del post */
h3[data-testid="post-title"], 
a[data-click-id="body"]

/* Texto del post */
div[data-test-id="post-content"] p,
div[slot="text-body"]

/* Upvotes/Downvotes */
button[aria-label*="upvote"],
button[aria-label*="downvote"],
span[data-testid="vote-count"]

/* Comentarios */
shreddit-comment,
div[data-testid="comment"]

/* URL del post */
a[data-click-id="body"]

/* Autor */
a[data-testid="subreddit-name"],
a[data-testid="author-name"]

/* Fecha */
time[datetime],
span[data-testid="post_timestamp"]
```

**Estructura HTML de Reddit:**
```html
<shreddit-post>
  <article data-testid="post-container">
    <div class="Post">
      <h3 data-testid="post-title">Título del post</h3>
      <div slot="text-body">Contenido del post</div>
      <div class="PostFooter">
        <button aria-label="upvote">↑</button>
        <span data-testid="vote-count">1.2k</span>
        <a data-click-id="comments">Comentarios</a>
      </div>
    </div>
  </article>
</shreddit-post>
```

### 3. **Reddit Old (old.reddit.com) - MÁS FÁCIL DE SCRAPEAR**

**Ventajas:**
- ✅ HTML más simple y estable
- ✅ Menos JavaScript dinámico
- ✅ Más fácil de scrapear con BeautifulSoup

**Estructura:**
```python
# URL: https://old.reddit.com/r/subreddit/
# Selectores:
div.thing  # Contenedor de post
p.title > a.title  # Título del post
div.score  # Puntos (upvotes)
a.comments  # Link a comentarios
span.tagline  # Autor y fecha
```

## 📊 Datos que se Pueden Extraer

### Posts:
- Título
- Contenido/Texto
- Autor (username)
- Subreddit
- Upvotes/Downvotes (score)
- Número de comentarios
- URL del post
- Fecha de publicación
- Imágenes/Videos (si aplica)
- Flair (etiquetas)

### Comentarios:
- Texto del comentario
- Autor
- Upvotes
- Fecha
- Respuestas (threads)

## 🔧 Implementación Recomendada

### Arquitectura Híbrida:

1. **Intentar API primero (PRAW)**
   - Si hay credenciales disponibles
   - Más confiable y rápido

2. **Fallback a Selenium**
   - Si no hay API disponible
   - Para contenido dinámico
   - Usar old.reddit.com si es posible

### Métodos de Extracción:

**Método 1: API con PRAW (PREFERIDO)**
```python
import praw

class RedditAPIScraper:
    def __init__(self, client_id, client_secret, user_agent):
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
    
    def get_subreddit_posts(self, subreddit_name, limit=100, sort='hot'):
        subreddit = self.reddit.subreddit(subreddit_name)
        
        if sort == 'hot':
            posts = subreddit.hot(limit=limit)
        elif sort == 'new':
            posts = subreddit.new(limit=limit)
        elif sort == 'top':
            posts = subreddit.top(limit=limit)
        
        results = []
        for post in posts:
            results.append({
                'title': post.title,
                'content': post.selftext,
                'author': str(post.author),
                'subreddit': subreddit_name,
                'score': post.score,
                'upvotes': post.ups,
                'downvotes': post.downs,
                'comments': post.num_comments,
                'url': post.url,
                'permalink': f"https://reddit.com{post.permalink}",
                'created_at': datetime.fromtimestamp(post.created_utc),
                'flair': post.link_flair_text,
                'image_url': post.url if post.url.endswith(('.jpg', '.png', '.gif')) else None
            })
        
        return results
```

**Método 2: Selenium (Fallback)**
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class RedditSeleniumScraper:
    def __init__(self, headless=True):
        self.driver = self._setup_driver(headless)
    
    def scrape_subreddit(self, subreddit_name, max_posts=100):
        # Usar old.reddit.com para más facilidad
        url = f"https://old.reddit.com/r/{subreddit_name}/"
        self.driver.get(url)
        
        posts = []
        scrolls = 0
        max_scrolls = 50
        
        while len(posts) < max_posts and scrolls < max_scrolls:
            # Extraer posts visibles
            post_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div.thing')
            
            for post_elem in post_elements:
                try:
                    title = post_elem.find_element(By.CSS_SELECTOR, 'p.title > a.title').text
                    author = post_elem.find_element(By.CSS_SELECTOR, 'a.author').text
                    score = post_elem.find_element(By.CSS_SELECTOR, 'div.score').text
                    comments = post_elem.find_element(By.CSS_SELECTOR, 'a.comments').text
                    post_url = post_elem.find_element(By.CSS_SELECTOR, 'p.title > a.title').get_attribute('href')
                    
                    posts.append({
                        'title': title,
                        'author': author,
                        'score': self._parse_score(score),
                        'comments': self._parse_comments(comments),
                        'url': post_url,
                        'subreddit': subreddit_name
                    })
                except:
                    continue
            
            # Scroll para cargar más
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            scrolls += 1
        
        return posts[:max_posts]
```

## ⚠️ Consideraciones Legales y Éticas

### IMPORTANTE:
1. **Reddit prohíbe scraping no autorizado** en sus Términos de Servicio
2. **Reddit ha demandado empresas** por scraping no autorizado (ej: Anthropic, Perplexity)
3. **Usa la API oficial** siempre que sea posible
4. **Respeta robots.txt**: Reddit actualizó su robots.txt en 2024 para bloquear scraping

### Mejores Prácticas:
- ✅ Usar API oficial (PRAW) cuando sea posible
- ✅ Respetar límites de tasa (60 requests/minuto)
- ✅ Usar delays responsables (1-2 segundos entre requests)
- ✅ Solo extraer datos públicos
- ✅ No almacenar información personal
- ✅ Solo para fines académicos/educativos
- ⚠️ Evitar scraping automatizado del sitio web principal

## 🔍 Selectores CSS para Reddit (2025)

### Reddit Moderno (reddit.com):
```css
/* Posts */
shreddit-post
article[data-testid="post-container"]
div[data-testid="post-container"]

/* Título */
h3[data-testid="post-title"]
a[data-click-id="body"]

/* Contenido */
div[slot="text-body"]
div[data-test-id="post-content"]

/* Upvotes */
button[aria-label*="upvote"]
span[data-testid="vote-count"]

/* Autor */
a[data-testid="author-name"]
a[data-testid="subreddit-name"]

/* Comentarios */
a[data-click-id="comments"]
span[data-testid="comment-count"]
```

### Reddit Old (old.reddit.com):
```css
/* Posts */
div.thing

/* Título */
p.title > a.title

/* Autor */
a.author

/* Score */
div.score

/* Comentarios */
a.comments

/* Fecha */
time.live-timestamp
```

## 📝 Formato de Datos Esperado

```python
{
    'platform': 'reddit',
    'title': 'Título del post',
    'content': 'Contenido del post',
    'author': 'username',
    'subreddit': 'subreddit_name',
    'score': 1234,  # Upvotes - downvotes
    'upvotes': 1500,
    'downvotes': 266,
    'comments': 89,
    'url': 'https://reddit.com/r/...',
    'permalink': 'https://reddit.com/r/.../comments/...',
    'created_at': '2025-01-15T10:30:00',
    'flair': 'Discussion',  # Etiqueta del post
    'image_url': 'https://...',  # Si tiene imagen
    'category': 'tecnologia',  # Categoría detectada
    'sentiment': 'positive',  # Sentimiento
    'hashtags': []  # Reddit no usa hashtags tradicionalmente
}
```

## 🚀 Plan de Implementación

1. **Crear RedditAPIScraper** (PRAW)
2. **Crear RedditSeleniumScraper** (Fallback)
3. **Integrar en social_media_scraper.py**
4. **Actualizar api_server.py** para soportar Reddit
5. **Actualizar frontend** para mostrar Reddit como opción
6. **Agregar Reddit a requirements.txt** (praw)

## 📚 Recursos Adicionales

- [PRAW Documentation](https://praw.readthedocs.io/)
- [Reddit API Documentation](https://www.reddit.com/dev/api/)
- [Reddit Data API Terms](https://www.redditinc.com/policies/data-api-terms)
- [Pushshift API](https://github.com/pushshift/api) - Para datos históricos

## ⚡ Ventajas de Reddit vs Facebook/Twitter

1. **API Oficial Robusta**: PRAW es muy completo
2. **Datos Estructurados**: Posts, comentarios, subreddits bien organizados
3. **Menos Anti-Detección**: Si usas API, no hay problemas
4. **Datos Más Ricos**: Upvotes, downvotes, flairs, etc.

## 🎯 Recomendación Final

**Para este proyecto académico:**
1. Implementar RedditAPIScraper con PRAW (método principal)
2. Implementar RedditSeleniumScraper como fallback (old.reddit.com)
3. Priorizar API, usar Selenium solo si no hay credenciales
4. Documentar claramente que es solo para fines académicos















