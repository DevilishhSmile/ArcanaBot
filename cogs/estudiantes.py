import discord
from discord import app_commands
from discord.ext import commands

from utils.constants import (
    GUILD_ID, CANAL_REGISTRAR_ESTUDIANTE, CANAL_CARTA_ACEPTACION,
    CANAL_FICHAS_ESTUDIANTES, ROL_STAFF, ROL_ESTUDIANTE, ROL_REGISTRADO,
    get_slots_config, COLOR_PENDIENTE, COLOR_APROBADO, COLOR_RECHAZADO, CLUBES, CASAS,
)
from utils.helpers import (
    is_valid_character_name, clean_field, default_if_empty,
    build_review_embed, build_acceptance_embed,
    publicar_ficha_con_imagenes, validar_edad_estudiante,
)
from utils.sheets import has_approved_uniform, aprobar_estudiante, rechazar_estudiante
from utils.database import puede_registrar, registrar_personaje, usar_slot_extra, get_conteo_usuario
from utils.image_handler import registrar_espera
from cogs.admin import cargar_generacion


# ── MODAL PARTE 1 — Datos básicos ─────────────

class EstudianteModal1(discord.ui.Modal, title="🎓 Ficha de Estudiante — Parte 1/3"):
    personaje = discord.ui.TextInput(label="Nombre del personaje", placeholder="Ej: Lysander Vael", min_length=2, max_length=50)
    edad      = discord.ui.TextInput(label="Edad (máximo 18 años)", placeholder="Máximo 18 — los estudiantes son menores de edad", min_length=1, max_length=3)
    pronouns  = discord.ui.TextInput(label="Pronombres", placeholder="Ej: él/sus, ella/sus, elle/sus", min_length=2, max_length=30)
    especie   = discord.ui.TextInput(label="Especie", placeholder="Ej: Humano, Élfico, Híbrido...", min_length=2, max_length=50)
    elemento  = discord.ui.TextInput(label="Elemento mágico", placeholder="Ej: Fuego, Agua, Sombra...", min_length=2, max_length=50)

    async def on_submit(self, interaction: discord.Interaction):
        nombre = self.personaje.value.strip()
        if not is_valid_character_name(nombre):
            await interaction.response.send_message("❌ Nombre no válido. Solo letras, espacios y guiones.", ephemeral=True)
            return

        valida, msg = validar_edad_estudiante(self.edad.value)
        if not valida:
            await interaction.response.send_message(msg, ephemeral=True)
            return

        if not has_approved_uniform(interaction.user.id, nombre):
            await interaction.response.send_message(f"❌ **{nombre}** no tiene uniforme aprobado. Usa `/uniforme` primero.", ephemeral=True)
            return

        gen    = cargar_generacion()
        config = get_slots_config()
        res    = await puede_registrar(interaction.user.id, "estudiantes", gen, config.get("estudiantes"))

        if not res["puede"]:
            if res["tiene_slot_extra"]:
                _guardar_temp(interaction.client, interaction.user.id, {
                    "personaje": clean_field(nombre), "edad": clean_field(self.edad.value),
                    "pronouns": clean_field(self.pronouns.value), "especie": clean_field(self.especie.value),
                    "elemento": clean_field(self.elemento.value), "usar_slot_extra": True,
                })
                await interaction.response.send_message(
                    f"⚠️ Límite de estudiantes ({config.get('estudiantes')}). ✨ Tienes slot adicional. ¿Usarlo para **{nombre}**?",
                    view=ConfirmarSlotView(interaction.user.id), ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ {res['razon']}", ephemeral=True)
            return

        _guardar_temp(interaction.client, interaction.user.id, {
            "personaje": clean_field(nombre), "edad": clean_field(self.edad.value),
            "pronouns": clean_field(self.pronouns.value), "especie": clean_field(self.especie.value),
            "elemento": clean_field(self.elemento.value), "usar_slot_extra": False,
            "casa": "",
        })
        # Si no hay casas configuradas, saltar directo a la parte 2
        if not CASAS:
            await interaction.response.send_message(
                "✅ **Parte 1 recibida.**\n\nPresiona para continuar con poderes y personalidad.",
                view=ContinuarModal2View(interaction.user.id), ephemeral=True)
        else:
            await interaction.response.send_message(
                "✅ **Parte 1 recibida.**\n\n🏠 Selecciona la **casa** de tu personaje:",
                view=CasaSelectEstudianteView(interaction.user.id), ephemeral=True)


# ── MODAL PARTE 2 — Poderes, personalidad e historia ──

class EstudianteModal2(discord.ui.Modal, title="🎓 Ficha de Estudiante — Parte 2/3"):
    habilidades  = discord.ui.TextInput(
        label="Poderes / Habilidades",
        style=discord.TextStyle.paragraph,
        placeholder="Salud, estado físico, habilidades mágicas y especiales...",
        min_length=10, max_length=800,
    )
    debilidades  = discord.ui.TextInput(
        label="Debilidades",
        style=discord.TextStyle.paragraph,
        placeholder="Vulnerabilidades, limitaciones, miedos que lo afecten en combate...",
        min_length=10, max_length=800,
    )
    personalidad = discord.ui.TextInput(
        label="Personalidad",
        style=discord.TextStyle.paragraph,
        placeholder="Sanidad, inteligencia, rasgos de carácter, cómo se comporta...",
        min_length=10, max_length=800,
    )
    historia     = discord.ui.TextInput(
        label="Historia",
        style=discord.TextStyle.paragraph,
        placeholder="Trasfondo y origen del personaje, eventos importantes de su vida...",
        min_length=20, max_length=1500,
    )

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        datos1 = _obtener_temp(interaction.client, self.user_id)
        if not datos1:
            await interaction.response.send_message("❌ Sesión expirada. Usa `/ficha-estudiante` de nuevo.", ephemeral=True)
            return

        datos2 = {
            **datos1,
            "habilidades":  clean_field(self.habilidades.value),
            "debilidades":  clean_field(self.debilidades.value),
            "personalidad": clean_field(self.personalidad.value),
            "historia":     clean_field(self.historia.value),
        }
        _guardar_temp(interaction.client, self.user_id, datos2)

        await interaction.response.send_message(
            "✅ **Parte 2 recibida.** Ahora ingresa hobbies, gustos y disgustos.",
            view=ContinuarModal3View(self.user_id), ephemeral=True)


# ── MODAL PARTE 3 — Hobbies, gustos, disgustos (campos separados) ──

class EstudianteModal3(discord.ui.Modal, title="🎓 Ficha de Estudiante — Parte 3/3"):
    hobbies = discord.ui.TextInput(
        label="Hobbies",
        style=discord.TextStyle.paragraph,
        placeholder="¿Qué le gusta hacer en su tiempo libre? (actividades, pasatiempos...)",
        required=False,
        max_length=300,
    )
    gustos = discord.ui.TextInput(
        label="Gustos",
        style=discord.TextStyle.paragraph,
        placeholder="¿Qué cosas le agradan, le gustan o disfruta? (comida, lugares, personas...)",
        required=False,
        max_length=300,
    )
    disgustos = discord.ui.TextInput(
        label="Disgustos",
        style=discord.TextStyle.paragraph,
        placeholder="¿Qué cosas le desagradan o no soporta?",
        required=False,
        max_length=300,
    )

    def __init__(self, user_id: int, canal_id: int):
        super().__init__()
        self.user_id  = user_id
        self.canal_id = canal_id

    async def on_submit(self, interaction: discord.Interaction):
        datos = _obtener_temp(interaction.client, self.user_id)
        if not datos:
            await interaction.response.send_message("❌ Sesión expirada. Usa `/ficha-estudiante` de nuevo.", ephemeral=True)
            return

        datos["hobbies"]   = default_if_empty(self.hobbies.value)
        datos["gustos"]    = default_if_empty(self.gustos.value)
        datos["disgustos"] = default_if_empty(self.disgustos.value)
        datos["user_id"]   = interaction.user.id
        datos["username"]  = str(interaction.user)
        datos["clubes_nombres"] = datos.get("clubes_nombres", [])
        datos["clubes_ids"]     = datos.get("clubes_ids", [])
        datos["imagen"]         = ""
        datos["_tipo"]          = "estudiante"
        _guardar_temp(interaction.client, self.user_id, datos)

        # Si no hay clubes configurados, saltar directo a la imagen
        if not CLUBES:
            datos["clubes_nombres"] = []
            datos["clubes_ids"]     = []
            _guardar_temp(interaction.client, self.user_id, datos)
            registrar_espera(interaction.user.id, "estudiante", self.canal_id, datos)
            await interaction.response.edit_message(
                content=(
                    "✅ **Parte 3 recibida.**\n\n"
                    "📎 Último paso — **envía la(s) imagen(es) de tu personaje en este canal**.\n"
                    "Pégala 📋 o adjúntala desde tu galería 🖼️\n\n"
                    "🪪 **La primera imagen que adjuntes** será usada automáticamente "
                    "para generar tu **ID de estudiante** al ser aprobado.\n"
                    "Las demás también aparecerán en tu ficha con normalidad.\n\n"
                    "*Escribe `sin imagen` si no tienes una.*"
                ),
                view=None)
        else:
            # Ir al selector de clubes
            await interaction.response.send_message(
                "✅ **Parte 3 recibida.**\n\n🎭 Selecciona el/los club(es) de tu personaje.",
                view=ClubesSelectView(self.user_id, self.canal_id), ephemeral=True)


# ── SELECT CLUBES ─────────────────────────────

class ClubesSelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=n, value=n) for n in CLUBES.keys()]
        super().__init__(placeholder="🎭 Selecciona uno o varios clubes...",
                         min_values=0, max_values=len(CLUBES), options=options)

    async def callback(self, interaction: discord.Interaction):
        self.view.clubes_seleccionados = self.values
        await interaction.response.defer()


