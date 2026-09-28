# 🪄 ArcanaBot — Bot de Discord para Servidores de Roleplay

> Bot de gestión para servidores de roleplay temáticos. Desarrollado para **Academia Arcana Isefora** — adaptable para cualquier comunidad similar.

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![discord.py 2.4.0](https://img.shields.io/badge/discord.py-2.4.0-5865F2.svg)](https://discordpy.readthedocs.io/)
[![Licencia MIT](https://img.shields.io/badge/licencia-MIT-green.svg)](LICENSE)

---

## 📋 ¿Qué hace este bot?

ArcanaBot automatiza la gestión de personajes y flujos de moderación para servidores de Discord con temática de roleplay. Incluye:

- **Sistema de fichas de personajes** — Estudiantes, profesores y trabajadores con fichas detalladas
- **Revisión por parte del staff** — Aprobación/rechazo con retroalimentación en los canales designados
- **Sistema de Puntos de Conducta Académica (PCA)** — Sanciones, redenciones y apelaciones
- **Sistema de poderes con Spin** — 7 categorías de razas secretas con tiradas ponderadas
- **Sistema de batallas** — Duelos con registro de resultados en Google Sheets
- **Generación de carnet de identidad** — Carnets visuales con PIL/Pillow
- **Panel de administración** — Estadísticas, gestión de generaciones y limpieza de datos
- **Seguimiento de slots** — Límites configurables de personajes por generación
- **Sistema de uniformes** — Versiones de uniformes diferentes + con selector de casa

---

## ⚙️ Requisitos

- **Python 3.11 exactamente** (Python 3.12+ elimina `audioop`, que necesita discord.py)
- **Cuenta y servidor de Discord**
- **Cuenta de Google** con acceso a Google Sheets
- **Cuenta en Railway o Render** (para hosting, opcional)

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/arcanabot.git
cd arcanabot
```

### 2. Verificar la versión de Python

```bash
python --version
# Debe mostrar: Python 3.11.x
```

Si tienes una versión diferente, descarga Python 3.11 desde [python.org/downloads](https://www.python.org/downloads/release/python-3110/).

Para Railway, crea un archivo `.python-version` en la raíz del proyecto:

```
3.11.9
```

### 3. Crear y activar entorno virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
discord.py==2.4.0
python-dotenv==1.0.0
gspread==6.0.2
google-auth==2.27.0
aiosqlite==0.20.0
Pillow
```

---

## 🤖 Configurar el Bot de Discord

### 1. Crear la aplicación del bot

1. Ve a [discord.com/developers/applications](https://discord.com/developers/applications)
2. Haz clic en **New Application** → ponle nombre → Create
3. Ve a la sección **Bot** → haz clic en **Add Bot**
4. Activa los siguientes **Privileged Gateway Intents**:
   - ✅ Presence Intent
   - ✅ Server Members Intent
   - ✅ Message Content Intent

### 2. Copiar el token

En la sección **Bot**, haz clic en **Reset Token** y copia el token. Lo necesitarás para el `.env`.

### 3. Invitar el bot al servidor

Ve a **OAuth2 → URL Generator** y selecciona:

- **Scopes:** `bot`, `applications.commands`
- **Bot Permissions:**
  - `Send Messages`
  - `Embed Links`
  - `Attach Files`
  - `Read Message History`
  - `Use External Emojis`
  - `Add Reactions`
  - `Manage Roles` (para asignación automática de roles)

Copia la URL generada y úsala para invitar al bot.

---

## 📊 Configurar Google Sheets

### 1. Crear la hoja de cálculo

Crea una nueva hoja en [sheets.google.com](https://sheets.google.com). Crea exactamente **15 pestañas** con estos nombres (respetando mayúsculas y espacios):

| # | Nombre de la pestaña | Descripción |
|---|---------------------|-------------|
| 1 | `UniformesPendientes` | Solicitudes de uniforme en espera |
| 2 | `UniformesAprobados` | Uniformes aprobados |
| 3 | `EstudiantesPendientes` | Fichas de estudiante en espera |
| 4 | `EstudiantesAprobados` | Estudiantes aprobados |
| 5 | `Profesores` | Profesores aprobados |
| 6 | `Trabajadores` | Trabajadores aprobados |
| 7 | `TrabajosPendientes` | Fichas de trabajo en espera |
| 8 | `GlobalStats` | Estadísticas generales del servidor |
| 9 | `PuntosPC` | Puntos de conducta actuales por usuario |
| 10 | `HistorialPC` | Historial completo de puntos |
| 11 | `Sanciones` | Registro de sanciones activas |
| 12 | `FichasPoder` | Fichas de poder aprobadas |
| 13 | `HistorialSpins` | Historial de tiradas de poder |
| 14 | `HistorialBatallas` | Registro de batallas |
| 15 | `CodigosID` | Códigos de carnet generados |

### 2. Crear cuenta de servicio de Google

1. Ve a [console.cloud.google.com](https://console.cloud.google.com)
2. Crea un nuevo proyecto (o usa uno existente)
3. Ve a **APIs y Servicios → Biblioteca**
4. Activa **Google Sheets API** y **Google Drive API**
5. Ve a **Credenciales → Crear credenciales → Cuenta de servicio**
6. Ponle nombre, continúa y descarga el archivo JSON de credenciales
7. Guarda ese archivo como `credentials.json` en la raíz del proyecto

### 3. Compartir la hoja con la cuenta de servicio

Abre `credentials.json` y busca el campo `client_email` (algo como `bot@proyecto.iam.gserviceaccount.com`).

Comparte tu hoja de Google con ese correo dándole permisos de **Editor**.

---

## 🔑 Variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
# Token del bot de Discord
DISCORD_TOKEN=tu_token_aqui

# ID del servidor de Discord (haz clic derecho en el servidor → Copiar ID del servidor)
GUILD_ID=123456789012345678

# IDs de canales (haz clic derecho en el canal → Copiar ID)
CANAL_REVISION_FICHAS=123456789012345678
CANAL_REVISION_PODER=123456789012345678
CANAL_REGISTRO_TRABAJOS=123456789012345678
CANAL_REGISTRO_ESTUDIANTES=123456789012345678
CANAL_REGISTRO_PODERES=123456789012345678

# IDs de roles
ROL_REGISTRADO=123456789012345678
ROL_CONSEJO=123456789012345678
ROL_SLOT_ADICIONAL=123456789012345678
ROL_RESPIN=123456789012345678

# URL de la hoja de Google Sheets (desde el navegador)
SPREADSHEET_URL=https://docs.google.com/spreadsheets/d/TU_ID_AQUI/edit

# Generación actual del servidor (para el seguimiento de slots)
GENERACION_ACTUAL=1
```

**Cómo obtener IDs de Discord:**
- Activa el **Modo Desarrollador** en Ajustes de Discord → Avanzado → Modo desarrollador
- Haz clic derecho en cualquier servidor, canal o rol para ver "Copiar ID"

---

## 🎨 Personalizar el bot

### Editar `utils/constants.py`

Este es el archivo principal de configuración. Cambia estos valores para tu servidor:

```python
# ID de tu servidor
GUILD_ID = int(os.getenv("GUILD_ID", "TU_GUILD_ID"))

# Casas / facciones de tu servidor
CASAS = ["Casa1", "Casa2", "Casa3", "Casa4"]

# Materias disponibles para profesores
MATERIAS = ["Materia 1", "Materia 2", "Materia 3"]

# Cupos máximos por materia (cuántos profesores puede haber por materia por generación)
MATERIAS_LIMITE = {
    "Materia 1": 2,
    "Materia 2": 2,
    "Materia 3": 1,
}

# Cargos disponibles para trabajadores
CARGOS = ["Cargo 1", "Cargo 2", "Cargo 3"]

# Cupos máximos por cargo
CARGOS_LIMITE = {
    "Cargo 1": 3,
    "Cargo 2": 2,
}

# Clubes disponibles para estudiantes
CLUBES = ["Club 1", "Club 2", "Club 3"]

# Límite de personajes por usuario por generación
SLOTS_BASE = {
    "estudiantes": 2,
    "trabajadores": 1,
    "profesores": 1,
}
```

---

## 🗃️ Base de datos SQLite

El bot usa SQLite para el seguimiento de slots de personajes. La base de datos se crea automáticamente al iniciar.

Ubicación del archivo: `data/isefora.db`

**Estructura de la tabla principal `slots_usuarios`:**

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `user_id` | INTEGER | ID del usuario de Discord |
| `generacion` | INTEGER | Número de generación |
| `estudiantes_usados` | INTEGER | Fichas de estudiante creadas |
| `trabajadores_usados` | INTEGER | Fichas de trabajador creadas |
| `profesores_usados` | INTEGER | Fichas de profesor creadas |
| `slots_extra_disponibles` | INTEGER | Slots adicionales otorgados |
| `slots_extra_usados` | INTEGER | Slots adicionales usados |

---

## 🌐 Despliegue

### Opción A: Railway (recomendado)

1. Sube el código a un repositorio de GitHub
2. Ve a [railway.app](https://railway.app) → **New Project → Deploy from GitHub repo**
3. Selecciona tu repositorio
4. Ve a la pestaña **Variables** y agrega todas las variables del `.env`
5. Para las credenciales de Google, puedes pegar el contenido del JSON como variable:
   ```
   GOOGLE_CREDENTIALS_JSON={"type":"service_account",...}
   ```
   Y adaptar `utils/sheets.py` para leer desde esta variable.
6. Railway detectará automáticamente el `Procfile`:
   ```
   worker: python bot.py
   ```
7. Crea `.python-version` con contenido `3.11.9` para fijar la versión de Python.

**⚠️ Importante con Railway:**
- El archivo SQLite **sí persiste** entre despliegues (se guarda en `/app/data/`)
- Si cambias de generación, actualiza la variable `GENERACION_ACTUAL` en Railway
- El archivo `credentials.json` **no persiste** entre despliegues — usa la variable de entorno del JSON

### Opción B: Render

1. Sube el código a GitHub
2. Ve a [render.com](https://render.com) → **New → Background Worker**
3. Conecta tu repositorio
4. Configura:
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
5. Agrega las variables de entorno en la sección **Environment**

---

## 📂 Estructura del proyecto

```
arcanabot/
├── bot.py                  # Entrada principal, carga de cogs
├── .env                    # Variables de entorno (NO subir a Git)
├── .env.example            # Plantilla de variables
├── credentials.json        # Credenciales de Google (NO subir a Git)
├── .python-version         # Fija Python 3.11.9 para Railway
├── requirements.txt        # Dependencias
├── Procfile                # Comando para Railway
├── .gitignore              # Protege archivos sensibles
│
├── cogs/                   # Módulos del bot (comandos)
│   ├── admin.py            # Comandos de administración
│   ├── admin_data.py       # Gestión de datos de personajes
│   ├── uniformes.py        # Sistema de uniformes
│   ├── estudiantes.py      # Registro de estudiantes
│   ├── profesores.py       # Registro de profesores
│   ├── trabajos.py         # Registro de trabajadores
│   ├── editar_ficha.py     # Edición de fichas existentes
│   ├── pca.py              # Sistema de puntos de conducta
│   ├── spins.py            # Sistema de poderes y batallas
│   ├── generar_id.py       # Generación de carnets
│   └── ver_id.py           # Visualización de carnets
│
├── utils/                  # Módulos de utilidad
│   ├── constants.py        # Configuración principal
│   ├── database.py         # Operaciones con SQLite
│   ├── sheets.py           # Integración con Google Sheets
│   └── helpers.py          # Funciones auxiliares y embeds
│
├── assets/                 # Recursos visuales
│   ├── IDEstudiante.png    # Plantilla de carnet de estudiante
│   └── IDWorker.png        # Plantilla de carnet de trabajador
│
└── data/                   # Datos generados en tiempo de ejecución
    ├── isefora.db          # Base de datos SQLite
    └── generacion.json     # Generación actual (respaldo local)
```

---

## 🧾 Referencia de comandos

### Registro de personajes
| Comando | Descripción |
|---------|-------------|
| `/uniforme` | Solicitar aprobación de uniforme |
| `/estudiante` | Registrar ficha de estudiante |
| `/profesor` | Registrar ficha de profesor |
| `/trabajo` | Registrar ficha de trabajador |
| `/editar-ficha` | Editar una ficha ya registrada |

### Sistema de poderes
| Comando | Descripción |
|---------|-------------|
| `/poder` | Girar para obtener poder (requiere foto de la ficha) |
| `/respin` | Volver a girar (requiere rol especial) |
| `/iniciar-batalla` | Iniciar un duelo con otro usuario |

### Carnets de identidad
| Comando | Descripción |
|---------|-------------|
| `/generar-id` | Generar carnet visual de estudiante o trabajador |
| `/ver-id` | Ver carnet generado previamente |

### Puntos de conducta (PCA)
| Comando | Descripción |
|---------|-------------|
| `/asignar-pc` | Asignar puntos positivos o negativos |
| `/sancionar` | Crear sanción formal |
| `/redimir-sancion` | Aprobar una redención de sanción |
| `/apelar` | Apelar una sanción |
| `/ver-sanciones` | Ver sanciones activas de un usuario |
| `/historial-pc` | Ver historial de puntos de un usuario |

### Administración (solo staff)
| Comando | Descripción |
|---------|-------------|
| `/admin` | Panel de control (estadísticas, slots, generación) |
| `/admin-data ver` | Ver todos los personajes de un usuario |
| `/admin-data eliminar-personaje` | Eliminar un personaje específico |
| `/admin-data eliminar-tipo` | Eliminar todos los personajes de un tipo |
| `/admin-data reset-slots` | Reiniciar slots de un usuario |
| `/admin-data reset-total` | Reiniciar completamente los datos de un usuario |

---

## 🐛 Solución de errores comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `ModuleNotFoundError: audioop` | Python 3.12+ incompatible | Usar exactamente Python 3.11; agregar `.python-version` con `3.11.9` |
| `Forbidden: 403` al sincronizar | Bot sin permisos de `applications.commands` | Re-invitar el bot con el scope correcto |
| `gspread.exceptions.SpreadsheetNotFound` | URL incorrecta o sin permisos | Verificar URL en `.env` y que la hoja esté compartida con la cuenta de servicio |
| `discord.errors.InteractionTimedOut` | Interacción no respondida en 3s | Agregar `await interaction.response.defer()` al inicio de callbacks lentos |
| `Extension has no 'setup' function` | Falta `async def setup(bot)` en el cog | Agregar al final de cada archivo de cog |
| Slots muestran datos incorrectos | Variable `GENERACION_ACTUAL` desactualizada | Actualizar la variable de entorno en Railway/Render |

---

## 🔒 Seguridad

- **Nunca subas** `.env` o `credentials.json` a Git
- Agrega ambos al `.gitignore`
- Si tu token de Discord se filtra, **regénéralo inmediatamente** en el portal de desarrolladores
- Los tokens filtrados pueden usarse para spamear, eliminar contenido del servidor o hacer ban masivo de usuarios

---

## 📄 Licencia

[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) — Libre para usar, modificar y compartir. **No se permite el uso comercial ni la venta.** Debes dar crédito a la autora original.

Ve el archivo [LICENSE](LICENSE) para más detalles.

---

## 👩‍💻 Créditos

Desarrollado originalmente para **Academia Arcana Isefora** por **Devilishh** (`devilishh.` en Discord).

Construido con ❤️ por **Devilishh** · ¿Necesitas soporte técnico? Contacta `devilishh.` en Discord.

Contribuciones bienvenidas — abre un issue o pull request en GitHub.
