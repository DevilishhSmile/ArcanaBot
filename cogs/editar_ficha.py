import discord
from discord import app_commands
from discord.ext import commands

from utils.constants import (
    GUILD_ID, CANAL_REGISTRAR_ESTUDIANTE, CANAL_REGISTRO_TRABAJOS,
    CANAL_CARTA_ACEPTACION, CANAL_FICHAS_ESTUDIANTES, CANAL_FICHAS_PROFESORES,
    CANAL_FICHAS_TRABAJADORES, CANAL_REVISION_FICHAS,
    ROL_STAFF, ROL_ESTUDIANTE, ROL_PROFESOR, ROL_TRABAJADOR, ROL_REGISTRADO,
    get_slots_config, COLOR_PENDIENTE, COLOR_APROBADO, COLOR_RECHAZADO,
    COLOR_INFO, CLUBES,
)
from utils.helpers import (
    is_valid_character_name, clean_field, default_if_empty,
    build_review_embed, publicar_ficha_con_imagenes,
    validar_edad_estudiante, validar_edad_adulto,
)
from utils.sheets import (
    get_personajes_usuario, aprobar_estudiante, rechazar_estudiante,
    aprobar_profesor, aprobar_trabajador, rechazar_trabajo,
    get_all_rows,
)
from utils.image_handler import registrar_espera
from cogs.admin import cargar_generacion
from cogs.estudiantes import RechazoFichaModal


# ──────────────────────────────────────────────
# HELPERS — cargar datos actuales del personaje
# ──────────────────────────────────────────────

def _cargar_datos_estudiante(user_id: int, nombre: str) -> dict | None:
    """Lee los datos actuales de un estudiante desde Sheets."""
    try:
        for r in get_all_rows("EstudiantesAprobados"):
            if (str(r.get("user_id","")) == str(user_id) and
                    r.get("personaje","").strip().lower() == nombre.strip().lower()):
                return r
    except Exception:
        pass
    return None

def _cargar_datos_profesor(user_id: int, nombre: str) -> dict | None:
    try:
        for r in get_all_rows("Profesores"):
            if (str(r.get("user_id","")) == str(user_id) and
                    r.get("personaje","").strip().lower() == nombre.strip().lower() and
                    r.get("estado","").upper() == "APROBADO"):
                return r
    except Exception:
        pass
    return None

def _cargar_datos_trabajador(user_id: int, nombre: str) -> dict | None:
    try:
        for r in get_all_rows("Trabajadores"):
            if (str(r.get("user_id","")) == str(user_id) and
                    r.get("personaje","").strip().lower() == nombre.strip().lower() and
                    r.get("estado","").upper() == "APROBADO"):
                return r
    except Exception:
        pass
    return None


# ──────────────────────────────────────────────
# MODALES DE EDICIÓN — Estudiante
# Los campos vienen pre-rellenados con datos actuales
# ──────────────────────────────────────────────

class EditarEstudianteModal1(discord.ui.Modal, title="✏️ Editar Ficha — Parte 1/3"):
    personaje = discord.ui.TextInput(label="Nombre del personaje", min_length=2, max_length=50)
    edad      = discord.ui.TextInput(label="Edad (máximo 18 años)", min_length=1, max_length=3)
    pronouns  = discord.ui.TextInput(label="Pronombres", min_length=2, max_length=30)
    especie   = discord.ui.TextInput(label="Especie", min_length=2, max_length=50)
    elemento  = discord.ui.TextInput(label="Elemento mágico", min_length=2, max_length=50)

    def __init__(self, datos_actuales: dict, user_id: int):
        super().__init__()
        self.user_id = user_id
        # Pre-rellenar con datos actuales
        self.personaje.default = datos_actuales.get("personaje", "")
        self.edad.default      = str(datos_actuales.get("edad", ""))
        self.pronouns.default  = datos_actuales.get("pronouns", datos_actuales.get("pronombres", ""))
        self.especie.default   = datos_actuales.get("especie", "")
        self.elemento.default  = datos_actuales.get("elemento", "")

    async def on_submit(self, interaction: discord.Interaction):
        nombre = self.personaje.value.strip()
        if not is_valid_character_name(nombre):
            await interaction.response.send_message("❌ Nombre no válido.", ephemeral=True)
            return
        valida, msg = validar_edad_estudiante(self.edad.value)
        if not valida:
            await interaction.response.send_message(msg, ephemeral=True)
            return

        _guardar_temp(interaction.client, self.user_id, {
            "personaje": clean_field(nombre),
            "edad":      clean_field(self.edad.value),
            "pronouns":  clean_field(self.pronouns.value),
            "especie":   clean_field(self.especie.value),
            "elemento":  clean_field(self.elemento.value),
            "_tipo":     "estudiante",
            "_edicion":  True,
        })
        await interaction.response.send_message(
            "✅ **Parte 1 guardada.** Presiona para continuar.",
            view=_ContinuarView(self.user_id, "editar_est_2"), ephemeral=True)


