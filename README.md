# 🕷️ Web Scraper Inteligente

Un sistema completo de web scraping con análisis inteligente, paginación automática y exportación de datos. Extrae artículos de múltiples periódicos y los almacena en una base de datos SQLite con interfaz web moderna.

## 📊 Estadísticas del Proyecto

- **📰 Total de artículos extraídos:** 1,088
- **🖼️ Total de imágenes descargadas:** 119
- **📈 Sesiones de scraping:** 74
- **🗞️ Periódicos configurados:** 13
- **🤖 Sistema de scraping automático:** Activo (cada 5 horas)

## 🗞️ Periódicos Soportados

| Periódico | Artículos | Región | Categoría |
|-----------|-----------|--------|-----------|
| **Elmundo** | 324 | Extranjero | Internacional |
| **La Vanguardia** | 150 | Extranjero | Internacional |
| **El Popular** | 129 | Nacional | General |
| **Trome** | 110 | Nacional | General |
| **Ojo** | 102 | Nacional | General |
| **Diario Sin Fronteras** | 66 | Nacional | Regional |
| **El Comercio** | 57 | Nacional | General |
| **America** | 34 | Nacional | General |
| **Dario Sin Fronteras** | 33 | Nacional | Regional |
| **El popular** | 32 | Nacional | General |
| **Nytimes** | 27 | Extranjero | Internacional |
| **Peru21** | 18 | Nacional | General |
| **El Peruano** | 6 | Nacional | Economía |

## ✨ Características Principales

### 🧠 Análisis Inteligente
- **Detección automática** del mejor método de scraping
- **Análisis de página** (JavaScript, SPA, paginación, lazy loading)
- **Recomendación inteligente** con nivel de confianza

### 🔄 Scraping Automático
- **Paginación automática** para extraer todos los artículos
- **Sistema de cron** configurado para ejecutar cada 5 horas
- **Múltiples métodos** de scraping (Hybrid, Optimized, Improved, Selenium)

### 📊 Gestión de Datos
- **Base de datos SQLite** para almacenamiento local
- **Exportación a Excel** con formato profesional
- **Filtros avanzados** por periódico, categoría y región
- **Búsqueda de texto** en títulos y contenido

### 🎨 Interfaz Moderna
- **Frontend React** con Material-UI
- **Dashboard profesional** con estadísticas en tiempo real
- **Galería de imágenes** con vista previa
- **Gráficos interactivos** para análisis de datos

## 🛠️ Tecnologías Utilizadas

### Backend
- **Python 3.11+**
- **Flask** - Framework web
- **SQLite** - Base de datos
- **Selenium** - Automatización de navegador
- **BeautifulSoup** - Parsing HTML
- **Requests** - Cliente HTTP
- **Pandas** - Manipulación de datos
- **OpenPyXL** - Exportación Excel

### Frontend
- **React 18**
- **TypeScript**
- **Material-UI** - Componentes UI
- **Chart.js** - Gráficos
- **Axios** - Cliente HTTP

### Herramientas
- **WebDriver Manager** - Gestión automática de drivers
- **Cron** - Programación de tareas
- **MySQL Connector** - Conexión MySQL (opcional)

## 📦 Instalación

### Prerrequisitos
- Python 3.11 o superior
- Node.js 16 o superior
- npm o yarn
- Git

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

## 🚀 Uso

### Iniciar el Sistema

#### 1. Backend (Terminal 1)
```bash
python api_server.py
```
El servidor se ejecutará en `http://localhost:5001`

#### 2. Frontend (Terminal 2)
```bash
cd frontend
npm start
```
La aplicación se abrirá en `http://localhost:3000`

### Configurar Scraping Automático

#### 1. Activar Cron (macOS/Linux)
```bash
# El sistema ya está configurado para ejecutarse cada 5 horas
crontab -l  # Verificar configuración
```

#### 2. Configurar Periódicos
Edita `auto_scraping_config.json` para agregar/modificar periódicos:

```json
{
  "auto_scraping": {
    "enabled": true,
    "schedules": [
      {
        "name": "El Comercio - Cada 5 horas",
        "url": "https://elcomercio.pe/",
        "method": "auto",
        "max_articles": 30,
        "max_images": 15,
        "category": "General",
        "newspaper": "El Comercio",
        "region": "Nacional",
        "cron_schedule": "0 */5 * * *",
        "enabled": true
      }
    ]
  }
}
```

## 📖 Manual de Usuario

