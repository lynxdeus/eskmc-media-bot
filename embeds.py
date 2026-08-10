"""Utilidades para crear embeds profesionales."""
import discord
from config import CONFIG

def create_embed(title: str, description: str = "", color: int = None) -> discord.Embed:
    embed = discord.Embed(
        title=f"**{title}**",
        description=description,
        color=color or CONFIG.EMBED_COLOR,
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text="EskMC Media Team", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
    return embed

def success_embed(title: str, description: str = "") -> discord.Embed:
    return create_embed(f"✅ {title}", description, discord.Color.green())

def error_embed(title: str, description: str = "") -> discord.Embed:
    return create_embed(f"❌ {title}", description, discord.Color.red())

def warning_embed(title: str, description: str = "") -> discord.Embed:
    return create_embed(f"⚠️ {title}", description, discord.Color.yellow())

def info_embed(title: str, description: str = "") -> discord.Embed:
    return create_embed(f"ℹ️ {title}", description, discord.Color.blue())