class EditarEstudianteModal2(discord.ui.Modal, title="✏️ Editar Ficha — Parte 2/3"):
    habilidades  = discord.ui.TextInput(label="Poderes / Habilidades", style=discord.TextStyle.paragraph,
                                         placeholder="Salud, estado físico, habilidades mágicas...", min_length=10, max_length=800)
    debilidades  = discord.ui.TextInput(label="Debilidades", style=discord.TextStyle.paragraph,
                                         placeholder="Vulnerabilidades, limitaciones...", min_length=10, max_length=800)
    personalidad = discord.ui.TextInput(label="Personalidad", style=discord.TextStyle.paragraph,
                                         placeholder="Sanidad, inteligencia, rasgos de carácter...", min_length=10, max_length=800)
    historia     = discord.ui.TextInput(label="Historia", style=discord.TextStyle.paragraph,
                                         placeholder="Trasfondo y origen del personaje...", min_length=20, max_length=1500)

    def __init__(self, datos_actuales: dict, user_id: int):
        super().__init__()
        self.user_id = user_id
        self.habilidades.default  = datos_actuales.get("habilidades", "")[:800]
        self.debilidades.default  = datos_actuales.get("debilidades", "")[:800]
        self.personalidad.default = datos_actuales.get("personalidad", "")[:800]
        self.historia.default     = datos_actuales.get("historia", "")[:1500]

    async def on_submit(self, interaction: discord.Interaction):
        datos = _obtener_temp(interaction.client, self.user_id)
        if not datos:
            await interaction.response.send_message("❌ Sesión expirada.", ephemeral=True)
            return
        datos.update({
            "habilidades":  clean_field(self.habilidades.value),
            "debilidades":  clean_field(self.debilidades.value),
            "personalidad": clean_field(self.personalidad.value),
            "historia":     clean_field(self.historia.value),
        })
        _guardar_temp(interaction.client, self.user_id, datos)
        await interaction.response.send_message(
            "✅ **Parte 2 guardada.** Presiona para continuar.",
            view=_ContinuarView(self.user_id, "editar_est_3"), ephemeral=True)


class EditarEstudianteModal3(discord.ui.Modal, title="✏️ Editar Ficha — Parte 3/3"):
    hobbies   = discord.ui.TextInput(label="Hobbies", style=discord.TextStyle.paragraph,
                                      placeholder="¿Qué le gusta hacer en su tiempo libre?",
                                      required=False, max_length=300)
    gustos    = discord.ui.TextInput(label="Gustos", style=discord.TextStyle.paragraph,
                                      placeholder="¿Qué cosas le agradan o disfruta?",
                                      required=False, max_length=300)
    disgustos = discord.ui.TextInput(label="Disgustos", style=discord.TextStyle.paragraph,
                                      placeholder="¿Qué cosas le desagradan o no soporta?",
                                      required=False, max_length=300)

    def __init__(self, datos_actuales: dict, user_id: int, canal_id: int):
        super().__init__()
        self.user_id  = user_id
        self.canal_id = canal_id
        self.hobbies.default   = datos_actuales.get("hobbies", "")[:300]
        self.gustos.default    = datos_actuales.get("gustos", "")[:300]
        self.disgustos.default = datos_actuales.get("disgustos", "")[:300]

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
        _guardar_temp(interaction.client, self.user_id, datos)

        # Ir al selector de clubes
        await interaction.response.send_message(
            "✅ **Parte 3 guardada.**\n\n🎭 Actualiza el/los club(es) de tu personaje.",
            view=EditarClubesView(self.user_id, self.canal_id), ephemeral=True)