class ClubesSelectView(discord.ui.View):
    def __init__(self, user_id, canal_id):
        super().__init__(timeout=300)
        self.user_id  = user_id
        self.canal_id = canal_id
        self.clubes_seleccionados = []
        self.add_item(ClubesSelect())

    @discord.ui.button(label="✅ Confirmar selección", style=discord.ButtonStyle.success, row=1)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._procesar(interaction, self.clubes_seleccionados)

    @discord.ui.button(label="Sin club", style=discord.ButtonStyle.secondary, row=1)
    async def sin_club(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._procesar(interaction, [])

    async def _procesar(self, interaction, clubes):
        data = _obtener_temp(interaction.client, self.user_id)
        if not data:
            await interaction.response.send_message("❌ Sesión expirada.", ephemeral=True)
            return
        data["clubes_nombres"] = clubes
        data["clubes_ids"]     = [CLUBES[c] for c in clubes if c in CLUBES]
        _guardar_temp(interaction.client, self.user_id, data)
        registrar_espera(interaction.user.id, "estudiante", self.canal_id, data)
        clubs_txt = ", ".join(clubes) if clubes else "Ninguno"
        await interaction.response.edit_message(
            content=(
                f"✅ **Clubes:** {clubs_txt}\n\n"
                f"📎 Último paso — **envía la(s) imagen(es) de tu personaje en este canal**.\n"
                f"Pégala 📋 o adjúntala desde tu galería 🖼️\n\n"
                f"🪪 **La primera imagen que adjuntes** será usada automáticamente "
                f"para generar tu **ID de estudiante** al ser aprobado.\n"
                f"Las demás también aparecerán en tu ficha con normalidad.\n\n"
                f"*Escribe `sin imagen` si no tienes una.*"
            ),
            view=None)
        self.stop()


# ── VIEWS ─────────────────────────────────────


class CasaSelectEstudianteView(discord.ui.View):
    """Selector de casa — aparece después de la parte 1."""
    def __init__(self, user_id):
        super().__init__(timeout=300)
        self.user_id = user_id
        select = discord.ui.Select(
            placeholder="🏠 Selecciona la casa del personaje...",
            options=[discord.SelectOption(label=c, value=c, emoji="🏠") for c in CASAS],
            min_values=1, max_values=1,
        )
        select.callback = self._on_select
        self.add_item(select)

    async def _on_select(self, interaction: discord.Interaction):
        datos = _obtener_temp(interaction.client, self.user_id)
        if datos:
            datos["casa"] = interaction.data["values"][0]
            _guardar_temp(interaction.client, self.user_id, datos)
        await interaction.response.edit_message(
            content="✅ **Casa:** " + interaction.data["values"][0] + "\n\nPresiona para continuar con poderes y personalidad.",
            view=ContinuarModal2View(self.user_id),
        )
        self.stop()


class ContinuarModal2View(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=300)
        self.user_id = user_id

    @discord.ui.button(label="📝 Continuar — Parte 2", style=discord.ButtonStyle.primary)
    async def continuar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EstudianteModal2(self.user_id))
        self.stop()


