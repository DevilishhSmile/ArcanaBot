from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
from datetime import datetime

from utils.constants import (
    GUILD_ID, ROL_STAFF, ROL_RESPIN,
    CATEGORIAS_RAZA, NIVELES_PODER, DESCRIPCIONES_MANA,
    COLOR_INFO, COLOR_APROBADO, COLOR_RECHAZADO, COLOR_PENDIENTE,
    CANAL_REVISION_FICHAS,
)
from utils.sheets import get_personajes_usuario

# ──────────────────────────────────────────────
# SHEETS — Hojas del sistema de spins
# FichasPoder: user_id | personaje | nivel | mana | categoria_raza |
#              habilidades | debilidades | estado | rechazos |
#              staff_revisor | fecha | ultima_actualizacion
# HistorialSpins: user_id | personaje | nivel | mana | fecha
# HistorialBatallas: user_id | personaje | rival_user_id | rival_personaje |
#                    resultado | fecha
# ──────────────────────────────────────────────

def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _get_ficha_poder(user_id: int, personaje: str) -> dict | None:
    from utils.sheets import get_sheet
    try:
        for r in get_sheet("FichasPoder").get_all_records():
            if str(r.get("user_id","")) == str(user_id) and \
               r.get("personaje","").strip().lower() == personaje.strip().lower():
                return r
    except Exception as e:
        print(f"[SPINS] _get_ficha_poder: {e}")
    return None

def _guardar_ficha_poder(user_id: int, username: str, personaje: str,
                          nivel: str, mana: int, habilidades: str,
                          debilidades: str, estado: str = "PENDIENTE",
                          rechazos: int = 0, categoria: str = ""):
    """
    Columnas Sheets (orden exacto):
    1:user_id | 2:username | 3:personaje | 4:categoria_raza | 5:nivel_poder
    6:mana | 7:habilidades | 8:debilidades | 9:estado | 10:staff_que_reviso
    11:fecha | 12:motivo_rechazo | 13:denegaciones
    """
    from utils.sheets import get_sheet
    try:
        sheet = get_sheet("FichasPoder")
        rows  = sheet.get_all_values()
        for i, row in enumerate(rows):
            if i == 0: continue
            if len(row) >= 3 and str(row[0]) == str(user_id) and \
               row[2].strip().lower() == personaje.strip().lower():
                # Al re-enviar ficha: solo actualizar habilidades/debilidades
                # nivel y maná se mantienen del spin original
                sheet.update_cell(i+1, 7,  habilidades)
                sheet.update_cell(i+1, 8,  debilidades)
                sheet.update_cell(i+1, 9,  estado)
                sheet.update_cell(i+1, 11, _now())
                return
        # Nueva fila
        sheet.append_row([
            str(user_id), username, personaje,
            categoria,      # col 4: categoria_raza (vacía, la asigna el staff)
            nivel,          # col 5: nivel_poder
            str(mana),      # col 6: mana
            habilidades,    # col 7
            debilidades,    # col 8
            estado,         # col 9
            "",             # col 10: staff_que_reviso
            _now(),         # col 11: fecha
            "",             # col 12: motivo_rechazo
            str(rechazos),  # col 13: denegaciones
        ], value_input_option="USER_ENTERED")
    except Exception as e:
        print(f"[SPINS] _guardar_ficha_poder: {e}")

def _actualizar_estado_ficha(user_id: int, personaje: str, estado: str,
                              staff: str = "", categoria: str = "",
                              rechazos: int | None = None,
                              motivo: str = ""):
    """
    Actualiza estado, staff, categoría, motivo y denegaciones en FichasPoder.
    Columnas: 4:categoria_raza | 9:estado | 10:staff | 11:fecha | 12:motivo | 13:denegaciones
    """
    from utils.sheets import get_sheet
    try:
        sheet = get_sheet("FichasPoder")
        rows  = sheet.get_all_values()
        for i, row in enumerate(rows):
            if i == 0: continue
            if len(row) >= 3 and str(row[0]) == str(user_id) and \
               row[2].strip().lower() == personaje.strip().lower():
                sheet.update_cell(i+1, 9,  estado)
                sheet.update_cell(i+1, 11, _now())
                if staff:                sheet.update_cell(i+1, 10, staff)
                if categoria:            sheet.update_cell(i+1, 4,  categoria)
                if motivo:               sheet.update_cell(i+1, 12, motivo)
                if rechazos is not None: sheet.update_cell(i+1, 13, str(rechazos))
                return
    except Exception as e:
        print(f"[SPINS] _actualizar_estado_ficha: {e}")

def _get_rechazos(user_id: int, personaje: str) -> int:
    from utils.sheets import get_sheet
    try:
        for r in get_sheet("FichasPoder").get_all_records():
            if str(r.get("user_id","")) == str(user_id) and \
               r.get("personaje","").strip().lower() == personaje.strip().lower():
                return int(r.get("denegaciones", 0) or 0)
    except Exception: pass
    return 0

def _registrar_spin(user_id: int, personaje: str, nivel: str, mana: int):
    from utils.sheets import get_sheet
    try:
        get_sheet("HistorialSpins").append_row(
            [str(user_id), personaje, nivel, str(mana), _now()],
            value_input_option="USER_ENTERED")
    except Exception as e:
        print(f"[SPINS] _registrar_spin: {e}")

def _registrar_batalla(user_id: int, personaje: str, rival_id: int,
                        rival_personaje: str, resultado: str):
    from utils.sheets import get_sheet
    try:
        get_sheet("HistorialBatallas").append_row(
            [str(user_id), personaje, str(rival_id), rival_personaje, resultado, _now()],
            value_input_option="USER_ENTERED")
    except Exception as e:
        print(f"[SPINS] _registrar_batalla: {e}")

def _get_historial_batallas(user_id: int, personaje: str) -> list:
    from utils.sheets import get_sheet
    try:
        return [r for r in get_sheet("HistorialBatallas").get_all_records()
                if str(r.get("user_id","")) == str(user_id) and
                r.get("personaje","").strip().lower() == personaje.strip().lower()]
    except Exception: return []

