# 🔮 ArcanaBot — Discord RP Academy Bot

**ArcanaBot** is a fully-featured Discord bot designed for roleplay academy servers. It handles character registration, staff review workflows, academic points, power spins, battle systems, and much more — all integrated with Google Sheets for persistent data storage.

> Built with ❤️ by **Agnes** · Need technical support? Contact: `devilishh.` on Discord

---

## ✨ Features

### 👕 Uniform System
- Players submit their character's uniform via `/uniforme`
- Select house and uniform version (Diplomatic / Militarized)
- Staff reviews and approves/rejects with reason
- Mass review panel with `/panel-uniformes`

### 📋 Character Registration
- **Students** (`/ficha-estudiante`) — up to 3 per user, requires approved uniform
- **Professors** (`/ficha-profesor`) — up to 2 per user, subject selection
- **Workers** (`/ficha-trabajador`) — up to 2 per user, position selection
- Multi-part forms (data, powers/history, personality/hobbies)
- House selection, club selection with automatic role assignment
- Fully published in 2 messages to avoid Discord's 2000 char limit

### 🪪 ID Card System
- Auto-generated ID card on character approval
- Manual generation with `/generar-id`
- View any character's ID with `/ver-id`
- Unique codes per character type (STU/PRF/WRK + sequential number)

### ✏️ Character Editing
- `/editar-ficha` — edit any approved character with pre-filled data
- Changes go through staff review before publishing

### ⚠️ Academic Points System (PCA)
- Professors assign PC points by grade (3.5→1PC up to 5.0→10PC)
- Council assigns direct PC for special tasks (5-10 PC)
- Points can be redeemed to reduce sanctions
- Sanction types: minor punishment, detention, suspension, expulsion
- Automatic approval flow for suspensions and expulsions
- Appeal system for suspensions/expulsions
- Full history tracking in Google Sheets

### ✨ Power Spin System
- `/spin-poder` — generates random power stats (level + mana)
- Staff assigns secret race category on approval (7 tiers: Basic to Divine)
- Power sheet review with rejection protocol (4 rejections = assistance protocol)
- Re-spin system via store item (Discord role)
- Public power sheet viewing

### ⚔️ Battle System
- `/batalla @rival` — initiates a narrative battle
- Probability-based hit calculation from power stats
- Immersive narrative results via buttons (no extra commands needed)
- Battle history tracked per character
- Cancel or conclude battles at any time

### 🎰 Slot System
- Configurable slots per generation per character type
- Extra slots via store role + `/reclamar-slot`
- Per-generation tracking in SQLite

### 📊 Admin Panel
- `/admin-stats` — 5-section interactive panel:
  - 📋 General (approvals, pending, quotas)
  - ⚠️ Moderation (sanctions by type, top sanctioned, most active staff)
  - 💎 PCA (PC totals, top characters, top assigners)
  - ✨ Spins (approved/pending/rejected, by level and race category)
  - ⚔️ Battles (total battles, top winners, most active)

### 🗂️ Data Management
- `/admin-data ver/eliminar-personaje/eliminar-tipo/reset-slots/reset-total`
- Full user data control for staff

### 📚 Generation System
- Multi-generation support
- `/generacion ver/cambiar/historial`
- Generation persists via Railway environment variable

---

## 🛠️ Installation Guide

### Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | 3.11.x | Must be exactly 3.11 (3.13 removes `audioop`) |
| Git | Any | For cloning and version control |
| Node.js | 18+ | Only needed for local docx generation (optional) |

---

### STEP 1 — Install Python 3.11

1. Go to https://www.python.org/downloads/
2. Download **Python 3.11.x** (not 3.12 or 3.13)
3. During installation, check **"Add Python to PATH"** ✅
4. Verify in terminal:
```bash
python --version
# Expected: Python 3.11.x
```

---

### STEP 2 — Clone the repository

```bash
git clone https://github.com/your-username/arcana-bot.git
cd arcana-bot
```

Or download the ZIP from GitHub and extract it.

---

### STEP 3 — Create virtual environment and install dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

You should see `(venv)` in your terminal prompt.

---

### STEP 4 — Create your Discord Bot

1. Go to https://discord.com/developers/applications
2. Click **"New Application"** → give it a name → **Create**
3. Go to **Bot** in the left menu
4. Click **"Add Bot"** → confirm
5. Enable these **Privileged Gateway Intents**:
   - ✅ Server Members Intent
   - ✅ Message Content Intent
6. Click **"Reset Token"** → copy it (you only see it once!)

**Invite the bot to your server:**

1. Go to **OAuth2 → URL Generator**
2. In **Scopes**, check: `bot` and `applications.commands`
3. In **Bot Permissions**, check:
   - Manage Roles
   - Send Messages
   - Embed Links
   - Attach Files
   - Read Message History
   - Use Slash Commands
4. Copy the generated URL, open it in your browser, select your server

---

### STEP 5 — Set up Google Sheets

1. Go to https://console.cloud.google.com/
2. Create a new project
3. Enable these APIs:
   - **Google Sheets API**
   - **Google Drive API**
