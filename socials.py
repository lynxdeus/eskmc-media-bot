"""Sistema de redes sociales para creadores."""
import discord
from discord import app_commands
from discord.ext import commands
from database import db
from utils.embeds import success_embed, error_embed, info_embed
from utils.checks import is_media_staff

SOCIAL_PLATFORMS = {
    "youtube": {"emoji": "📺", "name": "YouTube", "column": "youtube_link"},
    "tiktok": {"emoji": "📱", "name": "TikTok", "column": "tiktok_link"},
    "twitch": {"emoji": "🎮", "name": "Twitch", "column": "twitch_link"},
    "instagram": {"emoji": "📸", "name": "Instagram", "column": "instagram_link"},
    "twitter": {"emoji": "🐦", "name": "Twitter/X", "column": "twitter_link"},
    "kick": {"emoji": "🟢", "name": "Kick", "column": "kick_link"},
    "discord": {"emoji": "💬", "name": "Discord", "column": "discord_tag"},
}

class SocialsModal(discord.ui.Modal, title="Agregar/Actualizar Red Social"):
    link = discord.ui.TextInput(
        label="Link o usuario",
        placeholder="https://youtube.com/c/tucanal o @usuario",
        required=True,
        style=discord.TextStyle.short
    )

    def __init__(self, platform_key: str):
        super().__init__()
        self.platform_key = platform_key
        platform_info = SOCIAL_PLATFORMS[platform_key]
        self.title = f"{platform_info['emoji']} {platform_info['name']}"

    async def on_submit(self, interaction: discord.Interaction):
        creator = await db.get_creator(interaction.user.id)
        if not creator:
            await interaction.response.send_message(
                embed=error_embed("No eres creador del Media Team"), ephemeral=True
            )
            return

        column = SOCIAL_PLATFORMS[self.platform_key]["column"]
        await db.execute(
            f"UPDATE creators SET {column} = ? WHERE discord_id = ?",
            (self.link.value, interaction.user.id)
        )

        platform_name = SOCIAL_PLATFORMS[self.platform_key]["name"]
        await db.log_action("RED_SOCIAL_ACTUALIZADA", interaction.user.id, interaction.user.id,
                           f"{platform_name}: {self.link.value}")

        await interaction.response.send_message(
            embed=success_embed(
                "Red social actualizada",
                f"Tu {platform_name} ha sido guardado: `{self.link.value}`"
            ), ephemeral=True
        )

class SocialsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="Selecciona una red social para editar...",
        options=[
            discord.SelectOption(label="YouTube", value="youtube", emoji="📺", description="Agrega tu canal de YouTube"),
            discord.SelectOption(label="TikTok", value="tiktok", emoji="📱", description="Agrega tu TikTok"),
            discord.SelectOption(label="Twitch", value="twitch", emoji="🎮", description="Agrega tu Twitch"),
            discord.SelectOption(label="Instagram", value="instagram", emoji="📸", description="Agrega tu Instagram"),
            discord.SelectOption(label="Twitter/X", value="twitter", emoji="🐦", description="Agrega tu Twitter/X"),
            discord.SelectOption(label="Kick", value="kick", emoji="🟢", description="Agrega tu Kick"),
            discord.SelectOption(label="Discord", value="discord", emoji="💬", description="Agrega tu tag de Discord"),
        ]
    )
    async def select_social(self, interaction: discord.Interaction, select: discord.ui.Select):
        modal = SocialsModal(select.values[0])
        await interaction.response.send_modal(modal)

class Socials(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="socials", description="Gestionar tus redes sociales")
    async def socials(self, interaction: discord.Interaction):
        creator = await db.get_creator(interaction.user.id)
        if not creator:
            await interaction.response.send_message(
                embed=error_embed("No eres creador del Media Team"), ephemeral=True
            )
            return

        # Mostrar redes actuales
        socials_text = ""
        for key, info in SOCIAL_PLATFORMS.items():
            value = creator[info["column"]]
            if value:
                socials_text += f"{info['emoji']} **{info['name']}:** {value}\n"
            else:
                socials_text += f"{info['emoji']} **{info['name']}:** *No configurado*\n"

        embed = info_embed(
            "Tus Redes Sociales",
            f"Selecciona una red social del menu para agregarla o actualizarla.\n\n"
            f"**Redes actuales:**\n{socials_text}"
        )

        view = SocialsView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="socials-view", description="Ver redes sociales de un creador")
    async def view_socials(self, interaction: discord.Interaction,
                           usuario: discord.Member = None):
        target = usuario or interaction.user
        creator = await db.get_creator(target.id)

        if not creator:
            await interaction.response.send_message(
                embed=error_embed("El usuario no es creador del Media Team"), ephemeral=True
            )
            return

        socials_text = ""
        has_any = False
        for key, info in SOCIAL_PLATFORMS.items():
            value = creator[info["column"]]
            if value:
                socials_text += f"{info['emoji']} **{info['name']}:** {value}\n"
                has_any = True

        if not has_any:
            socials_text = "*Este creador no ha configurado sus redes sociales.*\n"
            socials_text += f"Usa `/socials` para agregarlas."

        embed = info_embed(
            f"Redes Sociales de {target.display_name}",
            socials_text
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="socials-staff", description="Editar redes sociales de un creador (Staff)")
    @is_media_staff()
    async def staff_edit_socials(self, interaction: discord.Interaction,
                                  usuario: discord.Member,
                                  plataforma: str,
                                  link: str):
        if plataforma not in SOCIAL_PLATFORMS:
            await interaction.response.send_message(
                embed=error_embed("Plataforma invalida", 
                    f"Opciones: {', '.join(SOCIAL_PLATFORMS.keys())}"),
                ephemeral=True
            )
            return

        creator = await db.get_creator(usuario.id)
        if not creator:
            await interaction.response.send_message(
                embed=error_embed("El usuario no es creador"), ephemeral=True
            )
            return

        column = SOCIAL_PLATFORMS[plataforma]["column"]
        await db.execute(
            f"UPDATE creators SET {column} = ? WHERE discord_id = ?",
            (link, usuario.id)
        )

        platform_name = SOCIAL_PLATFORMS[plataforma]["name"]
        await db.log_action("RED_SOCIAL_EDITADA_STAFF", usuario.id, interaction.user.id,
                           f"{platform_name}: {link}")

        await interaction.response.send_message(
            embed=success_embed(
                "Red social actualizada",
                f"{platform_name} de {usuario.mention} actualizado: `{link}`"
            )
        )

async def setup(bot):
    await bot.add_cog(Socials(bot))
