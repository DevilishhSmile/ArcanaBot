import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

from utils.constants import (
    GUILD_ID, ROLES_AUTORIDAD_PC, ROL_ESTUDIANTE,
    COLOR_INFO, COLOR_APROBADO, COLOR_RECHAZADO, COLOR_PENDIENTE,
    TIPOS_SANCION, TABLA_NOTAS_PC, PC_TRABAJO_SUCIO_MIN, PC_TRABAJO_SUCIO_MAX,
    calcular_pc_por_nota, calcular_reduccion_castigo_menor,
    calcular_reduccion_detencion, calcular_reduccion_suspension,
)
from utils.sheets import get_personajes_usuario


# ──────────────────────────────────────────────
# SHEETS — Hojas de PCA
# PuntosPC:   user_id | personaje | pc_total | pc_disponible | fecha_actualizacion
# HistorialPC: user_id | personaje | pc_otorgados | motivo | asignado_por | fecha
# Sanciones:  user_id | personaje | tipo | duracion | estado | asignado_por | fecha | motivo
# ──────────────────────────────────────────────

def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _get_pc(user_id: int, personaje: str) -> dict:
    """Obtiene el balance de PC de un personaje."""
    from utils.sheets import get_sheet
    try:
        rows = get_sheet("PuntosPC").get_all_records()
        for r in rows:
            if str(r.get("user_id","")) == str(user_id) and \
               r.get("personaje","").strip().lower() == personaje.strip().lower():
                return {
                    "pc_total":       int(r.get("pc_total", 0)),
                    "pc_disponible":  int(r.get("pc_disponible", 0)),
                }
    except Exception as e:
        print(f"[PCA] Error leyendo PuntosPC: {e}")
    return {"pc_total": 0, "pc_disponible": 0}

def _inicializar_pc(user_id: int, username: str, personaje: str):
    """Crea la fila de PC para un personaje si no existe."""
    from utils.sheets import get_sheet
    try:
        sheet = get_sheet("PuntosPC")
        rows  = sheet.get_all_records()
        for r in rows:
            if str(r.get("user_id","")) == str(user_id) and \
               r.get("personaje","").strip().lower() == personaje.strip().lower():
                return  # ya existe
        sheet.append_row([str(user_id), username, personaje, 0, 0, _now()],
                         value_input_option="USER_ENTERED")
    except Exception as e:
        print(f"[PCA] Error inicializando PC: {e}")

def _sumar_pc(user_id: int, personaje: str, cantidad: int, motivo: str, asignado_por: str, username: str):
    """Suma PC a un personaje y registra en el historial."""
    from utils.sheets import get_sheet
    try:
        sheet = get_sheet("PuntosPC")
        rows  = sheet.get_all_values()
        for i, row in enumerate(rows):
            if i == 0: continue
            if len(row) >= 3 and str(row[0]) == str(user_id) and \
               row[2].strip().lower() == personaje.strip().lower():
                pc_total  = int(row[3] or 0) + cantidad
                pc_disp   = int(row[4] or 0) + cantidad
                sheet.update_cell(i+1, 4, pc_total)
                sheet.update_cell(i+1, 5, pc_disp)
                sheet.update_cell(i+1, 6, _now())
                break
        else:
            # No existe aún — inicializar con la cantidad
            sheet.append_row([str(user_id), username, personaje, cantidad, cantidad, _now()],
                             value_input_option="USER_ENTERED")

        # Historial
        get_sheet("HistorialPC").append_row(
            [str(user_id), personaje, cantidad, motivo, asignado_por, _now()],
            value_input_option="USER_ENTERED")
    except Exception as e:
        print(f"[PCA] Error sumando PC: {e}")

