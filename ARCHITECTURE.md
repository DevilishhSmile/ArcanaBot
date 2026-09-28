# 🔮 ArcanaBot — Architecture & Feature Reference

> This document describes the complete technical architecture, all implemented features, and the data model of ArcanaBot. Use this as a reference when extending or maintaining the bot.

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Discord library | discord.py 2.4.0 |
| Local storage | SQLite (aiosqlite) |
| Remote storage | Google Sheets (gspread) |
| Auth | google-auth (Service Account) |
| Config | python-dotenv |
| Hosting | Railway (recommended) / Render |

---

## 📁 Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                   Discord Server                 │
│  Users → Slash Commands → Bot → Views/Modals    │
└───────────────────┬─────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────┐
│                  bot.py (entry)                  │
│  - Loads all cogs                               │
│  - Registers slash commands per guild           │
│  - Handles on_message for image capture         │
│  - Persists pending review views on restart     │
└───────┬───────────────────────┬─────────────────┘
        │                       │
┌───────▼───────┐     ┌─────────▼──────────┐
│  cogs/ (12)   │     │  utils/ (5)         │
│  Commands &   │     │  Shared services    │
│  UI Views     │     │  & helpers          │
└───────┬───────┘     └─────────┬──────────┘
        │                       │
        └──────────┬────────────┘
                   │
    ┌──────────────▼──────────────┐
    │   Data Layer                │
    │   SQLite (slots)            │
    │   Google Sheets (all data)  │
    └─────────────────────────────┘
