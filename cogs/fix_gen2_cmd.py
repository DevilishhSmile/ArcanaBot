"""
Cog temporal para resetear slots de Gen 2 desde Discord.
Añadir a cogs/, usarlo UNA VEZ, luego eliminar.
"""
import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "isefora.db")
from utils.constants import GUILD_ID, ROL_STAFF

class FixGen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="fix-gen2",
        description="[STAFF] Resetea todos los slots de Gen 2 a 0.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def fix_gen2(self, interaction: discord.Interaction):
        if not any(r.id == ROL_STAFF for r in interaction.user.roles):
            await interaction.response.send_message("❌ Solo el staff.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        async with aiosqlite.connect(DB_PATH) as db:
            # Ver cuántos registros hay en Gen 2
            cur = await db.execute(
                "SELECT COUNT(*) FROM slots_usuarios WHERE generacion = 2")
            total = (await cur.fetchone())[0]

            # Ver el estado antes
            cur = await db.execute(
                "SELECT user_id, estudiantes_usados, profesores_usados, trabajadores_usados "
                "FROM slots_usuarios WHERE generacion = 2")
            rows = await cur.fetchall()

            # Resetear
            await db.execute("""
                UPDATE slots_usuarios SET
                    estudiantes_usados      = 0,
                    trabajadores_usados     = 0,
                    profesores_usados       = 0,
                    slots_extra_disponibles = 0,
                    slots_extra_usados      = 0
                WHERE generacion = 2
            """)
            await db.commit()

        # Mostrar resumen
        detalle = "\n".join(
            f"• `{r[0]}` — est:{r[1]} prof:{r[2]} trab:{r[3]}"
            for r in rows[:15]
        ) or "Ninguno"

        embed = discord.Embed(
            title="✅ Slots de Gen 2 reseteados",
            description=(
                f"**Registros encontrados:** {total}\n\n"
                f"**Usuarios reseteados:**\n{detalle}\n\n"
                f"Todos los conteos de Gen 2 quedaron en 0."
            ),
            color=0x27AE60
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(FixGen(bot))
