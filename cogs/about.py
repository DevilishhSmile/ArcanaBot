import discord
from discord import app_commands
from discord.ext import commands
from utils.constants import GUILD_ID, COLOR_INFO
from cogs.admin import cargar_generacion


class About(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="about-bot",
        description="Información sobre el bot, sus funciones y créditos."
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def about_bot(self, interaction: discord.Interaction):
        gen = cargar_generacion()

        embed = discord.Embed(
            title="🪄 ArcanaBot",
            description=(
                "Bot de gestión para servidores de roleplay temáticos.\n"
                "Automatiza el registro de personajes, revisión por staff, "
                "sistema de puntos de conducta, poderes y más."
            ),
            color=COLOR_INFO,
        )

        embed.add_field(
            name="📦 Funciones principales",
            value=(
                "• 🎓 Registro de estudiantes, profesores y trabajadores\n"
                "• 👕 Sistema de uniformes con selector de casa\n"
                "• ⭐ Puntos de Conducta Académica (PCA)\n"
                "• 🌀 Sistema de poderes con spin ponderado\n"
                "• ⚔️ Sistema de batallas\n"
                "• 🪪 Generación de carnets de identidad\n"
                "• 🛠️ Panel de administración para el staff"
            ),
            inline=False,
        )

        embed.add_field(
            name="🌐 Generación activa",
            value=f"Gen {gen}",
            inline=True,
        )

        embed.add_field(
            name="⚙️ Versión",
            value="discord.py 2.4.0 · Python 3.11",
            inline=True,
        )

        embed.add_field(
            name="👩‍💻 Desarrollado por",
            value="**Devilishh** (`devilishh.` en Discord)",
            inline=False,
        )

        embed.add_field(
            name="📄 Licencia",
            value="[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) — Libre de usar, no para vender.",
            inline=False,
        )

        embed.set_footer(text="ArcanaBot · Construido con ❤️ por Devilishh")

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(About(bot))
