import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite, os
from utils.constants import GUILD_ID, ROL_STAFF
from utils.database import DB_PATH

class DebugDB(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="debug-db", description="[STAFF] Debug completo de la DB.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def debug_db(self, interaction: discord.Interaction):
        if not any(r.id == ROL_STAFF for r in interaction.user.roles):
            await interaction.response.send_message("❌", ephemeral=True); return
        await interaction.response.defer(ephemeral=True)

        from cogs.admin import cargar_generacion
        from utils.database import get_conteo_usuario
        gen = cargar_generacion()

        # Buscar TODOS los archivos .db en el sistema
        db_files = []
        for root, dirs, files in os.walk("/app"):
            for f in files:
                if f.endswith(".db"):
                    full = os.path.join(root, f)
                    db_files.append(f"`{full}` ({os.path.getsize(full)} bytes)")

        # Leer DB_PATH directamente
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute("SELECT user_id, generacion, estudiantes_usados, profesores_usados FROM slots_usuarios")
            rows_directo = await cur.fetchall()

        # Llamar get_conteo_usuario igual que mis_personajes
        conteo = await get_conteo_usuario(interaction.user.id, gen)

        lineas = [
            f"**DB_PATH:** `{DB_PATH}`",
            f"**Gen:** `{gen}`",
            f"**Archivos .db encontrados:**",
        ] + db_files + [
            f"",
            f"**Registros en DB_PATH:** {len(rows_directo)}",
        ] + [f"• user=`{r[0]}` gen=`{r[1]}` est={r[2]} prof={r[3]}" for r in rows_directo] + [
            f"",
            f"**get_conteo_usuario para ti:** `{dict(conteo)}`",
        ]

        await interaction.followup.send("\n".join(lineas[:40]), ephemeral=True)

    @app_commands.command(name="reset-gen", description="[STAFF] Resetear slots de una generación.")
    @app_commands.describe(generacion="Generación a resetear")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def reset_gen(self, interaction: discord.Interaction, generacion: int):
        if not any(r.id == ROL_STAFF for r in interaction.user.roles):
            await interaction.response.send_message("❌", ephemeral=True); return
        await interaction.response.defer(ephemeral=True)

        # Buscar TODOS los archivos .db y resetear en cada uno
        resultados = []
        for root, dirs, files in os.walk("/app"):
            for f in files:
                if f.endswith(".db"):
                    full = os.path.join(root, f)
                    try:
                        async with aiosqlite.connect(full) as db:
                            cur = await db.execute(
                                "SELECT COUNT(*) FROM slots_usuarios WHERE generacion = ?",
                                (generacion,))
                            count = (await cur.fetchone())[0]
                            if count > 0:
                                await db.execute("""
                                    UPDATE slots_usuarios SET
                                        estudiantes_usados=0, trabajadores_usados=0,
                                        profesores_usados=0, slots_extra_disponibles=0,
                                        slots_extra_usados=0
                                    WHERE generacion=?
                                """, (generacion,))
                                await db.commit()
                                resultados.append(f"✅ `{full}` — {count} usuario(s) reseteados")
                            else:
                                resultados.append(f"ℹ️ `{full}` — sin registros Gen {generacion}")
                    except Exception as e:
                        resultados.append(f"❌ `{full}` — {e}")

        embed = discord.Embed(
            title=f"🔄 Reset Gen {generacion} — Todos los archivos DB",
            description="\n".join(resultados) or "No se encontraron archivos .db",
            color=0x27AE60)
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(DebugDB(bot))
