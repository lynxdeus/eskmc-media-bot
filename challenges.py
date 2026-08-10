"""Sistema de desafios."""
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
from database import db
from utils.embeds import create_embed, success_embed, error_embed
from utils.checks import is_media_manager

class Challenges(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="challenge-create", description="Crear un desafio")
    @is_media_manager()
    async def create_challenge(self, interaction: discord.Interaction,
                                 nombre: str,
                                 descripcion: str,
                                 duracion_dias: int,
                                 premio: str,
                                 puntos: int,
                                 requisitos: str = None):
        end_date = (datetime.now() + timedelta(days=duracion_dias)).isoformat()

        challenge_id = await db.execute_and_get_id("""
            INSERT INTO challenges (name, description, start_date, end_date, prize, requirements, points)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (nombre, descripcion, datetime.now().isoformat(), end_date, premio, requisitos or "", puntos))

        embed = create_embed(
            f"NUEVO DESAFIO: {nombre}",
            f"**{descripcion}**\n\n"
            f"**Duracion:** {duracion_dias} dias\n"
            f"**Finaliza:** {end_date[:10]}\n"
            f"**Premio:** {premio}\n"
            f"**Puntos:** +{puntos}\n"
            f"**Requisitos:** {requisitos or 'Ninguno'}\n\n"
            f"**ID:** `{challenge_id}`\n\n"
            f"Participa y demuestra tu talento!"
        )

        challenges_ch = discord.utils.get(interaction.guild.text_channels, name="media-challenges")
        if challenges_ch:
            await challenges_ch.send(embed=embed)

        await interaction.response.send_message(
            embed=success_embed("Desafio creado", f"ID: `{challenge_id}`")
        )

    @app_commands.command(name="challenge-winner", description="Designar ganador de un desafio")
    @is_media_manager()
    async def challenge_winner(self, interaction: discord.Interaction,
                               challenge_id: int,
                               usuario: discord.Member):
        challenge = await db.fetchone("SELECT * FROM challenges WHERE id = ?", (challenge_id,))
        if not challenge:
            await interaction.response.send_message(
                embed=error_embed("Desafio no encontrado"), ephemeral=True
            )
            return

        await db.execute(
            "UPDATE challenges SET status = 'FINALIZADO', winner_id = ? WHERE id = ?",
            (usuario.id, challenge_id)
        )

        creator = await db.get_creator(usuario.id)
        if creator:
            new_points = creator["points"] + challenge["points"]
            await db.execute(
                "UPDATE creators SET points = ? WHERE discord_id = ?",
                (new_points, usuario.id)
            )

        embed = create_embed(
            f"GANADOR DEL DESAFIO: {challenge['name']}!",
            f"**{usuario.mention}**\n\n"
            f"**Premio:** {challenge['prize']}\n"
            f"**Puntos ganados:** +{challenge['points']}\n\n"
            f"Felicitaciones por tu gran trabajo!"
        )

        challenges_ch = discord.utils.get(interaction.guild.text_channels, name="media-challenges")
        if challenges_ch:
            await challenges_ch.send(embed=embed)

        await db.log_action("DESAFIO_GANADO", usuario.id, interaction.user.id,
                           f"Desafio #{challenge_id}: {challenge['name']}")

        await interaction.response.send_message(
            embed=success_embed("Ganador designado", f"{usuario.mention} gano **{challenge['name']}**")
        )

async def setup(bot):
    await bot.add_cog(Challenges(bot))