# ──────────────────────────────────────────────
# SPIN — Generar estadísticas aleatorias
# ──────────────────────────────────────────────

def _hacer_spin() -> dict:
    # Solo nivel y maná — la categoría la asigna el staff al revisar
    nivel = random.choices(
        ["bajo", "medio", "alto"],
        weights=[50, 35, 15],
        k=1
    )[0]
    mana = random.randint(0, 10)
    return {"nivel": nivel, "mana": mana}

def _build_spin_embed(spin: dict, personaje: str = "") -> discord.Embed:
    """Embed que ve el usuario — sin categoría de raza (es secreta hasta aprobación)."""
    nivel_data = NIVELES_PODER[spin["nivel"]]
    mana       = spin["mana"]
    mana_desc  = DESCRIPCIONES_MANA.get(mana, "")

    mensajes_inmersivos = [
        "El archipiélago ha reconocido tu esencia...",
        "Las corrientes mágicas han hablado...",
        "El velo entre mundos se ha abierto para revelar tu destino...",
        "La academia ha tomado nota de tu potencial...",
        "Los antiguos han deliberado sobre tu naturaleza...",
        "El tejido del maná se ha alineado para revelarte...",
        "Isefora ha leído tu origen en las estrellas del archipiélago...",
    ]

    embed = discord.Embed(
        title="✨ Resultado del Spin de Poder",
        description=f"*{random.choice(mensajes_inmersivos)}*",
        color=COLOR_INFO
    )
    if personaje:
        embed.add_field(name="Personaje", value=f"**{personaje}**", inline=False)

    embed.add_field(
        name=f"{nivel_data['emoji']} Nivel de Poder",
        value=f"**{nivel_data['nombre']}**\n*{nivel_data['desc']}*",
        inline=True
    )
    embed.add_field(
        name="💧 Poder de Maná",
        value=f"**{mana}/10**\n*{mana_desc}*",
        inline=True
    )
    embed.add_field(
        name="🔍 Categoría de Raza",
        value="*Pendiente de revisión del staff...*",
        inline=False
    )
    embed.set_footer(text="Completa tu ficha de poder con el botón de abajo.")
    return embed


# ──────────────────────────────────────────────
# MODALES
# ──────────────────────────────────────────────

class FichaPodeModal(discord.ui.Modal, title="✨ Ficha de Poder"):
    habilidades = discord.ui.TextInput(
        label="Habilidades del personaje",
        style=discord.TextStyle.paragraph,
        placeholder="Describe las habilidades y poderes de tu personaje...",
        min_length=20, max_length=1000,
    )
    debilidades = discord.ui.TextInput(
        label="Debilidades del personaje",
        style=discord.TextStyle.paragraph,
        placeholder="Describe las debilidades y limitaciones...",
        min_length=20, max_length=1000,
    )

    def __init__(self, personaje: str, spin: dict, user_id: int,
                 es_edicion: bool = False, es_respin: bool = False):
        super().__init__()
        self.personaje  = personaje
        self.spin       = spin
        self.user_id    = user_id
        self.es_edicion = es_edicion
        self.es_respin  = es_respin

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        loop = asyncio.get_event_loop()

        # Si ya existe ficha previa (rechazada), conservar nivel y maná originales
        ficha_previa = await loop.run_in_executor(None, _get_ficha_poder,
            interaction.user.id, self.personaje)

        if ficha_previa and not self.es_respin:
            nivel = ficha_previa.get("nivel_poder", self.spin["nivel"])
            mana  = int(ficha_previa.get("mana", self.spin["mana"]) or self.spin["mana"])
        else:
            nivel = self.spin["nivel"]
            mana  = self.spin["mana"]

        # Guardar en Sheets
        estado = "PENDIENTE"
        await loop.run_in_executor(None, _guardar_ficha_poder,
            interaction.user.id, str(interaction.user),
            self.personaje, nivel, mana,
            self.habilidades.value, self.debilidades.value, estado)

        await loop.run_in_executor(None, _registrar_spin,
            interaction.user.id, self.personaje, nivel, mana)

        # Si es re-spin, quitar el rol
        if self.es_respin:
            try:
                rol = interaction.guild.get_role(ROL_RESPIN)
                if rol and rol in interaction.user.roles:
                    await interaction.user.remove_roles(rol, reason="Re-spin usado")
            except Exception as e:
                print(f"[SPINS] Error quitando rol respin: {e}")

        # Enviar al canal de revisión
        canal = interaction.client.get_channel(CANAL_REVISION_FICHAS)
        if canal:
            embed_rev = discord.Embed(
                title=f"{'🔄 Re-spin' if self.es_respin else '✨ Ficha de Poder'} — {self.personaje}",
                description=(
                    f"**Usuario:** <@{interaction.user.id}>\n"
                    f"**Personaje:** {self.personaje}\n\n"
                    f"{NIVELES_PODER[nivel]['emoji']} **Nivel:** {NIVELES_PODER[nivel]['nombre']}\n"
                    f"💧 **Maná:** {mana}/10\n\n"
                    f"**Habilidades:**\n{self.habilidades.value}\n\n"
                    f"**Debilidades:**\n{self.debilidades.value}"
                ),
                color=COLOR_PENDIENTE
            )
            embed_rev.set_footer(text=f"Enviado por {interaction.user.display_name}")
            await canal.send(
                embed=embed_rev,
                view=FichaPodeReviewView(
                    user_id=interaction.user.id,
                    personaje=self.personaje,
                    nivel=nivel, mana=mana,
                    habilidades=self.habilidades.value,
                    debilidades=self.debilidades.value,
                    guild=interaction.guild,
                )
            )

        accion = "re-spin" if self.es_respin else "ficha de poder"
        await interaction.followup.send(
            embed=discord.Embed(
                title="✅ Enviado a revisión",
                description=(
                    f"Tu {accion} para **{self.personaje}** fue enviado al Staff.\n\n"
                    f"Recibirás un DM cuando sea revisado. 🌟"
                ),
                color=COLOR_APROBADO
            ),
            ephemeral=True
        )


