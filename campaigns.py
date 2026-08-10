"""Sistema de campanas."""
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
from database import db
from utils.embeds import create_embed, success_embed, error_embed
from utils.checks import is_media_manager

class Campaigns(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="campaign-create", description="Crear una campana")
    @is_media_manager()
    async def create_campaign(self, interaction: discord.Interaction,
                                nombre: str,
                                objetivo: str,
                                duracion_dias: int,
                                requisitos: str,
                                premio: str,
                                puntos: int):
        end_date = (datetime.now() + timedelta(days=duracion_dias)).isoformat()

        campaign_id = await db.execute_and_get_id("""
            INSERT INTO campaigns (name, objective, duration_days, requirements, prize, points, end_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (nombre, objetivo, duracion_dias, requisitos, premio, puntos, end_date))

        embed = create_embed(
            f"CAMPANA: {nombre}",
            f"**Objetivo:** {objetivo}\n\n"
            f"**Duracion:** {duracion_dias} dias\n"
            f"**Finaliza:** {end_date[:10]}\n"
            f"**Requisitos:** {requisitos}\n"
            f"**Premio:** {premio}\n"
            f"**Puntos:** +{puntos}\n\n"
            f"**ID:** `{campaign_id}`\n\n"
            f"Todos los Media pueden participar!"
        )

        campaigns_ch = discord.utils.get(interaction.guild.text_channels, name="campanas")
        if campaigns_ch:
            await campaigns_ch.send(embed=embed)

        await interaction.response.send_message(
            embed=success_embed("Campana creada", f"ID: `{campaign_id}`")
        )

    @app_commands.command(name="campaign-end", description="Finalizar una campana")
    @is_media_manager()
    async def end_campaign(self, interaction: discord.Interaction,
                           campaign_id: int):
        await db.execute(
            "UPDATE campaigns SET status = 'FINALIZADA' WHERE id = ?",
            (campaign_id,)
        )
        await interaction.response.send_message(
            embed=success_embed("Campana finalizada")
        )

async def setup(bot):
    await bot.add_cog(Campaigns(bot))
