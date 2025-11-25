# 📘 INSTRUCCIONES PARA USAR FACEBOOK GRAPH API

## ✅ VENTAJAS DEL MÉTODO GRAPH API

- ✅ **Método oficial de Facebook** - Legal y confiable
- ✅ **No se bloquea** - Acceso garantizado con token válido
- ✅ **Datos completos y precisos** - Métricas reales, imágenes reales
- ✅ **Más rápido** - No requiere navegador
- ✅ **Estable** - No depende de cambios en la estructura HTML

## 🔑 PASO 1: OBTENER ACCESS TOKEN

### Opción A: Token Temporal (Para pruebas rápidas)

1. Ve a: https://developers.facebook.com/tools/explorer/
2. En el menú desplegable "Meta App", selecciona o crea una app
3. Click en "Generate Access Token"
4. Selecciona los permisos:
   - `pages_read_engagement`
   - `pages_show_list`
5. Copia el token generado

⚠️ **Nota:** Este token expira en 1-2 horas

### Opción B: Token Permanente (Recomendado para producción)

1. Sigue los pasos de la Opción A para obtener un token temporal
2. Ve a: https://developers.facebook.com/docs/facebook-login/guides/access-tokens/get-long-lived
3. Convierte el token temporal a uno de larga duración (60 días)
4. O configura un sistema de refresh automático

## ⚙️ PASO 2: CONFIGURAR EL TOKEN

### Opción 1: Variable de Entorno (Recomendado)

```bash
# En macOS/Linux
export FACEBOOK_ACCESS_TOKEN="tu_token_aqui"

# O en Windows
set FACEBOOK_ACCESS_TOKEN=tu_token_aqui
```

### Opción 2: En el código (No recomendado para producción)

Edita `api_server.py` y pasa el token directamente:

```python
scraper = FacebookScraper(headless=True, delay=3, access_token="tu_token_aqui")
```

## 🚀 PASO 3: USAR EL SISTEMA

1. El sistema automáticamente detectará si hay un token configurado
2. Si hay token → Usa Graph API (método oficial)
3. Si NO hay token → Usa métodos alternativos (Selenium/requests)

## 📊 VERIFICAR QUE FUNCIONA

1. Ve a http://localhost:3001
2. Selecciona "Facebook" como plataforma
3. Intenta scrapear: `https://www.facebook.com/elcomercio.pe`
4. Verifica los logs: `tail -f api_server.log | grep -E "GRAPH API|Graph API"`

Si ves "✅ ✅ ✅ GRAPH API EXITOSO" → ¡Funciona correctamente!

## 🔧 SOLUCIÓN DE PROBLEMAS

### Error: "Access Token inválido o expirado"
- El token expiró (los temporales duran 1-2 horas)
- Solución: Genera un nuevo token

### Error: "No tienes permisos"
- Faltan permisos en el token
- Solución: Regenera el token con los permisos correctos

### Error: "Página no encontrada"
- El nombre de usuario es incorrecto
- Solución: Verifica la URL de la página

## 📝 NOTAS IMPORTANTES

- El token temporal es suficiente para pruebas
- Para producción, usa tokens de larga duración
- Los tokens nunca deben compartirse públicamente
- Guarda el token de forma segura (variables de entorno, no en código)

