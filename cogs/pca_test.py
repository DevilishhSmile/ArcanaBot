import discord
from discord import app_commands
from discord.ext import commands
from utils.constants import GUILD_ID, COLOR_INFO

class PCATest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="test-pca-1",
        description="[DEBUG] Test básico sin Sheets")
    @app_commands.describe(usuario="El usuario")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def test1(self, interaction: discord.Interaction, usuario: discord.Member):
        print(f"[TEST1] Ejecutado por {interaction.user} para {usuario}")
        await interaction.response.send_message(
            f"✅ Test 1 OK — usuario: {usuario.display_name}", ephemeral=True)

    @app_commands.command(name="test-pca-2",
        description="[DEBUG] Test con defer sin Sheets")
    @app_commands.describe(usuario="El usuario")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def test2(self, interaction: discord.Interaction, usuario: discord.Member):
        print(f"[TEST2] Antes de defer — {interaction.user}")
        await interaction.response.defer(ephemeral=True)
        print(f"[TEST2] Después de defer")
        await interaction.followup.send(
            f"✅ Test 2 OK — defer funcionó para {usuario.display_name}", ephemeral=True)

    @app_commands.command(name="test-pca-3",
        description="[DEBUG] Test con defer + Sheets")
    @app_commands.describe(usuario="El usuario")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def test3(self, interaction: discord.Interaction, usuario: discord.Member):
        print(f"[TEST3] Antes de defer — {interaction.user}")
        await interaction.response.defer(ephemeral=True)
        print(f"[TEST3] Después de defer, llamando Sheets...")
        from utils.sheets import get_personajes_usuario
        personajes = get_personajes_usuario(usuario.id)
        print(f"[TEST3] Sheets respondió: {personajes}")
        await interaction.followup.send(
            f"✅ Test 3 OK — personajes: {[p['personaje'] for p in personajes]}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(PCATest(bot))
