import discord
from discord import app_commands
from discord.ext import commands

from utils.constants import (
    GUILD_ID, CANAL_REGISTRO_TRABAJOS, CANAL_CARTA_ACEPTACION,
    CANAL_FICHAS_PROFESORES, ROL_STAFF, ROL_PROFESOR, ROL_REGISTRADO,
    get_slots_config, COLOR_APROBADO, COLOR_RECHAZADO,
    COLOR_PENDIENTE, MATERIAS, MATERIAS_LIMITE,
)
from utils.helpers import (
    is_valid_character_name, clean_field, default_if_empty,
    build_review_embed, build_acceptance_embed,
    publicar_ficha_con_imagenes, validar_edad_adulto,
)
from utils.sheets import aprobar_profesor, rechazar_trabajo, get_profesores_aprobados_por_materia
from utils.database import puede_registrar, registrar_personaje, usar_slot_extra, get_conteo_usuario
from utils.image_handler import registrar_espera
from cogs.admin import cargar_generacion
from cogs.estudiantes import RechazoFichaModal

MATERIAS_SELECT = [m for m in MATERIAS if m != "Profesor sustituto"]


# ── SELECT MATERIA ────────────────────────────

class MateriaSelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=m, value=m) for m in MATERIAS_SELECT]
        super().__init__(placeholder="📚 Selecciona la materia...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        materia  = self.values[0]
        limite   = MATERIAS_LIMITE.get(materia, 1)
        ocupados = get_profesores_aprobados_por_materia(materia)
        if ocupados >= limite:
            await interaction.response.send_message(
                f"❌ **{materia}** ya no tiene cupos disponibles.", ephemeral=True)
            return
        await interaction.response.edit_message(
            content=f"✅ Materia: **{materia}**\nPresiona para continuar.",
            view=ConfirmarMateriaView(materia=materia, user_id=interaction.user.id))


class MateriaSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(MateriaSelect())

    @discord.ui.button(label="🔄 Profesor sustituto", style=discord.ButtonStyle.secondary, row=1)
    async def sustituto(self, interaction: discord.Interaction, button: discord.ui.Button):
        materia  = "Profesor sustituto"
        limite   = MATERIAS_LIMITE.get(materia, 3)
        ocupados = get_profesores_aprobados_por_materia(materia)
        if ocupados >= limite:
            await interaction.response.send_message(
                f"❌ **{materia}** ya no tiene cupos ({limite} cupos).", ephemeral=True)
            return
        await interaction.response.edit_message(
            content=f"✅ Materia: **{materia}**\nPresiona para continuar.",
            view=ConfirmarMateriaView(materia=materia, user_id=interaction.user.id))


class ConfirmarMateriaView(discord.ui.View):
    def __init__(self, materia, user_id):
        super().__init__(timeout=120)
        self.materia = materia
        self.user_id = user_id

    @discord.ui.button(label="📝 Continuar con los datos del personaje", style=discord.ButtonStyle.primary)
    async def continuar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ProfesorModal1(materia=self.materia, user_id=self.user_id))
        self.stop()


# ── MODAL PARTE 1 ─────────────────────────────

