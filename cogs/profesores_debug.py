import discord
from discord import app_commands
from discord.ext import commands
import traceback

from utils.constants import GUILD_ID, CANAL_REGISTRO_TRABAJOS, MATERIAS, MATERIAS_LIMITE
from utils.sheets import get_profesores_aprobados_por_materia

class MateriaSelectDebug(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=m, value=m) for m in MATERIAS]
        super().__init__(
            placeholder="📚 Selecciona la materia...",
            min_values=1, max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        print(f"[DEBUG] Select callback ejecutado por {interaction.user} — materia: {self.values[0]}")
        try:
            materia  = self.values[0]
            limite   = MATERIAS_LIMITE.get(materia, 1)

            print(f"[DEBUG] Verificando cupos en Sheets para: {materia}")
            ocupados = get_profesores_aprobados_por_materia(materia)
            print(f"[DEBUG] Ocupados: {ocupados} / Límite: {limite}")

            if ocupados >= limite:
                await interaction.response.send_message(
                    f"❌ **{materia}** ya no tiene cupos.", ephemeral=True)
                return

            print(f"[DEBUG] Editando mensaje con botón de confirmación...")
            await interaction.response.edit_message(
                content=f"✅ Materia: **{materia}**\nPresiona para continuar.",
                view=ConfirmarMateriaViewDebug(materia=materia, user_id=interaction.user.id),
            )
            print(f"[DEBUG] Mensaje editado exitosamente")

        except Exception as e:
            print(f"[DEBUG ERROR] En select callback: {e}")
            traceback.print_exc()
            try:
                await interaction.response.send_message(
                    f"❌ Error interno: {e}", ephemeral=True)
            except Exception:
                pass

class MateriaSelectViewDebug(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(MateriaSelectDebug())

class ConfirmarMateriaViewDebug(discord.ui.View):
    def __init__(self, materia: str, user_id: int):
        super().__init__(timeout=120)
        self.materia = materia
        self.user_id = user_id

    @discord.ui.button(label="📝 Continuar", style=discord.ButtonStyle.primary)
    async def continuar(self, interaction: discord.Interaction, button: discord.ui.Button):
        print(f"[DEBUG] Botón continuar presionado por {interaction.user}")
        await interaction.response.send_message(
            f"✅ Funciona. Materia: **{self.materia}**\n\nEl flujo completo va aquí.",
            ephemeral=True
        )
        self.stop()

class ProfesoresDebug(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"[DEBUG] Cog ProfesoresDebug inicializado")

    @app_commands.command(
        name="test-profesor",
        description="[DEBUG] Prueba el flujo de profesor paso a paso."
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def test_profesor(self, interaction: discord.Interaction):
        print(f"[DEBUG] Comando /test-profesor ejecutado por {interaction.user} en canal {interaction.channel_id}")
        try:
            await interaction.response.send_message(
                "📚 **[DEBUG] Selecciona la materia:**",
                view=MateriaSelectViewDebug(),
                ephemeral=True,
            )
            print(f"[DEBUG] Mensaje enviado exitosamente")
        except Exception as e:
            print(f"[DEBUG ERROR] Al enviar mensaje: {e}")
            traceback.print_exc()

async def setup(bot):
    print(f"[DEBUG] Cargando cog ProfesoresDebug...")
    await bot.add_cog(ProfesoresDebug(bot))
    print(f"[DEBUG] Cog ProfesoresDebug cargado")
