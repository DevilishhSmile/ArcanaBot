from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import io
import asyncio
import urllib.request
from datetime import datetime

from utils.constants import GUILD_ID, GENERACION_ACTUAL, COLOR_PENDIENTE, COLOR_INFO
from utils.sheets import get_personajes_usuario

# ──────────────────────────────────────────────
# CONFIGURACIÓN DE POSICIONES EN LA PLANTILLA
# Calibradas con la plantilla IDEstudiante.png (600x400px)
# ──────────────────────────────────────────────

PLANTILLA_PATH = "IDEstudiante.png"

# (campo, x, y)
POSICIONES = {
    "nombre":        (350, 205),
    "elemento":      (350, 228),
    "especie":       (350, 251),
    "generacion":    (375, 268),
    "casa":          (325, 291),
    "fecha_ingreso": (425, 313),
    "codigo":        (75,  367),  # en barra inferior
}

# Zona de la foto (rectángulo redondeado)
FOTO_X1, FOTO_Y1 = 18,  20
FOTO_X2, FOTO_Y2 = 255, 348

COLOR_TEXTO = (130, 80, 50)
COLOR_BARRA = (220, 185, 150)

# Número real del servidor para mostrar en el ID
GEN_SERVIDOR = GENERACION_ACTUAL + 3  # Gen 1 bot = Gen 4 servidor

# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def _get_siguiente_codigo(tipo: str) -> str:
    """Genera el código secuencial ISE-GEN-TIPO-NNNN."""
    from utils.sheets import get_sheet
    tipo_map = {"estudiante": "EST", "profesor": "PRF", "trabajador": "TRB"}
    tipo_str = tipo_map.get(tipo, "EST")
    gen_str  = f"{GEN_SERVIDOR:02d}"
    try:
        rows = get_sheet("CodigosID").get_all_values()
        # Filtrar por tipo y generación
        prefix = f"ISE-{gen_str}-{tipo_str}-"
        nums = []
        for row in rows[1:]:
            if len(row) > 0 and row[0].startswith(prefix):
                try:
                    nums.append(int(row[0].replace(prefix, "")))
                except ValueError:
                    pass
        siguiente = max(nums) + 1 if nums else 1
        return f"ISE-{gen_str}-{tipo_str}-{siguiente:04d}"
    except Exception as e:
        print(f"[ID] Error obteniendo código: {e}")
        import random
        return f"ISE-{gen_str}-{tipo_str}-{random.randint(1000,9999)}"

