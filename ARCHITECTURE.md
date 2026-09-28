# 🏗️ ArcanaBot Architecture — Technical Reference

This document is the complete technical reference for developers who want to extend, modify or understand the bot's internal workings.

---

## 🧱 Tech stack

| Component | Technology | Version | Notes |
|-----------|-----------|---------|-------|
| Language | Python | 3.11 exactly | 3.12+ removes `audioop` |
| Discord framework | discord.py | 2.4.0 | Slash commands, Views, Modals |
| Local database | SQLite (aiosqlite) | 0.20.0 | Async slot tracking |
| Spreadsheet | gspread + google-auth | 6.0.2 / 2.27.0 | Sheet storage and stats |
| Image generation | Pillow (PIL) | Latest | ID card generation |
| Environment vars | python-dotenv | 1.0.0 | Local configuration |
| Hosting | Railway / Render | — | Cloud hosting |

---

## 📐 Architecture overview

```
Discord ←──→ bot.py (Entry point)
                ├── 11 Cogs (cogs/)
                │     └── Slash commands, Views, Modals, Selects
                ├── utils/constants.py   ← Centralized configuration
                ├── utils/database.py    ← Async SQLite (slots)
                ├── utils/sheets.py      ← Google Sheets (sheets, stats)
                └── utils/helpers.py     ← Embeds, formatting, publishing
```

**Typical interaction flow:**

1. User runs a slash command
2. The corresponding cog shows a Modal or View
3. User fills in the form → callback receives the data
4. Data is validated and saved to Sheets (pending)
5. Staff reviews and approves/rejects in the review channel
6. On approval: Sheets updated, role assigned, user notified

---

## 📦 Modules (Cogs)

### `bot.py` — Main entry point

- Loads all 11 cogs on startup
- `on_ready` event: syncs guild slash commands
- `on_message` event: captures images sent by users (for pending sheet profile photos)
- Sync strategy: **guild-only** (global commands can take up to 1 hour to propagate)

```python
# Cogs loaded on startup
EXTENSIONS = [
    "cogs.admin", "cogs.admin_data",
    "cogs.uniformes", "cogs.estudiantes",
    "cogs.profesores", "cogs.trabajos",
    "cogs.editar_ficha", "cogs.pca",
    "cogs.spins", "cogs.generar_id", "cogs.ver_id"
]
```

---

### `cogs/uniformes.py` — Uniform system

**Command:** `/uniforme`

**Flow:**
```
/uniforme
  → UniformeModal (name, last name, age, reference link)
  → CasaSelectView (house/faction selector)
  → VersionSelectView (Diplomatic / Militarized)
  → Send to review channel (embed with Approve/Reject buttons)
  → Staff approves → moved to UniformesAprobados in Sheets
```

**Sheets involved:** `UniformesPendientes`, `UniformesAprobados`

---

### `cogs/estudiantes.py` — Student registration

**Command:** `/estudiante`

**Flow:**
```
/estudiante
  → Slot availability check
  → Modal 1: Basic info (name, last name, age, academic year)
  → Modal 2: History and personality
  → Modal 3: Appearance and photo
  → CasaSelectView (house selector)
  → ClubesSelectView (multi-select club picker)
  → Profile photo capture (waits for user to send image)
  → Send to review channel
  → Staff approves → slot recorded in SQLite + Sheets
```

**Sheets involved:** `EstudiantesPendientes`, `EstudiantesAprobados`

---

### `cogs/profesores.py` — Professor registration

**Command:** `/profesor`

**Flow:**
```
/profesor
  → MateriaSelectView (checks available slots per generation)
  → Modal 1: Professor info
  → Modal 2: History and experience
  → Modal 3: Appearance and photo
  → Send to review channel
  → Staff approves → slot recorded in SQLite + Sheets
```

**Slot logic:** `get_profesores_aprobados_por_materia(materia)` filters by current generation. If `occupied >= limit`, the request is rejected.

**Sheets involved:** `Profesores`, `TrabajosPendientes`

---

### `cogs/trabajos.py` — Worker registration

**Command:** `/trabajo`

**Flow:**
```
/trabajo
  → CargoSelectView (checks available slots per generation)
  → Modal 1: Worker info
  → Modal 2: History and motivation
  → Modal 3: Appearance and photo
  → Send to review channel
  → Staff approves → slot recorded in SQLite + Sheets
```

**Sheets involved:** `TrabajosPendientes`, `Trabajadores`

---

### `cogs/editar_ficha.py` — Sheet editing

**Command:** `/editar-ficha`

