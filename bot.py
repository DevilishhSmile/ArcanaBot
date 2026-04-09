import discord
from discord.ext import commands
import asyncio
from dotenv import load_dotenv
from utils.database import init_db
from utils.constants import TOKEN, GUILD_ID, CANAL_LOGS_BOT
from utils.image_handler import esta_esperando, get_espera, cancelar_espera

load_dotenv()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ──────────────────────────────────────────────
# LISTENER CENTRAL DE IMÁGENES
# Captura TODAS las imágenes adjuntas en el mensaje
# ──────────────────────────────────────────────

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    await bot.process_commands(message)

    if not esta_esperando(message.author.id, message.channel.id):
        return

    espera = get_espera(message.author.id)
    if not espera:
        return

    tipo = espera["tipo"]
    sin_imagen = message.content.strip().lower() in ["sin imagen", "sin imagen.", "no"]

    # Recoger TODAS las imágenes adjuntas
    imagenes = []
    if not sin_imagen:
        for att in message.attachments:
            if att.content_type and att.content_type.startswith("image/"):
                imagenes.append(att.url)

        if not imagenes:
            await message.reply(
                "❌ No detecté ninguna imagen. Adjúntala al mensaje "
                "(pégala 📋 o usa el ícono de adjunto 📎).\n"
                "Si no tienes imagen escribe `sin imagen`.",
                delete_after=15)
            return

    cancelar_espera(message.author.id)

    # La primera imagen es la principal, las demás son adicionales
    imagen_principal = imagenes[0] if imagenes else ""
    imagenes_extra   = imagenes[1:] if len(imagenes) > 1 else []

    data = {
        **espera["data"],
        "imagen":   imagen_principal,
        "imagenes": imagenes_extra,
    }

    if tipo == "uniforme":
        await _procesar_uniforme(message, data)
    elif tipo == "estudiante":
        await _procesar_estudiante(message, data)
    elif tipo == "profesor":
        await _procesar_profesor(message, data)
    elif tipo == "trabajador":
        await _procesar_trabajador(message, data)


async def _procesar_uniforme(message, data):
    from utils.sheets import guardar_uniforme_pendiente
    from utils.helpers import build_review_embed
    from utils.constants import CANAL_REVISION_UNIFORMES, COLOR_PENDIENTE
    from cogs.uniformes import UniformeReviewView

    confirm = discord.Embed(
        title="👕 Uniforme enviado a revisión",
        description=f"**Personaje:** {data['personaje']}\n\nEl staff revisará pronto. 🌟",
        color=COLOR_PENDIENTE)
    if data["imagen"]: confirm.set_image(url=data["imagen"])
    confirm.set_footer(text=f"Enviado por {message.author.display_name}")
    await message.reply(embed=confirm)

    try:
        guardar_uniforme_pendiente(data["user_id"], data["username"],
                                   data["personaje"], data["imagen"], message.id)
    except Exception as e:
        print(f"[BOT] Sheets uniforme: {e}")

    canal = bot.get_channel(CANAL_REVISION_UNIFORMES)
    if canal:
        await canal.send(embed=build_review_embed("uniforme", data),
                         view=UniformeReviewView(data=data))


async def _procesar_estudiante(message, data):
    from utils.sheets import guardar_estudiante_pendiente
    from utils.helpers import build_review_embed
    from utils.constants import CANAL_REVISION_FICHAS, COLOR_PENDIENTE
    from cogs.estudiantes import EstudianteReviewView
    from cogs.admin import cargar_generacion

    gen = cargar_generacion()
    confirm = discord.Embed(
        title="🎓 Ficha enviada a revisión",
        description=f"**Personaje:** {data['personaje']}\nEl staff revisará pronto. ✨",
        color=COLOR_PENDIENTE)
    if data["imagen"]: confirm.set_thumbnail(url=data["imagen"])
    confirm.set_footer(text=f"Enviado por {message.author.display_name}")
    await message.reply(embed=confirm)

    try:
        guardar_estudiante_pendiente(data, gen, message.id)
    except Exception as e:
        print(f"[BOT] Sheets estudiante: {e}")

    canal = bot.get_channel(CANAL_REVISION_FICHAS)
    if canal:
        await canal.send(embed=build_review_embed("estudiante", data),
                         view=EstudianteReviewView(data=data))