# ── SELECT CLUBES PARA EDICIÓN ────────────────

class EditarClubesSelect(discord.ui.Select):
    def __init__(self, clubes_actuales: list):
        options = [
            discord.SelectOption(
                label=n, value=n,
                default=(n in clubes_actuales)
            )
            for n in CLUBES.keys()
        ]
        super().__init__(placeholder="🎭 Selecciona uno o varios clubes...",
                         min_values=0, max_values=len(CLUBES), options=options)

    async def callback(self, interaction: discord.Interaction):
        self.view.clubes_seleccionados = self.values
        await interaction.response.defer()


class EditarClubesView(discord.ui.View):
    def __init__(self, user_id, canal_id):
        super().__init__(timeout=300)
        self.user_id  = user_id
        self.canal_id = canal_id
        self.clubes_seleccionados = []
        datos = {}  # se carga en _procesar
        self.add_item(EditarClubesSelect(clubes_actuales=[]))

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
        registrar_espera(interaction.user.id, "editar_estudiante", self.canal_id, data)
        clubs_txt = ", ".join(clubes) if clubes else "Ninguno"
        await interaction.response.edit_message(
            content=(
                f"✅ **Clubes:** {clubs_txt}\n\n"
                f"📎 Último paso — **envía la imagen actualizada en este canal**.\n"
                f"Pégala 📋 o adjúntala 🖼️  *Puedes adjuntar varias.*\n"
                f"*Escribe `sin imagen` si no cambias la imagen.*"
            ),
            view=None)
        self.stop()


# ──────────────────────────────────────────────
# MODALES DE EDICIÓN — Profesor
# ──────────────────────────────────────────────

class EditarProfesorModal1(discord.ui.Modal, title="✏️ Editar Ficha Profesor — 1/3"):
    personaje = discord.ui.TextInput(label="Nombre del personaje", min_length=2, max_length=50)
    edad      = discord.ui.TextInput(label="Edad (mínimo 25 años)", min_length=1, max_length=3)
    pronouns  = discord.ui.TextInput(label="Pronombres", min_length=2, max_length=30)
    especie   = discord.ui.TextInput(label="Especie", min_length=2, max_length=50)
    elemento  = discord.ui.TextInput(label="Elemento mágico", min_length=2, max_length=50)

    def __init__(self, datos_actuales: dict, user_id: int):
        super().__init__()
        self.user_id = user_id
        self.personaje.default = datos_actuales.get("personaje", "")
        self.edad.default      = str(datos_actuales.get("edad", ""))
        self.pronouns.default  = datos_actuales.get("pronouns", datos_actuales.get("pronombres", ""))
        self.especie.default   = datos_actuales.get("especie", "")
        self.elemento.default  = datos_actuales.get("elemento", "")
        self._clase = datos_actuales.get("materia", datos_actuales.get("clase", ""))

    async def on_submit(self, interaction: discord.Interaction):
        nombre = self.personaje.value.strip()
        if not is_valid_character_name(nombre):
            await interaction.response.send_message("❌ Nombre no válido.", ephemeral=True)
            return
        valida, msg = validar_edad_adulto(self.edad.value)
        if not valida:
            await interaction.response.send_message(msg, ephemeral=True)
            return
        _guardar_temp(interaction.client, self.user_id, {
            "personaje": clean_field(nombre), "edad": clean_field(self.edad.value),
            "pronouns": clean_field(self.pronouns.value), "especie": clean_field(self.especie.value),
            "elemento": clean_field(self.elemento.value), "clase": self._clase,
            "_tipo": "profesor", "_edicion": True,
        })
        await interaction.response.send_message(
            "✅ **Parte 1 guardada.**",
            view=_ContinuarView(self.user_id, "editar_prof_2"), ephemeral=True)