4. Go to **Credentials → Create Credentials → Service Account**
5. Give it any name → **Create and Continue → Done**
6. Click on the service account → **Keys → Add Key → JSON**
7. Download the JSON file
8. Rename it to `credentials.json` and place it in the `data/` folder
9. Copy the service account email (looks like `bot@project.iam.gserviceaccount.com`)
10. Create a new Google Spreadsheet
11. Share it with the service account email with **Editor** permissions
12. Copy the Spreadsheet ID from the URL:
    `https://docs.google.com/spreadsheets/d/`**`THIS_IS_THE_ID`**`/edit`

**Create these sheets (tabs) in the spreadsheet** with exactly these column headers in row 1:

| Sheet Name | Columns (row 1) |
|---|---|
| `UniformesPendientes` | user_id, username, personaje, link_imagen, fecha, estado, staff_que_reviso, motivo_rechazo, notas, mensaje_id |
| `UniformesAprobados` | user_id, personaje, link_imagen, fecha, staff_que_reviso, estado |
| `EstudiantesPendientes` | user_id, username, personaje, club, elemento, imagen, fecha, staff_que_reviso, motivo, link_ficha_final, estado, notas, generacion, mensaje_id |
| `EstudiantesAprobados` | user_id, username, personaje, elemento, club, link_ficha, fecha, staff_que_reviso, generacion, especie, casa |
| `Profesores` | user_id, username, personaje, materia, subcargo, link_ficha, fecha, staff_que_reviso, estado, generacion |
| `Trabajadores` | user_id, username, personaje, cargo, subcargo, link_ficha, fecha, staff_que_reviso, estado, generacion |
| `TrabajosPendientes` | user_id, username, personaje, cargo, subcargo, materia, notas, fecha, estado, staff_que_reviso, motivo, link_ficha_final, generacion, mensaje_id |
| `GlobalStats` | categoria, valor |
| `PuntosPC` | user_id, username, personaje, pc_total, pc_disponible, fecha_actualizacion |
| `HistorialPC` | user_id, personaje, pc_otorgados, motivo, asignado_por, fecha |
| `Sanciones` | user_id, username, personaje, tipo, duracion, estado, asignado_por, fecha, motivo |
| `FichasPoder` | user_id, username, personaje, categoria_raza, nivel_poder, mana, habilidades, debilidades, estado, staff_que_reviso, fecha, motivo_rechazo, denegaciones |
| `HistorialSpins` | user_id, personaje, nivel_poder, mana, fecha |
| `HistorialBatallas` | user_id, personaje, rival_user_id, rival_personaje, resultado, fecha |
| `CodigosID` | user_id, personaje, tipo, codigo, foto_url, fecha |

**For the `GlobalStats` sheet**, add these values in column A (column B will be auto-filled by the bot):

```
estudiantes_total
trabajadores_total
profesores_total
uniformes_aprobados
fichas_aprobadas
trabajos_aprobados
pendientes_totales
uniformes_pendientes
fichas_pendientes
trabajos_pendientes
```

---

### STEP 6 — Configure environment variables

Copy `.env.example` to `.env` and fill in all values:

```bash
cp .env.example .env
```

Then edit `.env`:

```env
# ── DISCORD ──────────────────────────────────
DISCORD_TOKEN=your_bot_token_here
GUILD_ID=your_server_id_here

# ── GOOGLE SHEETS ────────────────────────────
GOOGLE_SHEETS_ID=your_spreadsheet_id_here

# ── CHANNELS ─────────────────────────────────
CANAL_ENVIAR_UNIFORME=channel_id
CANAL_REGISTRAR_ESTUDIANTE=channel_id
CANAL_REGISTRO_TRABAJOS=channel_id
CANAL_CARTA_ACEPTACION=channel_id
CANAL_FICHAS_ESTUDIANTES=channel_id
CANAL_FICHAS_PROFESORES=channel_id
CANAL_FICHAS_TRABAJADORES=channel_id
CANAL_REVISION_UNIFORMES=channel_id
CANAL_REVISION_FICHAS=channel_id
CANAL_LOGS_BOT=channel_id
CANAL_SANCIONES=channel_id

# ── ROLES ────────────────────────────────────
ROL_STAFF=role_id
ROL_ESTUDIANTE=role_id
ROL_PROFESOR=role_id
ROL_TRABAJADOR=role_id

# ── GENERATION ───────────────────────────────
GENERACION_ACTUAL=1
```

**How to get Discord IDs:**
1. Enable Developer Mode: Discord Settings → Advanced → Developer Mode ✅
2. Right-click any channel/role/server → **Copy ID**

---

### STEP 7 — Configure the bot for your server

Open `utils/constants.py` and customize these sections:

