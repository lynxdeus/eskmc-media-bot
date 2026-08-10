"""Perfiles de creadores."""
import discord
from discord import app_commands
from discord.ext import commands
from config import CONFIG
from database import db
from utils.embeds import create_embed, error_embed

SOCIAL_PLATFORMS = {
    "youtube_link": {"emoji": "📺", "name": "YouTube"},
    "tiktok_link": {"emoji": "📱", "name": "TikTok"},
    "twitch_link": {"emoji": "🎮", "name": "Twitch"},
    "instagram_link": {"emoji": "📸", "name": "Instagram"},
    "twitter_link": {"emoji": "🐦", "name": "Twitter/X"},
    "kick_link": {"emoji": "🟢", "name": "Kick"},
    "discord_tag": {"emoji": "💬", "name": "Discord"},
}

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="media-profile", description="Ver perfil de un creador")
    async def profile(self, interaction: discord.Interaction,
                      usuario: discord.Member = None):
        target = usuario or interaction.user
        creator = await db.get_creator(target.id)

        if not creator:
            await interaction.response.send_message(
                embed=error_embed("El usuario no es creador del Media Team"), ephemeral=True
            )
            return

        rank_emoji = CONFIG.RANKS.get(creator["rank"], {}).get("emoji", "")
        status_emoji = CONFIG.STATUSES.get(creator["status"], "")

        # Construir texto de redes sociales
        socials_text = ""
        has_socials = False
        for col, info in SOCIAL_PLATFORMS.items():
            value = creator[col]
            if value:
                socials_text += f"{info['emoji']} **{info['name']}:** {value}\n"
                has_socials = True

        if not has_socials:
            socials_text = "*No hay redes configuradas. Usa `/socials` para agregarlas.*"

        embed = create_embed(
            f"PERFIL MEDIA -- {target.display_name}",
            f"**Rango:** {rank_emoji} {creator['rank']}\n"
            f"**Plataforma principal:** {creator['platform'] or 'N/A'}\n"
            f"**Seguidores:** {creator['followers'] or 0}\n"
            f"**Puntos:** {creator['points'] or 0}\n"
            f"**Contenido:** {creator['content_count'] or 0} publicaciones\n"
            f"**Visualizaciones totales:** {creator['total_views'] or 0}\n"
            f"**Advertencias:** {creator['warnings'] or 0}\n"
            f"**Ultima actividad:** {creator.get('last_activity', 'N/A')}\n"
            f"**Ultima renovacion:** {str(creator['last_renewal'])[:10] if creator['last_renewal'] else 'N/A'}\n"
            f"**Proxima renovacion:** {str(creator['next_renewal'])[:10] if creator['next_renewal'] else 'N/A'}\n"
            f"**Estado:** {status_emoji} {creator['status']}\n"
            f"**Fecha de ingreso:** {str(creator['join_date'])[:10] if creator['join_date'] else 'N/A'}\n\n"
            f"**Redes Sociales:**\n{socials_text}"
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Profile(bot))
