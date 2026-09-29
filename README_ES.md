# 🪄 ArcanaBot — Bot de Discord para Servidores de Roleplay

> Bot de gestión de personajes para servidores de roleplay temáticos.  
> Desarrollado originalmente para **Academia Arcana Isefora** — adaptable para cualquier comunidad similar.

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![discord.py 2.4.0](https://img.shields.io/badge/discord.py-2.4.0-5865F2.svg)](https://discordpy.readthedocs.io/)
[![Licencia CC BY-NC 4.0](https://img.shields.io/badge/licencia-CC%20BY--NC%204.0-green.svg)](https://creativecommons.org/licenses/by-nc/4.0/)

---

## 📋 ¿Qué hace este bot?

ArcanaBot automatiza la gestión de personajes y moderación en servidores de Discord de roleplay. Incluye:

- **Sistema de fichas** — Estudiantes, profesores y trabajadores con fichas detalladas
- **Revisión por el staff** — El staff aprueba o rechaza fichas con retroalimentación
- **Puntos de Conducta Académica (PCA)** — Sanciones, redenciones y apelaciones
- **Sistema de poderes con Spin** — 7 categorías de razas con tiradas ponderadas
- **Sistema de batallas** — Duelos con registro en Google Sheets
- **Carnets de identidad** — Carnets visuales generados automáticamente
- **Panel de administración** — Estadísticas, generaciones y gestión de datos
- **Sistema de slots** — Límites configurables de personajes por generación
- **Sistema de uniformes** — Los usuarios eligen entre variantes de uniforme configurables para su servidor

---

## 🗂️ Tabla de contenidos

1. [Requisitos previos](#-requisitos-previos)
2. [Paso 1 — Descargar el bot](#-paso-1--descargar-el-bot)
3. [Paso 2 — Crear el bot de Discord](#-paso-2--crear-el-bot-de-discord)
4. [Paso 3 — Configurar Google Sheets](#-paso-3--configurar-google-sheets)
5. [Paso 4 — Personalizar el bot para tu servidor](#-paso-4--personalizar-el-bot-para-tu-servidor)
6. [Paso 5 — Hosting (Railway o tu PC)](#-paso-5--hosting-elige-cómo-correr-el-bot)
7. [Referencia de comandos](#-referencia-de-comandos)
8. [Solución de problemas](#-solución-de-problemas)

---

## ✅ Requisitos previos

Antes de empezar, necesitas tener estas cuentas creadas:

| Qué | Para qué | Enlace |
|-----|----------|--------|
| Cuenta de **GitHub** | Guardar y subir el código | [github.com](https://github.com) |
| Cuenta de **Discord** con un servidor | Donde vivirá el bot | [discord.com](https://discord.com) |
| Cuenta de **Google** | Para Google Sheets | Ya la tienes |
| Cuenta de **Railway** | Para que el bot funcione 24/7 | [railway.app](https://railway.app) |

> 💡 **¿No sabes qué es GitHub?** Es como Google Drive pero para código. Gratuito para este uso.

---

## 📥 Paso 1 — Descargar el bot

Hay dos formas de obtener los archivos del bot. Elige la que te resulte más fácil:

### Opción A — Descargar como ZIP (más fácil, sin conocimientos técnicos)

1. Ve al repositorio en GitHub: `https://github.com/DevilishhSmile/IseforaBot`
2. Haz clic en el botón verde que dice **`<> Code`**
3. Haz clic en **`Download ZIP`**
4. Descomprime el archivo en una carpeta de tu computadora (por ejemplo `C:\ArcanaBot\`)

### Opción B — Clonar con GitHub Desktop (recomendado si planeas hacer cambios)

1. Descarga **GitHub Desktop** desde [desktop.github.com](https://desktop.github.com)
2. Instálalo e inicia sesión con tu cuenta de GitHub
3. Ve al repositorio en GitHub
4. Haz clic en **`<> Code`** → **`Open with GitHub Desktop`**
5. Elige una carpeta en tu computadora y haz clic en **Clone**

> ✅ Después del paso 1, deberías tener una carpeta con estos archivos:
> `bot.py`, `requirements.txt`, `.env.example`, `cogs/`, `utils/`, etc.

---

## 🤖 Paso 2 — Crear el bot de Discord

### 2.1 — Crear la aplicación

1. Ve a [discord.com/developers/applications](https://discord.com/developers/applications)
2. Inicia sesión con tu cuenta de Discord
3. Haz clic en el botón azul **`New Application`** (arriba a la derecha)
4. Escribe un nombre para tu bot (por ejemplo: `ArcanaBot`) y haz clic en **`Create`**

### 2.2 — Configurar el bot

1. En el menú izquierdo, haz clic en **`Bot`**
2. Si ves el botón **`Add Bot`**, haz clic en él y confirma con **`Yes, do it!`**
3. Baja hasta la sección **`Privileged Gateway Intents`** y activa las tres opciones:
   - ✅ **Presence Intent**
   - ✅ **Server Members Intent**  
   - ✅ **Message Content Intent**
4. Haz clic en **`Save Changes`** (el botón verde al fondo)

### 2.3 — Copiar el token del bot

> ⚠️ **El token es como la contraseña del bot. Nunca lo compartas con nadie.**

1. Todavía en la sección **`Bot`**, busca el área que dice **`TOKEN`**
2. Haz clic en **`Reset Token`** y confirma
3. Haz clic en **`Copy`** y guarda ese texto en un lugar seguro (bloc de notas, etc.)
   - Se ve algo así: `MTIzNDU2Nzg5MDEy.AbCdEf.xYzAbCdEfGhIjKlMnOpQrStUv`

### 2.4 — Activar el Modo Desarrollador en Discord

Para poder copiar IDs de canales y roles más adelante:

1. Abre Discord en tu computadora
2. Ve a **Configuración** (el engranaje ⚙️ junto a tu nombre)
3. En el menú izquierdo, haz clic en **`Avanzado`**
4. Activa **`Modo desarrollador`**

> ✅ Ahora cuando hagas clic derecho en cualquier canal, rol o usuario, verás la opción **`Copiar ID`**

### 2.5 — Obtener el ID de tu servidor

1. En Discord, haz **clic derecho** en el ícono de tu servidor (en la barra lateral izquierda)
2. Haz clic en **`Copiar ID del servidor`**
3. Guarda ese número — lo necesitarás en el `.env`

### 2.6 — Invitar el bot a tu servidor

1. En el portal de desarrolladores, ve al menú izquierdo → **`OAuth2`** → **`URL Generator`**
2. En la sección **`Scopes`**, marca:
   - ✅ `bot`
   - ✅ `applications.commands`
3. En la sección **`Bot Permissions`** que aparece debajo, marca:
   - ✅ `Send Messages`
   - ✅ `Embed Links`
   - ✅ `Attach Files`
   - ✅ `Read Message History`
   - ✅ `Use External Emojis`
   - ✅ `Add Reactions`
   - ✅ `Manage Roles`
4. Copia la URL generada al fondo de la página
5. Pega esa URL en tu navegador, selecciona tu servidor y haz clic en **`Autorizar`**

> ✅ El bot debería aparecer ahora en la lista de miembros de tu servidor (estará desconectado hasta que lo inicies)

---

## 📊 Paso 3 — Configurar Google Sheets

El bot guarda toda la información de personajes en una hoja de cálculo de Google. Necesitas crear esa hoja y darle acceso al bot.

### 3.1 — Crear la hoja de cálculo

1. Ve a [sheets.google.com](https://sheets.google.com) e inicia sesión
2. Haz clic en el botón **`+`** (Hoja de cálculo en blanco)
3. Ponle un nombre arriba (por ejemplo: `ArcanaBot Data`)
4. Ahora necesitas crear **15 pestañas** con nombres exactos. Para crear cada pestaña:
   - Haz clic en el **`+`** que está abajo a la izquierda
   - Doble clic en el nombre de la pestaña y renómbrala

Crea las siguientes pestañas **exactamente** como se muestran (respeta mayúsculas, minúsculas y sin espacios extra):

| # | Nombre exacto de la pestaña | ¿Qué guarda? |
|---|----------------------------|--------------|
| 1 | `UniformesPendientes` | Solicitudes de uniforme en revisión |
| 2 | `UniformesAprobados` | Uniformes aprobados |
| 3 | `EstudiantesPendientes` | Fichas de estudiante en revisión |
| 4 | `EstudiantesAprobados` | Estudiantes aprobados |
| 5 | `Profesores` | Profesores aprobados |
| 6 | `Trabajadores` | Trabajadores aprobados |
| 7 | `TrabajosPendientes` | Fichas de trabajo en revisión |
| 8 | `GlobalStats` | Estadísticas generales |
| 9 | `PuntosPC` | Puntos de conducta por usuario |
| 10 | `HistorialPC` | Historial completo de puntos |
| 11 | `Sanciones` | Sanciones activas |
| 12 | `FichasPoder` | Fichas de poder aprobadas |
| 13 | `HistorialSpins` | Historial de tiradas de poder |
| 14 | `HistorialBatallas` | Registro de batallas |
| 15 | `CodigosID` | Códigos de carnet generados |

> ⚠️ Los nombres deben ser exactamente iguales. Un espacio de más o una letra diferente hará que el bot falle.

### 3.2 — Copiar el ID de tu hoja

Desde la barra de dirección del navegador, copia el ID que aparece en la URL:

```
https://docs.google.com/spreadsheets/d/  ESTE_ES_EL_ID  /edit
```

Guarda ese ID — lo necesitarás en el `.env`.

### 3.3 — Crear un proyecto en Google Cloud

> 💡 Google Cloud es el sistema que permite que el bot lea y escriba en tu hoja de cálculo de forma automática.

1. Ve a [console.cloud.google.com](https://console.cloud.google.com) e inicia sesión
2. En la parte superior, haz clic en el selector de proyectos (dice "Seleccionar proyecto" o muestra el nombre de un proyecto)
3. En la ventana que aparece, haz clic en **`Nuevo proyecto`**
4. Ponle un nombre (por ejemplo: `ArcanaBot`) y haz clic en **`Crear`**
5. Espera unos segundos y asegúrate de que ese proyecto esté seleccionado arriba

### 3.4 — Activar las APIs necesarias

1. En el menú izquierdo, haz clic en **`APIs y Servicios`** → **`Biblioteca`**
2. En el buscador, escribe **`Google Sheets API`**
3. Haz clic en el resultado y luego en el botón azul **`Habilitar`**
4. Vuelve a la biblioteca, busca **`Google Drive API`** y habilítala también

### 3.5 — Crear la cuenta de servicio

> 💡 Una "cuenta de servicio" es como un usuario robot que el bot usará para acceder a tu hoja sin necesitar tu contraseña.

1. Ve a **`APIs y Servicios`** → **`Credenciales`**
2. Haz clic en **`+ Crear credenciales`** → **`Cuenta de servicio`**
3. En el campo **`Nombre de cuenta de servicio`** escribe algo como `arcanabot-sheets`
4. Haz clic en **`Crear y continuar`**
5. En el paso 2 ("Otorgar acceso..."), en el menú desplegable **`Seleccionar un rol`**, elige **`Editor`** (está en la sección "Básico")
6. Haz clic en **`Continuar`** y luego en **`Listo`**

### 3.6 — Descargar el archivo de credenciales

1. Verás tu nueva cuenta de servicio en la lista. Haz clic en su nombre (o en el ícono del lápiz ✏️)
2. Ve a la pestaña **`Claves`**
3. Haz clic en **`Agregar clave`** → **`Crear clave nueva`**
4. Selecciona formato **`JSON`** y haz clic en **`Crear`**
5. Se descargará automáticamente un archivo con un nombre largo. **Renómbralo a `credentials.json`**
6. Mueve ese archivo a la carpeta donde descargaste el bot

### 3.7 — Compartir la hoja con la cuenta de servicio

1. Abre el archivo `credentials.json` con el bloc de notas
2. Busca la línea que dice `"client_email"` — copia el correo que aparece ahí
   - Se verá algo así: `arcanabot-sheets@arcanabot-12345.iam.gserviceaccount.com`
3. Ve a tu hoja de Google Sheets
4. Haz clic en el botón **`Compartir`** (arriba a la derecha)
5. Pega el correo de la cuenta de servicio en el campo de destinatarios
6. Cambia el permiso a **`Editor`**
7. **Desmarca** la opción "Notificar a las personas" (así no llegará un correo)
8. Haz clic en **`Compartir`**

> ✅ Ahora el bot tiene acceso para leer y escribir en tu hoja de cálculo.

---

## 🎨 Paso 4 — Personalizar el bot para tu servidor

Aquí es donde adaptas el bot para que use los nombres, roles y canales de **tu** servidor. Hay dos archivos que debes editar.

### 4.1 — Crear el archivo `.env`

El archivo `.env` guarda los datos privados de tu bot (tokens, IDs).

1. En la carpeta del bot, busca el archivo llamado `.env.example`
2. **Copia** ese archivo y renombra la copia a `.env` (sin `.example`)
3. Abre `.env` con el bloc de notas

Llena cada campo con la información de tu servidor:

```env
# ── DISCORD ──────────────────────────────────────────
# El token que copiaste en el Paso 2.3
DISCORD_TOKEN=pega_tu_token_aqui

# El ID de tu servidor que copiaste en el Paso 2.5
GUILD_ID=123456789012345678

# ── GOOGLE SHEETS ─────────────────────────────────────
# El ID de tu hoja que copiaste en el Paso 3.2
GOOGLE_SHEETS_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms

# ── CANALES ──────────────────────────────────────────
# Para cada canal: clic derecho en el canal en Discord → Copiar ID
CANAL_ENVIAR_UNIFORME=id_del_canal_donde_los_usuarios_piden_uniforme
CANAL_REGISTRAR_ESTUDIANTE=id_del_canal_donde_los_usuarios_registran_estudiantes
CANAL_REGISTRO_TRABAJOS=id_del_canal_donde_los_usuarios_registran_trabajos
CANAL_CARTA_ACEPTACION=id_del_canal_donde_se_anuncian_las_aceptaciones
CANAL_FICHAS_ESTUDIANTES=id_del_canal_donde_se_guardan_fichas_de_estudiantes
CANAL_FICHAS_PROFESORES=id_del_canal_donde_se_guardan_fichas_de_profesores
CANAL_FICHAS_TRABAJADORES=id_del_canal_donde_se_guardan_fichas_de_trabajadores
CANAL_REVISION_UNIFORMES=id_del_canal_de_revision_de_uniformes_para_el_staff
CANAL_REVISION_FICHAS=id_del_canal_de_revision_de_fichas_para_el_staff
CANAL_LOGS_BOT=id_del_canal_donde_el_bot_registra_sus_acciones
CANAL_SANCIONES=id_del_canal_donde_se_publican_las_sanciones

# ── ROLES ─────────────────────────────────────────────
# Para cada rol: en Discord, ve a Ajustes del servidor → Roles
# Haz clic derecho en el rol → Copiar ID
ROL_STAFF=id_del_rol_de_staff
ROL_ESTUDIANTE=id_del_rol_que_se_da_al_aprobar_una_ficha_de_estudiante
ROL_PROFESOR=id_del_rol_que_se_da_al_aprobar_una_ficha_de_profesor
ROL_TRABAJADOR=id_del_rol_que_se_da_al_aprobar_una_ficha_de_trabajador
ROL_REGISTRADO=id_del_rol_que_se_da_cuando_cualquier_personaje_es_aprobado
ROL_SLOT_ADICIONAL=id_del_rol_que_se_consume_cuando_se_usa_un_slot_extra
ROL_CONSEJO=id_del_rol_del_consejo_estudiantil_que_puede_dar_puntos

# ── GENERACIÓN ────────────────────────────────────────
# El número de generación actual de tu servidor (empieza en 1)
GENERACION_ACTUAL=1
```

> 💡 **¿Cómo copio el ID de un canal?** En Discord, haz **clic derecho** en el canal → **`Copiar ID`** (si no aparece esa opción, vuelve al Paso 2.4 para activar el modo desarrollador).

> 💡 **¿Cómo copio el ID de un rol?** Ve a **Ajustes del servidor** → **Roles** → haz **clic derecho** en el rol → **`Copiar ID`**.

> ⚠️ Si un rol no existe en tu servidor o no quieres usarlo, pon `0` en su lugar. Por ejemplo: `ROL_CONSEJO=0`

### 4.2 — Editar `utils/constants.py`

Este archivo es donde personalizas las listas de casas, materias, cargos, clubes y más cosas específicas de tu servidor. Ábrelo con el bloc de notas o cualquier editor de texto.

> 💡 Solo debes cambiar los valores que están entre comillas `""` o entre corchetes `[]`. No borres las comas ni los dos puntos `:`.

---

#### 🏠 CASAS (facciones del servidor)

```python
CASAS = ["Redmeadow", "Ledacrealis", "Ravyelle", "Azorya"]
```

Cambia los nombres por las casas de **tu** servidor. Si tu servidor no tiene casas, déjalo como una lista vacía:

```python
CASAS = []
```

> ⚠️ Si lo dejas vacío (`[]`), el bot **omitirá automáticamente** el selector de casa al registrar personajes.

---

#### 👔 CARGOS (puestos de trabajo disponibles)

```python
CARGOS = {
    "Bibliotecario":  2,
    "Secretario":     2,
    "Enfermero":      3,
    "Inspector":      None,
    "Decano":         1,
}
```

Cada cargo tiene:
- El **nombre** del cargo (entre comillas)
- El **límite de personas** que pueden tener ese cargo (`None` = sin límite)

Para agregar un cargo nuevo:
```python
"Nombre del cargo": 2,   # máximo 2 personas
"Otro cargo":       None, # sin límite
```

---

#### 📚 MATERIAS (para profesores)

```python
MATERIAS = [
    "Criminología", "Química", "Astronomía", "Biología",
    "Historia de la magia", "Alquimia",
]
```

Cambia o agrega las materias que tiene tu servidor. Cada materia permite **1 profesor** por defecto. Si quieres permitir más, edita también esta línea:

```python
MATERIAS_LIMITE = {m: 1 for m in MATERIAS}     # 1 profesor por materia
MATERIAS_LIMITE["Profesor sustituto"] = 3       # excepto sustitutos: 3
```

---

#### 🎭 CLUBES (para estudiantes)

```python
CLUBES = {
    "Danza":      123456789012345678,
    "Deportes":   123456789012345678,
    "Música":     123456789012345678,
}
```

Cada club tiene:
- El **nombre** del club (entre comillas)
- El **ID del rol** de Discord que se asigna al unirse a ese club

Para obtener el ID de un rol: clic derecho en el rol en Discord → **Copiar ID**.

Si tu servidor no tiene clubes, déjalo como un diccionario vacío:

```python
CLUBES = {}
```

> ⚠️ Si lo dejas vacío (`{}`), el bot **omitirá automáticamente** el selector de clubes al registrar estudiantes.

---

#### 🎰 SLOTS (límite de personajes por generación)

```python
SLOTS_CONFIG = {
    1: {"estudiantes": 3, "trabajadores": 2, "profesores": 2},
    "default": {"estudiantes": 3, "trabajadores": 2, "profesores": 2}
}
```

Aquí defines cuántos personajes de cada tipo puede crear cada usuario por generación.

- El número `1` es la configuración de la Generación 1
- `"default"` se usa para cualquier generación que no tenga configuración específica
- Puedes agregar configuraciones para generaciones futuras:
  ```python
  SLOTS_CONFIG = {
      1: {"estudiantes": 3, "trabajadores": 2, "profesores": 2},
      2: {"estudiantes": 2, "trabajadores": 1, "profesores": 1},
      "default": {"estudiantes": 2, "trabajadores": 1, "profesores": 1}
  }
  ```
### 🪪 Imágenes de los Carnés de Identidad

El bot incluye imágenes de carnés de identidad **prediseñadas para el servidor Isefora Academia Arcana**. Para adaptarlas a tu servidor necesitas reemplazarlas:

> ⚠️ **Importante:** Los archivos de imagen deben mantener **exactamente los mismos nombres** que los originales y estar en la **raíz del proyecto** (la carpeta principal, junto a `bot.py`) para que el bot los encuentre correctamente.

| Archivo | Para quién | Dimensiones |
|---|---|---|
| `IDEstudiante.png` | Estudiantes | 600 × 400 px |
| `IDWorker.png` | Profesores y Trabajadores | 400 × 600 px |

1. Ve a la carpeta donde están guardadas las imágenes de los carnés (dentro del proyecto)
2. Diseña tus propias versiones para tu servidor siguiendo la misma plantilla / disposición de los carnés de ejemplo.
3. Guárdalas con los **mismos nombres de archivo** (`IDEstudiante.png` y `IDWorker.png`) que las originales (respetando mayúsculas, minúsculas y extensión)
4. Cópialas a la carpeta raíz del proyecto, reemplazando los archivos originales

Si subes una imagen con un nombre distinto o en una carpeta diferente, el bot no podrá encontrarla y los carnés no se generarán correctamente.
> 💡 **Consejo:** Deja espacio en blanco en las zonas donde el bot escribe el texto (nombre, casa, generación, código) y donde pega la foto del personaje. Si no tienes claro dónde van esas zonas, usa primero las plantillas originales como referencia visual.

---

#### ✨ SISTEMA DE SPINS DE PODER (categorías de razas)

Las categorías de razas y sus probabilidades están en `CATEGORIAS_RAZA`. Los pesos actuales son:

| Categoría | Probabilidad |
|-----------|-------------|
| ⚪ Básico | 40% |
| 🔵 Sensitivo | 25% |
| 🟢 Épico | 15% |
| 🟡 Mítico | 10% |
| 🟠 Legendario | 6% |
| 🔴 Maldito | 3% |
| ✨ Divino | 1% |

Para ajustar las probabilidades, cambia el valor `"peso"` de cada categoría. Los pesos no tienen que sumar 100 — el bot calcula el porcentaje automáticamente.

---

## 🚀 Paso 5 — Hosting: elige cómo correr el bot

Tienes dos opciones para que el bot funcione. Elige la que más te convenga:

| | Opción A: Railway (en la nube) | Opción B: Tu computadora |
|---|---|---|
| **Costo** | Gratis (con límites) o ~$5/mes | Gratis |
| **El bot funciona** | 24/7 siempre | Solo cuando tu PC está encendida |
| **Dificultad** | Media | Fácil |
| **Recomendado para** | Servidores activos | Pruebas o servidores pequeños |

> ⚠️ **Una cosa más a tener en cuenta:** Si decides correr el Bot desde tu PC, tendrás que iniciarlo desde la terminal cada vez que vuelvas a encender tu PC.

> 💡 **Sobre el costo de Railway:** Railway cobra por uso real. Un bot pequeño típicamente consume menos de $1-2 del crédito mensual de $5. En la práctica casi nunca se llega al límite.

> 🔍 **¿Quieres explorar otras opciones de hosting?** Existen otros servicios como **Fly.io**, **Oracle Cloud Free Tier**, **Render** o **DigitalOcean** que pueden funcionar para alojar bots de Discord. Cada uno tiene su propio proceso de configuración — si te interesa alguno, puedes preguntarle a tu IA de confianza cómo hacer el setup para un bot de Python. 😊

---

### Opción A — Railway (recomendado para servidores activos)

Railway mantiene el bot funcionando 24/7 sin que tengas que dejar tu computadora encendida.

### 5.1 — Subir el código a GitHub

Si descargaste el ZIP y nunca has usado GitHub:

1. Ve a [github.com](https://github.com) e inicia sesión
2. Haz clic en **`+`** → **`New repository`**
3. Ponle un nombre (por ejemplo: `mi-arcanabot`)
4. Selecciona **`Private`** (privado — para que nadie vea tu código)
5. Haz clic en **`Create repository`**
6. Descarga **GitHub Desktop** desde [desktop.github.com](https://desktop.github.com)
7. En GitHub Desktop: **`File`** → **`Add Local Repository`** → selecciona la carpeta del bot
8. Haz clic en **`Publish repository`** y selecciona tu repositorio nuevo

> ⚠️ Antes de subir, asegúrate de que el archivo `.env` y `credentials.json` estén en el `.gitignore` (ya deberían estarlo). Estos archivos contienen información privada y **nunca** deben subirse a GitHub.

### 5.2 — Crear el proyecto en Railway

1. Ve a [railway.app](https://railway.app) e inicia sesión (puedes usar tu cuenta de GitHub)
2. Haz clic en **`New Project`**
3. Selecciona **`Deploy from GitHub repo`**
4. Conecta tu cuenta de GitHub si te lo pide
5. Busca y selecciona el repositorio que creaste en el paso anterior
6. Railway comenzará a intentar iniciar el bot (fallará por ahora — falta configurar las variables)

### 5.3 — Agregar las variables de entorno en Railway

1. Haz clic en tu servicio en Railway (el recuadro que aparece en el proyecto)
2. Ve a la pestaña **`Variables`**
3. Agrega **cada una** de las variables que tienes en tu `.env`:
   - Haz clic en **`New Variable`**
   - Escribe el nombre (por ejemplo: `DISCORD_TOKEN`)
   - Escribe el valor (el token que copiaste)
   - Repite para cada variable

> 💡 También puedes hacer clic en **`RAW Editor`** y pegar todo el contenido de tu `.env` de una vez.

### 5.4 — Agregar las credenciales de Google

El archivo `credentials.json` no se puede subir a GitHub por seguridad. En Railway lo agregas como variable:

1. Abre tu archivo `credentials.json` con el bloc de notas
2. Selecciona **todo el contenido** (Ctrl+A) y cópialo (Ctrl+C)
3. En Railway → Variables, crea una nueva variable:
   - Nombre: `GOOGLE_CREDENTIALS_JSON`
   - Valor: pega todo el contenido del archivo JSON
4. Haz clic en **`Add`**

### 5.5 — Crear el volumen para la base de datos

Railway borra los archivos temporales cuando reinicia el bot. Para que la base de datos se guarde permanentemente, necesitas un **volumen**:

1. En la vista de tu proyecto en Railway, haz clic en **`+ New`**
2. Selecciona **`Volume`**
3. En **`Mount Path`** escribe: `/app/data`
4. Haz clic en el botón para conectarlo a tu servicio del bot
5. Railway reiniciará el bot automáticamente

### 5.6 — Verificar que el bot está funcionando

1. En Railway, haz clic en tu servicio y ve a la pestaña **`Logs`** (o **`Deploy Logs`**)
2. Deberías ver algo como:
   ```
   ✅ Cog cargado: cogs.admin
   ✅ Cog cargado: cogs.estudiantes
   ...
   ✅ Bot conectado como TuBot#1234 (ID: 123456789)
   ✅ 25 comando(s) sincronizados: [uniforme, estudiante, ...]
   ```
3. Si ves errores, revisa la sección [Solución de problemas](#-solución-de-problemas)

---

### Opción B — Desde tu propia computadora (sin hosting)

Esta opción es ideal si quieres probar el bot, tienes un servidor pequeño, o prefieres no pagar por hosting. El bot solo funcionará mientras tu computadora esté encendida y el script corriendo.

#### B.1 — Instalar Python

1. Ve a [python.org/downloads](https://www.python.org/downloads/)
2. Descarga **Python 3.11** (busca la versión que diga `3.11.x`)
3. Ejecuta el instalador
4. **Importante:** en la primera pantalla del instalador, marca la casilla que dice **"Add Python to PATH"** antes de hacer clic en Install
5. Verifica que quedó instalado: abre la terminal (en Windows: busca `cmd` en el menú inicio) y escribe:
   ```
   python --version
   ```
   Debe mostrar `Python 3.11.x`

#### B.2 — Abrir la terminal dentro de la carpeta del bot

1. Navega a la carpeta donde descargaste el bot
2. **En Windows:** mantén presionado `Shift` y haz clic derecho dentro de la carpeta → selecciona **"Abrir ventana de PowerShell aquí"** (o "Abrir en Terminal")
3. **En Mac:** clic derecho en la carpeta → **"Nuevo terminal en la carpeta"**

#### B.3 — Crear el entorno virtual e instalar dependencias

En la terminal que abriste, escribe estos comandos uno por uno (presiona Enter después de cada uno):

```bash
# Crear el entorno virtual
python -m venv venv
```

```bash
# Activar el entorno virtual (Windows)
venv\Scripts\activate
```
```bash
# Activar el entorno virtual (Mac/Linux)
source venv/bin/activate
```

Sabrás que está activo porque aparecerá `(venv)` al inicio de la línea en la terminal.

```bash
# Instalar todas las dependencias
pip install -r requirements.txt
```

Esto puede tardar unos minutos. Verás que se descargan e instalan varios paquetes.

#### B.4 — Crear el archivo `.env`

Ya deberías haber hecho esto en el **Paso 4.1**. Si no lo has hecho, ve ahora a esa sección.

#### B.5 — Ejecutar el bot

Con el entorno virtual activado (debe aparecer `(venv)` en la terminal):

```bash
python bot.py
```

Si todo está bien, verás algo como:

```
✅ Cog cargado: cogs.admin
✅ Cog cargado: cogs.estudiantes
...
✅ Bot conectado como TuBot#1234 (ID: 123456789)
✅ Base de datos SQLite lista
✅ 25 comando(s) sincronizados
```

> ✅ ¡El bot está funcionando! Puedes minimizar la terminal pero **no la cierres** — si la cierras, el bot se desconecta.

#### B.6 — Próximas veces que quieras iniciar el bot

Cada vez que quieras arrancar el bot desde tu computadora:

```bash
# 1. Activa el entorno virtual
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 2. Ejecuta el bot
python bot.py
```

> 💡 **Tip:** Puedes crear un archivo `iniciar.bat` (Windows) con esas dos líneas para iniciar el bot con doble clic.

---

## 🧾 Referencia de comandos

### General
| Comando | Descripción |
|---------|-------------|
| `/about-bot` | Muestra información del bot, versión y créditos |

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

## 🐛 Solución de problemas

### ❌ `TypeError: expected token to be a str, received NoneType`
**Causa:** La variable `DISCORD_TOKEN` no está configurada en Railway.  
**Solución:** Ve a Railway → tu servicio → **Variables** y asegúrate de que `DISCORD_TOKEN` tiene el token correcto.

### ❌ `sqlite3.OperationalError: unable to open database file`
**Causa:** Railway no puede crear la base de datos porque no hay un volumen montado.  
**Solución:** Sigue el Paso 5.5 para crear el volumen en `/app/data`.

### ❌ Los comandos no aparecen al escribir `/`
**Causa 1:** El bot no tiene el permiso `applications.commands`.  
**Solución 1:** Sigue el Paso 2.6 para re-invitar el bot con los permisos correctos (no lo expulsa, solo actualiza permisos).

**Causa 2:** Los comandos fallaron al sincronizarse.  
**Solución 2:** Revisa los Logs en Railway para ver si aparece `❌ Error sincronizando`. Si hay un error, corrige el problema y haz un nuevo Deploy.

### ❌ `gspread.exceptions.SpreadsheetNotFound`
**Causa:** El bot no puede encontrar tu hoja de Google Sheets.  
**Solución:** 
- Verifica que `GOOGLE_SHEETS_ID` en las variables de Railway tiene el ID correcto (solo el ID, no la URL completa)
- Verifica que compartiste la hoja con el correo de la cuenta de servicio (Paso 3.7)

### ❌ `ModuleNotFoundError: No module named 'audioop'`
**Causa:** Estás usando Python 3.12 o superior, que no es compatible.  
**Solución:** En Railway, crea un archivo llamado `.python-version` en la raíz del proyecto con el contenido `3.11.9`. Luego haz un nuevo Deploy.

### ❌ El bot está en línea pero no responde a comandos
**Causa:** Los Intents privilegiados no están activados.  
**Solución:** Ve a [discord.com/developers/applications](https://discord.com/developers/applications) → tu aplicación → **Bot** → activa los tres Privileged Gateway Intents (Paso 2.2).

### ❌ "No tengo permiso para asignar ese rol"
**Causa:** El rol del bot en el servidor no está por encima de los roles que intenta asignar.  
**Solución:** En Discord, ve a **Ajustes del servidor** → **Roles**, y arrastra el rol del bot para que esté **por encima** de todos los roles que el bot asigna (ROL_ESTUDIANTE, ROL_PROFESOR, etc.)

## 🐛 Solución de otros errores comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `ModuleNotFoundError: audioop` | Python 3.12+ incompatible | Usar exactamente Python 3.11; agregar `.python-version` con `3.11.9` |
| `Forbidden: 403` al sincronizar | Bot sin permisos de `applications.commands` | Re-invitar el bot con el scope correcto |
| `gspread.exceptions.SpreadsheetNotFound` | URL incorrecta o sin permisos | Verificar URL en `.env` y que la hoja esté compartida con la cuenta de servicio |
| `discord.errors.InteractionTimedOut` | Interacción no respondida en 3s | Agregar `await interaction.response.defer()` al inicio de callbacks lentos |
| `Extension has no 'setup' function` | Falta `async def setup(bot)` en el cog | Agregar al final de cada archivo de cog |
| Slots muestran datos incorrectos | Variable `GENERACION_ACTUAL` desactualizada | Actualizar la variable de entorno en Railway/Render |
---

## 🔒 Seguridad importante

> ⚠️ **Nunca compartas ni subas estos archivos a GitHub:**
> - `.env` — contiene el token de Discord
> - `credentials.json` — contiene el acceso a Google Sheets

Si alguien obtiene tu token de Discord, puede controlar tu bot completamente. Si esto pasa:
1. Ve a [discord.com/developers/applications](https://discord.com/developers/applications) → **Bot** → **Reset Token** inmediatamente
2. Actualiza el nuevo token en Railway

---

## 📄 Licencia

[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) — Libre para usar, modificar y compartir. **No se permite el uso comercial ni la reventa.** Se debe dar crédito a la autora original.

---

## 👩‍💻 Créditos

Desarrollado con ❤️ por **Devilishh** para **Academia Arcana Isefora**.

¿Tienes dudas o necesitas ayuda? Contacta a `devilishh.` en Discord.

Contribuciones son bienvenidas — abre un issue o pull request en GitHub.
