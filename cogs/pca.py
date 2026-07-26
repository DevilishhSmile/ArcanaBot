import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

from utils.constants import (
    GUILD_ID, ROLES_AUTORIDAD_PC, ROL_ESTUDIANTE, ROL_STAFF, ROL_PROFESOR,
    COLOR_INFO, COLOR_APROBADO, COLOR_RECHAZADO, COLOR_PENDIENTE,
    TIPOS_SANCION, calcular_pc_por_nota, calcular_reduccion_castigo_menor,
    calcular_reduccion_detencion, calcular_reduccion_suspension,
    PC_TRABAJO_SUCIO_MIN, PC_TRABAJO_SUCIO_MAX,
)
from utils.sheets import get_personajes_usuario

# Canal donde llegan solicitudes de aprobación del staff
CANAL_APROBACIONES = 1490609417572323329


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ──────────────────────────────────────────────
# SHEETS helpers
# ──────────────────────────────────────────────

def _get_pc(user_id: int, personaje: str) -> dict:
    from utils.sheets import get_sheet
    try:
        for r in get_sheet("PuntosPC").get_all_records():
            if str(r.get("user_id","")) == str(user_id) and \
               r.get("personaje","").strip().lower() == personaje.strip().lower():
                return {"pc_total": int(r.get("pc_total",0)),
                        "pc_disponible": int(r.get("pc_disponible",0))}
    except Exception as e:
        print(f"[PCA] _get_pc: {e}")
    return {"pc_total": 0, "pc_disponible": 0}

def _sumar_pc(user_id: int, username: str, personaje: str,
               cantidad: int, motivo: str, asignado_por: str):
    from utils.sheets import get_sheet
    try:
        sheet = get_sheet("PuntosPC")
        rows  = sheet.get_all_values()
        encontrado = False
        for i, row in enumerate(rows):
            if i == 0: continue
            if len(row) >= 3 and str(row[0]) == str(user_id) and \
               row[2].strip().lower() == personaje.strip().lower():
                sheet.update_cell(i+1, 4, int(row[3] or 0) + cantidad)
                sheet.update_cell(i+1, 5, int(row[4] or 0) + cantidad)
                sheet.update_cell(i+1, 6, _now())
                encontrado = True
                break
        if not encontrado:
            sheet.append_row([str(user_id), username, personaje, cantidad, cantidad, _now()],
                             value_input_option="USER_ENTERED")
        get_sheet("HistorialPC").append_row(
            [str(user_id), personaje, cantidad, motivo, asignado_por, _now()],
            value_input_option="USER_ENTERED")
    except Exception as e:
        print(f"[PCA] _sumar_pc: {e}")

def _restar_pc(user_id: int, personaje: str, cantidad: int) -> bool:
    from utils.sheets import get_sheet
    try:
        sheet = get_sheet("PuntosPC")
        rows  = sheet.get_all_values()
        for i, row in enumerate(rows):
            if i == 0: continue
            if len(row) >= 3 and str(row[0]) == str(user_id) and \
               row[2].strip().lower() == personaje.strip().lower():
                disp = int(row[4] or 0)
                if disp < cantidad: return False
                sheet.update_cell(i+1, 5, disp - cantidad)
                sheet.update_cell(i+1, 6, _now())
                return True
    except Exception as e:
        print(f"[PCA] _restar_pc: {e}")
    return False

def _limpiar_pc_personaje(user_id: int, personaje: str) -> bool:
    from utils.sheets import get_sheet
    try:
        sheet = get_sheet("PuntosPC")
        rows  = sheet.get_all_values()
        for i, row in enumerate(rows):
            if i == 0: continue
            if len(row) >= 3 and str(row[0]) == str(user_id) and \
               row[2].strip().lower() == personaje.strip().lower():
                sheet.update_cell(i+1, 4, 0)
                sheet.update_cell(i+1, 5, 0)
                sheet.update_cell(i+1, 6, _now())
                return True
    except Exception as e:
        print(f"[PCA] _limpiar_pc_personaje: {e}")
    return False

def _limpiar_pc_todos() -> bool:
    from utils.sheets import get_sheet
    try:
        sheet = get_sheet("PuntosPC")
        rows  = sheet.get_all_values()
        for i, row in enumerate(rows):
            if i == 0 or len(row) < 5: continue
            sheet.update_cell(i+1, 4, 0)
            sheet.update_cell(i+1, 5, 0)
            sheet.update_cell(i+1, 6, _now())
        return True
    except Exception as e:
        print(f"[PCA] _limpiar_pc_todos: {e}")
        return False

def _registrar_sancion(user_id, username, personaje, tipo, duracion, motivo, asignado_por,
                        estado="ACTIVA"):
    from utils.sheets import get_sheet
    try:
        get_sheet("Sanciones").append_row(
            [str(user_id), username, personaje, tipo, str(duracion),
             estado, asignado_por, _now(), motivo],
            value_input_option="USER_ENTERED")
    except Exception as e:
        print(f"[PCA] _registrar_sancion: {e}")

def _get_sanciones_activas(user_id: int, personaje: str) -> list:
    from utils.sheets import get_sheet
    try:
        return [r for r in get_sheet("Sanciones").get_all_records()
                if str(r.get("user_id","")) == str(user_id) and
                r.get("personaje","").strip().lower() == personaje.strip().lower() and
                r.get("estado","").upper() == "ACTIVA"]
    except Exception as e:
        print(f"[PCA] _get_sanciones_activas: {e}")
        return []

def _marcar_sancion_cumplida(user_id: int, personaje: str, indice: int) -> bool:
    from utils.sheets import get_sheet
    try:
        sheet = get_sheet("Sanciones")
        rows  = sheet.get_all_values()
        count = 0
        for i, row in enumerate(rows):
            if i == 0: continue
            if (len(row) >= 6 and str(row[0]) == str(user_id) and
                    row[2].strip().lower() == personaje.strip().lower() and
                    row[5].upper() == "ACTIVA"):
                if count == indice:
                    sheet.update_cell(i+1, 6, "CUMPLIDA")
                    return True
                count += 1
    except Exception as e:
        print(f"[PCA] _marcar_cumplida: {e}")
    return False

def _limpiar_sanciones_personaje(user_id: int, personaje: str) -> int:
    from utils.sheets import get_sheet
    try:
        sheet     = get_sheet("Sanciones")
        rows      = sheet.get_all_values()
        limpiadas = 0
        for i, row in enumerate(rows):
            if i == 0: continue
            if (len(row) >= 6 and str(row[0]) == str(user_id) and
                    row[2].strip().lower() == personaje.strip().lower() and
                    row[5].upper() == "ACTIVA"):
                sheet.update_cell(i+1, 6, "LIMPIADA")
                limpiadas += 1
        return limpiadas
    except Exception as e:
        print(f"[PCA] _limpiar_sanciones: {e}")
        return 0

def _get_reduccion_canje(user_id: int, personaje: str, tipo_sancion: str) -> str:
    """Devuelve texto con la reducción por canje activa si existe."""
    from utils.sheets import get_sheet
    try:
        rows = get_sheet("HistorialPC").get_all_records()
        canjes = [r for r in rows
                  if str(r.get("user_id","")) == str(user_id) and
                  r.get("personaje","").strip().lower() == personaje.strip().lower() and
                  f"Canje sanción: {tipo_sancion}" in r.get("motivo","")]
        if canjes:
            total = sum(abs(int(r.get("pc_otorgados",0))) for r in canjes)
            return f"🔄 Reducción por canje: **{total} PC** gastados"
    except Exception:
        pass
    return ""

<<<<<<< HEAD
async def _notificar_usuario(guild, user_id, embed):
    """Intenta enviar DM al usuario de forma segura. Usa get_member sin fetch para no bloquear."""
    try:
        member = guild.get_member(int(user_id))
        if member:
            await member.send(embed=embed)
        else:
            # fallback: fetch asíncrono solo si no está en caché
            try:
                member = await guild.fetch_member(int(user_id))
                await member.send(embed=embed)
            except Exception:
                pass
    except Exception as e:
        print(f"[PCA] DM error para {user_id}: {e}")
=======
def _tiene_autoridad(interaction: discord.Interaction) -> bool:
    return any(r.id in ROLES_AUTORIDAD_PC for r in interaction.user.roles)

def _es_staff(interaction: discord.Interaction) -> bool:
    return any(r.id == ROL_STAFF for r in interaction.user.roles)

def _es_profesor(interaction: discord.Interaction) -> bool:
    return any(r.id == ROL_PROFESOR for r in interaction.user.roles)

def _get_estudiantes(user_id: int) -> list[str]:
    try:
        return [p["personaje"] for p in get_personajes_usuario(user_id)
                if p["tipo"] == "estudiante"]
    except Exception:
        return []

