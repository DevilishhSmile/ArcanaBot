from __future__ import annotations
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

CANAL_APROBACIONES = 1490609417572323329


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _nombre_sancion(tipo: str) -> str:
    return TIPOS_SANCION.get(tipo, {}).get("nombre", tipo)

def _tiene_autoridad(interaction: discord.Interaction) -> bool:
    return any(r.id in ROLES_AUTORIDAD_PC for r in interaction.user.roles)

def _es_staff(interaction: discord.Interaction) -> bool:
    return any(r.id == ROL_STAFF for r in interaction.user.roles)

def _es_solo_profesor(interaction: discord.Interaction) -> bool:
    tiene_prof  = any(r.id == ROL_PROFESOR for r in interaction.user.roles)
    tiene_staff = any(r.id == ROL_STAFF for r in interaction.user.roles)
    return tiene_prof and not tiene_staff

def _get_estudiantes(user_id: int) -> list[str]:
    """Versión síncrona — solo usar fuera de comandos slash."""
    try:
        return [p["personaje"] for p in get_personajes_usuario(user_id)
                if p["tipo"] == "estudiante"]
    except Exception:
        return []

async def _get_estudiantes_async(bot, user_id: int) -> list[str]:
    """Versión async — usar en comandos slash para no bloquear el event loop."""
    import asyncio
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(None, get_personajes_usuario, user_id)
        return [p["personaje"] for p in result if p["tipo"] == "estudiante"]
    except Exception as e:
        print(f"[PCA] _get_estudiantes_async: {e}")
        return []

async def _log(bot, titulo: str, descripcion: str, color=None, footer: str = ""):
    """Envía un mensaje de log al canal de aprobaciones."""
    try:
        canal = bot.get_channel(CANAL_APROBACIONES)
        if not canal:
            canal = await bot.fetch_channel(CANAL_APROBACIONES)
        embed = discord.Embed(title=titulo, description=descripcion,
                              color=color or COLOR_INFO)
        if footer:
            embed.set_footer(text=footer)
        embed.timestamp = datetime.now()
        await canal.send(embed=embed)
    except Exception as e:
        print(f"[PCA] _log error: {e}")

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

def _sumar_pc(user_id, username, personaje, cantidad, motivo, asignado_por):
    from utils.sheets import get_sheet
    try:
        sheet = get_sheet("PuntosPC")
        rows  = sheet.get_all_values()
        found = False
        for i, row in enumerate(rows):
            if i == 0: continue
            if len(row) >= 3 and str(row[0]) == str(user_id) and \
               row[2].strip().lower() == personaje.strip().lower():
                sheet.update_cell(i+1, 4, int(row[3] or 0) + cantidad)
                sheet.update_cell(i+1, 5, int(row[4] or 0) + cantidad)
                sheet.update_cell(i+1, 6, _now())
                found = True; break
        if not found:
            sheet.append_row([str(user_id), username, personaje, cantidad, cantidad, _now()],
                             value_input_option="USER_ENTERED")
        get_sheet("HistorialPC").append_row(
            [str(user_id), personaje, cantidad, motivo, asignado_por, _now()],
            value_input_option="USER_ENTERED")
    except Exception as e:
        print(f"[PCA] _sumar_pc: {e}")

def _restar_pc(user_id, personaje, cantidad) -> bool:
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

def _limpiar_pc_personaje(user_id, personaje) -> bool:
    from utils.sheets import get_sheet
    try:
        sheet = get_sheet("PuntosPC")
        rows  = sheet.get_all_values()
        for i, row in enumerate(rows):
            if i == 0: continue
            if len(row) >= 3 and str(row[0]) == str(user_id) and \
               row[2].strip().lower() == personaje.strip().lower():
                sheet.update_cell(i+1, 4, 0); sheet.update_cell(i+1, 5, 0)
                sheet.update_cell(i+1, 6, _now()); return True
    except Exception as e:
        print(f"[PCA] _limpiar_pc_personaje: {e}")
    return False

def _limpiar_pc_todos() -> bool:
    from utils.sheets import get_sheet
    try:
        sheet = get_sheet("PuntosPC"); rows = sheet.get_all_values()
        for i, row in enumerate(rows):
            if i == 0 or len(row) < 5: continue
            sheet.update_cell(i+1, 4, 0); sheet.update_cell(i+1, 5, 0)
            sheet.update_cell(i+1, 6, _now())
        return True
    except Exception as e:
        print(f"[PCA] _limpiar_pc_todos: {e}"); return False

def _registrar_sancion(user_id, username, personaje, tipo, duracion, motivo, asignado_por):
    from utils.sheets import get_sheet
    try:
        get_sheet("Sanciones").append_row(
            [str(user_id), username, personaje, tipo, str(duracion),
             "ACTIVA", asignado_por, _now(), motivo],
            value_input_option="USER_ENTERED")
    except Exception as e:
        print(f"[PCA] _registrar_sancion: {e}")

def _get_sanciones_activas(user_id, personaje) -> list:
    from utils.sheets import get_sheet
    try:
        return [r for r in get_sheet("Sanciones").get_all_records()
                if str(r.get("user_id","")) == str(user_id) and
                r.get("personaje","").strip().lower() == personaje.strip().lower() and
                r.get("estado","").upper() == "ACTIVA"]
    except Exception as e:
        print(f"[PCA] _get_sanciones_activas: {e}"); return []

def _marcar_sancion_cumplida(user_id, personaje, indice) -> bool:
    from utils.sheets import get_sheet
    try:
        sheet = get_sheet("Sanciones"); rows = sheet.get_all_values(); count = 0
        for i, row in enumerate(rows):
            if i == 0: continue
            if (len(row) >= 6 and str(row[0]) == str(user_id) and
                    row[2].strip().lower() == personaje.strip().lower() and
                    row[5].upper() == "ACTIVA"):
                if count == indice:
                    sheet.update_cell(i+1, 6, "CUMPLIDA"); return True
                count += 1
    except Exception as e:
        print(f"[PCA] _marcar_cumplida: {e}")
    return False

def _limpiar_sanciones_personaje(user_id, personaje) -> int:
    from utils.sheets import get_sheet
    try:
        sheet = get_sheet("Sanciones"); rows = sheet.get_all_values(); n = 0
        for i, row in enumerate(rows):
            if i == 0: continue
            if (len(row) >= 6 and str(row[0]) == str(user_id) and
                    row[2].strip().lower() == personaje.strip().lower() and
                    row[5].upper() == "ACTIVA"):
                sheet.update_cell(i+1, 6, "LIMPIADA"); n += 1
        return n
    except Exception as e:
        print(f"[PCA] _limpiar_sanciones: {e}"); return 0

def _get_reduccion_canje(user_id, personaje, tipo_sancion) -> str:
    from utils.sheets import get_sheet
    try:
        rows   = get_sheet("HistorialPC").get_all_records()
        canjes = [r for r in rows
                  if str(r.get("user_id","")) == str(user_id) and
                  r.get("personaje","").strip().lower() == personaje.strip().lower() and
                  "Canje" in r.get("motivo","")]
        if canjes:
            total = sum(abs(int(str(r.get("pc_otorgados",0)).replace("-",""))) for r in canjes)
            return f"🔄 PC gastados en canje: **{total} PC**"
    except Exception: pass
    return ""

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


# ──────────────────────────────────────────────
# COG
# ──────────────────────────────────────────────

