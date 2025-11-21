# 🕷️ Web Scraper Inteligente

Un sistema completo de web scraping con análisis inteligente, análisis de sentimientos, sistema de anuncios, chatbot con LLM, gestión de usuarios y suscripciones. Extrae artículos de múltiples periódicos y los almacena en una base de datos SQLite con interfaz web moderna.

## 🌟 Nuevas Funcionalidades

### ✨ Sistema de Análisis de Sentimientos
- **Análisis avanzado** de sentimientos (positivo, negativo, neutral) usando VADER y TextBlob
- **Detección de emociones**: enojo, alegría, miedo, tristeza, sorpresa, disgusto
- **Polarización de opiniones**: alta, media, baja
- **Evolución temporal**: gráficos de sentimiento a lo largo del tiempo
- **Comparación entre medios**: análisis comparativo de sentimientos por periódico
- **Comparación con comentarios virales**: análisis de noticias vs comentarios sociales
- **Alertas inteligentes**: notificaciones cuando el sentimiento es muy negativo
- **Integración con anuncios**: colocación inteligente de anuncios según sentimiento

### 💬 Chatbot Inteligente con LLM
- **Asistente conversacional** integrado con LLM (Ollama/OpenRouter)
- **Búsqueda inteligente** de artículos por texto, fecha o tema
- **Resúmenes automáticos** de noticias
- **Consulta de planes** y límites de suscripción
- **Detección automática de fechas**: soporta "hoy", "esta semana", "este mes", rangos personalizados
- **Prompts rápidos** para consultas comunes
- **Configuración flexible**: Ollama (local, gratuito) o OpenRouter (API externa)

### 📢 Sistema de Anuncios (Ads)
- **Gestión de campañas publicitarias** completa
- **Anuncios inteligentes** basados en sentimiento del contenido
- **Carrusel de anuncios** en el Dashboard (rotación automática cada 3 segundos)
- **Métricas y analytics** de rendimiento de anuncios
- **Integración con sentimientos**: evitar anuncios en contenido muy negativo
- **Sistema de tracking**: clicks, impresiones, conversiones
- **Recomendaciones automáticas** de colocación

### 💭 Comentarios Virales
- **Sección de comentarios virales** en el Dashboard
- **Comentarios de usuarios** sobre temas virales
- **Sistema de likes** para comentarios
- **Análisis de sentimiento** automático de comentarios
- **Filtrado por tema** y popularidad
- **Integración con análisis de sentimientos**

### 🔐 Sistema de Autenticación y Permisos
- **Autenticación completa** con JWT tokens
- **Sistema de roles**: Admin, Usuario
- **Permisos dinámicos**: el admin puede otorgar permisos específicos a usuarios
- **Gestión de usuarios** completa desde el panel de admin
- **Control granular** de acceso a funcionalidades
- **Sistema independiente de planes**: permisos no afectan suscripciones

### 💳 Sistema de Suscripciones
- **Planes de suscripción**: Freemium, Premium, Enterprise
- **Límites por plan**: artículos, scraping, chat, exportación
- **Gestión de pagos** (panel admin)
- **Características por plan**:
  - **Freemium**: Básico, análisis de sentimientos básico
  - **Premium**: Análisis avanzado, comparación con comentarios, alertas
  - **Enterprise**: Todo lo anterior + integración inteligente de anuncios

### 📊 Análisis Avanzado
- **Dashboard de análisis completo** con múltiples visualizaciones
- **Tendencias temporales** de contenido
- **Análisis de sentimientos** por periódico y categoría
- **Top categorías y periódicos** más activos
- **Nube de palabras** con las palabras más frecuentes
- **Comparación de periódicos** con métricas detalladas
- **Estadísticas detalladas** por medio de comunicación

### 📱 Redes Sociales (Proyecto Académico)
- **Scraping de redes sociales**: Twitter/X, Facebook, Reddit, YouTube
- **Análisis de sentimientos** en posts sociales
- **Clasificación por categorías** automática
- **Dashboard de redes sociales** con visualizaciones
- **⚠️ Solo para fines académicos y educativos**

## 📊 Estadísticas del Proyecto

- **📰 Total de artículos extraídos:** 1,600+
- **🖼️ Total de imágenes descargadas:** 1,500+
- **📈 Sesiones de scraping:** 100+
- **🗞️ Periódicos configurados:** 10
- **🤖 Sistema de scraping automático:** Activo (cada 5 minutos)
- **🌐 Métodos de scraping:** 5 (Análisis Inteligente, Híbrido, Optimizado, Mejorado, Selenium)
- **💾 Base de datos:** SQLite con múltiples tablas especializadas
- **🔄 Última actualización:** Sistema en funcionamiento continuo

