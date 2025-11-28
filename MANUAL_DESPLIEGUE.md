# 🚀 Manual de Despliegue Completo - Web Scraper

Guía completa para desplegar el sistema Web Scraper en producción.

---

## 📋 Tabla de Contenidos

1. [Requisitos del Servidor](#requisitos-del-servidor)
2. [Preparación del Servidor](#preparación-del-servidor)
3. [Instalación de Dependencias](#instalación-de-dependencias)
4. [Configuración del Proyecto](#configuración-del-proyecto)
5. [Configuración de Variables de Entorno](#configuración-de-variables-de-entorno)
6. [Configuración de Base de Datos](#configuración-de-base-de-datos)
7. [Construcción del Frontend](#construcción-del-frontend)
8. [Configuración de Servicios del Sistema](#configuración-de-servicios-del-sistema)
9. [Configuración de Nginx (Reverse Proxy)](#configuración-de-nginx-reverse-proxy)
10. [Configuración de SSL/HTTPS](#configuración-de-sslhttps)
11. [Configuración de Firewall](#configuración-de-firewall)
12. [Monitoreo y Logs](#monitoreo-y-logs)
13. [Backup y Recuperación](#backup-y-recuperación)
14. [Actualizaciones](#actualizaciones)
15. [Solución de Problemas](#solución-de-problemas)

---

## 🖥️ Requisitos del Servidor

### Especificaciones Mínimas Recomendadas

- **CPU**: 2 cores mínimo (4 cores recomendado)
- **RAM**: 4GB mínimo (8GB recomendado)
- **Almacenamiento**: 20GB mínimo (SSD recomendado)
- **Sistema Operativo**: Ubuntu 20.04 LTS o superior / Debian 11 o superior
- **Conexión**: Internet estable para scraping

### Software Requerido

- **Python**: 3.11 o superior
- **Node.js**: 16 o superior (18+ recomendado)
- **Nginx**: Para reverse proxy
- **Git**: Para clonar el repositorio
- **Chrome/Chromium**: Para Selenium (se descarga automáticamente)

---

## 🔧 Preparación del Servidor

### 1. Actualizar el Sistema

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y build-essential curl git
```

### 2. Instalar Python 3.11+

```bash
# Ubuntu/Debian
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Verificar instalación
python3.11 --version
```

### 3. Instalar Node.js 18+

```bash
# Usando NodeSource
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Verificar instalación
node --version
npm --version
```

### 4. Instalar Nginx

```bash
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 5. Instalar Chrome/Chromium (para Selenium)

```bash
# Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
sudo apt update
sudo apt install -y google-chrome-stable

# O Chromium (alternativa)
# sudo apt install -y chromium-browser
```

---

## 📦 Instalación de Dependencias

### 1. Crear Usuario para la Aplicación

```bash
# Crear usuario sin privilegios de root
sudo adduser --system --group --home /opt/webscraper webscraper
sudo mkdir -p /opt/webscraper
sudo chown webscraper:webscraper /opt/webscraper
```

### 2. Clonar el Repositorio

```bash
cd /opt/webscraper
sudo -u webscraper git clone https://github.com/AlexCoilaJrt/webscraper.git .
```

### 3. Configurar Backend (Python)

```bash
cd /opt/webscraper

# Crear entorno virtual
sudo -u webscraper python3.11 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configurar Frontend (React)

```bash
cd /opt/webscraper/frontend

# Instalar dependencias
sudo -u webscraper npm install

# Construir para producción
sudo -u webscraper npm run build
```

---

## ⚙️ Configuración del Proyecto

### 1. Crear Estructura de Directorios

```bash
sudo mkdir -p /opt/webscraper/{logs,data,backups}
sudo chown -R webscraper:webscraper /opt/webscraper
```

### 2. Configurar Permisos

```bash
# Dar permisos necesarios
sudo chmod +x /opt/webscraper/start_app.sh
sudo chmod +x /opt/webscraper/*.sh
```

---

## 🔐 Configuración de Variables de Entorno

### 1. Crear Archivo .env

```bash
sudo -u webscraper nano /opt/webscraper/.env
```

### 2. Configuración Básica (.env)

```env
# ============================================
# CONFIGURACIÓN DEL SERVIDOR
# ============================================
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=tu_clave_secreta_muy_larga_y_compleja_aqui_cambiar_en_produccion
JWT_SECRET_KEY=tu_jwt_secret_key_muy_larga_y_compleja_aqui

# ============================================
# CONFIGURACIÓN DE PUERTOS
# ============================================
BACKEND_PORT=5001
FRONTEND_PORT=3001

# ============================================
# CONFIGURACIÓN DE BASE DE DATOS
# ============================================
# SQLite (por defecto)
DATABASE_PATH=/opt/webscraper/data/news_database.db

# MySQL (opcional - descomentar si usas MySQL)
# MYSQL_HOST=localhost
# MYSQL_PORT=3306
# MYSQL_USER=webscraper
# MYSQL_PASSWORD=tu_password_seguro
# MYSQL_DATABASE=webscraper_db

# ============================================
# CONFIGURACIÓN DE LLM (Chatbot)
# ============================================
# Opción 1: Ollama (Local, Gratuito)
LLM_PROVIDER=ollama
LLM_MODEL=llama3

# Opción 2: OpenRouter (API Externa)
# LLM_PROVIDER=openrouter
# LLM_MODEL=deepseek/deepseek-chat-v3.1:free
# OPENROUTER_API_KEY=sk-or-tu-api-key

# Opción 3: Groq (API Externa, Rápida)
# LLM_PROVIDER=groq
# LLM_MODEL=mixtral-8x7b-32768
# GROQ_API_KEY=tu-groq-api-key

# Opción 4: Hugging Face (Gratuito, sin API key requerida)
# LLM_PROVIDER=huggingface
# LLM_MODEL=mistralai/Mistral-7B-Instruct-v0.2
# HUGGINGFACE_API_KEY=opcional-para-mejores-limites

# ============================================
# CONFIGURACIÓN DE SEGURIDAD
# ============================================
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
CORS_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com

# ============================================
# CONFIGURACIÓN DE LOGS
# ============================================
LOG_LEVEL=INFO
LOG_FILE=/opt/webscraper/logs/api_server.log
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=10

# ============================================
# CONFIGURACIÓN DE SCRAPING
# ============================================
SCRAPING_INTERVAL=300
MAX_ARTICLES_PER_SCRAPE=100
MAX_IMAGES_PER_SCRAPE=50

# ============================================
# CONFIGURACIÓN DE BACKUP
# ============================================
BACKUP_ENABLED=True
BACKUP_INTERVAL=86400
BACKUP_RETENTION_DAYS=30
BACKUP_PATH=/opt/webscraper/backups
```

### 3. Generar Claves Secretas

```bash
# Generar SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generar JWT_SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**⚠️ IMPORTANTE**: Cambia todas las claves secretas en producción. No uses las claves de ejemplo.

---

## 🗄️ Configuración de Base de Datos

### Opción 1: SQLite (Por Defecto - Recomendado para Inicio)

```bash
# Las bases de datos se crean automáticamente al iniciar
# Solo asegúrate de que el directorio tenga permisos
sudo mkdir -p /opt/webscraper/data
sudo chown -R webscraper:webscraper /opt/webscraper/data
```

### Opción 2: MySQL (Recomendado para Producción)

```bash
# Instalar MySQL
sudo apt install -y mysql-server

# Configurar MySQL
sudo mysql_secure_installation

# Crear base de datos y usuario
sudo mysql -u root -p << EOF
CREATE DATABASE webscraper_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'webscraper'@'localhost' IDENTIFIED BY 'tu_password_seguro';
GRANT ALL PRIVILEGES ON webscraper_db.* TO 'webscraper'@'localhost';
FLUSH PRIVILEGES;
EXIT;
EOF

# Actualizar .env con credenciales MySQL
```

---

## 🏗️ Construcción del Frontend

### 1. Construir para Producción

```bash
cd /opt/webscraper/frontend

# Construir aplicación React
sudo -u webscraper npm run build

# Verificar que se creó la carpeta build
ls -la build/
```

### 2. Configurar Variables de Entorno del Frontend

```bash
# Crear archivo .env.production en frontend
sudo -u webscraper nano /opt/webscraper/frontend/.env.production
```

```env
REACT_APP_API_URL=https://tu-dominio.com/api
REACT_APP_ENV=production
```

---

## 🔄 Configuración de Servicios del Sistema

### 1. Crear Servicio Systemd para Backend

```bash
sudo nano /etc/systemd/system/webscraper-backend.service
```

```ini
[Unit]
Description=Web Scraper Backend API
After=network.target

[Service]
Type=simple
User=webscraper
Group=webscraper
WorkingDirectory=/opt/webscraper
Environment="PATH=/opt/webscraper/venv/bin"
ExecStart=/opt/webscraper/venv/bin/python /opt/webscraper/api_server.py
Restart=always
RestartSec=10
StandardOutput=append:/opt/webscraper/logs/backend.log
StandardError=append:/opt/webscraper/logs/backend.error.log

[Install]
WantedBy=multi-user.target
```

### 2. Crear Servicio Systemd para Frontend (Opcional - si usas servidor Node)

```bash
sudo nano /etc/systemd/system/webscraper-frontend.service
```

```ini
[Unit]
Description=Web Scraper Frontend
After=network.target webscraper-backend.service

[Service]
Type=simple
User=webscraper
Group=webscraper
WorkingDirectory=/opt/webscraper/frontend
Environment="NODE_ENV=production"
Environment="PORT=3001"
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10
StandardOutput=append:/opt/webscraper/logs/frontend.log
StandardError=append:/opt/webscraper/logs/frontend.error.log

[Install]
WantedBy=multi-user.target
```

**Nota**: En producción, es mejor servir el frontend desde Nginx en lugar de Node.js.

### 3. Habilitar y Iniciar Servicios

```bash
# Recargar systemd
sudo systemctl daemon-reload

# Habilitar servicios
sudo systemctl enable webscraper-backend
# sudo systemctl enable webscraper-frontend  # Solo si usas Node para frontend

# Iniciar servicios
sudo systemctl start webscraper-backend
# sudo systemctl start webscraper-frontend

# Verificar estado
sudo systemctl status webscraper-backend
```

### 4. Comandos Útiles

```bash
# Ver logs
sudo journalctl -u webscraper-backend -f

# Reiniciar servicio
sudo systemctl restart webscraper-backend

# Detener servicio
sudo systemctl stop webscraper-backend

# Ver estado
sudo systemctl status webscraper-backend
```

---

## 🌐 Configuración de Nginx (Reverse Proxy)

### 1. Crear Configuración de Nginx

```bash
sudo nano /etc/nginx/sites-available/webscraper
```

```nginx
# Redirigir HTTP a HTTPS
server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;
    
    # Redirigir todo a HTTPS
    return 301 https://$server_name$request_uri;
}

# Configuración HTTPS
server {
    listen 443 ssl http2;
    server_name tu-dominio.com www.tu-dominio.com;

    # Certificados SSL (configurar después con Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/tu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tu-dominio.com/privkey.pem;
    
    # Configuración SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Tamaño máximo de archivos
    client_max_body_size 100M;

    # Logs
    access_log /var/log/nginx/webscraper-access.log;
    error_log /var/log/nginx/webscraper-error.log;

    # Servir Frontend (construido)
    location / {
        root /opt/webscraper/frontend/build;
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache";
    }

    # API Backend
    location /api {
        proxy_pass http://localhost:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # WebSocket (si se usa)
    location /ws {
        proxy_pass http://localhost:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Archivos estáticos
    location /static {
        alias /opt/webscraper/frontend/build/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 2. Habilitar Sitio

```bash
# Crear enlace simbólico
sudo ln -s /etc/nginx/sites-available/webscraper /etc/nginx/sites-enabled/

# Eliminar configuración por defecto (opcional)
sudo rm /etc/nginx/sites-enabled/default

# Verificar configuración
sudo nginx -t

# Recargar Nginx
sudo systemctl reload nginx
```

---

## 🔒 Configuración de SSL/HTTPS

### 1. Instalar Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 2. Obtener Certificado SSL

```bash
# Obtener certificado y configurar Nginx automáticamente
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com

# O solo obtener certificado
sudo certbot certonly --nginx -d tu-dominio.com -d www.tu-dominio.com
```

### 3. Renovación Automática

```bash
# Certbot configura la renovación automática
# Verificar con:
sudo certbot renew --dry-run
```

### 4. Actualizar Configuración de Nginx

Después de obtener el certificado, actualiza la configuración de Nginx con las rutas correctas de los certificados.

---

## 🔥 Configuración de Firewall

### 1. Configurar UFW (Ubuntu Firewall)

```bash
# Permitir SSH (importante antes de habilitar firewall)
sudo ufw allow 22/tcp

# Permitir HTTP y HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Habilitar firewall
sudo ufw enable

# Verificar estado
sudo ufw status
```

### 2. Configurar iptables (Alternativa)

```bash
# Permitir puertos necesarios
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -i lo -j ACCEPT
sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
sudo iptables -P INPUT DROP

# Guardar reglas
sudo iptables-save > /etc/iptables/rules.v4
```

---

## 📊 Monitoreo y Logs

### 1. Configurar Rotación de Logs

```bash
sudo nano /etc/logrotate.d/webscraper
```

```
/opt/webscraper/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 webscraper webscraper
    sharedscripts
    postrotate
        systemctl reload webscraper-backend > /dev/null 2>&1 || true
    endscript
}
```

### 2. Monitoreo con systemd

```bash
# Ver logs en tiempo real
sudo journalctl -u webscraper-backend -f

# Ver últimos 100 líneas
sudo journalctl -u webscraper-backend -n 100

# Ver logs desde hoy
sudo journalctl -u webscraper-backend --since today
```

### 3. Monitoreo de Recursos

```bash
# Instalar herramientas de monitoreo
sudo apt install -y htop iotop

# Ver uso de recursos
htop
```

---

## 💾 Backup y Recuperación

### 1. Script de Backup Automático

```bash
sudo nano /opt/webscraper/scripts/backup.sh
```

```bash
#!/bin/bash

BACKUP_DIR="/opt/webscraper/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Crear directorio de backup si no existe
mkdir -p $BACKUP_DIR

# Backup de bases de datos
echo "Iniciando backup de bases de datos..."
tar -czf $BACKUP_DIR/databases_$DATE.tar.gz /opt/webscraper/data/*.db

# Backup de configuración
echo "Iniciando backup de configuración..."
tar -czf $BACKUP_DIR/config_$DATE.tar.gz /opt/webscraper/.env /opt/webscraper/auto_scraping_config.json

# Backup de imágenes (opcional)
# echo "Iniciando backup de imágenes..."
# tar -czf $BACKUP_DIR/images_$DATE.tar.gz /opt/webscraper/scraped_images

# Eliminar backups antiguos
find $BACKUP_DIR -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completado: $DATE"
```

```bash
# Dar permisos de ejecución
sudo chmod +x /opt/webscraper/scripts/backup.sh
sudo chown webscraper:webscraper /opt/webscraper/scripts/backup.sh
```

### 2. Configurar Cron para Backups Automáticos

```bash
sudo -u webscraper crontab -e
```

```cron
# Backup diario a las 2:00 AM
0 2 * * * /opt/webscraper/scripts/backup.sh >> /opt/webscraper/logs/backup.log 2>&1
```

### 3. Restaurar desde Backup

```bash
# Detener servicios
sudo systemctl stop webscraper-backend

# Restaurar bases de datos
tar -xzf /opt/webscraper/backups/databases_YYYYMMDD_HHMMSS.tar.gz -C /

# Restaurar configuración
tar -xzf /opt/webscraper/backups/config_YYYYMMDD_HHMMSS.tar.gz -C /

# Reiniciar servicios
sudo systemctl start webscraper-backend
```

---

## 🔄 Actualizaciones

### 1. Script de Actualización

```bash
sudo nano /opt/webscraper/scripts/update.sh
```

```bash
#!/bin/bash

set -e

echo "Iniciando actualización del sistema..."

# Detener servicios
sudo systemctl stop webscraper-backend

# Backup antes de actualizar
/opt/webscraper/scripts/backup.sh

# Ir al directorio del proyecto
cd /opt/webscraper

# Actualizar código
sudo -u webscraper git pull origin main

# Actualizar dependencias del backend
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Actualizar dependencias del frontend
cd frontend
sudo -u webscraper npm install
sudo -u webscraper npm run build

# Reiniciar servicios
sudo systemctl start webscraper-backend

echo "Actualización completada"
```

```bash
# Dar permisos
sudo chmod +x /opt/webscraper/scripts/update.sh
```

### 2. Proceso de Actualización Manual

```bash
# 1. Hacer backup
/opt/webscraper/scripts/backup.sh

# 2. Detener servicios
sudo systemctl stop webscraper-backend

# 3. Actualizar código
cd /opt/webscraper
sudo -u webscraper git pull origin main

# 4. Actualizar dependencias
source venv/bin/activate
pip install -r requirements.txt
cd frontend && npm install && npm run build

# 5. Reiniciar servicios
sudo systemctl start webscraper-backend

# 6. Verificar que todo funciona
sudo systemctl status webscraper-backend
curl http://localhost:5001/api/health
```

---

## 🛠️ Solución de Problemas

### Problema: Backend no inicia

```bash
# Ver logs
sudo journalctl -u webscraper-backend -n 50

# Verificar sintaxis de Python
cd /opt/webscraper
source venv/bin/activate
python -m py_compile api_server.py

# Verificar puerto
sudo netstat -tlnp | grep 5001
```

### Problema: Frontend no carga

```bash
# Verificar que el build existe
ls -la /opt/webscraper/frontend/build

# Verificar configuración de Nginx
sudo nginx -t
sudo systemctl status nginx

# Ver logs de Nginx
sudo tail -f /var/log/nginx/webscraper-error.log
```

### Problema: Error de permisos

```bash
# Corregir permisos
sudo chown -R webscraper:webscraper /opt/webscraper
sudo chmod -R 755 /opt/webscraper
```

### Problema: Base de datos bloqueada

```bash
# Verificar procesos usando la base de datos
sudo lsof /opt/webscraper/data/*.db

# Reiniciar servicio
sudo systemctl restart webscraper-backend
```

### Problema: Certificado SSL expirado

```bash
# Renovar certificado
sudo certbot renew

# Reiniciar Nginx
sudo systemctl reload nginx
```

---

## 📝 Checklist de Despliegue

### Pre-Despliegue

- [ ] Servidor configurado con especificaciones mínimas
- [ ] Dominio configurado y apuntando al servidor
- [ ] Puertos 80 y 443 abiertos en firewall
- [ ] Usuario `webscraper` creado

### Instalación

- [ ] Python 3.11+ instalado
- [ ] Node.js 18+ instalado
- [ ] Nginx instalado y configurado
- [ ] Chrome/Chromium instalado
- [ ] Repositorio clonado
- [ ] Dependencias instaladas (backend y frontend)
- [ ] Frontend construido para producción

### Configuración

- [ ] Archivo `.env` creado con todas las variables
- [ ] Claves secretas generadas y configuradas
- [ ] Base de datos inicializada
- [ ] Servicios systemd creados y habilitados
- [ ] Nginx configurado como reverse proxy
- [ ] SSL/HTTPS configurado con Let's Encrypt

### Post-Despliegue

- [ ] Servicios corriendo correctamente
- [ ] Frontend accesible en https://tu-dominio.com
- [ ] API respondiendo en https://tu-dominio.com/api/health
- [ ] Login funcionando con credenciales por defecto
- [ ] Backups automáticos configurados
- [ ] Monitoreo de logs configurado
- [ ] Firewall configurado correctamente

---

## 🔗 Enlaces Útiles

- **Repositorio**: https://github.com/AlexCoilaJrt/webscraper
- **Documentación Nginx**: https://nginx.org/en/docs/
- **Let's Encrypt**: https://letsencrypt.org/
- **Systemd**: https://www.freedesktop.org/software/systemd/man/systemd.service.html

---

## 📞 Soporte

Si encuentras problemas durante el despliegue:

1. Revisa los logs: `sudo journalctl -u webscraper-backend -f`
2. Verifica la configuración de Nginx: `sudo nginx -t`
3. Consulta la sección de [Solución de Problemas](#solución-de-problemas)
4. Abre un issue en GitHub con detalles del problema

---

## ⚠️ Notas Importantes

1. **Seguridad**: Cambia todas las claves secretas en producción
2. **Backups**: Configura backups automáticos antes de poner en producción
3. **Monitoreo**: Configura alertas para monitorear el estado del sistema
4. **Actualizaciones**: Mantén el sistema actualizado regularmente
5. **SSL**: Usa siempre HTTPS en producción
6. **Firewall**: Configura el firewall correctamente para proteger el servidor

---

**¡Despliegue exitoso! 🎉**


