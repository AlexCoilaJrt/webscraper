# 📦 ¿Qué Archivos Subir a GitHub?

## ✅ **SÍ DEBES SUBIR** (Código y Documentación)

### Código Fuente
- ✅ Todos los archivos `.py` (Python)
- ✅ `requirements.txt` (dependencias)
- ✅ `package.json` (frontend)
- ✅ Archivos de configuración de TypeScript/React

### Documentación
- ✅ `README.md`
- ✅ `MANUAL_DESPLIEGUE.md`
- ✅ `MANUAL_USUARIO.md`
- ✅ Todos los archivos `.md` de documentación
- ✅ `LICENSE`

### Configuración del Proyecto
- ✅ `.gitignore`
- ✅ Scripts de setup (`.sh`) que sean genéricos y útiles para otros usuarios
- ✅ `auto_scraping_config.json` (si no contiene datos sensibles)
- ✅ `site_kb.json` (conocimiento base del sitio)

### Frontend
- ✅ Todo el código fuente de `frontend/src/`
- ✅ `frontend/package.json`
- ✅ `frontend/tsconfig.json`
- ✅ `frontend/public/` (archivos estáticos)

---

## ❌ **NO DEBES SUBIR** (Datos y Configuración Local)

### Bases de Datos
- ❌ `*.db` (todas las bases de datos)
- ❌ `*.sqlite`
- ❌ `*.sqlite3`
- **Razón**: Contienen datos personales y son muy pesadas

### Archivos Temporales de Scraping
- ❌ `facebook_posts_*.json` (datos temporales de scraping)
- ❌ `*_posts_*.json` (cualquier dato temporal)
- ❌ `scraped_images/` (imágenes descargadas)
- **Razón**: Son datos temporales y pueden ser muy pesados

### Logs y Archivos de Proceso
- ❌ `*.log` (todos los logs)
- ❌ `*.pid` (archivos de proceso)
- ❌ `api_server.log`, `backend.log`, `frontend.log`
- **Razón**: Son archivos temporales de ejecución

### Entorno Virtual y Dependencias
- ❌ `venv/` (entorno virtual de Python)
- ❌ `frontend/node_modules/` (dependencias de Node)
- ❌ `__pycache__/` (caché de Python)
- **Razón**: Se generan automáticamente, son pesados y específicos del sistema

### Variables de Entorno
- ❌ `.env`
- ❌ `.env.local`
- ❌ `frontend/.env`
- **Razón**: Contienen claves API, tokens y datos sensibles

### Archivos del Sistema
- ❌ `.DS_Store` (macOS)
- ❌ `Thumbs.db` (Windows)
- ❌ `.vscode/` (configuración del IDE)
- **Razón**: Específicos del sistema operativo o IDE

### Drivers y Binarios
- ❌ `chromedriver*`
- ❌ `geckodriver*`
- **Razón**: Dependen del sistema operativo y se descargan automáticamente

---

## 🤔 **CASOS ESPECIALES** (Depende del Contenido)

### Scripts de Configuración (`.sh`)
- ✅ **SÍ**: Scripts genéricos como `setup_cron.sh`, `start_app.sh`
- ❌ **NO**: Scripts con rutas absolutas o configuración personal

### Archivos de Configuración JSON
- ✅ **SÍ**: `auto_scraping_config.json` (si es una plantilla)
- ❌ **NO**: Si contiene tokens, claves API o datos personales

### Archivos de Backup
- ❌ **NO**: `*.bak`, `*_backup.*`
- **Razón**: Son copias temporales

---

## 📋 **RESUMEN RÁPIDO**

### ✅ Sube esto:
```
✅ Código fuente (.py, .ts, .tsx, .js)
✅ Documentación (.md)
✅ Configuración del proyecto (.gitignore, requirements.txt)
✅ Scripts genéricos (.sh)
✅ Frontend (src/, public/, package.json)
```

### ❌ NO subas esto:
```
❌ Bases de datos (*.db)
❌ Logs (*.log)
❌ Datos temporales (facebook_posts_*.json)
❌ Entorno virtual (venv/, node_modules/)
❌ Variables de entorno (.env)
❌ Archivos del sistema (.DS_Store)
```

---

## 🔧 **Verificación Rápida**

Antes de hacer commit, verifica:

```bash
# Ver qué archivos están siendo rastreados
git status

# Verificar que no hay archivos sensibles
git ls-files | grep -E "\.(db|log|env|json)$"

# Verificar tamaño de archivos grandes
find . -type f -size +1M -not -path "./venv/*" -not -path "./.git/*"
```

---

## 🎯 **Recomendación Final**

**El proyecto SÍ debe subirse a GitHub**, pero solo el código fuente, documentación y configuración genérica. Los datos, logs y archivos temporales deben quedarse en tu máquina local.

El `.gitignore` ya está configurado para excluir automáticamente los archivos que no deben subirse. Solo asegúrate de revisar `git status` antes de hacer commit.

