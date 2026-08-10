"""Sistema antifraud y advertencias."""
import discord
from discord import app_commands
from discord.ext import commands
from database import db
from utils.embeds import success_embed, error_embed, warning_embed, info_embed
from utils.checks import is_media_staff, is_media_manager

class Antifraud(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="media-warn", description="Advertir a un usuario")
    @is_media_staff()
    async def warn(self, interaction: discord.Interaction,
                   usuario: discord.Member,
                   razon: str):
        # Registrar advertencia en la tabla warnings (funciona para cualquier usuario)
        await db.execute("""
            INSERT INTO warnings (discord_id, reason, staff_id)
            VALUES (?, ?, ?)
        """, (usuario.id, razon, interaction.user.id))

        # Contar advertencias totales
        warns = await db.fetchall(
            "SELECT * FROM warnings WHERE discord_id = ?",
            (usuario.id,)
        )
        total_warnings = len(warns) if warns else 0

        # Si es creador, actualizar contador en creators
        creator = await db.get_creator(usuario.id)
        if creator:
            await db.execute(
                "UPDATE creators SET warnings = ? WHERE discord_id = ?",
                (total_warnings, usuario.id)
            )

        await db.log_action("ADVERTENCIA", usuario.id, interaction.user.id, razon)

        # Notificar al usuario
        try:
            await usuario.send(embed=warning_embed(
                "Has recibido una advertencia",
                f"**Razon:** {razon}\n"
                f"**Advertencias totales:** {total_warnings}\n\n"
                f"Acumular demasiadas advertencias puede resultar en sanciones."
            ))
        except:
            pass

        creator_text = " (creador del Media Team)" if creator else ""
        await interaction.response.send_message(
            embed=warning_embed(
                "Advertencia registrada",
                f"{usuario.mention}{creator_text} ha sido advertido.\n"
                f"**Razon:** {razon}\n"
                f"**Total de advertencias:** {total_warnings}"
            )
        )

    @app_commands.command(name="media-warnings", description="Ver advertencias de un usuario")
    @is_media_staff()
    async def warnings(self, interaction: discord.Interaction,
                       usuario: discord.Member):
        warns = await db.fetchall(
            "SELECT * FROM warnings WHERE discord_id = ? ORDER BY created_at DESC",
            (usuario.id,)
        )

        if not warns:
            await interaction.response.send_message(
                embed=info_embed("Sin advertencias", f"{usuario.mention} no tiene advertencias."),
                ephemeral=True
            )
            return

        text = "\n".join([
            f"**#{w['id']}** -- {w['reason'][:40]} (`{w['created_at'][:10]}`)"
            for w in warns
        ])

        await interaction.response.send_message(
            embed=info_embed(f"Advertencias de {usuario.display_name} ({len(warns)} total)", text)
        )

    @app_commands.command(name="media-unwarn", description="Eliminar una advertencia")
    @is_media_manager()
    async def unwarn(self, interaction: discord.Interaction,
                     warning_id: int):
        warn = await db.fetchone("SELECT * FROM warnings WHERE id = ?", (warning_id,))
        if not warn:
            await interaction.response.send_message(
                embed=error_embed("Advertencia no encontrada"), ephemeral=True
            )
            return

        await db.execute("DELETE FROM warnings WHERE id = ?", (warning_id,))

        # Actualizar contador si es creador
        creator = await db.get_creator(warn["discord_id"])
        if creator:
            remaining = await db.fetchall(
                "SELECT * FROM warnings WHERE discord_id = ?",
                (warn["discord_id"],)
            )
            await db.execute(
                "UPDATE creators SET warnings = ? WHERE discord_id = ?",
                (len(remaining) if remaining else 0, warn["discord_id"])
            )

        await db.log_action("ADVERTENCIA_REMOVIDA", warn["discord_id"], interaction.user.id,
                           f"ID: {warning_id}")

        await interaction.response.send_message(
            embed=success_embed("Advertencia eliminada", f"ID: `{warning_id}`")
        )

async def setup(bot):
    await bot.add_cog(Antifraud(bot))