class EditarFichaPodeModal(discord.ui.Modal, title="✏️ Editar Ficha de Poder"):
    habilidades = discord.ui.TextInput(
        label="Habilidades del personaje",
        style=discord.TextStyle.paragraph,
        min_length=20, max_length=1000,
    )
    debilidades = discord.ui.TextInput(
        label="Debilidades del personaje",
        style=discord.TextStyle.paragraph,
        min_length=20, max_length=1000,
    )

    def __init__(self, personaje: str, ficha_actual: dict, user_id: int):
        super().__init__()
        self.personaje = personaje
        self.ficha     = ficha_actual
        self.user_id   = user_id
        self.habilidades.default = ficha_actual.get("habilidades", "")[:1000]
        self.debilidades.default = ficha_actual.get("debilidades", "")[:1000]

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        nivel = self.ficha.get("nivel", "bajo")
        mana  = int(self.ficha.get("mana", 0))

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _guardar_ficha_poder,
            interaction.user.id, str(interaction.user),
            self.personaje, nivel, mana,
            self.habilidades.value, self.debilidades.value, "PENDIENTE")

        canal = interaction.client.get_channel(CANAL_REVISION_FICHAS)
        if canal:
            embed_rev = discord.Embed(
                title=f"✏️ Ficha de Poder Editada — {self.personaje}",
                description=(
                    f"**Usuario:** <@{interaction.user.id}>\n"
                    f"**Personaje:** {self.personaje}\n\n"
                    f"{NIVELES_PODER[nivel]['emoji']} **Nivel:** {NIVELES_PODER[nivel]['nombre']}\n"
                    f"💧 **Maná:** {mana}/10\n\n"
                    f"**Habilidades:**\n{self.habilidades.value}\n\n"
                    f"**Debilidades:**\n{self.debilidades.value}"
                ),
                color=COLOR_PENDIENTE
            )
            await canal.send(
                embed=embed_rev,
                view=FichaPodeReviewView(
                    user_id=interaction.user.id,
                    personaje=self.personaje,
                    nivel=nivel, mana=mana,
                    habilidades=self.habilidades.value,
                    debilidades=self.debilidades.value,
                    guild=interaction.guild,
                )
            )

        await interaction.followup.send(
            embed=discord.Embed(
                title="✅ Edición enviada",
                description=f"Tu ficha editada para **{self.personaje}** fue enviada al Staff. 🌟",
                color=COLOR_APROBADO
            ),
            ephemeral=True
        )


# ──────────────────────────────────────────────
# VIEWS
# ──────────────────────────────────────────────

