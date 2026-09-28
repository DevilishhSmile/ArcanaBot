# 🏗️ Arquitectura de ArcanaBot — Referencia Técnica

Este documento es la referencia técnica completa para desarrolladores que quieran extender, modificar o entender el funcionamiento interno del bot.

---

## 🧱 Stack tecnológico

| Componente | Tecnología | Versión | Notas |
|-----------|-----------|---------|-------|
| Lenguaje | Python | 3.11 exactamente | 3.12+ elimina `audioop` |
| Framework de Discord | discord.py | 2.4.0 | Slash commands, Views, Modals |
| Base de datos local | SQLite (aiosqlite) | 0.20.0 | Seguimiento asíncrono de slots |
| Hoja de cálculo | gspread + google-auth | 6.0.2 / 2.27.0 | Almacenamiento de fichas y estadísticas |
| Generación de imágenes | Pillow (PIL) | Última | Carnets de identidad |
| Variables de entorno | python-dotenv | 1.0.0 | Configuración local |
| Hosting | Railway / Render | — | Hosting cloud |

---

## 📐 Visión general de la arquitectura

```
Discord ←──→ bot.py (Entrada)
                ├── 11 Cogs (cogs/)
                │     └── Comandos slash, Views, Modals, Selects
                ├── utils/constants.py   ← Configuración centralizada
                ├── utils/database.py    ← SQLite async (slots)
                ├── utils/sheets.py      ← Google Sheets (fichas, estadísticas)
                └── utils/helpers.py     ← Embeds, formateo, publicación
```

**Flujo de una interacción típica:**

1. Usuario ejecuta un comando slash
2. El cog correspondiente muestra un Modal o View
3. El usuario completa el formulario → callback recibe los datos
4. Los datos se validan y se guardan en Sheets (pendiente)
5. El staff revisa y aprueba/rechaza en el canal de revisión
6. Al aprobar: se actualiza Sheets, se asigna rol, se notifica al usuario

---

## 📦 Módulos (Cogs)

### `cogs/bot.py` — Entrada principal

- Carga los 11 cogs al inicio
- Evento `on_ready`: sincroniza los slash commands del guild
- Evento `on_message`: captura imágenes enviadas por los usuarios (para la foto de perfil de fichas en espera)
- Sincronización: **solo por guild** (los comandos globales tardan hasta 1 hora en propagarse)

```python
# Cogs cargados al inicio
EXTENSIONS = [
    "cogs.admin", "cogs.admin_data",
    "cogs.uniformes", "cogs.estudiantes",
    "cogs.profesores", "cogs.trabajos",
    "cogs.editar_ficha", "cogs.pca",
    "cogs.spins", "cogs.generar_id", "cogs.ver_id"
]
```

---

### `cogs/uniformes.py` — Sistema de uniformes

**Comando:** `/uniforme`

**Flujo:**
```
/uniforme
  → UniformeModal (nombre, apellido, edad, link de referencia)
  → CasaSelectView (selector de casa/facción)
  → VersionSelectView (Diplomático / Militarizado)
  → Envío a canal de revisión (embed con botones Aprobar/Rechazar)
  → Staff aprueba → se mueve a UniformesAprobados en Sheets
```

**Sheets involucradas:** `UniformesPendientes`, `UniformesAprobados`

---

### `cogs/estudiantes.py` — Registro de estudiantes

**Comando:** `/estudiante`

**Flujo:**
```
/estudiante
  → Verificación de slots disponibles
  → Modal 1: Datos básicos (nombre, apellido, edad, año académico)
  → Modal 2: Historia y personalidad
  → Modal 3: Apariencia y foto
  → CasaSelectView (selector de casa)
  → ClubesSelectView (selector múltiple de clubes)
  → Captura de foto de perfil (espera imagen del usuario)
  → Envío a canal de revisión
  → Staff aprueba → slot registrado en SQLite + Sheets
```

**Sheets involucradas:** `EstudiantesPendientes`, `EstudiantesAprobados`