```

---

## 🧩 Cogs Reference

### `cogs/admin.py`
Main admin cog. Contains:
- `/reclamar-slot` — activates extra character slot from store role
- `/mis-personajes` — shows slot usage and character list with navigation
- `/ver-personajes @user` — staff view of any user's characters
- `/eliminar-personaje` — request to delete a character (staff approval required)
- `/admin-stats` — 5-section interactive stats panel
- `/panel-uniformes` — mass uniform review with navigation
- `/generacion ver/cambiar/historial` — generation management
- `cargar_generacion()` — reads from `GENERACION_ACTUAL` env var → fallback to JSON file → fallback to 1
- `guardar_generacion()` — saves to local JSON (reminder to update Railway var manually)
- `AdminStatsView` — 5-tab interactive panel (General, Moderation, PCA, Spins, Battles)
- All UI views for character deletion, uniform panel, generation confirmation

### `cogs/admin_data.py`
Data management for staff:
- `/admin-data ver @user` — shows all registered data for a user
- `/admin-data eliminar-personaje @user name` — deletes one specific character
- `/admin-data eliminar-tipo @user type` — deletes all characters of a type (student/professor/worker/uniform)
- `/admin-data reset-slots @user` — resets only SQLite slot counters to 0
- `/admin-data reset-total @user` — full reset (all characters + uniforms + slots) — irreversible

### `cogs/uniformes.py`
Uniform registration flow:
1. `/uniforme` → `UniformeModal` (character name)
2. `CasaSelectView` → house selection
3. `VersionSelectView` → uniform version (Diplomatic / Militarized)
4. Image sent in channel → captured by `bot.py` `on_message`
5. Review embed sent to staff channel → `UniformeReviewView` (Approve/Reject)

### `cogs/estudiantes.py`
Student registration (3 modals + selectors):
1. `/ficha-estudiante` → checks uniform approved + slot available
2. Modal 1: name, age (max 18), pronouns, species, element
3. House selector
4. Modal 2: powers, weaknesses, personality, history
5. Modal 3: hobbies, likes, dislikes
6. Club selector (multiple choice, maps to Discord roles)
7. Image in channel
8. Staff review → `EstudianteReviewView` → on approve: roles assigned, acceptance letter sent, card published in 2 messages, ID generated

### `cogs/profesores.py`
Professor registration:
1. `/ficha-profesor` → subject selector (25 subjects + substitute button)
2. Modal 1: name, age (min 25), pronouns, species, element
3. Modal 2: powers, weaknesses, personality, history
4. Modal 3: hobbies, likes, dislikes
5. Image in channel
6. Staff review → on approve: professor role assigned, card published

### `cogs/trabajos.py`
Worker registration:
1. `/ficha-trabajador` → position selector (checks quota)
2. Modal 1: name, age (min 25), pronouns, species, element
3. Modal 2: powers, weaknesses, personality, history
4. Modal 3: hobbies, likes, dislikes
5. Image in channel
6. Staff review → on approve: worker role assigned, card published

### `cogs/editar_ficha.py`
Character editing:
- `/editar-ficha [name]` — opens pre-filled modals with current data
- Supports students, professors, and workers
- Changes go through staff review before publishing

### `cogs/pca.py`
Academic Points System (full moderaton subsystem):
- `/asignar-pc-nota @user grade reason` — assigns PC by academic grade
- `/asignar-pc-directo @user pc reason` — direct PC assignment (Council only)
- `/aplicar-sancion @user type reason` — applies sanction
- `/marcar-sancion-cumplida @user` — marks sanction as fulfilled
- `/limpiar-sanciones @user` — clears active sanctions
- `/limpiar-pc mode [user]` — resets PC for one or all
- `/ver-pc @user` — balance + active sanctions (character selector)
- `/historial-pc @user` — full PC history (character selector)
- `/canjear-pc` — redeem PC to reduce active sanction
- `/apelar` — appeal suspension/expulsion (character owner only)
- Automatic approval flow in `CANAL_APROBACIONES` for suspensions, expulsions, professor detentions
- 4-rejection protocol: auto-mentions staff for personal assistance

### `cogs/spins.py`
Power Spin + Battle System:
- `/spin-poder` — generates level (low/medium/high) and mana (0-10)
- Power sheet modal (abilities + weaknesses)
- Staff review → category assignment (secret, 7 tiers) → DM with full info on approval
- `/editar-ficha-poder [name]` — edit approved power sheet (abilities/weaknesses only, stats preserved)
- `/respin-personaje` — full re-roll (requires store role `ROL_RESPIN`)
- `/ver-ficha-poder [name]` — public power sheet view with navigation
- `/batalla @rival` — initiates battle, both users select characters
- `BatallaActivaView` — ⚔️ Roll / 🏆 End / 🏳️ Cancel buttons
- `SeleccionarGanadorView` — winner selection on battle end
- `/historial-batalla [name]` — battle history per character

### `cogs/generar_id.py`
ID card generation:
- Auto-triggered on character approval
- `/generar-id` — manual generation
- Fills image template with: photo, unique code, name, age, species, element, clubs, house, generation, join date, signature
- Code format: `STU0001`, `PRF0001`, `WRK0001` (type + sequential number)

### `cogs/ver_id.py`
- `/ver-id [name]` — view any character's ID card

---

## 🔧 Utils Reference

### `utils/constants.py`
**The main configuration file.** All server-specific values live here:
- `CASAS` — list of house names
- `CARGOS` — dict of position name → max slots (None = 1)
- `MATERIAS` — list of subject names
- `MATERIAS_LIMITE` — dict of subject → max professors
- `CLUBES` — dict of club name → Discord role ID
- `SLOTS_CONFIG` — per-generation slot limits
- `TABLA_NOTAS_PC` — grade-to-PC conversion table
- `TIPOS_SANCION` — sanction type configurations
- `CATEGORIAS_RAZA` — 7 race categories for power system (secret)
- `NIVELES_PODER` — power level descriptions
- `DESCRIPCIONES_MANA` — mana value descriptions
- All channel/role ID constants loaded from env vars

### `utils/database.py`
SQLite operations via `aiosqlite`:
- `init_db()` — creates `slots_usuarios` table if not exists
- `get_conteo_usuario(user_id, generation)` — returns slot usage dict
- `puede_registrar(user_id, type, generation, limit)` — checks if registration is allowed
- `registrar_personaje(user_id, type, generation)` — increments slot counter
- `restar_personaje(user_id, type, generation)` — decrements slot counter
- `agregar_slot_extra(user_id, generation)` — adds extra slot
- `usar_slot_extra(user_id, type, generation)` — uses extra slot
- `reset_usuario(user_id, generation)` — resets all counters to 0

**Table: `slots_usuarios`**
```sql
user_id                 INTEGER
generacion              INTEGER
estudiantes_usados      INTEGER DEFAULT 0
trabajadores_usados     INTEGER DEFAULT 0
profesores_usados       INTEGER DEFAULT 0
slots_extra_disponibles INTEGER DEFAULT 0
slots_extra_usados      INTEGER DEFAULT 0
PRIMARY KEY (user_id, generacion)
```

### `utils/sheets.py`
Google Sheets operations:
- All CRUD operations for each sheet
- `actualizar_global_stats()` — recalculates and updates GlobalStats sheet
- `get_global_stats()` — reads GlobalStats
- `get_personajes_usuario(user_id)` — returns all characters across sheets
- `get_profesores_aprobados_por_materia(subject)` — filtered by current generation
- `get_trabajadores_aprobados_por_cargo(position)` — filtered by current generation
- `eliminar_personaje_sheets(user_id, name, type)` — removes from appropriate sheet
- Approval/rejection functions for each character type

### `utils/helpers.py`
- `is_valid_character_name(name)` — validates name (letters only, no numbers)
- `clean_field(text)` — sanitizes text input
- `build_review_embed(type, data)` — builds the staff review embed for any character type
- `format_ficha_*()` — formats character sheets for public publication

### `utils/image_handler.py`
- `registrar_espera(user_id, type, channel_id, data)` — registers that bot is waiting for image
- `get_espera(user_id)` — checks if there's a pending image wait
- `limpiar_espera(user_id)` — clears pending wait
- Used by `bot.py`'s `on_message` handler to capture images after form completion

---

## 🔄 Key Flows

### Character Registration Flow
```
User: /ficha-estudiante
  → Check uniform approved
  → Check slot available (SQLite)
  → Modal 1 (data)
  → House selector
  → Modal 2 (powers/history)
  → Modal 3 (personality)
  → Club selector
  → Wait for image (image_handler)
