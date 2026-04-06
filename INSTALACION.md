# 🛠️ Guía de instalación — IseforaBot

Sigue estos pasos en orden. Si algo falla, revisa el paso anterior.

\---

## PASO 1 — Instalar Python

1. Ve a https://www.python.org/downloads/
2. Descarga **Python 3.11 o superior**
3. Durante la instalación, **marca la casilla "Add Python to PATH"** (muy importante)
4. Verifica en la terminal:

```
   python --version
   ```

Debe mostrar `Python 3.11.x` o mayor.

\---

## PASO 2 — Descargar el proyecto

Copia la carpeta `IseforaBot` donde quieras en tu PC (por ejemplo, en el Escritorio).

\---

## PASO 3 — Crear entorno virtual e instalar dependencias

Abre la terminal dentro de la carpeta `IseforaBot` y ejecuta:

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual (Windows)
venv\\\\Scripts\\\\activate

# Activar entorno virtual (Mac/Linux)
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

Verás que el nombre del entorno virtual aparece entre paréntesis: `(venv)`

\---

## PASO 4 — Crear el bot en Discord

1. Ve a https://discord.com/developers/applications
2. Clic en **"New Application"** → dale un nombre → **Create**
3. Ve a la sección **"Bot"** en el menú lateral
4. Clic en **"Add Bot"** → confirma
5. Activa estos **Privileged Gateway Intents**:

   * ✅ Server Members Intent
   * ✅ Message Content Intent
6. Clic en **"Reset Token"** → copia el token (guárdalo, solo se ve una vez)

   \---

   ## PASO 5 — Invitar el bot al servidor

7. Ve a **OAuth2 → URL Generator**
8. En Scopes marca: `bot` y `applications.commands`
9. En Bot Permissions marca:

   * Manage Roles
   * Send Messages
   * Embed Links
   * Read Message History
   * Use Slash Commands
10. Copia la URL generada y ábrela en el navegador
11. Selecciona tu servidor y autoriza

    \---

    ## PASO 6 — Configurar Google Sheets

12. Ve a https://console.cloud.google.com/
13. Crea un proyecto nuevo
14. Activa la API de **Google Sheets** y **Google Drive**
15. Ve a **Credenciales → Crear credenciales → Cuenta de servicio**
16. Descarga el archivo JSON de credenciales
17. Renómbralo como `credentials.json` y colócalo en la carpeta `data/`
18. Copia el email de la cuenta de servicio (algo como `bot@proyecto.iam.gserviceaccount.com`)
19. En tu Google Sheets, comparte la hoja con ese email con permisos de **Editor**

    ### Hojas que debes crear en el Google Sheets:

* UniformesPendientes
* UniformesAprobados
* EstudiantesPendientes
* EstudiantesAprobados
* Profesores
* Trabajadores

  \---

  ## PASO 7 — Configurar el .env

1. Copia el archivo `.env.example` y renómbralo como `.env`
2. Rellena todos los valores:

   ```
DISCORD\\\_TOKEN=pega\\\_tu\\\_token\\\_aqui

   DISCORD\_TOKEN=pega\_tu\_token\_aqui
GUILD\_ID=id\_de\_tu\_servidor
GOOGLE\_SHEETS\_ID=id\_del\_spreadsheet
... (y todos los IDs de canales y roles)

   ```

   \*\*¿Cómo obtener IDs?\*\*

\* Activa el modo desarrollador en Discord: Ajustes → Avanzado → Modo desarrollador ✅
\* Clic derecho en cualquier canal/rol/servidor → \*\*Copiar ID\*\*

  \\---

  ## PASO 8 — Ejecutar el bot

  Con el entorno virtual activado:

  ```bash
python bot.py
```

   Si todo está bien, verás en la terminal:

   ```
✅ Bot conectado como IseforaBot#xxxx (ID: xxxxxxxxxx)
✅ Base de datos SQLite lista
✅ 0 comando(s) sincronizado(s) con el servidor
✅ Cog cargado: cogs.uniformes
✅ Cog cargado: cogs.estudiantes
✅ Cog cargado: cogs.profesores
✅ Cog cargado: cogs.trabajos
```

   \---

   ## ⚠️ Errores comunes

|Error|Solución|
|-|-|
|`ModuleNotFoundError`|Asegúrate de tener el entorno virtual activado y haber corrido `pip install -r requirements.txt`|
|`discord.errors.LoginFailure`|Token incorrecto en el `.env`|
|`gspread.exceptions.SpreadsheetNotFound`|El ID del spreadsheet está mal o no compartiste la hoja con la cuenta de servicio|
|`KeyError: 0` en GUILD\_ID|El GUILD\_ID en el `.env` está vacío|

\---

## 🔄 Para las próximas sesiones

Cada vez que quieras arrancar el bot:

```bash
# 1. Activa el entorno virtual
venv\\\\Scripts\\\\activate    # Windows
source venv/bin/activate # Mac/Linux

# 2. Ejecuta el bot
python bot.py
```