def _nombre_sancion(tipo: str) -> str:
    return TIPOS_SANCION.get(tipo, {}).get("nombre", tipo)


# ──────────────────────────────────────────────
# VIEW BASE — Selector de usuario + personaje
# ──────────────────────────────────────────────

class UsuarioPersonajeView(discord.ui.View):
    """
    View reutilizable: primero selecciona usuario con @mention en el comando,
    luego muestra sus personajes estudiantes en un select desplegable.
    Al elegir personaje llama a self._on_personaje_elegido(interaction, personaje).
    """
    def __init__(self, user_id: int, personajes: list[str], timeout: int = 120):
        super().__init__(timeout=timeout)
        self.user_id   = user_id
        self.personajes = personajes

        select = discord.ui.Select(
            placeholder="🎓 Selecciona el personaje...",
            options=[discord.SelectOption(label=p, value=p) for p in personajes],
            min_values=1, max_values=1
        )
        select.callback = self._select_callback
        self.add_item(select)

    async def _select_callback(self, interaction: discord.Interaction):
        personaje = interaction.data["values"][0]
        await self._on_personaje_elegido(interaction, personaje)

    async def _on_personaje_elegido(self, interaction: discord.Interaction, personaje: str):
        """Override en subclases para manejar la acción específica."""
        pass
>>>>>>> parent of 5b6c5a7 (Fix3PCA)


# ──────────────────────────────────────────────
# COG
# ──────────────────────────────────────────────