class EditarProfesorModal2(discord.ui.Modal, title="✏️ Editar Ficha Profesor — 2/3"):
    habilidades  = discord.ui.TextInput(label="Poderes / Habilidades", style=discord.TextStyle.paragraph, min_length=10, max_length=800)
    debilidades  = discord.ui.TextInput(label="Debilidades", style=discord.TextStyle.paragraph, min_length=10, max_length=800)
    personalidad = discord.ui.TextInput(label="Personalidad", style=discord.TextStyle.paragraph, min_length=10, max_length=800)
    historia     = discord.ui.TextInput(label="Historia", style=discord.TextStyle.paragraph, min_length=20, max_length=1500)

    def __init__(self, datos_actuales: dict, user_id: int):
        super().__init__()
        self.user_id = user_id
        self.habilidades.default  = datos_actuales.get("habilidades", "")[:800]
        self.debilidades.default  = datos_actuales.get("debilidades", "")[:800]
        self.personalidad.default = datos_actuales.get("personalidad", "")[:800]
        self.historia.default     = datos_actuales.get("historia", "")[:1500]

    async def on_submit(self, interaction: discord.Interaction):
        datos = _obtener_temp(interaction.client, self.user_id)
        if not datos:
            await interaction.response.send_message("❌ Sesión expirada.", ephemeral=True)
            return
        datos.update({
            "habilidades": clean_field(self.habilidades.value),
            "debilidades": clean_field(self.debilidades.value),
            "personalidad": clean_field(self.personalidad.value),
            "historia":    clean_field(self.historia.value),
        })
        _guardar_temp(interaction.client, self.user_id, datos)
        await interaction.response.send_message(
            "✅ **Parte 2 guardada.**",
            view=_ContinuarView(self.user_id, "editar_prof_3"), ephemeral=True)


class EditarProfesorModal3(discord.ui.Modal, title="✏️ Editar Ficha Profesor — 3/3"):
    hobbies   = discord.ui.TextInput(label="Hobbies", style=discord.TextStyle.paragraph, required=False, max_length=300)
    gustos    = discord.ui.TextInput(label="Gustos",  style=discord.TextStyle.paragraph, required=False, max_length=300)
    disgustos = discord.ui.TextInput(label="Disgustos", style=discord.TextStyle.paragraph, required=False, max_length=300)

    def __init__(self, datos_actuales: dict, user_id: int, canal_id: int):
        super().__init__()
        self.user_id  = user_id
        self.canal_id = canal_id
        self.hobbies.default   = datos_actuales.get("hobbies", "")[:300]
        self.gustos.default    = datos_actuales.get("gustos", "")[:300]
        self.disgustos.default = datos_actuales.get("disgustos", "")[:300]

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
        _guardar_temp(interaction.client, self.user_id, datos)
        registrar_espera(interaction.user.id, "editar_profesor", self.canal_id, datos)
        await interaction.response.send_message(
            f"✅ **Formulario completado.**\n\n"
            f"📎 Envía la imagen actualizada en este canal. Pégala 📋 o adjúntala 🖼️\n"
            f"*Escribe `sin imagen` si no cambias la imagen.*",
            ephemeral=True)


# ──────────────────────────────────────────────
# MODALES DE EDICIÓN — Trabajador
# ──────────────────────────────────────────────