class ProfesorModal1(discord.ui.Modal, title="🧑‍🏫 Ficha de Profesor — Parte 1/3"):
    personaje = discord.ui.TextInput(label="Nombre del personaje", placeholder="Ej: Mireille Duskwood", min_length=2, max_length=50)
    edad      = discord.ui.TextInput(label="Edad (mínimo 25 años)", placeholder="Mínimo 25 — los profesores son adultos", min_length=1, max_length=3)
    pronouns  = discord.ui.TextInput(label="Pronombres", placeholder="Ej: él/sus, ella/sus, elle/sus", min_length=2, max_length=30)
    especie   = discord.ui.TextInput(label="Especie", placeholder="Ej: Humano, Élfico, Híbrido...", min_length=2, max_length=50)
    elemento  = discord.ui.TextInput(label="Elemento mágico", placeholder="Ej: Fuego, Agua, Sombra...", min_length=2, max_length=50)

    def __init__(self, materia, user_id):
        super().__init__()
        self.materia = materia
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        nombre = self.personaje.value.strip()
        if not is_valid_character_name(nombre):
            await interaction.response.send_message("❌ Nombre no válido.", ephemeral=True)
            return
        valida, msg = validar_edad_adulto(self.edad.value)
        if not valida:
            await interaction.response.send_message(msg, ephemeral=True)
            return

        gen    = cargar_generacion()
        config = get_slots_config()
        res    = await puede_registrar(interaction.user.id, "profesores", gen, config.get("profesores"))

        if not res["puede"]:
            if res["tiene_slot_extra"]:
                _guardar_temp(interaction.client, interaction.user.id, {
                    "personaje": clean_field(nombre), "edad": clean_field(self.edad.value),
                    "pronouns": clean_field(self.pronouns.value), "especie": clean_field(self.especie.value),
                    "elemento": clean_field(self.elemento.value), "clase": self.materia, "usar_slot_extra": True,
                })
                await interaction.response.send_message(
                    f"⚠️ Límite de profesores. ✨ Slot disponible. ¿Usarlo para **{nombre}**?",
                    view=ConfirmarSlotView(interaction.user.id), ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ {res['razon']}", ephemeral=True)
            return

        _guardar_temp(interaction.client, interaction.user.id, {
            "personaje": clean_field(nombre), "edad": clean_field(self.edad.value),
            "pronouns": clean_field(self.pronouns.value), "especie": clean_field(self.especie.value),
            "elemento": clean_field(self.elemento.value), "clase": self.materia, "usar_slot_extra": False,
        })
        await interaction.response.send_message(
            f"✅ **Parte 1** para **{clean_field(nombre)}** — Clase: **{self.materia}**\nPresiona para continuar.",
            view=ContinuarModal2View(interaction.user.id), ephemeral=True)


# ── MODAL PARTE 2 ─────────────────────────────

class ProfesorModal2(discord.ui.Modal, title="🧑‍🏫 Ficha de Profesor — Parte 2/3"):
    habilidades  = discord.ui.TextInput(label="Poderes / Habilidades", style=discord.TextStyle.paragraph,
                                         placeholder="Salud, estado físico, habilidades mágicas...", min_length=10, max_length=800)
    debilidades  = discord.ui.TextInput(label="Debilidades", style=discord.TextStyle.paragraph,
                                         placeholder="Vulnerabilidades, limitaciones...", min_length=10, max_length=800)
    personalidad = discord.ui.TextInput(label="Personalidad", style=discord.TextStyle.paragraph,
                                         placeholder="Sanidad, inteligencia, rasgos de carácter...", min_length=10, max_length=800)
    historia     = discord.ui.TextInput(label="Historia", style=discord.TextStyle.paragraph,
                                         placeholder="Trasfondo y origen del personaje...", min_length=20, max_length=1500)

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        datos1 = _obtener_temp(interaction.client, self.user_id)
        if not datos1:
            await interaction.response.send_message("❌ Sesión expirada. Usa `/ficha-profesor` de nuevo.", ephemeral=True)
            return
        datos1.update({
            "habilidades":  clean_field(self.habilidades.value),
            "debilidades":  clean_field(self.debilidades.value),
            "personalidad": clean_field(self.personalidad.value),
            "historia":     clean_field(self.historia.value),
        })
        _guardar_temp(interaction.client, self.user_id, datos1)
        await interaction.response.send_message(
            "✅ **Parte 2 recibida.** Ahora ingresa hobbies, gustos y disgustos.",
            view=ContinuarModal3View(self.user_id), ephemeral=True)


# ── MODAL PARTE 3 ─────────────────────────────

class ProfesorModal3(discord.ui.Modal, title="🧑‍🏫 Ficha de Profesor — Parte 3/3"):
    hobbies   = discord.ui.TextInput(label="Hobbies", style=discord.TextStyle.paragraph,
                                      placeholder="¿Qué le gusta hacer en su tiempo libre?",
                                      required=False, max_length=300)
    gustos    = discord.ui.TextInput(label="Gustos", style=discord.TextStyle.paragraph,
                                      placeholder="¿Qué cosas le agradan o disfruta?",
                                      required=False, max_length=300)
    disgustos = discord.ui.TextInput(label="Disgustos", style=discord.TextStyle.paragraph,
                                      placeholder="¿Qué cosas le desagradan o no soporta?",
                                      required=False, max_length=300)

    def __init__(self, user_id, canal_id):
        super().__init__()
        self.user_id  = user_id
        self.canal_id = canal_id

    async def on_submit(self, interaction: discord.Interaction):
        datos = _obtener_temp(interaction.client, self.user_id)
        if not datos:
            await interaction.response.send_message("❌ Sesión expirada.", ephemeral=True)
            return
        datos["hobbies"]   = default_if_empty(self.hobbies.value)
        datos["gustos"]    = default_if_empty(self.gustos.value)
        datos["disgustos"] = default_if_empty(self.disgustos.value)
        datos["user_id"]   = interaction.user.id
        datos["username"]  = str(interaction.user)
        datos["imagen"]    = ""
        datos["_tipo"]     = "profesor"
        _guardar_temp(interaction.client, self.user_id, datos)
        registrar_espera(interaction.user.id, "profesor", self.canal_id, datos)
        await interaction.response.send_message(
            f"✅ **Formulario completado para {datos['personaje']}.**\n\n"
            f"📎 Último paso — **envía la imagen de tu personaje en este canal**.\n"
            f"Pégala 📋 o adjúntala 🖼️  *Puedes adjuntar varias imágenes.*\n"
            f"*Escribe `sin imagen` si no tienes una.*",
            ephemeral=True)


# ── VIEWS ─────────────────────────────────────

class ContinuarModal2View(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=300)
        self.user_id = user_id

    @discord.ui.button(label="📝 Continuar — Parte 2", style=discord.ButtonStyle.primary)
    async def continuar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ProfesorModal2(self.user_id))
        self.stop()