class PCA(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── /asignar-pc-nota ──────────────────────

    @app_commands.command(name="asignar-pc-nota",
        description="[STAFF/PROF/CONSEJO] Asignar PC a un estudiante por nota académica (3.5-5.0).")
    @app_commands.describe(usuario="El usuario", nota="Nota entre 3.5 y 5.0 (ej: 4.5 o 4,5)",
                           motivo="Tarea o actividad calificada")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def asignar_pc_nota(self, interaction: discord.Interaction,
                               usuario: discord.Member, nota: str, motivo: str):
        if not _tiene_autoridad(interaction):
            await interaction.response.send_message("❌ Sin autoridad para asignar PC.", ephemeral=True)
            return
        try:
            nota_f = float(nota.replace(",", "."))
        except ValueError:
            await interaction.response.send_message("❌ Nota inválida. Ej: `4.5` o `4,5`.", ephemeral=True)
            return
        if not (1.0 <= nota_f <= 5.0):
            await interaction.response.send_message("❌ La nota debe estar entre 1.0 y 5.0.", ephemeral=True)
            return
        if not any(r.id == ROL_ESTUDIANTE for r in usuario.roles):
            await interaction.response.send_message(f"❌ {usuario.display_name} no es Estudiante.", ephemeral=True)
            return

        pc = calcular_pc_por_nota(nota_f)

        # Nota insuficiente — notificar al asignador Y al estudiante
        if pc == 0:
            await interaction.response.send_message(
                f"ℹ️ La nota **{nota_f}** es menor al mínimo aprobatorio (3.5). No se otorgan PC.",
                ephemeral=True)
            # Notificar al estudiante también
            try:
                await usuario.send(embed=discord.Embed(
                    title="📋 Calificación registrada",
                    description=(f"Se registró una nota de **{nota_f}** para uno de tus personajes.\n\n"
                                 f"**Motivo:** {motivo}\n\n"
                                 f"La nota mínima para obtener PC es **3.5**. "
                                 f"¡Sigue esforzándote! 💪"),
                    color=COLOR_PENDIENTE))
            except Exception: pass
            return

        estudiantes = _get_estudiantes(usuario.id)
        if not estudiantes:
            await interaction.response.send_message(
                f"❌ {usuario.display_name} no tiene personajes estudiantes.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        motivo_c = f"Nota académica {nota_f} — {motivo}"
        view = _AsignarPCView(user_id=usuario.id, username=str(usuario),
                               usuario_mention=usuario.mention, personajes=estudiantes,
                               pc=pc, motivo=motivo_c, asignado_por=str(interaction.user))
        embed = discord.Embed(title="🎓 Seleccionar personaje", color=COLOR_PENDIENTE,
            description=(f"**Usuario:** {usuario.mention}\n"
                         f"**Nota:** {nota_f} → **+{pc} PC**\n"
                         f"**Motivo:** {motivo}\n\nSelecciona el personaje:"))
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    # ── /asignar-pc-directo ───────────────────

    @app_commands.command(name="asignar-pc-directo",
        description="[STAFF/CONSEJO] Asignar PC directamente por Trabajo Sucio del Consejo (5-10).")
    @app_commands.describe(usuario="El usuario", pc="Cantidad de PC (5-10)",
                           motivo="Descripción del trabajo")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def asignar_pc_directo(self, interaction: discord.Interaction,
                                  usuario: discord.Member, pc: int, motivo: str):
        if not _tiene_autoridad(interaction):
            await interaction.response.send_message("❌ Sin autoridad.", ephemeral=True)
            return
        if not (PC_TRABAJO_SUCIO_MIN <= pc <= PC_TRABAJO_SUCIO_MAX):
            await interaction.response.send_message(
                f"❌ PC directos deben estar entre {PC_TRABAJO_SUCIO_MIN} y {PC_TRABAJO_SUCIO_MAX}.",
                ephemeral=True)
            return
        if not any(r.id == ROL_ESTUDIANTE for r in usuario.roles):
            await interaction.response.send_message(f"❌ {usuario.display_name} no es Estudiante.", ephemeral=True)
            return
        estudiantes = _get_estudiantes(usuario.id)
        if not estudiantes:
            await interaction.response.send_message(
                f"❌ {usuario.display_name} no tiene personajes estudiantes.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        motivo_c = f"Trabajo Sucio (Consejo) — {motivo}"
        view = _AsignarPCView(user_id=usuario.id, username=str(usuario),
                               usuario_mention=usuario.mention, personajes=estudiantes,
                               pc=pc, motivo=motivo_c, asignado_por=str(interaction.user))
        embed = discord.Embed(title="💎 Asignar PC directos", color=COLOR_PENDIENTE,
            description=(f"**Usuario:** {usuario.mention}\n**PC:** +{pc}\n"
                         f"**Motivo:** {motivo}\n\nSelecciona el personaje:"))
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    # ── /aplicar-sancion ──────────────────────

    @app_commands.command(name="aplicar-sancion",
        description="[STAFF/PROF/CONSEJO] Aplicar una sanción a un personaje estudiante.")
    @app_commands.describe(
        usuario="El usuario", tipo="Tipo de sanción", motivo="Motivo de la sanción",
        minutos="Duración en minutos de rol (castigo: 5-20, detención: 30-120)",
        dias="Duración en días IRL (solo suspensión: 2 o 3)")
    @app_commands.choices(tipo=[
        app_commands.Choice(name="⚠️ Castigo Menor (5-20 min de rol)",  value="castigo_menor"),
        app_commands.Choice(name="🔒 Detención (30-120 min de rol)",     value="detencion"),
        app_commands.Choice(name="🚫 Suspensión (2-3 días IRL)",         value="suspension"),
    ])
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def aplicar_sancion(self, interaction: discord.Interaction,
                               usuario: discord.Member, tipo: str, motivo: str,
                               minutos: int | None = None, dias: int | None = None):
        if not _tiene_autoridad(interaction):
            await interaction.response.send_message("❌ Sin autoridad.", ephemeral=True)
            return

        cfg = TIPOS_SANCION[tipo]
        if tipo in ("castigo_menor", "detencion"):
            if minutos is None:
                await interaction.response.send_message(
                    f"❌ Para {cfg['nombre']} indica `minutos` ({cfg['duracion_min']}-{cfg['duracion_max']} min).",
                    ephemeral=True)
                return
            if not (cfg["duracion_min"] <= minutos <= cfg["duracion_max"]):
                await interaction.response.send_message(
                    f"❌ Duración: {cfg['duracion_min']}-{cfg['duracion_max']} min.", ephemeral=True)
                return
            duracion, unidad = minutos, "minutos de rol"
        else:
            if dias is None:
                await interaction.response.send_message(
                    "❌ Para Suspensión indica `dias` (2 o 3).", ephemeral=True)
                return
            if not (cfg["duracion_min"] <= dias <= cfg["duracion_max"]):
                await interaction.response.send_message(
                    f"❌ Suspensión: {cfg['duracion_min']}-{cfg['duracion_max']} días.", ephemeral=True)
                return
            duracion, unidad = dias, "días IRL"

        if not any(r.id == ROL_ESTUDIANTE for r in usuario.roles):
            await interaction.response.send_message(f"❌ {usuario.display_name} no es Estudiante.", ephemeral=True)
            return
        estudiantes = _get_estudiantes(usuario.id)
        if not estudiantes:
            await interaction.response.send_message(
                f"❌ {usuario.display_name} no tiene personajes estudiantes.", ephemeral=True)
            return

<<<<<<< HEAD
        # Calcular requiere_aprobacion ANTES del defer (accede a interaction.user.roles)
        requiere_aprobacion = (_es_solo_profesor(interaction) and tipo == "detencion")
        if tipo == "expulsion":
            requiere_aprobacion = True
=======
        # Detención de profesor → requiere aprobación del staff
        es_solo_profesor = (_es_profesor(interaction) and not _es_staff(interaction)
                            and tipo == "detencion")
>>>>>>> parent of 5b6c5a7 (Fix3PCA)

        await interaction.response.defer(ephemeral=False)
        view = _AplicarSancionView(
            user_id=usuario.id, username=str(usuario),
            usuario_mention=usuario.mention, personajes=estudiantes,
            tipo=tipo, duracion=duracion, unidad=unidad,
            motivo=motivo, asignado_por=str(interaction.user),
            requiere_aprobacion=es_solo_profesor,
            bot=self.bot)
        embed = discord.Embed(
            title=f"⚠️ Aplicar sanción — {cfg['nombre']}",
            color=COLOR_RECHAZADO,
            description=(f"**Usuario:** {usuario.mention}\n"
                         f"**Duración:** {duracion} {unidad}\n"
                         f"**Motivo:** {motivo}\n\n"
                         f"{'⏳ *Esta detención requiere aprobación del Staff antes de aplicarse.*' if es_solo_profesor else ''}\n\n"
                         f"Selecciona el personaje sancionado:"))
        await interaction.followup.send(embed=embed, view=view)

    # ── /ver-pc @usuario ──────────────────────

    @app_commands.command(name="ver-pc",
        description="Ver el balance de PC y sanciones activas de un estudiante.")
<<<<<<< HEAD
    @app_commands.describe(usuario="El usuario a consultar (puedes mencionarte a ti mismo)")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def ver_pc(self, interaction: discord.Interaction,
                     usuario: discord.Member):
        if usuario.id != interaction.user.id and not _tiene_autoridad(interaction):
            await interaction.response.send_message("❌ Sin autoridad para ver PC de otros.", ephemeral=True); return

        estudiantes = _get_estudiantes(usuario.id)
        if not estudiantes:
            await interaction.response.send_message(
                f"❌ {usuario.display_name} no tiene personajes estudiantes registrados.", ephemeral=True); return

        await interaction.response.defer(ephemeral=True)
        view = _VerPCView(target_id=usuario.id, target_name=usuario.display_name,
                          target_avatar=str(usuario.display_avatar.url), personajes=estudiantes)
        await interaction.followup.send(
            embed=discord.Embed(title=f"🎓 Ver PC — {usuario.display_name}", color=COLOR_INFO,
                description="Selecciona el personaje a consultar:"),
            view=view, ephemeral=True)
=======
    @app_commands.describe(usuario="El usuario a consultar (deja vacío para verte a ti mismo)")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def ver_pc(self, interaction: discord.Interaction,
                     usuario: discord.Member | None = None):
        target = usuario or interaction.user
        if usuario and usuario != interaction.user and not _tiene_autoridad(interaction):
            await interaction.response.send_message("❌ Sin autoridad para ver PC de otros.", ephemeral=True)
            return

        estudiantes = _get_estudiantes(target.id)
        if not estudiantes:
            await interaction.response.send_message(
                f"❌ {target.display_name} no tiene personajes estudiantes registrados.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        view = _VerPCView(target_id=target.id, target_name=target.display_name,
                          target_avatar=target.display_avatar.url, personajes=estudiantes)
        embed = discord.Embed(title=f"🎓 Ver PC — {target.display_name}", color=COLOR_INFO,
            description="Selecciona el personaje a consultar:")
        embed.set_author(name=target.display_name, icon_url=target.display_avatar.url)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
>>>>>>> parent of 5b6c5a7 (Fix3PCA)

    # ── /historial-pc @usuario ────────────────

    @app_commands.command(name="historial-pc",
        description="Ver el historial de PC de un personaje estudiante.")
<<<<<<< HEAD
    @app_commands.describe(usuario="El usuario a consultar (puedes mencionarte a ti mismo)")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def historial_pc(self, interaction: discord.Interaction,
                            usuario: discord.Member):
        if usuario.id != interaction.user.id and not _tiene_autoridad(interaction):
            await interaction.response.send_message("❌ Sin autoridad.", ephemeral=True); return

        estudiantes = _get_estudiantes(usuario.id)
        if not estudiantes:
            await interaction.response.send_message(
                f"❌ {usuario.display_name} no tiene personajes estudiantes registrados.", ephemeral=True); return

        await interaction.response.defer(ephemeral=True)
        view = _HistorialPCView(target_id=usuario.id, target_name=usuario.display_name,
                                target_avatar=str(usuario.display_avatar.url), personajes=estudiantes)
        await interaction.followup.send(
            embed=discord.Embed(title=f"📋 Historial PC — {usuario.display_name}", color=COLOR_INFO,
                description="Selecciona el personaje:"),
            view=view, ephemeral=True)
=======
    @app_commands.describe(usuario="El usuario a consultar (deja vacío para verte a ti mismo)")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def historial_pc(self, interaction: discord.Interaction,
                            usuario: discord.Member | None = None):
        target = usuario or interaction.user
        if usuario and usuario != interaction.user and not _tiene_autoridad(interaction):
            await interaction.response.send_message("❌ Sin autoridad.", ephemeral=True)
            return

        estudiantes = _get_estudiantes(target.id)
        if not estudiantes:
            await interaction.response.send_message(
                f"❌ {target.display_name} no tiene personajes estudiantes registrados.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        view = _HistorialPCView(target_id=target.id, target_name=target.display_name,
                                target_avatar=target.display_avatar.url, personajes=estudiantes)
        embed = discord.Embed(title=f"📋 Historial PC — {target.display_name}", color=COLOR_INFO,
            description="Selecciona el personaje:")
        embed.set_author(name=target.display_name, icon_url=target.display_avatar.url)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
>>>>>>> parent of 5b6c5a7 (Fix3PCA)

    # ── /canjear-pc ───────────────────────────

    @app_commands.command(name="canjear-pc",
        description="Canjear tus PC para reducir una sanción activa.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def canjear_pc(self, interaction: discord.Interaction):
        estudiantes = _get_estudiantes(interaction.user.id)
        if not estudiantes:
            await interaction.response.send_message(
                "❌ No tienes personajes estudiantes registrados.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        view = _CanjeSelectPersonajeView(user_id=interaction.user.id, personajes=estudiantes,
                                          bot=self.bot)
        embed = discord.Embed(title="💎 Canjear PC", color=COLOR_INFO,
            description="Selecciona el personaje con el que quieres canjear:")
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    # ── /marcar-sancion-cumplida ──────────────

    @app_commands.command(name="marcar-sancion-cumplida",
        description="[STAFF/PROF/CONSEJO] Marcar una sanción como cumplida.")
    @app_commands.describe(usuario="El usuario dueño del personaje")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def marcar_sancion_cumplida(self, interaction: discord.Interaction,
                                       usuario: discord.Member):
        if not _tiene_autoridad(interaction):
            await interaction.response.send_message("❌ Sin autoridad.", ephemeral=True)
            return

        estudiantes = _get_estudiantes(usuario.id)
        if not estudiantes:
            await interaction.response.send_message(
                f"❌ {usuario.display_name} no tiene personajes estudiantes.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        view = _MarcarCumplidaSelectView(user_id=usuario.id, personajes=estudiantes)
        embed = discord.Embed(title=f"✅ Marcar sanción cumplida — {usuario.display_name}",
            description="Selecciona el personaje:", color=COLOR_PENDIENTE)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    # ── /limpiar-sanciones ────────────────────

    @app_commands.command(name="limpiar-sanciones",
        description="[STAFF] Limpiar todas las sanciones activas de un personaje.")
    @app_commands.describe(usuario="El usuario dueño del personaje")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def limpiar_sanciones(self, interaction: discord.Interaction, usuario: discord.Member):
        if not _es_staff(interaction):
            await interaction.response.send_message("❌ Solo el Staff puede.", ephemeral=True)
            return

        estudiantes = _get_estudiantes(usuario.id)
        if not estudiantes:
            await interaction.response.send_message(
                f"❌ {usuario.display_name} no tiene personajes estudiantes.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        view = _LimpiarSancionesView(user_id=usuario.id, personajes=estudiantes,
                                      staff_name=str(interaction.user))
        embed = discord.Embed(title=f"🧹 Limpiar sanciones — {usuario.display_name}",
            description="Selecciona el personaje:", color=COLOR_PENDIENTE)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    # ── /limpiar-pc ───────────────────────────

    @app_commands.command(name="limpiar-pc",
        description="[STAFF] Limpiar los PC de un personaje o de todos.")
    @app_commands.describe(modo="¿Limpiar uno o todos?",
                           usuario="(Si modo=personaje) Usuario dueño")
    @app_commands.choices(modo=[
        app_commands.Choice(name="Un personaje específico",              value="personaje"),
        app_commands.Choice(name="⚠️ TODOS los personajes del servidor", value="todos"),
    ])
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def limpiar_pc(self, interaction: discord.Interaction, modo: str,
                          usuario: discord.Member | None = None):
        if not _es_staff(interaction):
            await interaction.response.send_message("❌ Solo el Staff puede.", ephemeral=True)
            return

        if modo == "personaje":
            if not usuario:
                await interaction.response.send_message("❌ Debes indicar `usuario`.", ephemeral=True)
                return
            estudiantes = _get_estudiantes(usuario.id)
            if not estudiantes:
                await interaction.response.send_message(
                    f"❌ {usuario.display_name} no tiene personajes estudiantes.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            view = _LimpiarPCPersonajeView(user_id=usuario.id, personajes=estudiantes,
                                            staff_name=str(interaction.user))
            embed = discord.Embed(title=f"🧹 Limpiar PC — {usuario.display_name}",
                description="Selecciona el personaje:", color=COLOR_PENDIENTE)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            embed = discord.Embed(title="🚨 Confirmar limpieza TOTAL",
                description="Se resetearán los PC de **TODOS** los personajes a 0. ⚠️ No reversible.",
                color=COLOR_RECHAZADO)
            await interaction.response.send_message(
                embed=embed, view=_ConfirmarLimpiezaTotalView(str(interaction.user)), ephemeral=True)

    # ── /apelar ───────────────────────────────

    @app_commands.command(name="apelar",
        description="Apelar una suspensión o expulsión de uno de tus personajes.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def apelar(self, interaction: discord.Interaction):
        estudiantes = _get_estudiantes(interaction.user.id)
        if not estudiantes:
            await interaction.response.send_message(
                "❌ No tienes personajes estudiantes registrados.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        view = _ApelarSelectView(user_id=interaction.user.id, personajes=estudiantes,
                                  bot=self.bot)
        embed = discord.Embed(title="⚖️ Apelar sanción", color=COLOR_INFO,
            description=(
                "Selecciona el personaje que quieres defender.\n\n"
                "ℹ️ Solo puedes apelar **suspensiones** y **expulsiones**.\n"
                "La apelación será revisada por el Staff."))
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)


# ──────────────────────────────────────────────
# VIEWS ESPECÍFICAS
# ──────────────────────────────────────────────

class _AsignarPCView(discord.ui.View):
    def __init__(self, user_id, username, usuario_mention, personajes, pc, motivo, asignado_por):
        super().__init__(timeout=120)
        self.user_id         = user_id
        self.username        = username
        self.usuario_mention = usuario_mention
        self.pc              = pc
        self.motivo          = motivo
        self.asignado_por    = asignado_por
        select = discord.ui.Select(
            placeholder="🎓 Selecciona el personaje...",
            options=[discord.SelectOption(label=p, value=p) for p in personajes])
        select.callback = self._on_select
        self.add_item(select)

    async def _on_select(self, interaction: discord.Interaction):
        personaje = interaction.data["values"][0]
        _sumar_pc(self.user_id, self.username, personaje, self.pc, self.motivo, self.asignado_por)
        balance = _get_pc(self.user_id, personaje)

        embed = discord.Embed(title="✅ PC asignados", color=COLOR_APROBADO)
        embed.add_field(name="Personaje",    value=f"**{personaje}**",          inline=True)
        embed.add_field(name="Usuario",      value=self.usuario_mention,         inline=True)
        embed.add_field(name="PC otorgados", value=f"**+{self.pc} PC**",        inline=True)
        embed.add_field(name="Motivo",       value=self.motivo,                  inline=False)
        embed.add_field(name="Balance",
            value=f"Disponibles: **{balance['pc_disponible']} PC** | Total: **{balance['pc_total']} PC**",
            inline=False)
        embed.set_footer(text=f"Asignado por {self.asignado_por}")
        await interaction.response.edit_message(embed=embed, view=None)

        try:
            guild  = interaction.guild
            member = guild.get_member(self.user_id) or await guild.fetch_member(self.user_id)
            await member.send(embed=discord.Embed(
                title="🎓 ¡Recibiste Puntos de Canje Académico!",
                description=(f"Tu personaje **{personaje}** recibió **+{self.pc} PC**.\n\n"
                             f"**Motivo:** {self.motivo}\n\n"
                             f"Tienes **{balance['pc_disponible']} PC disponibles**.\n"
                             f"Úsalos con `/canjear-pc` para reducir sanciones."),
                color=COLOR_APROBADO))
        except Exception as e:
            print(f"[PCA] DM PC: {e}")
        self.stop()


class _AplicarSancionView(discord.ui.View):
    def __init__(self, user_id, username, usuario_mention, personajes,
                 tipo, duracion, unidad, motivo, asignado_por, requiere_aprobacion, bot):
        super().__init__(timeout=120)
        self.user_id              = user_id
        self.username             = username
        self.usuario_mention      = usuario_mention
        self.tipo                 = tipo
        self.duracion             = duracion
        self.unidad               = unidad
        self.motivo               = motivo
        self.asignado_por         = asignado_por
        self.requiere_aprobacion  = requiere_aprobacion
        self.bot                  = bot
        select = discord.ui.Select(
            placeholder="🎓 Selecciona el personaje sancionado...",
            options=[discord.SelectOption(label=p, value=p) for p in personajes])
        select.callback = self._on_select
        self.add_item(select)

    async def _on_select(self, interaction: discord.Interaction):
        personaje = interaction.data["values"][0]
        cfg       = TIPOS_SANCION[self.tipo]

        if self.requiere_aprobacion:
            # Detención de profesor → enviar al canal de aprobaciones
            embed_log = discord.Embed(
                title="🔒 Solicitud de Detención — Requiere Aprobación",
                description=(
                    f"**Profesor:** {self.asignado_por}\n"
                    f"**Estudiante:** {self.usuario_mention}\n"
                    f"**Personaje:** {personaje}\n"
                    f"**Duración:** {self.duracion} {self.unidad}\n"
                    f"**Motivo:** {self.motivo}\n\n"
                    f"Un miembro del Staff o Consejo debe aprobar esta detención."
                ),
                color=COLOR_PENDIENTE
            )
            canal = self.bot.get_channel(CANAL_APROBACIONES)
            if canal:
                await canal.send(
                    embed=embed_log,
                    view=AprobacionSancionView(
                        user_id=self.user_id, username=self.username,
                        personaje=personaje, tipo=self.tipo,
                        duracion=self.duracion, unidad=self.unidad,
                        motivo=self.motivo, asignado_por=self.asignado_por,
                        bot=self.bot))
            embed = discord.Embed(
                title="⏳ Solicitud enviada al Staff",
                description=(f"Tu solicitud de detención para **{personaje}** "
                             f"fue enviada al Staff para aprobación.\n\n"
                             f"Recibirás una notificación cuando sea procesada."),
                color=COLOR_PENDIENTE)
            await interaction.response.edit_message(embed=embed, view=None)
        else:
            # Aplicar directamente
            _registrar_sancion(self.user_id, self.username, personaje,
                               self.tipo, self.duracion, self.motivo, self.asignado_por)
            embed = discord.Embed(title=f"⚠️ Sanción aplicada — {cfg['nombre']}", color=COLOR_RECHAZADO)
            embed.add_field(name="Personaje", value=f"**{personaje}**",                inline=True)
            embed.add_field(name="Usuario",   value=self.usuario_mention,              inline=True)
            embed.add_field(name="Duración",  value=f"**{self.duracion} {self.unidad}**", inline=True)
            embed.add_field(name="Motivo",    value=self.motivo,                       inline=False)
            embed.add_field(name="💡 Canje",
                value=f"El estudiante puede usar `/canjear-pc` para reducir con PC.", inline=False)
            embed.set_footer(text=f"Aplicado por {self.asignado_por}")
            await interaction.response.edit_message(embed=embed, view=None)
            try:
                guild  = interaction.guild
                member = guild.get_member(self.user_id) or await guild.fetch_member(self.user_id)
                await member.send(embed=discord.Embed(
                    title=f"⚠️ Sanción recibida — {cfg['nombre']}",
                    description=(f"Tu personaje **{personaje}** recibió una sanción.\n\n"
                                 f"**Duración:** {self.duracion} {self.unidad}\n"
                                 f"**Motivo:** {self.motivo}\n\n"
                                 f"Usa `/canjear-pc` para reducir con tus PC."),
                    color=COLOR_RECHAZADO))
            except Exception as e:
                print(f"[PCA] DM sancion: {e}")
        self.stop()


class _VerPCView(discord.ui.View):
    def __init__(self, target_id, target_name, target_avatar, personajes):
        super().__init__(timeout=120)
        self.target_id     = target_id
        self.target_name   = target_name
        self.target_avatar = target_avatar
        select = discord.ui.Select(
            placeholder="🎓 Selecciona el personaje...",
            options=[discord.SelectOption(label=p, value=p) for p in personajes])
        select.callback = self._on_select
        self.add_item(select)

    async def _on_select(self, interaction: discord.Interaction):
        personaje = interaction.data["values"][0]
        balance   = _get_pc(self.target_id, personaje)
        sanciones = _get_sanciones_activas(self.target_id, personaje)

        embed = discord.Embed(title=f"🎓 PC de {personaje}", color=COLOR_INFO)
        embed.set_author(name=self.target_name, icon_url=self.target_avatar)
        embed.add_field(name="💎 Balance",
            value=(f"Disponibles: **{balance['pc_disponible']} PC**\n"
                   f"Total histórico: **{balance['pc_total']} PC**\n"
                   f"Gastados: **{balance['pc_total'] - balance['pc_disponible']} PC**"),
            inline=False)

        if sanciones:
            lines = []
            for i, s in enumerate(sanciones):
                c  = TIPOS_SANCION.get(s.get("tipo",""), {})
                u  = "min" if s.get("tipo") != "suspension" else "días"
                rc = _get_reduccion_canje(self.target_id, personaje, c.get("nombre",""))
                line = f"**{i+1}.** {c.get('nombre','?')} — **{s.get('duracion','?')} {u}** *(por {s.get('asignado_por','?')})*"
                if rc: line += f"\n   {rc}"
                lines.append(line)
            embed.add_field(name="⚠️ Sanciones activas", value="\n".join(lines), inline=False)
            embed.add_field(name="💡 Reducir", value="Usa `/canjear-pc` para gastar PC.", inline=False)
        else:
            embed.add_field(name="✅ Sanciones activas", value="Ninguna", inline=False)

        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()


class _HistorialPCView(discord.ui.View):
    def __init__(self, target_id, target_name, target_avatar, personajes):
        super().__init__(timeout=120)
        self.target_id     = target_id
        self.target_name   = target_name
        self.target_avatar = target_avatar
        select = discord.ui.Select(
            placeholder="🎓 Selecciona el personaje...",
            options=[discord.SelectOption(label=p, value=p) for p in personajes])
        select.callback = self._on_select
        self.add_item(select)

    async def _on_select(self, interaction: discord.Interaction):
        personaje = interaction.data["values"][0]
        from utils.sheets import get_sheet
        try:
            rows = get_sheet("HistorialPC").get_all_records()
            hist = [r for r in rows
                    if str(r.get("user_id","")) == str(self.target_id) and
                    r.get("personaje","").strip().lower() == personaje.strip().lower()]
        except Exception as e:
            hist = []
            print(f"[PCA] historial: {e}")

        if not hist:
            await interaction.response.edit_message(
                content=f"ℹ️ **{personaje}** no tiene historial de PC aún.", embed=None, view=None)
            return

        embed = discord.Embed(title=f"📋 Historial PC — {personaje}", color=COLOR_INFO)
        embed.set_author(name=self.target_name, icon_url=self.target_avatar)
        lines = []
        for r in hist[-15:]:
            cant   = r.get("pc_otorgados","?")
            prefix = "+" if str(cant).lstrip("-").replace(".","").isdigit() and float(str(cant)) > 0 else ""
            lines.append(f"`{prefix}{cant} PC` — {r.get('motivo','?')} *(por {r.get('asignado_por','?')} · {r.get('fecha','?')})*")
        embed.description = "\n".join(lines)
        if len(hist) > 15:
            embed.set_footer(text=f"Últimos 15 de {len(hist)} registros.")
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()


class _CanjeSelectPersonajeView(discord.ui.View):
    def __init__(self, user_id, personajes, bot):
        super().__init__(timeout=120)
        self.user_id   = user_id
        self.personajes = personajes
        self.bot       = bot
        select = discord.ui.Select(
            placeholder="🎓 Selecciona el personaje...",
            options=[discord.SelectOption(label=p, value=p) for p in personajes])
        select.callback = self._on_select
        self.add_item(select)

    async def _on_select(self, interaction: discord.Interaction):
        personaje = interaction.data["values"][0]
        sanciones = _get_sanciones_activas(self.user_id, personaje)
        if not sanciones:
            await interaction.response.edit_message(
                content=f"✅ **{personaje}** no tiene sanciones activas.", embed=None, view=None)
            return
        balance = _get_pc(self.user_id, personaje)
        if balance["pc_disponible"] == 0:
            await interaction.response.edit_message(
                content=f"❌ **{personaje}** no tiene PC disponibles.", embed=None, view=None)
            return
        view  = CanjeView(self.user_id, personaje, sanciones, balance, self.bot)
        await interaction.response.edit_message(embed=view.build_embed(), view=view)
        self.stop()


class _MarcarCumplidaSelectView(discord.ui.View):
    def __init__(self, user_id, personajes):
        super().__init__(timeout=120)
        self.user_id  = user_id
        select = discord.ui.Select(
            placeholder="🎓 Selecciona el personaje...",
            options=[discord.SelectOption(label=p, value=p) for p in personajes])
        select.callback = self._on_select
        self.add_item(select)

    async def _on_select(self, interaction: discord.Interaction):
        personaje = interaction.data["values"][0]
        sanciones = _get_sanciones_activas(self.user_id, personaje)
        if not sanciones:
            await interaction.response.edit_message(
                content=f"✅ **{personaje}** no tiene sanciones activas.", embed=None, view=None)
            return
        view = MarcarCumplidaView(self.user_id, personaje, sanciones)
        await interaction.response.edit_message(embed=view.build_embed(), view=view)
        self.stop()


class _LimpiarSancionesView(discord.ui.View):
    def __init__(self, user_id, personajes, staff_name):
        super().__init__(timeout=120)
        self.user_id    = user_id
        self.staff_name = staff_name
        select = discord.ui.Select(
            placeholder="🎓 Selecciona el personaje...",
            options=[discord.SelectOption(label=p, value=p) for p in personajes])
        select.callback = self._on_select
        self.add_item(select)

    async def _on_select(self, interaction: discord.Interaction):
        personaje = interaction.data["values"][0]
        n = _limpiar_sanciones_personaje(self.user_id, personaje)
        embed = discord.Embed(title="🧹 Sanciones limpiadas",
            description=f"**{n}** sanción(es) activa(s) de **{personaje}** limpiadas.",
            color=COLOR_APROBADO)
        embed.set_footer(text=f"Por {self.staff_name}")
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()


class _LimpiarPCPersonajeView(discord.ui.View):
    def __init__(self, user_id, personajes, staff_name):
        super().__init__(timeout=120)
        self.user_id    = user_id
        self.staff_name = staff_name
        select = discord.ui.Select(
            placeholder="🎓 Selecciona el personaje...",
            options=[discord.SelectOption(label=p, value=p) for p in personajes])
        select.callback = self._on_select
        self.add_item(select)

    async def _on_select(self, interaction: discord.Interaction):
        personaje = interaction.data["values"][0]
        embed = discord.Embed(title="⚠️ Confirmar limpieza de PC",
            description=f"¿Resetear los PC de **{personaje}** a 0? No reversible.",
            color=COLOR_PENDIENTE)
        view = _ConfirmarLimpiezaUnoView(self.user_id, personaje, self.staff_name)
        await interaction.response.edit_message(embed=embed, view=view)
        self.stop()


class _ConfirmarLimpiezaUnoView(discord.ui.View):
    def __init__(self, user_id, personaje, staff_name):
        super().__init__(timeout=60)
        self.user_id    = user_id
        self.personaje  = personaje
        self.staff_name = staff_name

    @discord.ui.button(label="✅ Confirmar", style=discord.ButtonStyle.danger)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        ok = _limpiar_pc_personaje(self.user_id, self.personaje)
        embed = discord.Embed(title="🧹 PC limpiados",
            description=f"PC de **{self.personaje}** reseteados a 0.\n{'✅ OK' if ok else '⚠️ No encontrado.'}",
            color=COLOR_APROBADO if ok else COLOR_RECHAZADO)
        embed.set_footer(text=f"Por {self.staff_name}")
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Cancelado.", embed=None, view=None)
        self.stop()


class _ConfirmarLimpiezaTotalView(discord.ui.View):
    def __init__(self, staff_name):
        super().__init__(timeout=60)
        self.staff_name = staff_name

    @discord.ui.button(label="✅ Confirmar", style=discord.ButtonStyle.danger)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        ok = _limpiar_pc_todos()
        embed = discord.Embed(title="🧹 PC limpiados — TODOS",
            description="PC de todos reseteados a 0." if ok else "⚠️ Error.",
            color=COLOR_APROBADO if ok else COLOR_RECHAZADO)
        embed.set_footer(text=f"Por {self.staff_name}")
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Cancelado.", embed=None, view=None)
        self.stop()


# ──────────────────────────────────────────────
# VIEW — Aprobación de detención / reducción en canal de logs
# ──────────────────────────────────────────────

class AprobacionSancionView(discord.ui.View):
    """Botones que aparecen en el canal de logs para aprobar/rechazar detenciones de profesores
    y reducciones de suspensión por canje."""

    def __init__(self, user_id, username, personaje, tipo, duracion, unidad,
                 motivo, asignado_por, bot, es_canje=False, pc_canje=0):
        super().__init__(timeout=None)
        self.user_id      = user_id
        self.username     = username
        self.personaje    = personaje
        self.tipo         = tipo
        self.duracion     = duracion
        self.unidad       = unidad
        self.motivo       = motivo
        self.asignado_por = asignado_por
        self.bot          = bot
        self.es_canje     = es_canje
        self.pc_canje     = pc_canje

    @discord.ui.button(label="✅ Aprobar", style=discord.ButtonStyle.success)
    async def aprobar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(r.id in [ROL_STAFF] for r in interaction.user.roles):
            await interaction.response.send_message("❌ Solo el Staff puede aprobar.", ephemeral=True)
            return

        if self.es_canje:
            # Aprobar reducción de suspensión
            ok = _restar_pc(self.user_id, self.personaje, self.pc_canje)
            try:
                from utils.sheets import get_sheet
                get_sheet("HistorialPC").append_row(
                    [str(self.user_id), self.personaje, f"-{self.pc_canje}",
                     f"Canje sanción aprobado: {_nombre_sancion(self.tipo)}",
                     str(interaction.user), _now()],
                    value_input_option="USER_ENTERED")
            except Exception: pass
            desc = (f"Reducción de **{self.duracion}** aplicada a **{self.personaje}**.\n"
                    f"PC descontados: **{self.pc_canje}**")
        else:
            # Aprobar detención
            _registrar_sancion(self.user_id, self.username, self.personaje,
                               self.tipo, self.duracion, self.motivo, self.asignado_por)
            desc = f"Detención de **{self.duracion} {self.unidad}** aplicada a **{self.personaje}**."

        embed = discord.Embed(title="✅ Aprobado", description=desc, color=COLOR_APROBADO)
        embed.set_footer(text=f"Aprobado por {interaction.user.display_name}")
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message("✅ Procesado.", ephemeral=True)

        # Notificar al estudiante
        try:
            guild  = interaction.guild
            member = guild.get_member(self.user_id) or await guild.fetch_member(self.user_id)
            await member.send(embed=discord.Embed(
                title="⚠️ Sanción aplicada" if not self.es_canje else "✅ Reducción aprobada",
                description=(
                    f"Tu personaje **{self.personaje}** recibió una **{_nombre_sancion(self.tipo)}**.\n\n"
                    f"**Duración:** {self.duracion} {self.unidad}\n"
                    f"**Motivo:** {self.motivo}"
                ) if not self.es_canje else (
                    f"La reducción de sanción para **{self.personaje}** fue aprobada por el Staff.\n\n"
                    f"PC descontados: **{self.pc_canje}**"
                ),
                color=COLOR_RECHAZADO if not self.es_canje else COLOR_APROBADO))
        except Exception: pass
        self.stop()

    @discord.ui.button(label="❌ Rechazar", style=discord.ButtonStyle.danger)
    async def rechazar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(r.id in [ROL_STAFF] for r in interaction.user.roles):
            await interaction.response.send_message("❌ Solo el Staff puede rechazar.", ephemeral=True)
            return
        await interaction.response.send_modal(
            _MotivoRechazoAprobacionModal(
                user_id=self.user_id, personaje=self.personaje,
                tipo=self.tipo, message=interaction.message,
                es_canje=self.es_canje))

    @discord.ui.button(label="🎫 Abrir ticket", style=discord.ButtonStyle.secondary)
    async def abrir_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🎫 Ticket solicitado",
            description=(
                f"El Staff ha solicitado abrir un ticket para tratar este caso.\n\n"
                f"**Personaje:** {self.personaje}\n"
                f"**Tipo:** {_nombre_sancion(self.tipo)}\n"
                f"**Motivo original:** {self.motivo}\n\n"
                f"Por favor abre un ticket usando el sistema de tickets del servidor "
                f"para continuar con la conciliación."
            ),
            color=COLOR_INFO
        )
        embed.set_footer(text=f"Solicitado por {interaction.user.display_name}")
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message(
            "✅ Se notificó al estudiante que debe abrir un ticket.", ephemeral=True)

        try:
            guild  = interaction.guild
            member = guild.get_member(self.user_id) or await guild.fetch_member(self.user_id)
            await member.send(embed=discord.Embed(
                title="🎫 Se requiere un ticket para tu caso",
                description=(
                    f"El Staff necesita más contexto sobre el caso de **{self.personaje}**.\n\n"
                    f"Por favor **abre un ticket** en el servidor usando el sistema de tickets "
                    f"para continuar con la revisión de tu sanción."
                ),
                color=COLOR_INFO))
        except Exception: pass
        self.stop()


class _MotivoRechazoAprobacionModal(discord.ui.Modal, title="❌ Motivo de rechazo"):
    motivo = discord.ui.TextInput(label="Motivo", style=discord.TextStyle.paragraph,
                                   placeholder="Explica por qué se rechaza...",
                                   required=False, max_length=500)

    def __init__(self, user_id, personaje, tipo, message, es_canje):
        super().__init__()
        self.user_id  = user_id
        self.personaje = personaje
        self.tipo     = tipo
        self.message  = message
        self.es_canje = es_canje

    async def on_submit(self, interaction: discord.Interaction):
        m = self.motivo.value.strip() or "Sin motivo especificado."
        embed = discord.Embed(
            title="❌ Rechazado",
            description=(f"**Personaje:** {self.personaje}\n"
                         f"**Tipo:** {_nombre_sancion(self.tipo)}\n"
                         f"**Motivo del rechazo:** {m}"),
            color=COLOR_RECHAZADO)
        embed.set_footer(text=f"Rechazado por {interaction.user.display_name}")
        await self.message.edit(embed=embed, view=None)
        await interaction.response.send_message("✅ Rechazado.", ephemeral=True)

        try:
            guild  = interaction.guild
            member = guild.get_member(self.user_id) or await guild.fetch_member(self.user_id)
            await member.send(embed=discord.Embed(
                title="❌ Solicitud rechazada",
                description=(
                    f"La {'reducción de sanción' if self.es_canje else 'detención'} "
                    f"para **{self.personaje}** fue rechazada por el Staff.\n\n"
                    f"**Motivo:** {m}"
                ),
                color=COLOR_RECHAZADO))
        except Exception: pass


# ──────────────────────────────────────────────
# VIEW — Canje (con envío a aprobaciones si es suspensión)
# ──────────────────────────────────────────────

class CanjeView(discord.ui.View):
    def __init__(self, user_id, personaje, sanciones, balance, bot):
        super().__init__(timeout=120)
        self.user_id   = user_id
        self.personaje = personaje
        self.sanciones = sanciones
        self.balance   = balance
        self.bot       = bot
        self.idx       = 0
        select = discord.ui.Select(
            placeholder="📋 Selecciona la sanción a reducir...",
            options=[discord.SelectOption(
                label=f"{_nombre_sancion(s.get('tipo',''))} — {s.get('duracion','?')} {'min' if s.get('tipo') != 'suspension' else 'días'}",
                value=str(i)) for i, s in enumerate(sanciones)],
            min_values=1, max_values=1)
        select.callback = self._on_select
        self.add_item(select)

    async def _on_select(self, interaction: discord.Interaction):
        self.idx = int(interaction.data["values"][0])
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    def build_embed(self):
        s        = self.sanciones[self.idx]
        tipo     = s.get("tipo","castigo_menor")
        duracion = int(s.get("duracion", 20))
        unidad   = "min de rol" if tipo != "suspension" else "días IRL"
        disp     = self.balance["pc_disponible"]

        embed = discord.Embed(title=f"💎 Canjear PC — {self.personaje}", color=COLOR_INFO)
        embed.add_field(name="Sanción",
            value=f"**{_nombre_sancion(tipo)}** — {duracion} {unidad}\n*{s.get('motivo','?')}*", inline=False)
        embed.add_field(name="PC disponibles", value=f"**{disp} PC**", inline=True)

        if tipo == "castigo_menor":
            r1   = calcular_reduccion_castigo_menor(1, duracion)
            rmax = calcular_reduccion_castigo_menor(10, duracion)
            embed.add_field(name="📊 Opciones", value=(
                f"**1 PC** → quedan **{r1['tiempo_final']:.1f} min**\n"
                f"**10 PC** → quedan **{rmax['tiempo_final']:.1f} min** ✨ (bono incluido)"), inline=False)
        elif tipo == "detencion":
            pc_max = max(1, int(duracion * 0.8 / 2.5))
            r1     = calcular_reduccion_detencion(1, duracion)
            rmax   = calcular_reduccion_detencion(pc_max, duracion)
            embed.add_field(name="📊 Opciones", value=(
                f"**1 PC** → quedan **{r1['tiempo_final']:.1f} min**\n"
                f"**{pc_max} PC** (máx) → quedan **{rmax['tiempo_final']:.1f} min**"), inline=False)
        elif tipo == "suspension":
            embed.add_field(name="📊 Opciones", value=(
                "**20 PC** = 1 día menos *(requiere aprobación del Staff)*\n"
                "*Siempre queda al menos 1 día obligatorio.*"), inline=False)
        embed.set_footer(text="Ingresa cuántos PC gastar con el botón.")
        return embed

    @discord.ui.button(label="💎 Confirmar canje", style=discord.ButtonStyle.primary, row=1)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            ConfirmarCanjeModal(self.user_id, self.personaje,
                                self.sanciones[self.idx], self.idx, self.balance, self.bot))
        self.stop()

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary, row=1)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Cancelado.", embed=None, view=None)
        self.stop()


class ConfirmarCanjeModal(discord.ui.Modal, title="💎 ¿Cuántos PC gastar?"):
    pc_input = discord.ui.TextInput(label="PC a gastar (número)", placeholder="Ej: 5",
                                     min_length=1, max_length=3)

    def __init__(self, user_id, personaje, sancion, sancion_idx, balance, bot):
        super().__init__()
        self.user_id     = user_id
        self.personaje   = personaje
        self.sancion     = sancion
        self.sancion_idx = sancion_idx
        self.balance     = balance
        self.bot         = bot

    async def on_submit(self, interaction: discord.Interaction):
        try:
            pc = int(self.pc_input.value.strip())
            if pc < 1: raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ Número válido mayor a 0.", ephemeral=True)
            return

        disp = self.balance["pc_disponible"]
        if pc > disp:
            await interaction.response.send_message(
                f"❌ Solo tienes **{disp} PC** disponibles.", ephemeral=True)
            return

        tipo     = self.sancion.get("tipo","castigo_menor")
        duracion = int(self.sancion.get("duracion", 20))

        try:
            if tipo == "castigo_menor":
                r = calcular_reduccion_castigo_menor(pc, duracion)
                resumen  = (f"**{pc} PC** gastados\nReducción: **{r['minutos_reducidos']:.1f} min**"
                            f"{' + 1 bono ✨' if r['bonificacion'] else ''}\n"
                            f"Tiempo final: **{r['tiempo_final']:.1f} min de rol**")
                pc_usar  = pc
                necesita_aprobacion = False
            elif tipo == "detencion":
                r = calcular_reduccion_detencion(pc, duracion)
                resumen  = (f"**{pc} PC** gastados\nReducción: **{r['minutos_reducidos']:.1f} min**\n"
                            f"Tiempo final: **{r['tiempo_final']:.1f} min de rol**")
                pc_usar  = pc
                necesita_aprobacion = False
            elif tipo == "suspension":
                r = calcular_reduccion_suspension(pc, duracion)
                if r["dias_reducidos"] == 0:
                    await interaction.response.send_message(
                        f"❌ Necesitas al menos **20 PC** para reducir 1 día. Tienes **{disp} PC**.",
                        ephemeral=True)
                    return
                resumen  = (f"**{r['pc_usados']} PC** serán descontados si el Staff aprueba.\n"
                            f"Reducción solicitada: **{r['dias_reducidos']} día(s)**\n"
                            f"Suspensión resultante: **{r['dias_final']} día(s) IRL**\n\n"
                            f"⏳ *Pendiente de autorización del Staff.*")
                pc_usar  = r["pc_usados"]
                necesita_aprobacion = True
            else:
                await interaction.response.send_message("❌ Tipo no reconocido.", ephemeral=True)
                return
        except Exception as e:
            print(f"[PCA] Cálculo canje: {e}")
            await interaction.response.send_message(
                "❌ Error al calcular el canje. Intenta de nuevo.", ephemeral=True)
            return

        if necesita_aprobacion:
            # Enviar solicitud al canal de aprobaciones
            canal = self.bot.get_channel(CANAL_APROBACIONES)
            if canal:
                embed_log = discord.Embed(
                    title="🔄 Solicitud de reducción de suspensión",
                    description=(
                        f"**Usuario:** <@{self.user_id}>\n"
                        f"**Personaje:** {self.personaje}\n"
                        f"**Suspensión actual:** {duracion} días IRL\n"
                        f"**Reducción solicitada:** {r['dias_reducidos']} día(s) (-{pc_usar} PC)\n"
                        f"**Suspensión resultante:** {r['dias_final']} día(s) IRL\n\n"
                        f"Un miembro del Staff debe aprobar esta reducción."
                    ),
                    color=COLOR_PENDIENTE
                )
                await canal.send(
                    embed=embed_log,
                    view=AprobacionSancionView(
                        user_id=self.user_id, username="",
                        personaje=self.personaje, tipo=tipo,
                        duracion=r["dias_reducidos"], unidad="días",
                        motivo="Canje de PC", asignado_por=str(interaction.user),
                        bot=self.bot, es_canje=True, pc_canje=pc_usar))
            embed = discord.Embed(title="⏳ Solicitud enviada", description=resumen, color=COLOR_PENDIENTE)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Aplicar directamente (castigo menor o detención)
        if not _restar_pc(self.user_id, self.personaje, pc_usar):
            await interaction.response.send_message(
                "❌ No se pudieron descontar los PC. Intenta de nuevo.", ephemeral=True)
            return

        try:
            from utils.sheets import get_sheet
            get_sheet("HistorialPC").append_row(
                [str(self.user_id), self.personaje, f"-{pc_usar}",
                 f"Canje sanción: {_nombre_sancion(tipo)}",
                 str(interaction.user), _now()],
                value_input_option="USER_ENTERED")
        except Exception as e:
            print(f"[PCA] Historial canje: {e}")

        balance_nuevo = _get_pc(self.user_id, self.personaje)
        embed = discord.Embed(title="✅ Canje procesado", description=resumen, color=COLOR_APROBADO)
        embed.add_field(name="Balance restante",
            value=f"**{balance_nuevo['pc_disponible']} PC** disponibles", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ──────────────────────────────────────────────
# VIEW — Marcar sanción cumplida
# ──────────────────────────────────────────────

class MarcarCumplidaView(discord.ui.View):
    def __init__(self, user_id, personaje, sanciones):
        super().__init__(timeout=120)
        self.user_id   = user_id
        self.personaje = personaje
        self.sanciones = sanciones
        self.idx       = 0
        select = discord.ui.Select(
            placeholder="📋 Selecciona la sanción cumplida...",
            options=[discord.SelectOption(
                label=f"{_nombre_sancion(s.get('tipo',''))} — {s.get('duracion','?')} {'min' if s.get('tipo') != 'suspension' else 'días'}",
                value=str(i), description=f"Por: {s.get('asignado_por','?')}")
                for i, s in enumerate(sanciones)],
            min_values=1, max_values=1)
        select.callback = self._on_select
        self.add_item(select)

    def build_embed(self):
        return discord.Embed(title=f"✅ Marcar sanción cumplida — {self.personaje}",
            description="Selecciona la sanción que fue cumplida:", color=COLOR_PENDIENTE)

    async def _on_select(self, interaction: discord.Interaction):
        self.idx = int(interaction.data["values"][0])
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="✅ Confirmar", style=discord.ButtonStyle.success, row=1)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        ok  = _marcar_sancion_cumplida(self.user_id, self.personaje, self.idx)
        s   = self.sanciones[self.idx]
        rc  = _get_reduccion_canje(self.user_id, self.personaje, _nombre_sancion(s.get("tipo","")))
        u   = "min" if s.get("tipo") != "suspension" else "días"
        desc = (f"**Personaje:** {self.personaje}\n"
                f"**Sanción:** {_nombre_sancion(s.get('tipo','?'))} — {s.get('duracion','?')} {u}\n"
                f"{rc}\n" if rc else "" +
                f"{'✅ Actualizado en Sheets.' if ok else '⚠️ Error actualizando.'}")
        embed = discord.Embed(title="✅ Sanción cumplida", description=desc,
            color=COLOR_APROBADO if ok else COLOR_RECHAZADO)
        embed.set_footer(text=f"Por {interaction.user.display_name}")
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary, row=1)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Cancelado.", embed=None, view=None)
        self.stop()


# ──────────────────────────────────────────────
# VIEW — Apelar sanción
# ──────────────────────────────────────────────

class _ApelarSelectView(discord.ui.View):
    def __init__(self, user_id, personajes, bot):
        super().__init__(timeout=120)
        self.user_id   = user_id
        self.bot       = bot
        select = discord.ui.Select(
            placeholder="🎓 Selecciona el personaje...",
            options=[discord.SelectOption(label=p, value=p) for p in personajes])
        select.callback = self._on_select
        self.add_item(select)

    async def _on_select(self, interaction: discord.Interaction):
        personaje = interaction.data["values"][0]
        # Buscar sanciones apelables (suspensión o expulsión)
        sanciones = _get_sanciones_activas(self.user_id, personaje)
        apelables = [s for s in sanciones if s.get("tipo") in ("suspension", "expulsion")]

        if not apelables:
            await interaction.response.edit_message(
                content=(f"ℹ️ **{personaje}** no tiene sanciones apelables activas.\n\n"
                         f"Solo se pueden apelar **suspensiones** y **expulsiones**."),
                embed=None, view=None)
            return

        view = _ApelarSancionView(user_id=self.user_id, personaje=personaje,
                                   sanciones=apelables, bot=self.bot)
        embed = discord.Embed(title=f"⚖️ Apelar — {personaje}",
            description="Selecciona la sanción que quieres apelar:", color=COLOR_INFO)
        await interaction.response.edit_message(embed=embed, view=view)
        self.stop()


class _ApelarSancionView(discord.ui.View):
    def __init__(self, user_id, personaje, sanciones, bot):
        super().__init__(timeout=120)
        self.user_id   = user_id
        self.personaje = personaje
        self.sanciones = sanciones
        self.bot       = bot
        self.idx       = 0
        select = discord.ui.Select(
            placeholder="📋 Selecciona la sanción a apelar...",
            options=[discord.SelectOption(
                label=f"{_nombre_sancion(s.get('tipo',''))} — {s.get('duracion','?')} {'días' if s.get('tipo') == 'suspension' else ''}",
                value=str(i)) for i, s in enumerate(sanciones)],
            min_values=1, max_values=1)
        select.callback = self._on_select
        self.add_item(select)

    async def _on_select(self, interaction: discord.Interaction):
        self.idx = int(interaction.data["values"][0])
        await interaction.response.edit_message(
            embed=discord.Embed(title=f"⚖️ Apelar — {self.personaje}",
                description="Selecciona la sanción y presiona **Apelar** para enviar tu argumento.",
                color=COLOR_INFO),
            view=self)

    @discord.ui.button(label="⚖️ Enviar apelación", style=discord.ButtonStyle.primary, row=1)
    async def apelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            _ApelarModal(user_id=self.user_id, personaje=self.personaje,
                         sancion=self.sanciones[self.idx], bot=self.bot))
        self.stop()

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary, row=1)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Cancelado.", embed=None, view=None)
        self.stop()


