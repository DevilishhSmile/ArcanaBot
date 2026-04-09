import discord
from discord import app_commands
from discord.ext import commands
import json, os

from utils.constants import (
    GUILD_ID, ROL_STAFF, ROL_SLOT_ADICIONAL,
    COLOR_INFO, COLOR_APROBADO, COLOR_RECHAZADO, COLOR_PENDIENTE
)

GEN_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "generacion.json")

def cargar_generacion() -> int:
    try:
        with open(GEN_FILE, "r") as f:
            return json.load(f).get("generacion_actual", 1)
    except Exception:
        return 1

def guardar_generacion(gen: int):
    os.makedirs(os.path.dirname(GEN_FILE), exist_ok=True)
    with open(GEN_FILE, "w") as f:
        json.dump({"generacion_actual": gen}, f)


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _es_staff(self, i):
        return any(r.id == ROL_STAFF for r in i.user.roles)

    # ──────────────────────────────────────────────
    # /reclamar-slot
    # ──────────────────────────────────────────────

    @app_commands.command(name="reclamar-slot",
        description="Reclama tu slot adicional de personaje si tienes el rol +Slot de Personaje.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def reclamar_slot(self, interaction: discord.Interaction):
        from utils.database import agregar_slot_extra, get_conteo_usuario

        if not any(r.id == ROL_SLOT_ADICIONAL for r in interaction.user.roles):
            await interaction.response.send_message(
                "❌ No tienes el rol **+Slot de Personaje**.\n\nAdquiérelo en la tienda y vuelve a usar este comando.",
                ephemeral=True)
            return

        gen = cargar_generacion()
        await agregar_slot_extra(interaction.user.id, gen, cantidad=1)

        try:
            rol = interaction.guild.get_role(ROL_SLOT_ADICIONAL)
            if rol: await interaction.user.remove_roles(rol, reason="Slot adicional reclamado")
        except Exception as e:
            print(f"[ADMIN] Error quitando rol slot: {e}")

        conteo = await get_conteo_usuario(interaction.user.id, gen)
        disp   = conteo.get("slots_extra_disponibles", 0)

        embed = discord.Embed(title="✨ Slot adicional reclamado",
            description=(
                f"¡Tu slot adicional fue añadido!\n\n"
                f"Tienes **{disp}** slot{'s' if disp != 1 else ''} adicional{'es' if disp != 1 else ''} disponible{'s' if disp != 1 else ''}.\n\n"
                f"Se usará automáticamente cuando llegues al límite al registrar un personaje."
            ), color=COLOR_APROBADO)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ──────────────────────────────────────────────
    # /mis-personajes
    # ──────────────────────────────────────────────

    @app_commands.command(name="mis-personajes",
        description="Ver cuántos personajes tienes registrados y tus slots disponibles.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def mis_personajes(self, interaction: discord.Interaction):
        from utils.database import get_conteo_usuario
        from utils.constants import SLOTS_CONFIG
        from utils.sheets import get_personajes_usuario

        gen    = cargar_generacion()
        conteo = await get_conteo_usuario(interaction.user.id, gen)
        config = SLOTS_CONFIG.get(gen, SLOTS_CONFIG["default"])
        personajes = get_personajes_usuario(interaction.user.id)

        def barra(usado, limite):
            if limite is None: return f"**{usado}** / ∞"
            llenos = "🟩" * min(usado, limite)
            vacios = "⬜" * max(0, limite - usado)
            extras = "🟨" * max(0, usado - limite)
            return f"{llenos}{vacios}{extras} **{usado}/{limite}**"

        embed = discord.Embed(
            title=f"📋 Mis personajes — Gen {gen} (Server Gen {gen+3})",
            color=COLOR_INFO)
        embed.set_author(name=interaction.user.display_name,
                         icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="Slots base", value=(
            f"🎓 Estudiantes:   {barra(conteo.get('estudiantes_usados',0),  config.get('estudiantes',3))}\n"
            f"🧑‍🏫 Profesores:   {barra(conteo.get('profesores_usados',0),   config.get('profesores',2))}\n"
            f"🧑‍💼 Trabajadores: {barra(conteo.get('trabajadores_usados',0), config.get('trabajadores',2))}"
        ), inline=False)

        disp   = conteo.get("slots_extra_disponibles", 0)
        usados = conteo.get("slots_extra_usados", 0)
        embed.add_field(name="✨ Slots adicionales",
            value=f"Disponibles: **{disp}** | Usados: **{usados}** | Total: **{disp+usados}**",
            inline=False)
        embed.set_footer(text="Solo tú puedes ver este mensaje.")

        view = MisPersonajesView(personajes=personajes, embed_slots=embed)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    # ──────────────────────────────────────────────
    # /ver-personajes @usuario
    # ──────────────────────────────────────────────

    @app_commands.command(name="ver-personajes",
        description="[STAFF] Ver los personajes de un usuario.")
    @app_commands.describe(usuario="El usuario a consultar")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def ver_personajes(self, interaction: discord.Interaction, usuario: discord.Member):
        if not self._es_staff(interaction):
            await interaction.response.send_message("❌ Solo el staff puede.", ephemeral=True)
            return

        from utils.database import get_conteo_usuario
        from utils.constants import SLOTS_CONFIG
        from utils.sheets import get_personajes_usuario

        gen    = cargar_generacion()
        conteo = await get_conteo_usuario(usuario.id, gen)
        config = SLOTS_CONFIG.get(gen, SLOTS_CONFIG["default"])
        personajes = get_personajes_usuario(usuario.id)

        def fmt(usado, limite):
            return f"**{usado}** / {'∞' if limite is None else limite}"

        embed = discord.Embed(title=f"📋 {usuario.display_name} — Gen {gen}", color=COLOR_INFO)
        embed.set_author(name=usuario.display_name, icon_url=usuario.display_avatar.url)
        embed.add_field(name="Slots usados", value=(
            f"🎓 Estudiantes:   {fmt(conteo.get('estudiantes_usados',0),  config.get('estudiantes',3))}\n"
            f"🧑‍🏫 Profesores:   {fmt(conteo.get('profesores_usados',0),   config.get('profesores',2))}\n"
            f"🧑‍💼 Trabajadores: {fmt(conteo.get('trabajadores_usados',0), config.get('trabajadores',2))}"
        ), inline=False)
        embed.add_field(name="✨ Slots adicionales",
            value=f"Disponibles: **{conteo.get('slots_extra_disponibles',0)}** | Usados: **{conteo.get('slots_extra_usados',0)}**",
            inline=False)

        view = MisPersonajesView(personajes=personajes, embed_slots=embed)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    # ──────────────────────────────────────────────
    # /eliminar-personaje
    # ──────────────────────────────────────────────

    @app_commands.command(name="eliminar-personaje",
        description="Solicita eliminar uno de tus personajes (requiere aprobación del staff).")
    @app_commands.describe(nombre="Nombre exacto del personaje a eliminar")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def eliminar_personaje(self, interaction: discord.Interaction, nombre: str):
        from utils.sheets import get_personajes_usuario
        from utils.constants import CANAL_REVISION_FICHAS

        personajes = get_personajes_usuario(interaction.user.id)
        encontrado = next(
            (p for p in personajes if p["personaje"].strip().lower() == nombre.strip().lower()), None)

        if not encontrado:
            await interaction.response.send_message(
                f"❌ No encontré ningún personaje llamado **{nombre}** en tus registros.\n\nUsa `/mis-personajes` para ver los tuyos.",
                ephemeral=True)
            return

        # Abrir modal para pedir motivo
        await interaction.response.send_modal(
            MotivoEliminacionModal(
                personaje=encontrado["personaje"],
                tipo=encontrado["tipo"],
                detalle=encontrado["detalle"],
                user_id=interaction.user.id,
            )
        )

    # ──────────────────────────────────────────────
    # /admin-stats
    # ──────────────────────────────────────────────

    @app_commands.command(name="admin-stats",
        description="[STAFF] Ver estadísticas globales del servidor RP.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def admin_stats(self, interaction: discord.Interaction):
        if not self._es_staff(interaction):
            await interaction.response.send_message("❌ Solo el staff puede.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        from utils.sheets import get_global_stats, actualizar_global_stats
        from utils.constants import CARGOS, MATERIAS_LIMITE
        from utils.sheets import get_profesores_aprobados_por_materia, get_trabajadores_aprobados_por_cargo

        actualizar_global_stats()
        stats = get_global_stats()
        gen   = cargar_generacion()

        embed = discord.Embed(title=f"📊 Admin Stats — Gen {gen} (Server Gen {gen+3})", color=COLOR_INFO)
        embed.add_field(name="✅ Aprobados", value=(
            f"🎓 Estudiantes: **{stats.get('estudiantes_total',0)}**\n"
            f"🧑‍🏫 Profesores: **{stats.get('profesores_total',0)}**\n"
            f"🧑‍💼 Trabajadores: **{stats.get('trabajadores_total',0)}**\n"
            f"👕 Uniformes: **{stats.get('uniformes_aprobados',0)}**"
        ), inline=True)
        embed.add_field(name="⏳ Pendientes", value=(
            f"👕 Uniformes: **{stats.get('uniformes_pendientes',0)}**\n"
            f"🎓 Fichas: **{stats.get('fichas_pendientes',0)}**\n"
            f"🧑‍💼 Trabajos: **{stats.get('trabajos_pendientes',0)}**\n"
            f"📋 Total: **{stats.get('pendientes_totales',0)}**"
        ), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=False)

        cargo_lines = []
        for cargo, limite in CARGOS.items():
            cupo = limite or 1
            ocup = get_trabajadores_aprobados_por_cargo(cargo)
            estado = "✅" if ocup < cupo else "🔴"
            cargo_lines.append(f"{estado} {cargo}: **{ocup}/{cupo}**")
        embed.add_field(name="🧑‍💼 Cupos trabajadores", value="\n".join(cargo_lines), inline=False)

        mat_lines = []
        for materia, limite in MATERIAS_LIMITE.items():
            ocup = get_profesores_aprobados_por_materia(materia)
            if ocup > 0 or limite <= 1:
                estado = "✅" if ocup < limite else "🔴"
                mat_lines.append(f"{estado} {materia}: **{ocup}/{limite}**")
        if mat_lines:
            mid = len(mat_lines) // 2
            embed.add_field(name="🧑‍🏫 Cupos materias (1/2)", value="\n".join(mat_lines[:mid]) or "—", inline=False)
            embed.add_field(name="🧑‍🏫 Cupos materias (2/2)", value="\n".join(mat_lines[mid:]) or "—", inline=False)

        embed.set_footer(text="Stats actualizados al momento de ejecutar el comando.")
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ──────────────────────────────────────────────
    # /panel-uniformes
    # ──────────────────────────────────────────────

    @app_commands.command(name="panel-uniformes",
        description="[STAFF] Ver y gestionar uniformes pendientes de revisión.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def panel_uniformes(self, interaction: discord.Interaction):
        if not self._es_staff(interaction):
            await interaction.response.send_message("❌ Solo el staff puede.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        from utils.sheets import get_uniformes_pendientes

        pendientes = get_uniformes_pendientes()
        if not pendientes:
            await interaction.followup.send("✅ No hay uniformes pendientes.", ephemeral=True)
            return

        # Mostrar el primer uniforme con botones de navegación
        view = PanelUniformesView(pendientes=pendientes, indice=0)
        embed = view.build_embed()
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    # ──────────────────────────────────────────────
    # /generacion
    # ──────────────────────────────────────────────

    gen_group = app_commands.Group(
        name="generacion", description="Gestión de generaciones.", guild_ids=[GUILD_ID])

    @gen_group.command(name="ver", description="Muestra la generación activa y sus slots.")
    async def gen_ver(self, interaction: discord.Interaction):
        from utils.constants import SLOTS_CONFIG
        gen    = cargar_generacion()
        config = SLOTS_CONFIG.get(gen, SLOTS_CONFIG["default"])
        embed  = discord.Embed(title="📚 Generación actual", color=COLOR_INFO)
        embed.add_field(name="Generación bot",    value=f"**Gen {gen}**",   inline=True)
        embed.add_field(name="Generación server", value=f"**Gen {gen+3}**", inline=True)
        embed.add_field(name="🎰 Slots por usuario", value=(
            f"🎓 Estudiantes: **{config.get('estudiantes',3)}**\n"
            f"🧑‍🏫 Profesores: **{config.get('profesores',2) or 'Sin límite'}**\n"
            f"🧑‍💼 Trabajadores: **{config.get('trabajadores',2) or 'Sin límite'}**"
        ), inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @gen_group.command(name="cambiar", description="[STAFF] Avanza a la siguiente generación.")
    async def gen_cambiar(self, interaction: discord.Interaction):
        if not self._es_staff(interaction):
            await interaction.response.send_message("❌ Solo el staff puede.", ephemeral=True)
            return
        gen_actual = cargar_generacion()
        gen_nueva  = gen_actual + 1
        from utils.constants import SLOTS_CONFIG
        c = SLOTS_CONFIG.get(gen_nueva, SLOTS_CONFIG["default"])
        embed = discord.Embed(title="⚠️ Confirmar cambio de generación", color=0xF0C040,
            description=(f"**Gen {gen_actual}** → **Gen {gen_nueva}** (Server Gen {gen_nueva+3})\n\n"
                f"Nuevos slots: 🎓 **{c.get('estudiantes',3)}** | 🧑‍🏫 **{c.get('profesores',2) or '∞'}** | 🧑‍💼 **{c.get('trabajadores',2) or '∞'}**\n\n⚠️ No se puede deshacer."))
        await interaction.response.send_message(
            embed=embed, view=ConfirmarCambioGenView(gen_actual, gen_nueva), ephemeral=True)

    @gen_group.command(name="historial", description="[STAFF] Ver personajes de una generación.")
    @app_commands.describe(numero="Número de generación del bot (Gen 1 = Server Gen 4)")
    async def gen_historial(self, interaction: discord.Interaction, numero: int):
        if not self._es_staff(interaction):
            await interaction.response.send_message("❌ Solo el staff puede.", ephemeral=True)
            return
        from utils.sheets import get_all_rows
        try:
            est  = [r for r in get_all_rows("EstudiantesAprobados") if str(r.get("generacion","")) == str(numero)]
            prof = [r for r in get_all_rows("Profesores") if str(r.get("generacion","")) == str(numero) and r.get("estado","").upper() == "APROBADO"]
            trab = [r for r in get_all_rows("Trabajadores") if str(r.get("generacion","")) == str(numero) and r.get("estado","").upper() == "APROBADO"]
        except Exception as e:
            await interaction.response.send_message(f"❌ Error Sheets: {e}", ephemeral=True)
            return
        embed = discord.Embed(title=f"📚 Gen {numero} (Server Gen {numero+3})", color=COLOR_INFO)
        embed.add_field(name="🎓", value=str(len(est)),  inline=True)
        embed.add_field(name="🧑‍🏫", value=str(len(prof)), inline=True)
        embed.add_field(name="🧑‍💼", value=str(len(trab)), inline=True)
        if est:  embed.add_field(name="Estudiantes",  value="\n".join(f"• {r.get('personaje','?')}" for r in est[:10]),  inline=False)
        if prof: embed.add_field(name="Profesores",   value="\n".join(f"• {r.get('personaje','?')} — {r.get('materia','?')}" for r in prof[:10]), inline=False)
        if trab: embed.add_field(name="Trabajadores", value="\n".join(f"• {r.get('personaje','?')} — {r.get('cargo','?')}" for r in trab[:10]), inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ──────────────────────────────────────────────
# MODAL — Motivo de eliminación de personaje
# ──────────────────────────────────────────────

class MotivoEliminacionModal(discord.ui.Modal, title="🗑️ Solicitud de eliminación"):
    motivo = discord.ui.TextInput(
        label="Motivo (opcional)",
        style=discord.TextStyle.paragraph,
        placeholder="¿Por qué quieres eliminar este personaje?",
        required=False,
        max_length=500,
    )

    def __init__(self, personaje: str, tipo: str, detalle: str, user_id: int):
        super().__init__()
        self.personaje = personaje
        self.tipo      = tipo
        self.detalle   = detalle
        self.user_id   = user_id

    async def on_submit(self, interaction: discord.Interaction):
        from utils.constants import CANAL_REVISION_FICHAS

        motivo_texto = self.motivo.value.strip() if self.motivo.value else "Sin motivo especificado."

        await interaction.response.send_message(
            f"📨 Tu solicitud de eliminación para **{self.personaje}** fue enviada al staff.\n"
            f"Recibirás una notificación cuando sea procesada.",
            ephemeral=True)

        canal_staff = interaction.client.get_channel(CANAL_REVISION_FICHAS)
        if not canal_staff: return

        embed = discord.Embed(title="🗑️ Solicitud de eliminación de personaje",
            description=(
                f"**Usuario:** <@{self.user_id}>\n"
                f"**Personaje:** {self.personaje}\n"
                f"**Tipo:** {self.tipo.capitalize()}\n"
                f"**Detalle:** {self.detalle}\n\n"
                f"**Motivo del usuario:**\n{motivo_texto}"
            ), color=COLOR_PENDIENTE)
        embed.set_footer(text=f"Solicitado por {interaction.user.display_name}")
        await canal_staff.send(embed=embed,
            view=EliminarPersonajeView(user_id=self.user_id, personaje=self.personaje, tipo=self.tipo))


# ──────────────────────────────────────────────
# VIEW — Panel de uniformes pendientes con navegación
# ──────────────────────────────────────────────

class PanelUniformesView(discord.ui.View):
    def __init__(self, pendientes: list, indice: int):
        super().__init__(timeout=300)
        self.pendientes = pendientes
        self.indice     = indice
        self._update_buttons()

    def _update_buttons(self):
        # Activar/desactivar botones según posición
        self.anterior.disabled = self.indice == 0
        self.siguiente.disabled = self.indice >= len(self.pendientes) - 1

    def build_embed(self) -> discord.Embed:
        u   = self.pendientes[self.indice]
        total = len(self.pendientes)
        embed = discord.Embed(
            title=f"👕 Uniforme pendiente ({self.indice+1}/{total})",
            color=COLOR_PENDIENTE)
        embed.add_field(name="Personaje", value=u.get("personaje","?"), inline=True)
        embed.add_field(name="Usuario",   value=f"<@{u.get('user_id','?')}> (`{u.get('username','?')}`)", inline=True)
        embed.add_field(name="Fecha",     value=u.get("fecha","?"), inline=False)
        if u.get("link_imagen"):
            embed.set_image(url=u["link_imagen"])
        return embed

    @discord.ui.button(label="◀ Anterior", style=discord.ButtonStyle.secondary)
    async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.indice = max(0, self.indice - 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Siguiente ▶", style=discord.ButtonStyle.secondary)
    async def siguiente(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.indice = min(len(self.pendientes) - 1, self.indice + 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="✅ Aprobar este", style=discord.ButtonStyle.success, row=1)
    async def aprobar(self, interaction: discord.Interaction, button: discord.ui.Button):
        from utils.sheets import aprobar_uniforme
        from utils.constants import CANAL_ENVIAR_UNIFORME

        u = self.pendientes[self.indice]
        try:
            aprobar_uniforme(u.get("user_id"), u.get("personaje",""), u.get("link_imagen",""), str(interaction.user))
        except Exception as e:
            print(f"[PANEL_UNIFORMES] Error Sheets: {e}")

        # Notificar al usuario
        canal = interaction.client.get_channel(CANAL_ENVIAR_UNIFORME)
        embed_user = discord.Embed(title="✅ Uniforme aprobado",
            description=f"¡Felicidades <@{u.get('user_id')}>! Tu uniforme para **{u.get('personaje','')}** fue aprobado. 🎉\n\nYa puedes registrar tu ficha.",
            color=COLOR_APROBADO)
        if u.get("link_imagen"): embed_user.set_image(url=u["link_imagen"])
        if canal: await canal.send(embed=embed_user)

        # Quitar de la lista y avanzar
        self.pendientes.pop(self.indice)
        if not self.pendientes:
            await interaction.response.edit_message(
                content="✅ Todos los uniformes han sido procesados.", embed=None, view=None)
            return
        self.indice = min(self.indice, len(self.pendientes) - 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="❌ Rechazar este", style=discord.ButtonStyle.danger, row=1)
    async def rechazar(self, interaction: discord.Interaction, button: discord.ui.Button):
        u = self.pendientes[self.indice]
        await interaction.response.send_modal(
            RechazoUniformePanelModal(uniforme=u, pendientes=self.pendientes,
                                      indice=self.indice, panel_view=self))

    @discord.ui.button(label="⏭ Terminar revisión", style=discord.ButtonStyle.secondary, row=1)
    async def terminar(self, interaction: discord.Interaction, button: discord.ui.Button):
        restantes = len(self.pendientes)
        await interaction.response.edit_message(
            content=f"✅ Revisión terminada. Quedan **{restantes}** uniforme{'s' if restantes != 1 else ''} pendiente{'s' if restantes != 1 else ''} en la cola.",
            embed=None, view=None)


class RechazoUniformePanelModal(discord.ui.Modal, title="✏️ Motivo de rechazo"):
    motivo = discord.ui.TextInput(
        label="¿Por qué se rechaza?",
        style=discord.TextStyle.paragraph,
        placeholder="Explica el motivo al usuario...",
        required=False, max_length=500)

    def __init__(self, uniforme: dict, pendientes: list, indice: int, panel_view):
        super().__init__()
        self.uniforme   = uniforme
        self.pendientes = pendientes
        self.indice     = indice
        self.panel_view = panel_view

    async def on_submit(self, interaction: discord.Interaction):
        from utils.sheets import rechazar_uniforme
        from utils.constants import CANAL_ENVIAR_UNIFORME

        m = self.motivo.value.strip() if self.motivo.value else "Sin motivo especificado."
        u = self.uniforme

        try:
            rechazar_uniforme(u.get("user_id"), u.get("personaje",""), str(interaction.user), m)
        except Exception as e:
            print(f"[PANEL_UNIFORMES] Error rechazar: {e}")

        canal = interaction.client.get_channel(CANAL_ENVIAR_UNIFORME)
        embed_user = discord.Embed(title="❌ Uniforme rechazado",
            description=f"Hola <@{u.get('user_id')}>, tu uniforme para **{u.get('personaje','')}** fue rechazado.\n\n**Motivo:**\n{m}\n\nCorrígelo con `/uniforme`. 💪",
            color=COLOR_RECHAZADO)
        if u.get("link_imagen"): embed_user.set_image(url=u["link_imagen"])
        if canal: await canal.send(embed=embed_user)

        # Quitar de la lista
        self.pendientes.pop(self.indice)
        if not self.pendientes:
            await interaction.response.edit_message(
                content="✅ Todos los uniformes han sido procesados.", embed=None, view=None)
            return
        self.panel_view.indice = min(self.indice, len(self.pendientes) - 1)
        self.panel_view._update_buttons()
        await interaction.response.edit_message(embed=self.panel_view.build_embed(), view=self.panel_view)


# ──────────────────────────────────────────────
# VIEW — Panel de personajes con navegación (slide)
# ──────────────────────────────────────────────

class MisPersonajesView(discord.ui.View):
    def __init__(self, personajes: list, embed_slots: discord.Embed):
        super().__init__(timeout=120)
        self.personajes  = personajes
        self.embed_slots = embed_slots
        self.indice      = 0
        self.mostrando_personajes = False

        if not personajes:
            self.ver_personajes.disabled = True

    def build_personaje_embed(self) -> discord.Embed:
        if not self.personajes:
            return discord.Embed(title="Sin personajes", description="No tienes personajes registrados.", color=COLOR_INFO)
        p     = self.personajes[self.indice]
        total = len(self.personajes)
        iconos = {"estudiante": "🎓", "profesor": "🧑‍🏫", "trabajador": "🧑‍💼"}
        embed = discord.Embed(
            title=f"{iconos.get(p['tipo'],'📋')} {p['personaje']} ({self.indice+1}/{total})",
            color=COLOR_INFO)
        embed.add_field(name="Tipo",   value=p["tipo"].capitalize(), inline=True)
        embed.add_field(name="Detalle",value=p["detalle"],            inline=True)
        return embed

    @discord.ui.button(label="👁 Ver personajes", style=discord.ButtonStyle.primary)
    async def ver_personajes(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.mostrando_personajes = True
        self.indice = 0
        self.ver_personajes.disabled  = True
        self.volver_slots.disabled    = False
        self.anterior.disabled        = True
        self.siguiente.disabled       = len(self.personajes) <= 1
        await interaction.response.edit_message(embed=self.build_personaje_embed(), view=self)

    @discord.ui.button(label="↩ Volver a slots", style=discord.ButtonStyle.secondary, disabled=True)
    async def volver_slots(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.mostrando_personajes = False
        self.ver_personajes.disabled = False
        self.volver_slots.disabled   = True
        self.anterior.disabled       = True
        self.siguiente.disabled      = True
        await interaction.response.edit_message(embed=self.embed_slots, view=self)

    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary, disabled=True, row=1)
    async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.indice = max(0, self.indice - 1)
        self.anterior.disabled  = self.indice == 0
        self.siguiente.disabled = self.indice >= len(self.personajes) - 1
        await interaction.response.edit_message(embed=self.build_personaje_embed(), view=self)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary, disabled=True, row=1)
    async def siguiente(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.indice = min(len(self.personajes) - 1, self.indice + 1)
        self.anterior.disabled  = self.indice == 0
        self.siguiente.disabled = self.indice >= len(self.personajes) - 1
        await interaction.response.edit_message(embed=self.build_personaje_embed(), view=self)


# ──────────────────────────────────────────────
# VIEW — Confirmar eliminación (staff)
# ──────────────────────────────────────────────

class EliminarPersonajeView(discord.ui.View):
    def __init__(self, user_id: int, personaje: str, tipo: str):
        super().__init__(timeout=None)
        self.user_id   = user_id
        self.personaje = personaje
        self.tipo      = tipo

    @discord.ui.button(label="✅ Aprobar eliminación", style=discord.ButtonStyle.danger)
    async def aprobar(self, interaction: discord.Interaction, button: discord.ui.Button):
        from utils.sheets import eliminar_personaje_sheets
        from utils.database import restar_personaje

        eliminado = eliminar_personaje_sheets(self.user_id, self.personaje, self.tipo)
        gen = cargar_generacion()
        try:
            await restar_personaje(self.user_id, f"{self.tipo}s", gen)
        except Exception as e:
            print(f"[ADMIN] Error restando slot: {e}")

        try:
            usuario = interaction.guild.get_member(self.user_id) or await interaction.guild.fetch_member(self.user_id)
            if usuario:
                embed_u = discord.Embed(title="🗑️ Personaje eliminado",
                    description=f"Tu personaje **{self.personaje}** fue eliminado. Tu slot fue liberado.",
                    color=COLOR_INFO)
                try: await usuario.send(embed=embed_u)
                except Exception: pass
        except Exception: pass

        updated = discord.Embed(title="🗑️ Eliminación aprobada",
            description=(f"**Personaje:** {self.personaje}\n**Usuario:** <@{self.user_id}>\n"
                f"{'✅ Eliminado de Sheets.' if eliminado else '⚠️ No encontrado en Sheets.'}"),
            color=COLOR_APROBADO)
        updated.set_footer(text=f"Aprobado por {interaction.user.display_name}")
        await interaction.message.edit(embed=updated, view=None)
        await interaction.response.send_message("✅ Eliminación procesada.", ephemeral=True)

    @discord.ui.button(label="❌ Rechazar solicitud", style=discord.ButtonStyle.secondary)
    async def rechazar(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            usuario = interaction.guild.get_member(self.user_id) or await interaction.guild.fetch_member(self.user_id)
            if usuario:
                embed_u = discord.Embed(title="❌ Solicitud rechazada",
                    description=f"Tu solicitud para eliminar **{self.personaje}** fue rechazada.",
                    color=COLOR_RECHAZADO)
                try: await usuario.send(embed=embed_u)
                except Exception: pass
        except Exception: pass
        updated = discord.Embed(title="🗑️ Solicitud rechazada",
            description=f"**Personaje:** {self.personaje}\n**Usuario:** <@{self.user_id}>",
            color=COLOR_RECHAZADO)
        updated.set_footer(text=f"Rechazado por {interaction.user.display_name}")
        await interaction.message.edit(embed=updated, view=None)
        await interaction.response.send_message("✅ Rechazado.", ephemeral=True)


# ──────────────────────────────────────────────
# VIEW — Confirmar cambio de generación
# ──────────────────────────────────────────────

class ConfirmarCambioGenView(discord.ui.View):
    def __init__(self, gen_actual, gen_nueva):
        super().__init__(timeout=60)
        self.gen_actual = gen_actual
        self.gen_nueva  = gen_nueva

    @discord.ui.button(label="✅ Confirmar", style=discord.ButtonStyle.danger)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        guardar_generacion(self.gen_nueva)
        import utils.constants as const
        const.GENERACION_ACTUAL = self.gen_nueva
        await interaction.response.edit_message(
            embed=discord.Embed(title="✅ Generación actualizada",
                description=f"Ahora en **Gen {self.gen_nueva}** (Server Gen {self.gen_nueva+3}).",
                color=COLOR_APROBADO), view=None)
        self.stop()

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Cancelado.", embed=None, view=None)
        self.stop()


async def setup(bot):
    await bot.add_cog(Admin(bot))