class ContinuarModal3View(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=300)
        self.user_id = user_id

    @discord.ui.button(label="📝 Continuar — Parte 3", style=discord.ButtonStyle.primary)
    async def continuar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            EstudianteModal3(user_id=self.user_id, canal_id=interaction.channel_id))
        self.stop()


class ConfirmarSlotView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=120)
        self.user_id = user_id

    @discord.ui.button(label="✨ Sí, usar slot adicional", style=discord.ButtonStyle.success)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="✅ Slot reservado.", view=ContinuarModal2View(self.user_id))
        self.stop()

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        _limpiar_temp(interaction.client, self.user_id)
        await interaction.response.edit_message(content="Cancelado.", view=None)
        self.stop()


# ── REVIEW ────────────────────────────────────

class EstudianteReviewView(discord.ui.View):
    def __init__(self, data):
        super().__init__(timeout=None)
        self.data = data

    def _es_staff(self, i):
        return any(r.id == ROL_STAFF for r in i.user.roles)

    @discord.ui.button(label="✅ Aprobar", style=discord.ButtonStyle.success, custom_id="estudiante_aprobar")
    async def aprobar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._es_staff(interaction):
            await interaction.response.send_message("❌ Solo el staff puede.", ephemeral=True)
            return
        user_id = self.data["user_id"]
        gen     = cargar_generacion()
        try:
            if self.data.get("usar_slot_extra"): await usar_slot_extra(user_id, "estudiantes", gen)
            else: await registrar_personaje(user_id, "estudiantes", gen)
        except Exception as e: print(f"[ESTUDIANTES] DB: {e}")
        try: aprobar_estudiante(self.data, gen, str(interaction.user))
        except Exception as e: print(f"[ESTUDIANTES] Sheets: {e}")
        try:
            guild  = interaction.guild
            member = guild.get_member(user_id) or await guild.fetch_member(user_id)
            # Rol de estudiante
            rol = guild.get_role(ROL_ESTUDIANTE)
            if rol and member and rol not in member.roles:
                await member.add_roles(rol, reason="Ficha aprobada")
            # Rol registrado (primera ficha)
            rol_reg = guild.get_role(ROL_REGISTRADO)
            if rol_reg and member and rol_reg not in member.roles:
                await member.add_roles(rol_reg, reason="Primera ficha aprobada")
            # Roles de clubes
            for club_id in self.data.get("clubes_ids", []):
                r = guild.get_role(club_id)
                if r and member and r not in member.roles:
                    await member.add_roles(r, reason="Club asignado")
        except Exception as e: print(f"[ESTUDIANTES] Roles: {e}")

        canal = interaction.client.get_channel(CANAL_FICHAS_ESTUDIANTES)
        if canal:
            await publicar_ficha_con_imagenes(canal, "", self.data)

        canal_carta = interaction.client.get_channel(CANAL_CARTA_ACEPTACION)
        if canal_carta:
            conteo = await get_conteo_usuario(user_id, gen)
            carta_embed = build_acceptance_embed("estudiante", self.data["personaje"], user_id, conteo, gen)

            # Generar ID automáticamente con la primera imagen de la ficha
            try:
                from bot import _generar_id_al_aprobar
                archivo_id, codigo_id = await _generar_id_al_aprobar(
                    interaction.guild, user_id, self.data)
                if archivo_id:
                    carta_embed.add_field(
                        name="🪪 Tu ID de estudiante",
                        value="Código: `" + str(codigo_id) + "`\nGuárdalo — es tu identificación oficial en Isefora.",
                        inline=False)
                    await canal_carta.send(embed=carta_embed, file=archivo_id)
                else:
                    await canal_carta.send(embed=carta_embed)
            except Exception as e:
                print(f"[ESTUDIANTES] Error generando ID: {e}")
                await canal_carta.send(embed=carta_embed)

        updated = discord.Embed(title="🎓 Ficha Estudiante — APROBADA ✅",
            description=f"**Personaje:** {self.data['personaje']}\n**Usuario:** <@{user_id}>", color=COLOR_APROBADO)
        updated.set_footer(text=f"Aprobado por {interaction.user.display_name}")
        await interaction.message.edit(embed=updated, view=None)
        await interaction.response.send_message("✅ Aprobado.", ephemeral=True)

    @discord.ui.button(label="❌ Rechazar", style=discord.ButtonStyle.danger, custom_id="estudiante_rechazar")
    async def rechazar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._es_staff(interaction):
            await interaction.response.send_message("❌ Solo el staff puede.", ephemeral=True)
            return
        await interaction.response.send_modal(RechazoFichaModal(
            data=self.data, review_message=interaction.message,
            canal_id=CANAL_REGISTRAR_ESTUDIANTE, rechazar_fn=rechazar_estudiante))


