# 🔑 CÓMO CONFIGURAR EL TOKEN DE FACEBOOK GRAPH API

## 📋 PASO 1: OBTENER EL TOKEN

### 1.1. Ve al Graph API Explorer
👉 https://developers.facebook.com/tools/explorer/

### 1.2. Selecciona o crea una App
- Si no tienes una app, crea una nueva:
  - Click en "Create App"
  - Selecciona tipo "Business"
  - Completa el formulario

### 1.3. Genera el Access Token
- En el Graph API Explorer, selecciona tu app en el menú desplegable
- Click en **"Generate Access Token"**
- Selecciona estos permisos:
  - ✅ `pages_read_engagement`
  - ✅ `pages_show_list`
- Copia el token generado (será algo como: `EAAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)

⚠️ **Nota:** Este token temporal expira en 1-2 horas. Para producción, convierte a token de larga duración.

---

## ⚙️ PASO 2: CONFIGURAR EL TOKEN

### OPCIÓN A: Variable de Entorno (Recomendado para desarrollo)

**En macOS/Linux (Terminal):**

```bash
# Configurar para esta sesión
export FACEBOOK_ACCESS_TOKEN="TU_TOKEN_AQUI"

# Para hacerlo permanente (agrega a ~/.zshrc o ~/.bashrc)
echo 'export FACEBOOK_ACCESS_TOKEN="TU_TOKEN_AQUI"' >> ~/.zshrc
source ~/.zshrc
```

**En Windows (CMD/PowerShell):**

```cmd
# CMD
set FACEBOOK_ACCESS_TOKEN=TU_TOKEN_AQUI

# PowerShell
$env:FACEBOOK_ACCESS_TOKEN="TU_TOKEN_AQUI"
```

### OPCIÓN B: Archivo .env (Recomendado para producción)

1. Crea un archivo `.env` en la raíz del proyecto:

```bash
cd "/Users/usuario/Documents/scraping 2"
touch .env
```

2. Agrega el token al archivo `.env`:

```
FACEBOOK_ACCESS_TOKEN=TU_TOKEN_AQUI
```

3. El sistema automáticamente cargará el token desde el archivo `.env`

⚠️ **IMPORTANTE:** Agrega `.env` a `.gitignore` para no compartir el token:

```bash
echo ".env" >> .gitignore
```

---

## 🔄 PASO 3: REINICIAR EL BACKEND

Después de configurar el token, reinicia el backend:

```bash
cd "/Users/usuario/Documents/scraping 2"

# Detener backend actual
pkill -f "python3 api_server.py"

# Esperar un momento
sleep 2

# Reiniciar backend
nohup python3 api_server.py > api_server.log 2>&1 &

# Esperar a que inicie
sleep 5

# Verificar que está funcionando
curl http://localhost:5001/api/health
```

---

## ✅ PASO 4: VERIFICAR QUE FUNCIONA

### Verificar en los logs:

```bash
tail -f api_server.log | grep -E "Graph API|Access Token"
```

Deberías ver:
- ✅ `"✅ Graph API scraper disponible"`
- ✅ `"✅ Access Token encontrado, usando Graph API (método oficial)"`

### Probar scraping:

1. Ve a http://localhost:3001
2. Selecciona "Facebook" como plataforma
3. Intenta scrapear: `https://www.facebook.com/elcomercio.pe`
4. Verifica los logs para ver si usa Graph API

---

## 🔧 SOLUCIÓN DE PROBLEMAS

### ❌ Error: "Access Token inválido o expirado"
**Causa:** El token temporal expiró (duran 1-2 horas)

**Solución:**
- Genera un nuevo token en el Graph API Explorer
- O convierte a token de larga duración (60 días):
  - https://developers.facebook.com/docs/facebook-login/guides/access-tokens/get-long-lived

### ❌ Error: "No tienes permisos"
**Causa:** Faltan permisos en el token

**Solución:**
- Regenera el token con estos permisos:
  - `pages_read_engagement`
  - `pages_show_list`

### ❌ Error: "Página no encontrada"
**Causa:** El nombre de usuario es incorrecto

**Solución:**
- Verifica la URL de la página
- Asegúrate de usar solo el username (ej: `elcomercio.pe`)

### ❌ No detecta el token
**Causa:** Variable de entorno no configurada o archivo .env no encontrado

**Solución:**
```bash
# Verificar que está configurado
echo $FACEBOOK_ACCESS_TOKEN

# O si usas .env, verificar que existe
ls -la .env
```

---

## 📝 NOTAS IMPORTANTES

- ✅ El token temporal es suficiente para pruebas
- ✅ Para producción, usa tokens de larga duración (60 días)
- ❌ **NUNCA** compartas tu token públicamente
- ✅ Guarda el token de forma segura (variables de entorno o .env)
- ✅ Agrega `.env` a `.gitignore` si usas control de versiones

---

## 🚀 TOKEN DE LARGA DURACIÓN (Opcional)

Para un token que dura 60 días:

1. Obtén un token temporal (como se explicó arriba)
2. Conviértelo a token de larga duración:

```python
import requests

short_token = "TU_TOKEN_TEMPORAL"
app_id = "TU_APP_ID"
app_secret = "TU_APP_SECRET"

url = f"https://graph.facebook.com/v18.0/oauth/access_token"
params = {
    'grant_type': 'fb_exchange_token',
    'client_id': app_id,
    'client_secret': app_secret,
    'fb_exchange_token': short_token
}

response = requests.get(url, params=params)
long_token = response.json()['access_token']
print(f"Token de larga duración: {long_token}")
```

