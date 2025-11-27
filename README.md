# 🕷️ Web Scraper 

Un sistema completo de web scraping con análisis inteligente, análisis de sentimientos, sistema de anuncios, chatbot con LLM, gestión de usuarios y suscripciones. Extrae artículos de múltiples periódicos y los almacena en una base de datos SQLite con interfaz web moderna.

## ⚡ Inicio Rápido

¿Quieres empezar rápido? Sigue estos pasos:

```bash
# 1. Clonar el repositorio
git clone https://github.com/AlexCoilaJrt/webscraper.git
cd webscraper

# 2. Configurar backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configurar frontend
cd frontend
npm install
cd ..

# 4. Iniciar el sistema
# Terminal 1 - Backend
python api_server.py

# Terminal 2 - Frontend
cd frontend
npm start
```

**Acceder a la aplicación:**
- Frontend: http://localhost:3001
- Backend API: http://localhost:5001

**Credenciales por defecto:**
- Usuario: `admin`
- Contraseña: `AdminSecure2024!`

> ⚠️ **Nota**: El sistema funciona sin LLM. Solo el chatbot no funcionará sin configuración adicional. Ver sección [Configurar LLM](#4-configurar-llm-opcional---solo-para-chatbot) para habilitar el chatbot.

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
- **Asistente conversacional** integrado con LLM (Ollama/OpenRouter/Groq/Hugging Face)
- **Búsqueda inteligente** de artículos por texto, fecha o tema
- **Resúmenes automáticos** de noticias
- **Consulta de planes** y límites de suscripción
- **Detección automática de fechas**: soporta "hoy", "esta semana", "este mes", rangos personalizados
- **Prompts rápidos** para consultas comunes
- **Configuración flexible**: Ollama (local, gratuito), OpenRouter, Groq, o Hugging Face (API externa)
- **Sistema de fallback inteligente**: Si el LLM configurado falla, el sistema automáticamente:
  1. Intenta APIs gratuitas sin key (Together AI, Perplexity, DeepInfra)
  2. Si fallan, intenta el proveedor configurado (Groq, Hugging Face, OpenRouter, Ollama)
  3. Si el proveedor configurado falla, intenta Hugging Face como fallback automático
  4. Si todo falla o hay timeout (8 segundos), usa un sistema de respuestas inteligentes basado en el contexto del portal
- **Siempre funcional**: El chatbot siempre responderá, incluso si todos los LLMs fallan, usando respuestas contextuales inteligentes

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

### 🔮 Trending Topics Predictor
- **Predicción de temas trending** 24-48 horas antes de que se vuelvan virales
- **Análisis de patrones históricos** de los últimos 14 días
- **Métricas de confianza** y potencial viral
- **Extracción automática** de palabras clave relevantes
- **Categorización automática** (General, Tecnología, Política, etc.)
- **Dashboard visual** con métricas en tiempo real
- **Sistema de límites** por plan de suscripción

### 🔍 Competitive Intelligence
- **Monitoreo de competidores** en tiempo real
- **Detección automática** de menciones en artículos
- **Análisis de sentimiento** de menciones
- **Sistema de alertas** automáticas
- **Dashboard de métricas** y estadísticas
- **Sugerencias de IA** para keywords relevantes
- **Análisis de artículos existentes** sin necesidad de nuevo scraping

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
- **Python 3.11 o superior** - [Descargar Python](https://www.python.org/downloads/)
- **Node.js 16 o superior** - [Descargar Node.js](https://nodejs.org/)
- **npm o yarn** - Viene incluido con Node.js
- **Git** - [Descargar Git](https://git-scm.com/downloads)
- **Chrome o Chromium** - Requerido para Selenium (el sistema descarga ChromeDriver automáticamente)
- **Ollama (opcional)** - Solo si quieres usar el chatbot con LLM local

### 1. Clonar el Repositorio
```bash
git clone https://github.com/AlexCoilaJrt/webscraper.git
cd webscraper
```

### 2. Configurar Backend (Python)
```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En macOS/Linux:
source venv/bin/activate
# En Windows:
# venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

**Nota**: Si tienes problemas con alguna dependencia, intenta actualizar pip:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configurar Frontend (React)
```bash
cd frontend
npm install
```

**Nota**: Si tienes problemas con npm, intenta:
```bash
npm cache clean --force
npm install
```

### 4. Configurar Variables de Entorno (Opcional)

El sistema funciona sin configuración adicional, pero puedes personalizar opciones creando un archivo `.env` en la raíz del proyecto:

```bash
# Crear archivo .env (opcional)
touch .env  # En Windows: crear archivo .env manualmente
```

**Variables opcionales para el Chatbot con LLM:**
```env
# Opción 1: Ollama (Local, Gratuito)
LLM_PROVIDER=ollama
LLM_MODEL=llama3

# Opción 2: OpenRouter (API Externa)
LLM_PROVIDER=openrouter
LLM_MODEL=deepseek/deepseek-chat-v3.1:free
OPENROUTER_API_KEY=sk-or-tu-api-key

# Opción 3: Groq (API Externa, Rápida)
LLM_PROVIDER=groq
LLM_MODEL=mixtral-8x7b-32768
GROQ_API_KEY=tu-groq-api-key

# Opción 4: Hugging Face (Gratuito, sin API key requerida)
LLM_PROVIDER=huggingface
LLM_MODEL=mistralai/Mistral-7B-Instruct-v0.2
HUGGINGFACE_API_KEY=opcional-para-mejores-limites
```

**Nota**: El sistema funciona perfectamente sin LLM. El chatbot **siempre funcionará** gracias a su sistema de fallback inteligente:
- Si el LLM configurado falla, intenta automáticamente otras APIs gratuitas
- Si todas fallan, usa respuestas contextuales inteligentes basadas en el conocimiento del portal
- Todas las demás funcionalidades están disponibles independientemente del estado del LLM

### 5. Configurar LLM (Opcional - Solo para Chatbot)

#### Opción 1: Ollama (Recomendado - Gratuito y Local)
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows: Descargar desde https://ollama.ai

# Iniciar servidor
ollama serve

# En otra terminal, descargar modelo
ollama pull llama3
```

#### Opción 2: OpenRouter (API Externa)
1. Crear cuenta en [OpenRouter](https://openrouter.ai/)
2. Obtener API key
3. Agregar al archivo `.env`:
```env
LLM_PROVIDER=openrouter
LLM_MODEL=deepseek/deepseek-chat-v3.1:free
OPENROUTER_API_KEY=sk-or-tu-api-key
```

#### Opción 3: Hugging Face (Gratuito, sin API key)
El sistema usa Hugging Face por defecto. No requiere configuración adicional, pero puedes agregar una API key para mejores límites:
```env
LLM_PROVIDER=huggingface
LLM_MODEL=mistralai/Mistral-7B-Instruct-v0.2
HUGGINGFACE_API_KEY=opcional
```

Ver [CONFIGURAR_LLM.md](./CONFIGURAR_LLM.md) o [CONFIGURAR_LLM_GRATIS.md](./CONFIGURAR_LLM_GRATIS.md) para más detalles.

### 6. Inicializar Base de Datos

El sistema creará automáticamente todas las bases de datos necesarias al iniciar por primera vez:

```bash
# Activar entorno virtual si no está activo
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

# Iniciar el servidor (creará las bases de datos automáticamente)
python api_server.py
```

**Bases de datos que se crean automáticamente:**
- `news_database.db` - Artículos y noticias
- `auth_database.db` - Usuarios y autenticación
- `subscription_database.db` - Suscripciones y planes
- `social_media.db` - Datos de redes sociales (si se usa)
- `competitive_intelligence.db` - Inteligencia competitiva (si se usa)
- `trending_predictions.db` - Predicciones trending (si se usa)

**Usuario administrador por defecto:**
- Se crea automáticamente al iniciar por primera vez
- **Usuario**: `admin`
- **Contraseña**: `AdminSecure2024!`
- **Email**: `admin@webscraper.com`

⚠️ **IMPORTANTE**: Cambia la contraseña del admin después del primer inicio en producción.

### 7. Verificar Instalación

Después de completar los pasos anteriores, verifica que todo esté funcionando:

```bash
# 1. Verificar que el backend esté corriendo
curl http://localhost:5001/api/health
# Debería responder: {"status": "ok"}

# 2. Verificar que el frontend esté accesible
# Abre en el navegador: http://localhost:3001
# Deberías ver la página de login

# 3. Iniciar sesión con las credenciales por defecto
# Usuario: admin
# Contraseña: AdminSecure2024!
```

**Si todo funciona correctamente:**
- ✅ Verás el Dashboard principal
- ✅ Podrás acceder a todas las funcionalidades
- ✅ El sistema estará listo para usar

**Si hay problemas:**
- Revisa la sección [Solución de Problemas](#-solución-de-problemas)
- Verifica que todos los prerrequisitos estén instalados
- Asegúrate de que los puertos 5001 y 3001 no estén ocupados

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
La aplicación se abrirá automáticamente en `http://localhost:3001` (puerto configurado en `package.json`)

**Nota**: Si el puerto 3001 está ocupado, React te preguntará si quieres usar otro puerto.

### Credenciales por Defecto

El sistema crea automáticamente un usuario administrador al iniciar por primera vez:

- **Usuario**: `admin`
- **Contraseña**: `AdminSecure2024!`
- **Email**: `admin@webscraper.com`

⚠️ **IMPORTANTE**: 
- Estas credenciales se crean automáticamente solo si no existe ningún usuario en la base de datos
- **Cambia la contraseña** después del primer inicio en producción
- Puedes crear más usuarios desde el panel de administración una vez que inicies sesión

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
4. **Recibe respuestas** generadas por LLM o sistema de fallback inteligente

**Sistema de Fallback del Chatbot:**
- El chatbot **siempre responderá**, incluso si el LLM falla
- Si el LLM configurado no está disponible, el sistema automáticamente:
  1. Intenta APIs gratuitas sin key
  2. Intenta el proveedor configurado
  3. Usa Hugging Face como fallback automático
  4. Si todo falla, usa respuestas contextuales inteligentes basadas en el conocimiento del portal
- Las respuestas de fallback son contextuales y útiles, aunque no tan elaboradas como las del LLM

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

### 🔮 Trending Topics Predictor
1. Ve a la pestaña **"TRENDING PREDICTOR"**
2. **Genera predicciones** de temas que serán trending en 24-48 horas
3. **Visualiza métricas**:
   - Nivel de confianza de la predicción
   - Potencial viral
   - Tiempo estimado para trending
   - Tasa de crecimiento
4. **Analiza palabras clave** relevantes extraídas automáticamente
5. **Consulta historial** de predicciones anteriores
6. **Filtra por categoría** (General, Tecnología, Política, etc.)

**Nota**: Requiere análisis de patrones históricos. El sistema analiza los últimos 14 días de artículos para generar predicciones.

### 🔍 Competitive Intelligence
1. Ve a la pestaña **"COMPETITIVE INTELLIGENCE"**
2. **Agrega competidores**:
   - Ingresa nombre del competidor
   - Define keywords o dominios a monitorear
   - El sistema detecta automáticamente menciones
3. **Visualiza analytics**:
   - Total de menciones por competidor
   - Distribución por periódico
   - Análisis de sentimiento de menciones
   - Tendencias temporales
4. **Configura alertas** para recibir notificaciones de nuevas menciones
5. **Analiza artículos existentes** automáticamente al agregar un competidor
6. **Recibe sugerencias de IA** para keywords relevantes

**Nota**: El sistema analiza automáticamente los últimos 10,000 artículos al agregar un nuevo competidor.

### ⭐ Favoritos
1. Ve a la pestaña **"FAVORITOS"**
2. **Marca artículos** como favoritos desde la lista de artículos
3. **Accede rápidamente** a tus artículos guardados
4. **Filtra y busca** dentro de tus favoritos
5. **Elimina favoritos** cuando ya no los necesites

### 🗄️ Configuración de Base de Datos (Admin)
1. Ve a la pestaña **"BASE DE DATOS"**
2. **Visualiza estadísticas**:
   - Total de artículos por periódico
   - Fechas de primer y último artículo
   - Total de imágenes
3. **Limpia datos** por periódico específico
4. **Gestiona bases de datos** del sistema

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

## 📦 ¿Por qué hay tantos archivos en el repositorio?

Este proyecto contiene una gran cantidad de archivos debido a su naturaleza como sistema completo de scraping y análisis. A continuación se explica la razón de cada tipo de archivo:

### 🔧 Archivos de Código Fuente (Esenciales)

#### Scripts de Scraping (Múltiples Métodos)
- **`intelligent_analyzer.py`** - Analizador inteligente que detecta el mejor método
- **`hybrid_crawler.py`** - Scraper híbrido (combina Requests + Selenium)
- **`optimized_scraper.py`** - Scraper optimizado con paralelización
- **`improved_scraper.py`** - Scraper mejorado sin Selenium
- **`auto_scraper_standalone.py`** - Scraper automático independiente
- **`elperuano_scraper.py`** - Scraper específico para El Peruano
- **`elperuano_selenium_scraper.py`** - Versión Selenium para El Peruano

**Razón**: Cada método de scraping tiene ventajas para diferentes tipos de sitios web. El sistema prueba automáticamente el mejor método según las características de cada página.

#### Scripts de Redes Sociales (Proyecto Académico)
- **`facebook_graph_scraper.py`** - Scraper de Facebook usando Graph API
- **`facebook_manual_scraper.py`** - Scraper manual de Facebook
- **`reddit_api_scraper.py`** - Scraper de Reddit usando API
- **`reddit_selenium_scraper.py`** - Scraper de Reddit con Selenium
- **`youtube_api_scraper.py`** - Scraper de YouTube usando API
- **`youtube_selenium_scraper.py`** - Scraper de YouTube con Selenium
- **`social_media_scraper.py`** - Scraper unificado de redes sociales
- **`social_media_processor.py`** - Procesador de datos de redes sociales
- **`social_media_db.py`** - Gestión de base de datos de redes sociales

**Razón**: Cada red social requiere métodos diferentes de scraping. Algunas tienen APIs oficiales, otras requieren Selenium. Estos scripts permiten extraer datos de múltiples plataformas.

#### Sistemas Especializados
- **`api_server.py`** - Servidor Flask principal (API REST)
- **`auth_system.py`** - Sistema de autenticación y permisos
- **`subscription_system.py`** - Sistema de suscripciones y planes
- **`sentiment_analyzer.py`** - Analizador de sentimientos
- **`ads_system.py`** - Sistema de gestión de anuncios
- **`trending_predictor_system.py`** - Predictor de temas trending
- **`competitive_intelligence_system.py`** - Sistema de inteligencia competitiva
- **`ai_keyword_analyzer.py`** - Analizador de palabras clave con IA

**Razón**: Cada sistema es un módulo independiente que puede funcionar por separado o integrarse con el sistema principal.

#### Scripts de Configuración y Utilidades
- **`configure_mysql.py`** - Configuración de MySQL (opcional)
- **`setup_auto_scraping.py`** - Configuración de scraping automático
- **`manage_auto_scraping.py`** - Gestión de scraping automático
- **`migrate_database.py`** - Migración de base de datos
- **`init_competitive_intelligence.py`** - Inicialización de inteligencia competitiva
- **`test_*.py`** - Scripts de prueba para diferentes componentes

**Razón**: Estos scripts facilitan la configuración, migración y pruebas del sistema.

#### Scripts de Inicio y Gestión
- **`start_app.sh`** - Inicia backend y frontend automáticamente
- **`start_simple.sh`** - Inicio simplificado
- **`start_websocket.sh`** - Inicia servidor WebSocket
- **`clean_and_restart.sh`** - Limpia y reinicia el sistema
- **`restart_system.sh`** - Reinicia el sistema
- **`restart_clean.sh`** - Reinicio con limpieza
- **`force_restart.sh`** - Reinicio forzado
- **`run_auto_scraping.sh`** - Ejecuta scraping automático

**Razón**: Diferentes scripts para diferentes escenarios de uso (desarrollo, producción, limpieza, etc.).

### 📄 Archivos de Datos Generados

#### Archivos JSON de Redes Sociales
- **`facebook_posts_*.json`** (múltiples archivos) - Datos extraídos de Facebook durante pruebas

**Razón**: Estos archivos son resultado de pruebas y scraping de redes sociales. Son datos de ejemplo que demuestran la funcionalidad del sistema. Pueden eliminarse si no se necesitan.

#### Imágenes Descargadas
- **`scraped_images/`** (1,500+ imágenes) - Imágenes descargadas de los artículos scraped

**Razón**: El sistema descarga automáticamente las imágenes de los artículos para mostrarlas en la galería. Estas imágenes son parte de los datos extraídos y se almacenan localmente.

### 📚 Archivos de Documentación

#### Documentación Principal
- **`README.md`** - Este archivo (documentación principal)
- **`CAMBIOS_SESION.md`** - Registro de cambios de la sesión actual
- **`INSTALACION.md`** - Guía de instalación detallada
- **`MANUAL_USUARIO.md`** - Manual de usuario completo

#### Documentación de Funcionalidades Específicas
- **`CONFIGURAR_LLM.md`** - Configuración del chatbot con LLM
- **`CONFIGURAR_LLM_GRATIS.md`** - Configuración de LLM gratuito
- **`CONFIGURAR_TOKEN.md`** - Configuración de tokens de API
- **`PASOS_CREAR_TOKEN.md`** - Pasos para crear tokens
- **`README_AUTH.md`** - Documentación del sistema de autenticación
- **`README_SUBSCRIPTIONS.md`** - Documentación de suscripciones
- **`README_SOCIAL_MEDIA.md`** - Documentación de redes sociales
- **`README_SOCIAL_MEDIA_SCRAPING.md`** - Guía de scraping de redes sociales

#### Documentación de Investigación
- **`FACEBOOK_SCRAPING_RESEARCH.md`** - Investigación sobre scraping de Facebook
- **`REDDIT_SCRAPING_RESEARCH.md`** - Investigación sobre scraping de Reddit
- **`YOUTUBE_SCRAPING_RESEARCH.md`** - Investigación sobre scraping de YouTube
- **`INSTRUCCIONES_GRAPH_API.md`** - Instrucciones para Graph API

#### Documentación de Negocio
- **`MONETIZACION_DETALLADA.md`** - Estrategia de monetización
- **`PLAN_NEGOCIO_MONETIZACION.md`** - Plan de negocio y monetización
- **`DESCRIPCION_ANALISIS.md`** - Descripción del análisis de sentimientos
- **`solucion_permisos.md`** - Solución de problemas de permisos

**Razón**: Documentación completa para facilitar el uso, configuración y mantenimiento del sistema.

### 🗄️ Bases de Datos

- **`news_database.db`** - Base de datos principal de artículos
- **`auth_database.db`** - Base de datos de autenticación
- **`subscription_database.db`** - Base de datos de suscripciones
- **`social_media.db`** - Base de datos de redes sociales
- **`competitive_intelligence.db`** - Base de datos de inteligencia competitiva
- **`trending_predictions.db`** - Base de datos de predicciones trending
- **`*.db`** (múltiples) - Bases de datos de respaldo y pruebas

**Razón**: Cada módulo tiene su propia base de datos para mantener la separación de responsabilidades y facilitar el mantenimiento.

### 🧹 Limpieza de Archivos (Opcional)

Si deseas reducir el tamaño del repositorio, puedes eliminar:

1. **Archivos JSON de prueba**: `facebook_posts_*.json` (si no los necesitas)
2. **Imágenes descargadas**: `scraped_images/` (se regenerarán al hacer scraping)
3. **Bases de datos de respaldo**: `*_backup.db`, `news_database_backup.db`
4. **Logs**: `*.log` (se regeneran automáticamente)
5. **Archivos PID**: `*.pid` (archivos temporales de procesos)

**Nota**: Los archivos `.gitignore` ya está configurado para ignorar bases de datos, logs y archivos temporales en futuros commits.

### 📊 Resumen de Archivos por Categoría

| Categoría | Cantidad Aprox. | Propósito |
|-----------|----------------|-----------|
| **Scripts Python** | ~30 | Lógica del sistema |
| **Scripts Shell** | ~8 | Automatización y gestión |
| **Componentes React** | ~20 | Interfaz de usuario |
| **Páginas React** | ~15 | Páginas principales |
| **Documentación** | ~20 | Guías y manuales |
| **Imágenes** | 1,500+ | Contenido descargado |
| **JSON de prueba** | ~15 | Datos de ejemplo |
| **Bases de datos** | ~8 | Almacenamiento de datos |

**Total**: ~1,600+ archivos (incluyendo imágenes y datos generados)

### ✅ Archivos Esenciales vs Opcionales

#### ✅ Esenciales (No eliminar)
- Todos los scripts `.py` de scraping y sistemas
- Todos los componentes y páginas de React
- `requirements.txt`, `package.json`
- Archivos de configuración (`.json`, `.env.example`)
- Documentación principal (`README.md`, `INSTALACION.md`)

#### ⚠️ Opcionales (Pueden eliminarse)
- `facebook_posts_*.json` - Datos de prueba
- `scraped_images/` - Se regeneran automáticamente
- Bases de datos de respaldo (`*_backup.db`)
- Logs (`*.log`)
- Archivos PID (`*.pid`)

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
# El sistema descarga automáticamente ChromeDriver usando webdriver-manager
# Si falla, verifica que tengas Chrome o Chromium instalado:

# macOS
brew install --cask google-chrome

# Linux (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install google-chrome-stable

# Windows: Descargar desde https://www.google.com/chrome/

# Si el problema persiste, el sistema intentará usar undetected-chromedriver
# que descarga el driver automáticamente
```

### Error: "Module not found"
```bash
# Reinstalar dependencias
pip install -r requirements.txt
cd frontend && npm install
```

### Chatbot no funciona o responde con fallback
```bash
# El chatbot SIEMPRE funciona, incluso sin LLM configurado.
# Si el LLM falla, usa un sistema de fallback inteligente.

# 1. Verificar estado del LLM
curl http://localhost:5001/api/llm/status

# 2. Si usa Ollama, verificar que esté corriendo
curl http://localhost:11434/api/tags

# 3. Sistema de Fallback del Chatbot:
#    - Si el LLM configurado falla, intenta automáticamente APIs gratuitas
#    - Si todas fallan, usa respuestas contextuales inteligentes
#    - El chatbot SIEMPRE responderá, aunque sea con fallback

# 4. Para mejorar las respuestas del chatbot, configura un LLM:
#    - CONFIGURAR_LLM_GRATIS.md - Para opciones gratuitas
#    - CONFIGURAR_LLM.md - Para configuración completa
#    - O instalar Ollama: https://ollama.ai

# 5. Orden de intentos del sistema:
#    1. APIs gratuitas sin key (Together AI, Perplexity, DeepInfra)
#    2. Proveedor configurado (Groq, Hugging Face, OpenRouter, Ollama)
#    3. Hugging Face como fallback automático
#    4. Sistema de respuestas inteligentes (siempre disponible)
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