class EditarTrabajadorModal1(discord.ui.Modal, title="✏️ Editar Ficha Trabajador — 1/3"):
    personaje = discord.ui.TextInput(label="Nombre del personaje", min_length=2, max_length=50)
    edad      = discord.ui.TextInput(label="Edad (mínimo 25 años)", min_length=1, max_length=3)
    pronouns  = discord.ui.TextInput(label="Pronombres", min_length=2, max_length=30)
    especie   = discord.ui.TextInput(label="Especie", min_length=2, max_length=50)
    elemento  = discord.ui.TextInput(label="Elemento mágico", min_length=2, max_length=50)

    def __init__(self, datos_actuales: dict, user_id: int):
        super().__init__()
        self.user_id = user_id
        self.personaje.default = datos_actuales.get("personaje", "")
        self.edad.default      = str(datos_actuales.get("edad", ""))
        self.pronouns.default  = datos_actuales.get("pronouns", datos_actuales.get("pronombres", ""))
        self.especie.default   = datos_actuales.get("especie", "")
        self.elemento.default  = datos_actuales.get("elemento", "")
        self._cargo = datos_actuales.get("cargo", "")

    async def on_submit(self, interaction: discord.Interaction):
        nombre = self.personaje.value.strip()
        if not is_valid_character_name(nombre):
            await interaction.response.send_message("❌ Nombre no válido.", ephemeral=True)
            return
        valida, msg = validar_edad_adulto(self.edad.value)
        if not valida:
            await interaction.response.send_message(msg, ephemeral=True)
            return
        _guardar_temp(interaction.client, self.user_id, {
            "personaje": clean_field(nombre), "edad": clean_field(self.edad.value),
            "pronouns": clean_field(self.pronouns.value), "especie": clean_field(self.especie.value),
            "elemento": clean_field(self.elemento.value), "cargo": self._cargo,
            "_tipo": "trabajador", "_edicion": True,
        })
        await interaction.response.send_message(
            "✅ **Parte 1 guardada.**",
            view=_ContinuarView(self.user_id, "editar_trab_2"), ephemeral=True)


class EditarTrabajadorModal2(discord.ui.Modal, title="✏️ Editar Ficha Trabajador — 2/3"):
    habilidades  = discord.ui.TextInput(label="Poderes / Habilidades", style=discord.TextStyle.paragraph, min_length=10, max_length=800)
    debilidades  = discord.ui.TextInput(label="Debilidades", style=discord.TextStyle.paragraph, min_length=10, max_length=800)
    personalidad = discord.ui.TextInput(label="Personalidad", style=discord.TextStyle.paragraph, min_length=10, max_length=800)
    historia     = discord.ui.TextInput(label="Historia", style=discord.TextStyle.paragraph, min_length=20, max_length=1500)

    def __init__(self, datos_actuales: dict, user_id: int):
        super().__init__()
        self.user_id = user_id
        self.habilidades.default  = datos_actuales.get("habilidades", "")[:800]
        self.debilidades.default  = datos_actuales.get("debilidades", "")[:800]
        self.personalidad.default = datos_actuales.get("personalidad", "")[:800]
        self.historia.default     = datos_actuales.get("historia", "")[:1500]

    async def on_submit(self, interaction: discord.Interaction):
        datos = _obtener_temp(interaction.client, self.user_id)
        if not datos:
            await interaction.response.send_message("❌ Sesión expirada.", ephemeral=True)
            return
        datos.update({
            "habilidades": clean_field(self.habilidades.value),
            "debilidades": clean_field(self.debilidades.value),
            "personalidad": clean_field(self.personalidad.value),
            "historia":    clean_field(self.historia.value),
        })
        _guardar_temp(interaction.client, self.user_id, datos)
        await interaction.response.send_message(
            "✅ **Parte 2 guardada.**",
            view=_ContinuarView(self.user_id, "editar_trab_3"), ephemeral=True)


class EditarTrabajadorModal3(discord.ui.Modal, title="✏️ Editar Ficha Trabajador — 3/3"):
    hobbies   = discord.ui.TextInput(label="Hobbies",    style=discord.TextStyle.paragraph, required=False, max_length=300)
    gustos    = discord.ui.TextInput(label="Gustos",     style=discord.TextStyle.paragraph, required=False, max_length=300)
    disgustos = discord.ui.TextInput(label="Disgustos",  style=discord.TextStyle.paragraph, required=False, max_length=300)

    def __init__(self, datos_actuales: dict, user_id: int, canal_id: int):
        super().__init__()
        self.user_id  = user_id
        self.canal_id = canal_id
        self.hobbies.default   = datos_actuales.get("hobbies", "")[:300]
        self.gustos.default    = datos_actuales.get("gustos", "")[:300]
        self.disgustos.default = datos_actuales.get("disgustos", "")[:300]

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
        _guardar_temp(interaction.client, self.user_id, datos)
        registrar_espera(interaction.user.id, "editar_trabajador", self.canal_id, datos)
        await interaction.response.send_message(
            f"✅ **Formulario completado.**\n\n"
            f"📎 Envía la imagen actualizada en este canal. Pégala 📋 o adjúntala 🖼️\n"
            f"*Escribe `sin imagen` si no cambias la imagen.*",
            ephemeral=True)