## 🗞️ Periódicos Configurados

### 📊 Resumen de Periódicos

| Periódico | Región | Categoría | Estado | Artículos/Max | Imágenes/Max |
|-----------|--------|-----------|--------|---------------|--------------|
| **El Comercio** | Nacional | General | ✅ Activo | 50 | 1 |
| **El Popular** | Nacional | General | ✅ Activo | 40 | 1 |
| **Diario Sin Fronteras** | Nacional | Regional | ✅ Activo | 35 | 1 |
| **El Peruano** | Nacional | Economía | ✅ Activo | 40 | 1 |
| **Peru21** | Nacional | General | ✅ Activo | 40 | 1 |
| **Ojo** | Nacional | General | ✅ Activo | 35 | 1 |
| **Trome** | Nacional | General | ✅ Activo | 35 | 1 |
| **El Mundo** | Extranjero | Internacional | ✅ Activo | 50 | 1 |
| **La Vanguardia** | Extranjero | Internacional | ✅ Activo | 50 | 1 |
| **New York Times** | Extranjero | Internacional | ✅ Activo | 40 | 1 |

## ✨ Características Principales

### 🧠 Análisis Inteligente
- **Detección automática** del mejor método de scraping
- **Análisis de página** (JavaScript, SPA, paginación, lazy loading)
- **Recomendación inteligente** con nivel de confianza
- **Detección de idioma** y clasificación regional automática

### 🔄 Scraping Automático
- **Paginación automática** para extraer todos los artículos
- **Sistema de cron** configurado para ejecutar cada 5 minutos
- **Múltiples métodos** de scraping (Análisis Inteligente, Híbrido, Optimizado, Mejorado, Selenium)
- **Scraping independiente** sin necesidad de servidor API
- **Prevención de duplicados** automática

### 📊 Gestión de Datos
- **Base de datos SQLite** para almacenamiento local
- **Exportación a Excel** con formato profesional
- **Filtros avanzados** por periódico, categoría, región, fecha
- **Búsqueda de texto** en títulos y contenido
- **Gestión de periódicos** con eliminación selectiva
- **Limpieza masiva** de datos

### 🎨 Interfaz Moderna
- **Frontend React** con Material-UI v7 y TypeScript
- **Dashboard profesional** con estadísticas en tiempo real
- **Galería de imágenes** con vista previa
- **Gráficos interactivos** (ECharts) para análisis de datos
- **Sistema de notificaciones** en tiempo real
- **Diseño responsivo** y moderno
- **Tema claro/oscuro** configurable

## 🛠️ Tecnologías Utilizadas

### Backend
- **Python 3.11+**
- **Flask** - Framework web REST API
- **SQLite** - Base de datos principal
- **Selenium** - Automatización de navegador
- **BeautifulSoup** - Parsing HTML
- **Requests** - Cliente HTTP
- **Pandas** - Manipulación de datos
- **OpenPyXL** - Exportación Excel
- **SQLAlchemy** - ORM para base de datos
- **VADER Sentiment** - Análisis de sentimientos
- **TextBlob** - Análisis de texto
- **APScheduler** - Programación de tareas
- **JWT** - Autenticación

### Frontend
- **React 19** con TypeScript
- **Material-UI v7** - Componentes UI modernos
- **ECharts** - Gráficos interactivos avanzados
- **Axios** - Cliente HTTP
- **React Router** - Navegación
- **Date-fns** - Manipulación de fechas
- **XLSX** - Exportación de archivos

### LLM (Opcional)
- **Ollama** - LLM local gratuito (recomendado)
- **OpenRouter** - API de LLM externa (alternativa)

## 📦 Instalación

### Prerrequisitos
- Python 3.11 o superior
- Node.js 16 o superior
- npm o yarn
- Git
- Ollama (opcional, para chatbot con LLM)

### 1. Clonar el Repositorio
```bash
git clone https://github.com/AlexCoilaJrt/webscraper.git
cd webscraper
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

### 4. Configurar LLM (Opcional - para Chatbot)
```bash
# Opción 1: Ollama (Recomendado - Gratuito)
brew install ollama  # macOS
ollama serve
ollama pull llama3

