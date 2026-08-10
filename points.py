"""Sistema de puntos."""
import discord
from discord import app_commands
from discord.ext import commands
from config import CONFIG
from database import db
from utils.embeds import success_embed, error_embed, info_embed
from utils.checks import is_media_staff, is_media_manager

class Points(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="points-add", description="Anadir puntos a un creador")
    @is_media_staff()
    async def add_points(self, interaction: discord.Interaction, 
                         usuario: discord.Member,
                         cantidad: int,
                         razon: str):
        creator = await db.get_creator(usuario.id)
        if not creator:
            await interaction.response.send_message(
                embed=error_embed(
                    "El usuario no es creador",
                    f"{usuario.mention} no esta registrado en el Media Team.\n"
                    f"Usa `/media-setrank {usuario.mention} MEDIA` para registrarlo primero."
                ), ephemeral=True
            )
            return

        new_total = creator["points"] + cantidad
        await db.execute(
            "UPDATE creators SET points = ? WHERE discord_id = ?",
            (new_total, usuario.id)
        )
        await db.execute("""
            INSERT INTO points_log (discord_id, points_change, reason, new_total, staff_id)
            VALUES (?, ?, ?, ?, ?)
        """, (usuario.id, cantidad, razon, new_total, interaction.user.id))

        await db.log_action("PUNTOS_ANADIDOS", usuario.id, interaction.user.id,
                           f"+{cantidad} - {razon}")

        await interaction.response.send_message(
            embed=success_embed(
                "Puntos anadidos",
                f"{usuario.mention} ha recibido **+{cantidad}** puntos.\n"
                f"**Razon:** {razon}\n"
                f"**Total:** {new_total}"
            )
        )

    @app_commands.command(name="points-remove", description="Quitar puntos a un creador")
    @is_media_staff()
    async def remove_points(self, interaction: discord.Interaction,
                              usuario: discord.Member,
                              cantidad: int,
                              razon: str):
        creator = await db.get_creator(usuario.id)
        if not creator:
            await interaction.response.send_message(
                embed=error_embed(
                    "El usuario no es creador",
                    f"{usuario.mention} no esta registrado en el Media Team."
                ), ephemeral=True
            )
            return

        new_total = max(0, creator["points"] - cantidad)
        await db.execute(
            "UPDATE creators SET points = ? WHERE discord_id = ?",
            (new_total, usuario.id)
        )
        await db.execute("""
            INSERT INTO points_log (discord_id, points_change, reason, new_total, staff_id)
            VALUES (?, ?, ?, ?, ?)
        """, (usuario.id, -cantidad, razon, new_total, interaction.user.id))

        await db.log_action("PUNTOS_QUITADOS", usuario.id, interaction.user.id,
                           f"-{cantidad} - {razon}")

        await interaction.response.send_message(
            embed=success_embed(
                "Puntos removidos",
                f"Se quitaron **{cantidad}** puntos a {usuario.mention}.\n"
                f"**Razon:** {razon}\n"
                f"**Total:** {new_total}"
            )
        )

    @app_commands.command(name="points-set", description="Establecer puntos exactos")
    @is_media_manager()
    async def set_points(self, interaction: discord.Interaction,
                         usuario: discord.Member,
                         cantidad: int):
        creator = await db.get_creator(usuario.id)
        if not creator:
            await interaction.response.send_message(
                embed=error_embed(
                    "El usuario no es creador",
                    f"{usuario.mention} no esta registrado en el Media Team."
                ), ephemeral=True
            )
            return

        await db.execute(
            "UPDATE creators SET points = ? WHERE discord_id = ?",
            (cantidad, usuario.id)
        )
        await db.execute("""
            INSERT INTO points_log (discord_id, points_change, reason, new_total, staff_id)
            VALUES (?, ?, ?, ?, ?)
        """, (usuario.id, cantidad - creator["points"], "SET", cantidad, interaction.user.id))

        await interaction.response.send_message(
            embed=success_embed("Puntos establecidos", f"{usuario.mention} ahora tiene **{cantidad}** puntos.")
        )

    @app_commands.command(name="points-view", description="Ver puntos de un creador")
    async def view_points(self, interaction: discord.Interaction,
                          usuario: discord.Member = None):
        target = usuario or interaction.user
        creator = await db.get_creator(target.id)
        if not creator:
            await interaction.response.send_message(
                embed=error_embed(
                    "No es creador",
                    f"{target.mention} no esta registrado en el Media Team."
                ), ephemeral=True
            )
            return

        history = await db.fetchall(
            "SELECT * FROM points_log WHERE discord_id = ? ORDER BY created_at DESC LIMIT 5",
            (target.id,)
        )

        history_text = "\n".join([
            f"{'+' if h['points_change'] > 0 else ''}{h['points_change']} - {h['reason'][:30]}"
            for h in history
        ]) if history else "Sin historial reciente"

        embed = info_embed(
            f"Puntos de {target.display_name}",
            f"**Total:** `{creator['points']}` puntos\n\n"
            f"**Historial reciente:**\n```{history_text}```"
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="points-config", description="Configurar puntos por accion")
    @is_media_manager()
    async def config_points(self, interaction: discord.Interaction,
                            accion: str,
                            puntos: int):
        valid_actions = list(CONFIG.DEFAULT_POINTS.keys())
        if accion not in valid_actions:
            await interaction.response.send_message(
                embed=error_embed("Accion invalida", f"Opciones: {', '.join(valid_actions)}"),
                ephemeral=True
            )
            return

        await db.execute("""
            INSERT OR REPLACE INTO points_config (action_name, points)
            VALUES (?, ?)
        """, (accion, puntos))

        await interaction.response.send_message(
            embed=success_embed("Configuracion actualizada", f"`{accion}` = {puntos} puntos")
        )

async def setup(bot):
    await bot.add_cog(Points(bot))