# ──────────────────────────────────────────────
# VIEW GENÉRICO DE CONTINUAR
# ──────────────────────────────────────────────

class _ContinuarView(discord.ui.View):
    def __init__(self, user_id: int, siguiente: str):
        super().__init__(timeout=300)
        self.user_id   = user_id
        self.siguiente = siguiente

    @discord.ui.button(label="📝 Continuar", style=discord.ButtonStyle.primary)
    async def continuar(self, interaction: discord.Interaction, button: discord.ui.Button):
        datos = _obtener_temp(interaction.client, self.user_id) or {}
        canal_id = interaction.channel_id

        if self.siguiente == "editar_est_2":
            await interaction.response.send_modal(EditarEstudianteModal2(datos, self.user_id))
        elif self.siguiente == "editar_est_3":
            await interaction.response.send_modal(EditarEstudianteModal3(datos, self.user_id, canal_id))
        elif self.siguiente == "editar_prof_2":
            await interaction.response.send_modal(EditarProfesorModal2(datos, self.user_id))
        elif self.siguiente == "editar_prof_3":
            await interaction.response.send_modal(EditarProfesorModal3(datos, self.user_id, canal_id))
        elif self.siguiente == "editar_trab_2":
            await interaction.response.send_modal(EditarTrabajadorModal2(datos, self.user_id))
        elif self.siguiente == "editar_trab_3":
            await interaction.response.send_modal(EditarTrabajadorModal3(datos, self.user_id, canal_id))
        self.stop()


# ──────────────────────────────────────────────
# REVIEW VIEW — Ficha editada
# ──────────────────────────────────────────────

class EditarFichaReviewView(discord.ui.View):
    def __init__(self, data: dict):
        super().__init__(timeout=None)
        self.data = data

    def _es_staff(self, i):
        return any(r.id == ROL_STAFF for r in i.user.roles)

    @discord.ui.button(label="✅ Aprobar edición", style=discord.ButtonStyle.success, custom_id="editar_aprobar")
    async def aprobar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._es_staff(interaction):
            await interaction.response.send_message("❌ Solo el staff puede.", ephemeral=True)
            return

        tipo    = self.data.get("_tipo", "estudiante")
        user_id = self.data["user_id"]
        gen     = cargar_generacion()

        # Actualizar Sheets según tipo
        try:
            if tipo == "estudiante":
                aprobar_estudiante(self.data, gen, str(interaction.user))
            elif tipo == "profesor":
                aprobar_profesor(self.data, gen, str(interaction.user))
            elif tipo == "trabajador":
                aprobar_trabajador(self.data, gen, str(interaction.user))
        except Exception as e:
            print(f"[EDITAR] Sheets: {e}")

        # Publicar ficha editada en el canal correspondiente
        canales = {
            "estudiante": CANAL_FICHAS_ESTUDIANTES,
            "profesor":   CANAL_FICHAS_PROFESORES,
            "trabajador": CANAL_FICHAS_TRABAJADORES,
        }
        canal = interaction.client.get_channel(canales.get(tipo, CANAL_FICHAS_ESTUDIANTES))
        if canal:
            await publicar_ficha_con_imagenes(canal, "", self.data)

        # Notificar al usuario
        try:
            guild  = interaction.guild
            member = guild.get_member(user_id) or await guild.fetch_member(user_id)
            if member:
                embed_u = discord.Embed(
                    title="✏️ Ficha actualizada",
                    description=(
                        f"¡Hola <@{user_id}>! Tu ficha para **{self.data['personaje']}** "
                        f"fue editada y aprobada correctamente. 🎉\n\n"
                        f"La nueva versión ya está publicada en el canal de fichas."
                    ),
                    color=COLOR_APROBADO
                )
                try: await member.send(embed=embed_u)
                except Exception: pass
        except Exception: pass

        updated = discord.Embed(
            title="✏️ Ficha Editada — APROBADA ✅",
            description=f"**Personaje:** {self.data['personaje']}\n**Usuario:** <@{user_id}>",
            color=COLOR_APROBADO
        )
        updated.set_footer(text=f"Aprobado por {interaction.user.display_name}")
        await interaction.message.edit(embed=updated, view=None)
        await interaction.response.send_message("✅ Edición aprobada.", ephemeral=True)

    @discord.ui.button(label="❌ Rechazar edición", style=discord.ButtonStyle.danger, custom_id="editar_rechazar")
    async def rechazar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._es_staff(interaction):
            await interaction.response.send_message("❌ Solo el staff puede.", ephemeral=True)
            return
        await interaction.response.send_modal(RechazoFichaModal(
            data=self.data, review_message=interaction.message,
            canal_id=CANAL_REGISTRAR_ESTUDIANTE, rechazar_fn=rechazar_estudiante))


