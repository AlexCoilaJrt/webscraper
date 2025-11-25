# 🔑 PASOS PARA CREAR TOKEN DE FACEBOOK GRAPH API

## 📋 GUÍA PASO A PASO COMPLETA

### PASO 1: IR A FACEBOOK DEVELOPERS

1. Abre tu navegador
2. Ve a: **https://developers.facebook.com/**
3. Inicia sesión con tu cuenta de Facebook

---

### PASO 2: CREAR UNA APP (Si no tienes una)

1. En la página principal, busca el botón **"Mis Apps"** (arriba a la derecha)
2. Click en **"Crear App"** o **"Create App"**
3. Selecciona el tipo de app:
   - Elige **"Business"** o **"Negocios"**
   - Click en **"Siguiente"** o **"Next"**
4. Completa el formulario:
   - **Nombre de la app**: Puede ser cualquier nombre (ej: "Mi Scraper")
   - **Email de contacto**: Tu email
   - **Propósito de la app**: Selecciona "Otro" o "Other"
5. Click en **"Crear App"** o **"Create App"**
6. Completa la verificación de seguridad si te la pide

---

### PASO 3: IR AL GRAPH API EXPLORER

1. En el menú lateral izquierdo, busca **"Herramientas"** o **"Tools"**
2. Click en **"Graph API Explorer"** o **"Explorador de Graph API"**
3. Si no lo encuentras, puedes ir directamente a:
   - **https://developers.facebook.com/tools/explorer/**

---

### PASO 4: SELECCIONAR TU APP

1. En la parte superior del Graph API Explorer, verás un menú desplegable que dice **"Meta App"** o **"Aplicación"**
2. Click en ese menú
3. Selecciona la app que acabas de crear (o una existente)

---

### PASO 5: GENERAR EL ACCESS TOKEN

1. A la derecha del menú de la app, verás un botón que dice:
   - **"Generate Access Token"** o **"Generar Token de Acceso"**
2. Click en ese botón
3. Se abrirá una ventana de permisos

---

### PASO 6: SELECCIONAR PERMISOS

En la ventana de permisos, busca y selecciona estos permisos:

✅ **pages_read_engagement**
   - Permite leer engagement de páginas públicas

✅ **pages_show_list**
   - Permite ver la lista de páginas

**Cómo seleccionar:**
1. Busca cada permiso en la lista
2. Click en la casilla para seleccionarlo
3. Puedes buscar escribiendo "pages" en el buscador

4. Click en **"Generar Token"** o **"Generate Token"**

---

### PASO 7: COPIAR EL TOKEN

1. Después de generar el token, verás un campo de texto con el token
2. El token será algo como: `EAAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
3. **IMPORTANTE:** Copia el token completo (puede ser muy largo)
4. Guárdalo en un lugar seguro temporalmente

⚠️ **ADVERTENCIA:** 
- Este token es TEMPORAL (expira en 1-2 horas)
- Es suficiente para pruebas
- Para producción, necesitarás convertirlo a token de larga duración

---

### PASO 8: CONFIGURAR EL TOKEN EN TU SISTEMA

Una vez que tengas el token copiado, ejecuta estos comandos:

**OPCIÓN A: Variable de Entorno (Temporal - Solo esta sesión)**

```bash
export FACEBOOK_ACCESS_TOKEN="PEGA_TU_TOKEN_AQUI"
```

**OPCIÓN B: Variable de Entorno (Permanente)**

```bash
echo 'export FACEBOOK_ACCESS_TOKEN="PEGA_TU_TOKEN_AQUI"' >> ~/.zshrc
source ~/.zshrc
```

**OPCIÓN C: Archivo .env (Recomendado)**

```bash
cd "/Users/usuario/Documents/scraping 2"
echo 'FACEBOOK_ACCESS_TOKEN=PEGA_TU_TOKEN_AQUI' > .env
```

---

### PASO 9: VERIFICAR QUE FUNCIONA

1. Reinicia el backend:
```bash
cd "/Users/usuario/Documents/scraping 2"
pkill -f "python3 api_server.py"
sleep 2
nohup python3 api_server.py > api_server.log 2>&1 &
sleep 5
```

2. Verifica en los logs:
```bash
tail -f api_server.log | grep -E "Graph API|Access Token"
```

Deberías ver:
- ✅ `"✅ Graph API scraper disponible"`
- ✅ `"✅ Access Token encontrado, usando Graph API (método oficial)"`

---

## 🔧 SOLUCIÓN DE PROBLEMAS

### ❌ No puedo crear una app
**Solución:**
- Asegúrate de estar logueado con tu cuenta de Facebook
- Verifica que tu cuenta tenga permisos de desarrollador
- Intenta desde otro navegador

### ❌ No aparece "Graph API Explorer"
**Solución:**
- Ve directamente a: https://developers.facebook.com/tools/explorer/
- O busca "Graph API Explorer" en el menú de herramientas

### ❌ No puedo encontrar los permisos
**Solución:**
- Busca escribiendo "pages" en el buscador de permisos
- Los permisos pueden estar en diferentes categorías
- Asegúrate de seleccionar exactamente: `pages_read_engagement` y `pages_show_list`

### ❌ El token expira muy rápido
**Solución:**
- Los tokens temporales expiran en 1-2 horas (normal)
- Para producción, necesitas convertirlo a token de larga duración (60 días)
- Por ahora, genera uno nuevo cuando necesites

### ❌ El token no funciona
**Solución:**
- Verifica que copiaste el token completo (puede ser muy largo)
- Asegúrate de que no tenga espacios antes o después
- Verifica que los permisos sean correctos
- Genera un nuevo token

---

## 📝 NOTAS IMPORTANTES

- ✅ El token es personal y único para tu cuenta
- ✅ No compartas el token públicamente
- ✅ El token temporal es suficiente para pruebas
- ✅ Para producción, convierte a token de larga duración

---

## 🚀 SIGUIENTE PASO

Una vez que tengas el token configurado, el sistema automáticamente:
1. Detectar el token
2. Usar Graph API (método oficial)
3. Extraer datos reales de Facebook

¡Ya estarás listo para scrapear Facebook de forma confiable!

