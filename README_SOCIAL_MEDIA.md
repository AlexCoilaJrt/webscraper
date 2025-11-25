# 📱 Sistema de Web Scraping de Redes Sociales
## PROYECTO ACADÉMICO - Solo para fines educativos

---

## ⚠️ DISCLAIMER IMPORTANTE

Este módulo es **SOLO PARA FINES ACADÉMICOS Y EDUCATIVOS**. 

**IMPORTANTE:**
- ✅ Respeta los términos de servicio de Twitter/X
- ✅ Usa delays responsables (mínimo 3-5 segundos entre requests)
- ✅ Límite máximo de 50 tweets por sesión
- ✅ Solo extrae datos públicos
- ✅ No almacena información personal sensible
- ✅ Este código es para aprendizaje y demostración técnica

---

## 🎯 Funcionalidades Implementadas

### 1. **Extractor de Datos (Twitter/X)**
- ✅ Extracción de tweets públicos
- ✅ Datos extraídos:
  - Texto del tweet
  - Autor (username)
  - Fecha de publicación
  - Likes, Retweets, Respuestas
  - Hashtags
  - URL del tweet

### 2. **Parámetros de Búsqueda**
- ✅ Por hashtag (ej: #tecnologia)
- ✅ Por palabra clave
- ✅ Límite configurable (máximo 50 por ética)
- ✅ Filtro por idioma (español/inglés)

### 3. **Procesamiento de Datos**
- ✅ Limpieza de texto (remover URLs, menciones opcional)
- ✅ Detección automática de idioma
- ✅ Clasificación por categorías:
  - Tecnología
  - Deportes
  - Política
  - Entretenimiento
  - Negocios
  - Salud
  - General
- ✅ Análisis de sentimiento (positivo/negativo/neutral)

### 4. **Almacenamiento**
- ✅ Base de datos SQLite
- ✅ Tabla: `social_media_posts`
- ✅ Campos completos:
  - id, platform, username, text, cleaned_text
  - likes, retweets, replies
  - hashtags, category, sentiment
  - detected_language, url
  - created_at, scraped_at, processed_at

### 5. **Visualización**
- ✅ Dashboard completo en React
- ✅ Lista de posts extraídos
- ✅ Gráficos:
  - Posts por categoría (Bar Chart)
  - Distribución de sentimientos (Pie Chart)
- ✅ Filtros por categoría y sentimiento
- ✅ Estadísticas en tiempo real

### 6. **Medidas Responsables Implementadas**
- ✅ Delay de 5 segundos entre requests
- ✅ Máximo 50 tweets por sesión
- ✅ Código completamente documentado
- ✅ Disclaimers éticos en la interfaz

---

## 📁 Estructura del Proyecto

```
/scraping 2
  /social_media_scraper.py      # Scraper principal de Twitter/X
  /social_media_processor.py     # Procesamiento y análisis
  /social_media_db.py            # Gestión de base de datos
  
  /api_server.py                 # Endpoints API (agregados)
  /frontend/src/pages/
    /SocialMedia.tsx            # Página del frontend
  
  /news_database.db              # Base de datos SQLite (tabla social_media_posts)
```

---

## 🚀 Instalación y Uso

### Requisitos Previos

```bash
# Python 3.10+
python --version

# ChromeDriver instalado y en PATH
# O instalar con:
pip install webdriver-manager
```

### Dependencias

Todas las dependencias ya están en `requirements.txt`:
- ✅ Selenium (ya instalado)
- ✅ BeautifulSoup4 (ya instalado)
- ✅ Flask (ya instalado)
- ✅ SQLite (incluido en Python)

### Configuración

1. **Base de datos**: Se crea automáticamente al iniciar el servidor
2. **Tabla**: Se inicializa en `init_database()` del `api_server.py`
3. **Frontend**: Ya integrado en la aplicación React

---

## 📖 Uso del Sistema

### Desde el Frontend

1. **Acceder a la sección:**
   - Ve a "Redes Sociales" en el menú lateral
   - O directamente: `http://localhost:3001/social-media`

2. **Realizar scraping:**
   - Ingresa un hashtag o palabra clave (ej: `#tecnologia`)
   - Selecciona máximo de posts (máx 50)
   - Opcional: Filtra por idioma
   - Click en "Iniciar Scraping"

3. **Ver resultados:**
   - Los posts aparecen automáticamente
   - Gráficos se actualizan en tiempo real
   - Filtra por categoría o sentimiento

### Desde el Backend (API)

```python
# Ejemplo de uso directo
from social_media_scraper import scrape_twitter
from social_media_processor import process_social_media_data
from social_media_db import SocialMediaDB

# Scraping
tweets = scrape_twitter(
    query="#tecnologia",
    max_tweets=20,
    filter_language="es"
)

# Procesar
processed = process_social_media_data(tweets)

# Guardar
db = SocialMediaDB()
db.save_batch(processed)
```

### Endpoints API

```
POST /api/social-media/scrape
Body: {
  "query": "#tecnologia",
  "max_posts": 50,
  "filter_language": "es"
}

GET /api/social-media/posts
Query params:
  - platform: twitter
  - category: tecnología
  - sentiment: positive
  - limit: 100
  - offset: 0

GET /api/social-media/stats
```

---

## 🔬 Detalles Técnicos

### Arquitectura

```
Frontend (React)
    ↓
API Server (Flask)
    ↓
┌─────────────────────┐
│ SocialMediaScraper  │ → Selenium → Twitter/X
└─────────────────────┘
    ↓
┌─────────────────────┐
│ SocialMediaProcessor│ → Limpieza + Análisis
└─────────────────────┘
    ↓
┌─────────────────────┐
│ SocialMediaDB       │ → SQLite
└─────────────────────┘
```

### Flujo de Datos

1. **Usuario** ingresa query en frontend
2. **Frontend** llama a `/api/social-media/scrape`
3. **Backend** ejecuta `TwitterScraper.search_tweets()`
4. **Selenium** navega Twitter/X y extrae datos
5. **Processor** limpia y analiza los tweets
6. **Database** guarda los posts procesados
7. **Frontend** muestra resultados y gráficos

---

## 📊 Categorías y Análisis

### Categorías Disponibles

- **Tecnología**: IA, software, programación, etc.
- **Deportes**: Fútbol, basquet, olímpicos, etc.
- **Política**: Gobierno, elecciones, leyes, etc.
- **Entretenimiento**: Cine, música, TV, etc.
- **Negocios**: Empresas, mercado, finanzas, etc.
- **Salud**: Medicina, hospitales, tratamientos, etc.
- **General**: Default para otros temas

### Análisis de Sentimiento

- **Positivo**: Palabras como "bueno", "excelente", "amor", etc.
- **Negativo**: Palabras como "malo", "terrible", "odio", etc.
- **Neutral**: Cuando no hay predominio claro

---

## ⚙️ Configuración Avanzada

### Modificar Delays

En `social_media_scraper.py`:
```python
scraper = TwitterScraper(headless=True, delay=5)  # Cambiar delay
```

### Agregar Categorías

En `social_media_processor.py`:
```python
self.category_keywords = {
    'tu_categoria': ['palabra1', 'palabra2', ...],
    ...
}
```

### Modificar Límites

En `api_server.py`:
```python
max_posts = min(data.get('max_posts', 50), 50)  # Cambiar límite
```

---

## 🐛 Solución de Problemas

### Error: ChromeDriver no encontrado

```bash
# Instalar ChromeDriver
pip install webdriver-manager

# O descargar manualmente de:
# https://chromedriver.chromium.org/
```

### Error: No se encuentran tweets

- Verifica que la query sea válida
- Twitter/X puede requerir login para algunas búsquedas
- Intenta con hashtags más populares

### Error: Timeout en scraping

- Aumenta el delay entre requests
- Reduce el máximo de tweets
- Verifica conexión a internet

---

## 📚 Referencias Académicas

Este proyecto demuestra:

1. **Web Scraping Ético**: Delays, límites, respeto a ToS
2. **Procesamiento de Datos**: NLP básico, clasificación
3. **Arquitectura Full-Stack**: React + Flask + SQLite
4. **Análisis de Sentimiento**: Clasificación básica
5. **Visualización de Datos**: Gráficos interactivos

---

## 📝 Notas del Desarrollador

- ✅ Código completamente documentado
- ✅ Comentarios explicativos en cada función
- ✅ Manejo de errores robusto
- ✅ Logging detallado para debugging
- ✅ Estructura modular y extensible

---

## 🎓 Propósito Académico

Este módulo fue desarrollado para:

- ✅ Demostrar técnicas de web scraping
- ✅ Enseñar procesamiento de datos
- ✅ Practicar arquitectura full-stack
- ✅ Aprender análisis de sentimiento básico
- ✅ Entender consideraciones éticas en scraping

---

## 📞 Soporte

Para preguntas o problemas:
1. Revisa los logs del servidor
2. Verifica la consola del navegador
3. Consulta la documentación de Selenium
4. Revisa los términos de servicio de Twitter/X

---

**Última actualización**: Enero 2025
**Versión**: 1.0.0
**Estado**: ✅ Completamente funcional

---

*Este proyecto es solo para fines educativos. Respeta siempre los términos de servicio y las leyes locales.*















