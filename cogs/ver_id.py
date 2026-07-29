from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import io

from utils.constants import GUILD_ID, COLOR_INFO, COLOR_PENDIENTE
from utils.sheets import get_personajes_usuario


class VerID(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ver-id",
        description="Ver el ID de carnet de un personaje. Comando público.")
    @app_commands.describe(
        usuario="El usuario cuyos IDs quieres ver (deja vacío para verte a ti mismo)")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def ver_id(self, interaction: discord.Interaction,
                     usuario: discord.Member | None = None):

        target = usuario or interaction.user
        await interaction.response.defer(ephemeral=False)

        # Buscar IDs generados en Sheets
        loop = asyncio.get_event_loop()
        ids  = await loop.run_in_executor(None, _get_ids_usuario, target.id)

        if not ids:
            await interaction.followup.send(
                f"ℹ️ **{target.display_name}** no tiene IDs generados aún.\n"
                f"Usa `/generar-id` para crear el ID de un personaje.",
                ephemeral=True)
            return

        if len(ids) == 1:
            # Un solo ID — mostrar directo
            await _enviar_id_embed(interaction.followup, target, ids[0])
        else:
            # Varios IDs — selector
            view = VerIDSelectView(
                followup=interaction.followup,
                target=target,
                ids=ids,
            )
            embed = discord.Embed(
                title=f"🪪 IDs de {target.display_name}",
                description=f"Tiene **{len(ids)}** ID(s) generado(s). Selecciona cuál ver:",
                color=COLOR_INFO,
            )
            await interaction.followup.send(embed=embed, view=view)


def _get_ids_usuario(user_id: int) -> list[dict]:
    """Obtiene todos los IDs generados de un usuario desde CodigosID."""
    from utils.sheets import get_sheet
    try:
        rows = get_sheet("CodigosID").get_all_records()
        return [r for r in rows if str(r.get("user_id","")) == str(user_id)]
    except Exception as e:
        print(f"[VER_ID] Error leyendo CodigosID: {e}")
        return []

def _get_imagen_id(codigo: str) -> bytes | None:
    """
    Regenera la imagen del ID a partir del código.
    Usa la foto_url guardada en CodigosID si existe.
    """
    from utils.sheets import get_sheet, get_personajes_usuario
    from cogs.generar_id import _generar_id_imagen, _descargar_imagen, GEN_SERVIDOR, GENERACION_ACTUAL
    from datetime import datetime
    import asyncio, io

    try:
        # Buscar datos del código en CodigosID
        rows = get_sheet("CodigosID").get_all_records()
        fila = next((r for r in rows if r.get("codigo","") == codigo), None)
        if not fila:
            return None

        user_id          = int(fila.get("user_id", 0))
        personaje_nombre = fila.get("personaje", "")
        tipo             = fila.get("tipo", "estudiante")
        foto_url         = fila.get("foto_url", "")

        # Buscar datos completos del personaje
        personajes = get_personajes_usuario(user_id)
        personaje  = next(
            (p for p in personajes if p["personaje"].strip().lower() == personaje_nombre.strip().lower()),
            None) or {"personaje": personaje_nombre, "tipo": tipo}

        # Formatear fecha
        fecha_raw = fila.get("fecha", "") or personaje.get("fecha_aprobacion", "")
        if fecha_raw:
            try:
                from datetime import datetime as dt
                fecha_ingreso = dt.strptime(fecha_raw[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
            except Exception:
                fecha_ingreso = fecha_raw
        else:
            fecha_ingreso = datetime.now().strftime("%d/%m/%Y")

        datos_id = {
            "personaje":     personaje.get("personaje", "—"),
            "elemento":      personaje.get("elemento", "—") or "—",
            "especie":       personaje.get("especie", "—") or "—",
            "generacion":    GENERACION_ACTUAL,
            "casa":          personaje.get("casa", "—") or "—",
            "fecha_ingreso": fecha_ingreso,
            "cargo_display": personaje.get("materia", personaje.get("cargo", "—")),
            "codigo_id":     codigo,
        }

        # Descargar foto si hay URL guardada
        foto_img = None
        if foto_url:
            try:
                loop = asyncio.new_event_loop()
                foto_img = loop.run_until_complete(_descargar_imagen(foto_url))
                loop.close()
            except Exception as e:
                print(f"[VER_ID] No se pudo descargar foto: {e}")

        buffer = _generar_id_imagen(datos_id, foto_img)
        return buffer.read()

    except Exception as e:
        print(f"[VER_ID] Error generando imagen: {e}")
        return None


async def _enviar_id_embed(followup, target: discord.Member, id_data: dict):
    """Envía el embed con el ID regenerado."""
    codigo   = id_data.get("codigo", "—")
    personaje = id_data.get("personaje", "—")
    tipo     = id_data.get("tipo", "estudiante")
    fecha    = id_data.get("fecha", "—")

    iconos = {"estudiante": "🎓", "profesor": "🧑‍🏫", "trabajador": "🧑‍💼"}

    # Regenerar imagen del ID
    loop   = asyncio.get_event_loop()
    imagen = await loop.run_in_executor(None, _get_imagen_id, codigo)

    embed = discord.Embed(
        title=f"🪪 ID — {personaje}",
        description=(
            f"**Código:** `{codigo}`\n"
            f"**Tipo:** {iconos.get(tipo,'')} {tipo.capitalize()}\n"
            f"**Generado:** {fecha[:10] if fecha else '—'}"
        ),
        color=COLOR_INFO,
    )
    embed.set_author(name=target.display_name, icon_url=target.display_avatar.url)

    if imagen:
        nombre_archivo = f"ID_{personaje.replace(' ','_')}.png"
        archivo = discord.File(io.BytesIO(imagen), filename=nombre_archivo)
        embed.set_image(url=f"attachment://{nombre_archivo}")
        await followup.send(embed=embed, file=archivo)
    else:
        await followup.send(embed=embed)


class VerIDSelectView(discord.ui.View):
    def __init__(self, followup, target, ids):
        super().__init__(timeout=120)
        self.followup = followup
        self.target   = target
        self.ids      = ids

        iconos = {"estudiante": "🎓", "profesor": "🧑‍🏫", "trabajador": "🧑‍💼"}
        options = [
            discord.SelectOption(
                label=r.get("personaje", "—"),
                value=r.get("codigo", ""),
                description=f"Código: {r.get('codigo','')}",
                emoji=iconos.get(r.get("tipo",""), "📋"),
            )
            for r in ids[:25]  # Discord permite máx 25 opciones
        ]
        select = discord.ui.Select(
            placeholder="🪪 Selecciona el personaje...",
            options=options, min_values=1, max_values=1)
        select.callback = self._on_select
        self.add_item(select)

    async def _on_select(self, interaction: discord.Interaction):
        codigo   = interaction.data["values"][0]
        id_data  = next((r for r in self.ids if r.get("codigo") == codigo), None)
        if not id_data:
            await interaction.response.send_message("❌ No encontrado.", ephemeral=True)
            return
        await interaction.response.defer()
        await _enviar_id_embed(interaction.followup, self.target, id_data)
        self.stop()


async def setup(bot):
    await bot.add_cog(VerID(bot))
