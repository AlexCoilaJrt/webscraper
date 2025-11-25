# Investigación: Scraping de YouTube - Mejores Prácticas 2024-2025

## 📋 Resumen Ejecutivo

YouTube es la plataforma de video más grande del mundo. Tiene una **API oficial muy completa** (YouTube Data API v3) que es la forma recomendada y legal de extraer datos. También es posible hacer web scraping con Selenium, pero es más complejo debido al contenido dinámico.

## 🎯 Métodos de Extracción

### 1. **API Oficial de YouTube (RECOMENDADO) - YouTube Data API v3**

**Ventajas:**
- ✅ Legal y ético
- ✅ Estructurado y confiable
- ✅ No requiere Selenium
- ✅ Acceso a metadatos completos (vistas, likes, comentarios, etc.)
- ✅ Información de canales y playlists

**Desventajas:**
- ⚠️ Requiere API Key de Google Cloud
- ⚠️ Tiene límites de cuota diaria (10,000 unidades por defecto)
- ⚠️ Requiere configuración en Google Cloud Console

**Instalación:**
```bash
pip install google-api-python-client
```

**Configuración:**
1. Ir a https://console.cloud.google.com/
2. Crear proyecto o seleccionar existente
3. Habilitar "YouTube Data API v3"
4. Crear credenciales (API Key)
5. Obtener API Key

**Ejemplo de Uso:**
```python
from googleapiclient.discovery import build

youtube = build('youtube', 'v3', developerKey='TU_API_KEY')

# Buscar videos
request = youtube.search().list(
    part='snippet',
    q='python tutorial',
    maxResults=10,
    type='video'
)
response = request.execute()

# Obtener videos de un canal
request = youtube.search().list(
    part='snippet',
    channelId='CANAL_ID',
    maxResults=50,
    order='date'
)
response = request.execute()
```

### 2. **Web Scraping con Selenium (ALTERNATIVO)**

**Cuándo usar:**
- No tienes API Key
- Necesitas datos que la API no proporciona
- Solo para fines académicos

**Consideraciones:**
- ⚠️ YouTube tiene medidas anti-scraping
- ⚠️ Puede violar términos de servicio
- ⚠️ Menos confiable que la API
- ⚠️ Requiere más recursos (Selenium)
- ⚠️ Contenido muy dinámico (scroll infinito)

**Selectores CSS (2025):**
```css
/* Videos en grid */
ytd-video-renderer
div#dismissible

/* Título del video */
a#video-title
h3 a

/* Canal */
ytd-channel-name a
#channel-name a

/* Vistas */
span#metadata-line
span.style-scope.ytd-video-meta-block

/* Duración */
span.ytd-thumbnail-overlay-time-status-renderer

/* Thumbnail */
img.yt-img-shadow
img[src*="i.ytimg.com"]

/* Descripción */
ytd-video-renderer #description-text

/* Likes/Dislikes (oculto en 2025, pero disponible en API) */
button[aria-label*="like"]
```

## 📊 Datos que se Pueden Extraer

### Videos:
- Título
- Descripción
- Canal (autor)
- URL del video
- Thumbnail (imagen)
- Duración
- Vistas
- Likes (desde API)
- Dislikes (removido en 2025, solo API histórica)
- Fecha de publicación
- Comentarios (número y contenido)
- Tags
- Categoría

### Canales:
- Nombre del canal
- Descripción
- Número de suscriptores
- Número de videos
- URL del canal

## 🔧 Implementación Recomendada

### Arquitectura Híbrida:

1. **Intentar API primero (YouTube Data API v3)**
   - Si hay API Key disponible
   - Más confiable y rápido

2. **Fallback a Selenium**
   - Si no hay API Key disponible
   - Para contenido dinámico
   - Usar scroll para cargar más videos

### Métodos de Extracción:

**Método 1: API con google-api-python-client (PREFERIDO)**
```python
from googleapiclient.discovery import build

class YouTubeAPIScraper:
    def __init__(self, api_key):
        self.youtube = build('youtube', 'v3', developerKey=api_key)
    
    def search_videos(self, query, max_results=50):
        request = self.youtube.search().list(
            part='snippet',
            q=query,
            maxResults=max_results,
            type='video',
            order='relevance'
        )
        response = request.execute()
        
        videos = []
        for item in response['items']:
            video_id = item['id']['videoId']
            # Obtener estadísticas adicionales
            stats = self.youtube.videos().list(
                part='statistics,snippet,contentDetails',
                id=video_id
            ).execute()
            
            videos.append({
                'title': item['snippet']['title'],
                'description': item['snippet']['description'],
                'channel': item['snippet']['channelTitle'],
                'url': f"https://www.youtube.com/watch?v={video_id}",
                'thumbnail': item['snippet']['thumbnails']['high']['url'],
                'published_at': item['snippet']['publishedAt'],
                'views': stats['items'][0]['statistics'].get('viewCount', 0),
                'likes': stats['items'][0]['statistics'].get('likeCount', 0),
                'comments': stats['items'][0]['statistics'].get('commentCount', 0)
            })
        
        return videos
    
    def get_channel_videos(self, channel_id, max_results=50):
        # Buscar videos del canal
        request = self.youtube.search().list(
            part='snippet',
            channelId=channel_id,
            maxResults=max_results,
            order='date',
            type='video'
        )
        response = request.execute()
        
        # Procesar similar a search_videos
        return self._process_videos(response)
```