# ──────────────────────────────────────────────
# UTILS
# ──────────────────────────────────────────────

def _guardar_temp(c, uid, d):
    if not hasattr(c, "_ficha_temp"): c._ficha_temp = {}
    c._ficha_temp[uid] = d

def _obtener_temp(c, uid):
    return getattr(c, "_ficha_temp", {}).get(uid)

def _limpiar_temp(c, uid):
    if hasattr(c, "_ficha_temp") and uid in c._ficha_temp: del c._ficha_temp[uid]


# ──────────────────────────────────────────────
# COG
# ──────────────────────────────────────────────

class EditarFicha(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="editar-ficha",
        description="Edita la ficha de uno de tus personajes aprobados."
    )
    @app_commands.describe(nombre="Nombre exacto del personaje a editar")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def editar_ficha(self, interaction: discord.Interaction, nombre: str):
        # Buscar el personaje en todos los tipos
        personajes = get_personajes_usuario(interaction.user.id)
        encontrado = next(
            (p for p in personajes if p["personaje"].strip().lower() == nombre.strip().lower()),
            None
        )

        if not encontrado:
            await interaction.response.send_message(
                f"❌ No encontré el personaje **{nombre}** en tus registros aprobados.\n\n"
                f"Usa `/mis-personajes` para ver tus personajes.",
                ephemeral=True
            )
            return

        tipo = encontrado["tipo"]

        # Cargar datos actuales de Sheets
        if tipo == "estudiante":
            datos = _cargar_datos_estudiante(interaction.user.id, encontrado["personaje"])
        elif tipo == "profesor":
            datos = _cargar_datos_profesor(interaction.user.id, encontrado["personaje"])
        else:
            datos = _cargar_datos_trabajador(interaction.user.id, encontrado["personaje"])

        if not datos:
            await interaction.response.send_message(
                "❌ No se pudieron cargar los datos actuales. Intenta de nuevo.",
                ephemeral=True
            )
            return

        # Guardar datos actuales en temp para pre-rellenar los modales
        _guardar_temp(self.bot, interaction.user.id, {**datos, "_tipo": tipo, "_edicion": True})

        # Abrir el primer modal según el tipo
        if tipo == "estudiante":
            await interaction.response.send_modal(
                EditarEstudianteModal1(datos_actuales=datos, user_id=interaction.user.id))
        elif tipo == "profesor":
            await interaction.response.send_modal(
                EditarProfesorModal1(datos_actuales=datos, user_id=interaction.user.id))
        else:
            await interaction.response.send_modal(
                EditarTrabajadorModal1(datos_actuales=datos, user_id=interaction.user.id))


async def setup(bot):
    await bot.add_cog(EditarFicha(bot))