class SpinResultView(discord.ui.View):
    """Botón que aparece después del spin para crear la ficha de poder."""
    def __init__(self, personaje: str, spin: dict, user_id: int,
                 es_respin: bool = False):
        super().__init__(timeout=300)
        self.personaje = personaje
        self.spin      = spin
        self.user_id   = user_id
        self.es_respin = es_respin

    @discord.ui.button(label="📝 Crear Ficha de Poder", style=discord.ButtonStyle.primary)
    async def crear_ficha(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Solo el dueño del personaje puede completar esta ficha.", ephemeral=True)
            return
        await interaction.response.send_modal(
            FichaPodeModal(self.personaje, self.spin, self.user_id, es_respin=self.es_respin))
        self.stop()


class FichaPodeReviewView(discord.ui.View):
    """Panel de revisión del staff para aprobar/rechazar fichas de poder."""
    def __init__(self, user_id: int, personaje: str, nivel: str, mana: int,
                 habilidades: str, debilidades: str, guild: discord.Guild):
        super().__init__(timeout=None)
        self.user_id     = user_id
        self.personaje   = personaje
        self.nivel       = nivel
        self.mana        = mana
        self.habilidades = habilidades
        self.debilidades = debilidades
        self.guild       = guild

    def _es_staff(self, i):
        return any(r.id == ROL_STAFF for r in i.user.roles)

    @discord.ui.button(label="✅ Aprobar", style=discord.ButtonStyle.success,
                       custom_id="poder_aprobar")
    async def aprobar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._es_staff(interaction):
            await interaction.response.send_message("❌ Solo el Staff puede.", ephemeral=True)
            return
        # Mostrar selector de categoría antes del modal
        view = SeleccionarCategoriaView(
            user_id=self.user_id, personaje=self.personaje,
            nivel=self.nivel, mana=self.mana,
            message=interaction.message, guild=self.guild
        )
        await interaction.response.send_message(
            embed=discord.Embed(
                title="🏷️ Selecciona la Categoría de Raza",
                description="Elige la categoría que corresponde a este personaje según sus habilidades y debilidades.",
                color=COLOR_INFO
            ),
            view=view, ephemeral=True
        )

    @discord.ui.button(label="❌ Rechazar", style=discord.ButtonStyle.danger,
                       custom_id="poder_rechazar")
    async def rechazar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._es_staff(interaction):
            await interaction.response.send_message("❌ Solo el Staff puede.", ephemeral=True)
            return
        await interaction.response.send_modal(
            RechazarFichaPodeModal(
                user_id=self.user_id, personaje=self.personaje,
                message=interaction.message, guild=self.guild
            )
        )


class SeleccionarCategoriaView(discord.ui.View):
    """Selector desplegable de categoría de raza — solo visible para el staff."""

    def __init__(self, user_id, personaje, nivel, mana, message, guild):
        super().__init__(timeout=120)
        self.user_id   = user_id
        self.personaje = personaje
        self.nivel     = nivel
        self.mana      = mana
        self.message   = message
        self.guild     = guild

        # Construir opciones del select con descripción de cada categoría
        opciones = [
            discord.SelectOption(
                label=f"{data['emoji']} {data['nombre']}",
                value=key,
                description=data["desc"][:100],  # Discord limita a 100 chars
            )
            for key, data in CATEGORIAS_RAZA.items()
        ]
        self.categoria_select.options = opciones

    @discord.ui.select(placeholder="Elige la categoría de raza...")
    async def categoria_select(self, interaction: discord.Interaction,
                                select: discord.ui.Select):
        cat_raw = select.values[0]
        # Abrir modal de notas con la categoría ya elegida
        await interaction.response.send_modal(
            AprobarFichaPodeModal(
                user_id=self.user_id, personaje=self.personaje,
                nivel=self.nivel, mana=self.mana,
                message=self.message, guild=self.guild,
                categoria_elegida=cat_raw
            )
        )


class AprobarFichaPodeModal(discord.ui.Modal, title="✅ Aprobar Ficha de Poder"):

    notas = discord.ui.TextInput(
        label="Notas para el usuario (opcional)",
        style=discord.TextStyle.paragraph,
        placeholder="Comentarios, correcciones o contexto para el usuario...",
        required=False, max_length=500,
    )

    def __init__(self, user_id, personaje, nivel, mana, message, guild,
                 categoria_elegida: str = ""):
        super().__init__()
        self.user_id           = user_id
        self.personaje         = personaje
        self.nivel             = nivel
        self.mana              = mana
        self.message           = message
        self.guild             = guild
        self.categoria_elegida = categoria_elegida

    async def on_submit(self, interaction: discord.Interaction):
        cat_raw  = self.categoria_elegida
        cat_data = CATEGORIAS_RAZA.get(cat_raw)
        if not cat_data:
            await interaction.response.send_message(
                "❌ Error interno: categoría no válida. Intenta de nuevo.",
                ephemeral=True)
            return

        cat_display = f"{cat_data['emoji']} {cat_data['nombre']}"
        loop        = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: _actualizar_estado_ficha(
            self.user_id, self.personaje, "APROBADO",
            staff=str(interaction.user),
            categoria=cat_raw,
            rechazos=0,
            motivo=""
        ))

        # Actualizar mensaje del panel de staff
        embed = discord.Embed(
            title="✨ Ficha de Poder — APROBADA ✅",
            description=(
                f"**Personaje:** {self.personaje}\n"
                f"**Usuario:** <@{self.user_id}>\n"
                f"**Categoría asignada:** {cat_display}"
            ),
            color=COLOR_APROBADO
        )
        embed.set_footer(text=f"Aprobado por {interaction.user.display_name}")
        await self.message.edit(embed=embed, view=None)
        await interaction.response.send_message("✅ Aprobado.", ephemeral=True)

        # DM al usuario con toda la info completa
        try:
            member = self.guild.get_member(self.user_id) or \
                     await self.guild.fetch_member(self.user_id)
            nivel_data = NIVELES_PODER[self.nivel]
            mana_desc  = DESCRIPCIONES_MANA.get(self.mana, "")
            dm_embed = discord.Embed(
                title="✨ ¡Tu Ficha de Poder fue aprobada!",
                description=(
                    f"Tu personaje **{self.personaje}** tiene ahora una ficha de poder oficial.\n\n"
                    f"**{cat_data['emoji']} Categoría de Raza:** {cat_data['nombre']}\n"
                    f"*{cat_data['desc']}*\n\n"
                    f"**{nivel_data['emoji']} Nivel de Poder:** {nivel_data['nombre']}\n"
                    f"*{nivel_data['desc']}*\n\n"
                    f"**💧 Poder de Maná:** {self.mana}/10\n"
                    f"*{mana_desc}*"
                    + (f"\n\n**📝 Notas del Staff:**\n{self.notas.value}" if self.notas.value else "")
                ),
                color=COLOR_APROBADO
            )
            await member.send(embed=dm_embed)
        except Exception as e:
            print(f"[SPINS] DM aprobación: {e}")


class RechazarFichaPodeModal(discord.ui.Modal, title="❌ Rechazar Ficha de Poder"):
    motivo = discord.ui.TextInput(
        label="Motivo del rechazo y correcciones",
        style=discord.TextStyle.paragraph,
        placeholder="Explica qué debe corregir el usuario...",
        min_length=10, max_length=500,
    )

    def __init__(self, user_id, personaje, message, guild):
        super().__init__()
        self.user_id   = user_id
        self.personaje = personaje
        self.message   = message
        self.guild     = guild

    async def on_submit(self, interaction: discord.Interaction):
        loop     = asyncio.get_event_loop()
        rechazos = await loop.run_in_executor(None, _get_rechazos,
            self.user_id, self.personaje)
        rechazos += 1

        await loop.run_in_executor(None, lambda: _actualizar_estado_ficha(
            self.user_id, self.personaje, "RECHAZADO",
            staff=str(interaction.user),
            categoria="",
            rechazos=rechazos,
            motivo=self.motivo.value
        ))

        embed = discord.Embed(
            title="✨ Ficha de Poder — RECHAZADA ❌",
            description=(
                f"**Personaje:** {self.personaje}\n"
                f"**Usuario:** <@{self.user_id}>\n"
                f"**Motivo:** {self.motivo.value}\n"
                f"**Rechazos acumulados:** {rechazos}/4"
            ),
            color=COLOR_RECHAZADO
        )
        embed.set_footer(text=f"Rechazado por {interaction.user.display_name}")
        await self.message.edit(embed=embed, view=None)
        await interaction.response.send_message("✅ Rechazado.", ephemeral=True)

        # DM al usuario
        try:
            member = self.guild.get_member(self.user_id) or \
                     await self.guild.fetch_member(self.user_id)
            dm_embed = discord.Embed(
                title="❌ Ficha de Poder rechazada",
                description=(
                    f"Tu ficha de poder para **{self.personaje}** fue rechazada.\n\n"
                    f"**Motivo y correcciones:**\n{self.motivo.value}\n\n"
                    f"Usa `/editar-ficha-poder` y selecciona **{self.personaje}** para corregir solo las habilidades y debilidades. 💪\n\n*Tus estadísticas de nivel y maná se mantienen del spin original.*"
                ),
                color=COLOR_RECHAZADO
            )
            await member.send(embed=dm_embed)
        except Exception as e:
            print(f"[SPINS] DM rechazo: {e}")

        # Protocolo de asistencia si llega a 4 rechazos
        if rechazos >= 4:
            try:
                canal = interaction.client.get_channel(CANAL_REVISION_FICHAS)
                if canal:
                    await canal.send(
                        content=f"<@&{ROL_STAFF}>",
                        embed=discord.Embed(
                            title="🆘 Protocolo de Asistencia activado",
                            description=(
                                f"<@{self.user_id}> ha acumulado **4 rechazos** en la ficha de poder "
                                f"de **{self.personaje}**.\n\n"
                                f"Por favor, un miembro del Staff contacte al usuario directamente "
                                f"para ayudarle a balancear su ficha de forma personalizada. 🙏"
                            ),
                            color=0xFF6B35
                        )
                    )
                # DM al usuario avisando del protocolo
                member = self.guild.get_member(self.user_id) or \
                         await self.guild.fetch_member(self.user_id)
                await member.send(embed=discord.Embed(
                    title="🆘 Asistencia personalizada",
                    description=(
                        f"Has acumulado 4 rechazos en la ficha de **{self.personaje}**.\n\n"
                        f"Un miembro del Staff se pondrá en contacto contigo para "
                        f"ayudarte a balancear tu ficha. ¡No te rindas! 💪"
                    ),
                    color=0xFF6B35
                ))
            except Exception as e:
                print(f"[SPINS] Protocolo asistencia: {e}")


