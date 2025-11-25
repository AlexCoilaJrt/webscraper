# 📖 Manual de Usuario - Web Scraper Inteligente

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Instalación y Configuración](#instalación-y-configuración)
3. [Primeros Pasos](#primeros-pasos)
4. [Dashboard Principal](#dashboard-principal)
5. [Scraping Manual](#scraping-manual)
6. [Gestión de Artículos](#gestión-de-artículos)
7. [Galería de Imágenes](#galería-de-imágenes)
8. [Estadísticas y Análisis](#estadísticas-y-análisis)
9. [Configuración de Base de Datos](#configuración-de-base-de-datos)
10. [Scraping Automático](#scraping-automático)
11. [Solución de Problemas](#solución-de-problemas)
12. [Referencia Técnica](#referencia-técnica)

---

## 🎯 Introducción

El **Web Scraper Inteligente** es un sistema completo para extraer, procesar y analizar contenido de sitios web de noticias. Con más de **1,600 artículos** extraídos y **1,500 imágenes** descargadas, el sistema ofrece:

- **Análisis inteligente** de páginas web
- **Scraping automático** programado
- **Interfaz web moderna** con React y TypeScript
- **Gestión avanzada** de datos
- **Exportación** a Excel
- **Múltiples métodos** de extracción

---

## 🛠️ Instalación y Configuración

### Prerrequisitos

- **Python 3.11+**
- **Node.js 16+**
- **npm o yarn**
- **Git**

### 1. Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/web-scraper-inteligente.git
cd web-scraper-inteligente
```

### 2. Configurar Backend (Python)

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar Frontend (React)

```bash
cd frontend
npm install
```

### 4. Inicializar Base de Datos

```bash
# El sistema creará automáticamente la base de datos SQLite
python api_server.py
```

---

## 🚀 Primeros Pasos

### Iniciar el Sistema

#### Opción 1: Script Automático (Recomendado)
```bash
chmod +x start_app.sh
./start_app.sh
```

#### Opción 2: Inicio Manual

**Terminal 1 - Backend:**
```bash
python api_server.py
```
Servidor disponible en: `http://localhost:5001`

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```
Aplicación disponible en: `http://localhost:3000`

### Verificar Instalación

1. Abre `http://localhost:3000` en tu navegador
2. Deberías ver el Dashboard principal
3. Verifica que las estadísticas se carguen correctamente

---

## 🏠 Dashboard Principal

### Descripción General

El Dashboard es el centro de control del sistema, mostrando:

- **Métricas en tiempo real** del sistema
- **Estado del scraping** actual
- **Gestión de periódicos** configurados
- **Acciones rápidas** para navegación

### Componentes del Dashboard

#### 📊 Métricas Principales

| Métrica | Descripción | Valor Actual |
|---------|-------------|--------------|
| **Artículos Extraídos** | Total de artículos en la base de datos | 1,600+ |
| **Imágenes Descargadas** | Total de imágenes almacenadas | 1,500+ |
| **Periódicos Monitoreados** | Fuentes de noticias activas | 10 |
| **Categorías Identificadas** | Tipos de contenido clasificados | 5+ |

#### 🔄 Estado del Scraping

- **Sistema Activo**: Muestra cuando hay scraping en curso
- **Sistema Inactivo**: Estado de reposo, listo para iniciar
- **Progreso en Tiempo Real**: Barra de progreso y estadísticas

#### 🗞️ Gestión de Periódicos

Cada periódico muestra:
- **Nombre** del periódico
- **Cantidad de artículos** extraídos
- **Imágenes descargadas**
- **Fecha de última extracción**
- **Botón de eliminación** selectiva

#### ⚡ Acciones Rápidas

- **Ver Artículos**: Navegar a la lista de artículos
- **Galería de Imágenes**: Ver imágenes descargadas
- **Ver Estadísticas**: Análisis detallado
- **Configurar BD**: Configuración de base de datos

### Funciones Especiales

#### 🗑️ Limpieza de Datos

**Limpieza Total:**
- Elimina todos los artículos
- Elimina todas las imágenes
- Elimina todas las estadísticas
- **⚠️ Acción irreversible**

**Eliminación Selectiva:**
- Elimina datos de un periódico específico
- Mantiene datos de otros periódicos
- **⚠️ Acción irreversible**

#### 🔄 Actualización Automática

- **Botón "ACTUALIZAR AUTOMÁTICO"**
- Ejecuta scraping de todos los periódicos configurados
- Actualiza datos en tiempo real
- Muestra progreso en el dashboard

---

## 🔍 Scraping Manual

### Acceso al Control de Scraping

1. Navega a la pestaña **"SCRAPING"** en el menú
2. O usa el botón **"INICIAR SCRAPING"** en el dashboard

### Configuración de Scraping

#### 📝 Campos de Configuración

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| **URL** | Dirección del sitio web a scrapear | `https://elcomercio.pe/` |
| **Método** | Técnica de extracción | Análisis Inteligente |
| **Máx. Artículos** | Límite de artículos a extraer | 50 |
| **Máx. Imágenes** | Límite de imágenes por artículo | 1 |
| **Categoría** | Clasificación del contenido | General |
| **Periódico** | Nombre de la fuente | El Comercio |
| **Región** | Clasificación geográfica | Nacional |

#### 🧠 Métodos de Scraping

##### 1. Análisis Inteligente (Recomendado)
- **Detección automática** del mejor método
- **Análisis de página** completo
- **Recomendación** con nivel de confianza
- **Detección de idioma** y región

**Características:**
- Analiza JavaScript y contenido dinámico
- Detecta paginación y lazy loading
- Clasifica automáticamente la región
- Proporciona razones para la recomendación

##### 2. Híbrido
- **Combina Requests y Selenium**
- **Ideal para sitios complejos**
- **Maneja contenido dinámico**

**Cuándo usar:**
- Sitios con mucho JavaScript
- Contenido que se carga asincrónicamente
- SPAs (Single Page Applications)

##### 3. Optimizado
- **Paralelización** para máximo rendimiento
- **Múltiples workers** simultáneos
- **Ideal para sitios estáticos**

**Cuándo usar:**
- Sitios con muchos artículos
- Contenido estático
- Necesidad de velocidad máxima

##### 4. Mejorado
- **Sin Selenium** (menor uso de recursos)
- **Buena compatibilidad** general
- **Headers inteligentes**

**Cuándo usar:**
- Sitios estándar de noticias
- Cuando se necesita eficiencia de recursos
- Compatibilidad general

##### 5. Selenium
- **Navegador completo** con JavaScript
- **Máxima compatibilidad**
- **Mayor uso de recursos**

**Cuándo usar:**
- Sitios muy complejos
- SPAs complejas
- Cuando otros métodos fallan

### Proceso de Scraping

#### 1. Análisis de Página (Solo con Análisis Inteligente)

El sistema analiza:
- **Tamaño de página** y tiempo de respuesta
- **Presencia de JavaScript** y frameworks
- **Estructura de enlaces** y paginación
- **Contenido dinámico** y lazy loading
- **Idioma** y características regionales

#### 2. Extracción de Datos

- **Búsqueda de enlaces** de artículos
- **Extracción de contenido** de cada artículo
- **Descarga de imágenes** (si está habilitado)
- **Clasificación** automática de categorías

#### 3. Almacenamiento

- **Guardado en base de datos** SQLite
- **Prevención de duplicados** automática
- **Actualización de estadísticas**
- **Logging** detallado de operaciones

### Monitoreo en Tiempo Real

Durante el scraping, puedes ver:
- **Progreso actual** (artículos procesados)
- **URL actual** siendo procesada
- **Artículos encontrados** hasta el momento
- **Imágenes descargadas**
- **Tiempo transcurrido**

---

## 📰 Gestión de Artículos

### Acceso a la Lista de Artículos

1. Navega a la pestaña **"ARTÍCULOS"** en el menú
2. O usa el botón **"Ver Artículos"** en el dashboard

### Vista de Lista de Artículos

#### 📋 Información Mostrada

| Campo | Descripción |
|-------|-------------|
| **Título** | Título del artículo |
| **Periódico** | Fuente de la noticia |
| **Categoría** | Clasificación del contenido |
| **Región** | Nacional o Extranjero |
| **Fecha** | Fecha de extracción |
| **Imágenes** | Cantidad de imágenes |

#### 🔍 Filtros Disponibles

##### Filtro por Periódico
- **El Comercio** - 324 artículos
- **La Vanguardia** - 150 artículos
- **El Popular** - 129 artículos
- **Trome** - 110 artículos
- **Ojo** - 102 artículos
- **Diario Sin Fronteras** - 66 artículos
- **America** - 34 artículos
- **Nytimes** - 27 artículos
- **Peru21** - 18 artículos
- **El Peruano** - 6 artículos

##### Filtro por Categoría
- **General** - Noticias generales
- **Internacional** - Noticias del extranjero
- **Regional** - Noticias regionales
- **Economía** - Noticias económicas

##### Filtro por Región
- **Nacional** - Noticias de Perú
- **Extranjero** - Noticias internacionales

##### Búsqueda de Texto
- **Búsqueda en títulos**
- **Búsqueda en contenido**
- **Búsqueda en resúmenes**

#### 📄 Paginación

- **20 artículos por página** (configurable)
- **Navegación** con botones anterior/siguiente
- **Información de paginación** (página X de Y)
- **Total de artículos** mostrado

### Funciones de Artículos

#### 👁️ Ver Artículo Completo

Al hacer clic en un artículo:
- **Vista detallada** del contenido completo
- **Información completa** (autor, fecha, etc.)
- **Imágenes asociadas** (si las hay)
- **URL original** del artículo

#### 📊 Exportar a Excel

**Características de la exportación:**
- **Formato profesional** con columnas ajustadas
- **Todos los artículos** o filtrados
- **Información completa** (título, contenido, metadatos)
- **Nombre de archivo** con timestamp
- **Descarga automática** al navegador

**Columnas incluidas:**
- ID, Título, Resumen, Contenido
- Periódico, Categoría, Región
- URL, Fecha de Extracción
- Cantidad de Imágenes

---

## 🖼️ Galería de Imágenes

### Acceso a la Galería

1. Navega a la pestaña **"IMÁGENES"** en el menú
2. O usa el botón **"Galería de Imágenes"** en el dashboard

### Vista de Galería

#### 🖼️ Visualización de Imágenes

- **Vista de cuadrícula** con miniaturas
- **Vista previa** al pasar el mouse
- **Información de imagen** (tamaño, formato, etc.)
- **Filtros** por periódico y fecha

#### 📋 Información de Imágenes

| Campo | Descripción |
|-------|-------------|
| **Archivo** | Nombre del archivo de imagen |
| **Periódico** | Fuente de la imagen |
| **Tamaño** | Dimensiones en píxeles |
| **Formato** | JPG, PNG, WebP, etc. |
| **Peso** | Tamaño en bytes |
| **Fecha** | Fecha de descarga |

#### 🔍 Filtros de Imágenes

- **Por periódico**: Filtrar imágenes por fuente
- **Por fecha**: Rango de fechas de descarga
- **Por formato**: JPG, PNG, WebP, etc.
- **Por tamaño**: Filtrar por dimensiones

#### ⬇️ Descarga de Imágenes

- **Descarga individual**: Clic en imagen
- **Descarga múltiple**: Selección múltiple
- **Información detallada**: Metadatos completos

---

## 📊 Estadísticas y Análisis

### Acceso a Estadísticas

1. Navega a la pestaña **"ESTADÍSTICAS"** en el menú
2. O usa el botón **"Ver Estadísticas"** en el dashboard

### Tipos de Estadísticas

#### 📈 Estadísticas Generales

- **Total de artículos** extraídos
- **Total de imágenes** descargadas
- **Periódicos monitoreados**
- **Categorías identificadas**
- **Regiones cubiertas**

#### 📊 Estadísticas por Periódico

**Top 10 Periódicos por Artículos:**
1. **Elmundo** - 324 artículos
2. **La Vanguardia** - 150 artículos
3. **El Popular** - 129 artículos
4. **Trome** - 110 artículos
5. **Ojo** - 102 artículos
6. **Diario Sin Fronteras** - 66 artículos
7. **El Comercio** - 57 artículos
8. **America** - 34 artículos
9. **Dario Sin Fronteras** - 33 artículos
10. **El popular** - 32 artículos

#### 📋 Estadísticas por Categoría

- **General** - Mayor cantidad de artículos
- **Internacional** - Noticias del extranjero
- **Regional** - Noticias regionales
- **Economía** - Noticias económicas

#### ⏱️ Sesiones de Scraping

**Últimas 10 sesiones:**
- **Fecha y hora** de ejecución
- **URL scrapeada**
- **Artículos encontrados**
- **Imágenes descargadas**
- **Duración** de la sesión
- **Método utilizado**

### Gráficos Interactivos

#### 📊 Gráfico de Barras - Artículos por Periódico
- Visualización clara de la distribución
- Comparación entre periódicos
- Datos actualizados en tiempo real

#### 🥧 Gráfico Circular - Distribución por Categoría
- Porcentajes de cada categoría
- Visualización intuitiva
- Colores diferenciados

#### 📈 Gráfico de Líneas - Tendencias Temporales
- Evolución del scraping en el tiempo
- Picos de actividad
- Tendencias de crecimiento

---

## ⚙️ Configuración de Base de Datos

### Acceso a Configuración

1. Navega a la pestaña **"CONFIGURAR BD"** en el menú
2. O usa el botón **"Configurar BD"** en el dashboard

### Configuraciones Disponibles

#### 🗄️ Base de Datos Actual

**SQLite (Por defecto):**
- **Archivo**: `news_database.db`
- **Ubicación**: Directorio raíz del proyecto
- **Tamaño**: ~50MB (con 1,600+ artículos)
- **Tablas**: articles, images, scraping_stats

#### 🔄 Migración a MySQL (Opcional)

**Configuración MySQL:**
```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'tu_usuario',
    'password': 'tu_contraseña',
    'database': 'noticias_db'
}
```

**Ventajas de MySQL:**
- **Mejor rendimiento** para grandes volúmenes
- **Concurrencia** mejorada
- **Respaldo** más robusto
- **Escalabilidad** superior

#### 💾 Respaldo y Restauración

**Respaldo de SQLite:**
```bash
cp news_database.db news_database_backup_$(date +%Y%m%d).db
```

**Respaldo de MySQL:**
```bash
mysqldump -u usuario -p noticias_db > backup_$(date +%Y%m%d).sql
```

### Gestión de Datos

#### 🗑️ Limpieza de Base de Datos

**Limpieza Total:**
- Elimina todos los registros
- Resetea contadores
- Libera espacio en disco

**Limpieza Selectiva:**
- Elimina por período de tiempo
- Elimina por periódico específico
- Elimina artículos duplicados

#### 📊 Optimización de Base de Datos

**Comandos de optimización:**
```sql
-- SQLite
VACUUM;
ANALYZE;

-- MySQL
OPTIMIZE TABLE articles;
OPTIMIZE TABLE images;
OPTIMIZE TABLE scraping_stats;
```

---

## 🤖 Scraping Automático

### Configuración del Sistema Automático

#### 📅 Programación con Cron

**Configuración actual:**
```bash
# Ejecutar cada 5 minutos
*/5 * * * * cd /ruta/al/proyecto && python auto_scraper_standalone.py
```

**Verificar configuración:**
```bash
crontab -l
```

#### ⚙️ Archivo de Configuración

**Ubicación**: `auto_scraping_config.json`

**Estructura:**
```json
{
  "auto_scraping": {
    "enabled": true,
    "schedules": [
      {
        "name": "El Comercio - Cada 5 minutos",
        "url": "https://elcomercio.pe/",
        "method": "auto",
        "max_articles": 50,
        "max_images": 1,
        "category": "General",
        "newspaper": "El Comercio",
        "region": "Nacional",
        "cron_schedule": "*/5 * * * *",
        "enabled": true
      }
    ]
  }
}
```

### Periódicos Configurados

#### 🇵🇪 Periódicos Nacionales

| Periódico | URL | Artículos/Max | Imágenes/Max | Categoría |
|-----------|-----|---------------|--------------|-----------|
| **El Comercio** | https://elcomercio.pe/ | 50 | 1 | General |
| **El Popular** | https://elpopular.pe/ | 40 | 1 | General |
| **Diario Sin Fronteras** | https://diariosinfronteras.com.pe/ | 35 | 1 | Regional |
| **El Peruano** | https://elperuano.pe/economia | 40 | 1 | Economía |
| **Peru21** | https://peru21.pe/ | 40 | 1 | General |
| **Ojo** | https://ojo.pe/ | 35 | 1 | General |
| **Trome** | https://trome.pe/ | 35 | 1 | General |

#### 🌍 Periódicos Internacionales

| Periódico | URL | Artículos/Max | Imágenes/Max | Categoría |
|-----------|-----|---------------|--------------|-----------|
| **El Mundo** | https://www.elmundo.es/ | 50 | 1 | Internacional |
| **La Vanguardia** | https://www.lavanguardia.com/ | 50 | 1 | Internacional |
| **New York Times** | https://www.nytimes.com/ | 40 | 1 | Internacional |

### Ejecución del Scraping Automático

#### 🚀 Inicio Manual

```bash
# Ejecutar scraping automático
python auto_scraper_standalone.py
```

#### 📊 Monitoreo de Logs

**Archivo de log**: `auto_scraping.log`

**Comandos útiles:**
```bash
# Ver logs en tiempo real
tail -f auto_scraping.log

# Ver últimas 50 líneas
tail -n 50 auto_scraping.log

# Buscar errores
grep "ERROR" auto_scraping.log
```

#### 📈 Estadísticas de Ejecución

**Métricas monitoreadas:**
- **Artículos extraídos** por sesión
- **Imágenes descargadas**
- **Tiempo de ejecución**
- **Errores encontrados**
- **Periódicos procesados**

---

## 🔧 Solución de Problemas

### Problemas Comunes

#### ❌ Error: "Connection refused"

**Causa**: El servidor backend no está ejecutándose

**Solución**:
```bash
# Verificar que el backend esté corriendo
curl http://localhost:5001/api/status

# Reiniciar el servidor
python api_server.py
```

#### ❌ Error: "ChromeDriver not found"

**Causa**: Driver de Chrome no disponible

**Solución**:
```bash
# El sistema descarga automáticamente el driver
# Si falla, instalar Chrome manualmente
brew install --cask google-chrome  # macOS
```

#### ❌ Error: "Module not found"

**Causa**: Dependencias Python no instaladas

**Solución**:
```bash
# Reinstalar dependencias
pip install -r requirements.txt

# Verificar entorno virtual
source venv/bin/activate
```

#### ❌ Scraping automático no funciona

**Causa**: Cron no configurado o permisos incorrectos

**Solución**:
```bash
# Verificar cron
crontab -l

# Verificar logs
tail -f auto_scraping.log

# Verificar permisos
chmod +x auto_scraper_standalone.py
```

#### ❌ Frontend no carga

**Causa**: Dependencias Node.js no instaladas

**Solución**:
```bash
cd frontend
npm install
npm start
```

### Logs y Debugging

#### 📝 Archivos de Log

| Archivo | Propósito |
|---------|-----------|
| `auto_scraping.log` | Logs del scraping automático |
| `api_server.log` | Logs del servidor API |
| `frontend.log` | Logs del frontend React |

#### 🔍 Comandos de Debugging

```bash
# Ver logs del sistema
journalctl -f

# Ver procesos Python
ps aux | grep python

# Ver puertos en uso
lsof -i :5001  # Backend
lsof -i :3000  # Frontend
```

### Optimización de Rendimiento

#### ⚡ Mejoras de Velocidad

**Backend:**
- Usar método "Optimizado" para sitios estáticos
- Aumentar `max_workers` en SmartScraper
- Usar base de datos MySQL para grandes volúmenes

**Frontend:**
- Limitar artículos por página (20-50)
- Usar filtros para reducir datos mostrados
- Habilitar compresión gzip

#### 💾 Optimización de Almacenamiento

**Base de datos:**
```sql
-- Limpiar registros antiguos
DELETE FROM articles WHERE scraped_at < '2024-01-01';

-- Optimizar base de datos
VACUUM;
```

**Imágenes:**
```bash
# Comprimir imágenes existentes
find scraped_images -name "*.jpg" -exec jpegoptim --max=80 {} \;
```

---

## 📚 Referencia Técnica

### Arquitectura del Sistema

#### 🏗️ Componentes Principales

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (React)       │◄──►│   (Flask)       │◄──►│   (SQLite)      │
│   Port: 3000    │    │   Port: 5001    │    │   File: .db     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Browser       │    │   Scrapers      │    │   Images        │
│   (Chrome)      │    │   (5 Methods)   │    │   (Files)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

#### 🔄 Flujo de Datos

1. **Usuario** inicia scraping desde frontend
2. **Frontend** envía request a backend API
3. **Backend** selecciona método de scraping
4. **Scraper** extrae datos del sitio web
5. **Backend** guarda datos en base de datos
6. **Frontend** actualiza interfaz con nuevos datos

### Librerías y Dependencias

#### 🐍 Backend (Python)

| Librería | Versión | Propósito |
|----------|---------|-----------|
| **Flask** | 2.3.3 | Framework web REST API |
| **Flask-CORS** | 4.0.0 | CORS para frontend |
| **requests** | 2.31.0 | Cliente HTTP |
| **beautifulsoup4** | 4.12.2 | Parser HTML |
| **selenium** | 4.15.2 | Automatización navegador |
| **webdriver-manager** | 4.0.1 | Gestión drivers |
| **sqlalchemy** | 2.0.21 | ORM base de datos |
| **pandas** | 2.1.3 | Manipulación datos |
| **openpyxl** | 3.1.2 | Exportación Excel |
| **lxml** | 4.9.3 | Parser XML/HTML rápido |

#### ⚛️ Frontend (React/TypeScript)

| Librería | Versión | Propósito |
|----------|---------|-----------|
| **React** | 19.1.1 | Framework UI |
| **TypeScript** | 4.9.5 | Tipado estático |
| **@mui/material** | 7.3.2 | Componentes UI |
| **@mui/icons-material** | 7.3.2 | Iconos Material |
| **axios** | 1.12.1 | Cliente HTTP |
| **chart.js** | 4.5.0 | Gráficos |
| **react-chartjs-2** | 5.3.0 | Integración React-Chart |
| **react-router-dom** | 7.9.1 | Navegación |
| **date-fns** | 4.1.0 | Manipulación fechas |
| **xlsx** | 0.18.5 | Exportación archivos |

### APIs y Endpoints

#### 🔌 Endpoints del Backend

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/health` | GET | Estado de la API |
| `/api/status` | GET | Estado del scraping |
| `/api/start-scraping` | POST | Iniciar scraping |
| `/api/stop-scraping` | POST | Detener scraping |
| `/api/articles` | GET | Listar artículos |
| `/api/articles/export/excel` | GET | Exportar a Excel |
| `/api/images` | GET | Listar imágenes |
| `/api/stats` | GET | Estadísticas |
| `/api/newspapers` | GET | Listar periódicos |
| `/api/clear-all` | DELETE | Limpiar todos los datos |
| `/api/auto-update` | POST | Actualización automática |

### Base de Datos

#### 🗄️ Estructura de Tablas

**Tabla `articles`:**
```sql
CREATE TABLE articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT,
    summary TEXT,
    author TEXT,
    date TEXT,
    category TEXT,
    newspaper TEXT,
    url TEXT NOT NULL,
    images_found INTEGER DEFAULT 0,
    images_downloaded INTEGER DEFAULT 0,
    images_data TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    article_id TEXT UNIQUE,
    region TEXT DEFAULT 'extranjero'
);
```

**Tabla `images`:**
```sql
CREATE TABLE images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id TEXT,
    url TEXT NOT NULL,
    local_path TEXT,
    alt_text TEXT,
    title TEXT,
    width INTEGER,
    height INTEGER,
    format TEXT,
    size_bytes INTEGER,
    relevance_score INTEGER DEFAULT 0,
    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Tabla `scraping_stats`:**
```sql
CREATE TABLE scraping_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    url_scraped TEXT,
    articles_found INTEGER,
    images_found INTEGER,
    images_downloaded INTEGER,
    duration_seconds INTEGER,
    method_used TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Métodos de Scraping Detallados

#### 🧠 Análisis Inteligente

**Algoritmo de análisis:**
1. **Análisis de página** (tamaño, tiempo respuesta)
2. **Detección de JavaScript** (frameworks, librerías)
3. **Análisis de estructura** (enlaces, paginación)
4. **Detección de contenido dinámico**
5. **Clasificación de idioma** y región
6. **Recomendación** con nivel de confianza

**Criterios de evaluación:**
- **JavaScript pesado** → Recomienda Selenium
- **Paginación compleja** → Recomienda Híbrido
- **Contenido estático** → Recomienda Optimizado
- **Sitio estándar** → Recomienda Mejorado

#### 🔄 Híbrido

**Estrategia:**
1. **Intento con Requests** (rápido)
2. **Fallback a Selenium** si falla
3. **Combinación de resultados**
4. **Optimización** de tiempo total

#### ⚡ Optimizado

**Paralelización:**
- **10 workers** simultáneos
- **Pool de conexiones** HTTP
- **Procesamiento asíncrono**
- **Gestión de memoria** optimizada

#### 🛠️ Mejorado

**Características:**
- **Headers inteligentes** (User-Agent, Accept, etc.)
- **Manejo de sesiones** persistente
- **Detección de enlaces** mejorada
- **Filtrado de contenido** relevante

#### 🌐 Selenium

**Configuración:**
- **Chrome headless** por defecto
- **WebDriver Manager** automático
- **Timeouts** configurables
- **Gestión de recursos** optimizada

---

## 📞 Soporte y Contacto

### 🆘 Obtener Ayuda

1. **Revisa** la sección de solución de problemas
2. **Consulta** los logs del sistema
3. **Verifica** la configuración
4. **Contacta** al desarrollador

### 📧 Información de Contacto

- **Desarrollador**: Tu Nombre
- **Email**: tu-email@ejemplo.com
- **GitHub**: [@tu-usuario](https://github.com/tu-usuario)

### 🔄 Actualizaciones

- **Versión actual**: 2.0
- **Última actualización**: Diciembre 2024
- **Próximas características**: 
  - Soporte para más periódicos
  - Análisis de sentimientos
  - API REST pública
  - Dashboard móvil

---

## 📄 Licencia

Este proyecto está bajo la **Licencia MIT**. Ver el archivo `LICENSE` para más detalles.

---

## 🙏 Agradecimientos

- **BeautifulSoup** por el parsing HTML
- **Selenium** por la automatización de navegador
- **Material-UI** por los componentes React
- **Chart.js** por las visualizaciones
- **Flask** por el framework web
- **React** por el framework frontend

---

⭐ **¡Si te gusta este proyecto, no olvides darle una estrella en GitHub!** ⭐

