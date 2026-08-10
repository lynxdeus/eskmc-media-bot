"""Funciones auxiliares."""
from datetime import datetime

def format_date(date_str: str) -> str:
    if not date_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%d/%m/%Y")
    except:
        return str(date_str)[:10]

def parse_platform(platform: str) -> str:
    platform = platform.lower().strip()
    if "youtube" in platform or "yt" in platform:
        return "YOUTUBE"
    elif "tiktok" in platform or "tt" in platform:
        return "TIKTOK"
    elif "twitch" in platform or "tw" in platform:
        return "TWITCH"
    return platform.upper()