def _registrar_codigo(codigo: str, user_id: int, personaje: str, tipo: str):
    """Guarda el código generado en Sheets."""
    from utils.sheets import get_sheet
    try:
        get_sheet("CodigosID").append_row(
            [codigo, str(user_id), personaje, tipo,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            value_input_option="USER_ENTERED")
    except Exception as e:
        print(f"[ID] Error registrando código: {e}")

async def _descargar_imagen(url: str) -> Image.Image | None:
    """Descarga una imagen desde una URL de Discord."""
    try:
        loop = asyncio.get_event_loop()
        def _fetch():
            req = urllib.request.Request(url, headers={"User-Agent": "IseforaBot/1.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.read()
        data = await loop.run_in_executor(None, _fetch)
        return Image.open(io.BytesIO(data)).convert("RGBA")
    except Exception as e:
        print(f"[ID] Error descargando imagen: {e}")
        return None

def _generar_id_imagen(data: dict, foto: Image.Image | None) -> io.BytesIO:
    """
    Genera la imagen del ID con los datos del personaje.
    Devuelve un BytesIO con la imagen PNG lista para enviar.
    """
    plantilla = Image.open(PLANTILLA_PATH).convert("RGBA")
    draw      = ImageDraw.Draw(plantilla)

    try:
        font_regular = ImageFont.truetype(
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf', 13)
        font_bold = ImageFont.truetype(
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 13)
    except Exception:
        font_regular = ImageFont.load_default()
        font_bold    = ImageFont.load_default()

    # ── Pegar foto del personaje ──────────────────
    if foto:
        try:
            fw = FOTO_X2 - FOTO_X1
            fh = FOTO_Y2 - FOTO_Y1

            # Recortar foto al aspect ratio del hueco (mantener centro)
            foto_rgb = foto.convert("RGBA")
            orig_w, orig_h = foto_rgb.size
            ratio_w = fw / orig_w
            ratio_h = fh / orig_h
            ratio   = max(ratio_w, ratio_h)
            nuevo_w = int(orig_w * ratio)
            nuevo_h = int(orig_h * ratio)
            foto_rgb = foto_rgb.resize((nuevo_w, nuevo_h), Image.LANCZOS)

            # Centrar y recortar
            left = (nuevo_w - fw) // 2
            top  = (nuevo_h - fh) // 2
            foto_rgb = foto_rgb.crop((left, top, left + fw, top + fh))

            # Máscara redondeada para la foto
            mask = Image.new("L", (fw, fh), 0)
            mask_draw = ImageDraw.Draw(mask)
            radio = 20
            mask_draw.rounded_rectangle([(0, 0), (fw-1, fh-1)], radius=radio, fill=255)

            plantilla.paste(foto_rgb, (FOTO_X1, FOTO_Y1), mask)
        except Exception as e:
            print(f"[ID] Error pegando foto: {e}")

    # ── Escribir campos de texto ──────────────────
    gen_real = GEN_SERVIDOR + (data.get("generacion", 1) - 1)

    textos = [
        ("nombre",        data.get("personaje", "—"),          font_regular, COLOR_TEXTO),
        ("elemento",      data.get("elemento", "—"),           font_regular, COLOR_TEXTO),
        ("especie",       data.get("especie", "—"),            font_regular, COLOR_TEXTO),
        ("generacion",    f"Gen {GEN_SERVIDOR}",               font_regular, COLOR_TEXTO),
        ("casa",          data.get("casa", "—"),               font_regular, COLOR_TEXTO),
        ("fecha_ingreso", data.get("fecha_ingreso", "—"),      font_regular, COLOR_TEXTO),
        ("codigo",        data.get("codigo_id", "ISE-00-EST-0000"), font_bold, COLOR_BARRA),
    ]

    for campo, texto, font, color in textos:
        x, y = POSICIONES[campo]
        # Truncar si es muy largo
        max_chars = 22
        if len(texto) > max_chars:
            texto = texto[:max_chars - 1] + "…"
        draw.text((x, y), texto, font=font, fill=color)

    # Convertir a RGB para guardar como PNG
    resultado = plantilla.convert("RGB")
    buffer = io.BytesIO()
    resultado.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)
    return buffer


# ──────────────────────────────────────────────
# VIEWS
# ──────────────────────────────────────────────

class SeleccionarPersonajeIDView(discord.ui.View):
    """Paso 1 — seleccionar qué personaje quiere su ID."""

    def __init__(self, user_id: int, personajes: list[dict]):
        super().__init__(timeout=120)
        self.user_id   = user_id
        self.personajes = personajes

        options = [
            discord.SelectOption(
                label=p["personaje"],
                value=p["personaje"],
                description=p["tipo"].capitalize(),
                emoji={"estudiante": "🎓", "profesor": "🧑‍🏫", "trabajador": "🧑‍💼"}.get(p["tipo"], "📋"),
            )
            for p in personajes
        ]
        select = discord.ui.Select(
            placeholder="🎓 Selecciona el personaje...",
            options=options, min_values=1, max_values=1)
        select.callback = self._on_select
        self.add_item(select)

    async def _on_select(self, interaction: discord.Interaction):
        nombre    = interaction.data["values"][0]
        personaje = next((p for p in self.personajes if p["personaje"] == nombre), None)
        if not personaje:
            await interaction.response.edit_message(
                content="❌ No se encontró el personaje.", view=None); return

        # Guardar selección en temp
        if not hasattr(interaction.client, "_id_temp"):
            interaction.client._id_temp = {}
        interaction.client._id_temp[self.user_id] = {
            "personaje": personaje,
            "foto_url":  None,
        }

        # Mostrar opciones de foto si el personaje tiene imágenes guardadas
        imagenes = personaje.get("imagenes", [])
        if imagenes:
            view = SeleccionarFotoView(
                user_id=self.user_id,
                personaje=personaje,
                imagenes=imagenes,
                canal_id=interaction.channel_id,
            )
            await interaction.response.edit_message(
                content=(
                    f"✅ **{nombre}** seleccionado.\n\n"
                    f"📸 ¿Qué imagen quieres usar para el ID?\n"
                    f"Puedes elegir una de las que ya enviaste en la ficha, "
                    f"o subir una nueva."
                ),
                view=view,
            )
        else:
            # No hay imágenes guardadas — pedir una nueva
            from utils.image_handler import registrar_espera
            registrar_espera(self.user_id, "generar_id", interaction.channel_id,
                             {"personaje": personaje})
            await interaction.response.edit_message(
                content=(
                    f"✅ **{nombre}** seleccionado.\n\n"
                    f"📎 Envía la imagen para el ID en este canal.\n"
                    f"Pégala 📋 o adjúntala 🖼️\n\n"
                    f"*Escribe `sin imagen` para generar el ID sin foto.*"
                ),
                view=None,
            )
        self.stop()


class SeleccionarFotoView(discord.ui.View):
    """Paso 2 — elegir foto de la ficha o subir una nueva."""

    def __init__(self, user_id: int, personaje: dict,
                 imagenes: list[str], canal_id: int):
        super().__init__(timeout=120)
        self.user_id   = user_id
        self.personaje = personaje
        self.imagenes  = imagenes
        self.canal_id  = canal_id

        # Botones para cada imagen de la ficha (máx 3)
        for i, url in enumerate(imagenes[:3]):
            btn = discord.ui.Button(
                label=f"📷 Imagen {i+1} de la ficha",
                style=discord.ButtonStyle.secondary,
                custom_id=f"foto_{i}",
                row=0,
            )
            btn.callback = self._make_callback(url)
            self.add_item(btn)

    def _make_callback(self, url: str):
        async def callback(interaction: discord.Interaction):
            await self._procesar(interaction, url)
        return callback

    async def _procesar(self, interaction: discord.Interaction, url: str | None):
        if not hasattr(interaction.client, "_id_temp"):
            interaction.client._id_temp = {}
        temp = interaction.client._id_temp.get(self.user_id, {})
        temp["foto_url"] = url
        interaction.client._id_temp[self.user_id] = temp

        if url:
            await _generar_y_enviar(interaction, self.user_id)
        else:
            from utils.image_handler import registrar_espera
            registrar_espera(self.user_id, "generar_id", self.canal_id,
                             {"personaje": self.personaje})
            await interaction.response.edit_message(
                content=(
                    f"📎 Envía la imagen nueva para el ID en este canal.\n"
                    f"Pégala 📋 o adjúntala 🖼️\n\n"
                    f"*Escribe `sin imagen` para generar sin foto.*"
                ),
                view=None,
            )
        self.stop()

    @discord.ui.button(label="📤 Subir imagen nueva", style=discord.ButtonStyle.primary, row=1)
    async def subir_nueva(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._procesar(interaction, None)


async def _generar_y_enviar(interaction: discord.Interaction, user_id: int):
    """Genera la imagen del ID y la envía al canal."""
    await interaction.response.defer(ephemeral=True)

    temp      = getattr(interaction.client, "_id_temp", {}).get(user_id, {})
    personaje = temp.get("personaje", {})
    foto_url  = temp.get("foto_url")

    # Descargar foto si hay URL
    foto_img = None
    if foto_url:
        foto_img = await _descargar_imagen(foto_url)

    # Obtener datos del personaje
    datos = {
        "personaje":     personaje.get("personaje", "—"),
        "elemento":      personaje.get("elemento", "—"),
        "especie":       personaje.get("especie", "—"),
        "generacion":    GENERACION_ACTUAL,
        "casa":          personaje.get("casa", "—"),
        "fecha_ingreso": personaje.get("fecha_aprobacion",
                         datetime.now().strftime("%d/%m/%Y")),
    }

    # Generar código único
    tipo   = personaje.get("tipo", "estudiante")
    codigo = await asyncio.get_event_loop().run_in_executor(
        None, _get_siguiente_codigo, tipo)
    datos["codigo_id"] = codigo

    # Generar imagen en executor para no bloquear
    buffer = await asyncio.get_event_loop().run_in_executor(
        None, _generar_id_imagen, datos, foto_img)

    # Registrar código en Sheets
    await asyncio.get_event_loop().run_in_executor(
        None, _registrar_codigo, codigo, user_id,
        datos["personaje"], tipo)

    # Limpiar temp
    if hasattr(interaction.client, "_id_temp"):
        interaction.client._id_temp.pop(user_id, None)

    # Enviar ID
    archivo = discord.File(buffer, filename=f"ID_{datos['personaje'].replace(' ','_')}.png")
    embed = discord.Embed(
        title=f"🪪 ID Generado — {datos['personaje']}",
        description=(
            f"**Código:** `{codigo}`\n"
            f"**Casa:** {datos['casa']}\n"
            f"**Generación:** Gen {GEN_SERVIDOR}"
        ),
        color=COLOR_INFO,
    )
    embed.set_image(url=f"attachment://ID_{datos['personaje'].replace(' ','_')}.png")
    embed.set_footer(text=f"Generado para <@{user_id}>")

    await interaction.followup.send(embed=embed, file=archivo, ephemeral=False)


# ──────────────────────────────────────────────
# COG
# ──────────────────────────────────────────────

class GenerarID(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="generar-id",
        description="Genera el carnet de identificación de uno de tus personajes.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def generar_id(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        personajes = await asyncio.get_event_loop().run_in_executor(
            None, get_personajes_usuario, interaction.user.id)

        if not personajes:
            await interaction.followup.send(
                "❌ No tienes personajes registrados.", ephemeral=True)
            return

        view = SeleccionarPersonajeIDView(
            user_id=interaction.user.id,
            personajes=personajes,
        )
        await interaction.followup.send(
            embed=discord.Embed(
                title="🪪 Generar ID",
                description=(
                    "Selecciona el personaje para el que quieres generar el ID.\n\n"
                    "El bot te pedirá una foto — puedes usar una de las que "
                    "ya enviaste en tu ficha o subir una nueva."
                ),
                color=COLOR_PENDIENTE,
            ),
            view=view,
            ephemeral=True,
        )

    async def on_image_received(self, user_id: int, foto_url: str,
                                 interaction_or_message):
        """
        Llamado desde bot.py cuando llega una imagen para generar_id.
        """
        if not hasattr(self.bot, "_id_temp"):
            self.bot._id_temp = {}
        temp = self.bot._id_temp.get(user_id, {})
        temp["foto_url"] = foto_url
        self.bot._id_temp[user_id] = temp


async def setup(bot):
    await bot.add_cog(GenerarID(bot))