def _restar_pc(user_id: int, personaje: str, cantidad: int) -> bool:
    """Resta PC disponibles. Retorna False si no hay suficientes."""
    from utils.sheets import get_sheet
    try:
        sheet = get_sheet("PuntosPC")
        rows  = sheet.get_all_values()
        for i, row in enumerate(rows):
            if i == 0: continue
            if len(row) >= 3 and str(row[0]) == str(user_id) and \
               row[2].strip().lower() == personaje.strip().lower():
                disp = int(row[4] or 0)
                if disp < cantidad:
                    return False
                sheet.update_cell(i+1, 5, disp - cantidad)
                sheet.update_cell(i+1, 6, _now())
                return True
    except Exception as e:
        print(f"[PCA] Error restando PC: {e}")
    return False

def _registrar_sancion(user_id: int, username: str, personaje: str,
                        tipo: str, duracion: int | str, motivo: str, asignado_por: str):
    """Guarda una sanción en la hoja Sanciones."""
    from utils.sheets import get_sheet
    try:
        get_sheet("Sanciones").append_row(
            [str(user_id), username, personaje, tipo, str(duracion),
             "ACTIVA", asignado_por, _now(), motivo],
            value_input_option="USER_ENTERED")
    except Exception as e:
        print(f"[PCA] Error registrando sanción: {e}")

def _get_sanciones_activas(user_id: int, personaje: str) -> list:
    """Obtiene las sanciones activas de un personaje."""
    from utils.sheets import get_sheet
    try:
        rows = get_sheet("Sanciones").get_all_records()
        return [r for r in rows
                if str(r.get("user_id","")) == str(user_id) and
                r.get("personaje","").strip().lower() == personaje.strip().lower() and
                r.get("estado","").upper() == "ACTIVA"]
    except Exception:
        return []

def _marcar_sancion_cumplida(user_id: int, personaje: str, indice_sancion: int):
    """Marca una sanción como cumplida en Sheets."""
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
                if count == indice_sancion:
                    sheet.update_cell(i+1, 6, "CUMPLIDA")
                    return True
                count += 1
    except Exception as e:
        print(f"[PCA] Error marcando sanción: {e}")
    return False


# ──────────────────────────────────────────────
# HELPER — verificar autoridad
# ──────────────────────────────────────────────

def _tiene_autoridad(interaction: discord.Interaction) -> bool:
    return any(r.id in ROLES_AUTORIDAD_PC for r in interaction.user.roles)


# ──────────────────────────────────────────────
# COG
# ──────────────────────────────────────────────