---

### `cogs/profesores.py` — Registro de profesores

**Comando:** `/profesor`

**Flujo:**
```
/profesor
  → MateriaSelectView (verifica cupos disponibles por generación)
  → Modal 1: Datos del profesor
  → Modal 2: Historia y experiencia
  → Modal 3: Apariencia y foto
  → Envío a canal de revisión
  → Staff aprueba → slot registrado en SQLite + Sheets
```

**Lógica de cupos:** `get_profesores_aprobados_por_materia(materia)` filtra por generación actual. Si `ocupados >= limite`, se rechaza la solicitud.

**Sheets involucradas:** `Profesores`, `TrabajosPendientes`

---

### `cogs/trabajos.py` — Registro de trabajadores

**Comando:** `/trabajo`

**Flujo:**
```
/trabajo
  → CargoSelectView (verifica cupos disponibles por generación)
  → Modal 1: Datos del trabajador
  → Modal 2: Historia y motivación
  → Modal 3: Apariencia y foto
  → Envío a canal de revisión
  → Staff aprueba → slot registrado en SQLite + Sheets
```

**Sheets involucradas:** `TrabajosPendientes`, `Trabajadores`

---

### `cogs/editar_ficha.py` — Edición de fichas

**Comando:** `/editar-ficha`

**Flujo:**
```
/editar-ficha
  → Selector de tipo (Estudiante / Profesor / Trabajador)
  → Selector de personaje (lista de fichas del usuario)
  → Modales pre-rellenados con datos existentes
  → Envío al canal de revisión (marcado como "EDICIÓN")
  → Staff aprueba → actualiza la fila en Sheets
```

---

### `cogs/pca.py` — Sistema de Puntos de Conducta Académica

**Comandos:** `/asignar-pc`, `/sancionar`, `/redimir-sancion`, `/apelar`, `/ver-sanciones`, `/historial-pc`

**Estructura del sistema PCA:**

| Acción | Descripción |
|--------|-------------|
| Asignar PC | Staff agrega puntos positivos o negativos a un usuario |
| Sancionar | Staff registra una sanción formal (falta leve/grave/expulsión) |
| Apelar | Usuario solicita revisión de una sanción |
| Redimir | Staff aprueba un proceso de redención |

**Sheets involucradas:** `PuntosPC`, `HistorialPC`, `Sanciones`

**Flujo de apelación:**
```
Usuario /apelar
  → Modal con justificación
  → Envío al canal de revisión de staff
  → Staff aprueba → sanción marcada como "redimida"
  → Notificación al usuario
```

---

### `cogs/spins.py` — Sistema de poderes y batallas

**Comandos:** `/poder`, `/respin`, `/iniciar-batalla`

**Flujo del spin de poder:**
```
/poder
  → Usuario proporciona foto de su ficha
  → Bot gira: selecciona categoría de raza ponderada
  → Dentro de la categoría: selecciona poder específico
  → Staff ve la categoría (secreta) + el poder
  → Staff aprueba → se registra en FichasPoder + HistorialSpins
  → Usuario recibe embed con su poder (sin ver la categoría)
```

**Las 7 categorías de razas (secretas, solo staff):**

| Emoji | Categoría | Peso (%) | Descripción |
|-------|-----------|----------|-------------|
| ⚪ | Básico | 40% | La raza más común |
| 🔵 | Sensitivo | 25% | Ligeramente poco común |
| 🟢 | Épico | 15% | Poco frecuente |
| 🟡 | Mítico | 10% | Raro |
| 🟠 | Legendario | 6% | Muy raro |
| 🔴 | Maldito | 3% | Extremadamente raro |
| ✨ | Divino | 1% | Casi imposible |

La selección usa `random.choices()` con los pesos definidos en `CATEGORIAS_RAZA` dentro de `constants.py`.

