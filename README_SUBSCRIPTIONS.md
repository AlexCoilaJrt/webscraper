# 💳 Sistema de Suscripciones Premium/Freemium

## 🎯 Descripción

Sistema completo de planes de suscripción con pago manual para el Web Scraper. Permite monetizar el servicio ofreciendo diferentes niveles de acceso con límites de uso.

## 🏗️ Arquitectura

### Backend
- **`subscription_system.py`**: Lógica principal de suscripciones
- **`auth_system.py`**: Integración con autenticación
- **`api_server.py`**: Endpoints REST para suscripciones

### Frontend
- **`Subscriptions.tsx`**: Página de planes para usuarios
- **`PaymentManagement.tsx`**: Dashboard de administración de pagos
- **`PaymentNotifications.tsx`**: Sistema de notificaciones

### Base de Datos
- **`subscription_database.db`**: Base de datos SQLite para suscripciones
- **`auth_database.db`**: Base de datos de usuarios (existente)

## 📋 Planes Disponibles

### 🆓 Plan Freemium (Gratuito)
- **Precio**: $0/mes
- **Artículos**: 50 por día
- **Imágenes**: 10 por scraping
- **Usuarios**: 1 por cuenta
- **Características**:
  - Estadísticas básicas
  - Soporte por email

### 💎 Plan Premium ($29/mes)
- **Precio**: $29/mes
- **Artículos**: 500 por día
- **Imágenes**: 100 por scraping
- **Usuarios**: 5 por cuenta
- **Características**:
  - Análisis avanzados y nubes de palabras
  - Scraping programado
  - Soporte prioritario
  - Exportación a múltiples formatos

### 🚀 Plan Enterprise ($99/mes)
- **Precio**: $99/mes
- **Artículos**: Ilimitados
- **Imágenes**: Ilimitadas
- **Usuarios**: Ilimitados
- **Características**:
  - API completa
  - Scraping en tiempo real
  - Soporte 24/7
  - Integración con webhooks
  - Análisis de sentimientos avanzado

## 💳 Sistema de Pago Manual

### Flujo de Pago
1. **Usuario selecciona plan** → Se genera código único de pago
2. **Usuario transfiere dinero** → A tu número de celular/banco
3. **Usuario envía comprobante** → Por WhatsApp/Email
4. **Admin verifica pago** → En dashboard de administración
5. **Suscripción se activa** → Automáticamente por 30 días

### Códigos de Pago
- **Formato**: `PAY-XXXXXXXX` (8 caracteres hexadecimales)
- **Expiración**: 7 días
- **Únicos**: No se pueden duplicar
- **Rastreables**: Historial completo de códigos

## 🔧 Instalación y Configuración

### 1. Instalar Dependencias
```bash
# Backend ya tiene las dependencias necesarias
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### 2. Inicializar Base de Datos
```bash
# El sistema se inicializa automáticamente al ejecutar
python api_server.py
```

### 3. Configurar Información de Pago
Edita los siguientes archivos con tu información:

**Frontend - `Subscriptions.tsx`** (líneas 200-210):
```typescript
// Número de WhatsApp actualizado
onClick={() => window.open('https://wa.me/51955867498?text=...')}