User: [sends image in channel]
  → bot.py on_message captures it
  → Review embed sent to CANAL_REVISION_FICHAS
Staff: [clicks Approve]
  → Roles assigned (character type + Registered + clubs)
  → Slot counter incremented (SQLite)
  → Character saved to Sheets
  → Card published in 2 messages
  → Acceptance letter sent
  → ID card auto-generated
```

### Image Capture Flow
`bot.py` has a single `on_message` handler that:
1. Checks if user has a pending image wait (`image_handler.get_espera`)
2. Captures ALL attachments from the message (not just first)
3. Routes to the appropriate processing function (`_procesar_uniforme`, `_procesar_ficha`, etc.)
4. Clears the pending wait

### Generation System
- Generation stored in Railway env var `GENERACION_ACTUAL`
- `cargar_generacion()` priority: env var → JSON file → default 1
- All slot checks use the current generation
- Sheets data filtered by generation for quota checks
- When advancing generation: use `/generacion cambiar` → also update Railway variable manually

---

## 📊 Google Sheets Data Model

All 16 sheets and their purposes:

| Sheet | Purpose | Filtered by gen? |
|---|---|---|
| UniformesPendientes | Uniforms awaiting review | No |
| UniformesAprobados | Approved uniforms (gate for students) | No |
| EstudiantesPendientes | Student sheets awaiting review | No |
| EstudiantesAprobados | Approved student sheets | No |
| Profesores | Professor sheets with status | Yes (quota) |
| Trabajadores | Worker sheets with status | Yes (quota) |
| TrabajosPendientes | Prof/worker sheets awaiting review | No |
| GlobalStats | Auto-updated server counters | No |
| PuntosPC | PC balance per character | No |
| HistorialPC | Full PC assignment history | No |
| Sanciones | All sanctions with status | No |
| FichasPoder | Power sheets with stats and status | No |
| HistorialSpins | Log of all spins performed | No |
| HistorialBatallas | Battle results per character | No |
| CodigosID | Generated ID codes and photo URLs | No |

---

## 🔐 Roles Used

| Constant | Purpose |
|---|---|
| `ROL_STAFF` | Can use all admin commands |
| `ROL_ESTUDIANTE` | Assigned on student approval |
| `ROL_PROFESOR` | Assigned on professor approval |
| `ROL_TRABAJADOR` | Assigned on worker approval |
| `ROL_REGISTRADO` | Assigned to all approved characters |
| `ROL_CONSEJO` | Can assign direct PC (Trabajo Sucio) |
| `ROL_SLOT_ADICIONAL` | Store role → `/reclamar-slot` converts to slot |
| `ROL_RESPIN` | Store role → enables `/respin-personaje` |

---

## 📈 Scaling Notes

### Current limits
- SQLite works well up to ~500 concurrent active users
- Google Sheets API: 60 read requests/minute (shared across all operations)
- Discord slash commands: registered per-guild (no global limit issues)

### When to migrate to PostgreSQL
If your server exceeds ~500 active registered users, migrate `utils/database.py`:
1. Add `asyncpg` to `requirements.txt`
2. Replace `aiosqlite.connect(DB_PATH)` with `asyncpg.connect(DATABASE_URL)`
3. Update SQL syntax (PostgreSQL uses `$1, $2` placeholders instead of `?`)
4. Add `DATABASE_URL` to environment variables (Railway provides this automatically with their PostgreSQL addon)

### Google Sheets rate limiting
If you hit 429 errors frequently:
- Add exponential backoff to `utils/sheets.py` operations
- Consider batching multiple cell updates into single API calls
- For heavy read operations, implement a local cache with TTL

---

## 🏷️ Race Categories (Power System — Staff Only)

The 7 secret race categories assigned by staff on power sheet approval:

| Key | Name | Description |
|---|---|---|
| `basico` | ⚪ Basic | Humans with magical spark, elemental sensitivity |
| `sensitivo` | 🔵 Sensitive | Minor bloodline mages, passive supernatural gifts |
| `epico` | 🟢 Epic | Mutants, hybrid species, altered-form magic |
| `mitico` | 🟡 Mythic | Fantasy creatures: Goblins, Orcs, Elves, Fairies |
| `legendario` | 🟠 Legendary | Mythological beings: Phoenix, Pegasus, Kraken, Kitsune |
| `maldito` | 🔴 Cursed | Ghosts, Yokai, Demons, Vampires, divine curses |
| `divino` | ✨ Divine | Gods, Angels, Blessed beings, Divine avatars |

---

*ArcanaBot Architecture Reference — Keep this document updated when adding new features*
