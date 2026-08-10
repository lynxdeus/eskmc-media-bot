"""Configuracion centralizada del bot."""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Config:
    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
    GUILD_ID: int = int(os.getenv("GUILD_ID", "0"))
    MEDIA_MANAGER_ROLE_ID: int = int(os.getenv("MEDIA_MANAGER_ROLE_ID", "0"))
    MEDIA_STAFF_ROLE_ID: int = int(os.getenv("MEDIA_STAFF_ROLE_ID", "0"))
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/eskmc_media.db")
    EMBED_COLOR: int = int(os.getenv("EMBED_COLOR", "0x5865F2"), 16)
    LOG_CHANNEL_ID: int = int(os.getenv("LOG_CHANNEL_ID", "0"))
    BOT_PREFIX: str = os.getenv("BOT_PREFIX", "/")

    RANKS = {
        "MEDIA": {"emoji": "Media", "renewal_days": 30, "role_name": "MEDIA"},
        "MEDIA+": {"emoji": "Media+", "renewal_days": 45, "role_name": "MEDIA+"},
        "FAMOSO": {"emoji": "Famoso", "renewal_days": 60, "role_name": "FAMOSO"},
        "PARTNER": {"emoji": "Partner", "renewal_days": None, "role_name": "PARTNER"},
        "O-MEDIA": {"emoji": "O-Media", "renewal_days": 30, "role_name": "O-MEDIA"},
    }

    DEFAULT_POINTS = {
        "tiktok_eskmc": 5,
        "youtube_video": 10,
        "stream": 10,
        "views_500": 5,
        "views_1000": 10,
        "views_5000": 20,
        "campaign": 10,
        "event": 10,
        "collab": 5,
        "exceptional": 20,
    }

    STATUSES = {
        "ACTIVO": "Activo",
        "EN REVISION": "En Revision",
        "INACTIVO": "Inactivo",
        "RETIRADO": "Retirado",
    }

CONFIG = Config()
