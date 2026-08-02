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
            cur = await db.execute("SELECT user_id, generacion, estudiantes_usados, profesores_usados, trabajadores_usados FROM slots_usuarios ORDER BY generacion, user_id")
            rows = await cur.fetchall()
        if not rows:
            await interaction.followup.send("La base de datos está completamente vacía.", ephemeral=True)
            return
        lineas = [f"`generacion_actual = {gen_actual}`\n"]
        for r in rows:
            lineas.append(f"user=`{r[0]}` gen=`{r[1]}` | est={r[2]} prof={r[3]} trab={r[4]}")
        await interaction.followup.send("\n".join(lineas[:25]), ephemeral=True)

    @app_commands.command(name="reset-gen", description="[STAFF] Resetear slots de una generación a 0.")
    @app_commands.describe(generacion="Número de generación a resetear")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def reset_gen(self, interaction: discord.Interaction, generacion: int):
        if not any(r.id == ROL_STAFF for r in interaction.user.roles):
            await interaction.response.send_message("❌", ephemeral=True); return
        await interaction.response.defer(ephemeral=True)
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute(
                "SELECT user_id, estudiantes_usados, profesores_usados, trabajadores_usados FROM slots_usuarios WHERE generacion = ?",
                (generacion,))
            rows = await cur.fetchall()
            await db.execute("""
                UPDATE slots_usuarios SET
                    estudiantes_usados      = 0,
                    trabajadores_usados     = 0,
                    profesores_usados       = 0,
                    slots_extra_disponibles = 0,
                    slots_extra_usados      = 0
                WHERE generacion = ?
            """, (generacion,))
            await db.commit()
        detalle = "\n".join(
            f"• `{r[0]}` — est:{r[1]} prof:{r[2]} trab:{r[3]}"
            for r in rows
        ) or "Ninguno"
        embed = discord.Embed(
            title=f"✅ Gen {generacion} reseteada",
            description=f"**{len(rows)} usuario(s) reseteados:**\n{detalle}",
            color=0x27AE60)
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(DebugDB(bot))