**Flow:**
```
/editar-ficha
  → Type selector (Student / Professor / Worker)
  → Character selector (list of user's sheets)
  → Pre-filled modals with existing data
  → Send to review channel (marked as "EDIT")
  → Staff approves → updates the row in Sheets
```

---

### `cogs/pca.py` — Academic Conduct Points

**Commands:** `/asignar-pc`, `/sancionar`, `/redimir-sancion`, `/apelar`, `/ver-sanciones`, `/historial-pc`

**PCA system structure:**

| Action | Description |
|--------|-------------|
| Assign PC | Staff adds positive or negative points to a user |
| Sanction | Staff registers a formal sanction (minor/major offense/expulsion) |
| Appeal | User requests a sanction review |
| Redeem | Staff approves a redemption process |

**Sheets involved:** `PuntosPC`, `HistorialPC`, `Sanciones`

**Appeal flow:**
```
User /apelar
  → Modal with justification
  → Sent to staff review channel
  → Staff approves → sanction marked as "redeemed"
  → User notified
```

---

### `cogs/spins.py` — Power and battle system

**Commands:** `/poder`, `/respin`, `/iniciar-batalla`

**Power spin flow:**
```
/poder
  → User provides photo of their character sheet
  → Bot spins: selects weighted race category
  → Within category: selects specific power
  → Staff sees category (secret) + the power
  → Staff approves → recorded in FichasPoder + HistorialSpins
  → User receives embed with their power (category hidden)
```

**The 7 race categories (secret, staff-only):**

| Emoji | Category | Weight (%) | Description |
|-------|----------|-----------|-------------|
| ⚪ | Básico (Basic) | 40% | Most common race |
| 🔵 | Sensitivo (Sensitive) | 25% | Slightly uncommon |
| 🟢 | Épico (Epic) | 15% | Infrequent |
| 🟡 | Mítico (Mythic) | 10% | Rare |
| 🟠 | Legendario (Legendary) | 6% | Very rare |
| 🔴 | Maldito (Cursed) | 3% | Extremely rare |
| ✨ | Divino (Divine) | 1% | Near impossible |

Selection uses `random.choices()` with the weights defined in `CATEGORIAS_RAZA` inside `constants.py`.

**Battle system flow:**
```
/iniciar-batalla @rival
  → Bot verifies both users have approved power sheets
  → Creates BatallaActivaView with buttons:
     ⚔️ Roll      → generates random result for both
     🏆 End       → winner selector → records in HistorialBatallas
     🏳️ Cancel    → cancels the battle
```

**Sheets involved:** `FichasPoder`, `HistorialSpins`, `HistorialBatallas`

---

### `cogs/generar_id.py` — ID card generation

**Command:** `/generar-id`

**Process:**
```
/generar-id @user
  → Looks up user data in Sheets (student or worker)
  → Opens PNG template (assets/IDEstudiante.png or assets/IDWorker.png)
  → Draws text over template with PIL/Pillow:
     - Full name
     - House / Position
     - Academic year / Position description
     - Unique ID code
  → Downloads user's Discord profile photo
  → Places it in the designated position on the template
  → Saves result as temporary image
  → Sends in the channel and records the code in CodigosID in Sheets
```

**Sheets involved:** `CodigosID`, `EstudiantesAprobados`, `Trabajadores`

---

### `cogs/ver_id.py` — View ID cards

**Command:** `/ver-id`

Looks up the user's registered ID in `CodigosID` and regenerates it from the saved photo URL.

---

### `cogs/admin.py` — Admin panel

**Command:** `/admin` (staff with council role only)

**AdminStatsView — 5 sections:**

| Button | Description |
|--------|-------------|
| 📊 Statistics | Character totals, slot usage, global stats |
| 👥 Users | Slot info for a specific user |
| 🎓 Generation | Change the active server generation |
| 🔄 Mass reset | Reset all slots (new generation) |
| ❌ Close | Close the panel |

**Generation logic:**

`cargar_generacion()` reads in this priority order:
1. Environment variable `GENERACION_ACTUAL` (persists on Railway)
2. File `data/generacion.json` (local backup)
3. Default value: `1`

---

### `cogs/admin_data.py` — Data management

**Commands:**

| Command | Description |
|---------|-------------|
| `/admin-data ver @user` | List all characters of a user |
| `/admin-data eliminar-personaje @user` | Delete a specific character |
| `/admin-data eliminar-tipo @user type` | Delete all characters of a type |
| `/admin-data reset-slots @user` | Reset slot counters |
| `/admin-data reset-total @user` | Delete all user data |

---

## 🔧 Utility modules

### `utils/constants.py`

The bot's central configuration file. **Everything configurable lives here.**

Key variables:

