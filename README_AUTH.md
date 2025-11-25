# 🔐 Sistema de Autenticación - Web Scraper

## 🎯 **¡Sistema de Autenticación Implementado!**

Tu Web Scraper ahora cuenta con un **sistema completo de autenticación y autorización** con dos roles diferenciados:

### 👑 **Administrador** (Acceso Completo)
- ✅ **Scraping manual** - Iniciar y detener scraping
- ✅ **Gestión de usuarios** - Crear, editar y desactivar usuarios
- ✅ **Configuración de BD** - Configurar bases de datos
- ✅ **Limpieza de datos** - Borrar todos los datos
- ✅ **Visualización** - Ver artículos, imágenes y estadísticas
- ✅ **Descarga** - Exportar datos a Excel

### 👤 **Usuario** (Solo Visualización)
- ✅ **Visualización** - Ver artículos, imágenes y estadísticas
- ✅ **Descarga** - Exportar datos a Excel
- ❌ **Sin acceso** a funciones administrativas

---

## 🚀 **Cómo Usar el Sistema**

### **1. Acceder al Sistema**
1. Abre tu navegador en: **http://localhost:3000**
2. Serás redirigido automáticamente a la página de login
3. Usa las credenciales por defecto:

#### **Credenciales por Defecto:**
- **Usuario Administrador:**
  - Usuario: `admin`
  - Contraseña: `admin123`

- **Usuario Regular:**
  - Usuario: `usuario`
  - Contraseña: `usuario123`

### **2. Funcionalidades por Rol**

#### **🔐 Como Administrador:**
- **Dashboard completo** con todas las opciones
- **Menú "SCRAPING"** - Para iniciar scraping manual
- **Menú "USUARIOS"** - Para gestionar usuarios
- **Menú "BASE DE DATOS"** - Para configurar BD
- **Botón "Limpiar Datos"** - Para borrar todos los datos

#### **👤 Como Usuario:**
- **Dashboard limitado** sin opciones administrativas
- **Solo visualización** de artículos, imágenes y estadísticas
- **Descarga de datos** a Excel
- **Sin acceso** a funciones de scraping o gestión

---

## 🛠️ **Gestión de Usuarios (Solo Admin)**

### **Crear Nuevo Usuario:**
1. Inicia sesión como **administrador**
2. Ve a **"USUARIOS"** en el menú
3. Haz clic en **"Crear Usuario"**
4. Completa los datos:
   - Usuario
   - Email
   - Contraseña
   - Rol (Usuario/Administrador)

### **Gestionar Usuarios Existentes:**
- **Cambiar rol** - Convertir usuario en admin o viceversa
- **Desactivar usuario** - Bloquear acceso temporalmente
- **Ver información** - Último login, fecha de creación

---

## 🔒 **Seguridad Implementada**

### **Autenticación:**
- ✅ **JWT Tokens** - Tokens seguros con expiración
- ✅ **Contraseñas hasheadas** - PBKDF2 con salt
- ✅ **Sesiones seguras** - Verificación automática de tokens

### **Autorización:**
- ✅ **Protección de rutas** - Solo usuarios autenticados
- ✅ **Control de roles** - Funciones según permisos
- ✅ **API protegida** - Endpoints con autenticación

### **Base de Datos:**
- ✅ **Base de datos separada** - `auth_database.db`
- ✅ **Gestión de sesiones** - Control de tokens activos
- ✅ **Auditoría** - Registro de logins y actividades

---

## 📊 **Endpoints de API**

### **Autenticación:**
- `POST /api/auth/login` - Iniciar sesión
- `GET /api/auth/verify` - Verificar token
- `GET /api/auth/users` - Listar usuarios (solo admin)
- `POST /api/auth/users` - Crear usuario (solo admin)
- `PUT /api/auth/users/{id}/role` - Cambiar rol (solo admin)
- `PUT /api/auth/users/{id}/deactivate` - Desactivar usuario (solo admin)

### **Protegidos por Rol:**
- `POST /api/start-scraping` - Solo administradores
- `POST /api/stop-scraping` - Solo administradores
- `DELETE /api/clear-all` - Solo administradores
- `DELETE /api/newspapers/{name}` - Solo administradores

### **Acceso Público (Autenticado):**
- `GET /api/articles` - Ver artículos
- `GET /api/images` - Ver imágenes
- `GET /api/stats` - Ver estadísticas
- `GET /api/newspapers` - Ver periódicos

---

## 🎨 **Interfaz de Usuario**

### **Página de Login:**
- 🎨 **Diseño moderno** con Material-UI
- 🔐 **Formulario seguro** con validación
- 📱 **Responsive** - Funciona en móviles
- 💡 **Credenciales visibles** para facilitar el acceso

### **Navbar Inteligente:**
- 👤 **Información del usuario** - Nombre y rol
- 🔄 **Menú dinámico** - Opciones según permisos
- 🚪 **Logout seguro** - Cerrar sesión
- 🎯 **Indicador de rol** - Admin/Usuario

### **Protección de Rutas:**
- 🛡️ **Redirección automática** - Login si no autenticado
- ⚠️ **Mensajes de error** - Acceso denegado claro
- 🔄 **Carga de verificación** - Spinner durante autenticación

---

## 🔧 **Configuración Técnica**

### **Backend (Python/Flask):**
- **PyJWT** - Manejo de tokens JWT
- **SQLite** - Base de datos de autenticación
- **Decoradores** - Protección de endpoints
- **Hash PBKDF2** - Contraseñas seguras

### **Frontend (React/TypeScript):**
- **Context API** - Estado global de autenticación
- **Axios Interceptors** - Tokens automáticos
- **Protected Routes** - Componentes de protección
- **Material-UI** - Interfaz moderna

---

## 🚨 **Importante - Seguridad**

### **⚠️ Cambiar Credenciales por Defecto:**
```bash
# En producción, cambiar las credenciales por defecto
# Editar auth_system.py línea 25-27:
admin_username = "tu_admin"
admin_password = "tu_password_seguro"
admin_email = "tu_email@dominio.com"
```

### **🔐 Variables de Entorno:**
```bash
# Crear archivo .env para producción:
SECRET_KEY=tu_clave_secreta_muy_larga_y_compleja
JWT_EXPIRATION_HOURS=24
```

---

## 🎉 **¡Sistema Listo!**

Tu Web Scraper ahora es una **aplicación profesional** con:

- ✅ **Autenticación completa**
- ✅ **Dos roles diferenciados**
- ✅ **Interfaz moderna**
- ✅ **Seguridad robusta**
- ✅ **Gestión de usuarios**
- ✅ **Protección de rutas**

### **Próximos Pasos:**
1. **Cambiar credenciales** por defecto
2. **Crear usuarios** según necesidades
3. **Configurar variables** de entorno
4. **Personalizar roles** si es necesario

**¡Tu sistema de web scraping ahora es completamente profesional y seguro!** 🚀




















