# 🚀 Guía de Instalación - Web Scraper

## 📋 Requisitos Previos

### Sistema Operativo
- macOS (recomendado)
- Linux
- Windows (con WSL)

### Software Requerido
- Python 3.8+
- Node.js 16+
- MySQL 8.0+
- Git

## 🔧 Instalación Paso a Paso

### 1. Instalar Dependencias del Sistema

#### macOS (usando Homebrew)
```bash
# Instalar Homebrew si no lo tienes
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalar dependencias
brew install python@3.11 node mysql git
```

#### Ubuntu/Debian
```bash
# Actualizar sistema
sudo apt update

# Instalar dependencias
sudo apt install python3.11 python3-pip nodejs npm mysql-server git
```

### 2. Configurar MySQL

#### Iniciar MySQL
```bash
# macOS
brew services start mysql

# Ubuntu/Debian
sudo systemctl start mysql
sudo systemctl enable mysql
```

#### Configurar MySQL
```bash
# Ejecutar configuración segura
sudo mysql_secure_installation

# Crear base de datos
mysql -u root -p
```

En MySQL:
```sql
CREATE DATABASE noticias_db;
CREATE USER 'scraper_user'@'localhost' IDENTIFIED BY 'scraper_pass';
GRANT ALL PRIVILEGES ON noticias_db.* TO 'scraper_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3. Clonar y Configurar el Proyecto

```bash
# Clonar el proyecto (si es un repositorio)
git clone <tu-repositorio>
cd scraping-2

# O si ya tienes el proyecto, navegar a él
cd "/Users/usuario/Documents/scraping 2"
```

### 4. Configurar Backend Python

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate  # macOS/Linux
# o
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Probar configuración de MySQL
python setup_mysql.py

# Probar conexión
python test_mysql.py
```

### 5. Configurar Frontend React

```bash
# Navegar al directorio frontend
cd frontend

# Instalar dependencias
npm install

# Crear archivo de configuración
echo "REACT_APP_API_URL=http://localhost:5000/api" > .env

# Volver al directorio raíz
cd ..
```

### 6. Crear Directorios Necesarios

```bash
# Crear directorio para imágenes
mkdir -p scraped_images

# Verificar permisos
chmod 755 scraped_images
```

## 🚀 Iniciar la Aplicación

### Opción 1: Script Automático (Recomendado)
```bash
# Hacer ejecutable
chmod +x start_app.sh

# Ejecutar
./start_app.sh
```

### Opción 2: Manual

#### Terminal 1 - Backend
```bash
# Activar entorno virtual
source venv/bin/activate

# Iniciar API
python api_server.py
```

#### Terminal 2 - Frontend
```bash
# Navegar a frontend
cd frontend

# Iniciar React
npm start
```

## 🌐 Acceder a la Aplicación

- **Frontend**: http://localhost:3000
- **API**: http://localhost:5000
- **Documentación API**: http://localhost:5000/api/health

## 🔍 Verificar Instalación

### 1. Verificar Backend
```bash
curl http://localhost:5000/api/health
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00",
  "database": "connected"
}
```

### 2. Verificar Frontend
- Abrir http://localhost:3000
- Deberías ver el dashboard del Web Scraper

### 3. Verificar Base de Datos
```bash
mysql -u root -p noticias_db
```

```sql
SHOW TABLES;
-- Deberías ver: articles, images, scraping_stats
```

## 🐛 Solución de Problemas

### Error: "Module not found"
```bash
# Reinstalar dependencias
pip install -r requirements.txt
npm install
```

### Error: "MySQL connection failed"
```bash
# Verificar MySQL
brew services list | grep mysql  # macOS
sudo systemctl status mysql      # Linux

# Reiniciar MySQL
brew services restart mysql      # macOS
sudo systemctl restart mysql     # Linux
```

### Error: "Port already in use"
```bash
# Encontrar proceso usando el puerto
lsof -i :5000  # Backend
lsof -i :3000  # Frontend

# Matar proceso
kill -9 <PID>
```

### Error: "Permission denied"
```bash
# Dar permisos al script
chmod +x start_app.sh

# Dar permisos al directorio de imágenes
chmod 755 scraped_images
```

## 📝 Configuración Adicional

### Variables de Entorno
Crear archivo `.env` en el directorio raíz:
```bash
# Database
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=noticias_db
DB_PORT=3306

# API
API_HOST=0.0.0.0
API_PORT=5000
API_DEBUG=true

# Frontend
REACT_APP_API_URL=http://localhost:5000/api
```

### Configuración de MySQL
Editar `/etc/mysql/mysql.conf.d/mysqld.cnf`:
```ini
[mysqld]
max_connections = 200
innodb_buffer_pool_size = 256M
```

## 🎯 Próximos Pasos

1. **Primer Scraping**: Usar la interfaz web para hacer tu primer scraping
2. **Configurar Sitios**: Agregar URLs de sitios web que quieres scrapear
3. **Monitorear**: Usar el dashboard para ver estadísticas
4. **Personalizar**: Modificar configuraciones según tus necesidades

## 📞 Soporte

Si tienes problemas:
1. Revisar logs en la consola
2. Verificar que todos los servicios estén corriendo
3. Consultar la documentación en README.md
4. Crear un issue en el repositorio

---

**¡Listo para scrapear! 🕷️✨**