**Flujo del sistema de batallas:**
```
/iniciar-batalla @rival
  → Bot verifica que ambos tengan fichas de poder aprobadas
  → Crea BatallaActivaView con botones:
     ⚔️ Tirada      → genera resultado aleatorio para ambos
     🏆 Terminar    → selector de ganador → registra en HistorialBatallas
     🏳️ Cancelar    → cancela la batalla
```

**Sheets involucradas:** `FichasPoder`, `HistorialSpins`, `HistorialBatallas`

---

### `cogs/generar_id.py` — Generación de carnets

**Comando:** `/generar-id`

**Proceso:**
```
/generar-id @usuario
  → Busca datos del usuario en Sheets (estudiante o trabajador)
  → Abre plantilla PNG (assets/IDEstudiante.png o assets/IDWorker.png)
  → Dibuja texto sobre la plantilla con PIL/Pillow:
     - Nombre completo
     - Casa / Cargo
     - Año académico / Descripción de cargo
     - Código único de ID
  → Descarga la foto de perfil de Discord del usuario
  → La coloca en la posición designada en la plantilla
  → Guarda el resultado como imagen temporal
  → Lo envía en el canal y registra el código en CodigosID en Sheets
```

**Sheets involucradas:** `CodigosID`, `EstudiantesAprobados`, `Trabajadores`

---

### `cogs/ver_id.py` — Visualización de carnets

**Comando:** `/ver-id`

Busca el carnet registrado del usuario en `CodigosID` y lo regenera desde la URL de foto guardada.

---

### `cogs/admin.py` — Panel de administración

**Comando:** `/admin` (solo staff con rol de consejo)

**AdminStatsView — 5 secciones:**

| Botón | Descripción |
|-------|-------------|
| 📊 Estadísticas | Totales de personajes, slots usados, estadísticas globales |
| 👥 Usuarios | Información de slots de un usuario específico |
| 🎓 Generación | Cambiar la generación activa del servidor |
| 🔄 Reset masivo | Reiniciar todos los slots (nueva generación) |
| ❌ Cerrar | Cerrar el panel |

**Lógica de generación:**

`cargar_generacion()` lee en este orden de prioridad:
1. Variable de entorno `GENERACION_ACTUAL` (persiste en Railway)
2. Archivo `data/generacion.json` (respaldo local)
3. Valor por defecto: `1`

---

### `cogs/admin_data.py` — Gestión de datos

**Comandos:**

| Comando | Descripción |
|---------|-------------|
| `/admin-data ver @usuario` | Lista todos los personajes del usuario |
| `/admin-data eliminar-personaje @usuario` | Elimina un personaje específico |
| `/admin-data eliminar-tipo @usuario tipo` | Elimina todos los personajes de un tipo |
| `/admin-data reset-slots @usuario` | Reinicia contadores de slots |
| `/admin-data reset-total @usuario` | Elimina todos los datos del usuario |

---

## 🔧 Módulos de utilidad

### `utils/constants.py`

El archivo de configuración central del bot. **Todo lo que es configurable está aquí.**

Variables principales:

```python
# IDs del servidor
GUILD_ID              # ID del servidor de Discord
CANAL_REVISION_FICHAS # Canal donde el staff revisa fichas
CANAL_REVISION_PODER  # Canal donde el staff revisa poderes
CANAL_REGISTRO_*      # Canales donde se publican las fichas aprobadas

# IDs de roles
ROL_REGISTRADO        # Rol que se asigna al aprobar una ficha
ROL_CONSEJO           # Rol de staff con acceso a comandos de admin
ROL_SLOT_ADICIONAL    # Rol que otorga un slot extra de personaje
ROL_RESPIN            # Rol que permite hacer un respin de poder

# Configuración de personajes
CASAS                 # Lista de casas/facciones disponibles
MATERIAS              # Lista de materias para profesores
MATERIAS_LIMITE       # Cupos máximos por materia por generación
CARGOS                # Lista de cargos para trabajadores
CARGOS_LIMITE         # Cupos máximos por cargo por generación
CLUBES                # Lista de clubes para estudiantes
SLOTS_BASE            # Slots base por tipo de personaje

# Sistema de poder (no cambiar los pesos sin ajustar la lógica)
CATEGORIAS_RAZA       # 7 categorías con pesos ponderados
NIVELES_PODER         # Niveles de poder por categoría
DESCRIPCIONES_MANA    # Descripciones del tipo de maná

# Colores de embeds
COLOR_OK              # Verde (aprobado)
COLOR_ERROR           # Rojo (rechazado)
COLOR_INFO            # Azul (información)
COLOR_PENDIENTE       # Amarillo (en espera)
```

