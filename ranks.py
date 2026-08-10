"""Sistema de rangos y ascensos."""
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
from config import CONFIG
from database import db
from utils.embeds import success_embed, error_embed, info_embed
from utils.checks import is_media_manager

class Ranks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _get_role(self, guild: discord.Guild, rank: str):
        """Obtiene el rol de un rango, primero por ID en DB, luego por nombre."""
        config = await db.fetchone("SELECT * FROM server_config WHERE guild_id = ?", (guild.id,))

        role_id = 0
        if config:
            if rank == "MEDIA":
                role_id = config["role_media"] or 0
            elif rank == "MEDIA+":
                role_id = config["role_media_plus"] or 0
            elif rank == "FAMOSO":
                role_id = config["role_famoso"] or 0
            elif rank == "PARTNER":
                role_id = config["role_partner"] or 0
            elif rank == "O-MEDIA":
                role_id = config["role_o_media"] or 0

        if role_id:
            role = guild.get_role(role_id)
            if role:
                return role

        role_name = CONFIG.RANKS[rank]["role_name"]
        return discord.utils.get(guild.roles, name=role_name)

    async def _update_rank(self, guild: discord.Guild, member: discord.Member, new_rank: str):
        """Quita roles antiguos y asigna el nuevo."""
        for rank_key in CONFIG.RANKS:
            role = await self._get_role(guild, rank_key)
            if role and role in member.roles:
                await member.remove_roles(role)

        new_role = await self._get_role(guild, new_rank)
        if new_role:
            await member.add_roles(new_role)
        return new_role

    @app_commands.command(name="media-promote", description="Ascender a un creador")
    @is_media_manager()
    async def promote(self, interaction: discord.Interaction,
                      usuario: discord.Member,
                      rango: str,
                      motivo: str):
        if rango not in CONFIG.RANKS:
            await interaction.response.send_message(
                embed=error_embed("Rango invalido", f"Opciones: {', '.join(CONFIG.RANKS.keys())}"),
                ephemeral=True
            )
            return

        creator = await db.get_creator(usuario.id)
        if not creator:
            await interaction.response.send_message(
                embed=error_embed("El usuario no es creador"), ephemeral=True
            )
            return

        old_rank = creator["rank"]
        if old_rank == rango:
            await interaction.response.send_message(
                embed=error_embed("Ya tiene ese rango"), ephemeral=True
            )
            return

        req_check = await self._check_requirements(creator, rango)
        if not req_check["pass"]:
            await interaction.response.send_message(
                embed=error_embed("No cumple requisitos", req_check["message"]),
                ephemeral=True
            )
            return

        await db.execute(
            "UPDATE creators SET rank = ? WHERE discord_id = ?",
            (rango, usuario.id)
        )

        await db.execute("""
            INSERT INTO rank_history (discord_id, old_rank, new_rank, changed_by, reason)
            VALUES (?, ?, ?, ?, ?)
        """, (usuario.id, old_rank, rango, interaction.user.id, motivo))

        new_role = await self._update_rank(interaction.guild, usuario, rango)

        days = CONFIG.RANKS[rango]["renewal_days"] if rango != "PARTNER" else 30
        new_renewal = (datetime.now() + timedelta(days=days)).isoformat() if days else None

        await db.execute(
            "UPDATE creators SET next_renewal = ? WHERE discord_id = ?",
            (new_renewal, usuario.id)
        )

        await db.log_action("ASCENSO", usuario.id, interaction.user.id,
                           f"{old_rank} -> {rango}")

        embed = success_embed(
            "Ascenso realizado",
            f"{usuario.mention} ha sido ascendido a **{CONFIG.RANKS[rango]['emoji']} {rango}**\n\n"
            f"**Rango anterior:** {old_rank}\n"
            f"**Motivo:** {motivo}\n"
            f"**Nueva renovacion:** {new_renewal[:10] if new_renewal else 'N/A'}"
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="media-demote", description="Descender a un creador")
    @is_media_manager()
    async def demote(self, interaction: discord.Interaction,
                     usuario: discord.Member,
                     rango: str,
                     motivo: str):
        if rango not in CONFIG.RANKS:
            await interaction.response.send_message(
                embed=error_embed("Rango invalido"), ephemeral=True
            )
            return

        creator = await db.get_creator(usuario.id)
        if not creator:
            await interaction.response.send_message(
                embed=error_embed("El usuario no es creador"), ephemeral=True
            )
            return

        old_rank = creator["rank"]
        await db.execute(
            "UPDATE creators SET rank = ? WHERE discord_id = ?",
            (rango, usuario.id)
        )

        await db.execute("""
            INSERT INTO rank_history (discord_id, old_rank, new_rank, changed_by, reason)
            VALUES (?, ?, ?, ?, ?)
        """, (usuario.id, old_rank, rango, interaction.user.id, motivo))

        await self._update_rank(interaction.guild, usuario, rango)

        days = CONFIG.RANKS[rango]["renewal_days"] if rango != "PARTNER" else 30
        new_renewal = (datetime.now() + timedelta(days=days)).isoformat() if days else None
        await db.execute(
            "UPDATE creators SET next_renewal = ? WHERE discord_id = ?",
            (new_renewal, usuario.id)
        )

        await db.log_action("DESCENSO", usuario.id, interaction.user.id,
                           f"{old_rank} -> {rango}")

        await interaction.response.send_message(
            embed=info_embed(
                "Descenso realizado",
                f"{usuario.mention} ha sido descendido a **{rango}**\n**Motivo:** {motivo}"
            )
        )

    @app_commands.command(name="media-setrank", description="Establecer rango directamente")
    @is_media_manager()
    async def set_rank(self, interaction: discord.Interaction,
                       usuario: discord.Member,
                       rango: str):
        if rango not in CONFIG.RANKS:
            await interaction.response.send_message(
                embed=error_embed("Rango invalido"), ephemeral=True
            )
            return

        creator = await db.get_creator(usuario.id)
        old_rank = creator["rank"] if creator else "Ninguno"

        if not creator:
            await db.add_creator(usuario.id, "Desconocido", rango, "Desconocida", 0)
        else:
            await db.execute(
                "UPDATE creators SET rank = ? WHERE discord_id = ?",
                (rango, usuario.id)
            )

        await self._update_rank(interaction.guild, usuario, rango)

        await db.execute("""
            INSERT INTO rank_history (discord_id, old_rank, new_rank, changed_by, reason)
            VALUES (?, ?, ?, ?, ?)
        """, (usuario.id, old_rank, rango, interaction.user.id, "SET directo"))

        await interaction.response.send_message(
            embed=success_embed("Rango establecido", f"{usuario.mention} -> {rango}")
        )

    async def _check_requirements(self, creator, target_rank: str):
        platform = creator["platform"].upper() if creator["platform"] else ""
        followers = creator["followers"] or 0

        reqs = {
            "MEDIA": {"YOUTUBE": 50, "TIKTOK": 75, "TWITCH": 50},
            "MEDIA+": {"YOUTUBE": 150, "TIKTOK": 200, "TWITCH": 100},
            "FAMOSO": {"YOUTUBE": 300, "TIKTOK": 500, "TWITCH": 500},
        }

        if target_rank == "PARTNER":
            return {"pass": True, "message": "Partner es por invitacion"}

        if target_rank not in reqs:
            return {"pass": True, "message": ""}

        min_followers = reqs[target_rank].get(platform, 0)
        if followers < min_followers:
            return {
                "pass": False,
                "message": f"Necesita {min_followers} seguidores en {platform}. Tiene: {followers}"
            }

        return {"pass": True, "message": ""}

async def setup(bot):
    await bot.add_cog(Ranks(bot))