### 🏠 Dashboard Principal
- **Vista general** de estadísticas
- **Gestión de periódicos** con opciones de eliminación
- **Botón de limpieza** de todos los datos
- **Estado del sistema** en tiempo real

### 🔍 Scraping Manual
1. Ve a la pestaña **"SCRAPING"**
2. Ingresa la **URL** del sitio web
3. Selecciona el **método** (recomendado: "Análisis Inteligente")
4. Configura **parámetros** (artículos, imágenes, categoría, etc.)
5. Haz clic en **"INICIAR SCRAPING"**

### 📰 Gestión de Artículos
1. Ve a la pestaña **"ARTÍCULOS"**
2. **Filtra** por periódico, categoría o región
3. **Busca** en títulos y contenido
4. **Exporta** a Excel con un clic
5. **Visualiza** artículos individuales

### 🖼️ Galería de Imágenes
1. Ve a la pestaña **"IMÁGENES"**
2. **Navega** por todas las imágenes descargadas
3. **Filtra** por periódico o fecha
4. **Descarga** imágenes individuales

### 📊 Estadísticas
1. Ve a la pestaña **"ESTADÍSTICAS"**
2. **Visualiza** gráficos de rendimiento
3. **Analiza** tendencias temporales
4. **Revisa** sesiones de scraping

## ⚙️ Configuración Avanzada

### Métodos de Scraping

#### 🧠 Análisis Inteligente (Recomendado)
- Detecta automáticamente el mejor método
- Analiza características de la página
- Proporciona recomendación con confianza

#### 🔄 Híbrido
- Combina Requests y Selenium
- Ideal para sitios con JavaScript
- Maneja contenido dinámico

#### ⚡ Optimizado
- Usa paralelización
- Más rápido para sitios estáticos
- Ideal para sitios con muchos artículos

#### 🛠️ Mejorado
- Método robusto sin Selenium
- Buena compatibilidad
- Menor uso de recursos

#### 🌐 Selenium
- Navegador completo
- Para sitios muy complejos
- Mayor uso de recursos

### Configuración de Base de Datos

#### SQLite (Por defecto)
```python
DB_PATH = "news_database.db"
```

#### MySQL (Opcional)
```python
DB_PATH = "mysql://usuario:contraseña@localhost:3306/noticias_db"
```

## 🔧 Solución de Problemas

### Error: "Connection refused"
```bash
# Verificar que el backend esté corriendo
curl http://localhost:5001/api/status
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
```

### Scraping automático no funciona
```bash
# Verificar cron
crontab -l

# Verificar logs
tail -f auto_scraping.log
```

## 📁 Estructura del Proyecto

```
web-scraper-inteligente/
├── 📁 frontend/                 # Aplicación React
│   ├── 📁 src/
│   │   ├── 📁 components/       # Componentes reutilizables
│   │   ├── 📁 pages/           # Páginas principales
│   │   └── 📁 services/        # Servicios API
│   └── package.json
├── 📁 images/                  # Imágenes descargadas
├── 📄 api_server.py           # Servidor Flask principal
├── 📄 hybrid_crawler.py       # Scraper híbrido
├── 📄 optimized_scraper.py    # Scraper optimizado
├── 📄 improved_scraper.py     # Scraper mejorado
├── 📄 intelligent_analyzer.py # Analizador inteligente
├── 📄 pagination_crawler.py   # Crawler de paginación
├── 📄 auto_scraper_standalone.py # Scraper automático
├── 📄 auto_scraping_config.json # Configuración automática
├── 📄 news_database.db        # Base de datos SQLite
├── 📄 requirements.txt        # Dependencias Python
└── 📄 README.md              # Este archivo
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

**Tu Nombre**
- GitHub: [@tu-usuario](https://github.com/tu-usuario)
- Email: tu-email@ejemplo.com

## 🙏 Agradecimientos

- **BeautifulSoup** por el parsing HTML
- **Selenium** por la automatización de navegador
- **Material-UI** por los componentes React
- **Chart.js** por las visualizaciones
- **Flask** por el framework web

---

## 📞 Soporte

Si tienes problemas o preguntas:

1. **Revisa** la sección de solución de problemas
2. **Consulta** los issues existentes en GitHub
3. **Crea** un nuevo issue con detalles del problema
4. **Contacta** al autor por email

---

⭐ **¡Si te gusta este proyecto, no olvides darle una estrella en GitHub!** ⭐