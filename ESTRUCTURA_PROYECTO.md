# 📁 Estructura del Proyecto

## 🎯 Organización

El proyecto está organizado en una estructura clara y modular:

```
proyecto/
├── backend/                    # Todo el código del backend
│   ├── core/                   # Archivos principales del servidor
│   │   ├── api_server.py      # Servidor Flask principal
│   │   ├── auth_system.py     # Sistema de autenticación
│   │   └── websocket_server.py # Servidor WebSocket
│   │
│   ├── scrapers/               # Todos los scrapers
│   │   ├── hybrid_crawler.py
│   │   ├── optimized_scraper.py
│   │   ├── improved_scraper.py
│   │   ├── intelligent_analyzer.py
│   │   ├── elperuano_scraper.py
│   │   ├── pagination_crawler.py
│   │   ├── social_media_scraper.py
│   │   ├── youtube_api_scraper.py
│   │   ├── reddit_api_scraper.py
│   │   ├── facebook_*.py
│   │   └── auto_scraper*.py
│   │
│   ├── systems/                # Sistemas del backend
│   │   ├── competitive_intelligence_system.py
│   │   ├── subscription_system.py
│   │   ├── trending_predictor_system.py
│   │   ├── ads_system.py
│   │   ├── social_media_db.py
│   │   └── social_media_processor.py
│   │
│   ├── utils/                  # Utilidades
│   │   ├── sentiment_analyzer.py
│   │   └── ai_keyword_analyzer.py
│   │
│   ├── config/                 # Archivos de configuración
│   │   ├── auto_scraping_config.json
│   │   └── site_kb.json
│   │
│   └── scripts/                # Scripts de configuración
│       ├── setup_auto_scraping.py
│       ├── setup_mysql.py
│       ├── migrate_database.py
│       └── ...
│
├── frontend/                   # Aplicación React
│   ├── src/
│   ├── public/
│   └── package.json
│
├── scraped_images/             # Imágenes descargadas (no en git)
├── *.db                        # Bases de datos (no en git)
├── venv/                       # Entorno virtual (no en git)
├── requirements.txt            # Dependencias Python
├── README.md                   # Documentación principal
└── *.sh                        # Scripts de inicio
```

## 🚀 Cómo Iniciar el Proyecto

### Opción 1: Script Automático
```bash
./start_app.sh
```

### Opción 2: Manual
```bash
# Terminal 1 - Backend
source venv/bin/activate
python backend/core/api_server.py

# Terminal 2 - Frontend
cd frontend
npm start
```

## 📝 Notas Importantes

1. **Bases de datos**: Se mantienen en la raíz del proyecto (no en `backend/`)
2. **Configuración**: Los archivos de configuración están en `backend/config/`
3. **Imágenes**: Se guardan en `scraped_images/` (raíz del proyecto)
4. **Importaciones**: Todas las importaciones usan rutas relativas desde `backend/`

## 🔧 Estructura de Importaciones

Las importaciones en `api_server.py` siguen este patrón:

```python
# Sistemas
from backend.core.auth_system import AuthSystem
from backend.systems.competitive_intelligence_system import CompetitiveIntelligenceSystem

# Scrapers
from backend.scrapers.hybrid_crawler import HybridDataCrawler
from backend.scrapers.optimized_scraper import SmartScraper

# Utilidades
from backend.utils.sentiment_analyzer import sentiment_analyzer
from backend.utils.ai_keyword_analyzer import get_ai_suggestions
```

## 📦 Ventajas de esta Estructura

✅ **Organización clara**: Cada tipo de archivo tiene su lugar  
✅ **Fácil mantenimiento**: Es fácil encontrar y modificar código  
✅ **Escalabilidad**: Fácil agregar nuevos módulos  
✅ **Separación de concerns**: Backend y frontend claramente separados  
✅ **Reutilización**: Los módulos pueden importarse fácilmente  

