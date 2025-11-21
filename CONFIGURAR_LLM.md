# Configuración del LLM para el Chatbot

## Estado Actual
El chatbot está funcionando, pero **sin LLM activo**. Esto significa que:
- ✅ Funciona la búsqueda de artículos
- ✅ Funciona el resumen de noticias
- ✅ Funciona el filtrado por fechas
- ❌ Las respuestas conversacionales son predefinidas (no inteligentes)

## Opciones para Activar el LLM

### Opción 1: Ollama (Recomendado - Gratuito y Local)

**Ventajas:**
- ✅ Completamente gratuito
- ✅ Funciona localmente (sin internet necesario después de descargar)
- ✅ Privacidad total (todo se procesa en tu máquina)

**Pasos:**

1. **Instalar Ollama:**
   ```bash
   # macOS
   brew install ollama
   # O descarga desde: https://ollama.ai
   ```

2. **Iniciar Ollama:**
   ```bash
   ollama serve
   # Se ejecuta en http://localhost:11434
   ```

3. **Descargar un modelo:**
   ```bash
   ollama pull llama3
   # O prueba otros modelos: llama3.2, mistral, etc.
   ```

4. **Crear archivo `.env` en la raíz del proyecto:**
   ```env
   LLM_PROVIDER=ollama
   LLM_MODEL=llama3
   ```

5. **Reiniciar el backend:**
   ```bash
   # Detener el backend actual y volver a iniciarlo
   python3 api_server.py
   ```

---

### Opción 2: OpenRouter (API Externa)

**Ventajas:**
- ✅ Fácil de configurar
- ✅ No requiere instalación local
- ✅ Modelos gratuitos disponibles

**Desventajas:**
- ❌ Requiere conexión a internet
- ❌ Requiere API key (gratuita pero con límites)

**Pasos:**

1. **Crear cuenta en OpenRouter:**
   - Ve a: https://openrouter.ai
   - Crea una cuenta gratuita
   - Obtén tu API key desde el dashboard

2. **Crear archivo `.env` en la raíz del proyecto:**
   ```env
   LLM_PROVIDER=openrouter
   LLM_MODEL=deepseek/deepseek-chat-v3.1:free
   OPENROUTER_API_KEY=sk-or-tu-api-key-aqui
   ```

3. **Reiniciar el backend:**
   ```bash
   python3 api_server.py
   ```

---

## Verificar que Funciona

Después de configurar, verifica el estado:

```bash
curl http://localhost:5001/api/llm/status
```

Deberías ver:
```json
{
  "available": true,
  "provider": "ollama",  // o "openrouter"
  "model": "llama3",
  "key_present": true  // solo para openrouter
}
```

## Modelos Recomendados

### Para Ollama:
- `llama3` - Balanceado, rápido
- `llama3.2` - Más reciente
- `mistral` - Alternativa ligera

### Para OpenRouter:
- `deepseek/deepseek-chat-v3.1:free` - Gratuito
- `meta-llama/llama-3.1-8b-instruct:free` - Gratuito
- `google/gemini-flash-1.5:free` - Gratuito

## Nota Importante

El chatbot **funciona sin LLM**, pero las respuestas serán más básicas. Con LLM activo, el chatbot puede:
- Entender mejor el contexto
- Generar respuestas más naturales
- Responder preguntas más complejas

