"""Sistema de recompensas."""
import discord
from discord import app_commands
from discord.ext import commands
from database import db
from utils.embeds import success_embed, error_embed, info_embed
from utils.checks import is_media_manager, is_media_staff

class Rewards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="reward-add", description="Añadir una recompensa")
    @is_media_manager()
    async def add_reward(self, interaction: discord.Interaction,
                         nombre: str,
                         descripcion: str,
                         tipo: str,
                         valor: str,
                         requisitos: str = None):
        await db.execute("""
            INSERT INTO rewards (name, description, reward_type, value, requirements)
            VALUES (?, ?, ?, ?, ?)
        """, (nombre, descripcion, tipo, valor, requisitos or ""))

        await interaction.response.send_message(
            embed=success_embed("Recompensa añadida", f"**{nombre}** ({tipo})")
        )

    @app_commands.command(name="reward-remove", description="Eliminar una recompensa")
    @is_media_manager()
    async def remove_reward(self, interaction: discord.Interaction,
                            nombre: str):
        await db.execute("DELETE FROM rewards WHERE name = ?", (nombre,))
        await interaction.response.send_message(
            embed=success_embed("Recompensa eliminada", nombre)
        )

    @app_commands.command(name="reward-give", description="Entregar recompensa a un creador")
    @is_media_staff()
    async def give_reward(self, interaction: discord.Interaction,
                          usuario: discord.Member,
                          nombre: str):
        creator = await db.get_creator(usuario.id)
        if not creator:
            await interaction.response.send_message(
                embed=error_embed("No es creador"), ephemeral=True
            )
            return

        reward = await db.fetchone("SELECT * FROM rewards WHERE name = ?", (nombre,))
        if not reward:
            await interaction.response.send_message(
                embed=error_embed("Recompensa no encontrada"), ephemeral=True
            )
            return

        existing = await db.fetchone(
            "SELECT * FROM rewards_history WHERE discord_id = ? AND reward_id = ?",
            (usuario.id, reward["id"])
        )
        if existing:
            await interaction.response.send_message(
                embed=error_embed("El usuario ya reclamó esta recompensa"), ephemeral=True
            )
            return

        await db.execute("""
            INSERT INTO rewards_history (discord_id, reward_id, staff_id)
            VALUES (?, ?, ?)
        """, (usuario.id, reward["id"], interaction.user.id))

        await db.log_action("RECOMPENSA_ENTREGADA", usuario.id, interaction.user.id,
                           f"{nombre} ({reward['reward_type']})")

        await interaction.response.send_message(
            embed=success_embed(
                "Recompensa entregada",
                f"{usuario.mention} recibió: **{nombre}**\n"
                f"**Tipo:** {reward['reward_type']}\n"
                f"**Valor:** {reward['value']}"
            )
        )

    @app_commands.command(name="reward-list", description="Listar recompensas disponibles")
    async def list_rewards(self, interaction: discord.Interaction):
        rewards = await db.fetchall("SELECT * FROM rewards WHERE available = 1")
        if not rewards:
            await interaction.response.send_message(
                embed=info_embed("Sin recompensas", "No hay recompensas configuradas"), ephemeral=True
            )
            return

        text = "\n".join([
            f"**{r['name']}** ({r['reward_type']}) — {r['value']}"
            for r in rewards
        ])

        await interaction.response.send_message(
            embed=info_embed("🎁 Recompensas disponibles", text)
        )

    @app_commands.command(name="reward-history", description="Historial de recompensas")
    async def reward_history(self, interaction: discord.Interaction,
                             usuario: discord.Member = None):
        target = usuario or interaction.user
        history = await db.fetchall("""
            SELECT r.*, rh.claimed_at FROM rewards_history rh
            JOIN rewards r ON rh.reward_id = r.id
            WHERE rh.discord_id = ?
            ORDER BY rh.claimed_at DESC
        """, (target.id,))

        if not history:
            await interaction.response.send_message(
                embed=info_embed("Sin historial", "No ha reclamado recompensas"), ephemeral=True
            )
            return

        text = "\n".join([
            f"**{h['name']}** — {h['claimed_at'][:10]}"
            for h in history
        ])

        await interaction.response.send_message(
            embed=info_embed(f"Historial de {target.display_name}", text)
        )

async def setup(bot):
    await bot.add_cog(Rewards(bot))