# ── RECHAZO ───────────────────────────────────

class RechazoFichaModal(discord.ui.Modal, title="✏️ Motivo de rechazo"):
    motivo = discord.ui.TextInput(
        label="¿Por qué se rechaza?",
        style=discord.TextStyle.paragraph,
        placeholder="Explica el motivo al usuario...",
        required=False, max_length=500)

    def __init__(self, data, review_message, canal_id, rechazar_fn):
        super().__init__()
        self.data = data
        self.review_message = review_message
        self.canal_id = canal_id
        self.rechazar_fn = rechazar_fn

    async def on_submit(self, interaction: discord.Interaction):
        m = self.motivo.value.strip() if self.motivo.value else "Sin motivo especificado."
        try: self.rechazar_fn(self.data, str(interaction.user), m)
        except Exception: pass
        canal = interaction.client.get_channel(self.canal_id)
        embed = discord.Embed(title="❌ Ficha rechazada",
            description=f"Hola <@{self.data['user_id']}>, tu ficha para **{self.data['personaje']}** fue rechazada.\n\n**Motivo:**\n{m}\n\n¡Puedes corregirla! 💪",
            color=COLOR_RECHAZADO)
        if canal: await canal.send(embed=embed)
        else:
            try:
                u = await interaction.client.fetch_user(self.data["user_id"])
                await u.send(embed=embed)
            except Exception: pass
        updated = discord.Embed(title="Ficha — RECHAZADA",
            description=f"**Personaje:** {self.data['personaje']}\n**Usuario:** <@{self.data['user_id']}>\n\n**Motivo:**\n{m}",
            color=COLOR_RECHAZADO)
        updated.set_footer(text=f"Rechazado por {interaction.user.display_name}")
        await self.review_message.edit(embed=updated, view=None)
        await interaction.response.send_message("✅ Rechazo procesado.", ephemeral=True)


# ── UTILS ─────────────────────────────────────

def _guardar_temp(c, uid, d):
    if not hasattr(c, "_ficha_temp"): c._ficha_temp = {}
    c._ficha_temp[uid] = d

def _obtener_temp(c, uid):
    return getattr(c, "_ficha_temp", {}).get(uid)

def _limpiar_temp(c, uid):
    if hasattr(c, "_ficha_temp") and uid in c._ficha_temp: del c._ficha_temp[uid]


# ── COG ──────────────────────────────────────

class Estudiantes(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="ficha-estudiante", description="Registra la ficha de tu personaje estudiante.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def ficha_estudiante(self, interaction: discord.Interaction):
        if CANAL_REGISTRAR_ESTUDIANTE and interaction.channel_id != CANAL_REGISTRAR_ESTUDIANTE:
            canal = self.bot.get_channel(CANAL_REGISTRAR_ESTUDIANTE)
            mencionar = canal.mention if canal else f"<#{CANAL_REGISTRAR_ESTUDIANTE}>"
            await interaction.response.send_message(f"❌ Usa este comando en {mencionar}.", ephemeral=True)
            return
        await interaction.response.send_modal(EstudianteModal1())


async def setup(bot):
    await bot.add_cog(Estudiantes(bot))
