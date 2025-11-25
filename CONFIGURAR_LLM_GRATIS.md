# Configuración de LLM Gratuito para el Chatbot

El chatbot ahora soporta múltiples APIs gratuitas de LLM. **Para usar el LLM necesitas obtener una API key gratuita** de uno de estos proveedores.

## 🚀 Opción 1: Groq (Recomendada - Gratuita y Muy Rápida)

Groq ofrece APIs gratuitas con modelos como Llama 3.1, Mixtral, y Gemma. Es la opción más rápida.

### Pasos:

1. **Obtener API Key (Gratuita):**
   - Ve a https://console.groq.com/
   - Crea una cuenta gratuita (solo necesitas email)
   - Ve a "API Keys" en el menú
   - Genera una nueva API key
   - Copia la key (empieza con `gsk_...`)

2. **Configurar en `.env`:**
   ```bash
   LLM_PROVIDER=groq
   LLM_MODEL=llama-3.1-8b-instant
   GROQ_API_KEY=gsk_tu_key_aqui
   ```

3. **Reiniciar el backend:**
   ```bash
   pkill -f api_server.py
   python3 api_server.py
   ```

### Modelos disponibles en Groq (gratuitos):
- `llama-3.1-8b-instant` (muy rápido, recomendado)
- `mixtral-8x7b-32768` (más potente)
- `gemma-7b-it` (alternativa)

## 🎯 Opción 2: Hugging Face (Gratuita)

Hugging Face ofrece acceso gratuito a modelos de código abierto.

### Pasos:

1. **Obtener API Key (Gratuita):**
   - Ve a https://huggingface.co/settings/tokens
   - Crea una cuenta gratuita
   - Genera un token (tipo "Read")
   - Copia el token (empieza con `hf_...`)

2. **Configurar en `.env`:**
   ```bash
   LLM_PROVIDER=huggingface
   LLM_MODEL=mistralai/Mistral-7B-Instruct-v0.2
   HUGGINGFACE_API_KEY=hf_tu_token_aqui
   ```

3. **Reiniciar el backend**

### Modelos disponibles en Hugging Face:
- `mistralai/Mistral-7B-Instruct-v0.2`
- `meta-llama/Llama-2-7b-chat-hf`
- `google/gemma-7b-it`

## ⚙️ Otras Opciones

### Ollama (Local - Requiere instalación):
```bash
LLM_PROVIDER=ollama
LLM_MODEL=llama3
```
Requiere instalar Ollama localmente: https://ollama.ai/

### OpenRouter (Requiere API Key):
```bash
LLM_PROVIDER=openrouter
LLM_MODEL=openai/gpt-3.5-turbo
OPENROUTER_API_KEY=tu_key_aqui
```

## 📝 Archivo `.env` de Ejemplo

Crea un archivo `.env` en la raíz del proyecto:

```bash
# LLM Configuration (Groq - Recomendado)
LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-8b-instant
GROQ_API_KEY=gsk_tu_key_aqui

# Alternativa: Hugging Face
# LLM_PROVIDER=huggingface
# LLM_MODEL=mistralai/Mistral-7B-Instruct-v0.2
# HUGGINGFACE_API_KEY=hf_tu_token_aqui
```

## ✅ Verificar Configuración

Después de configurar, verifica que funciona:

```bash
curl http://localhost:5001/api/llm/status
```

Deberías ver:
```json
{
  "provider": "groq",
  "model": "llama-3.1-8b-instant",
  "key_present": true,
  "available": true,
  "note": "Groq y Hugging Face son gratuitas. Groq es muy rápida."
}
```

## 🎉 Ventajas de Groq

- ✅ **Gratuita** (con límites generosos: 30 requests/minuto)
- ✅ **Muy rápida** (respuestas en <1 segundo)
- ✅ **No requiere instalación local**
- ✅ **Modelos modernos** (Llama 3.1, Mixtral, etc.)
- ✅ **Fácil de configurar** (solo necesitas una API key gratuita)

## 🔧 Solución de Problemas

Si el chatbot no responde con LLM:

1. Verifica que tengas una API key configurada
2. Revisa los logs: `tail -f backend.log | grep -i llm`
3. Prueba cambiar a otro proveedor
4. Verifica la conexión a internet (necesaria para APIs)
5. Si no tienes API key, el chatbot usará respuestas predefinidas (más rápidas pero menos inteligentes)

## 📚 Recursos

- Groq: https://console.groq.com/
- Hugging Face: https://huggingface.co/
- Documentación Groq: https://console.groq.com/docs
- Guía rápida: https://console.groq.com/quickstart

## 💡 Nota Importante

**Sin API key configurada**, el chatbot seguirá funcionando pero usará respuestas predefinidas basadas en la información del sitio. Para obtener respuestas más inteligentes y contextuales, configura una API key gratuita de Groq (recomendado) o Hugging Face.