# Opción 2: OpenRouter (API Externa)
# Crear archivo .env en la raíz:
# LLM_PROVIDER=openrouter
# LLM_MODEL=deepseek/deepseek-chat-v3.1:free
# OPENROUTER_API_KEY=sk-or-tu-api-key
```

### 5. Inicializar Base de Datos
```bash
# El sistema creará automáticamente todas las bases de datos necesarias
python api_server.py
```

## 🚀 Uso

### Iniciar el Sistema

#### Opción 1: Script de Inicio Automático
```bash
# Ejecutar script que inicia backend y frontend automáticamente
chmod +x start_app.sh
./start_app.sh
```

#### Opción 2: Inicio Manual

##### 1. Backend (Terminal 1)
```bash
python api_server.py
```
El servidor se ejecutará en `http://localhost:5001`

##### 2. Frontend (Terminal 2)
```bash
cd frontend
npm start
```
La aplicación se abrirá en `http://localhost:3000`

### Credenciales por Defecto
- **Usuario Admin**: `admin`
- **Contraseña**: `AdminSecure2024!`

## 📖 Funcionalidades Detalladas

### 🏠 Dashboard Principal
- **Vista general** de estadísticas en tiempo real
- **Carrusel de anuncios** con rotación automática
- **Comentarios virales** de usuarios
- **Estado del scraping** en tiempo real
- **Métricas visuales** con gráficos y tarjetas informativas
- **Acciones rápidas** según permisos del usuario

### 🔍 Scraping Manual
1. Ve a la pestaña **"SCRAPING"**
2. Ingresa la **URL** del sitio web
3. Selecciona el **método** (recomendado: "Análisis Inteligente")
4. Configura **parámetros** (artículos, imágenes, categoría, región, etc.)
5. Haz clic en **"INICIAR SCRAPING"**
6. **Monitorea** el progreso en tiempo real

### 📰 Gestión de Artículos
1. Ve a la pestaña **"ARTÍCULOS"**
2. **Filtra** por periódico, categoría, región o fecha
3. **Filtros de tiempo**: última hora, 24h, 7 días, mes, año, rango personalizado
4. **Busca** en títulos y contenido
5. **Exporta** a Excel con un clic
6. **Visualiza** artículos individuales con comentarios
7. **Paginación** para navegar grandes volúmenes

### 😊 Análisis de Sentimientos
1. Ve a la pestaña **"SENTIMIENTOS"**
2. **Filtra** por categoría, periódico, tema o días
3. **Visualiza** gráficos de:
   - Distribución de sentimientos (positivo/negativo/neutral)
   - Emociones detectadas
   - Polarización de opiniones
   - Evolución temporal
   - Comparación entre medios
   - Comparación con comentarios virales (Premium/Enterprise)
4. **Alertas** de sentimiento negativo (Premium/Enterprise)
5. **Interpretación** automática de resultados

### 📢 Gestión de Anuncios (Admin)
1. Ve a la pestaña **"ANUNCIOS"**
2. **Crea campañas** publicitarias
3. **Gestiona anuncios** por campaña
4. **Visualiza analytics** y métricas
5. **Recibe recomendaciones** de colocación

### 💬 Chatbot Inteligente
1. Haz clic en el **botón flotante de chat** (esquina inferior derecha)
2. **Escribe** tu consulta o usa prompts rápidos
3. **Pregunta** por:
   - Búsqueda de artículos: "buscar noticias sobre Perú"
   - Resúmenes: "resumen selección peruana esta semana"
   - Filtros por fecha: "rpp 2025-01-01 a 2025-12-31"
   - Tu plan: "mi plan"
4. **Recibe respuestas** generadas por LLM

### 👥 Gestión de Usuarios (Admin)
1. Ve a la pestaña **"USUARIOS"**
2. **Crea, edita o elimina** usuarios
3. **Gestiona permisos** dinámicos por usuario
4. **Asigna roles** (admin/usuario)
5. **Visualiza estadísticas** de usuarios

### 💳 Suscripciones
1. Ve a la pestaña **"SUSCRIPCIONES"**
2. **Visualiza** planes disponibles
3. **Consulta** tu plan actual y límites
4. **Gestiona pagos** (admin)

### 📊 Análisis Avanzado
1. Ve a la pestaña **"ANÁLISIS"**
2. **Visualiza** tendencias temporales
3. **Analiza** sentimientos por periódico y categoría
4. **Revisa** top categorías y periódicos
5. **Explora** nube de palabras
6. **Compara** periódicos con métricas detalladas

## ⚙️ Configuración Avanzada

### Métodos de Scraping

#### 🧠 Análisis Inteligente (Recomendado)
- **Detección automática** del mejor método
- **Análisis de página** (JavaScript, SPA, paginación, lazy loading)
- **Recomendación inteligente** con nivel de confianza
- **Detección de idioma** y clasificación regional

