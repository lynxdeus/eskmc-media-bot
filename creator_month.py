"""Sistema Creador del Mes."""
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from database import db
from utils.embeds import create_embed, success_embed
from utils.checks import is_media_manager

class CreatorMonth(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="creator-month", description="Designar al Creador del Mes")
    @is_media_manager()
    async def creator_month(self, interaction: discord.Interaction,
                            usuario: discord.Member,
                            recompensa: str):
        creator = await db.get_creator(usuario.id)
        if not creator:
            await interaction.response.send_message("El usuario no es creador", ephemeral=True)
            return

        now = datetime.now()
        month_name = now.strftime("%B").upper()
        year = now.year

        await db.execute("""
            INSERT INTO creator_month (month, year, winner_id, reward)
            VALUES (?, ?, ?, ?)
        """, (month_name, year, usuario.id, recompensa))

        embed = create_embed(
            f"🏆 CREADOR DEL MES — {month_name} {year}",
            f"🥇 {usuario.mention}\n\n"
            f"Gracias por tu trabajo y dedicación durante este mes.\n\n"
            f"🎁 **Recompensa:** {recompensa}\n\n"
            f"¡Sigue creando contenido para EskMC!"
        )
        embed.set_thumbnail(url=usuario.display_avatar.url)

        channel = discord.utils.get(interaction.guild.text_channels, name="#・creador-del-mes")
        if channel:
            await channel.send(embed=embed)

        await db.log_action("CREADOR_DEL_MES", usuario.id, interaction.user.id,
                           f"{month_name} {year} - {recompensa}")

        await interaction.response.send_message(
            embed=success_embed("Creador del Mes designado", f"Ganador: {usuario.mention}")
        )

async def setup(bot):
    await bot.add_cog(CreatorMonth(bot))