class PCA(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── /asignar-pc-nota ──────────────────────

    @app_commands.command(name="asignar-pc-nota",
        description="[STAFF/PROF/CONSEJO] Asignar PC por nota académica (3.5-5.0).")
    @app_commands.describe(usuario="El usuario estudiante", nota="Nota entre 3.5 y 5.0 (ej: 4.5 o 4,5)",
                           motivo="Tarea o actividad calificada")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def asignar_pc_nota(self, interaction: discord.Interaction,
                               usuario: discord.Member, nota: str, motivo: str):
        if not _tiene_autoridad(interaction):
            await interaction.response.send_message("❌ Sin autoridad.", ephemeral=True); return
        try:
            nota_f = float(nota.replace(",", "."))
        except ValueError:
            await interaction.response.send_message("❌ Nota inválida. Ej: `4.5`", ephemeral=True); return
        if not (1.0 <= nota_f <= 5.0):
            await interaction.response.send_message("❌ Nota entre 1.0 y 5.0.", ephemeral=True); return
        if not any(r.id == ROL_ESTUDIANTE for r in usuario.roles):
            await interaction.response.send_message(f"❌ {usuario.display_name} no es Estudiante.", ephemeral=True); return

        pc = calcular_pc_por_nota(nota_f)
        if pc == 0:
            await interaction.response.send_message(
                f"ℹ️ Nota **{nota_f}** menor al mínimo (3.5). No se otorgan PC.", ephemeral=True)
            await _notificar_usuario(interaction.guild, usuario.id, discord.Embed(
                title="📋 Calificación registrada",
                description=(f"Se registró una nota de **{nota_f}** para uno de tus personajes.\n\n"
                             f"**Motivo:** {motivo}\n\n"
                             f"La nota mínima para obtener PC es **3.5**. ¡Sigue adelante! 💪"),
                color=COLOR_PENDIENTE))
            return

        await interaction.response.defer(ephemeral=True)
        estudiantes = await _get_estudiantes_async(self.bot, usuario.id)
        if not estudiantes:
            await interaction.followup.send(
                f"❌ {usuario.display_name} no tiene personajes estudiantes.", ephemeral=True); return
        motivo_c = f"Nota académica {nota_f} — {motivo}"
        view = _AsignarPCView(user_id=usuario.id, username=str(usuario),
                               usuario_mention=usuario.mention, personajes=estudiantes,
                               pc=pc, motivo=motivo_c, asignado_por=str(interaction.user),
                               guild=interaction.guild)
        await interaction.followup.send(
            embed=discord.Embed(title="🎓 Seleccionar personaje", color=COLOR_PENDIENTE,
                description=f"**Usuario:** {usuario.mention}\n**Nota:** {nota_f} → **+{pc} PC**\n"
                            f"**Motivo:** {motivo}\n\nSelecciona el personaje:"),
            view=view, ephemeral=True)

    # ── /asignar-pc-directo ───────────────────

    @app_commands.command(name="asignar-pc-directo",
        description="[STAFF/CONSEJO] Asignar PC directamente — Trabajo Sucio del Consejo (5-10).")
    @app_commands.describe(usuario="El usuario estudiante", pc="Cantidad de PC (5-10)",
                           motivo="Descripción del trabajo")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def asignar_pc_directo(self, interaction: discord.Interaction,
                                  usuario: discord.Member, pc: int, motivo: str):
        if not _tiene_autoridad(interaction):
            await interaction.response.send_message("❌ Sin autoridad.", ephemeral=True); return
        if not (PC_TRABAJO_SUCIO_MIN <= pc <= PC_TRABAJO_SUCIO_MAX):
            await interaction.response.send_message(
                f"❌ PC directos entre {PC_TRABAJO_SUCIO_MIN} y {PC_TRABAJO_SUCIO_MAX}.", ephemeral=True); return
        if not any(r.id == ROL_ESTUDIANTE for r in usuario.roles):
            await interaction.response.send_message(f"❌ {usuario.display_name} no es Estudiante.", ephemeral=True); return
        await interaction.response.defer(ephemeral=True)
        estudiantes = await _get_estudiantes_async(self.bot, usuario.id)
        if not estudiantes:
            await interaction.followup.send(
                f"❌ {usuario.display_name} no tiene personajes estudiantes.", ephemeral=True); return
        motivo_c = f"Trabajo Sucio (Consejo) — {motivo}"
        view = _AsignarPCView(user_id=usuario.id, username=str(usuario),
                               usuario_mention=usuario.mention, personajes=estudiantes,
                               pc=pc, motivo=motivo_c, asignado_por=str(interaction.user),
                               guild=interaction.guild)
        await interaction.followup.send(
            embed=discord.Embed(title="💎 Asignar PC directos", color=COLOR_PENDIENTE,
                description=f"**Usuario:** {usuario.mention}\n**PC:** +{pc}\n"
                            f"**Motivo:** {motivo}\n\nSelecciona el personaje:"),
            view=view, ephemeral=True)

    # ── /aplicar-sancion ──────────────────────

    @app_commands.command(name="aplicar-sancion",
        description="[STAFF/PROF/CONSEJO] Aplicar una sanción a un personaje estudiante.")
    @app_commands.describe(
        usuario="El usuario estudiante", tipo="Tipo de sanción", motivo="Motivo",
        minutos="Duración en minutos de rol (castigo: 5-20, detención: 30-120)",
        dias="Duración en días IRL (solo suspensión: 2 o 3)")
    @app_commands.choices(tipo=[
        app_commands.Choice(name="⚠️ Castigo Menor (5-20 min de rol)",   value="castigo_menor"),
        app_commands.Choice(name="🔒 Detención (30-120 min de rol)",      value="detencion"),
        app_commands.Choice(name="🚫 Suspensión (2-3 días IRL)",          value="suspension"),
        app_commands.Choice(name="💀 Expulsión (solo Staff — irreversible)", value="expulsion"),
    ])
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def aplicar_sancion(self, interaction: discord.Interaction,
                               usuario: discord.Member, tipo: str, motivo: str,
                               minutos: int | None = None, dias: int | None = None):
        if not _tiene_autoridad(interaction):
            await interaction.response.send_message("❌ Sin autoridad.", ephemeral=True); return

        # Expulsión — solo Staff
        if tipo == "expulsion" and not _es_staff(interaction):
            await interaction.response.send_message(
                "❌ Solo el Staff puede aplicar expulsiones.", ephemeral=True); return

        cfg = TIPOS_SANCION.get(tipo, {})

        if tipo in ("castigo_menor", "detencion"):
            if minutos is None:
                await interaction.response.send_message(
                    f"❌ Para {cfg.get('nombre',tipo)} indica `minutos` "
                    f"({cfg.get('duracion_min',0)}-{cfg.get('duracion_max',0)} min).", ephemeral=True); return
            if tipo in TIPOS_SANCION and not (cfg["duracion_min"] <= minutos <= cfg["duracion_max"]):
                await interaction.response.send_message(
                    f"❌ Duración: {cfg['duracion_min']}-{cfg['duracion_max']} min.", ephemeral=True); return
            duracion, unidad = minutos, "minutos de rol"

        elif tipo == "suspension":
            if dias is None:
                await interaction.response.send_message(
                    "❌ Para Suspensión indica `dias` (2 o 3).", ephemeral=True); return
            if not (cfg["duracion_min"] <= dias <= cfg["duracion_max"]):
                await interaction.response.send_message(
                    f"❌ Suspensión: {cfg['duracion_min']}-{cfg['duracion_max']} días.", ephemeral=True); return
            duracion, unidad = dias, "días IRL"

        elif tipo == "expulsion":
            duracion, unidad = "Permanente", ""

        if not any(r.id == ROL_ESTUDIANTE for r in usuario.roles):
            await interaction.response.send_message(f"❌ {usuario.display_name} no es Estudiante.", ephemeral=True); return

        # No permitir aplicarse sanción a uno mismo
        if usuario.id == interaction.user.id:
            await interaction.response.send_message(
                "❌ No puedes aplicarte una sanción a ti mismo.", ephemeral=True); return

        # Calcular requiere_aprobacion ANTES del defer (accede a interaction.user.roles)
        requiere_aprobacion = (_es_solo_profesor(interaction) and tipo == "detencion")
        if tipo == "expulsion":
            requiere_aprobacion = True

        await interaction.response.defer(ephemeral=True)
        estudiantes = await _get_estudiantes_async(self.bot, usuario.id)
        if not estudiantes:
            await interaction.followup.send(
                f"❌ {usuario.display_name} no tiene personajes estudiantes.", ephemeral=True); return
        nombre_tipo = {"castigo_menor":"⚠️ Castigo Menor","detencion":"🔒 Detención",
                       "suspension":"🚫 Suspensión","expulsion":"💀 Expulsión"}.get(tipo, tipo)
        view = _AplicarSancionView(
            user_id=usuario.id, username=str(usuario),
            usuario_mention=usuario.mention, personajes=estudiantes,
            tipo=tipo, duracion=duracion, unidad=unidad,
            motivo=motivo, asignado_por=str(interaction.user),
            requiere_aprobacion=requiere_aprobacion, bot=self.bot)
        desc = (f"**Usuario:** {usuario.mention}\n"
                f"**Duración:** {duracion} {unidad}\n**Motivo:** {motivo}")
        if tipo == "expulsion":
            desc += "\n\n⚠️ **Esta acción es IRREVERSIBLE.** Requiere aprobación del Staff."
        elif requiere_aprobacion:
            desc += "\n\n⏳ *Esta detención requiere aprobación del Staff antes de aplicarse.*"
        desc += "\n\nSelecciona el personaje sancionado:"
        await interaction.followup.send(
            embed=discord.Embed(title=f"Aplicar sanción — {nombre_tipo}",
                                color=COLOR_RECHAZADO, description=desc),
            view=view, ephemeral=True)

    # ── /ver-pc ───────────────────────────────

    @app_commands.command(name="ver-pc",
        description="Ver el balance de PC y sanciones activas de un estudiante.")
    @app_commands.describe(usuario="El usuario a consultar (puedes mencionarte a ti mismo)")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def ver_pc(self, interaction: discord.Interaction,
                     usuario: discord.Member):
        if usuario.id != interaction.user.id and not _tiene_autoridad(interaction):
            await interaction.response.send_message("❌ Sin autoridad para ver PC de otros.", ephemeral=True); return

        await interaction.response.defer(ephemeral=True)
        estudiantes = await _get_estudiantes_async(self.bot, usuario.id)
        if not estudiantes:
            await interaction.followup.send(
                f"❌ {usuario.display_name} no tiene personajes estudiantes registrados.",
                ephemeral=True); return

        view = _VerPCView(target_id=usuario.id, target_name=usuario.display_name,
                          target_avatar=str(usuario.display_avatar.url), personajes=estudiantes)
        await interaction.followup.send(
            embed=discord.Embed(title=f"🎓 Ver PC — {usuario.display_name}", color=COLOR_INFO,
                description="Selecciona el personaje a consultar:"),
            view=view, ephemeral=True)

    # ── /historial-pc ─────────────────────────

    @app_commands.command(name="historial-pc",
        description="Ver el historial de PC de un personaje estudiante.")
    @app_commands.describe(usuario="El usuario a consultar (puedes mencionarte a ti mismo)")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def historial_pc(self, interaction: discord.Interaction,
                            usuario: discord.Member):
        if usuario.id != interaction.user.id and not _tiene_autoridad(interaction):
            await interaction.response.send_message("❌ Sin autoridad.", ephemeral=True); return

        await interaction.response.defer(ephemeral=True)
        estudiantes = await _get_estudiantes_async(self.bot, usuario.id)
        if not estudiantes:
            await interaction.followup.send(
                f"❌ {usuario.display_name} no tiene personajes estudiantes registrados.",
                ephemeral=True); return

        view = _HistorialPCView(target_id=usuario.id, target_name=usuario.display_name,
                                target_avatar=str(usuario.display_avatar.url), personajes=estudiantes)
        await interaction.followup.send(
            embed=discord.Embed(title=f"📋 Historial PC — {usuario.display_name}", color=COLOR_INFO,
                description="Selecciona el personaje:"),
            view=view, ephemeral=True)

    # ── /canjear-pc ───────────────────────────

    @app_commands.command(name="canjear-pc",
        description="Canjear tus PC para reducir una sanción activa.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def canjear_pc(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        estudiantes = await _get_estudiantes_async(self.bot, interaction.user.id)
        if not estudiantes:
            await interaction.followup.send(
                "❌ No tienes personajes estudiantes registrados.", ephemeral=True); return

        view = _CanjeSelectPersonajeView(user_id=interaction.user.id,
                                          personajes=estudiantes, bot=self.bot)
        await interaction.followup.send(
            embed=discord.Embed(title="💎 Canjear PC", color=COLOR_INFO,
                description="Selecciona el personaje con el que quieres canjear:"),
            view=view, ephemeral=True)

    # ── /marcar-sancion-cumplida ──────────────

    @app_commands.command(name="marcar-sancion-cumplida",
        description="[STAFF/PROF/CONSEJO] Marcar una sanción como cumplida.")
    @app_commands.describe(usuario="El usuario dueño del personaje")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def marcar_sancion_cumplida(self, interaction: discord.Interaction,
                                       usuario: discord.Member):
        if not _tiene_autoridad(interaction):
            await interaction.response.send_message("❌ Sin autoridad.", ephemeral=True); return
        await interaction.response.defer(ephemeral=True)
        estudiantes = await _get_estudiantes_async(self.bot, usuario.id)
        if not estudiantes:
            await interaction.followup.send(
                f"❌ {usuario.display_name} no tiene personajes estudiantes.", ephemeral=True); return
        view = _MarcarCumplidaSelectView(user_id=usuario.id, personajes=estudiantes,
                                          marcado_por=str(interaction.user), bot=self.bot)
        await interaction.followup.send(
            embed=discord.Embed(title=f"✅ Marcar sanción cumplida — {usuario.display_name}",
                description="Selecciona el personaje:", color=COLOR_PENDIENTE),
            view=view, ephemeral=True)

    # ── /limpiar-sanciones ────────────────────

    @app_commands.command(name="limpiar-sanciones",
        description="[STAFF] Limpiar todas las sanciones activas de un personaje.")
    @app_commands.describe(usuario="El usuario dueño del personaje")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def limpiar_sanciones(self, interaction: discord.Interaction, usuario: discord.Member):
        if not _es_staff(interaction):
            await interaction.response.send_message("❌ Solo el Staff puede.", ephemeral=True); return
        await interaction.response.defer(ephemeral=True)
        estudiantes = await _get_estudiantes_async(self.bot, usuario.id)
        if not estudiantes:
            await interaction.followup.send(
                f"❌ {usuario.display_name} no tiene personajes estudiantes.", ephemeral=True); return
        view = _LimpiarSancionesView(user_id=usuario.id, personajes=estudiantes,
                                      staff_name=str(interaction.user), bot=self.bot)
        await interaction.followup.send(
            embed=discord.Embed(title=f"🧹 Limpiar sanciones — {usuario.display_name}",
                description="Selecciona el personaje:", color=COLOR_PENDIENTE),
            view=view, ephemeral=True)

    # ── /limpiar-pc ───────────────────────────

    @app_commands.command(name="limpiar-pc",
        description="[STAFF] Limpiar los PC de un personaje o de todos.")
    @app_commands.describe(modo="¿Limpiar uno o todos?", usuario="(Si modo=personaje) Usuario dueño")
    @app_commands.choices(modo=[
        app_commands.Choice(name="Un personaje específico",              value="personaje"),
        app_commands.Choice(name="⚠️ TODOS los personajes del servidor", value="todos"),
    ])
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def limpiar_pc(self, interaction: discord.Interaction, modo: str,
                          usuario: discord.Member | None = None):
        if not _es_staff(interaction):
            await interaction.response.send_message("❌ Solo el Staff puede.", ephemeral=True); return
        if modo == "personaje":
            if not usuario:
                await interaction.response.send_message("❌ Debes indicar `usuario`.", ephemeral=True); return
            await interaction.response.defer(ephemeral=True)
            estudiantes = await _get_estudiantes_async(self.bot, usuario.id)
            if not estudiantes:
                await interaction.followup.send(
                    f"❌ {usuario.display_name} no tiene personajes estudiantes.", ephemeral=True); return
            view = _LimpiarPCPersonajeView(user_id=usuario.id, personajes=estudiantes,
                                            staff_name=str(interaction.user), bot=self.bot)
            await interaction.followup.send(
                embed=discord.Embed(title=f"🧹 Limpiar PC — {usuario.display_name}",
                    description="Selecciona el personaje:", color=COLOR_PENDIENTE),
                view=view, ephemeral=True)
        else:
            await interaction.response.send_message(
                embed=discord.Embed(title="🚨 Confirmar limpieza TOTAL",
                    description="Se resetearán los PC de **TODOS** a 0. ⚠️ No reversible.",
                    color=COLOR_RECHAZADO),
                view=_ConfirmarLimpiezaTotalView(str(interaction.user), self.bot),
                ephemeral=True)

    # ── /apelar ───────────────────────────────

    @app_commands.command(name="apelar",
        description="Apelar una suspensión o expulsión de uno de tus personajes.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def apelar(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        estudiantes = await _get_estudiantes_async(self.bot, interaction.user.id)
        if not estudiantes:
            await interaction.followup.send(
                "❌ No tienes personajes estudiantes registrados.", ephemeral=True); return
        view = _ApelarSelectView(user_id=interaction.user.id, personajes=estudiantes, bot=self.bot)
        await interaction.followup.send(
            embed=discord.Embed(title="⚖️ Apelar sanción", color=COLOR_INFO,
                description=("Selecciona el personaje.\n\n"
                             "ℹ️ Solo puedes apelar **suspensiones** y **expulsiones**.\n"
                             "El Staff revisará tu apelación.")),
            view=view, ephemeral=True)


# ──────────────────────────────────────────────
# VIEWS ESPECÍFICAS
# ──────────────────────────────────────────────

def _make_select(personajes, placeholder="🎓 Selecciona el personaje..."):
    return discord.ui.Select(
        placeholder=placeholder,
        options=[discord.SelectOption(label=p, value=p) for p in personajes],
        min_values=1, max_values=1)


class _AsignarPCView(discord.ui.View):
    def __init__(self, user_id, username, usuario_mention, personajes, pc, motivo, asignado_por, guild):
        super().__init__(timeout=120)
        self.user_id = user_id; self.username = username
        self.usuario_mention = usuario_mention; self.pc = pc
        self.motivo = motivo; self.asignado_por = asignado_por; self.guild = guild
        s = _make_select(personajes); s.callback = self._on; self.add_item(s)

    async def _on(self, interaction: discord.Interaction):
        personaje = interaction.data["values"][0]
        _sumar_pc(self.user_id, self.username, personaje, self.pc, self.motivo, self.asignado_por)
        b = _get_pc(self.user_id, personaje)
        embed = discord.Embed(title="✅ PC asignados", color=COLOR_APROBADO)
        embed.add_field(name="Personaje",    value=f"**{personaje}**",   inline=True)
        embed.add_field(name="Usuario",      value=self.usuario_mention, inline=True)
        embed.add_field(name="PC otorgados", value=f"**+{self.pc} PC**", inline=True)
        embed.add_field(name="Motivo",       value=self.motivo,          inline=False)
        embed.add_field(name="Balance",
            value=f"Disponibles: **{b['pc_disponible']} PC** | Total: **{b['pc_total']} PC**",
            inline=False)
        embed.set_footer(text=f"Asignado por {self.asignado_por}")
        await interaction.response.edit_message(embed=embed, view=None)
        await _notificar_usuario(self.guild, self.user_id, discord.Embed(
            title="🎓 ¡Recibiste Puntos de Canje Académico!",
            description=(f"Tu personaje **{personaje}** recibió **+{self.pc} PC**.\n\n"
                         f"**Motivo:** {self.motivo}\n\n"
                         f"Tienes **{b['pc_disponible']} PC disponibles**.\n"
                         f"Úsalos con `/canjear-pc` para reducir sanciones."),
            color=COLOR_APROBADO))
        self.stop()


class _AplicarSancionView(discord.ui.View):
    def __init__(self, user_id, username, usuario_mention, personajes, tipo,
                 duracion, unidad, motivo, asignado_por, requiere_aprobacion, bot):
        super().__init__(timeout=120)
        self.user_id = user_id; self.username = username
        self.usuario_mention = usuario_mention; self.tipo = tipo
        self.duracion = duracion; self.unidad = unidad; self.motivo = motivo
        self.asignado_por = asignado_por; self.requiere_aprobacion = requiere_aprobacion
        self.bot = bot
        s = _make_select(personajes, "🎓 Selecciona el personaje sancionado...")
        s.callback = self._on; self.add_item(s)

    async def _on(self, interaction: discord.Interaction):
        personaje = interaction.data["values"][0]
        cfg       = TIPOS_SANCION.get(self.tipo, {})

        if self.requiere_aprobacion:
            titulo_log = ("💀 Solicitud de EXPULSIÓN — Requiere Aprobación"
                          if self.tipo == "expulsion"
                          else "🔒 Solicitud de Detención — Requiere Aprobación")
            embed_log = discord.Embed(title=titulo_log, color=COLOR_PENDIENTE,
                description=(f"**Solicitado por:** {self.asignado_por}\n"
                             f"**Estudiante:** {self.usuario_mention}\n"
                             f"**Personaje:** {personaje}\n"
                             f"**Duración:** {self.duracion} {self.unidad}\n"
                             f"**Motivo:** {self.motivo}\n\n"
                             f"Un miembro del Staff debe aprobar esta sanción."))
            canal = self.bot.get_channel(CANAL_APROBACIONES)
            if canal:
                await canal.send(embed=embed_log,
                    view=AprobacionSancionView(
                        user_id=self.user_id, username=self.username,
                        personaje=personaje, tipo=self.tipo,
                        duracion=self.duracion, unidad=self.unidad,
                        motivo=self.motivo, asignado_por=self.asignado_por,
                        bot=self.bot))
            embed = discord.Embed(title="⏳ Solicitud enviada al Staff",
                description=(f"Tu solicitud para **{personaje}** fue enviada.\n"
                             f"Recibirás notificación cuando sea procesada."),
                color=COLOR_PENDIENTE)
        else:
            _registrar_sancion(self.user_id, self.username, personaje,
                               self.tipo, self.duracion, self.motivo, self.asignado_por)
            embed = discord.Embed(
                title=f"⚠️ Sanción aplicada — {cfg.get('nombre', self.tipo)}",
                color=COLOR_RECHAZADO)
            embed.add_field(name="Personaje", value=f"**{personaje}**",             inline=True)
            embed.add_field(name="Usuario",   value=self.usuario_mention,           inline=True)
            embed.add_field(name="Duración",  value=f"**{self.duracion} {self.unidad}**", inline=True)
            embed.add_field(name="Motivo",    value=self.motivo,                    inline=False)
            embed.add_field(name="💡 Canje",
                value="El estudiante puede usar `/canjear-pc` para reducir con PC.", inline=False)
            embed.set_footer(text=f"Aplicado por {self.asignado_por}")
            await _notificar_usuario(interaction.guild, self.user_id, discord.Embed(
                title=f"⚠️ Sanción recibida — {cfg.get('nombre', self.tipo)}",
                description=(f"Tu personaje **{personaje}** recibió una sanción.\n\n"
                             f"**Duración:** {self.duracion} {self.unidad}\n"
                             f"**Motivo:** {self.motivo}\n\n"
                             f"Usa `/canjear-pc` para reducir con tus PC."),
                color=COLOR_RECHAZADO))

        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()


class _VerPCView(discord.ui.View):
    def __init__(self, target_id, target_name, target_avatar, personajes):
        super().__init__(timeout=120)
        self.target_id = target_id; self.target_name = target_name
        self.target_avatar = target_avatar
        s = _make_select(personajes); s.callback = self._on; self.add_item(s)

    async def _on(self, interaction: discord.Interaction):
        personaje = interaction.data["values"][0]
        b         = _get_pc(self.target_id, personaje)
        sanciones = _get_sanciones_activas(self.target_id, personaje)
        embed = discord.Embed(title=f"🎓 PC de {personaje}", color=COLOR_INFO)
        embed.set_author(name=self.target_name, icon_url=self.target_avatar)
        embed.add_field(name="💎 Balance",
            value=(f"Disponibles: **{b['pc_disponible']} PC**\n"
                   f"Total histórico: **{b['pc_total']} PC**\n"
                   f"Gastados: **{b['pc_total'] - b['pc_disponible']} PC**"), inline=False)
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
            embed.add_field(name="💡 ¿Reducir?", value="Usa `/canjear-pc`", inline=False)
        else:
            embed.add_field(name="✅ Sanciones activas", value="Ninguna", inline=False)
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()


class _HistorialPCView(discord.ui.View):
    def __init__(self, target_id, target_name, target_avatar, personajes):
        super().__init__(timeout=120)
        self.target_id = target_id; self.target_name = target_name
        self.target_avatar = target_avatar
        s = _make_select(personajes); s.callback = self._on; self.add_item(s)

    async def _on(self, interaction: discord.Interaction):
        personaje = interaction.data["values"][0]
        from utils.sheets import get_sheet
        try:
            rows = get_sheet("HistorialPC").get_all_records()
            hist = [r for r in rows
                    if str(r.get("user_id","")) == str(self.target_id) and
                    r.get("personaje","").strip().lower() == personaje.strip().lower()]
        except Exception as e:
            hist = []; print(f"[PCA] historial: {e}")
        if not hist:
            await interaction.response.edit_message(
                content=f"ℹ️ **{personaje}** no tiene historial de PC aún.",
                embed=None, view=None); return
        embed = discord.Embed(title=f"📋 Historial PC — {personaje}", color=COLOR_INFO)
        embed.set_author(name=self.target_name, icon_url=self.target_avatar)
        lines = []
        for r in hist[-15:]:
            cant   = r.get("pc_otorgados","?")
            prefix = "+" if str(cant).lstrip("-").replace(".","").isdigit() and float(str(cant)) > 0 else ""
            lines.append(f"`{prefix}{cant} PC` — {r.get('motivo','?')} *(por {r.get('asignado_por','?')} · {r.get('fecha','?')})*")
        embed.description = "\n".join(lines)
        if len(hist) > 15: embed.set_footer(text=f"Últimos 15 de {len(hist)}.")
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()


class _CanjeSelectPersonajeView(discord.ui.View):
    def __init__(self, user_id, personajes, bot):
        super().__init__(timeout=120)
        self.user_id = user_id; self.bot = bot
        s = _make_select(personajes); s.callback = self._on; self.add_item(s)

    async def _on(self, interaction: discord.Interaction):
        personaje = interaction.data["values"][0]
        sanciones = _get_sanciones_activas(self.user_id, personaje)
        if not sanciones:
            await interaction.response.edit_message(
                content=f"✅ **{personaje}** no tiene sanciones activas.",
                embed=None, view=None); return
        balance = _get_pc(self.user_id, personaje)
        if balance["pc_disponible"] == 0:
            await interaction.response.edit_message(
                content=f"❌ **{personaje}** no tiene PC disponibles.",
                embed=None, view=None); return
        view = CanjeView(self.user_id, personaje, sanciones, balance, self.bot)
        await interaction.response.edit_message(embed=view.build_embed(), view=view)
        self.stop()


class _MarcarCumplidaSelectView(discord.ui.View):
    def __init__(self, user_id, personajes, marcado_por, bot):
        super().__init__(timeout=120)
        self.user_id = user_id; self.marcado_por = marcado_por; self.bot = bot
        s = _make_select(personajes); s.callback = self._on; self.add_item(s)

    async def _on(self, interaction: discord.Interaction):
        personaje = interaction.data["values"][0]
        sanciones = _get_sanciones_activas(self.user_id, personaje)
        if not sanciones:
            await interaction.response.edit_message(
                content=f"✅ **{personaje}** no tiene sanciones activas.",
                embed=None, view=None); return
        view = MarcarCumplidaView(self.user_id, personaje, sanciones,
                                   self.marcado_por, self.bot)
        await interaction.response.edit_message(embed=view.build_embed(), view=view)
        self.stop()


class _LimpiarSancionesView(discord.ui.View):
    def __init__(self, user_id, personajes, staff_name, bot):
        super().__init__(timeout=120)
        self.user_id = user_id; self.staff_name = staff_name; self.bot = bot
        s = _make_select(personajes); s.callback = self._on; self.add_item(s)

    async def _on(self, interaction: discord.Interaction):
        personaje = interaction.data["values"][0]
        n = _limpiar_sanciones_personaje(self.user_id, personaje)
        embed = discord.Embed(title="🧹 Sanciones limpiadas",
            description=f"**{n}** sanción(es) activa(s) de **{personaje}** limpiadas.",
            color=COLOR_APROBADO)
        embed.set_footer(text=f"Por {self.staff_name}")
        await interaction.response.edit_message(embed=embed, view=None)
        # Log
        await _log(self.bot, "🧹 Sanciones limpiadas",
            f"**Personaje:** {personaje}\n**Sanciones limpiadas:** {n}\n**Por:** {self.staff_name}",
            COLOR_INFO, footer=self.staff_name)
        self.stop()


class _LimpiarPCPersonajeView(discord.ui.View):
    def __init__(self, user_id, personajes, staff_name, bot):
        super().__init__(timeout=120)
        self.user_id = user_id; self.staff_name = staff_name; self.bot = bot
        s = _make_select(personajes); s.callback = self._on; self.add_item(s)

    async def _on(self, interaction: discord.Interaction):
        personaje = interaction.data["values"][0]
        view = _ConfirmarLimpiezaUnoView(self.user_id, personaje, self.staff_name, self.bot)
        await interaction.response.edit_message(
            embed=discord.Embed(title="⚠️ Confirmar limpieza de PC",
                description=f"¿Resetear los PC de **{personaje}** a 0? No reversible.",
                color=COLOR_PENDIENTE),
            view=view)
        self.stop()


class _ConfirmarLimpiezaUnoView(discord.ui.View):
    def __init__(self, user_id, personaje, staff_name, bot):
        super().__init__(timeout=60)
        self.user_id = user_id; self.personaje = personaje
        self.staff_name = staff_name; self.bot = bot

    @discord.ui.button(label="✅ Confirmar", style=discord.ButtonStyle.danger)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        ok = _limpiar_pc_personaje(self.user_id, self.personaje)
        embed = discord.Embed(title="🧹 PC limpiados",
            description=f"PC de **{self.personaje}** reseteados a 0.\n{'✅ OK' if ok else '⚠️ No encontrado.'}",
            color=COLOR_APROBADO if ok else COLOR_RECHAZADO)
        embed.set_footer(text=f"Por {self.staff_name}")
        await interaction.response.edit_message(embed=embed, view=None)
        await _log(self.bot, "🧹 PC limpiados",
            f"**Personaje:** {self.personaje}\n**Estado:** {'OK' if ok else 'Error'}\n**Por:** {self.staff_name}",
            COLOR_INFO, footer=self.staff_name)
        self.stop()

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Cancelado.", embed=None, view=None)
        self.stop()


class _ConfirmarLimpiezaTotalView(discord.ui.View):
    def __init__(self, staff_name, bot):
        super().__init__(timeout=60)
        self.staff_name = staff_name; self.bot = bot

    @discord.ui.button(label="✅ Confirmar", style=discord.ButtonStyle.danger)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        ok = _limpiar_pc_todos()
        embed = discord.Embed(title="🧹 PC limpiados — TODOS",
            description="PC de todos reseteados a 0." if ok else "⚠️ Error.",
            color=COLOR_APROBADO if ok else COLOR_RECHAZADO)
        embed.set_footer(text=f"Por {self.staff_name}")
        await interaction.response.edit_message(embed=embed, view=None)
        await _log(self.bot, "🧹 PC limpiados — TODOS",
            f"Todos los PC del servidor reseteados a 0.\n**Por:** {self.staff_name}",
            COLOR_RECHAZADO, footer=self.staff_name)
        self.stop()

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Cancelado.", embed=None, view=None)
        self.stop()


# ──────────────────────────────────────────────
# VIEW — Marcar sanción cumplida (con log)
# ──────────────────────────────────────────────

class MarcarCumplidaView(discord.ui.View):
    def __init__(self, user_id, personaje, sanciones, marcado_por, bot):
        super().__init__(timeout=120)
        self.user_id = user_id; self.personaje = personaje
        self.sanciones = sanciones; self.marcado_por = marcado_por
        self.bot = bot; self.idx = 0
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
        partes = [f"**Personaje:** {self.personaje}",
                  f"**Sanción:** {_nombre_sancion(s.get('tipo','?'))} — {s.get('duracion','?')} {u}"]
        if rc: partes.append(rc)
        partes.append('✅ Actualizado.' if ok else '⚠️ Error actualizando.')
        embed = discord.Embed(title="✅ Sanción cumplida", description="\n".join(partes),
            color=COLOR_APROBADO if ok else COLOR_RECHAZADO)
        embed.set_footer(text=f"Por {self.marcado_por}")
        await interaction.response.edit_message(embed=embed, view=None)
        # Log
        await _log(self.bot, "✅ Sanción marcada como cumplida",
            f"**Personaje:** {self.personaje}\n"
            f"**Sanción:** {_nombre_sancion(s.get('tipo','?'))} — {s.get('duracion','?')} {u}\n"
            f"**Estado:** {'Cumplida ✅' if ok else 'Error ⚠️'}\n"
            f"**Por:** {self.marcado_por}",
            COLOR_APROBADO if ok else COLOR_RECHAZADO, footer=self.marcado_por)
        self.stop()

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary, row=1)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Cancelado.", embed=None, view=None)
        self.stop()


# ──────────────────────────────────────────────
# VIEW — Aprobación en canal de logs
# ──────────────────────────────────────────────

class AprobacionSancionView(discord.ui.View):
    def __init__(self, user_id, username, personaje, tipo, duracion, unidad,
                 motivo, asignado_por, bot, es_canje=False, pc_canje=0):
        super().__init__(timeout=None)
        self.user_id = user_id; self.username = username; self.personaje = personaje
        self.tipo = tipo; self.duracion = duracion; self.unidad = unidad
        self.motivo = motivo; self.asignado_por = asignado_por; self.bot = bot
        self.es_canje = es_canje; self.pc_canje = pc_canje

    def _check_staff(self, interaction):
        return any(r.id == ROL_STAFF for r in interaction.user.roles)

    @discord.ui.button(label="✅ Aprobar", style=discord.ButtonStyle.success)
    async def aprobar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check_staff(interaction):
            await interaction.response.send_message("❌ Solo el Staff puede.", ephemeral=True); return

        if self.es_canje:
            _restar_pc(self.user_id, self.personaje, self.pc_canje)
            try:
                from utils.sheets import get_sheet
                get_sheet("HistorialPC").append_row(
                    [str(self.user_id), self.personaje, f"-{self.pc_canje}",
                     f"Canje sanción aprobado: {_nombre_sancion(self.tipo)}",
                     str(interaction.user), _now()], value_input_option="USER_ENTERED")
            except Exception: pass
            desc_ok = f"Reducción aprobada para **{self.personaje}**. {self.pc_canje} PC descontados."
            desc_log = (f"**Personaje:** {self.personaje}\n**Tipo:** Reducción de {_nombre_sancion(self.tipo)}\n"
                        f"**PC descontados:** {self.pc_canje}\n**Resultado:** ✅ Aprobado\n"
                        f"**Por:** {interaction.user.display_name}")
        else:
            _registrar_sancion(self.user_id, self.username, self.personaje,
                               self.tipo, self.duracion, self.motivo, self.asignado_por)
            desc_ok = f"Sanción aplicada a **{self.personaje}** — {self.duracion} {self.unidad}."
            desc_log = (f"**Personaje:** {self.personaje}\n**Tipo:** {_nombre_sancion(self.tipo)}\n"
                        f"**Duración:** {self.duracion} {self.unidad}\n**Resultado:** ✅ Aprobado\n"
                        f"**Por:** {interaction.user.display_name}")

        embed = discord.Embed(title="✅ Aprobado", description=desc_ok, color=COLOR_APROBADO)
        embed.set_footer(text=f"Aprobado por {interaction.user.display_name}")
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message("✅ Procesado.", ephemeral=True)
        await _log(self.bot, "✅ Solicitud aprobada — PCA", desc_log,
                   COLOR_APROBADO, footer=interaction.user.display_name)

        await _notificar_usuario(interaction.guild, self.user_id, discord.Embed(
            title="✅ Solicitud aprobada" if self.es_canje else f"⚠️ Sanción aplicada — {_nombre_sancion(self.tipo)}",
            description=(f"La reducción de sanción para **{self.personaje}** fue aprobada.\n"
                         f"PC descontados: **{self.pc_canje}**"
                         if self.es_canje else
                         f"Tu personaje **{self.personaje}** recibió una sanción.\n\n"
                         f"**Duración:** {self.duracion} {self.unidad}\n**Motivo:** {self.motivo}"),
            color=COLOR_APROBADO if self.es_canje else COLOR_RECHAZADO))
        self.stop()

    @discord.ui.button(label="❌ Rechazar", style=discord.ButtonStyle.danger)
    async def rechazar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check_staff(interaction):
            await interaction.response.send_message("❌ Solo el Staff puede.", ephemeral=True); return
        await interaction.response.send_modal(
            _MotivoRechazoModal(user_id=self.user_id, personaje=self.personaje,
                                tipo=self.tipo, message=interaction.message,
                                es_canje=self.es_canje, bot=self.bot,
                                rechazado_por=interaction.user.display_name))

    @discord.ui.button(label="🎫 Abrir ticket", style=discord.ButtonStyle.secondary)
    async def ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="🎫 Ticket solicitado",
            description=(f"**Personaje:** {self.personaje}\n**Tipo:** {_nombre_sancion(self.tipo)}\n\n"
                         f"Se requiere abrir un ticket para continuar."),
            color=COLOR_INFO)
        embed.set_footer(text=f"Por {interaction.user.display_name}")
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message("✅ Notificado.", ephemeral=True)
        await _notificar_usuario(interaction.guild, self.user_id, discord.Embed(
            title="🎫 Se requiere un ticket",
            description=(f"El Staff necesita más contexto sobre el caso de **{self.personaje}**.\n\n"
                         f"Por favor **abre un ticket** en el servidor."),
            color=COLOR_INFO))
        self.stop()


class _MotivoRechazoModal(discord.ui.Modal, title="❌ Motivo de rechazo"):
    motivo = discord.ui.TextInput(label="Motivo", style=discord.TextStyle.paragraph,
                                   required=False, max_length=500,
                                   placeholder="Explica por qué se rechaza...")

    def __init__(self, user_id, personaje, tipo, message, es_canje, bot, rechazado_por):
        super().__init__()
        self.user_id = user_id; self.personaje = personaje; self.tipo = tipo
        self.message = message; self.es_canje = es_canje; self.bot = bot
        self.rechazado_por = rechazado_por

    async def on_submit(self, interaction: discord.Interaction):
        m = self.motivo.value.strip() or "Sin motivo especificado."
        embed = discord.Embed(title="❌ Rechazado",
            description=f"**Personaje:** {self.personaje}\n**Motivo:** {m}",
            color=COLOR_RECHAZADO)
        embed.set_footer(text=f"Por {self.rechazado_por}")
        await self.message.edit(embed=embed, view=None)
        await interaction.response.send_message("✅ Rechazado.", ephemeral=True)

        desc_log = (f"**Personaje:** {self.personaje}\n**Tipo:** "
                    f"{'Reducción' if self.es_canje else _nombre_sancion(self.tipo)}\n"
                    f"**Resultado:** ❌ Rechazado\n**Motivo:** {m}\n**Por:** {self.rechazado_por}")
        await _log(self.bot, "❌ Solicitud rechazada — PCA", desc_log,
                   COLOR_RECHAZADO, footer=self.rechazado_por)

        await _notificar_usuario(interaction.guild, self.user_id, discord.Embed(
            title="❌ Solicitud rechazada",
            description=(f"{'La reducción' if self.es_canje else 'La sanción'} "
                         f"para **{self.personaje}** fue rechazada.\n\n**Motivo:** {m}"),
            color=COLOR_RECHAZADO))


# ──────────────────────────────────────────────
# VIEW — Panel de canje
# ──────────────────────────────────────────────

class CanjeView(discord.ui.View):
    def __init__(self, user_id, personaje, sanciones, balance, bot):
        super().__init__(timeout=120)
        self.user_id = user_id; self.personaje = personaje
        self.sanciones = sanciones; self.balance = balance
        self.bot = bot; self.idx = 0
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
        s = self.sanciones[self.idx]; tipo = s.get("tipo","castigo_menor")
        duracion = int(s.get("duracion", 20))
        unidad   = "min de rol" if tipo != "suspension" else "días IRL"
        disp     = self.balance["pc_disponible"]
        embed = discord.Embed(title=f"💎 Canjear PC — {self.personaje}", color=COLOR_INFO)
        embed.add_field(name="Sanción",
            value=f"**{_nombre_sancion(tipo)}** — {duracion} {unidad}\n*{s.get('motivo','?')}*", inline=False)
        embed.add_field(name="PC disponibles", value=f"**{disp} PC**", inline=True)
        if tipo == "castigo_menor":
            r1 = calcular_reduccion_castigo_menor(1, duracion)
            rm = calcular_reduccion_castigo_menor(10, duracion)
            embed.add_field(name="📊 Opciones", value=(
                f"**1 PC** → quedan **{r1['tiempo_final']:.1f} min**\n"
                f"**10 PC** → quedan **{rm['tiempo_final']:.1f} min** ✨ (bono)"), inline=False)
        elif tipo == "detencion":
            pc_max = max(1, int(duracion * 0.8 / 2.5))
            r1 = calcular_reduccion_detencion(1, duracion)
            rm = calcular_reduccion_detencion(pc_max, duracion)
            embed.add_field(name="📊 Opciones", value=(
                f"**1 PC** → quedan **{r1['tiempo_final']:.1f} min**\n"
                f"**{pc_max} PC** (máx) → quedan **{rm['tiempo_final']:.1f} min**"), inline=False)
        elif tipo == "suspension":
            embed.add_field(name="📊 Opciones", value=(
                "**20 PC** = 1 día menos *(requiere aprobación del Staff)*\n"
                "*Siempre queda al menos 1 día.*"), inline=False)
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
        self.user_id = user_id; self.personaje = personaje; self.sancion = sancion
        self.sancion_idx = sancion_idx; self.balance = balance; self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        try:
            pc = int(self.pc_input.value.strip())
            if pc < 1: raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ Número válido mayor a 0.", ephemeral=True); return

        disp = self.balance["pc_disponible"]
        if pc > disp:
            await interaction.response.send_message(
                f"❌ Solo tienes **{disp} PC** disponibles.", ephemeral=True); return

        tipo = self.sancion.get("tipo","castigo_menor")
        duracion = int(self.sancion.get("duracion", 20))

        try:
            if tipo == "castigo_menor":
                r = calcular_reduccion_castigo_menor(pc, duracion)
                resumen = (f"**{pc} PC** gastados\nReducción: **{r['minutos_reducidos']:.1f} min**"
                           f"{' + 1 bono ✨' if r['bonificacion'] else ''}\n"
                           f"Tiempo final: **{r['tiempo_final']:.1f} min de rol**")
                pc_usar = pc; necesita = False
            elif tipo == "detencion":
                r = calcular_reduccion_detencion(pc, duracion)
                resumen = (f"**{pc} PC** gastados\nReducción: **{r['minutos_reducidos']:.1f} min**\n"
                           f"Tiempo final: **{r['tiempo_final']:.1f} min de rol**")
                pc_usar = pc; necesita = False
            elif tipo == "suspension":
                r = calcular_reduccion_suspension(pc, duracion)
                if r["dias_reducidos"] == 0:
                    await interaction.response.send_message(
                        f"❌ Necesitas al menos **20 PC** para reducir 1 día. Tienes **{disp} PC**.",
                        ephemeral=True); return
                resumen = (f"**{r['pc_usados']} PC** serán descontados si el Staff aprueba.\n"
                           f"Reducción solicitada: **{r['dias_reducidos']} día(s)**\n"
                           f"Suspensión resultante: **{r['dias_final']} día(s) IRL**\n\n"
                           f"⏳ *Pendiente de autorización del Staff.*")
                pc_usar = r["pc_usados"]; necesita = True
            else:
                await interaction.response.send_message("❌ Tipo no reconocido.", ephemeral=True); return
        except Exception as e:
            print(f"[PCA] Cálculo canje: {e}")
            await interaction.response.send_message(
                "❌ Error al calcular el canje. Intenta de nuevo.", ephemeral=True); return

        if necesita:
            canal = self.bot.get_channel(CANAL_APROBACIONES)
            if canal:
                await canal.send(
                    embed=discord.Embed(title="🔄 Solicitud de reducción de suspensión",
                        description=(f"**Usuario:** <@{self.user_id}>\n"
                                     f"**Personaje:** {self.personaje}\n"
                                     f"**Suspensión actual:** {duracion} días IRL\n"
                                     f"**Reducción solicitada:** {r['dias_reducidos']} día(s) (-{pc_usar} PC)\n"
                                     f"**Resultado si se aprueba:** {r['dias_final']} día(s) IRL"),
                        color=COLOR_PENDIENTE),
                    view=AprobacionSancionView(
                        user_id=self.user_id, username="",
                        personaje=self.personaje, tipo=tipo,
                        duracion=r["dias_reducidos"], unidad="días",
                        motivo="Canje de PC", asignado_por=str(interaction.user),
                        bot=self.bot, es_canje=True, pc_canje=pc_usar))
            await interaction.response.send_message(
                embed=discord.Embed(title="⏳ Solicitud enviada", description=resumen,
                                    color=COLOR_PENDIENTE), ephemeral=True)
            return

        if not _restar_pc(self.user_id, self.personaje, pc_usar):
            await interaction.response.send_message(
                "❌ No se pudieron descontar los PC. Intenta de nuevo.", ephemeral=True); return
        try:
            from utils.sheets import get_sheet
            get_sheet("HistorialPC").append_row(
                [str(self.user_id), self.personaje, f"-{pc_usar}",
                 f"Canje sanción: {_nombre_sancion(tipo)}",
                 str(interaction.user), _now()], value_input_option="USER_ENTERED")
        except Exception as e:
            print(f"[PCA] Historial canje: {e}")

        b = _get_pc(self.user_id, self.personaje)
        embed = discord.Embed(title="✅ Canje procesado", description=resumen, color=COLOR_APROBADO)
        embed.add_field(name="Balance restante",
            value=f"**{b['pc_disponible']} PC** disponibles", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ──────────────────────────────────────────────
# VIEWS — Apelar
# ──────────────────────────────────────────────

class _ApelarSelectView(discord.ui.View):
    def __init__(self, user_id, personajes, bot):
        super().__init__(timeout=120)
        self.user_id = user_id; self.bot = bot
        s = _make_select(personajes); s.callback = self._on; self.add_item(s)

    async def _on(self, interaction: discord.Interaction):
        personaje = interaction.data["values"][0]
        sanciones = _get_sanciones_activas(self.user_id, personaje)
        apelables = [s for s in sanciones if s.get("tipo") in ("suspension","expulsion")]
        if not apelables:
            await interaction.response.edit_message(
                content=(f"ℹ️ **{personaje}** no tiene sanciones apelables.\n\n"
                         f"Solo se pueden apelar **suspensiones** y **expulsiones**."),
                embed=None, view=None); return
        view = _ApelarSancionView(user_id=self.user_id, personaje=personaje,
                                   sanciones=apelables, bot=self.bot)
        await interaction.response.edit_message(
            embed=discord.Embed(title=f"⚖️ Apelar — {personaje}",
                description="Selecciona la sanción a apelar:", color=COLOR_INFO),
            view=view)
        self.stop()


class _ApelarSancionView(discord.ui.View):
    def __init__(self, user_id, personaje, sanciones, bot):
        super().__init__(timeout=120)
        self.user_id = user_id; self.personaje = personaje
        self.sanciones = sanciones; self.bot = bot; self.idx = 0
        select = discord.ui.Select(
            placeholder="📋 Selecciona la sanción...",
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
                description="Sanción seleccionada. Presiona **Enviar apelación** para argumentar.",
                color=COLOR_INFO), view=self)

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
    argumento = discord.ui.TextInput(label="¿Por qué apelas esta sanción?",
        style=discord.TextStyle.paragraph,
        placeholder="Explica tu caso detalladamente...", min_length=20, max_length=1000)

    def __init__(self, user_id, personaje, sancion, bot):
        super().__init__()
        self.user_id = user_id; self.personaje = personaje
        self.sancion = sancion; self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        tipo = self.sancion.get("tipo","suspension")
        u    = "días IRL" if tipo == "suspension" else ""
        canal = self.bot.get_channel(CANAL_APROBACIONES)
        if canal:
            await canal.send(
                embed=discord.Embed(title="⚖️ Apelación de sanción",
                    description=(f"**Usuario:** <@{self.user_id}>\n"
                                 f"**Personaje:** {self.personaje}\n"
                                 f"**Sanción apelada:** {_nombre_sancion(tipo)} — "
                                 f"{self.sancion.get('duracion','?')} {u}\n"
                                 f"**Aplicada por:** {self.sancion.get('asignado_por','?')}\n"
                                 f"**Motivo original:** {self.sancion.get('motivo','?')}\n\n"
                                 f"**Argumento del estudiante:**\n{self.argumento.value}"),
                    color=COLOR_INFO),
                view=_ApelacionStaffView(user_id=self.user_id, personaje=self.personaje,
                                          sancion=self.sancion, bot=self.bot))
        await interaction.response.send_message(
            embed=discord.Embed(title="✅ Apelación enviada",
                description=f"Tu apelación para **{self.personaje}** fue enviada al Staff.\nRecibirás una notificación.",
                color=COLOR_APROBADO), ephemeral=True)


class _ApelacionStaffView(discord.ui.View):
    def __init__(self, user_id, personaje, sancion, bot):
        super().__init__(timeout=None)
        self.user_id = user_id; self.personaje = personaje
        self.sancion = sancion; self.bot = bot

    def _check(self, i): return any(r.id == ROL_STAFF for r in i.user.roles)

    @discord.ui.button(label="✅ Aceptar apelación", style=discord.ButtonStyle.success)
    async def aceptar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check(interaction):
            await interaction.response.send_message("❌ Solo el Staff puede.", ephemeral=True); return
        _limpiar_sanciones_personaje(self.user_id, self.personaje)
        embed = discord.Embed(title="✅ Apelación aceptada",
            description=f"La sanción de **{self.personaje}** fue retirada.",
            color=COLOR_APROBADO)
        embed.set_footer(text=f"Por {interaction.user.display_name}")
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message("✅ Apelación aceptada.", ephemeral=True)
        # Log
        await _log(self.bot, "✅ Apelación aceptada",
            f"**Personaje:** {self.personaje}\n**Resultado:** Sanción retirada ✅\n"
            f"**Por:** {interaction.user.display_name}",
            COLOR_APROBADO, footer=interaction.user.display_name)
        await _notificar_usuario(interaction.guild, self.user_id, discord.Embed(
            title="✅ Apelación aceptada",
            description=f"Tu apelación para **{self.personaje}** fue **aceptada**. La sanción fue retirada.",
            color=COLOR_APROBADO))
        self.stop()

    @discord.ui.button(label="❌ Rechazar apelación", style=discord.ButtonStyle.danger)
    async def rechazar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check(interaction):
            await interaction.response.send_message("❌ Solo el Staff puede.", ephemeral=True); return
        await interaction.response.send_modal(
            _MotivoRechazoApelacionModal(user_id=self.user_id, personaje=self.personaje,
                                          message=interaction.message, bot=self.bot,
                                          rechazado_por=interaction.user.display_name))

    @discord.ui.button(label="🎫 Abrir ticket", style=discord.ButtonStyle.secondary)
    async def ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="🎫 Ticket requerido",
            description=f"Se requiere ticket para la apelación de **{self.personaje}**.",
            color=COLOR_INFO)
        embed.set_footer(text=f"Por {interaction.user.display_name}")
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message("✅ Notificado.", ephemeral=True)
        await _notificar_usuario(interaction.guild, self.user_id, discord.Embed(
            title="🎫 Se requiere un ticket",
            description=f"El Staff necesita más contexto para la apelación de **{self.personaje}**.\n\nPor favor **abre un ticket** en el servidor.",
            color=COLOR_INFO))
        self.stop()