#### 🔄 Híbrido
- **Combina Requests y Selenium** para máxima compatibilidad
- **Ideal para sitios con JavaScript** dinámico
- **Maneja contenido** que se carga asincrónicamente
- **Fallback automático** entre métodos

#### ⚡ Optimizado
- **Paralelización** para máximo rendimiento
- **Más rápido** para sitios estáticos
- **Ideal para sitios** con muchos artículos
- **Múltiples workers** simultáneos

#### 🛠️ Mejorado
- **Método robusto** sin Selenium
- **Buena compatibilidad** con la mayoría de sitios
- **Menor uso de recursos** del sistema
- **Headers inteligentes** y manejo de sesiones

#### 🌐 Selenium
- **Navegador completo** con JavaScript
- **Para sitios muy complejos** y SPAs
- **Mayor uso de recursos** pero máxima compatibilidad
- **Soporte completo** para contenido dinámico

### Configuración de LLM

#### Ollama (Recomendado)
```bash
# Instalar Ollama
brew install ollama  # macOS
# O descargar desde: https://ollama.ai

# Iniciar servidor
ollama serve

# Descargar modelo
ollama pull llama3

# Configurar en .env
LLM_PROVIDER=ollama
LLM_MODEL=llama3
```

#### OpenRouter (Alternativa)
```bash
# Crear archivo .env
LLM_PROVIDER=openrouter
LLM_MODEL=deepseek/deepseek-chat-v3.1:free
OPENROUTER_API_KEY=sk-or-tu-api-key-aqui
```

Ver [CONFIGURAR_LLM.md](./CONFIGURAR_LLM.md) para más detalles.

## 📁 Estructura del Proyecto

```
web-scraper-inteligente/
├── 📁 frontend/                    # Aplicación React con TypeScript
│   ├── 📁 src/
│   │   ├── 📁 components/          # Componentes reutilizables
│   │   │   ├── Navbar.tsx          # Barra de navegación
│   │   │   ├── ChatbotWidget.tsx   # Chatbot con LLM
│   │   │   ├── AdsCarousel.tsx     # Carrusel de anuncios
│   │   │   ├── ViralComments.tsx   # Comentarios virales
│   │   │   └── ...
│   │   ├── 📁 pages/               # Páginas principales
│   │   │   ├── Dashboard.tsx      # Dashboard principal
│   │   │   ├── ScrapingControl.tsx # Control de scraping
│   │   │   ├── ArticlesList.tsx   # Lista de artículos
│   │   │   ├── ImagesGallery.tsx  # Galería de imágenes
│   │   │   ├── Analytics.tsx       # Análisis avanzado
│   │   │   ├── SentimentAnalysis.tsx # Análisis de sentimientos
│   │   │   ├── AdsManagement.tsx  # Gestión de anuncios
│   │   │   ├── UserManagement.tsx # Gestión de usuarios
│   │   │   ├── Subscriptions.tsx  # Suscripciones
│   │   │   └── ...
│   │   ├── 📁 services/            # Servicios API
│   │   │   └── api.ts             # Cliente API
│   │   ├── 📁 contexts/           # Contextos React
│   │   │   ├── AuthContext.tsx    # Autenticación
│   │   │   └── ThemeContext.tsx   # Tema
│   │   └── App.tsx                # Componente principal
│   ├── package.json               # Dependencias Node.js
│   └── tsconfig.json              # Configuración TypeScript
├── 📁 scraped_images/             # Imágenes descargadas
├── 📄 api_server.py              # Servidor Flask REST API
├── 📄 auth_system.py              # Sistema de autenticación
├── 📄 subscription_system.py     # Sistema de suscripciones
├── 📄 sentiment_analyzer.py      # Analizador de sentimientos
├── 📄 ads_system.py              # Sistema de anuncios
├── 📄 auto_scraper_standalone.py # Scraper automático independiente
├── 📄 auto_scraping_config.json  # Configuración de scraping automático
├── 📄 hybrid_crawler.py         # Scraper híbrido
├── 📄 optimized_scraper.py      # Scraper optimizado
├── 📄 improved_scraper.py        # Scraper mejorado
├── 📄 intelligent_analyzer.py   # Analizador inteligente
├── 📄 news_database.db          # Base de datos SQLite principal
├── 📄 requirements.txt          # Dependencias Python
├── 📄 .env.example              # Ejemplo de configuración
├── 📄 CONFIGURAR_LLM.md         # Guía de configuración LLM
├── 📄 DESCRIPCION_ANALISIS.md   # Descripción del análisis
└── 📄 README.md                 # Este archivo
```

## 🚀 Funcionalidades Avanzadas