// Email actualizado
onClick={() => window.open('mailto:alexcjlegion@gmail.com?subject=...')}
```

## 🚀 Uso del Sistema

### Para Usuarios
1. **Acceder a Suscripciones**: Navegar a `/subscriptions`
2. **Seleccionar Plan**: Elegir entre Freemium, Premium o Enterprise
3. **Crear Código de Pago**: Sistema genera código único
4. **Realizar Pago**: Transferir dinero y enviar comprobante
5. **Esperar Activación**: Admin verifica y activa suscripción

### Para Administradores
1. **Dashboard de Pagos**: Navegar a `/payments`
2. **Ver Pagos Pendientes**: Lista de códigos de pago sin verificar
3. **Verificar Pagos**: Confirmar comprobantes y activar suscripciones
4. **Estadísticas**: Monitorear uso y suscripciones activas

## 📊 Monitoreo y Estadísticas

### Dashboard de Administración
- **Pagos Pendientes**: Códigos sin verificar
- **Suscripciones Activas**: Por plan
- **Uso Diario**: Artículos e imágenes procesadas
- **Usuarios Activos**: Por día

### Límites Automáticos
- **Verificación en Tiempo Real**: Antes de cada scraping
- **Contadores Diarios**: Se reinician cada día
- **Notificaciones**: Cuando se alcanzan límites

## 🔒 Seguridad

### Autenticación
- **JWT Tokens**: Para sesiones seguras
- **Roles**: Admin vs Usuario
- **Límites por Usuario**: Individuales y rastreables

### Validación de Pagos
- **Códigos Únicos**: Imposibles de duplicar
- **Expiración**: 7 días máximo
- **Verificación Manual**: Admin confirma cada pago

## 🧪 Pruebas

### Script de Prueba
```bash
python test_subscription_system.py
```

### Pruebas Manuales
1. **Crear Usuario**: Registrarse en el sistema
2. **Seleccionar Plan**: Elegir Premium o Enterprise
3. **Generar Código**: Verificar que se crea correctamente
4. **Simular Pago**: Usar dashboard de admin para verificar
5. **Probar Límites**: Intentar exceder límites del plan

## 📱 Notificaciones

### Tipos de Notificaciones
- **Pago Creado**: Cuando se genera código
- **Pago Verificado**: Cuando admin confirma pago
- **Pago Expirado**: Cuando código vence
- **Suscripción Activada**: Cuando se activa plan

### Configuración
- **Tiempo Real**: Polling cada 30 segundos
- **Persistencia**: Se mantienen en base de datos
- **Marcado como Leído**: Interfaz intuitiva

## 🛠️ Personalización

### Agregar Nuevos Planes
1. **Editar `subscription_system.py`**:
```python
# En create_default_plans()
{
    'name': 'nuevo_plan',
    'display_name': 'Nuevo Plan',
    'price': 49.0,
    'max_articles_per_day': 1000,
    'max_images_per_scraping': 200,
    'max_users': 10,
    'features': json.dumps(['Nueva característica'])
}
```

### Modificar Límites
- **Artículos por Día**: Cambiar en base de datos
- **Imágenes por Scraping**: Ajustar en configuración
- **Usuarios por Cuenta**: Modificar en planes

### Cambiar Precios
- **Base de Datos**: Actualizar tabla `plans`
- **Frontend**: Los precios se cargan dinámicamente

## 🚨 Solución de Problemas

### Errores Comunes

**"Límite de uso excedido"**
- Verificar suscripción activa del usuario
- Comprobar contadores diarios
- Revisar configuración del plan

**"Código de pago expirado"**
- Verificar fecha de expiración
- Generar nuevo código si es necesario
- Confirmar que no han pasado 7 días

**"Error verificando pago"**
- Verificar que el código existe
- Comprobar que no está ya verificado
- Revisar permisos de administrador

### Logs y Debugging
```bash
# Ver logs del servidor
tail -f auto_scraping.log

# Verificar base de datos
sqlite3 subscription_database.db
.tables
SELECT * FROM plans;
```

## 📈 Métricas de Éxito

### KPIs a Monitorear
- **Conversión**: Usuarios que pagan vs total
- **Retención**: Suscripciones que se renuevan
- **Uso**: Artículos/imágenes procesadas por plan
- **Satisfacción**: Tiempo de respuesta a pagos

### Reportes Sugeridos
- **Mensual**: Ingresos por plan
- **Semanal**: Nuevas suscripciones
- **Diario**: Uso y límites alcanzados

## 🔮 Próximas Mejoras

### Funcionalidades Futuras
- **Pagos Automáticos**: Integración con Stripe/PayPal
- **Facturación**: Generación automática de facturas
- **Descuentos**: Códigos promocionales
- **Referidos**: Sistema de afiliados
- **API**: Endpoints para integraciones externas

### Optimizaciones
- **Cache**: Redis para límites de uso
- **Webhooks**: Notificaciones en tiempo real
- **Analytics**: Dashboard avanzado de métricas
- **Mobile**: App móvil para administración

---

## 📞 Soporte

Para dudas o problemas con el sistema de suscripciones:

- **Email**: admin@webscraper.com
- **WhatsApp**: +51 999 999 999
- **Documentación**: Este archivo README

¡El sistema está listo para monetizar tu Web Scraper! 🚀💰
