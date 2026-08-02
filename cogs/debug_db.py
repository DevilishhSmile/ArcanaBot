import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite, os
from utils.constants import GUILD_ID, ROL_STAFF

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "isefora.db")

class DebugDB(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="debug-db", description="[STAFF] Ver slots reales en SQLite.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def debug_db(self, interaction: discord.Interaction):
        if not any(r.id == ROL_STAFF for r in interaction.user.roles):
            await interaction.response.send_message("❌", ephemeral=True); return
        await interaction.response.defer(ephemeral=True)

        from cogs.admin import cargar_generacion
        gen_actual = cargar_generacion()

        async with aiosqlite.connect(DB_PATH) as db:
            # Todos los registros de la DB
            cur = await db.execute("SELECT user_id, generacion, estudiantes_usados, profesores_usados, trabajadores_usados FROM slots_usuarios ORDER BY generacion, user_id")
            rows = await cur.fetchall()

        if not rows:
            await interaction.followup.send("La base de datos está completamente vacía.", ephemeral=True)
            return

        lineas = [f"`generacion_actual = {gen_actual}` (según cargar_generacion)\n"]
        for r in rows:
            lineas.append(f"user=`{r[0]}` gen=`{r[1]}` | est={r[2]} prof={r[3]} trab={r[4]}")

        await interaction.followup.send("\n".join(lineas[:25]), ephemeral=True)

async def setup(bot):
    await bot.add_cog(DebugDB(bot))
