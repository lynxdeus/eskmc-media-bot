"""Leaderboard de followers para el Media Team."""
import discord
from discord import app_commands
from discord.ext import commands
from database import db
from utils.embeds import create_embed, error_embed

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="leaderboard-followers", description="Tabla de creadores ordenados por seguidores")
    async def leaderboard_followers(self, interaction: discord.Interaction):
        top = await db.fetchall(
            """SELECT * FROM creators 
            WHERE status != 'RETIRADO' 
            ORDER BY followers DESC 
            LIMIT 15"""
        )

        if not top:
            await interaction.response.send_message(
                embed=error_embed("No hay creadores registrados"), ephemeral=True
            )
            return

        description = ""
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟",
                   "1️⃣1️⃣", "1️⃣2️⃣", "1️⃣3️⃣", "1️⃣4️⃣", "1️⃣5️⃣"]

        for i, creator in enumerate(top):
            member = interaction.guild.get_member(creator["discord_id"])
            name = member.display_name if member else f"Usuario {creator['discord_id']}"
            platform = creator['platform'] or "N/A"
            followers = creator['followers'] or 0
            rank = creator['rank'] or "MEDIA"

            description += (
                f"{medals[i]} **{name}** | `{followers}` followers | "
                f"{platform} | {rank}\n"
            )

        embed = create_embed(
            "📊 LEADERBOARD POR SEGUIDORES",
            f"**Top {len(top)} creadores del Media Team ordenados por seguidores:**\n\n"
            f"{description}"
        )
        embed.set_footer(text="EskMC Media Team | Actualizado en tiempo real")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard-platform", description="Tabla de creadores por plataforma")
    async def leaderboard_platform(self, interaction: discord.Interaction,
                                    plataforma: str):
        top = await db.fetchall(
            """SELECT * FROM creators 
            WHERE status != 'RETIRADO' AND UPPER(platform) = UPPER(?)
            ORDER BY followers DESC 
            LIMIT 15""",
            (plataforma,)
        )

        if not top:
            await interaction.response.send_message(
                embed=error_embed(f"No hay creadores en {plataforma}"), ephemeral=True
            )
            return

        description = ""
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        for i, creator in enumerate(top):
            member = interaction.guild.get_member(creator["discord_id"])
            name = member.display_name if member else f"Usuario {creator['discord_id']}"
            followers = creator['followers'] or 0
            rank = creator['rank'] or "MEDIA"

            description += (
                f"{medals[i]} **{name}** | `{followers}` followers | {rank}\n"
            )

        embed = create_embed(
            f"📊 LEADERBOARD {plataforma.upper()}",
            f"**Top creadores en {plataforma.upper()}:**\n\n{description}"
        )

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Leaderboard(bot))
