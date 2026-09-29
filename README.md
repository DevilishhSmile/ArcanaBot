# 🪄 ArcanaBot — Discord Bot for Roleplay Servers

> Character management bot for themed roleplay servers.  
> Originally developed for **Academia Arcana Isefora** — adaptable for any similar community.
> > 🇪🇸 ¿No entiendes inglés? Puedes ver la guía completa en español aquí: [Guía de Instalación ESP](README_ES.md)

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
- **Uniform system** — Users choose from configurable uniform variants defined for your server

---

## 🗂️ Table of Contents

1. [Prerequisites](#-prerequisites)
2. [Step 1 — Download the bot](#-step-1--download-the-bot)
3. [Step 2 — Create the Discord bot](#-step-2--create-the-discord-bot)
4. [Step 3 — Set up Google Sheets](#-step-3--set-up-google-sheets)
5. [Step 4 — Customize for your server](#-step-4--customize-for-your-server)
6. [Step 5 — Hosting (Railway or your PC)](#-step-5--hosting-choose-how-to-run-the-bot)
7. [Command Reference](#-command-reference)
8. [Troubleshooting](#-troubleshooting)

---

## ✅ Prerequisites

Before you start, make sure you have these accounts ready:

| What | What for | Link |
|------|----------|------|
| **GitHub** account | Store and upload the code | [github.com](https://github.com) |
| **Discord** account with a server | Where the bot will live | [discord.com](https://discord.com) |
| **Google** account | For Google Sheets | You already have one |
| **Railway** account | To keep the bot running 24/7 | [railway.app](https://railway.app) |

> 💡 **Not sure what GitHub is?** Think of it like Google Drive, but for code. It's free for this use.

---

## 📥 Step 1 — Download the bot

There are two ways to get the bot files. Choose whichever is easier for you:

### Option A — Download as ZIP (easiest, no technical knowledge needed)

1. Go to the GitHub repository: `https://github.com/DevilishhSmile/IseforaBot`
2. Click the green **`<> Code`** button
3. Click **`Download ZIP`**
4. Extract the ZIP file to a folder on your computer (e.g. `C:\ArcanaBot\`)

### Option B — Clone with GitHub Desktop (recommended if you plan to make changes)

1. Download **GitHub Desktop** from [desktop.github.com](https://desktop.github.com)
2. Install it and sign in with your GitHub account
3. Go to the GitHub repository
4. Click **`<> Code`** → **`Open with GitHub Desktop`**
5. Choose a folder on your computer and click **Clone**

> ✅ After Step 1, you should have a folder containing: `bot.py`, `requirements.txt`, `.env.example`, `cogs/`, `utils/`, etc.

---

## 🤖 Step 2 — Create the Discord bot

### 2.1 — Create the application

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications)
2. Sign in with your Discord account
3. Click the blue **`New Application`** button (top right)
4. Type a name for your bot (e.g. `ArcanaBot`) and click **`Create`**

### 2.2 — Configure the bot

1. In the left menu, click **`Bot`**
2. If you see an **`Add Bot`** button, click it and confirm with **`Yes, do it!`**
3. Scroll down to the **`Privileged Gateway Intents`** section and enable all three:
   - ✅ **Presence Intent**
   - ✅ **Server Members Intent**
   - ✅ **Message Content Intent**
4. Click **`Save Changes`** (the green button at the bottom)

### 2.3 — Copy the bot token

> ⚠️ **The token is like the bot's password. Never share it with anyone.**

1. Still in the **`Bot`** section, find the **`TOKEN`** area
2. Click **`Reset Token`** and confirm
3. Click **`Copy`** and save that text somewhere safe (Notepad, etc.)
   - It looks something like: `MTIzNDU2Nzg5MDEy.AbCdEf.xYzAbCdEfGhIjKlMnOpQrStUv`

### 2.4 — Enable Developer Mode in Discord

You'll need this to copy channel and role IDs later:

1. Open Discord on your computer
2. Go to **User Settings** (the gear icon ⚙️ next to your name)
3. In the left menu, click **`Advanced`**
4. Enable **`Developer Mode`**

> ✅ Now when you right-click any channel, role, or user, you'll see a **`Copy ID`** option.

### 2.5 — Get your server ID

1. In Discord, **right-click** your server icon (in the left sidebar)
2. Click **`Copy Server ID`**
3. Save that number — you'll need it for the `.env` file

### 2.6 — Invite the bot to your server

1. In the developer portal, go to **`OAuth2`** → **`URL Generator`**
2. Under **`Scopes`**, check:
   - ✅ `bot`
   - ✅ `applications.commands`
3. Under **`Bot Permissions`** (appears below), check:
   - ✅ `Send Messages`
   - ✅ `Embed Links`
   - ✅ `Attach Files`
   - ✅ `Read Message History`
   - ✅ `Use External Emojis`
   - ✅ `Add Reactions`
   - ✅ `Manage Roles`
4. Copy the generated URL at the bottom of the page
5. Paste that URL into your browser, select your server and click **`Authorize`**

> ✅ The bot should now appear in your server's member list (it will show as offline until you start it)

---

## 📊 Step 3 — Set up Google Sheets

The bot saves all character information in a Google Sheets spreadsheet. You need to create that spreadsheet and give the bot access to it.

### 3.1 — Create the spreadsheet

1. Go to [sheets.google.com](https://sheets.google.com) and sign in
2. Click the **`+`** button (Blank spreadsheet)
3. Give it a name at the top (e.g. `ArcanaBot Data`)
4. Now create **15 tabs** with exact names. For each tab:
   - Click the **`+`** at the bottom left
   - Double-click the tab name and rename it

Create these tabs **exactly** as shown (case-sensitive, no extra spaces):

| # | Exact Tab Name | What it stores |
|---|----------------|----------------|
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

> ⚠️ Tab names must be exactly as listed. An extra space or different capitalization will cause the bot to fail.

### 3.2 — Copy your spreadsheet ID

From the browser address bar, copy the ID from the URL:

```
https://docs.google.com/spreadsheets/d/  THIS_IS_THE_ID  /edit
```

Save that ID — you'll need it for the `.env`.

### 3.3 — Create a Google Cloud project

> 💡 Google Cloud is the system that lets the bot read and write to your spreadsheet automatically.

1. Go to [console.cloud.google.com](https://console.cloud.google.com) and sign in
2. At the top, click the project selector (it says "Select a project" or shows a project name)
3. In the window that appears, click **`New Project`**
4. Give it a name (e.g. `ArcanaBot`) and click **`Create`**
5. Wait a few seconds and make sure that project is selected at the top

### 3.4 — Enable the required APIs

1. In the left menu, click **`APIs & Services`** → **`Library`**
2. In the search box, type **`Google Sheets API`**
3. Click the result, then click the blue **`Enable`** button
4. Go back to the library, search for **`Google Drive API`** and enable it too

### 3.5 — Create the Service Account

> 💡 A "service account" is like a robot user the bot will use to access your sheet without needing your password.

1. Go to **`APIs & Services`** → **`Credentials`**
2. Click **`+ Create Credentials`** → **`Service Account`**
3. In **`Service account name`** type something like `arcanabot-sheets`
4. Click **`Create and Continue`**
5. In step 2 ("Grant access..."), in the **`Select a role`** dropdown, choose **`Editor`** (under "Basic")
6. Click **`Continue`**, then **`Done`**

### 3.6 — Download the credentials file

1. You'll see your new service account in the list. Click its name (or the pencil ✏️ icon)
2. Go to the **`Keys`** tab
3. Click **`Add Key`** → **`Create New Key`**
4. Select **`JSON`** format and click **`Create`**
5. A file will automatically download with a long name. **Rename it to `credentials.json`**
6. Move that file into the bot's folder

### 3.7 — Share the sheet with the service account

1. Open `credentials.json` with Notepad
2. Find the line that says `"client_email"` — copy the email address there
   - It looks like: `arcanabot-sheets@arcanabot-12345.iam.gserviceaccount.com`
3. Go to your Google Sheets spreadsheet
4. Click the **`Share`** button (top right)
5. Paste the service account email in the recipient field
6. Change the permission to **`Editor`**
7. **Uncheck** "Notify people" (so no email is sent to a robot)
8. Click **`Share`**

> ✅ The bot now has access to read and write your spreadsheet.

---

## 🎨 Step 4 — Customize for your server

This is where you adapt the bot to use your server's specific names, roles, and channels. There are two files to edit.

### 4.1 — Create the `.env` file

The `.env` file stores your bot's private data (tokens, IDs).

1. In the bot folder, find the file called `.env.example`
2. **Copy** that file and rename the copy to `.env` (without `.example`)
3. Open `.env` with Notepad

Fill in each field with your server's information:

```env
# ── DISCORD ──────────────────────────────────────────
# The token you copied in Step 2.3
DISCORD_TOKEN=paste_your_token_here

# Your server ID from Step 2.5
GUILD_ID=123456789012345678

# ── GOOGLE SHEETS ─────────────────────────────────────
# Your spreadsheet ID from Step 3.2
GOOGLE_SHEETS_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms

# ── CHANNELS ──────────────────────────────────────────
# For each channel: right-click the channel in Discord → Copy ID
CANAL_ENVIAR_UNIFORME=id_of_channel_where_users_request_uniform
CANAL_REGISTRAR_ESTUDIANTE=id_of_channel_where_users_register_students
CANAL_REGISTRO_TRABAJOS=id_of_channel_where_users_register_workers
CANAL_CARTA_ACEPTACION=id_of_channel_where_acceptances_are_announced
CANAL_FICHAS_ESTUDIANTES=id_of_channel_where_student_sheets_are_stored
CANAL_FICHAS_PROFESORES=id_of_channel_where_professor_sheets_are_stored
CANAL_FICHAS_TRABAJADORES=id_of_channel_where_worker_sheets_are_stored
CANAL_REVISION_UNIFORMES=id_of_staff_uniform_review_channel
CANAL_REVISION_FICHAS=id_of_staff_sheet_review_channel
CANAL_LOGS_BOT=id_of_channel_where_the_bot_logs_its_actions
CANAL_SANCIONES=id_of_channel_where_sanctions_are_published

# ── ROLES ─────────────────────────────────────────────
# For each role: in Discord, go to Server Settings → Roles
# Right-click any role → Copy ID
ROL_STAFF=id_of_staff_role
ROL_ESTUDIANTE=id_of_role_given_when_student_sheet_is_approved
ROL_PROFESOR=id_of_role_given_when_professor_sheet_is_approved
ROL_TRABAJADOR=id_of_role_given_when_worker_sheet_is_approved
ROL_REGISTRADO=id_of_role_given_when_any_character_is_approved
ROL_SLOT_ADICIONAL=id_of_role_consumed_when_using_an_extra_slot
ROL_CONSEJO=id_of_student_council_role_that_can_assign_points

# ── GENERATION ────────────────────────────────────────
# Current generation number (start at 1)
GENERACION_ACTUAL=1
```

> 💡 **How to copy a channel ID:** In Discord, **right-click** the channel → **`Copy ID`** (if this doesn't appear, go back to Step 2.4 to enable Developer Mode).

> 💡 **How to copy a role ID:** Go to **Server Settings** → **Roles** → **right-click** a role → **`Copy ID`**.

> ⚠️ If a role doesn't exist in your server or you don't want to use it, put `0` instead. For example: `ROL_CONSEJO=0`

### 4.2 — Edit `utils/constants.py`

This file is where you customize the lists of houses, subjects, jobs, clubs, and other server-specific things. Open it with Notepad or any text editor.

> 💡 Only change values between quotes `""` or inside brackets `[]`. Don't delete commas or colons `:`.

---

#### 🏠 CASAS (server factions/houses)

```python
CASAS = ["Redmeadow", "Ledacrealis", "Ravyelle", "Azorya"]
```

Replace the names with your server's houses. If your server has no houses, leave it as an empty list:

```python
CASAS = []
```

> ⚠️ If left empty (`[]`), the bot will **automatically skip** the house selector when registering characters.

---

#### 👔 CARGOS (available worker positions)

```python
CARGOS = {
    "Librarian":  2,
    "Secretary":  2,
    "Nurse":      3,
    "Inspector":  None,
    "Dean":       1,
}
```

Each position has:
- The **name** of the position (in quotes)
- The **max number** of people who can hold that position (`None` = no limit)

To add a new position:
```python
"Position Name": 2,    # max 2 people
"Another Position": None, # unlimited
```

---

#### 📚 MATERIAS (available subjects for professors)

```python
MATERIAS = [
    "Criminology", "Chemistry", "Astronomy", "Biology",
    "History of Magic", "Alchemy",
]
```

Change or add the subjects your server has. Each subject allows **1 professor** by default. To allow more, also edit:

```python
MATERIAS_LIMITE = {m: 1 for m in MATERIAS}   # 1 professor per subject
MATERIAS_LIMITE["Substitute Professor"] = 3   # except substitutes: 3
```

---

#### 🎭 CLUBES (available clubs for students)

```python
CLUBES = {
    "Dance":   123456789012345678,
    "Sports":  123456789012345678,
    "Music":   123456789012345678,
}
```

Each club has:
- The **name** of the club (in quotes)
- The **Discord role ID** assigned to members of that club

To get a role ID: right-click the role in Discord → **Copy ID**.

If your server has no clubs, leave it as an empty dictionary:

```python
CLUBES = {}
```

> ⚠️ If left empty (`{}`), the bot will **automatically skip** the club selector when registering students.

---

#### 🎰 SLOTS (character limits per generation)

```python
SLOTS_CONFIG = {
    1: {"estudiantes": 3, "trabajadores": 2, "profesores": 2},
    "default": {"estudiantes": 3, "trabajadores": 2, "profesores": 2}
}
```

This defines how many characters of each type each user can create per generation.

- The number `1` is the configuration for Generation 1
- `"default"` applies to any generation without a specific config
- You can add future generation configs:
  ```python
  SLOTS_CONFIG = {
      1: {"estudiantes": 3, "trabajadores": 2, "profesores": 2},
      2: {"estudiantes": 2, "trabajadores": 1, "profesores": 1},
      "default": {"estudiantes": 2, "trabajadores": 1, "profesores": 1}
  }
  ```
### 🪪 Identity Card Images

The bot includes identity card images **pre-designed for the Isefora Academia Arcana server**. To adapt them to your server you need to replace them with your own designs:

> ⚠️ **Important:** Image files must keep **exactly the same names** as the originals and be placed in the **project root** (the main folder, next to `bot.py`) so the bot can find them correctly.

| File | For | Dimensions |
|---|---|---|
| `IDEstudiante.png` | Students | 600 × 400 px |
| `IDWorker.png` | Teachers & Staff | 400 × 600 px |

1. Go to the folder where the card images are stored (inside the project)
2. Design your own versions for your server following the same template / disposition of the card imagaes.
3. Save them with the **exact same file names** (`IDEstudiante.png` and `IDWorker.png`) as the originals (matching uppercase, lowercase, and extension)
4. Copy them to the project root folder, replacing the original files

If you upload an image with a different name or place it in a different folder, the bot won't be able to find it and the cards won't generate correctly.

> 💡 **Tip:** Leave blank space in the areas where the bot writes text (name, house, generation, code) and where it places the character photo. If you're unsure where those areas are, use the original templates as a visual reference first.

---

#### ✨ POWER SPIN SYSTEM (race categories)

The race categories and their probabilities are in `CATEGORIAS_RAZA`. Current weights:

| Category | Probability |
|----------|-------------|
| ⚪ Basic | 40% |
| 🔵 Sensitive | 25% |
| 🟢 Epic | 15% |
| 🟡 Mythic | 10% |
| 🟠 Legendary | 6% |
| 🔴 Cursed | 3% |
| ✨ Divine | 1% |

To adjust probabilities, change the `"peso"` (weight) value of each category. Weights don't need to add up to 100 — the bot calculates percentages automatically.

---

## 🚀 Step 5 — Hosting: choose how to run the bot

You have two options for running the bot. Choose whichever works best for you:

| | Option A: Railway (cloud) | Option B: Your computer |
|---|---|---|
| **Cost** | Free (with limits) or ~$5/mo | Free |
| **Bot runs** | 24/7 always | Only when your PC is on |
| **Difficulty** | Medium | Easy |
| **Best for** | Active servers | Testing or small servers |

> ⚠️ **Another thing to have in mind:** If you choose to run the bot from your PC, you'll have to start the bot again from the terminal everytime you turn your PC off.

> 💡 **About Railway's cost:** Railway charges for actual usage. A small bot typically uses less than $1-2 of the monthly $5 credit. In practice you'll almost never hit the limit.

> 🔍 **Want to explore other hosting options?** Services like **Fly.io**, **Oracle Cloud Free Tier**, **Render** or **DigitalOcean** can also work for hosting Discord bots. Each has its own setup process — if any of them interest you, feel free to ask your favorite AI how to set them up for a Python bot. 😊

---

### Option A — Railway (recommended for active servers)

Railway keeps the bot running 24/7 without leaving your computer on.

### 5.1 — Upload the code to GitHub

If you downloaded the ZIP and have never used GitHub:

1. Go to [github.com](https://github.com) and sign in
2. Click **`+`** → **`New repository`**
3. Give it a name (e.g. `my-arcanabot`)
4. Select **`Private`** (so nobody can see your code)
5. Click **`Create repository`**
6. Download **GitHub Desktop** from [desktop.github.com](https://desktop.github.com)
7. In GitHub Desktop: **`File`** → **`Add Local Repository`** → select the bot folder
8. Click **`Publish repository`** and select your new repository

> ⚠️ Before uploading, make sure `.env` and `credentials.json` are in `.gitignore` (they already should be). These files contain private information and should **never** be pushed to GitHub.

### 5.2 — Create the Railway project

1. Go to [railway.app](https://railway.app) and sign in (you can use your GitHub account)
2. Click **`New Project`**
3. Select **`Deploy from GitHub repo`**
4. Connect your GitHub account if prompted
5. Find and select the repository you created in the previous step
6. Railway will start trying to start the bot (it will fail for now — you still need to configure the variables)

### 5.3 — Add environment variables in Railway

1. Click on your service in Railway (the box that appears in the project)
2. Go to the **`Variables`** tab
3. Add **every** variable from your `.env` file:
   - Click **`New Variable`**
   - Type the name (e.g. `DISCORD_TOKEN`)
   - Type the value (the token you copied)
   - Repeat for every variable

> 💡 You can also click **`RAW Editor`** and paste your entire `.env` file contents at once.

### 5.4 — Add Google credentials

The `credentials.json` file can't be uploaded to GitHub for security. In Railway you add it as a variable:

1. Open your `credentials.json` with Notepad
2. Select **all content** (Ctrl+A) and copy it (Ctrl+C)
3. In Railway → Variables, create a new variable:
   - Name: `GOOGLE_CREDENTIALS_JSON`
   - Value: paste all the file's content
4. Click **`Add`**

### 5.5 — Create the volume for the database

Railway wipes temporary files when the bot restarts. To save the database permanently, you need a **volume**:

1. In your Railway project view, click **`+ New`**
2. Select **`Volume`**
3. In **`Mount Path`** type: `/app/data`
4. Click to connect it to your bot service
5. Railway will automatically redeploy the bot

### 5.6 — Verify the bot is running

1. In Railway, click your service and go to the **`Logs`** (or **`Deploy Logs`**) tab
2. You should see something like:
   ```
   ✅ Cog cargado: cogs.admin
   ✅ Cog cargado: cogs.estudiantes
   ...
   ✅ Bot conectado como YourBot#1234 (ID: 123456789)
   ✅ 25 comando(s) sincronizados: [uniforme, estudiante, ...]
   ```
3. If you see errors, check the [Troubleshooting](#-troubleshooting) section

---

### Option B — Run from your own computer (no hosting needed)

This option is ideal if you want to test the bot, have a small server, or prefer not to pay for hosting. The bot will only work while your computer is on and the script is running.

#### B.1 — Install Python

1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download **Python 3.11** (look for the version that says `3.11.x`)
3. Run the installer
4. **Important:** on the first installer screen, check the box that says **"Add Python to PATH"** before clicking Install
5. Verify it installed: open a terminal (Windows: search `cmd` in the Start menu) and type:
   ```
   python --version
   ```
   It should show `Python 3.11.x`

#### B.2 — Open the terminal inside the bot folder

1. Navigate to the folder where you downloaded the bot
2. **Windows:** hold `Shift` and right-click inside the folder → select **"Open PowerShell window here"** (or "Open in Terminal")
3. **Mac:** right-click the folder → **"New Terminal at Folder"**

#### B.3 — Create the virtual environment and install dependencies

In the terminal you opened, type these commands one by one (press Enter after each):

```bash
# Create the virtual environment
python -m venv venv
```

```bash
# Activate it (Windows)
venv\Scripts\activate
```
```bash
# Activate it (Mac/Linux)
source venv/bin/activate
```

You'll know it's active because `(venv)` appears at the start of the terminal line.

```bash
# Install all dependencies
pip install -r requirements.txt
```

This may take a few minutes. You'll see several packages being downloaded and installed.

#### B.4 — Create the `.env` file

You should have done this in **Step 4.1**. If you haven't yet, go there now.

#### B.5 — Run the bot

With the virtual environment active (`(venv)` showing in the terminal):

```bash
python bot.py
```

If everything is working, you'll see something like:

```
✅ Cog cargado: cogs.admin
✅ Cog cargado: cogs.estudiantes
...
✅ Bot conectado como YourBot#1234 (ID: 123456789)
✅ Base de datos SQLite lista
✅ 25 comando(s) sincronizados
```

> ✅ The bot is running! You can minimize the terminal but **don't close it** — closing it disconnects the bot.

#### B.6 — Starting the bot next time

Every time you want to start the bot from your computer:

```bash
# 1. Activate the virtual environment
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 2. Run the bot
python bot.py
```

> 💡 **Tip:** On Windows, you can create a `start.bat` file with those two lines to start the bot with a double-click.

---

## 🧾 Command Reference

### General
| Command | Description |
|---------|-------------|
| `/about-bot` | Show bot info, features, version and credits |

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

## 🐛 Troubleshooting

### ❌ `TypeError: expected token to be a str, received NoneType`
**Cause:** The `DISCORD_TOKEN` variable isn't configured in Railway.  
**Fix:** Go to Railway → your service → **Variables** and make sure `DISCORD_TOKEN` has the correct token.

### ❌ `sqlite3.OperationalError: unable to open database file`
**Cause:** Railway can't create the database because no volume is mounted.  
**Fix:** Follow Step 5.5 to create the volume at `/app/data`.

### ❌ Commands don't appear when typing `/`
**Cause 1:** The bot doesn't have the `applications.commands` permission.  
**Fix 1:** Follow Step 2.6 to re-invite the bot with the correct permissions (it won't kick it, just updates permissions).

**Cause 2:** Commands failed to sync.  
**Fix 2:** Check the Logs in Railway for `❌ Error sincronizando`. If there's an error, fix the underlying issue and trigger a new Deploy.

### ❌ `gspread.exceptions.SpreadsheetNotFound`
**Cause:** The bot can't find your Google Sheets spreadsheet.  
**Fix:**
- Verify `GOOGLE_SHEETS_ID` in Railway Variables has the correct ID (just the ID, not the full URL)
- Verify you shared the sheet with the service account email (Step 3.7)

### ❌ `ModuleNotFoundError: No module named 'audioop'`
**Cause:** You're using Python 3.12 or higher, which isn't compatible.  
**Fix:** In Railway, create a file called `.python-version` in the project root with content `3.11.9`. Then trigger a new Deploy.

### ❌ Bot is online but commands don't respond
**Cause:** Privileged Intents aren't enabled.  
**Fix:** Go to [discord.com/developers/applications](https://discord.com/developers/applications) → your app → **Bot** → enable all three Privileged Gateway Intents (Step 2.2).

### ❌ "Missing permissions" when assigning roles
**Cause:** The bot's role in the server isn't above the roles it's trying to assign.  
**Fix:** In Discord, go to **Server Settings** → **Roles**, and drag the bot's role so it's **above** all the roles the bot assigns (ROL_ESTUDIANTE, ROL_PROFESOR, etc.)

## 🐛 Other common errors

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

> ⚠️ **Never share or upload these files to GitHub:**
> - `.env` — contains the Discord token
> - `credentials.json` — contains Google Sheets access

If someone gets your Discord token, they can fully control your bot. If this happens:
1. Go to [discord.com/developers/applications](https://discord.com/developers/applications) → **Bot** → **Reset Token** immediately
2. Update the new token in Railway

---

## 📄 License

[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) — Free to use, modify and share. **Commercial use and resale are not permitted.** Credit to the original author is required.

See the [LICENSE](LICENSE) file for full details.

---

Built with ❤️ by **Devilishh** · Need technical support? Contact `devilishh.` on Discord