### 🔄 Sistema de Scraping Automático
- **Ejecución programada** cada 5 minutos con cron
- **Scraping independiente** sin necesidad de servidor API
- **Prevención de duplicados** automática
- **Logging detallado** de todas las operaciones
- **Configuración flexible** por periódico

### 🧠 Análisis Inteligente de Páginas
- **Detección automática** de características de página
- **Análisis de JavaScript** y contenido dinámico
- **Detección de paginación** y lazy loading
- **Recomendación de método** con nivel de confianza
- **Clasificación regional** automática (Nacional/Extranjero)

### 📊 Gestión Avanzada de Datos
- **Base de datos SQLite** optimizada con múltiples tablas
- **Exportación a Excel** con formato profesional
- **Filtros múltiples** (periódico, categoría, región, fecha)
- **Búsqueda de texto** en contenido completo
- **Paginación** para grandes volúmenes de datos
- **Comentarios** en artículos

### 🎨 Interfaz de Usuario Moderna
- **Dashboard en tiempo real** con métricas actualizadas
- **Sistema de notificaciones** para eventos importantes
- **Diseño responsivo** compatible con móviles
- **Temas modernos** con Material-UI
- **Gráficos interactivos** (ECharts) para análisis de datos
- **Chatbot flotante** siempre accesible

### 🔧 Herramientas de Administración
- **Gestión de usuarios** con permisos dinámicos
- **Gestión de anuncios** y campañas
- **Limpieza masiva** de datos
- **Configuración de base de datos** MySQL opcional
- **Monitoreo de estado** del sistema
- **Logs detallados** para debugging

## 📈 Planes de Suscripción

### 🆓 Freemium
- ✅ Scraping básico
- ✅ Análisis de sentimientos básico
- ✅ Visualización de artículos
- ✅ Búsqueda y filtros
- ⚠️ Límites: 100 artículos/día, 10 mensajes chat/día

### 💎 Premium
- ✅ Todo lo de Freemium
- ✅ Análisis de sentimientos avanzado
- ✅ Comparación con comentarios virales
- ✅ Alertas de sentimiento negativo
- ✅ Exportación a Excel/CSV
- ⚠️ Límites: 500 artículos/día, 50 mensajes chat/día

### 🏢 Enterprise
- ✅ Todo lo de Premium
- ✅ Integración inteligente de anuncios
- ✅ Sin límites de uso
- ✅ API access
- ✅ Soporte prioritario
- ✅ Personalización avanzada

## 🔧 Solución de Problemas

### Error: "Connection refused"
```bash
# Verificar que el backend esté corriendo
curl http://localhost:5001/api/health
```

### Error: "ChromeDriver not found"
```bash
# El sistema descarga automáticamente el driver
# Si falla, instalar Chrome manualmente
```

### Error: "Module not found"
```bash
# Reinstalar dependencias
pip install -r requirements.txt
cd frontend && npm install
```

### Chatbot no funciona
```bash
# Verificar estado del LLM
curl http://localhost:5001/api/llm/status

# Si usa Ollama, verificar que esté corriendo
curl http://localhost:11434/api/tags
```

### Scraping automático no funciona
```bash
# Verificar cron
crontab -l

# Verificar logs
tail -f auto_scraping.log
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 👨‍💻 Autor

**AlexCoilaJrt**
- GitHub: [@AlexCoilaJrt](https://github.com/AlexCoilaJrt)
- Repositorio: [webscraper](https://github.com/AlexCoilaJrt/webscraper)

## 🙏 Agradecimientos

- **BeautifulSoup** por el parsing HTML
- **Selenium** por la automatización de navegador
- **Material-UI** por los componentes React
- **ECharts** por las visualizaciones avanzadas
- **Flask** por el framework web
- **VADER Sentiment** por el análisis de sentimientos
- **Ollama** por el LLM local gratuito

---

## 📞 Soporte

Si tienes problemas o preguntas:

1. **Revisa** la sección de solución de problemas
2. **Consulta** los issues existentes en GitHub
3. **Crea** un nuevo issue con detalles del problema
4. **Revisa** la documentación adicional:
   - [CONFIGURAR_LLM.md](./CONFIGURAR_LLM.md) - Configuración del chatbot
   - [DESCRIPCION_ANALISIS.md](./DESCRIPCION_ANALISIS.md) - Descripción del análisis
   - [README_AUTH.md](./README_AUTH.md) - Sistema de autenticación
   - [README_SUBSCRIPTIONS.md](./README_SUBSCRIPTIONS.md) - Sistema de suscripciones

---

⭐ **¡Si te gusta este proyecto, no olvides darle una estrella en GitHub!** ⭐