class _MotivoRechazoApelacionModal(discord.ui.Modal, title="❌ Rechazar apelación"):
    motivo = discord.ui.TextInput(label="Motivo del rechazo", style=discord.TextStyle.paragraph,
                                   required=False, max_length=500)

    def __init__(self, user_id, personaje, message, bot, rechazado_por):
        super().__init__()
        self.user_id = user_id; self.personaje = personaje
        self.message = message; self.bot = bot; self.rechazado_por = rechazado_por

    async def on_submit(self, interaction: discord.Interaction):
        m = self.motivo.value.strip() or "Sin motivo especificado."
        embed = discord.Embed(title="❌ Apelación rechazada",
            description=f"**Personaje:** {self.personaje}\n**Motivo:** {m}",
            color=COLOR_RECHAZADO)
        embed.set_footer(text=f"Por {self.rechazado_por}")
        await self.message.edit(embed=embed, view=None)
        await interaction.response.send_message("✅ Rechazado.", ephemeral=True)
        await _log(self.bot, "❌ Apelación rechazada",
            f"**Personaje:** {self.personaje}\n**Resultado:** Rechazada ❌\n"
            f"**Motivo:** {m}\n**Por:** {self.rechazado_por}",
            COLOR_RECHAZADO, footer=self.rechazado_por)
        await _notificar_usuario(interaction.guild, self.user_id, discord.Embed(
            title="❌ Apelación rechazada",
            description=f"Tu apelación para **{self.personaje}** fue rechazada.\n\n**Motivo:** {m}",
            color=COLOR_RECHAZADO))


async def setup(bot):
    await bot.add_cog(PCA(bot))
