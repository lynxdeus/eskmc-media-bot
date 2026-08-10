"""Comandos de configuración administrativa."""
import discord
from discord import app_commands
from discord.ext import commands
from database import db
from utils.embeds import success_embed, error_embed, info_embed
from utils.checks import is_media_manager

class ConfigCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="media-config", description="Ver configuración actual")
    @is_media_manager()
    async def view_config(self, interaction: discord.Interaction):
        config = await db.fetchone("SELECT * FROM server_config WHERE guild_id = ?", 
                                     (interaction.guild_id,))

        embed = info_embed(
            "⚙️ Configuración del Media Team",
            f"**Guild:** `{interaction.guild_id}`\n"
            f"**Log Channel:** <#{config['log_channel_id'] if config else 'No configurado'}>\n"
            f"**Manager Role:** <@&{config['manager_role_id'] if config else 'N/A'}>\n"
            f"**Staff Role:** <@&{config['staff_role_id'] if config else 'N/A'}>\n"
            f"**Setup completado:** {'✅' if config and config['setup_completed'] else '❌'}"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="media-config-channels", description="Configurar canales")
    @is_media_manager()
    async def config_channels(self, interaction: discord.Interaction,
                              log_channel: discord.TextChannel):
        await db.execute("""
            INSERT OR REPLACE INTO server_config (guild_id, log_channel_id)
            VALUES (?, ?)
        """, (interaction.guild_id, log_channel.id))

        await interaction.response.send_message(
            embed=success_embed("Canales configurados", f"Log: {log_channel.mention}")
        )

    @app_commands.command(name="media-config-roles", description="Configurar roles")
    @is_media_manager()
    async def config_roles(self, interaction: discord.Interaction,
                           manager_role: discord.Role,
                           staff_role: discord.Role):
        await db.execute("""
            UPDATE server_config 
            SET manager_role_id = ?, staff_role_id = ?
            WHERE guild_id = ?
        """, (manager_role.id, staff_role.id, interaction.guild_id))

        await interaction.response.send_message(
            embed=success_embed(
                "Roles configurados",
                f"Manager: {manager_role.mention}\nStaff: {staff_role.mention}"
            )
        )

    @app_commands.command(name="media-config-renewal", description="Configurar tiempos de renovación")
    @is_media_manager()
    async def config_renewal(self, interaction: discord.Interaction,
                             rango: str,
                             dias: int):
        from config import CONFIG
        if rango not in CONFIG.RANKS:
            await interaction.response.send_message(
                embed=error_embed("Rango inválido"), ephemeral=True
            )
            return

        await db.execute("""
            INSERT OR REPLACE INTO server_config (guild_id, renewal_override)
            VALUES (?, ?)
        """, (interaction.guild_id, f"{rango}:{dias}"))

        await interaction.response.send_message(
            embed=success_embed("Renovación configurada", f"{rango}: cada {dias} días")
        )

    @app_commands.command(name="media-config-notifications", description="Activar/desactivar notificaciones")
    @is_media_manager()
    async def config_notifications(self, interaction: discord.Interaction,
                                   activar: bool):
        status = "ACTIVADAS" if activar else "DESACTIVADAS"
        await interaction.response.send_message(
            embed=success_embed(f"Notificaciones {status}")
        )

async def setup(bot):
    await bot.add_cog(ConfigCommands(bot))