class _ApelarModal(discord.ui.Modal, title="⚖️ Apelación de sanción"):
    argumento = discord.ui.TextInput(
        label="¿Por qué apelas esta sanción?",
        style=discord.TextStyle.paragraph,
        placeholder="Explica tu caso detalladamente...",
        min_length=20, max_length=1000)

    def __init__(self, user_id, personaje, sancion, bot):
        super().__init__()
        self.user_id  = user_id
        self.personaje = personaje
        self.sancion  = sancion
        self.bot      = bot

    async def on_submit(self, interaction: discord.Interaction):
        tipo = self.sancion.get("tipo","suspension")
        u    = "días IRL" if tipo == "suspension" else ""

        # Enviar al canal de aprobaciones
        canal = self.bot.get_channel(CANAL_APROBACIONES)
        if canal:
            embed_log = discord.Embed(
                title="⚖️ Apelación de sanción",
                description=(
                    f"**Usuario:** <@{self.user_id}>\n"
                    f"**Personaje:** {self.personaje}\n"
                    f"**Sanción apelada:** {_nombre_sancion(tipo)} — "
                    f"{self.sancion.get('duracion','?')} {u}\n"
                    f"**Motivo original:** {self.sancion.get('motivo','?')}\n"
                    f"**Aplicada por:** {self.sancion.get('asignado_por','?')}\n\n"
                    f"**Argumento del estudiante:**\n{self.argumento.value}"
                ),
                color=COLOR_INFO
            )
            await canal.send(embed=embed_log, view=_ApelacionStaffView(
                user_id=self.user_id, personaje=self.personaje, sancion=self.sancion))

        await interaction.response.send_message(
            embed=discord.Embed(
                title="✅ Apelación enviada",
                description=(f"Tu apelación para **{self.personaje}** fue enviada al Staff.\n\n"
                             f"Recibirás una notificación cuando sea revisada."),
                color=COLOR_APROBADO),
            ephemeral=True)