```python
# ── HOUSES ── Change names and count here
CASAS = ["House1", "House2", "House3", "House4"]

# ── POSITIONS ── Edit names and slot limits
CARGOS = {
    "Librarian": 2,
    "Secretary": 2,
    # ... add or remove as needed
}

# ── SUBJECTS ── Edit for your server's curriculum
MATERIAS = [
    "Subject 1",
    "Subject 2",
    # ...
]

# ── CLUBS ── Map club names to Discord role IDs
CLUBES = {
    "Club Name": role_id_here,
    # ...
}

# ── SPECIAL ROLES ──
ROL_SLOT_ADICIONAL = role_id  # Role given when buying extra slot from store
ROL_REGISTRADO     = role_id  # Role assigned to all approved characters
ROL_CONSEJO        = role_id  # Council role (can assign direct PC)
```

---

### STEP 8 — Run the bot locally

```bash
# Make sure your virtual environment is active
python bot.py
```

Expected output:
```
✅ Cog cargado: cogs.admin
✅ Cog cargado: cogs.uniformes
...
✅ Bot conectado como YourBot#1234 (ID: 123456789)
✅ Base de datos SQLite lista
✅ 31 comando(s) sincronizados
[SHEETS] ✅ Conectado a Google Sheets
```

---

## 🚀 Deploy to Railway (Recommended — Free)

Railway keeps your bot running 24/7 for free.

1. Go to https://railway.app and create an account
2. Click **New Project → Deploy from GitHub repo**
3. Connect your GitHub account and select your repository
4. Railway will auto-detect Python and use `Procfile`
5. Go to your project → **Variables** tab → add all variables from your `.env`:
   - `DISCORD_TOKEN`
   - `GUILD_ID`
   - `GOOGLE_SHEETS_ID`
   - All channel and role IDs
   - `GENERACION_ACTUAL=1`
6. Railway will automatically redeploy on every `git push`

> **Important:** The `credentials.json` file must be in your repository's `data/` folder. Make sure it's committed to git (but keep your repo **private** if it contains credentials).

> **Generation changes:** When you advance to the next generation using `/generacion cambiar`, remember to also update `GENERACION_ACTUAL` in Railway's Variables panel so it persists between deploys.

---

## 🌐 Deploy to Render (Alternative — Free)

1. Go to https://render.com and create an account
2. Click **New → Web Service**
3. Connect your GitHub repository
4. Configure:
   - **Environment:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
5. Add all environment variables in the **Environment** tab
6. Click **Deploy**

> **Note:** Render's free tier spins down after 15 minutes of inactivity. For a Discord bot that needs to stay online, use Railway or upgrade to a paid Render plan.

---

## 📁 Project Structure

```
arcana-bot/
├── bot.py                  # Main entry point
├── Procfile                # Railway/Render start command
├── requirements.txt        # Python dependencies
├── .python-version         # Python version pin (3.11.9)
├── .env.example            # Environment variables template
├── .gitignore
├── data/
│   ├── credentials.json    # Google service account (keep private!)
│   └── isefora.db          # SQLite database (auto-created)
├── cogs/
│   ├── admin.py            # Admin commands + stats panel
│   ├── admin_data.py       # User data management
│   ├── uniformes.py        # Uniform registration
│   ├── estudiantes.py      # Student registration
│   ├── profesores.py       # Professor registration
│   ├── trabajos.py         # Worker registration
│   ├── editar_ficha.py     # Character editing
│   ├── pca.py              # Academic Points System
│   ├── spins.py            # Power Spin + Battle system
│   ├── generar_id.py       # ID card generation
│   └── ver_id.py           # ID card viewing
└── utils/
    ├── constants.py        # ⚙️ Main configuration file
    ├── database.py         # SQLite operations
    ├── sheets.py           # Google Sheets operations
    ├── helpers.py          # Shared utilities
    └── image_handler.py    # Image processing
```

---

## ⚠️ Common Errors

| Error | Solution |
|---|---|
| `ModuleNotFoundError: audioop` | You're using Python 3.13. Switch to Python 3.11 |
| `ModuleNotFoundError` (other) | Activate virtual environment and run `pip install -r requirements.txt` |
| `discord.errors.LoginFailure` | Wrong token in `.env` or Railway variables |
| `SpreadsheetNotFound` | Wrong Sheets ID or not shared with service account email |
| `KeyError: 0` in GUILD_ID | GUILD_ID is empty in `.env` |
| Commands not appearing | Wait 1-2 minutes after deploy — Discord takes time to sync |
| Slots showing wrong gen data | Update `GENERACION_ACTUAL` in Railway variables after changing generation |

---

## 🗄️ Database

The bot uses **SQLite** for slot tracking (`data/isefora.db`). This file is created automatically on first run.

> **Scaling note:** SQLite works well for servers up to ~500 active users. Beyond that, consider migrating to **PostgreSQL** (Railway offers a free PostgreSQL addon). The migration would require updating `utils/database.py` to use `asyncpg` instead of `aiosqlite`, and updating the connection string from a file path to a database URL.

---

## 🔄 Every Session (Local)

```bash
# 1. Activate virtual environment
venv\Scripts\activate    # Windows
source venv/bin/activate # Mac/Linux

# 2. Run the bot
python bot.py
```

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

You are free to use, modify, and distribute this bot for your own server. Credit appreciated but not required.

---

*ArcanaBot — Made with ❤️ for the RP community*
