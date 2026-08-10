"""Automatizaciones adicionales y utilidades."""
import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime
from database import db
from utils.embeds import success_embed, info_embed
from utils.checks import is_media_manager

class Automation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_stats.start()

    def cog_unload(self):
        self.daily_stats.cancel()

    @tasks.loop(hours=24)
    async def daily_stats(self):
        await self.bot.wait_until_ready()

        total = await db.fetchone("SELECT COUNT(*) as count FROM creators")
        active = await db.fetchone("SELECT COUNT(*) as count FROM creators WHERE status = 'ACTIVO'")
        pending_apps = await db.fetchone("SELECT COUNT(*) as count FROM applications WHERE status = 'PENDIENTE'")
        pending_rens = await db.fetchone("SELECT COUNT(*) as count FROM renewals WHERE status = 'PENDIENTE'")

        for guild in self.bot.guilds:
            stats_ch = discord.utils.get(guild.text_channels, name="#・estadisticas-media")
            if stats_ch:
                embed = info_embed(
                    "📊 Estadísticas Diarias del Media Team",
                    f"**Creadores totales:** {total['count']}\n"
                    f"**Activos:** {active['count']}\n"
                    f"**Solicitudes pendientes:** {pending_apps['count']}\n"
                    f"**Renovaciones pendientes:** {pending_rens['count']}\n"
                    f"**Fecha:** {datetime.now().strftime('%Y-%m-%d')}"
                )
                try:
                    await stats_ch.send(embed=embed)
                except:
                    pass

    @daily_stats.before_loop
    async def before_daily_stats(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="media-stats", description="Ver estadísticas generales")
    @is_media_manager()
    async def stats(self, interaction: discord.Interaction):
        total = await db.fetchone("SELECT COUNT(*) as count FROM creators")
        active = await db.fetchone("SELECT COUNT(*) as count FROM creators WHERE status = 'ACTIVO'")
        review = await db.fetchone("SELECT COUNT(*) as count FROM creators WHERE status = 'EN REVISIÓN'")
        inactive = await db.fetchone("SELECT COUNT(*) as count FROM creators WHERE status = 'INACTIVO'")
        retired = await db.fetchone("SELECT COUNT(*) as count FROM creators WHERE status = 'RETIRADO'")

        top_points = await db.fetchall(
            "SELECT discord_id, points FROM creators ORDER BY points DESC LIMIT 3"
        )

        top_text = "\n".join([
            f"{'🥇🥈🥉'[i]} <@{p['discord_id']}>: `{p['points']}` pts"
            for i, p in enumerate(top_points)
        ])

        embed = info_embed(
            "📊 Estadísticas del Media Team",
            f"**Creadores totales:** {total['count']}\n"
            f"🟢 Activos: {active['count']}\n"
            f"🟡 En revisión: {review['count']}\n"
            f"🟠 Inactivos: {inactive['count']}\n"
            f"🔴 Retirados: {retired['count']}\n\n"
            f"**Top Puntos:**\n{top_text}"
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="media-backup", description="Generar backup de la base de datos")
    @is_media_manager()
    async def backup(self, interaction: discord.Interaction):
        import shutil
        from config import CONFIG
        import os

        backup_path = f"data/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        os.makedirs("data", exist_ok=True)
        shutil.copy2(CONFIG.DATABASE_PATH, backup_path)

        await interaction.response.send_message(
            embed=success_embed("Backup creado", f"Archivo: `{backup_path}`"),
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Automation(bot))