async def _procesar_profesor(message, data):
    from utils.sheets import guardar_trabajo_pendiente
    from utils.helpers import build_review_embed
    from utils.constants import CANAL_REVISION_FICHAS, COLOR_PENDIENTE
    from cogs.profesores import ProfesorReviewView

    confirm = discord.Embed(
        title="🧑‍🏫 Ficha de Profesor enviada a revisión",
        description=f"**Personaje:** {data['personaje']}\n**Clase:** {data.get('clase','')}\nEl staff revisará pronto. ✨",
        color=COLOR_PENDIENTE)
    if data["imagen"]: confirm.set_thumbnail(url=data["imagen"])
    confirm.set_footer(text=f"Enviado por {message.author.display_name}")
    await message.reply(embed=confirm)

    try:
        guardar_trabajo_pendiente(data, tipo="profesor", mensaje_id=message.id)
    except Exception as e:
        print(f"[BOT] Sheets profesor: {e}")

    canal = bot.get_channel(CANAL_REVISION_FICHAS)
    if canal:
        await canal.send(embed=build_review_embed("profesor", data),
                         view=ProfesorReviewView(data=data))


async def _procesar_trabajador(message, data):
    from utils.sheets import guardar_trabajo_pendiente
    from utils.helpers import build_review_embed
    from utils.constants import CANAL_REVISION_FICHAS, COLOR_PENDIENTE
    from cogs.trabajos import TrabajadorReviewView

    confirm = discord.Embed(
        title="🧑‍💼 Ficha de Trabajador enviada a revisión",
        description=f"**Personaje:** {data['personaje']}\n**Cargo:** {data.get('cargo','')}\nEl staff revisará pronto. ✨",
        color=COLOR_PENDIENTE)
    if data["imagen"]: confirm.set_thumbnail(url=data["imagen"])
    confirm.set_footer(text=f"Enviado por {message.author.display_name}")
    await message.reply(embed=confirm)

    try:
        guardar_trabajo_pendiente(data, tipo="trabajador", mensaje_id=message.id)
    except Exception as e:
        print(f"[BOT] Sheets trabajador: {e}")

    canal = bot.get_channel(CANAL_REVISION_FICHAS)
    if canal:
        await canal.send(embed=build_review_embed("trabajador", data),
                         view=TrabajadorReviewView(data=data))


# ──────────────────────────────────────────────
# INICIO
# ──────────────────────────────────────────────

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user} (ID: {bot.user.id})")
    await init_db()
    print("✅ Base de datos SQLite lista")

    guild = discord.Object(id=GUILD_ID)
    bot.tree.clear_commands(guild=guild)
    bot.tree.clear_commands(guild=None)

    for cog in bot.cogs.values():
        for cmd in cog.get_app_commands():
            bot.tree.add_command(cmd, guild=guild)

    try:
        synced = await bot.tree.sync(guild=guild)
        await bot.tree.sync()
        print(f"✅ {len(synced)} comando(s): {[c.name for c in synced]}")
    except Exception as e:
        print(f"❌ Error sincronizando: {e}")

    if CANAL_LOGS_BOT:
        canal = bot.get_channel(CANAL_LOGS_BOT)
        if canal:
            await canal.send(embed=discord.Embed(
                title="🟢 Bot iniciado",
                description="IseforaBot está en línea.",
                color=0x57F287))

@bot.event
async def on_error(event, *args, **kwargs):
    import traceback
    print(f"❌ Error en {event}:")
    traceback.print_exc()


async def load_cogs():
    # admin PRIMERO — otros cogs lo importan
    cogs = ["cogs.admin", "cogs.uniformes", "cogs.estudiantes",
            "cogs.profesores", "cogs.trabajos"]
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"✅ Cog cargado: {cog}")
        except Exception as e:
            print(f"❌ Error cargando {cog}: {e}")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