class PCA(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ──────────────────────────────────────────
    # /asignar-pc @usuario personaje nota/cantidad
    # ──────────────────────────────────────────

    @app_commands.command(
        name="asignar-pc",
        description="[STAFF/PROF/CONSEJO] Asignar Puntos de Canje a un personaje estudiante."
    )
    @app_commands.describe(
        usuario="El usuario dueño del personaje",
        personaje="Nombre exacto del personaje",
        nota="Nota académica (1.0-5.0) — el bot calcula los PC automáticamente",
        pc_directos="PC a asignar directamente (solo para Trabajo Sucio del Consejo, 5-10)",
        motivo="Motivo o descripción de la asignación"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def asignar_pc(self,
                         interaction: discord.Interaction,
                         usuario: discord.Member,
                         personaje: str,
                         motivo: str,
                         nota: float | None = None,
                         pc_directos: int | None = None):

        if not _tiene_autoridad(interaction):
            await interaction.response.send_message(
                "❌ No tienes autoridad para asignar PC. Solo Staff, Profesores y Consejo Estudiantil.",
                ephemeral=True)
            return

        # Validar que sea estudiante
        if not any(r.id == ROL_ESTUDIANTE for r in usuario.roles):
            await interaction.response.send_message(
                f"❌ {usuario.display_name} no tiene el rol de Estudiante. Solo los estudiantes acumulan PC.",
                ephemeral=True)
            return

        # Verificar que el personaje existe
        personajes = get_personajes_usuario(usuario.id)
        p_encontrado = next(
            (p for p in personajes if p["personaje"].strip().lower() == personaje.strip().lower()
             and p["tipo"] == "estudiante"), None)
        if not p_encontrado:
            await interaction.response.send_message(
                f"❌ No encontré el personaje estudiante **{personaje}** para {usuario.display_name}.",
                ephemeral=True)
            return

        # Calcular PC
        if nota is not None:
            if nota < 1.0 or nota > 5.0:
                await interaction.response.send_message("❌ La nota debe estar entre 1.0 y 5.0.", ephemeral=True)
                return
            pc = calcular_pc_por_nota(nota)
            if pc == 0:
                await interaction.response.send_message(
                    f"ℹ️ La nota **{nota}** es menor al mínimo aprobatorio (3.5). No se otorgan PC.",
                    ephemeral=True)
                return
            motivo_completo = f"Nota académica {nota} — {motivo}"

        elif pc_directos is not None:
            if pc_directos < PC_TRABAJO_SUCIO_MIN or pc_directos > PC_TRABAJO_SUCIO_MAX:
                await interaction.response.send_message(
                    f"❌ Los PC directos deben estar entre {PC_TRABAJO_SUCIO_MIN} y {PC_TRABAJO_SUCIO_MAX} (Trabajo Sucio del Consejo).",
                    ephemeral=True)
                return
            pc = pc_directos
            motivo_completo = f"Trabajo Sucio (Consejo) — {motivo}"

        else:
            await interaction.response.send_message(
                "❌ Debes indicar una `nota` o `pc_directos`.", ephemeral=True)
            return

        # Guardar en Sheets
        _sumar_pc(usuario.id, personaje, pc, motivo_completo, str(interaction.user), str(usuario))

        # Balance actualizado
        balance = _get_pc(usuario.id, personaje)

        embed = discord.Embed(
            title="✅ PC asignados",
            color=COLOR_APROBADO
        )
        embed.add_field(name="Personaje", value=personaje,              inline=True)
        embed.add_field(name="PC otorgados", value=f"**+{pc} PC**",    inline=True)
        embed.add_field(name="Motivo",    value=motivo_completo,        inline=False)
        embed.add_field(name="Balance actual",
            value=f"Disponibles: **{balance['pc_disponible']} PC** | Total histórico: **{balance['pc_total']} PC**",
            inline=False)
        embed.set_footer(text=f"Asignado por {interaction.user.display_name}")

        await interaction.response.send_message(embed=embed, ephemeral=False)

        # Notificar al usuario
        try:
            embed_u = discord.Embed(
                title="🎓 ¡Recibiste Puntos de Canje Académico!",
                description=(
                    f"Tu personaje **{personaje}** recibió **{pc} PC**.\n\n"
                    f"**Motivo:** {motivo_completo}\n\n"
                    f"Ahora tienes **{balance['pc_disponible']} PC disponibles**.\n"
                    f"Úsalos con `/canjear-pc` para reducir sanciones."
                ),
                color=COLOR_APROBADO
            )
            await usuario.send(embed=embed_u)
        except Exception:
            pass

    # ──────────────────────────────────────────
    # /aplicar-sancion @usuario personaje tipo duracion
    # ──────────────────────────────────────────

    @app_commands.command(
        name="aplicar-sancion",
        description="[STAFF/PROF/CONSEJO] Aplicar una sanción a un personaje estudiante."
    )
    @app_commands.describe(
        usuario="El usuario dueño del personaje",
        personaje="Nombre exacto del personaje",
        tipo="Tipo de sanción",
        duracion="Duración en minutos (castigo/detención) o días (suspensión)",
        motivo="Motivo de la sanción"
    )
    @app_commands.choices(tipo=[
        app_commands.Choice(name="⚠️ Castigo Menor (5-20 min de rol)", value="castigo_menor"),
        app_commands.Choice(name="🔒 Detención (30-120 min de rol)",    value="detencion"),
        app_commands.Choice(name="🚫 Suspensión (2-3 días IRL)",        value="suspension"),
    ])
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def aplicar_sancion(self,
                               interaction: discord.Interaction,
                               usuario: discord.Member,
                               personaje: str,
                               tipo: str,
                               duracion: int,
                               motivo: str):

        if not _tiene_autoridad(interaction):
            await interaction.response.send_message(
                "❌ No tienes autoridad para aplicar sanciones.", ephemeral=True)
            return

        config = TIPOS_SANCION[tipo]

        # Validar duración
        if tipo in ("castigo_menor", "detencion"):
            if not (config["duracion_min"] <= duracion <= config["duracion_max"]):
                await interaction.response.send_message(
                    f"❌ La duración para **{config['nombre']}** debe estar entre "
                    f"**{config['duracion_min']}** y **{config['duracion_max']}** minutos.",
                    ephemeral=True)
                return
        elif tipo == "suspension":
            if not (config["duracion_min"] <= duracion <= config["duracion_max"]):
                await interaction.response.send_message(
                    f"❌ La suspensión debe ser de **{config['duracion_min']}** a **{config['duracion_max']}** días.",
                    ephemeral=True)
                return

        # Registrar sanción
        _registrar_sancion(usuario.id, str(usuario), personaje, tipo, duracion, motivo, str(interaction.user))

        unidad = "minutos de rol" if tipo != "suspension" else "días IRL"

        embed = discord.Embed(
            title=f"⚠️ Sanción aplicada — {config['nombre']}",
            color=COLOR_RECHAZADO
        )
        embed.add_field(name="Personaje", value=personaje, inline=True)
        embed.add_field(name="Usuario",   value=usuario.mention, inline=True)
        embed.add_field(name="Duración",  value=f"**{duracion} {unidad}**", inline=True)
        embed.add_field(name="Motivo",    value=motivo, inline=False)
        embed.add_field(
            name="ℹ️ Canje disponible",
            value=(
                f"El estudiante puede usar `/canjear-pc {personaje}` "
                f"para reducir esta sanción con sus PC acumulados."
            ),
            inline=False
        )
        embed.set_footer(text=f"Aplicado por {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

        # Notificar al usuario
        try:
            embed_u = discord.Embed(
                title=f"⚠️ Sanción recibida — {config['nombre']}",
                description=(
                    f"Tu personaje **{personaje}** ha recibido una sanción.\n\n"
                    f"**Tipo:** {config['nombre']}\n"
                    f"**Duración:** {duracion} {unidad}\n"
                    f"**Motivo:** {motivo}\n\n"
                    f"Puedes usar `/canjear-pc {personaje}` para reducir el tiempo con tus PC."
                ),
                color=COLOR_RECHAZADO
            )
            await usuario.send(embed=embed_u)
        except Exception:
            pass

    # ──────────────────────────────────────────
    # /ver-pc [usuario] [personaje]
    # ──────────────────────────────────────────

    @app_commands.command(
        name="ver-pc",
        description="Ver el balance de PC y sanciones activas de un personaje."
    )
    @app_commands.describe(
        personaje="Nombre del personaje a consultar",
        usuario="(Opcional) Usuario a consultar — solo Staff/Prof/Consejo pueden ver los de otros"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def ver_pc(self,
                     interaction: discord.Interaction,
                     personaje: str,
                     usuario: discord.Member | None = None):

        # Si no se especifica usuario, es el propio
        target = usuario or interaction.user
        if usuario and usuario != interaction.user and not _tiene_autoridad(interaction):
            await interaction.response.send_message(
                "❌ Solo Staff, Profesores y Consejo pueden ver los PC de otros.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        balance   = _get_pc(target.id, personaje)
        sanciones = _get_sanciones_activas(target.id, personaje)

        embed = discord.Embed(
            title=f"🎓 PC de {personaje}",
            color=COLOR_INFO
        )
        embed.set_author(name=target.display_name, icon_url=target.display_avatar.url)
        embed.add_field(
            name="💎 Balance de Puntos de Canje",
            value=(
                f"Disponibles: **{balance['pc_disponible']} PC**\n"
                f"Total histórico: **{balance['pc_total']} PC**\n"
                f"Gastados: **{balance['pc_total'] - balance['pc_disponible']} PC**"
            ),
            inline=False
        )

        if sanciones:
            lines = []
            for i, s in enumerate(sanciones):
                tipo_cfg = TIPOS_SANCION.get(s.get("tipo",""), {})
                unidad   = "min" if s.get("tipo") != "suspension" else "días"
                lines.append(
                    f"**{i+1}.** {tipo_cfg.get('nombre', s.get('tipo','?'))} — "
                    f"**{s.get('duracion','?')} {unidad}** "
                    f"*(por {s.get('asignado_por','?')})*"
                )
            embed.add_field(name="⚠️ Sanciones activas", value="\n".join(lines), inline=False)
            embed.add_field(
                name="💡 ¿Quieres reducir una sanción?",
                value=f"Usa `/canjear-pc {personaje}` para gastar tus PC.",
                inline=False
            )
        else:
            embed.add_field(name="✅ Sanciones activas", value="Ninguna", inline=False)

        await interaction.followup.send(embed=embed, ephemeral=True)

    # ──────────────────────────────────────────
    # /canjear-pc personaje
    # ──────────────────────────────────────────

    @app_commands.command(
        name="canjear-pc",
        description="Canjear tus PC para reducir una sanción activa."
    )
    @app_commands.describe(personaje="Nombre exacto de tu personaje")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def canjear_pc(self, interaction: discord.Interaction, personaje: str):

        await interaction.response.defer(ephemeral=True)

        # Verificar que el personaje es del usuario
        personajes = get_personajes_usuario(interaction.user.id)
        p_encontrado = next(
            (p for p in personajes if p["personaje"].strip().lower() == personaje.strip().lower()
             and p["tipo"] == "estudiante"), None)
        if not p_encontrado:
            await interaction.followup.send(
                f"❌ No encontré el personaje estudiante **{personaje}** en tus registros.", ephemeral=True)
            return

        # Ver sanciones activas
        sanciones = _get_sanciones_activas(interaction.user.id, personaje)
        if not sanciones:
            await interaction.followup.send(
                f"✅ **{personaje}** no tiene sanciones activas que canjear.", ephemeral=True)
            return

        balance = _get_pc(interaction.user.id, personaje)
        if balance["pc_disponible"] == 0:
            await interaction.followup.send(
                f"❌ **{personaje}** no tiene PC disponibles para canjear.", ephemeral=True)
            return

        # Mostrar panel de canje
        view = CanjeView(
            user_id=interaction.user.id,
            personaje=personaje,
            sanciones=sanciones,
            balance=balance,
        )
        embed = view.build_embed()
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    # ──────────────────────────────────────────
    # /historial-pc personaje
    # ──────────────────────────────────────────

    @app_commands.command(
        name="historial-pc",
        description="Ver el historial completo de PC de un personaje."
    )
    @app_commands.describe(personaje="Nombre del personaje")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def historial_pc(self, interaction: discord.Interaction, personaje: str):
        await interaction.response.defer(ephemeral=True)
        from utils.sheets import get_sheet
        try:
            rows = get_sheet("HistorialPC").get_all_records()
            historial = [r for r in rows
                         if str(r.get("user_id","")) == str(interaction.user.id) and
                         r.get("personaje","").strip().lower() == personaje.strip().lower()]
        except Exception:
            historial = []

        if not historial:
            await interaction.followup.send(
                f"ℹ️ **{personaje}** no tiene historial de PC aún.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"📋 Historial de PC — {personaje}",
            color=COLOR_INFO
        )
        lines = []
        for r in historial[-10:]:  # últimos 10
            lines.append(
                f"**+{r.get('pc_otorgados','?')} PC** — {r.get('motivo','?')} "
                f"*(por {r.get('asignado_por','?')} · {r.get('fecha','?')})*"
            )
        embed.description = "\n".join(lines)
        if len(historial) > 10:
            embed.set_footer(text=f"Mostrando los últimos 10 de {len(historial)} registros.")
        await interaction.followup.send(embed=embed, ephemeral=True)


# ──────────────────────────────────────────────
# VIEW — Panel de canje
# ──────────────────────────────────────────────

class CanjeView(discord.ui.View):
    def __init__(self, user_id: int, personaje: str, sanciones: list, balance: dict):
        super().__init__(timeout=120)
        self.user_id   = user_id
        self.personaje = personaje
        self.sanciones = sanciones
        self.balance   = balance
        self.sancion_idx = 0  # índice de la sanción seleccionada
        self._add_sancion_select()

    def _add_sancion_select(self):
        options = []
        for i, s in enumerate(self.sanciones):
            tipo_cfg = TIPOS_SANCION.get(s.get("tipo",""), {})
            unidad   = "min" if s.get("tipo") != "suspension" else "días"
            options.append(discord.SelectOption(
                label=f"{tipo_cfg.get('nombre','?')} — {s.get('duracion','?')} {unidad}",
                value=str(i),
                description=f"Por: {s.get('asignado_por','?')}"
            ))
        select = discord.ui.Select(
            placeholder="📋 Selecciona la sanción a reducir...",
            options=options,
            min_values=1, max_values=1
        )
        select.callback = self._on_sancion_select
        self.add_item(select)

    async def _on_sancion_select(self, interaction: discord.Interaction):
        self.sancion_idx = int(interaction.data["values"][0])
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    def build_embed(self) -> discord.Embed:
        s        = self.sanciones[self.sancion_idx]
        tipo     = s.get("tipo", "castigo_menor")
        cfg      = TIPOS_SANCION.get(tipo, {})
        duracion = int(s.get("duracion", 20))
        unidad   = "min de rol" if tipo != "suspension" else "días IRL"
        disp     = self.balance["pc_disponible"]

        embed = discord.Embed(
            title=f"💎 Canjear PC — {self.personaje}",
            color=COLOR_INFO
        )
        embed.add_field(
            name="Sanción seleccionada",
            value=f"**{cfg.get('nombre','?')}** — {duracion} {unidad}\n*Motivo: {s.get('motivo','?')}*",
            inline=False
        )
        embed.add_field(name="PC disponibles", value=f"**{disp} PC**", inline=True)

        # Calcular opciones de canje
        if tipo == "castigo_menor":
            r1 = calcular_reduccion_castigo_menor(1, duracion)
            r_max = calcular_reduccion_castigo_menor(10, duracion)
            embed.add_field(
                name="📊 Opciones de canje",
                value=(
                    f"**1 PC** → -{r1['minutos_reducidos']:.1f} min → quedan **{r1['tiempo_final']:.1f} min**\n"
                    f"**10 PC** → -{r_max['minutos_reducidos']:.1f} min + 1 min bono → quedan **{r_max['tiempo_final']:.1f} min** ✨"
                ),
                inline=False
            )
        elif tipo == "detencion":
            r1   = calcular_reduccion_detencion(1, duracion)
            r_max = calcular_reduccion_detencion(int(duracion * 0.8 / 2.5), duracion)
            pc_max = int(duracion * 0.8 / 2.5)
            embed.add_field(
                name="📊 Opciones de canje",
                value=(
                    f"**1 PC** → -{r1['minutos_reducidos']:.1f} min → quedan **{r1['tiempo_final']:.1f} min**\n"
                    f"**{pc_max} PC** (máximo) → -{r_max['minutos_reducidos']:.1f} min → quedan **{r_max['tiempo_final']:.1f} min**\n"
                    f"*Mínimo obligatorio: {r_max['min_obligatorio']} min*"
                ),
                inline=False
            )
        elif tipo == "suspension":
            embed.add_field(
                name="📊 Opciones de canje",
                value=(
                    f"**20 PC** → reduce 1 día IRL\n"
                    f"*Siempre queda al menos 1 día obligatorio.*\n"
                    f"*Requiere autorización del Staff para activarse.*"
                ),
                inline=False
            )

        embed.set_footer(text="Usa el botón para confirmar el canje.")
        return embed

    @discord.ui.button(label="💎 Confirmar canje", style=discord.ButtonStyle.primary, row=1)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            ConfirmarCanjeModal(
                user_id=self.user_id, personaje=self.personaje,
                sancion=self.sanciones[self.sancion_idx],
                sancion_idx=self.sancion_idx,
                balance=self.balance,
            )
        )
        self.stop()

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary, row=1)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Cancelado.", embed=None, view=None)
        self.stop()


class ConfirmarCanjeModal(discord.ui.Modal, title="💎 Confirmar canje de PC"):
    pc_a_gastar = discord.ui.TextInput(
        label="¿Cuántos PC quieres gastar?",
        placeholder="Ingresa un número",
        min_length=1, max_length=3
    )

    def __init__(self, user_id, personaje, sancion, sancion_idx, balance):
        super().__init__()
        self.user_id     = user_id
        self.personaje   = personaje
        self.sancion     = sancion
        self.sancion_idx = sancion_idx
        self.balance     = balance

    async def on_submit(self, interaction: discord.Interaction):
        try:
            pc = int(self.pc_a_gastar.value.strip())
        except ValueError:
            await interaction.response.send_message("❌ Ingresa un número válido.", ephemeral=True)
            return

        disp = self.balance["pc_disponible"]
        if pc > disp:
            await interaction.response.send_message(
                f"❌ No tienes suficientes PC. Tienes **{disp} PC** disponibles.", ephemeral=True)
            return
        if pc < 1:
            await interaction.response.send_message("❌ Debes gastar al menos 1 PC.", ephemeral=True)
            return

        tipo     = self.sancion.get("tipo", "castigo_menor")
        duracion = int(self.sancion.get("duracion", 20))

        # Calcular resultado
        if tipo == "castigo_menor":
            resultado = calcular_reduccion_castigo_menor(pc, duracion)
            resumen = (
                f"**{pc} PC** gastados\n"
                f"Reducción: **{resultado['minutos_reducidos']:.1f} min**"
                f"{' + 1 min bono ✨' if resultado['bonificacion'] else ''}\n"
                f"Tiempo final del castigo: **{resultado['tiempo_final']:.1f} min de rol**"
            )
        elif tipo == "detencion":
            resultado = calcular_reduccion_detencion(pc, duracion)
            resumen = (
                f"**{pc} PC** gastados\n"
                f"Reducción: **{resultado['minutos_reducidos']:.1f} min**\n"
                f"Tiempo final de detención: **{resultado['tiempo_final']:.1f} min de rol**"
            )
        elif tipo == "suspension":
            resultado = calcular_reduccion_suspension(pc, duracion)
            if resultado["dias_a_reducir"] == 0:
                await interaction.response.send_message(
                    f"❌ Necesitas al menos **20 PC** para reducir 1 día de suspensión. Tienes **{disp} PC**.",
                    ephemeral=True)
                return
            resumen = (
                f"**{resultado['pc_usados']} PC** gastados\n"
                f"Reducción: **{resultado['dias_reducidos']} día(s)**\n"
                f"Suspensión final: **{resultado['dias_final']} día(s) IRL**\n"
                f"*Pendiente de autorización del Staff.*"
            )
            pc = resultado["pc_usados"]  # solo gastar los que se usan

        # Descontar PC
        ok = _restar_pc(self.user_id, self.personaje, pc)
        if not ok:
            await interaction.response.send_message(
                "❌ Error al procesar el canje. Intenta de nuevo.", ephemeral=True)
            return

        # Registrar en historial
        from utils.sheets import get_sheet
        try:
            get_sheet("HistorialPC").append_row(
                [str(self.user_id), self.personaje, f"-{pc}",
                 f"Canje sanción: {TIPOS_SANCION[tipo]['nombre']}",
                 str(interaction.user), _now()],
                value_input_option="USER_ENTERED")
        except Exception: pass

        balance_nuevo = _get_pc(self.user_id, self.personaje)

        embed = discord.Embed(
            title="✅ Canje procesado",
            description=resumen,
            color=COLOR_APROBADO
        )
        embed.add_field(
            name="Balance restante",
            value=f"**{balance_nuevo['pc_disponible']} PC** disponibles",
            inline=False
        )
        if tipo == "suspension":
            embed.add_field(
                name="⚠️ Pendiente",
                value="Un miembro del Staff debe autorizar la reducción de suspensión.",
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(PCA(bot))