**Método 2: Selenium (Fallback)**
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class YouTubeSeleniumScraper:
    def __init__(self, headless=True):
        self.driver = self._setup_driver(headless)
    
    def scrape_channel(self, channel_url, max_videos=100):
        self.driver.get(f"{channel_url}/videos")
        time.sleep(5)
        
        videos = []
        scrolls = 0
        max_scrolls = 50
        
        while len(videos) < max_videos and scrolls < max_scrolls:
            # Extraer videos visibles
            video_elements = self.driver.find_elements(By.CSS_SELECTOR, 'ytd-video-renderer')
            
            for video_elem in video_elements:
                try:
                    title = video_elem.find_element(By.CSS_SELECTOR, 'a#video-title').text
                    url = video_elem.find_element(By.CSS_SELECTOR, 'a#video-title').get_attribute('href')
                    channel = video_elem.find_element(By.CSS_SELECTOR, 'ytd-channel-name a').text
                    views = video_elem.find_element(By.CSS_SELECTOR, 'span#metadata-line').text
                    thumbnail = video_elem.find_element(By.CSS_SELECTOR, 'img.yt-img-shadow').get_attribute('src')
                    
                    videos.append({
                        'title': title,
                        'url': url,
                        'channel': channel,
                        'views': self._parse_views(views),
                        'thumbnail': thumbnail
                    })
                except:
                    continue
            
            # Scroll para cargar más
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            scrolls += 1
        
        return videos[:max_videos]
```

## ⚠️ Consideraciones Legales y Éticas

### IMPORTANTE:
1. **YouTube prohíbe scraping no autorizado** en sus Términos de Servicio
2. **Usa la API oficial** siempre que sea posible
3. **Respeta robots.txt**: YouTube tiene restricciones en su robots.txt
4. **Límites de cuota**: La API tiene límites (10,000 unidades/día por defecto)

### Mejores Prácticas:
- ✅ Usar API oficial (YouTube Data API v3) cuando sea posible
- ✅ Respetar límites de cuota (10,000 unidades/día)
- ✅ Usar delays responsables (1-2 segundos entre requests)
- ✅ Solo extraer datos públicos
- ✅ No almacenar información personal
- ✅ Solo para fines académicos/educativos
- ⚠️ Evitar scraping automatizado del sitio web principal

## 🔍 Selectores CSS para YouTube (2025)

### Videos en Lista/Canal:
```css
/* Contenedor de video */
ytd-video-renderer
div#dismissible

/* Título */
a#video-title
h3 a[href*="/watch"]

/* Canal */
ytd-channel-name a
#channel-name a
.ytd-channel-name a

/* Vistas y fecha */
span#metadata-line
span.style-scope.ytd-video-meta-block

/* Thumbnail */
img.yt-img-shadow
img[src*="i.ytimg.com"]
ytd-thumbnail img

/* Duración */
span.ytd-thumbnail-overlay-time-status-renderer

/* Descripción */
ytd-video-renderer #description-text
```

### Página de Video Individual:
```css
/* Título */
h1.ytd-watch-metadata yt-formatted-string

/* Canal */
ytd-channel-name a

/* Vistas */
span.view-count

/* Likes (desde 2025 no visible, solo API) */
button[aria-label*="like"]

/* Descripción */
ytd-expander #description

/* Comentarios */
ytd-comment-thread-renderer
```

## 📝 Formato de Datos Esperado

```python
{
    'platform': 'youtube',
    'title': 'Título del video',
    'description': 'Descripción del video',
    'channel': 'Nombre del canal',
    'channel_id': 'UCxxxxx',
    'url': 'https://www.youtube.com/watch?v=xxxxx',
    'video_id': 'xxxxx',
    'thumbnail': 'https://i.ytimg.com/vi/xxxxx/hqdefault.jpg',
    'views': 123456,
    'likes': 1234,
    'comments': 89,
    'duration': '10:30',
    'published_at': '2025-01-15T10:30:00Z',
    'category': 'tecnologia',
    'sentiment': 'positive',
    'hashtags': [],
    'created_at': '2025-01-15T10:30:00Z',
    'scraped_at': '2025-01-15T12:00:00Z'
}
```

## 🚀 Plan de Implementación

1. **Crear YouTubeAPIScraper** (google-api-python-client)
2. **Crear YouTubeSeleniumScraper** (Fallback)
3. **Integrar en social_media_scraper.py**
4. **Actualizar api_server.py** para soportar YouTube
5. **Actualizar frontend** para mostrar YouTube como opción
6. **Agregar YouTube a requirements.txt** (google-api-python-client)

## 📚 Recursos Adicionales

- [YouTube Data API Documentation](https://developers.google.com/youtube/v3)
- [YouTube Data API Quotas](https://developers.google.com/youtube/v3/getting-started#quota)
- [YouTube Data API Python Client](https://github.com/googleapis/google-api-python-client)
- [YouTube Terms of Service](https://www.youtube.com/static?template=terms)

## ⚡ Ventajas de YouTube vs Otras Plataformas

1. **API Oficial Muy Completa**: YouTube Data API v3 es muy robusto
2. **Datos Ricos**: Vistas, likes, comentarios, duración, etc.
3. **Thumbnails**: URLs de imágenes disponibles
4. **Búsqueda Potente**: Puede buscar por query, canal, playlist

## 🎯 Recomendación Final

**Para este proyecto académico:**
1. Implementar YouTubeAPIScraper con YouTube Data API v3 (método principal)
2. Implementar YouTubeSeleniumScraper como fallback (scroll infinito)
3. Priorizar API, usar Selenium solo si no hay credenciales
4. Documentar claramente que es solo para fines académicos















