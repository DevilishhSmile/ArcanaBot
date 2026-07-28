import discord
from discord import app_commands
from discord.ext import commands

from utils.constants import (
    GUILD_ID, CANAL_ENVIAR_UNIFORME, ROL_STAFF,
    COLOR_APROBADO, COLOR_RECHAZADO, COLOR_PENDIENTE, CASAS,
)
from utils.helpers import is_valid_character_name, clean_field, build_review_embed
from utils.sheets import aprobar_uniforme, rechazar_uniforme
from utils.image_handler import registrar_espera


class UniformeModal(discord.ui.Modal, title="👕 Registro de Uniforme"):
    personaje = discord.ui.TextInput(
        label="Nombre del personaje",
        placeholder="Ej: Lysander Vael",
        min_length=2, max_length=50,
    )

    async def on_submit(self, interaction: discord.Interaction):
        nombre = self.personaje.value.strip()
        if not is_valid_character_name(nombre):
            await interaction.response.send_message(
                "❌ El nombre no es válido. Solo letras, espacios y guiones.", ephemeral=True)
            return

        # Guardar nombre en temp y mostrar selector de casa
        if not hasattr(interaction.client, "_uniforme_temp"):
            interaction.client._uniforme_temp = {}
        interaction.client._uniforme_temp[interaction.user.id] = {
            "personaje": clean_field(nombre),
            "user_id":   interaction.user.id,
            "username":  str(interaction.user),
        }

        await interaction.response.send_message(
            f"✅ Nombre registrado: **{clean_field(nombre)}**\n\n"
            f"🏠 Ahora selecciona la **casa** a la que pertenece este personaje:",
            view=CasaSelectView(
                user_id=interaction.user.id,
                canal_id=interaction.channel_id,
            ),
            ephemeral=True,
        )


class CasaSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=casa, value=casa, emoji="🏠")
            for casa in CASAS
        ]
        super().__init__(
            placeholder="🏠 Selecciona la casa del personaje...",
            min_values=1, max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        casa = self.values[0]
        view: CasaSelectView = self.view

        # Guardar casa en temp
        temp = getattr(interaction.client, "_uniforme_temp", {})
        data = temp.get(interaction.user.id, {})
        data["casa"] = casa
        temp[interaction.user.id] = data

        # Registrar espera de imagen
        registrar_espera(
            user_id=interaction.user.id,
            tipo="uniforme",
            canal_id=view.canal_id,
            data=data,
        )

        await interaction.response.edit_message(
            content=(
                f"✅ **Casa:** {casa}\n\n"
                f"📎 Ahora **envía la imagen del uniforme en este canal**.\n"
                f"Pégala desde el portapapeles 📋 o adjúntala desde tu galería 🖼️\n\n"
                f"*Escribe `sin imagen` si no tienes una todavía.*"
            ),
            view=None,
        )
        view.stop()


class CasaSelectView(discord.ui.View):
    def __init__(self, user_id: int, canal_id: int):
        super().__init__(timeout=120)
        self.user_id  = user_id
        self.canal_id = canal_id
        self.add_item(CasaSelect())


class RechazoUniformeModal(discord.ui.Modal, title="✏️ Motivo de rechazo"):
    motivo = discord.ui.TextInput(
        label="¿Por qué se rechaza?",
        style=discord.TextStyle.paragraph,
        placeholder="Explica el motivo al usuario...",
        required=False, max_length=500,
    )

    def __init__(self, data, review_message):
        super().__init__()
        self.data = data
        self.review_message = review_message

    async def on_submit(self, interaction: discord.Interaction):
        m = self.motivo.value.strip() if self.motivo.value else "Sin motivo especificado."
        try:
            rechazar_uniforme(self.data["user_id"], self.data["personaje"],
                              str(interaction.user), m)
        except Exception as e:
            print(f"[UNIFORMES] Sheets rechazar: {e}")

        canal = interaction.client.get_channel(CANAL_ENVIAR_UNIFORME)
        embed = discord.Embed(
            title="❌ Uniforme rechazado",
            description=(
                f"Hola <@{self.data['user_id']}>, tu uniforme para "
                f"**{self.data['personaje']}** fue rechazado.\n\n"
                f"**Motivo:**\n{m}\n\n"
                f"Corrígelo y reenvíalo con `/uniforme`. 💪"
            ),
            color=COLOR_RECHAZADO,
        )
        if self.data.get("imagen"):
            embed.set_image(url=self.data["imagen"])
        if canal:
            await canal.send(embed=embed)
        else:
            try:
                u = await interaction.client.fetch_user(self.data["user_id"])
                await u.send(embed=embed)
            except Exception:
                pass

        updated = discord.Embed(
            title="👕 Uniforme — RECHAZADO",
            description=(
                f"**Personaje:** {self.data['personaje']}\n"
                f"**Casa:** {self.data.get('casa','—')}\n"
                f"**Usuario:** <@{self.data['user_id']}>\n\n"
                f"**Motivo:**\n{m}"
            ),
            color=COLOR_RECHAZADO,
        )
        updated.set_footer(text=f"Rechazado por {interaction.user.display_name}")
        await self.review_message.edit(embed=updated, view=None)
        await interaction.response.send_message("✅ Rechazo procesado.", ephemeral=True)


class UniformeReviewView(discord.ui.View):
    def __init__(self, data):
        super().__init__(timeout=None)
        self.data = data

    def _es_staff(self, i):
        return any(r.id == ROL_STAFF for r in i.user.roles)

    @discord.ui.button(label="✅ Aprobar", style=discord.ButtonStyle.success,
                       custom_id="uniforme_aprobar")
    async def aprobar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._es_staff(interaction):
            await interaction.response.send_message("❌ Solo el staff puede.", ephemeral=True)
            return

        try:
            aprobar_uniforme(
                self.data["user_id"], self.data["personaje"],
                self.data.get("imagen", ""), str(interaction.user),
            )
        except Exception as e:
            print(f"[UNIFORMES] Sheets aprobar: {e}")

        canal = interaction.client.get_channel(CANAL_ENVIAR_UNIFORME)
        embed = discord.Embed(
            title="✅ Uniforme aprobado",
            description=(
                f"¡Felicidades <@{self.data['user_id']}>! "
                f"Tu uniforme para **{self.data['personaje']}** "
                f"(Casa **{self.data.get('casa','—')}**) fue aprobado. 🎉\n\n"
                f"Ya puedes registrar tu ficha."
            ),
            color=COLOR_APROBADO,
        )
        if self.data.get("imagen"):
            embed.set_image(url=self.data["imagen"])
        if canal:
            await canal.send(embed=embed)
        else:
            try:
                u = await interaction.client.fetch_user(self.data["user_id"])
                await u.send(embed=embed)
            except Exception:
                pass

        updated = discord.Embed(
            title="👕 Uniforme — APROBADO ✅",
            description=(
                f"**Personaje:** {self.data['personaje']}\n"
                f"**Casa:** {self.data.get('casa','—')}\n"
                f"**Usuario:** <@{self.data['user_id']}>"
            ),
            color=COLOR_APROBADO,
        )
        if self.data.get("imagen"):
            updated.set_image(url=self.data["imagen"])
        updated.set_footer(text=f"Aprobado por {interaction.user.display_name}")
        await interaction.message.edit(embed=updated, view=None)
        await interaction.response.send_message("✅ Uniforme aprobado.", ephemeral=True)

    @discord.ui.button(label="❌ Rechazar", style=discord.ButtonStyle.danger,
                       custom_id="uniforme_rechazar")
    async def rechazar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._es_staff(interaction):
            await interaction.response.send_message("❌ Solo el staff puede.", ephemeral=True)
            return
        await interaction.response.send_modal(
            RechazoUniformeModal(data=self.data, review_message=interaction.message))


class Uniformes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="uniforme",
        description="Registra el uniforme de tu personaje.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def uniforme(self, interaction: discord.Interaction):
        if CANAL_ENVIAR_UNIFORME and interaction.channel_id != CANAL_ENVIAR_UNIFORME:
            canal = self.bot.get_channel(CANAL_ENVIAR_UNIFORME)
            mencionar = canal.mention if canal else f"<#{CANAL_ENVIAR_UNIFORME}>"
            await interaction.response.send_message(
                f"❌ Usa este comando en {mencionar}.", ephemeral=True)
            return
        await interaction.response.send_modal(UniformeModal())


async def setup(bot):
    await bot.add_cog(Uniformes(bot))