---

### `utils/database.py`

Operaciones asíncronas con SQLite para el seguimiento de slots de personajes.

**Funciones principales:**

```python
async def init_db()
# Crea las tablas si no existen

async def get_conteo_usuario(user_id: int, generacion: int) -> dict
# Retorna cuántos personajes de cada tipo tiene el usuario en la generación actual

async def registrar_personaje(user_id: int, generacion: int, tipo: str)
# Incrementa el contador del tipo indicado ("estudiantes", "trabajadores", "profesores")

async def reset_usuario(user_id: int, generacion: int)
# Reinicia todos los contadores de un usuario a 0

async def agregar_slot_extra(user_id: int, generacion: int, cantidad: int)
# Agrega slots adicionales al usuario (para el rol ROL_SLOT_ADICIONAL)

async def get_todos_los_usuarios(generacion: int) -> list
# Retorna todos los registros de la generación actual (para estadísticas del admin)
```

**Esquema de la tabla `slots_usuarios`:**

```sql
CREATE TABLE IF NOT EXISTS slots_usuarios (
    user_id              INTEGER NOT NULL,
    generacion           INTEGER NOT NULL,
    estudiantes_usados   INTEGER DEFAULT 0,
    trabajadores_usados  INTEGER DEFAULT 0,
    profesores_usados    INTEGER DEFAULT 0,
    slots_extra_disponibles INTEGER DEFAULT 0,
    slots_extra_usados   INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, generacion)
)
```

---

### `utils/sheets.py`

Integración con Google Sheets para almacenamiento persistente de fichas y estadísticas.

**Funciones principales:**

```python
def get_sheet(nombre: str) -> gspread.Worksheet
# Obtiene una pestaña de la hoja por nombre

def agregar_fila(nombre_hoja: str, fila: list)
# Agrega una fila al final de la hoja indicada

def get_todas_las_filas(nombre_hoja: str) -> list[dict]
# Retorna todas las filas como lista de diccionarios (usa la primera fila como headers)

def actualizar_fila(nombre_hoja: str, col_busqueda: str, val_busqueda: str, datos: dict)
# Busca una fila por valor en una columna y actualiza los campos indicados

def get_personajes_usuario(user_id: int) -> list[dict]
# Retorna todos los personajes aprobados de un usuario (busca en todas las hojas)

def get_profesores_aprobados_por_materia(materia: str, gen: int) -> int
# Cuenta profesores aprobados de una materia en la generación actual

def get_trabajadores_aprobados_por_cargo(cargo: str, gen: int) -> int
# Cuenta trabajadores aprobados de un cargo en la generación actual
```

**⚠️ Nota sobre rate limits de Sheets:**

La API de Google Sheets tiene un límite de ~60 requests por minuto. Si el bot hace muchas operaciones en poco tiempo, puede recibir `APIError: RESOURCE_EXHAUSTED`. Soluciones:
- Caché local en memoria para datos que no cambian frecuentemente
- Agrupación de operaciones de lectura
- `asyncio.sleep(1)` entre operaciones masivas

---

### `utils/helpers.py`

Funciones auxiliares para construir embeds y publicar fichas.

**Funciones principales:**