class _ApelacionStaffView(discord.ui.View):
    def __init__(self, user_id, personaje, sancion):
        super().__init__(timeout=None)
        self.user_id   = user_id
        self.personaje = personaje
        self.sancion   = sancion

    @discord.ui.button(label="✅ Aceptar apelación", style=discord.ButtonStyle.success)
    async def aceptar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(r.id == ROL_STAFF for r in interaction.user.roles):
            await interaction.response.send_message("❌ Solo el Staff puede.", ephemeral=True)
            return
        _limpiar_sanciones_personaje(self.user_id, self.personaje)
        embed = discord.Embed(title="✅ Apelación aceptada",
            description=f"La sanción de **{self.personaje}** fue retirada.",
            color=COLOR_APROBADO)
        embed.set_footer(text=f"Por {interaction.user.display_name}")
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message("✅ Apelación aceptada.", ephemeral=True)
        try:
            guild  = interaction.guild
            member = guild.get_member(self.user_id) or await guild.fetch_member(self.user_id)
            await member.send(embed=discord.Embed(
                title="✅ Apelación aceptada",
                description=f"Tu apelación para **{self.personaje}** fue **aceptada** por el Staff.\n\nLa sanción ha sido retirada.",
                color=COLOR_APROBADO))
        except Exception: pass
        self.stop()

    @discord.ui.button(label="❌ Rechazar apelación", style=discord.ButtonStyle.danger)
    async def rechazar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(r.id == ROL_STAFF for r in interaction.user.roles):
            await interaction.response.send_message("❌ Solo el Staff puede.", ephemeral=True)
            return
        await interaction.response.send_modal(
            _MotivoRechazoApelacionModal(
                user_id=self.user_id, personaje=self.personaje, message=interaction.message))

    @discord.ui.button(label="🎫 Abrir ticket", style=discord.ButtonStyle.secondary)
    async def ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="🎫 Ticket requerido",
            description=f"El Staff requiere abrir un ticket para tratar la apelación de **{self.personaje}**.",
            color=COLOR_INFO)
        embed.set_footer(text=f"Por {interaction.user.display_name}")
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message("✅ Notificado.", ephemeral=True)
        try:
            guild  = interaction.guild
            member = guild.get_member(self.user_id) or await guild.fetch_member(self.user_id)
            await member.send(embed=discord.Embed(
                title="🎫 Se requiere un ticket para tu apelación",
                description=(f"El Staff necesita más contexto sobre la apelación de **{self.personaje}**.\n\n"
                             f"Por favor **abre un ticket** en el servidor para continuar."),
                color=COLOR_INFO))
        except Exception: pass
        self.stop()