```python
# Server IDs
GUILD_ID              # Discord server ID
CANAL_REVISION_FICHAS # Channel where staff reviews sheets
CANAL_REVISION_PODER  # Channel where staff reviews powers
CANAL_REGISTRO_*      # Channels where approved sheets are published

# Role IDs
ROL_REGISTRADO        # Role assigned when a sheet is approved
ROL_CONSEJO           # Staff role with access to admin commands
ROL_SLOT_ADICIONAL    # Role that grants one extra character slot
ROL_RESPIN            # Role that allows a power respin

# Character configuration
CASAS                 # List of available houses/factions
MATERIAS              # List of subjects for professors
MATERIAS_LIMITE       # Max slots per subject per generation
CARGOS                # List of positions for workers
CARGOS_LIMITE         # Max slots per position per generation
CLUBES                # List of clubs for students
SLOTS_BASE            # Base slots per character type

# Power system (don't change weights without adjusting logic)
CATEGORIAS_RAZA       # 7 categories with weighted probabilities
NIVELES_PODER         # Power levels per category
DESCRIPCIONES_MANA    # Mana type descriptions

# Embed colors
COLOR_OK              # Green (approved)
COLOR_ERROR           # Red (rejected)
COLOR_INFO            # Blue (info)
COLOR_PENDIENTE       # Yellow (pending)
```

---

### `utils/database.py`

Async SQLite operations for character slot tracking.

**Main functions:**

```python
async def init_db()
# Creates tables if they don't exist

async def get_conteo_usuario(user_id: int, generacion: int) -> dict
# Returns how many characters of each type the user has in the current generation

async def registrar_personaje(user_id: int, generacion: int, tipo: str)
# Increments the counter for the given type ("estudiantes", "trabajadores", "profesores")

async def reset_usuario(user_id: int, generacion: int)
# Resets all counters for a user to 0

async def agregar_slot_extra(user_id: int, generacion: int, cantidad: int)
# Adds extra slots to the user (for the ROL_SLOT_ADICIONAL role)

async def get_todos_los_usuarios(generacion: int) -> list
# Returns all records for the current generation (for admin stats)
```

**`slots_usuarios` table schema:**

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

Google Sheets integration for persistent storage of sheets and statistics.

**Main functions:**

```python
def get_sheet(nombre: str) -> gspread.Worksheet
# Gets a spreadsheet tab by name

def agregar_fila(nombre_hoja: str, fila: list)
# Appends a row to the end of the given sheet

def get_todas_las_filas(nombre_hoja: str) -> list[dict]
# Returns all rows as a list of dicts (uses first row as headers)

def actualizar_fila(nombre_hoja: str, col_busqueda: str, val_busqueda: str, datos: dict)
# Finds a row by value in a column and updates the given fields

def get_personajes_usuario(user_id: int) -> list[dict]
# Returns all approved characters for a user (searches all sheets)

def get_profesores_aprobados_por_materia(materia: str, gen: int) -> int
# Counts approved professors for a subject in the current generation

def get_trabajadores_aprobados_por_cargo(cargo: str, gen: int) -> int
# Counts approved workers for a position in the current generation
```

**⚠️ Note on Sheets rate limits:**

The Google Sheets API has a limit of ~60 requests per minute. If the bot makes many operations in a short time, it may receive `APIError: RESOURCE_EXHAUSTED`. Solutions:
- In-memory cache for data that doesn't change frequently
- Batch read operations
- `asyncio.sleep(1)` between bulk operations

---

### `utils/helpers.py`

Helper functions for building embeds and publishing sheets.

**Main functions:**

```python
def build_review_embed(tipo: str, data: dict, user: discord.Member) -> discord.Embed
# Builds the review embed for the staff channel
# tipo: "uniforme" | "estudiante" | "profesor" | "trabajador" | "poder"

def build_acceptance_embed(tipo: str, data: dict) -> discord.Embed
# Builds the confirmation embed sent to the user on approval

async def publicar_ficha_con_imagenes(channel, embed, foto_url, foto_ficha_url)
# Publishes the approved sheet in the registration channel in two messages:
# Message 1: Embed with character data
# Message 2: Images (profile photo + sheet photo)

def format_pc_table(historial: list) -> str
# Formats points history as a text table

def calcular_puntos_totales(historial: list) -> int
# Sums all points in a user's history
```

---

## 📊 Google Sheets data model

### Character sheets

Each character tab uses this column structure (adapted per type):

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

### Power sheets (FichasPoder)
```
user_id | generacion | nombre_personaje | categoria_raza (secret) |
poder | nivel | mana | fecha_aprobacion | aprobado_por
```

### PCA system

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