```python
def build_review_embed(tipo: str, data: dict, user: discord.Member) -> discord.Embed
# Construye el embed de revisión para el canal de staff
# tipo: "uniforme" | "estudiante" | "profesor" | "trabajador" | "poder"

def build_acceptance_embed(tipo: str, data: dict) -> discord.Embed
# Construye el embed de confirmación que se envía al usuario al aprobar

async def publicar_ficha_con_imagenes(channel, embed, foto_url, foto_ficha_url)
# Publica la ficha aprobada en el canal de registro en dos mensajes:
# Mensaje 1: Embed con datos del personaje
# Mensaje 2: Imágenes (foto de perfil + foto de ficha)

def format_pc_table(historial: list) -> str
# Formatea el historial de puntos como tabla de texto

def calcular_puntos_totales(historial: list) -> int
# Suma todos los puntos del historial de un usuario
```

---

## 📊 Modelo de datos en Google Sheets

### Fichas de personajes

Cada pestaña de fichas usa esta estructura de columnas (adaptada por tipo):

**EstudiantesAprobados:**
```
user_id | generacion | nombre | apellido | edad | año_academico | casa |
clubes | historia | personalidad | apariencia | foto_url | foto_ficha_url |
fecha_aprobacion | aprobado_por
```

**Profesores:**
```
user_id | generacion | nombre | apellido | edad | materia |
historia | experiencia | apariencia | foto_url | foto_ficha_url |
fecha_aprobacion | aprobado_por
```

**Trabajadores:**
```
user_id | generacion | nombre | apellido | edad | cargo |
historia | motivacion | apariencia | foto_url | foto_ficha_url |
fecha_aprobacion | aprobado_por
```

### Fichas de poder (FichasPoder)
```
user_id | generacion | nombre_personaje | categoria_raza (secreta) |
poder | nivel | mana | fecha_aprobacion | aprobado_por
```

### Sistema PCA

**PuntosPC:**
```
user_id | nombre_usuario | puntos_totales | ultima_actualizacion
```

**HistorialPC:**
```
user_id | tipo (positivo/negativo) | cantidad | motivo |
asignado_por | fecha
```

**Sanciones:**
```
id_sancion | user_id | tipo_falta | descripcion | estado |
fecha_sancion | sancionado_por | fecha_resolucion
```

### Estadísticas globales (GlobalStats)
```
generacion | total_estudiantes | total_profesores | total_trabajadores |
total_uniformes | ultima_actualizacion
```

---

## 🔑 Roles del sistema

| Rol | Propósito | Cuándo se asigna |
|-----|-----------|-----------------|
| `ROL_REGISTRADO` | Indica que el usuario tiene al menos una ficha aprobada | Al aprobar la primera ficha |
| `ROL_CONSEJO` | Acceso a comandos de administración y aprobación | Manualmente por admins |
| `ROL_SLOT_ADICIONAL` | Otorga 1 slot extra de personaje | Manualmente por admins (premio/evento) |
| `ROL_RESPIN` | Permite hacer un respin del poder | Manualmente por admins |

---

## 🌀 Sistema de generaciones

Una **generación** representa una "temporada" o "ciclo" del servidor. Al cambiar de generación:

- Los slots de personajes se reinician
- Las fichas del ciclo anterior quedan en Sheets pero no cuentan para los límites
- Los cupos de profesores/trabajadores se reinician (se evalúan por generación)

**Cómo cambiar de generación:**

1. Usar `/admin` → Sección "Generación" → ingresar el nuevo número
2. Actualizar la variable `GENERACION_ACTUAL` en Railway/Render
3. El bot empieza a usar la nueva generación inmediatamente

**Persistencia de la generación:**

```python
def cargar_generacion() -> int:
    # 1. Lee variable de entorno GENERACION_ACTUAL (persiste en Railway)
    gen_env = os.getenv("GENERACION_ACTUAL")
    if gen_env and gen_env.isdigit():
        return int(gen_env)
    
    # 2. Lee data/generacion.json (respaldo local)
    try:
        with open("data/generacion.json") as f:
            return json.load(f)["generacion"]
    except:
        pass
    
    # 3. Valor por defecto
    return 1
```

