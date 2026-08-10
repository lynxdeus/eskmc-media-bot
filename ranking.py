"""Sistema de rankings."""
import discord
from discord import app_commands
from discord.ext import commands
from database import db
from utils.embeds import create_embed, error_embed

class Ranking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ranking", description="Ver ranking de creadores")
    async def ranking(self, interaction: discord.Interaction):
        top = await db.fetchall(
            "SELECT * FROM creators WHERE status != 'RETIRADO' ORDER BY points DESC LIMIT 10"
        )

        if not top:
            await interaction.response.send_message(
                embed=error_embed("No hay creadores registrados"), ephemeral=True
            )
            return

        description = ""
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        for i, creator in enumerate(top):
            member = interaction.guild.get_member(creator["discord_id"])
            name = member.display_name if member else f"Usuario {creator['discord_id']}"
            description += (
                f"{medals[i]} **{name}** — `{creator['points']}` pts | "
                f"{creator['content_count']} contenidos | {creator['total_views']} views\n"
            )

        embed = create_embed("🏆 RANKING MEDIA TEAM", description)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ranking-mensual", description="Ranking del mes actual")
    async def monthly_ranking(self, interaction: discord.Interaction):
        await self.ranking(interaction)

    @app_commands.command(name="ranking-semanal", description="Ranking de la semana")
    async def weekly_ranking(self, interaction: discord.Interaction):
        await self.ranking(interaction)

    @app_commands.command(name="ranking-usuario", description="Posición de un usuario")
    async def user_ranking(self, interaction: discord.Interaction,
                           usuario: discord.Member = None):
        target = usuario or interaction.user
        creator = await db.get_creator(target.id)
        if not creator:
            await interaction.response.send_message(
                embed=error_embed("No es creador"), ephemeral=True
            )
            return

        all_creators = await db.fetchall(
            "SELECT discord_id FROM creators WHERE status != 'RETIRADO' ORDER BY points DESC"
        )
        position = next((i+1 for i, c in enumerate(all_creators) if c["discord_id"] == target.id), None)

        embed = create_embed(
            f"📊 Posición de {target.display_name}",
            f"**Puesto:** #{position} de {len(all_creators)}\n"
            f"**Puntos:** {creator['points']}"
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Ranking(bot))