class SeleccionarPersonajePodeView(discord.ui.View):
    """Selector de personaje para comandos de poder."""
    def __init__(self, user_id: int, personajes: list, accion: str,
                 extra: dict = None):
        super().__init__(timeout=120)
        self.user_id   = user_id
        self.personajes = personajes
        self.accion    = accion
        self.extra     = extra or {}

        options = [
            discord.SelectOption(
                label=p["personaje"],
                value=p["personaje"],
                description=p["tipo"].capitalize(),
                emoji={"estudiante":"🎓","profesor":"🧑‍🏫","trabajador":"🧑‍💼"}.get(p["tipo"],"📋")
            )
            for p in personajes
        ]
        select = discord.ui.Select(
            placeholder="🎭 Selecciona el personaje...",
            options=options, min_values=1, max_values=1)
        select.callback = self._on_select
        self.add_item(select)

    async def _on_select(self, interaction: discord.Interaction):
        personaje = interaction.data["values"][0]
        loop      = asyncio.get_event_loop()

        if self.accion == "spin":
            # Verificar que no tenga ficha aprobada
            ficha = await loop.run_in_executor(None, _get_ficha_poder,
                self.user_id, personaje)
            if ficha and ficha.get("estado","").upper() == "APROBADO":
                await interaction.response.edit_message(
                    content=(f"ℹ️ **{personaje}** ya tiene una ficha de poder aprobada.\n"
                             f"Usa `/editar-ficha-poder` para editarla o "
                             f"`/respin-personaje` si tienes el ítem de re-spin."),
                    embed=None, view=None)
                return

            spin   = _hacer_spin()
            embed  = _build_spin_embed(spin, personaje)
            view   = SpinResultView(personaje, spin, self.user_id)
            await interaction.response.edit_message(embed=embed, view=view)

        elif self.accion == "editar":
            ficha = await loop.run_in_executor(None, _get_ficha_poder,
                self.user_id, personaje)
            if not ficha or ficha.get("estado","").upper() not in ("APROBADO", "RECHAZADO"):
                await interaction.response.edit_message(
                    content=f"❌ **{personaje}** no tiene ficha de poder aprobada o en revisión aún.",
                    embed=None, view=None)
                return
            await interaction.response.send_modal(
                EditarFichaPodeModal(personaje, ficha, self.user_id))

        elif self.accion == "respin":
            # Verificar rol de re-spin
            if not any(r.id == ROL_RESPIN for r in interaction.user.roles):
                await interaction.response.edit_message(
                    content="❌ Necesitas el ítem de re-spin de la tienda para usar este comando.",
                    embed=None, view=None)
                return
            spin  = _hacer_spin()
            embed = _build_spin_embed(spin, personaje)
            embed.title = "🔄 Re-spin de Poder"
            embed.description = (
                "*Las estrellas han sido consultadas de nuevo...*\n\n"
                "⚠️ Las nuevas estadísticas pueden ser mejores o peores. "
                "Usa el botón para actualizar tu ficha con los nuevos valores."
            )
            view = SpinResultView(personaje, spin, self.user_id, es_respin=True)
            await interaction.response.edit_message(embed=embed, view=view)

        elif self.accion == "ver":
            target_id = self.extra.get("target_id", self.user_id)
            ficha = await loop.run_in_executor(None, _get_ficha_poder,
                target_id, personaje)
            if not ficha:
                await interaction.response.edit_message(
                    content=f"❌ **{personaje}** no tiene ficha de poder.",
                    embed=None, view=None)
                return
            embed = _build_ficha_embed(ficha, personaje)
            await interaction.response.edit_message(embed=embed, view=None)

        elif self.accion == "historial":
            target_id = self.extra.get("target_id", self.user_id)
            batallas  = await loop.run_in_executor(None, _get_historial_batallas,
                target_id, personaje)
            embed = _build_historial_embed(batallas, personaje)
            await interaction.response.edit_message(embed=embed, view=None)

        self.stop()