class _MotivoRechazoApelacionModal(discord.ui.Modal, title="❌ Rechazar apelación"):
    motivo = discord.ui.TextInput(label="Motivo del rechazo", style=discord.TextStyle.paragraph,
                                   required=False, max_length=500)

    def __init__(self, user_id, personaje, message):
        super().__init__()
        self.user_id   = user_id
        self.personaje = personaje
        self.message   = message

    async def on_submit(self, interaction: discord.Interaction):
        m = self.motivo.value.strip() or "Sin motivo especificado."
        embed = discord.Embed(title="❌ Apelación rechazada",
            description=f"**Personaje:** {self.personaje}\n**Motivo:** {m}",
            color=COLOR_RECHAZADO)
        embed.set_footer(text=f"Por {interaction.user.display_name}")
        await self.message.edit(embed=embed, view=None)
        await interaction.response.send_message("✅ Rechazado.", ephemeral=True)
        try:
            guild  = interaction.guild
            member = guild.get_member(self.user_id) or await guild.fetch_member(self.user_id)
            await member.send(embed=discord.Embed(
                title="❌ Apelación rechazada",
                description=(f"Tu apelación para **{self.personaje}** fue **rechazada** por el Staff.\n\n"
                             f"**Motivo:** {m}"),
                color=COLOR_RECHAZADO))
        except Exception: pass


async def setup(bot):
    await bot.add_cog(PCA(bot))
