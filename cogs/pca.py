import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

from utils.constants import (
    GUILD_ID, ROLES_AUTORIDAD_PC, ROL_ESTUDIANTE, ROL_STAFF,
    COLOR_INFO, COLOR_APROBADO, COLOR_RECHAZADO, COLOR_PENDIENTE,
    TIPOS_SANCION, calcular_pc_por_nota, calcular_reduccion_castigo_menor,
    calcular_reduccion_detencion, calcular_reduccion_suspension,
    PC_TRABAJO_SUCIO_MIN, PC_TRABAJO_SUCIO_MAX,
)
from utils.sheets import get_personajes_usuario


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

def _registrar_sancion(user_id, username, personaje, tipo, duracion, motivo, asignado_por):
    from utils.sheets import get_sheet
    try:
        get_sheet("Sanciones").append_row(
            [str(user_id), username, personaje, tipo, str(duracion),
             "ACTIVA", asignado_por, _now(), motivo],
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

def _tiene_autoridad(interaction: discord.Interaction) -> bool:
    return any(r.id in ROLES_AUTORIDAD_PC for r in interaction.user.roles)

def _es_staff(interaction: discord.Interaction) -> bool:
    return any(r.id == ROL_STAFF for r in interaction.user.roles)

def _get_estudiantes(user_id: int) -> list[str]:
    try:
        return [p["personaje"] for p in get_personajes_usuario(user_id)
                if p["tipo"] == "estudiante"]
    except Exception:
        return []


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
        pc = calcular_pc_por_nota(nota_f)
        if pc == 0:
            await interaction.response.send_message(
                f"ℹ️ La nota **{nota_f}** es menor al mínimo aprobatorio (3.5). No se otorgan PC.", ephemeral=True)
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
        motivo_c = f"Nota académica {nota_f} — {motivo}"
        view = SeleccionarPersonajeView(
            user_id=usuario.id, username=str(usuario),
            usuario_mention=usuario.mention, personajes=estudiantes,
            accion="pc", extra={"pc": pc, "motivo": motivo_c, "asignado_por": str(interaction.user)})
        embed = discord.Embed(title="🎓 Seleccionar personaje", color=COLOR_PENDIENTE,
            description=f"**Usuario:** {usuario.mention}\n**Nota:** {nota_f} → **+{pc} PC**\n"
                        f"**Motivo:** {motivo}\n\nSelecciona el personaje:")
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    # ── /asignar-pc-directo ───────────────────

    @app_commands.command(name="asignar-pc-directo",
        description="[STAFF/CONSEJO] Asignar PC directamente por Trabajo Sucio del Consejo (5-10 PC).")
    @app_commands.describe(usuario="El usuario", pc="Cantidad de PC (5-10)", motivo="Descripción del trabajo")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def asignar_pc_directo(self, interaction: discord.Interaction,
                                  usuario: discord.Member, pc: int, motivo: str):
        if not _tiene_autoridad(interaction):
            await interaction.response.send_message("❌ Sin autoridad.", ephemeral=True)
            return
        if not (PC_TRABAJO_SUCIO_MIN <= pc <= PC_TRABAJO_SUCIO_MAX):
            await interaction.response.send_message(
                f"❌ PC directos deben estar entre {PC_TRABAJO_SUCIO_MIN} y {PC_TRABAJO_SUCIO_MAX}.", ephemeral=True)
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
        view = SeleccionarPersonajeView(
            user_id=usuario.id, username=str(usuario),
            usuario_mention=usuario.mention, personajes=estudiantes,
            accion="pc", extra={"pc": pc, "motivo": motivo_c, "asignado_por": str(interaction.user)})
        embed = discord.Embed(title="💎 Asignar PC directos", color=COLOR_PENDIENTE,
            description=f"**Usuario:** {usuario.mention}\n**PC:** +{pc}\n"
                        f"**Motivo:** {motivo}\n\nSelecciona el personaje:")
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    # ── /aplicar-sancion ──────────────────────

    @app_commands.command(name="aplicar-sancion",
        description="[STAFF/PROF/CONSEJO] Aplicar una sanción a un personaje estudiante.")
    @app_commands.describe(usuario="El usuario", tipo="Tipo de sanción", motivo="Motivo",
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
                    f"❌ Para {cfg['nombre']} debes indicar `minutos` "
                    f"({cfg['duracion_min']}-{cfg['duracion_max']} min de rol).", ephemeral=True)
                return
            if not (cfg["duracion_min"] <= minutos <= cfg["duracion_max"]):
                await interaction.response.send_message(
                    f"❌ Duración debe ser {cfg['duracion_min']}-{cfg['duracion_max']} min.", ephemeral=True)
                return
            duracion, unidad = minutos, "minutos de rol"
        else:
            if dias is None:
                await interaction.response.send_message(
                    "❌ Para Suspensión debes indicar `dias` (2 o 3).", ephemeral=True)
                return
            if not (cfg["duracion_min"] <= dias <= cfg["duracion_max"]):
                await interaction.response.send_message(
                    f"❌ Suspensión debe ser {cfg['duracion_min']}-{cfg['duracion_max']} días.", ephemeral=True)
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

        await interaction.response.defer(ephemeral=False)
        view = SeleccionarPersonajeView(
            user_id=usuario.id, username=str(usuario),
            usuario_mention=usuario.mention, personajes=estudiantes,
            accion="sancion",
            extra={"tipo": tipo, "duracion": duracion, "unidad": unidad,
                   "motivo": motivo, "asignado_por": str(interaction.user)})
        embed = discord.Embed(title=f"⚠️ Aplicar sanción — {cfg['nombre']}", color=COLOR_RECHAZADO,
            description=f"**Usuario:** {usuario.mention}\n**Duración:** {duracion} {unidad}\n"
                        f"**Motivo:** {motivo}\n\nSelecciona el personaje sancionado:")
        await interaction.followup.send(embed=embed, view=view)

    # ── /ver-pc ───────────────────────────────

    @app_commands.command(name="ver-pc",
        description="Ver el balance de PC y sanciones activas de un personaje.")
    @app_commands.describe(personaje="Nombre del personaje",
                           usuario="(Opcional, solo autoridad) Ver los de otro usuario")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def ver_pc(self, interaction: discord.Interaction, personaje: str,
                     usuario: discord.Member | None = None):
        target = usuario or interaction.user
        if usuario and usuario != interaction.user and not _tiene_autoridad(interaction):
            await interaction.response.send_message("❌ Sin autoridad para ver PC de otros.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        balance   = _get_pc(target.id, personaje)
        sanciones = _get_sanciones_activas(target.id, personaje)
        embed = discord.Embed(title=f"🎓 PC de {personaje}", color=COLOR_INFO)
        embed.set_author(name=target.display_name, icon_url=target.display_avatar.url)
        embed.add_field(name="💎 Balance",
            value=(f"Disponibles: **{balance['pc_disponible']} PC**\n"
                   f"Total histórico: **{balance['pc_total']} PC**\n"
                   f"Gastados: **{balance['pc_total'] - balance['pc_disponible']} PC**"), inline=False)
        if sanciones:
            lines = []
            for i, s in enumerate(sanciones):
                c = TIPOS_SANCION.get(s.get("tipo",""), {})
                u = "min" if s.get("tipo") != "suspension" else "días"
                lines.append(f"**{i+1}.** {c.get('nombre','?')} — **{s.get('duracion','?')} {u}** *(por {s.get('asignado_por','?')})*")
            embed.add_field(name="⚠️ Sanciones activas", value="\n".join(lines), inline=False)
            embed.add_field(name="💡 ¿Reducir?", value=f"Usa `/canjear-pc {personaje}`", inline=False)
        else:
            embed.add_field(name="✅ Sanciones activas", value="Ninguna", inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ── /historial-pc ─────────────────────────

    @app_commands.command(name="historial-pc",
        description="Ver el historial de PC de un personaje.")
    @app_commands.describe(personaje="Nombre del personaje",
                           usuario="(Opcional, solo autoridad) Ver el de otro usuario")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def historial_pc(self, interaction: discord.Interaction, personaje: str,
                            usuario: discord.Member | None = None):
        target = usuario or interaction.user
        if usuario and usuario != interaction.user and not _tiene_autoridad(interaction):
            await interaction.response.send_message("❌ Sin autoridad.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        from utils.sheets import get_sheet
        try:
            rows = get_sheet("HistorialPC").get_all_records()
            hist = [r for r in rows
                    if str(r.get("user_id","")) == str(target.id) and
                    r.get("personaje","").strip().lower() == personaje.strip().lower()]
        except Exception as e:
            hist = []
            print(f"[PCA] historial_pc: {e}")
        if not hist:
            await interaction.followup.send(f"ℹ️ **{personaje}** no tiene historial de PC.", ephemeral=True)
            return
        embed = discord.Embed(title=f"📋 Historial PC — {personaje}", color=COLOR_INFO)
        embed.set_author(name=target.display_name, icon_url=target.display_avatar.url)
        lines = []
        for r in hist[-15:]:
            cant   = r.get("pc_otorgados","?")
            prefix = "+" if str(cant).lstrip("-").replace(".","").isdigit() and float(str(cant)) > 0 else ""
            lines.append(f"`{prefix}{cant} PC` — {r.get('motivo','?')} *(por {r.get('asignado_por','?')} · {r.get('fecha','?')})*")
        embed.description = "\n".join(lines)
        if len(hist) > 15:
            embed.set_footer(text=f"Últimos 15 de {len(hist)} registros.")
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ── /canjear-pc ───────────────────────────

    @app_commands.command(name="canjear-pc",
        description="Canjear tus PC para reducir una sanción activa de tu personaje.")
    @app_commands.describe(personaje="Nombre exacto de tu personaje estudiante")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def canjear_pc(self, interaction: discord.Interaction, personaje: str):
        await interaction.response.defer(ephemeral=True)
        estudiantes = _get_estudiantes(interaction.user.id)
        if personaje.strip().lower() not in [e.lower() for e in estudiantes]:
            await interaction.followup.send(
                f"❌ No encontré el personaje estudiante **{personaje}** en tus registros.", ephemeral=True)
            return
        sanciones = _get_sanciones_activas(interaction.user.id, personaje)
        if not sanciones:
            await interaction.followup.send(f"✅ **{personaje}** no tiene sanciones activas.", ephemeral=True)
            return
        balance = _get_pc(interaction.user.id, personaje)
        if balance["pc_disponible"] == 0:
            await interaction.followup.send(
                f"❌ **{personaje}** no tiene PC disponibles para canjear.", ephemeral=True)
            return
        view  = CanjeView(interaction.user.id, personaje, sanciones, balance)
        await interaction.followup.send(embed=view.build_embed(), view=view, ephemeral=True)

    # ── /marcar-sancion-cumplida ──────────────

    @app_commands.command(name="marcar-sancion-cumplida",
        description="[STAFF/PROF/CONSEJO] Marcar una sanción activa como cumplida.")
    @app_commands.describe(usuario="El usuario", personaje="Nombre del personaje")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def marcar_sancion_cumplida(self, interaction: discord.Interaction,
                                       usuario: discord.Member, personaje: str):
        if not _tiene_autoridad(interaction):
            await interaction.response.send_message("❌ Sin autoridad.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        sanciones = _get_sanciones_activas(usuario.id, personaje)
        if not sanciones:
            await interaction.followup.send(f"✅ **{personaje}** no tiene sanciones activas.", ephemeral=True)
            return
        view = MarcarCumplidaView(usuario.id, personaje, sanciones)
        await interaction.followup.send(embed=view.build_embed(), view=view, ephemeral=True)

    # ── /limpiar-sanciones ────────────────────

    @app_commands.command(name="limpiar-sanciones",
        description="[STAFF] Limpiar todas las sanciones activas de un personaje.")
    @app_commands.describe(usuario="El usuario", personaje="Nombre del personaje")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def limpiar_sanciones(self, interaction: discord.Interaction,
                                 usuario: discord.Member, personaje: str):
        if not _es_staff(interaction):
            await interaction.response.send_message("❌ Solo el Staff puede.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        n = _limpiar_sanciones_personaje(usuario.id, personaje)
        embed = discord.Embed(title="🧹 Sanciones limpiadas",
            description=f"**{n}** sanción(es) activa(s) de **{personaje}** ({usuario.display_name}) limpiadas.",
            color=COLOR_APROBADO)
        embed.set_footer(text=f"Por {interaction.user.display_name}")
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ── /limpiar-pc ───────────────────────────

    @app_commands.command(name="limpiar-pc",
        description="[STAFF] Limpiar los PC de un personaje o de todos.")
    @app_commands.describe(modo="¿Limpiar uno o todos?",
                           usuario="(Si modo=personaje) Usuario dueño",
                           personaje="(Si modo=personaje) Nombre del personaje")
    @app_commands.choices(modo=[
        app_commands.Choice(name="Un personaje específico",             value="personaje"),
        app_commands.Choice(name="⚠️ TODOS los personajes del servidor", value="todos"),
    ])
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def limpiar_pc(self, interaction: discord.Interaction, modo: str,
                          usuario: discord.Member | None = None, personaje: str | None = None):
        if not _es_staff(interaction):
            await interaction.response.send_message("❌ Solo el Staff puede.", ephemeral=True)
            return
        if modo == "personaje" and (not usuario or not personaje):
            await interaction.response.send_message(
                "❌ Debes indicar `usuario` y `personaje`.", ephemeral=True)
            return

        if modo == "personaje":
            embed = discord.Embed(title="⚠️ Confirmar limpieza de PC",
                description=f"Se resetearán los PC de **{personaje}** ({usuario.display_name}) a 0. ¿Confirmas?",
                color=COLOR_PENDIENTE)
            view = ConfirmarLimpiezaView("personaje", str(interaction.user), usuario.id, personaje)
        else:
            embed = discord.Embed(title="🚨 Confirmar limpieza TOTAL",
                description="Se resetearán los PC de **TODOS** los personajes a 0. ⚠️ No reversible.",
                color=COLOR_RECHAZADO)
            view = ConfirmarLimpiezaView("todos", str(interaction.user))

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ──────────────────────────────────────────────
# VIEW — Selector de personaje
# ──────────────────────────────────────────────

class SeleccionarPersonajeView(discord.ui.View):
    def __init__(self, user_id, username, usuario_mention, personajes, accion, extra):
        super().__init__(timeout=120)
        self.user_id         = user_id
        self.username        = username
        self.usuario_mention = usuario_mention
        self.personajes      = personajes
        self.accion          = accion
        self.extra           = extra
        select = discord.ui.Select(
            placeholder="🎓 Selecciona el personaje...",
            options=[discord.SelectOption(label=p, value=p) for p in personajes],
            min_values=1, max_values=1)
        select.callback = self._on_select
        self.add_item(select)

    async def _on_select(self, interaction: discord.Interaction):
        personaje = interaction.data["values"][0]
        ex        = self.extra

        if self.accion == "pc":
            pc, motivo, por = ex["pc"], ex["motivo"], ex["asignado_por"]
            _sumar_pc(self.user_id, self.username, personaje, pc, motivo, por)
            balance = _get_pc(self.user_id, personaje)
            embed = discord.Embed(title="✅ PC asignados", color=COLOR_APROBADO)
            embed.add_field(name="Personaje",    value=f"**{personaje}**",   inline=True)
            embed.add_field(name="Usuario",      value=self.usuario_mention, inline=True)
            embed.add_field(name="PC otorgados", value=f"**+{pc} PC**",      inline=True)
            embed.add_field(name="Motivo",       value=motivo,               inline=False)
            embed.add_field(name="Balance",
                value=f"Disponibles: **{balance['pc_disponible']} PC** | Total: **{balance['pc_total']} PC**",
                inline=False)
            embed.set_footer(text=f"Asignado por {por}")
            await interaction.response.edit_message(embed=embed, view=None)
            # DM al usuario
            try:
                guild  = interaction.guild
                member = guild.get_member(self.user_id) or await guild.fetch_member(self.user_id)
                await member.send(embed=discord.Embed(
                    title="🎓 ¡Recibiste Puntos de Canje Académico!",
                    description=(f"Tu personaje **{personaje}** recibió **+{pc} PC**.\n\n"
                                 f"**Motivo:** {motivo}\n\n"
                                 f"Tienes **{balance['pc_disponible']} PC disponibles**.\n"
                                 f"Úsalos con `/canjear-pc {personaje}` para reducir sanciones."),
                    color=COLOR_APROBADO))
            except Exception as e:
                print(f"[PCA] DM PC: {e}")

        elif self.accion == "sancion":
            tipo, duracion = ex["tipo"], ex["duracion"]
            unidad, motivo = ex["unidad"], ex["motivo"]
            por = ex["asignado_por"]
            cfg = TIPOS_SANCION[tipo]
            _registrar_sancion(self.user_id, self.username, personaje,
                               tipo, duracion, motivo, por)
            embed = discord.Embed(title=f"⚠️ Sanción aplicada — {cfg['nombre']}", color=COLOR_RECHAZADO)
            embed.add_field(name="Personaje", value=f"**{personaje}**",          inline=True)
            embed.add_field(name="Usuario",   value=self.usuario_mention,        inline=True)
            embed.add_field(name="Duración",  value=f"**{duracion} {unidad}**",  inline=True)
            embed.add_field(name="Motivo",    value=motivo,                      inline=False)
            embed.add_field(name="💡 Canje",
                value=f"El estudiante puede usar `/canjear-pc {personaje}` para reducir con PC.",
                inline=False)
            embed.set_footer(text=f"Aplicado por {por}")
            await interaction.response.edit_message(embed=embed, view=None)
            # DM al usuario
            try:
                guild  = interaction.guild
                member = guild.get_member(self.user_id) or await guild.fetch_member(self.user_id)
                await member.send(embed=discord.Embed(
                    title=f"⚠️ Sanción recibida — {cfg['nombre']}",
                    description=(f"Tu personaje **{personaje}** recibió una sanción.\n\n"
                                 f"**Tipo:** {cfg['nombre']}\n"
                                 f"**Duración:** {duracion} {unidad}\n"
                                 f"**Motivo:** {motivo}\n\n"
                                 f"Usa `/canjear-pc {personaje}` para reducir el tiempo con tus PC."),
                    color=COLOR_RECHAZADO))
            except Exception as e:
                print(f"[PCA] DM sancion: {e}")
        self.stop()


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
                label=f"{TIPOS_SANCION.get(s.get('tipo',''),{}).get('nombre','?')} — {s.get('duracion','?')} {'min' if s.get('tipo') != 'suspension' else 'días'}",
                value=str(i), description=f"Por: {s.get('asignado_por','?')}")
                for i, s in enumerate(sanciones)],
            min_values=1, max_values=1)
        select.callback = self._on_select
        self.add_item(select)

    def build_embed(self):
        return discord.Embed(title=f"✅ Marcar sanción cumplida — {self.personaje}",
            description="Selecciona la sanción que ya fue cumplida:", color=COLOR_PENDIENTE)

    async def _on_select(self, interaction: discord.Interaction):
        self.idx = int(interaction.data["values"][0])
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="✅ Confirmar", style=discord.ButtonStyle.success, row=1)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        ok  = _marcar_sancion_cumplida(self.user_id, self.personaje, self.idx)
        s   = self.sanciones[self.idx]
        cfg = TIPOS_SANCION.get(s.get("tipo",""), {})
        u   = "min" if s.get("tipo") != "suspension" else "días"
        embed = discord.Embed(title="✅ Sanción cumplida",
            description=(f"**Personaje:** {self.personaje}\n"
                         f"**Sanción:** {cfg.get('nombre','?')} — {s.get('duracion','?')} {u}\n"
                         f"{'✅ Actualizado en Sheets.' if ok else '⚠️ Error actualizando.'}"),
            color=COLOR_APROBADO if ok else COLOR_RECHAZADO)
        embed.set_footer(text=f"Por {interaction.user.display_name}")
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary, row=1)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Cancelado.", embed=None, view=None)
        self.stop()


# ──────────────────────────────────────────────
# VIEW — Panel de canje
# ──────────────────────────────────────────────

class CanjeView(discord.ui.View):
    def __init__(self, user_id, personaje, sanciones, balance):
        super().__init__(timeout=120)
        self.user_id   = user_id
        self.personaje = personaje
        self.sanciones = sanciones
        self.balance   = balance
        self.idx       = 0
        select = discord.ui.Select(
            placeholder="📋 Selecciona la sanción a reducir...",
            options=[discord.SelectOption(
                label=f"{TIPOS_SANCION.get(s.get('tipo',''),{}).get('nombre','?')} — {s.get('duracion','?')} {'min' if s.get('tipo') != 'suspension' else 'días'}",
                value=str(i))
                for i, s in enumerate(sanciones)],
            min_values=1, max_values=1)
        select.callback = self._on_select
        self.add_item(select)

    async def _on_select(self, interaction: discord.Interaction):
        self.idx = int(interaction.data["values"][0])
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    def build_embed(self):
        s        = self.sanciones[self.idx]
        tipo     = s.get("tipo","castigo_menor")
        cfg      = TIPOS_SANCION.get(tipo, {})
        duracion = int(s.get("duracion", 20))
        unidad   = "min de rol" if tipo != "suspension" else "días IRL"
        disp     = self.balance["pc_disponible"]

        embed = discord.Embed(title=f"💎 Canjear PC — {self.personaje}", color=COLOR_INFO)
        embed.add_field(name="Sanción",
            value=f"**{cfg.get('nombre','?')}** — {duracion} {unidad}\n*{s.get('motivo','?')}*", inline=False)
        embed.add_field(name="PC disponibles", value=f"**{disp} PC**", inline=True)

        if tipo == "castigo_menor":
            r1   = calcular_reduccion_castigo_menor(1, duracion)
            rmax = calcular_reduccion_castigo_menor(10, duracion)
            embed.add_field(name="📊 Opciones", value=(
                f"**1 PC** → quedan **{r1['tiempo_final']:.1f} min**\n"
                f"**10 PC** → quedan **{rmax['tiempo_final']:.1f} min** ✨ (bono incluido)"
            ), inline=False)
        elif tipo == "detencion":
            pc_max = max(1, int(duracion * 0.8 / 2.5))
            r1     = calcular_reduccion_detencion(1, duracion)
            rmax   = calcular_reduccion_detencion(pc_max, duracion)
            embed.add_field(name="📊 Opciones", value=(
                f"**1 PC** → quedan **{r1['tiempo_final']:.1f} min**\n"
                f"**{pc_max} PC** (máx) → quedan **{rmax['tiempo_final']:.1f} min** | Mín: {rmax['min_obligatorio']} min"
            ), inline=False)
        elif tipo == "suspension":
            embed.add_field(name="📊 Opciones", value=(
                "**20 PC** = 1 día menos\n*Siempre queda al menos 1 día.*\n*Requiere autorización Staff.*"
            ), inline=False)
        embed.set_footer(text="Ingresa cuántos PC gastar con el botón de abajo.")
        return embed

    @discord.ui.button(label="💎 Confirmar canje", style=discord.ButtonStyle.primary, row=1)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            ConfirmarCanjeModal(self.user_id, self.personaje,
                                self.sanciones[self.idx], self.idx, self.balance))
        self.stop()

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary, row=1)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Cancelado.", embed=None, view=None)
        self.stop()


