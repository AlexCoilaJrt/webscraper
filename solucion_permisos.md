# 🔧 SOLUCIÓN: AGREGAR PERMISOS CUANDO EL DROPDOWN NO FUNCIONA

## ⚠️ PROBLEMA

El dropdown del Graph API Explorer no muestra opciones cuando escribes.

## ✅ SOLUCIÓN 1: Escribir Manualmente

1. En el campo "Añadir un permiso" que muestra "user_payment_tokens"
2. Haz click en el campo
3. **BORRA** todo el texto (user_payment_tokens)
4. Escribe EXACTAMENTE: `pages_read_engagement`
5. Presiona **ENTER** o **TAB**
6. Si aparece en la lista de permisos arriba → ¡Perfecto!
7. Repite para el segundo permiso:
   - Click en "Añadir un permiso" de nuevo
   - Escribe: `pages_show_list`
   - Presiona ENTER

## ✅ SOLUCIÓN 2: Usar el Token Actual

El token que ya tienes puede funcionar para páginas públicas:

```bash
export FACEBOOK_ACCESS_TOKEN="EAAVZBZCgJaJYgBPZCr85BT6ZApqHmEtKdrh7c217sJpU8wjcSfYZB1usZAYbWC"
```

Reinicia el backend y prueba scraping. Si funciona, no necesitas más permisos.

## ✅ SOLUCIÓN 3: Generar Token desde Código

Si el Graph API Explorer no funciona, puedes generar el token programáticamente (requiere App ID y App Secret).

