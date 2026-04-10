import discord
from discord import app_commands
from discord.ext import commands

from utils.constants import GUILD_ID, ROL_STAFF, COLOR_INFO, COLOR_APROBADO, COLOR_RECHAZADO, COLOR_PENDIENTE
from cogs.admin import cargar_generacion


class AdminData(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _es_staff(self, i):
        return any(r.id == ROL_STAFF for r in i.user.roles)

    data_group = app_commands.Group(
        name="admin-data",
        description="[STAFF] Gestión de datos de usuarios.",
        guild_ids=[GUILD_ID]
    )

    # ──────────────────────────────────────────────
    # /admin-data ver @usuario
    # Muestra todo lo que tiene registrado el usuario
    # ──────────────────────────────────────────────

    @data_group.command(name="ver", description="[STAFF] Ver todos los datos registrados de un usuario.")
    @app_commands.describe(usuario="El usuario a consultar")
    async def data_ver(self, interaction: discord.Interaction, usuario: discord.Member):
        if not self._es_staff(interaction):
            await interaction.response.send_message("❌ Solo el staff puede.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        from utils.sheets import get_personajes_usuario, get_all_rows
        from utils.database import get_conteo_usuario

        gen    = cargar_generacion()
        conteo = await get_conteo_usuario(usuario.id, gen)
        personajes = get_personajes_usuario(usuario.id)

        # Verificar uniformes
        try:
            uniformes = [r for r in get_all_rows("UniformesAprobados")
                         if str(r.get("user_id","")) == str(usuario.id)]
        except Exception:
            uniformes = []

        embed = discord.Embed(
            title=f"🗂️ Datos de {usuario.display_name}",
            color=COLOR_INFO
        )
        embed.set_author(name=usuario.display_name, icon_url=usuario.display_avatar.url)
        embed.add_field(name="User ID", value=f"`{usuario.id}`", inline=True)
        embed.add_field(name="Generación activa", value=f"Gen {gen}", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=False)

        # Slots en DB
        embed.add_field(name="📊 Conteo en base de datos", value=(
            f"🎓 Estudiantes: **{conteo.get('estudiantes_usados',0)}**\n"
            f"🧑‍🏫 Profesores: **{conteo.get('profesores_usados',0)}**\n"
            f"🧑‍💼 Trabajadores: **{conteo.get('trabajadores_usados',0)}**\n"
            f"✨ Slots extra disponibles: **{conteo.get('slots_extra_disponibles',0)}**\n"
            f"✨ Slots extra usados: **{conteo.get('slots_extra_usados',0)}**"
        ), inline=True)

        # Uniformes aprobados
        if uniformes:
            lista_u = "\n".join(f"• {u.get('personaje','?')}" for u in uniformes)
            embed.add_field(name=f"👕 Uniformes aprobados ({len(uniformes)})", value=lista_u, inline=True)
        else:
            embed.add_field(name="👕 Uniformes aprobados", value="Ninguno", inline=True)

        embed.add_field(name="\u200b", value="\u200b", inline=False)

        # Personajes
        if personajes:
            iconos = {"estudiante": "🎓", "profesor": "🧑‍🏫", "trabajador": "🧑‍💼"}
            lista_p = "\n".join(
                f"{iconos.get(p['tipo'],'📋')} **{p['personaje']}** — {p['detalle']}"
                for p in personajes
            )
            embed.add_field(name=f"📋 Personajes registrados ({len(personajes)})", value=lista_p, inline=False)
        else:
            embed.add_field(name="📋 Personajes registrados", value="Ninguno", inline=False)

        await interaction.followup.send(embed=embed, ephemeral=True)

    # ──────────────────────────────────────────────
    # /admin-data eliminar-tipo @usuario tipo
    # Elimina todos los personajes de un tipo específico
    # ──────────────────────────────────────────────

    @data_group.command(
        name="eliminar-tipo",
        description="[STAFF] Eliminar todos los personajes de un tipo específico de un usuario."
    )
    @app_commands.describe(
        usuario="El usuario al que se le eliminarán los personajes",
        tipo="Tipo de personajes a eliminar"
    )
    @app_commands.choices(tipo=[
        app_commands.Choice(name="🎓 Estudiantes", value="estudiante"),
        app_commands.Choice(name="🧑‍🏫 Profesores", value="profesor"),
        app_commands.Choice(name="🧑‍💼 Trabajadores", value="trabajador"),
        app_commands.Choice(name="👕 Uniformes aprobados", value="uniforme"),
    ])
    async def data_eliminar_tipo(self, interaction: discord.Interaction,
                                  usuario: discord.Member,
                                  tipo: str):
        if not self._es_staff(interaction):
            await interaction.response.send_message("❌ Solo el staff puede.", ephemeral=True)
            return

        from utils.sheets import get_personajes_usuario, get_all_rows, get_sheet

        # Obtener lista de lo que se va a eliminar para mostrar confirmación
        if tipo == "uniforme":
            try:
                items = [r for r in get_all_rows("UniformesAprobados")
                         if str(r.get("user_id","")) == str(usuario.id)]
                nombres = [r.get("personaje","?") for r in items]
            except Exception:
                nombres = []
        else:
            personajes = get_personajes_usuario(usuario.id)
            nombres = [p["personaje"] for p in personajes if p["tipo"] == tipo]

        if not nombres:
            await interaction.response.send_message(
                f"ℹ️ **{usuario.display_name}** no tiene {tipo}s registrados.",
                ephemeral=True
            )
            return

        iconos = {"estudiante": "🎓", "profesor": "🧑‍🏫", "trabajador": "🧑‍💼", "uniforme": "👕"}
        lista = "\n".join(f"• {n}" for n in nombres)

        embed = discord.Embed(
            title=f"⚠️ Confirmar eliminación — {iconos.get(tipo,'')} {tipo.capitalize()}s",
            description=(
                f"Se eliminarán **{len(nombres)}** {tipo}(s) de **{usuario.display_name}**:\n\n"
                f"{lista}\n\n"
                f"Esta acción no se puede deshacer."
            ),
            color=COLOR_PENDIENTE
        )
        view = ConfirmarEliminacionTipoView(
            usuario_id=usuario.id,
            usuario_nombre=usuario.display_name,
            tipo=tipo,
            nombres=nombres,
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    # ──────────────────────────────────────────────
    # /admin-data eliminar-personaje @usuario nombre
    # Elimina un personaje específico por nombre
    # ──────────────────────────────────────────────

    @data_group.command(
        name="eliminar-personaje",
        description="[STAFF] Eliminar un personaje específico de un usuario."
    )
    @app_commands.describe(
        usuario="El usuario al que se le eliminará el personaje",
        nombre="Nombre exacto del personaje a eliminar"
    )
    async def data_eliminar_personaje(self, interaction: discord.Interaction,
                                       usuario: discord.Member,
                                       nombre: str):
        if not self._es_staff(interaction):
            await interaction.response.send_message("❌ Solo el staff puede.", ephemeral=True)
            return

        from utils.sheets import get_personajes_usuario

        personajes = get_personajes_usuario(usuario.id)
        encontrado = next(
            (p for p in personajes if p["personaje"].strip().lower() == nombre.strip().lower()),
            None
        )

        if not encontrado:
            await interaction.response.send_message(
                f"❌ No encontré el personaje **{nombre}** en los registros de **{usuario.display_name}**.",
                ephemeral=True
            )
            return

        iconos = {"estudiante": "🎓", "profesor": "🧑‍🏫", "trabajador": "🧑‍💼"}
        embed = discord.Embed(
            title="⚠️ Confirmar eliminación",
            description=(
                f"Se eliminará el personaje:\n\n"
                f"{iconos.get(encontrado['tipo'],'📋')} **{encontrado['personaje']}**\n"
                f"Tipo: {encontrado['tipo'].capitalize()} — {encontrado['detalle']}\n"
                f"Usuario: **{usuario.display_name}**\n\n"
                f"Esta acción no se puede deshacer."
            ),
            color=COLOR_PENDIENTE
        )
        view = ConfirmarEliminacionUnoView(
            usuario_id=usuario.id,
            usuario_nombre=usuario.display_name,
            personaje=encontrado["personaje"],
            tipo=encontrado["tipo"],
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    # ──────────────────────────────────────────────
    # /admin-data reset-total @usuario
    # Elimina ABSOLUTAMENTE todo de un usuario
    # ──────────────────────────────────────────────

    @data_group.command(
        name="reset-total",
        description="[STAFF] ⚠️ Eliminar TODOS los datos de un usuario (personajes, uniformes y slots)."
    )
    @app_commands.describe(usuario="El usuario al que se le hará reset total")
    async def data_reset_total(self, interaction: discord.Interaction, usuario: discord.Member):
        if not self._es_staff(interaction):
            await interaction.response.send_message("❌ Solo el staff puede.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🚨 RESET TOTAL — Confirmación requerida",
            description=(
                f"Estás a punto de **eliminar TODOS los datos** de **{usuario.display_name}**:\n\n"
                f"• Todos sus personajes (estudiantes, profesores, trabajadores)\n"
                f"• Todos sus uniformes aprobados\n"
                f"• Su conteo de slots en la base de datos (se resetea a 0)\n"
                f"• Sus slots adicionales disponibles\n\n"
                f"⚠️ **Esta acción es irreversible.** ¿Confirmas?"
            ),
            color=COLOR_RECHAZADO
        )
        view = ConfirmarResetTotalView(
            usuario_id=usuario.id,
            usuario_nombre=usuario.display_name,
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    # ──────────────────────────────────────────────
    # /admin-data reset-slots @usuario
    # Solo resetea los conteos en SQLite, sin tocar Sheets
    # ──────────────────────────────────────────────

    @data_group.command(
        name="reset-slots",
        description="[STAFF] Resetear solo los contadores de slots de un usuario en la base de datos."
    )
    @app_commands.describe(usuario="El usuario cuyos slots se resetearán")
    async def data_reset_slots(self, interaction: discord.Interaction, usuario: discord.Member):
        if not self._es_staff(interaction):
            await interaction.response.send_message("❌ Solo el staff puede.", ephemeral=True)
            return

        from utils.database import get_conteo_usuario
        gen    = cargar_generacion()
        conteo = await get_conteo_usuario(usuario.id, gen)

        embed = discord.Embed(
            title="⚠️ Confirmar reset de slots",
            description=(
                f"Se resetearán los contadores de slots de **{usuario.display_name}** en Gen {gen}:\n\n"
                f"🎓 Estudiantes: **{conteo.get('estudiantes_usados',0)}** → 0\n"
                f"🧑‍🏫 Profesores: **{conteo.get('profesores_usados',0)}** → 0\n"
                f"🧑‍💼 Trabajadores: **{conteo.get('trabajadores_usados',0)}** → 0\n"
                f"✨ Slots extra: **{conteo.get('slots_extra_disponibles',0)}** → 0\n\n"
                f"ℹ️ Esto NO elimina los personajes de Google Sheets, solo los contadores internos."
            ),
            color=COLOR_PENDIENTE
        )
        view = ConfirmarResetSlotsView(usuario_id=usuario.id, usuario_nombre=usuario.display_name)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ──────────────────────────────────────────────
# VIEWS DE CONFIRMACIÓN
# ──────────────────────────────────────────────

class ConfirmarEliminacionUnoView(discord.ui.View):
    def __init__(self, usuario_id, usuario_nombre, personaje, tipo):
        super().__init__(timeout=60)
        self.usuario_id    = usuario_id
        self.usuario_nombre = usuario_nombre
        self.personaje     = personaje
        self.tipo          = tipo

    @discord.ui.button(label="✅ Confirmar eliminación", style=discord.ButtonStyle.danger)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        from utils.sheets import eliminar_personaje_sheets
        from utils.database import restar_personaje

        gen       = cargar_generacion()
        eliminado = eliminar_personaje_sheets(self.usuario_id, self.personaje, self.tipo)

        try:
            await restar_personaje(self.usuario_id, f"{self.tipo}s", gen)
        except Exception as e:
            print(f"[ADMIN_DATA] Error restando slot: {e}")

        embed = discord.Embed(
            title="✅ Personaje eliminado",
            description=(
                f"**{self.personaje}** ({self.tipo}) de **{self.usuario_nombre}** fue eliminado.\n"
                f"{'✅ Eliminado de Sheets.' if eliminado else '⚠️ No se encontró en Sheets.'}"
            ),
            color=COLOR_APROBADO
        )
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Cancelado.", embed=None, view=None)


class ConfirmarEliminacionTipoView(discord.ui.View):
    def __init__(self, usuario_id, usuario_nombre, tipo, nombres):
        super().__init__(timeout=60)
        self.usuario_id    = usuario_id
        self.usuario_nombre = usuario_nombre
        self.tipo          = tipo
        self.nombres       = nombres

    @discord.ui.button(label="✅ Confirmar eliminación", style=discord.ButtonStyle.danger)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        from utils.sheets import eliminar_personaje_sheets, get_sheet
        from utils.database import restar_personaje

        gen         = cargar_generacion()
        eliminados  = 0
        errores     = 0

        if self.tipo == "uniforme":
            # Eliminar de UniformesAprobados
            try:
                sheet  = get_sheet("UniformesAprobados")
                rows   = sheet.get_all_values()
                # Borrar de abajo hacia arriba para no desfasar índices
                indices = [i+1 for i, row in enumerate(rows)
                           if i > 0 and len(row) > 0 and str(row[0]) == str(self.usuario_id)]
                for idx in reversed(indices):
                    sheet.delete_rows(idx)
                    eliminados += 1
            except Exception as e:
                print(f"[ADMIN_DATA] Error eliminando uniformes: {e}")
                errores += 1
        else:
            for nombre in self.nombres:
                ok = eliminar_personaje_sheets(self.usuario_id, nombre, self.tipo)
                if ok:
                    eliminados += 1
                    try:
                        await restar_personaje(self.usuario_id, f"{self.tipo}s", gen)
                    except Exception:
                        pass
                else:
                    errores += 1

        embed = discord.Embed(
            title=f"✅ Eliminación completada — {self.tipo.capitalize()}s",
            description=(
                f"Usuario: **{self.usuario_nombre}**\n\n"
                f"✅ Eliminados: **{eliminados}**\n"
                f"{'⚠️ Errores: **' + str(errores) + '**' if errores else ''}"
            ),
            color=COLOR_APROBADO
        )
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Cancelado.", embed=None, view=None)


class ConfirmarResetTotalView(discord.ui.View):
    def __init__(self, usuario_id, usuario_nombre):
        super().__init__(timeout=60)
        self.usuario_id    = usuario_id
        self.usuario_nombre = usuario_nombre

    @discord.ui.button(label="🚨 SÍ, resetear todo", style=discord.ButtonStyle.danger)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        from utils.sheets import get_sheet, get_personajes_usuario, eliminar_personaje_sheets
        from utils.database import reset_usuario

        gen       = cargar_generacion()
        resumen   = {"estudiantes": 0, "profesores": 0, "trabajadores": 0, "uniformes": 0}

        # Eliminar personajes de Sheets
        personajes = get_personajes_usuario(self.usuario_id)
        for p in personajes:
            ok = eliminar_personaje_sheets(self.usuario_id, p["personaje"], p["tipo"])
            if ok:
                resumen[f"{p['tipo']}s"] += 1

        # Eliminar uniformes aprobados
        try:
            sheet  = get_sheet("UniformesAprobados")
            rows   = sheet.get_all_values()
            indices = [i+1 for i, row in enumerate(rows)
                       if i > 0 and len(row) > 0 and str(row[0]) == str(self.usuario_id)]
            for idx in reversed(indices):
                sheet.delete_rows(idx)
                resumen["uniformes"] += 1
        except Exception as e:
            print(f"[ADMIN_DATA] Error eliminando uniformes en reset: {e}")

        # Resetear base de datos
        try:
            await reset_usuario(self.usuario_id, gen)
        except Exception as e:
            print(f"[ADMIN_DATA] Error reseteando DB: {e}")

        embed = discord.Embed(
            title="🚨 Reset total completado",
            description=(
                f"Todos los datos de **{self.usuario_nombre}** fueron eliminados:\n\n"
                f"🎓 Estudiantes eliminados: **{resumen['estudiantes']}**\n"
                f"🧑‍🏫 Profesores eliminados: **{resumen['profesores']}**\n"
                f"🧑‍💼 Trabajadores eliminados: **{resumen['trabajadores']}**\n"
                f"👕 Uniformes eliminados: **{resumen['uniformes']}**\n"
                f"💾 Base de datos reseteada: ✅"
            ),
            color=COLOR_APROBADO
        )
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Cancelado.", embed=None, view=None)


class ConfirmarResetSlotsView(discord.ui.View):
    def __init__(self, usuario_id, usuario_nombre):
        super().__init__(timeout=60)
        self.usuario_id    = usuario_id
        self.usuario_nombre = usuario_nombre

    @discord.ui.button(label="✅ Confirmar reset de slots", style=discord.ButtonStyle.danger)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        from utils.database import reset_usuario
        gen = cargar_generacion()
        try:
            await reset_usuario(self.usuario_id, gen)
            embed = discord.Embed(
                title="✅ Slots reseteados",
                description=f"Los contadores de slots de **{self.usuario_nombre}** fueron reseteados a 0 en Gen {gen}.",
                color=COLOR_APROBADO
            )
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"No se pudieron resetear los slots: {e}",
                color=COLOR_RECHAZADO
            )
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Cancelado.", embed=None, view=None)


async def setup(bot):
    await bot.add_cog(AdminData(bot))