class ConfirmarCanjeModal(discord.ui.Modal, title="💎 ¿Cuántos PC gastar?"):
    pc_input = discord.ui.TextInput(
        label="PC a gastar (número)",
        placeholder="Ej: 5",
        min_length=1, max_length=3)

    def __init__(self, user_id, personaje, sancion, sancion_idx, balance):
        super().__init__()
        self.user_id     = user_id
        self.personaje   = personaje
        self.sancion     = sancion
        self.sancion_idx = sancion_idx
        self.balance     = balance

    async def on_submit(self, interaction: discord.Interaction):
        try:
            pc = int(self.pc_input.value.strip())
            if pc < 1: raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ Ingresa un número válido mayor a 0.", ephemeral=True)
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
                resumen = (f"**{pc} PC** gastados\nReducción: **{r['minutos_reducidos']:.1f} min**"
                           f"{' + 1 bono ✨' if r['bonificacion'] else ''}\n"
                           f"Tiempo final: **{r['tiempo_final']:.1f} min de rol**")
                pc_usar = pc
            elif tipo == "detencion":
                r = calcular_reduccion_detencion(pc, duracion)
                resumen = (f"**{pc} PC** gastados\nReducción: **{r['minutos_reducidos']:.1f} min**\n"
                           f"Tiempo final: **{r['tiempo_final']:.1f} min de rol**")
                pc_usar = pc
            elif tipo == "suspension":
                r = calcular_reduccion_suspension(pc, duracion)
                if r["dias_reducidos"] == 0:
                    await interaction.response.send_message(
                        f"❌ Necesitas al menos **20 PC** para reducir 1 día. Tienes **{disp} PC**.", ephemeral=True)
                    return
                resumen = (f"**{r['pc_usados']} PC** gastados\n"
                           f"Reducción: **{r['dias_reducidos']} día(s)**\n"
                           f"Suspensión final: **{r['dias_final']} día(s) IRL**\n"
                           f"*Pendiente de autorización del Staff.*")
                pc_usar = r["pc_usados"]
            else:
                await interaction.response.send_message("❌ Tipo no reconocido.", ephemeral=True)
                return
        except Exception as e:
            print(f"[PCA] Cálculo canje: {e}")
            await interaction.response.send_message(
                "❌ Error al calcular el canje. Intenta de nuevo.", ephemeral=True)
            return

        if not _restar_pc(self.user_id, self.personaje, pc_usar):
            await interaction.response.send_message(
                "❌ No se pudieron descontar los PC. Intenta de nuevo.", ephemeral=True)
            return

        try:
            from utils.sheets import get_sheet
            get_sheet("HistorialPC").append_row(
                [str(self.user_id), self.personaje, f"-{pc_usar}",
                 f"Canje sanción: {TIPOS_SANCION[tipo]['nombre']}",
                 str(interaction.user), _now()],
                value_input_option="USER_ENTERED")
        except Exception as e:
            print(f"[PCA] Historial canje: {e}")

        balance_nuevo = _get_pc(self.user_id, self.personaje)
        embed = discord.Embed(title="✅ Canje procesado", description=resumen, color=COLOR_APROBADO)
        embed.add_field(name="Balance restante",
            value=f"**{balance_nuevo['pc_disponible']} PC** disponibles", inline=False)
        if tipo == "suspension":
            embed.add_field(name="⚠️ Pendiente",
                value="Un miembro del Staff debe autorizar la reducción.", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ──────────────────────────────────────────────
# VIEW — Confirmar limpieza de PC
# ──────────────────────────────────────────────

class ConfirmarLimpiezaView(discord.ui.View):
    def __init__(self, modo, staff_name, user_id=None, personaje=None):
        super().__init__(timeout=60)
        self.modo       = modo
        self.staff_name = staff_name
        self.user_id    = user_id
        self.personaje  = personaje

    @discord.ui.button(label="✅ Confirmar", style=discord.ButtonStyle.danger)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.modo == "personaje":
            ok = _limpiar_pc_personaje(self.user_id, self.personaje)
            embed = discord.Embed(title="🧹 PC limpiados",
                description=f"PC de **{self.personaje}** reseteados a 0.\n{'✅ OK' if ok else '⚠️ No encontrado en Sheets.'}",
                color=COLOR_APROBADO if ok else COLOR_RECHAZADO)
        else:
            ok = _limpiar_pc_todos()
            embed = discord.Embed(title="🧹 PC limpiados — TODOS",
                description="PC de todos reseteados a 0." if ok else "⚠️ Error. Revisa los logs.",
                color=COLOR_APROBADO if ok else COLOR_RECHAZADO)
        embed.set_footer(text=f"Por {self.staff_name}")
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Cancelado.", embed=None, view=None)
        self.stop()


async def setup(bot):
    await bot.add_cog(PCA(bot))