---

## 🔄 Flujo de aprobación (detalle)

Todos los tipos de fichas siguen el mismo patrón de revisión:

```
1. Usuario completa el formulario
2. Bot envía embed al canal de revisión:
   ┌──────────────────────────────┐
   │  📋 Nueva ficha: Estudiante  │
   │  Usuario: @nombre            │
   │  Nombre: Juan Pérez          │
   │  Casa: Casa1                 │
   │  ...                         │
   │  [✅ Aprobar] [❌ Rechazar]  │
   └──────────────────────────────┘
3. Staff hace clic en Aprobar o Rechazar
4a. Al Aprobar:
    - Mueve datos de Pendientes → Aprobados en Sheets
    - Registra slot en SQLite
    - Asigna ROL_REGISTRADO al usuario
    - Publica ficha en canal de registro (2 mensajes: embed + imágenes)
    - Envía DM al usuario con confirmación
4b. Al Rechazar:
    - Modal pide motivo del rechazo
    - Elimina la fila de Pendientes en Sheets
    - Envía DM al usuario con el motivo
```

---

## 📈 Escalabilidad y limitaciones

| Aspecto | Límite actual | Solución si se supera |
|---------|--------------|----------------------|
| Comandos por guild | ~100 slash commands | Usar grupos de comandos |
| Requests a Sheets | ~60/minuto | Agregar caché en memoria |
| Usuarios concurrentes | Sin límite lógico | El async de discord.py lo maneja |
| Tamaño de la DB SQLite | ~100MB práctico | Migrar a PostgreSQL (sin cambiar la API async) |
| Personajes en Sheets | ~10,000 filas por pestaña | Archivar fichas antiguas a otra hoja |

### Migrar SQLite a PostgreSQL

Si el servidor crece y la base de datos se vuelve un cuello de botella, la migración es sencilla gracias a `aiosqlite`:

1. Reemplazar `aiosqlite` con `asyncpg` o `databases`
2. Actualizar la variable de conexión en `database.py`
3. El resto del código no cambia (mismas funciones, misma API)

---

## 🧩 Agregar un nuevo tipo de personaje

Para agregar, por ejemplo, un tipo "Guardián":

1. **`utils/constants.py`**: Agregar `ROLES_GUARDIAN`, `GUARDIAN_LIMITE`
2. **`cogs/guardianes.py`**: Crear el cog siguiendo la estructura de `profesores.py`
3. **`utils/database.py`**: Agregar columna `guardianes_usados` a `slots_usuarios`
4. **`utils/sheets.py`**: Agregar funciones para la nueva pestaña
5. **Google Sheets**: Crear pestañas `GuardianesPendientes` y `Guardianes`
6. **`bot.py`**: Agregar `"cogs.guardianes"` a la lista de extensiones

---

## 🧩 Agregar o quitar casas

En `utils/constants.py`:

```python
# Cambiar esta lista
CASAS = ["Casa1", "Casa2", "Casa3"]

# Si cada casa tiene un rol:
ROLES_CASAS = {
    "Casa1": 123456789,
    "Casa2": 987654321,
    "Casa3": 111222333,
}
```

El selector de casa en los cogs se construye dinámicamente desde `CASAS`, así que solo necesitas actualizar esa lista.

---

## 🤝 Contribuir

1. Haz fork del repositorio
2. Crea una rama para tu feature: `git checkout -b feature/nueva-funcionalidad`
3. Haz commit de tus cambios: `git commit -m 'Agrega nueva funcionalidad'`
4. Push a tu fork: `git push origin feature/nueva-funcionalidad`
5. Abre un Pull Request

Por favor, sigue el estilo de código existente y documenta las funciones nuevas.

---

---

Construido con ❤️ por **Devilishh** · ¿Soporte técnico? Contacta `devilishh.` en Discord  
Licenciado bajo [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) — libre de usar, no para vender.