def _build_ficha_embed(ficha: dict, personaje: str) -> discord.Embed:
    nivel      = ficha.get("nivel", "bajo")
    mana       = int(ficha.get("mana", 0))
    cat_key    = ficha.get("categoria_raza", ficha.get("categoria", ""))
    cat_info   = CATEGORIAS_RAZA.get(cat_key)
    cat_display = f"{cat_info['emoji']} {cat_info['nombre']}" if cat_info else (cat_key or "Sin asignar")
    nivel_data = NIVELES_PODER.get(nivel, NIVELES_PODER["bajo"])

    embed = discord.Embed(
        title=f"✨ Ficha de Poder — {personaje}",
        color=COLOR_INFO
    )
    embed.add_field(name="🏷️ Categoría de Raza", value=cat_display,          inline=True)
    embed.add_field(name=f"{nivel_data['emoji']} Nivel", value=nivel_data["nombre"], inline=True)
    embed.add_field(name="💧 Maná",  value=f"{mana}/10",                       inline=True)
    embed.add_field(name="⚔️ Habilidades", value=ficha.get("habilidades","—"), inline=False)
    embed.add_field(name="🩹 Debilidades", value=ficha.get("debilidades","—"), inline=False)
    return embed


def _build_historial_embed(batallas: list, personaje: str) -> discord.Embed:
    if not batallas:
        return discord.Embed(
            title=f"⚔️ Historial de Batallas — {personaje}",
            description="Este personaje no ha participado en batallas aún.",
            color=COLOR_INFO
        )
    ganadas  = sum(1 for b in batallas if b.get("resultado","").upper() == "VICTORIA")
    perdidas = sum(1 for b in batallas if b.get("resultado","").upper() == "DERROTA")
    embed = discord.Embed(
        title=f"⚔️ Historial de Batallas — {personaje}",
        color=COLOR_INFO
    )
    embed.add_field(name="Total", value=str(len(batallas)), inline=True)
    embed.add_field(name="✅ Victorias", value=str(ganadas),  inline=True)
    embed.add_field(name="❌ Derrotas",  value=str(perdidas), inline=True)
    lines = []
    for b in batallas[-10:]:
        res   = "✅" if b.get("resultado","").upper() == "VICTORIA" else "❌"
        rival = b.get("rival_personaje","?")
        fecha = b.get("fecha","?")[:10]
        lines.append(f"{res} vs **{rival}** — {fecha}")
    embed.add_field(name="Últimas 10 batallas", value="\n".join(lines), inline=False)
    return embed


# ──────────────────────────────────────────────
# COG
# ──────────────────────────────────────────────

