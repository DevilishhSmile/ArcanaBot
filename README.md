# 🪄 ArcanaBot — Discord Bot for Roleplay Servers

> Character management bot for themed roleplay servers. Originally developed for **Academia Arcana Isefora** — adaptable for any similar community.

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![discord.py 2.4.0](https://img.shields.io/badge/discord.py-2.4.0-5865F2.svg)](https://discordpy.readthedocs.io/)
[![License CC BY-NC 4.0](https://img.shields.io/badge/license-CC%20BY--NC%204.0-green.svg)](https://creativecommons.org/licenses/by-nc/4.0/)

---

## 📋 What does this bot do?

ArcanaBot automates character management and moderation workflows for themed Discord roleplay servers. It includes:

- **Character sheet system** — Students, professors and workers with detailed profiles
- **Staff review workflow** — Approve/reject with feedback in designated channels
- **Academic Conduct Points (PCA)** — Sanctions, redemptions and appeals
- **Power Spin system** — 7 secret weighted race categories with randomized draws
- **Battle system** — Duels with results logged to Google Sheets
- **ID card generation** — Visual ID cards built with PIL/Pillow
- **Admin panel** — Stats, generation management and data cleanup
- **Slot tracking** — Configurable per-generation character limits
- **Uniform system** — Diplomatic / Militarized versions with house selector

---

## ⚙️ Requirements

- **Python 3.11 exactly** (Python 3.12+ removes `audioop`, which discord.py requires)
- **Discord account and server**
- **Google account** with Google Sheets access
- **Railway or Render account** (for hosting, optional)

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/arcanabot.git
cd arcanabot
```

### 2. Verify Python version

```bash
python --version
# Should output: Python 3.11.x
```

If you have a different version, download Python 3.11 from [python.org/downloads](https://www.python.org/downloads/release/python-3110/).

For Railway, create a `.python-version` file in the project root:

```
3.11.9
```

### 3. Create and activate virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

### 4. Install dependencies

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

## 🤖 Setting up the Discord Bot

### 1. Create the bot application

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications)
2. Click **New Application** → give it a name → Create
3. Go to the **Bot** section → click **Add Bot**
4. Enable the following **Privileged Gateway Intents**:
   - ✅ Presence Intent
   - ✅ Server Members Intent
   - ✅ Message Content Intent

### 2. Copy the token

In the **Bot** section, click **Reset Token** and copy it. You'll need it for the `.env` file.

### 3. Invite the bot to your server

Go to **OAuth2 → URL Generator** and select:

- **Scopes:** `bot`, `applications.commands`
- **Bot Permissions:**
  - `Send Messages`
  - `Embed Links`
  - `Attach Files`
  - `Read Message History`
  - `Use External Emojis`
  - `Add Reactions`
  - `Manage Roles` (for automatic role assignment)

Copy the generated URL and use it to invite the bot.

---

## 📊 Setting up Google Sheets

### 1. Create the spreadsheet

Create a new spreadsheet at [sheets.google.com](https://sheets.google.com). Create exactly **15 tabs** with these exact names (case-sensitive):

| # | Tab Name | Description |
|---|----------|-------------|
| 1 | `UniformesPendientes` | Pending uniform requests |
| 2 | `UniformesAprobados` | Approved uniforms |
| 3 | `EstudiantesPendientes` | Pending student sheets |
| 4 | `EstudiantesAprobados` | Approved students |
| 5 | `Profesores` | Approved professors |
| 6 | `Trabajadores` | Approved workers |
| 7 | `TrabajosPendientes` | Pending work sheets |
| 8 | `GlobalStats` | Server-wide statistics |
| 9 | `PuntosPC` | Current conduct points per user |
| 10 | `HistorialPC` | Full points history |
| 11 | `Sanciones` | Active sanctions log |
| 12 | `FichasPoder` | Approved power sheets |
| 13 | `HistorialSpins` | Power spin history |
| 14 | `HistorialBatallas` | Battle history |
| 15 | `CodigosID` | Generated ID codes |

### 2. Create a Google Service Account

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (or use an existing one)
3. Go to **APIs & Services → Library**
4. Enable **Google Sheets API** and **Google Drive API**
5. Go to **Credentials → Create Credentials → Service Account**
6. Give it a name, continue, and download the JSON credentials file
7. Save this file as `credentials.json` in the project root

### 3. Share the sheet with the service account

Open `credentials.json` and find the `client_email` field (something like `bot@project.iam.gserviceaccount.com`).

Share your Google Sheet with that email address, giving it **Editor** permissions.

---

## 🔑 Environment variables

Create a `.env` file in the project root:

```env
# Discord bot token
DISCORD_TOKEN=your_token_here

# Discord server ID (right-click server → Copy Server ID)
GUILD_ID=123456789012345678

# Channel IDs (right-click channel → Copy ID)
CANAL_REVISION_FICHAS=123456789012345678
CANAL_REVISION_PODER=123456789012345678
CANAL_REGISTRO_TRABAJOS=123456789012345678
CANAL_REGISTRO_ESTUDIANTES=123456789012345678
CANAL_REGISTRO_PODERES=123456789012345678

# Role IDs
ROL_REGISTRADO=123456789012345678
ROL_CONSEJO=123456789012345678
ROL_SLOT_ADICIONAL=123456789012345678
ROL_RESPIN=123456789012345678

# Google Sheets URL (from your browser)
SPREADSHEET_URL=https://docs.google.com/spreadsheets/d/YOUR_ID_HERE/edit

# Current server generation (for slot tracking)
GENERACION_ACTUAL=1
```

**How to get Discord IDs:**
- Enable **Developer Mode** in Discord Settings → Advanced → Developer Mode
- Right-click any server, channel, or role to see "Copy ID"

---

## 🎨 Customizing the bot

### Edit `utils/constants.py`

This is the main configuration file. Change these values for your server:

```python
# Your server ID
GUILD_ID = int(os.getenv("GUILD_ID", "YOUR_GUILD_ID"))

# Houses / factions in your server
CASAS = ["House1", "House2", "House3", "House4"]

# Available subjects for professors
MATERIAS = ["Subject 1", "Subject 2", "Subject 3"]

# Max slots per subject (how many professors per subject per generation)
MATERIAS_LIMITE = {
    "Subject 1": 2,
    "Subject 2": 2,
    "Subject 3": 1,
}

# Available positions for workers
CARGOS = ["Position 1", "Position 2", "Position 3"]

# Max slots per position
CARGOS_LIMITE = {
    "Position 1": 3,
    "Position 2": 2,
}

# Available clubs for students
CLUBES = ["Club 1", "Club 2", "Club 3"]

# Base character slots per user per generation
SLOTS_BASE = {
    "estudiantes": 2,
    "trabajadores": 1,
    "profesores": 1,
}
```

---

## 🌐 Deployment

### Option A: Railway (recommended)

1. Push the code to a GitHub repository
2. Go to [railway.app](https://railway.app) → **New Project → Deploy from GitHub repo**
3. Select your repository
4. Go to the **Variables** tab and add all variables from your `.env`
5. For Google credentials, you can paste the JSON content as a variable:
   ```
   GOOGLE_CREDENTIALS_JSON={"type":"service_account",...}
   ```
   Then adapt `utils/sheets.py` to read from this variable.
6. Railway will auto-detect the `Procfile`:
   ```
   worker: python bot.py
   ```
7. Create `.python-version` with content `3.11.9` to pin the Python version.

**⚠️ Important with Railway:**
- The SQLite file **does persist** between deploys (stored at `/app/data/`)
- When changing generation, update the `GENERACION_ACTUAL` variable in Railway
- The `credentials.json` file **does NOT persist** between deploys — use the JSON env variable

### Option B: Render

1. Push the code to GitHub
2. Go to [render.com](https://render.com) → **New → Background Worker**
3. Connect your repository
4. Configure:
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
5. Add environment variables in the **Environment** section

---

## 📂 Project structure

```
arcanabot/
├── bot.py                  # Main entry point, cog loading
├── .env                    # Environment variables (do NOT commit)
├── .env.example            # Variable template
├── credentials.json        # Google credentials (do NOT commit)
├── .python-version         # Pins Python 3.11.9 for Railway
├── requirements.txt        # Dependencies
├── Procfile                # Railway start command
├── .gitignore              # Protects sensitive files
│
├── cogs/                   # Bot modules (commands)
│   ├── admin.py            # Admin commands
│   ├── admin_data.py       # Character data management
│   ├── uniformes.py        # Uniform system
│   ├── estudiantes.py      # Student registration
│   ├── profesores.py       # Professor registration
│   ├── trabajos.py         # Worker registration
│   ├── editar_ficha.py     # Edit existing sheets
│   ├── pca.py              # Conduct points system
│   ├── spins.py            # Power & battle system
│   ├── generar_id.py       # ID card generation
│   └── ver_id.py           # View ID cards
│
├── utils/                  # Utility modules
│   ├── constants.py        # Main configuration
│   ├── database.py         # SQLite operations
│   ├── sheets.py           # Google Sheets integration
│   └── helpers.py          # Helper functions and embeds
│
├── assets/                 # Visual resources
│   ├── IDEstudiante.png    # Student ID card template
│   └── IDWorker.png        # Worker ID card template
│
└── data/                   # Runtime-generated data
    ├── isefora.db          # SQLite database
    └── generacion.json     # Current generation (local backup)
```

---

## 🧾 Command reference

### Character registration
| Command | Description |
|---------|-------------|
| `/uniforme` | Request uniform approval |
| `/estudiante` | Register student sheet |
| `/profesor` | Register professor sheet |
| `/trabajo` | Register worker sheet |
| `/editar-ficha` | Edit an existing sheet |

### Power system
| Command | Description |
|---------|-------------|
| `/poder` | Spin for a power (requires sheet photo) |
| `/respin` | Re-spin (requires special role) |
| `/iniciar-batalla` | Start a duel with another user |

### ID cards
| Command | Description |
|---------|-------------|
| `/generar-id` | Generate visual ID card |
| `/ver-id` | View a previously generated ID |

### Conduct points (PCA)
| Command | Description |
|---------|-------------|
| `/asignar-pc` | Assign positive or negative points |
| `/sancionar` | Create a formal sanction |
| `/redimir-sancion` | Approve a sanction redemption |
| `/apelar` | Appeal a sanction |
| `/ver-sanciones` | View a user's active sanctions |
| `/historial-pc` | View a user's points history |

### Administration (staff only)
| Command | Description |
|---------|-------------|
| `/admin` | Control panel (stats, slots, generation) |
| `/admin-data ver` | View all characters of a user |
| `/admin-data eliminar-personaje` | Delete a specific character |
| `/admin-data eliminar-tipo` | Delete all characters of a type |
| `/admin-data reset-slots` | Reset a user's slots |
| `/admin-data reset-total` | Fully reset a user's data |

---

## 🐛 Common errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: audioop` | Python 3.12+ incompatible | Use exactly Python 3.11; add `.python-version` with `3.11.9` |
| `Forbidden: 403` on sync | Bot missing `applications.commands` scope | Re-invite the bot with the correct scope |
| `gspread.exceptions.SpreadsheetNotFound` | Wrong URL or missing permissions | Check URL in `.env` and confirm sheet is shared with the service account |
| `discord.errors.InteractionTimedOut` | Interaction not responded to within 3s | Add `await interaction.response.defer()` at the start of slow callbacks |
| `Extension has no 'setup' function` | Missing `async def setup(bot)` in cog | Add it at the end of every cog file |
| Slots showing wrong generation data | Outdated `GENERACION_ACTUAL` variable | Update the environment variable in Railway/Render |

---

## 🔒 Security

- **Never commit** `.env` or `credentials.json` to Git
- Add both to `.gitignore`
- If your Discord token leaks, **regenerate it immediately** in the developer portal
- Leaked tokens can be used to spam, delete server content, or mass-ban users

---

## 📄 License

[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) — Free to use, modify and share. **Commercial use and resale are not permitted.** Credit to the original author is required.

See the [LICENSE](LICENSE) file for full details.

---

Built with ❤️ by **Devilishh** · Need technical support? Contact `devilishh.` on Discord
