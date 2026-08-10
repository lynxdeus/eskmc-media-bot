"""Sistema de logs centralizado."""
import discord
from discord import app_commands
from discord.ext import commands
from database import db
from utils.embeds import create_embed, error_embed
from utils.checks import is_media_manager

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_log(self, guild: discord.Guild, action: str, target_id: int, 
                       staff_id: int, details: str = ""):
        config = await db.fetchone("SELECT log_channel_id FROM server_config WHERE guild_id = ?", 
                                   (guild.id,))
        if not config or not config["log_channel_id"]:
            return

        channel = guild.get_channel(config["log_channel_id"])
        if not channel:
            return

        staff = guild.get_member(staff_id)
        target = guild.get_member(target_id)

        embed = create_embed(
            "📝 REGISTRO DE ACCIÓN",
            f"**Acción:** `{action}`\n"
            f"**Usuario afectado:** {target.mention if target else target_id}\n"
            f"**Staff:** {staff.mention if staff else staff_id}\n"
            f"**Fecha:** <t:{int(discord.utils.utcnow().timestamp())}:F>\n"
            f"**Detalles:** {details or 'Ninguno'}"
        )
        embed.color = discord.Color.dark_gray()

        try:
            await channel.send(embed=embed)
        except:
            pass

    @app_commands.command(name="media-logs", description="Ver logs recientes")
    @is_media_manager()
    async def view_logs(self, interaction: discord.Interaction,
                        limite: int = 20):
        if limite > 100:
            limite = 100

        logs = await db.fetchall(
            "SELECT * FROM activity_log ORDER BY created_at DESC LIMIT ?",
            (limite,)
        )

        if not logs:
            await interaction.response.send_message(
                embed=error_embed("No hay logs"), ephemeral=True
            )
            return

        text = "\n".join([
            f"`{l['created_at'][:16]}` | **{l['action']}** | <@{l['target_id']}> | {l['details'][:30]}"
            for l in logs
        ])

        if len(text) > 4000:
            text = text[:4000] + "\n..."

        embed = create_embed(f"📜 Últimos {limite} registros", text)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="media-log-user", description="Ver logs de un usuario específico")
    @is_media_manager()
    async def user_logs(self, interaction: discord.Interaction,
                        usuario: discord.Member,
                        limite: int = 10):
        logs = await db.fetchall(
            "SELECT * FROM activity_log WHERE target_id = ? ORDER BY created_at DESC LIMIT ?",
            (usuario.id, limite)
        )

        if not logs:
            await interaction.response.send_message(
                embed=error_embed("Sin registros"), ephemeral=True
            )
            return

        text = "\n".join([
            f"`{l['created_at'][:16]}` | **{l['action']}** | {l['details'][:40]}"
            for l in logs
        ])

        embed = create_embed(f"📜 Historial de {usuario.display_name}", text)
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Logs(bot))