class ContinuarModal3View(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=300)
        self.user_id = user_id

    @discord.ui.button(label="📝 Continuar — Parte 3", style=discord.ButtonStyle.primary)
    async def continuar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            ProfesorModal3(user_id=self.user_id, canal_id=interaction.channel_id))
        self.stop()


class ConfirmarSlotView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=120)
        self.user_id = user_id

    @discord.ui.button(label="✨ Sí, usar slot adicional", style=discord.ButtonStyle.success)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="✅ Slot reservado.", view=ContinuarModal2View(self.user_id))
        self.stop()

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        _limpiar_temp(interaction.client, self.user_id)
        await interaction.response.edit_message(content="Cancelado.", view=None)
        self.stop()


# ── REVIEW ────────────────────────────────────

class ProfesorReviewView(discord.ui.View):
    def __init__(self, data):
        super().__init__(timeout=None)
        self.data = data

    def _es_staff(self, i):
        return any(r.id == ROL_STAFF for r in i.user.roles)

    @discord.ui.button(label="✅ Aprobar", style=discord.ButtonStyle.success, custom_id="profesor_aprobar")
    async def aprobar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._es_staff(interaction):
            await interaction.response.send_message("❌ Solo el staff puede.", ephemeral=True)
            return
        user_id = self.data["user_id"]
        gen     = cargar_generacion()
        try:
            if self.data.get("usar_slot_extra"): await usar_slot_extra(user_id, "profesores", gen)
            else: await registrar_personaje(user_id, "profesores", gen)
        except Exception as e: print(f"[PROFESORES] DB: {e}")
        try: aprobar_profesor(self.data, gen, str(interaction.user))
        except Exception as e: print(f"[PROFESORES] Sheets: {e}")
        try:
            guild  = interaction.guild
            member = guild.get_member(user_id) or await guild.fetch_member(user_id)
            rol    = guild.get_role(ROL_PROFESOR)
            if rol and member and rol not in member.roles:
                await member.add_roles(rol, reason="Ficha aprobada")
            rol_reg = guild.get_role(ROL_REGISTRADO)
            if rol_reg and member and rol_reg not in member.roles:
                await member.add_roles(rol_reg, reason="Primera ficha aprobada")
        except Exception as e: print(f"[PROFESORES] Roles: {e}")
        canal = interaction.client.get_channel(CANAL_FICHAS_PROFESORES)
        if canal: await publicar_ficha_con_imagenes(canal, "", self.data)
        canal_carta = interaction.client.get_channel(CANAL_CARTA_ACEPTACION)
        if canal_carta:
            conteo = await get_conteo_usuario(user_id, gen)
            await canal_carta.send(embed=build_acceptance_embed("profesor", self.data["personaje"], user_id, conteo, gen))
        updated = discord.Embed(title="🧑‍🏫 Ficha Profesor — APROBADA ✅",
            description=f"**Personaje:** {self.data['personaje']}\n**Clase:** {self.data.get('clase','')}\n**Usuario:** <@{user_id}>",
            color=COLOR_APROBADO)
        updated.set_footer(text=f"Aprobado por {interaction.user.display_name}")
        await interaction.message.edit(embed=updated, view=None)
        await interaction.response.send_message("✅ Aprobado.", ephemeral=True)

    @discord.ui.button(label="❌ Rechazar", style=discord.ButtonStyle.danger, custom_id="profesor_rechazar")
    async def rechazar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._es_staff(interaction):
            await interaction.response.send_message("❌ Solo el staff puede.", ephemeral=True)
            return
        await interaction.response.send_modal(RechazoFichaModal(
            data=self.data, review_message=interaction.message,
            canal_id=CANAL_REGISTRO_TRABAJOS, rechazar_fn=rechazar_trabajo))


# ── UTILS ─────────────────────────────────────

def _guardar_temp(c, uid, d):
    if not hasattr(c, "_ficha_temp"): c._ficha_temp = {}
    c._ficha_temp[uid] = d

def _obtener_temp(c, uid):
    return getattr(c, "_ficha_temp", {}).get(uid)

def _limpiar_temp(c, uid):
    if hasattr(c, "_ficha_temp") and uid in c._ficha_temp: del c._ficha_temp[uid]


# ── COG ──────────────────────────────────────

class Profesores(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="ficha-profesor", description="Registra la ficha de tu personaje profesor.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def ficha_profesor(self, interaction: discord.Interaction):
        if CANAL_REGISTRO_TRABAJOS and interaction.channel_id != CANAL_REGISTRO_TRABAJOS:
            canal = self.bot.get_channel(CANAL_REGISTRO_TRABAJOS)
            mencionar = canal.mention if canal else f"<#{CANAL_REGISTRO_TRABAJOS}>"
            await interaction.response.send_message(f"❌ Usa este comando en {mencionar}.", ephemeral=True)
            return
        await interaction.response.send_message(
            "📚 **Selecciona la materia que impartirá tu personaje:**\n*(O presiona el botón para Profesor sustituto)*",
            view=MateriaSelectView(), ephemeral=True)


async def setup(bot):
    await bot.add_cog(Profesores(bot))