### Global statistics (GlobalStats)
```
generacion | total_estudiantes | total_profesores | total_trabajadores |
total_uniformes | ultima_actualizacion
```

---

## 🔑 Role reference

| Role | Purpose | When assigned |
|------|---------|--------------|
| `ROL_REGISTRADO` | Indicates the user has at least one approved sheet | On first sheet approval |
| `ROL_CONSEJO` | Staff access to admin and approval commands | Manually by admins |
| `ROL_SLOT_ADICIONAL` | Grants 1 extra character slot | Manually by admins (reward/event) |
| `ROL_RESPIN` | Allows a power respin | Manually by admins |

---

## 🌀 Generation system

A **generation** represents a "season" or "cycle" of the server. When changing generations:

- Character slots reset
- Previous cycle sheets remain in Sheets but don't count toward limits
- Professor/worker slots reset (evaluated per generation)

**How to change generations:**

1. Use `/admin` → "Generation" section → enter the new number
2. Update the `GENERACION_ACTUAL` variable in Railway/Render
3. The bot starts using the new generation immediately

**Generation persistence:**

```python
def cargar_generacion() -> int:
    # 1. Read GENERACION_ACTUAL env var (persists on Railway)
    gen_env = os.getenv("GENERACION_ACTUAL")
    if gen_env and gen_env.isdigit():
        return int(gen_env)
    
    # 2. Read data/generacion.json (local backup)
    try:
        with open("data/generacion.json") as f:
            return json.load(f)["generacion"]
    except:
        pass
    
    # 3. Default value
    return 1
```

---

## 🔄 Approval flow (detailed)

All sheet types follow the same review pattern:

```
1. User fills in the form
2. Bot sends embed to review channel:
   ┌──────────────────────────────┐
   │  📋 New sheet: Student       │
   │  User: @name                 │
   │  Name: John Doe              │
   │  House: House1               │
   │  ...                         │
   │  [✅ Approve] [❌ Reject]    │
   └──────────────────────────────┘
3. Staff clicks Approve or Reject
4a. On Approve:
    - Moves data from Pending → Approved in Sheets
    - Records slot in SQLite
    - Assigns ROL_REGISTRADO to the user
    - Publishes sheet in registration channel (2 messages: embed + images)
    - Sends DM to user with confirmation
4b. On Reject:
    - Modal requests rejection reason
    - Deletes the row from Pending in Sheets
    - Sends DM to user with the reason
```

---

## 📈 Scalability and limitations

| Aspect | Current limit | Solution if exceeded |
|--------|--------------|---------------------|
| Commands per guild | ~100 slash commands | Use command groups |
| Sheets requests | ~60/minute | Add in-memory cache |
| Concurrent users | No logical limit | discord.py's async handles it |
| SQLite DB size | ~100MB practical | Migrate to PostgreSQL (same async API) |
| Characters in Sheets | ~10,000 rows per tab | Archive old sheets to another tab |

### Migrating SQLite to PostgreSQL

If the server grows and the database becomes a bottleneck, migration is straightforward thanks to `aiosqlite`:

1. Replace `aiosqlite` with `asyncpg` or `databases`
2. Update the connection variable in `database.py`
3. The rest of the code stays the same (same functions, same API)

---

## 🧩 Adding a new character type

To add, for example, a "Guardian" type:

1. **`utils/constants.py`**: Add `ROLES_GUARDIAN`, `GUARDIAN_LIMITE`
2. **`cogs/guardianes.py`**: Create the cog following the structure of `profesores.py`
3. **`utils/database.py`**: Add `guardianes_usados` column to `slots_usuarios`
4. **`utils/sheets.py`**: Add functions for the new tab
5. **Google Sheets**: Create `GuardianesPendientes` and `Guardianes` tabs
6. **`bot.py`**: Add `"cogs.guardianes"` to the extensions list

---

## 🧩 Adding or removing houses

In `utils/constants.py`:

```python
# Change this list
CASAS = ["House1", "House2", "House3"]

# If each house has a role:
ROLES_CASAS = {
    "House1": 123456789,
    "House2": 987654321,
    "House3": 111222333,
}
```

The house selector in the cogs is built dynamically from `CASAS`, so you only need to update that list.

---

## 🤝 Contributing

1. Fork the repository
2. Create a branch for your feature: `git checkout -b feature/new-feature`
3. Commit your changes: `git commit -m 'Add new feature'`
4. Push to your fork: `git push origin feature/new-feature`
5. Open a Pull Request

Please follow the existing code style and document any new functions.

---

Built with ❤️ by **Devilishh** · Need technical support? Contact `devilishh.` on Discord  
Licensed under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) — free to use, not for sale.