class Spins(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Batallas activas: {user_id: {"personaje": ..., "ficha": ..., "rival_id": ..., "rival_personaje": ..., "rival_ficha": ...}}
        self._batallas_activas: dict = {}

    async def _get_personajes_async(self, user_id: int):
        loop = asyncio.get_event_loop()
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(None, get_personajes_usuario, user_id),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            print(f"[SPINS] Timeout obteniendo personajes de {user_id}")
            return []
        except Exception as e:
            print(f"[SPINS] Error obteniendo personajes de {user_id}: {e}")
            return []

    # ── /spin-poder ───────────────────────────

    @app_commands.command(name="spin-poder",
        description="Genera las estadísticas de poder de uno de tus personajes.")
    async def spin_poder(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        personajes = await self._get_personajes_async(interaction.user.id)
        if not personajes:
            await interaction.followup.send(
                "❌ No tienes personajes registrados.", ephemeral=True); return

        view = SeleccionarPersonajePodeView(interaction.user.id, personajes, "spin")
        await interaction.followup.send(
            embed=discord.Embed(title="✨ Spin de Poder",
                description="Selecciona el personaje para el spin:",
                color=COLOR_PENDIENTE),
            view=view, ephemeral=True)

    # ── /editar-ficha-poder ───────────────────

    @app_commands.command(name="editar-ficha-poder",
        description="Edita la ficha de poder de un personaje aprobado.")
    async def editar_ficha_poder(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        personajes = await self._get_personajes_async(interaction.user.id)
        if not personajes:
            await interaction.followup.send("❌ No tienes personajes.", ephemeral=True); return

        view = SeleccionarPersonajePodeView(interaction.user.id, personajes, "editar")
        await interaction.followup.send(
            embed=discord.Embed(title="✏️ Editar Ficha de Poder",
                description="Selecciona el personaje a editar:",
                color=COLOR_PENDIENTE),
            view=view, ephemeral=True)

    # ── /respin-personaje ─────────────────────

    @app_commands.command(name="respin-personaje",
        description="Re-rolea las estadísticas de poder (requiere ítem de re-spin).")
    async def respin_personaje(self, interaction: discord.Interaction):
        if not any(r.id == ROL_RESPIN for r in interaction.user.roles):
            await interaction.response.send_message(
                "❌ Necesitas el ítem de re-spin de la tienda.", ephemeral=True); return

        await interaction.response.defer(ephemeral=True)
        personajes = await self._get_personajes_async(interaction.user.id)
        if not personajes:
            await interaction.followup.send("❌ No tienes personajes.", ephemeral=True); return

        view = SeleccionarPersonajePodeView(interaction.user.id, personajes, "respin")
        await interaction.followup.send(
            embed=discord.Embed(title="🔄 Re-spin de Poder",
                description=(
                    "⚠️ El re-spin **cambia todas tus estadísticas** al azar.\n"
                    "Puedes quedar mejor o peor. ¿Continuar?\n\n"
                    "Selecciona el personaje:"),
                color=COLOR_PENDIENTE),
            view=view, ephemeral=True)

    # ── /ver-ficha-poder ──────────────────────

    @app_commands.command(name="ver-ficha-poder",
        description="Ver la ficha de poder de un personaje. Comando público.")
    @app_commands.describe(usuario="(Opcional) Usuario a consultar")
    async def ver_ficha_poder(self, interaction: discord.Interaction,
                               usuario: discord.Member | None = None):
        target = usuario or interaction.user
        await interaction.response.defer(ephemeral=False)

        personajes = await self._get_personajes_async(target.id)
        if not personajes:
            await interaction.followup.send(
                f"❌ {target.display_name} no tiene personajes registrados."); return

        view = SeleccionarPersonajePodeView(
            interaction.user.id, personajes, "ver",
            extra={"target_id": target.id})
        await interaction.followup.send(
            embed=discord.Embed(
                title=f"✨ Fichas de Poder — {target.display_name}",
                description="Selecciona el personaje:",
                color=COLOR_INFO),
            view=view)

    # ── /batalla ──────────────────────────────

    @app_commands.command(name="batalla",
        description="Iniciar una batalla contra otro personaje.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(rival="El usuario rival")
    async def batalla(self, interaction: discord.Interaction, rival: discord.Member):
        if rival.id == interaction.user.id:
            await interaction.response.send_message(
                "❌ No puedes batallar contra ti mismo.", ephemeral=True); return

        await interaction.response.defer(ephemeral=True)
        personajes = await self._get_personajes_async(interaction.user.id)
        if not personajes:
            await interaction.followup.send("❌ No tienes personajes.", ephemeral=True); return

        # Verificar que el rival tiene personajes
        personajes_rival = await self._get_personajes_async(rival.id)
        if not personajes_rival:
            await interaction.followup.send(
                f"❌ {rival.display_name} no tiene personajes registrados.", ephemeral=True); return

        view = SeleccionarPersonajeBatallaView(
            user_id=interaction.user.id,
            personajes=personajes,
            rival=rival,
            personajes_rival=personajes_rival,
            bot=self.bot,
            canal_id=interaction.channel_id,
        )
        await interaction.followup.send(
            embed=discord.Embed(title="⚔️ Iniciar Batalla",
                description=f"Selecciona tu personaje para batallar contra **{rival.display_name}**:",
                color=COLOR_INFO),
            view=view, ephemeral=True)

    # ── /historial-batalla ────────────────────

    @app_commands.command(name="historial-batalla",
        description="Ver el historial de batallas de un personaje.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(usuario="(Opcional) Usuario a consultar")
    async def historial_batalla(self, interaction: discord.Interaction,
                                 usuario: discord.Member | None = None):
        target = usuario or interaction.user
        await interaction.response.defer(ephemeral=False)

        personajes = await self._get_personajes_async(target.id)
        if not personajes:
            await interaction.followup.send(
                f"❌ {target.display_name} no tiene personajes."); return

        view = SeleccionarPersonajePodeView(
            interaction.user.id, personajes, "historial",
            extra={"target_id": target.id})
        await interaction.followup.send(
            embed=discord.Embed(
                title=f"⚔️ Historial de Batallas — {target.display_name}",
                description="Selecciona el personaje:",
                color=COLOR_INFO),
            view=view)


# ──────────────────────────────────────────────
# BATALLA
# ──────────────────────────────────────────────

class SeleccionarPersonajeBatallaView(discord.ui.View):
    def __init__(self, user_id, personajes, rival, personajes_rival, bot, canal_id):
        super().__init__(timeout=120)
        self.user_id          = user_id
        self.rival            = rival
        self.personajes_rival = personajes_rival
        self.bot              = bot
        self.canal_id         = canal_id

        options = [
            discord.SelectOption(label=p["personaje"], value=p["personaje"],
                description=p["tipo"].capitalize())
            for p in personajes
        ]
        select = discord.ui.Select(
            placeholder="🎭 Tu personaje...", options=options)
        select.callback = self._on_select
        self.add_item(select)

    async def _on_select(self, interaction: discord.Interaction):
        mi_personaje = interaction.data["values"][0]
        loop = asyncio.get_event_loop()

        # Verificar fichas de poder
        mi_ficha = await loop.run_in_executor(None, _get_ficha_poder,
            self.user_id, mi_personaje)
        if not mi_ficha or mi_ficha.get("estado","").upper() != "APROBADO":
            await interaction.response.edit_message(
                content=f"❌ **{mi_personaje}** no tiene ficha de poder aprobada.",
                embed=None, view=None); return

        # Seleccionar personaje del rival
        view = SeleccionarRivalView(
            user_id=self.user_id, mi_personaje=mi_personaje,
            mi_ficha=mi_ficha, rival=self.rival,
            personajes_rival=self.personajes_rival,
            bot=self.bot, canal_id=self.canal_id)
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="⚔️ Seleccionar rival",
                description=f"Selecciona el personaje de **{self.rival.display_name}**:",
                color=COLOR_INFO),
            view=view)
        self.stop()



    # ── /tirada-batalla ───────────────────────

    @app_commands.command(name="tirada-batalla",
        description="Realizar una tirada de movimiento en una batalla activa.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def tirada_batalla(self, interaction: discord.Interaction):
        if not hasattr(self.bot, "_batallas"):
            self.bot._batallas = {}

        # Buscar batalla activa del usuario
        batalla = None
        clave   = None
        for k, v in self.bot._batallas.items():
            if v["user_id"] == interaction.user.id or v["rival_id"] == interaction.user.id:
                batalla = v
                clave   = k
                break

        if not batalla:
            await interaction.response.send_message(
                "❌ No tienes una batalla activa. Usa `/batalla` para iniciar una.",
                ephemeral=True); return

        # Determinar si es el retador o el rival
        es_retador = batalla["user_id"] == interaction.user.id
        mi_personaje  = batalla["mi_personaje"] if es_retador else batalla["rival_personaje"]
        mi_pct        = batalla["mi_pct"]        if es_retador else batalla["rival_pct"]

        # Tirada
        resultado = random.random() * 100
        gana      = resultado <= mi_pct

        if gana:
            msg = f"El movimiento fue certero, **{mi_personaje}** prevalece."
            color = COLOR_APROBADO
            emoji = "✅"
        else:
            msg = f"El movimiento no fue suficiente, **{mi_personaje}** no logra su cometido."
            color = COLOR_RECHAZADO
            emoji = "❌"

        embed = discord.Embed(
            title=f"{emoji} Tirada de Batalla",
            description=f"*{msg}*",
            color=color
        )
        embed.add_field(
            name="Probabilidad de acierto",
            value=f"**{mi_pct}%** → Resultado: **{resultado:.1f}**",
            inline=False
        )
        embed.set_footer(text=f"Tirada por {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

    # ── /terminar-batalla ─────────────────────

    @app_commands.command(name="terminar-batalla",
        description="Terminar la batalla activa y registrar el resultado.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(ganador="El personaje ganador de la batalla")
    async def terminar_batalla(self, interaction: discord.Interaction, ganador: str):
        if not hasattr(self.bot, "_batallas"):
            self.bot._batallas = {}

        batalla = None
        clave   = None
        for k, v in self.bot._batallas.items():
            if v["user_id"] == interaction.user.id or v["rival_id"] == interaction.user.id:
                batalla = v
                clave   = k
                break

        if not batalla:
            await interaction.response.send_message(
                "❌ No tienes una batalla activa.", ephemeral=True); return

        ganador = ganador.strip()
        mi_p    = batalla["mi_personaje"]
        rival_p = batalla["rival_personaje"]

        if ganador.lower() not in [mi_p.lower(), rival_p.lower()]:
            await interaction.response.send_message(
                f"❌ El ganador debe ser **{mi_p}** o **{rival_p}**.", ephemeral=True); return

        loop = asyncio.get_event_loop()
        # Registrar resultado para ambos
        if ganador.lower() == mi_p.lower():
            await loop.run_in_executor(None, _registrar_batalla,
                batalla["user_id"], mi_p, batalla["rival_id"], rival_p, "VICTORIA")
            await loop.run_in_executor(None, _registrar_batalla,
                batalla["rival_id"], rival_p, batalla["user_id"], mi_p, "DERROTA")
        else:
            await loop.run_in_executor(None, _registrar_batalla,
                batalla["user_id"], mi_p, batalla["rival_id"], rival_p, "DERROTA")
            await loop.run_in_executor(None, _registrar_batalla,
                batalla["rival_id"], rival_p, batalla["user_id"], mi_p, "VICTORIA")

        del self.bot._batallas[clave]

        embed = discord.Embed(
            title="⚔️ Batalla terminada",
            description=(
                "🏆 **" + ganador + "** ganó la batalla.\n\n"
                "El resultado ha sido registrado en el historial."
            ),
            color=COLOR_APROBADO
        )
        await interaction.response.send_message(embed=embed)



class SeleccionarRivalView(discord.ui.View):
    def __init__(self, user_id, mi_personaje, mi_ficha, rival,
                 personajes_rival, bot, canal_id):
        super().__init__(timeout=120)
        self.user_id      = user_id
        self.mi_personaje = mi_personaje
        self.mi_ficha     = mi_ficha
        self.rival        = rival
        self.bot          = bot
        self.canal_id     = canal_id

        options = [
            discord.SelectOption(label=p["personaje"], value=p["personaje"],
                description=p["tipo"].capitalize())
            for p in personajes_rival
        ]
        select = discord.ui.Select(
            placeholder=f"🎭 Personaje de {rival.display_name}...", options=options)
        select.callback = self._on_select
        self.add_item(select)

    async def _on_select(self, interaction: discord.Interaction):
        rival_personaje = interaction.data["values"][0]
        loop = asyncio.get_event_loop()

        rival_ficha = await loop.run_in_executor(None, _get_ficha_poder,
            self.rival.id, rival_personaje)
        if not rival_ficha or rival_ficha.get("estado","").upper() != "APROBADO":
            await interaction.response.edit_message(
                content=f"❌ **{rival_personaje}** no tiene ficha de poder aprobada.",
                embed=None, view=None); return

        # Calcular porcentajes
        mi_nivel    = {"bajo": 1, "medio": 2, "alto": 3}.get(self.mi_ficha.get("nivel","bajo"), 1)
        rival_nivel = {"bajo": 1, "medio": 2, "alto": 3}.get(rival_ficha.get("nivel","bajo"), 1)
        mi_mana     = int(self.mi_ficha.get("mana", 0))
        rival_mana  = int(rival_ficha.get("mana", 0))

        mi_score    = mi_nivel * 3 + mi_mana
        rival_score = rival_nivel * 3 + rival_mana
        total       = mi_score + rival_score

        if total == 0:
            mi_pct = rival_pct = 50
        else:
            mi_pct    = round((mi_score / total) * 100)
            rival_pct = 100 - mi_pct

        # Guardar batalla activa en el bot
        if not hasattr(self.bot, "_batallas"):
            self.bot._batallas = {}
        self.bot._batallas[f"{self.user_id}_{self.rival.id}"] = {
            "user_id": self.user_id, "mi_personaje": self.mi_personaje,
            "mi_pct": mi_pct, "rival_id": self.rival.id,
            "rival_personaje": rival_personaje, "rival_pct": rival_pct,
        }

        # Publicar en el canal
        canal = self.bot.get_channel(self.canal_id)
        if canal:
            embed = discord.Embed(
                title=f"⚔️ Batalla — {self.mi_personaje} vs {rival_personaje}",
                description=(
                    f"**{self.mi_personaje}** (<@{self.user_id}>) "
                    f"desafía a **{rival_personaje}** (<@{self.rival.id}>)\n\n"
                    f"Probabilidades de acierto:\n"
                    f"🔵 **{self.mi_personaje}:** {mi_pct}%\n"
                    f"🔴 **{rival_personaje}:** {rival_pct}%\n\n"
                    f"*Usa `/tirada-batalla` para cada movimiento durante el rol.*"
                ),
                color=COLOR_INFO
            )
            await canal.send(embed=embed)

        await interaction.response.edit_message(
            content="⚔️ ¡Batalla iniciada! Ve al canal para continuar.",
            embed=None, view=None)
        self.stop()

async def setup(bot):
    await bot.add_cog(Spins(bot))
