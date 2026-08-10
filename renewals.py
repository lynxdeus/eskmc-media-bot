"""Sistema de renovaciones."""
import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from config import CONFIG
from database import db
from utils.embeds import create_embed, success_embed, error_embed, warning_embed
from utils.checks import is_media_staff, is_media_manager

class Renewals(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_renewals.start()

    def cog_unload(self):
        self.check_renewals.cancel()

    async def _get_role(self, guild: discord.Guild, rank: str):
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

    async def _remove_all_media_roles(self, guild: discord.Guild, member: discord.Member):
        for rank_key in CONFIG.RANKS:
            role = await self._get_role(guild, rank_key)
            if role and role in member.roles:
                await member.remove_roles(role)

    @tasks.loop(hours=24)
    async def check_renewals(self):
        now = datetime.now()

        seven_days = (now + timedelta(days=7)).isoformat()
        creators_7d = await db.fetchall(
            "SELECT * FROM creators WHERE next_renewal <= ? AND status = 'ACTIVO'",
            (seven_days,)
        )
        for creator in creators_7d:
            member = self.bot.get_user(creator["discord_id"])
            if member:
                try:
                    embed = warning_embed(
                        "RENOVACION PROXIMA",
                        "Tu renovacion del Media Team de EskMC se acerca.\n\n"
                        "Recuerda mantener tu actividad y presentar tu contenido antes de la fecha limite."
                    )
                    await member.send(embed=embed)
                except:
                    pass

        three_days = (now + timedelta(days=3)).isoformat()
        creators_3d = await db.fetchall(
            "SELECT * FROM creators WHERE next_renewal <= ? AND status = 'ACTIVO'",
            (three_days,)
        )
        for creator in creators_3d:
            member = self.bot.get_user(creator["discord_id"])
            if member:
                try:
                    embed = warning_embed(
                        "RENOVACION EN 3 DIAS",
                        "Tu renovacion vence en 3 dias! No olvides solicitarla."
                    )
                    await member.send(embed=embed)
                except:
                    pass

        today = now.isoformat()
        creators_today = await db.fetchall(
            "SELECT * FROM creators WHERE next_renewal <= ? AND status = 'ACTIVO'",
            (today,)
        )
        for creator in creators_today:
            await db.execute(
                "UPDATE creators SET status = 'EN REVISION' WHERE discord_id = ?",
                (creator["discord_id"],)
            )
            member = self.bot.get_user(creator["discord_id"])
            if member:
                try:
                    embed = error_embed(
                        "RENOVACION PENDIENTE",
                        "Tu periodo de Media ha terminado.\n\n"
                        "Solicita tu renovacion para mantener tu rango."
                    )
                    await member.send(embed=embed)
                except:
                    pass

        inactive_date = (now - timedelta(days=7)).isoformat()
        creators_inactive = await db.fetchall(
            "SELECT * FROM creators WHERE next_renewal <= ? AND status = 'EN REVISION'",
            (inactive_date,)
        )
        for creator in creators_inactive:
            await db.execute(
                "UPDATE creators SET status = 'INACTIVO' WHERE discord_id = ?",
                (creator["discord_id"],)
            )

        retired_date = (now - timedelta(days=14)).isoformat()
        creators_retired = await db.fetchall(
            "SELECT * FROM creators WHERE next_renewal <= ? AND status = 'INACTIVO'",
            (retired_date,)
        )
        for creator in creators_retired:
            await db.execute(
                "UPDATE creators SET status = 'RETIRADO' WHERE discord_id = ?",
                (creator["discord_id"],)
            )
            guild = self.bot.get_guild(CONFIG.GUILD_ID)
            if guild:
                member = guild.get_member(creator["discord_id"])
                if member:
                    await self._remove_all_media_roles(guild, member)

    @check_renewals.before_loop
    async def before_check_renewals(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="solicitar-renovacion", description="Solicitar renovacion de membresia")
    async def request_renewal(self, interaction: discord.Interaction):
        creator = await db.get_creator(interaction.user.id)
        if not creator:
            await interaction.response.send_message(
                embed=error_embed("No eres miembro del Media Team"), ephemeral=True
            )
            return

        modal = RenewalModal()
        await interaction.response.send_modal(modal)

    @app_commands.command(name="renovacion-aceptar", description="Aceptar una renovacion")
    @is_media_staff()
    async def accept_renewal(self, interaction: discord.Interaction, 
                            renewal_id: int, 
                            notas: str = None):
        renewal = await db.fetchone("SELECT * FROM renewals WHERE id = ?", (renewal_id,))
        if not renewal or renewal["status"] != "PENDIENTE":
            await interaction.response.send_message(
                embed=error_embed("Renovacion no encontrada o ya procesada"), ephemeral=True
            )
            return

        creator = await db.get_creator(renewal["discord_id"])
        rank = creator["rank"]
        days = CONFIG.RANKS[rank]["renewal_days"] if rank != "PARTNER" else 30
        new_renewal = (datetime.now() + timedelta(days=days)).isoformat() if days else None

        await db.execute("""
            UPDATE creators 
            SET last_renewal = ?, next_renewal = ?, status = 'ACTIVO'
            WHERE discord_id = ?
        """, (datetime.now().isoformat(), new_renewal, renewal["discord_id"]))

        await db.execute("""
            UPDATE renewals SET status = 'ACEPTADA', reviewed_by = ?, review_notes = ?
            WHERE id = ?
        """, (interaction.user.id, notas or "", renewal_id))

        await db.log_action("RENOVACION_ACEPTADA", renewal["discord_id"], interaction.user.id, notas)

        member = self.bot.get_user(renewal["discord_id"])
        if member:
            try:
                await member.send(embed=success_embed(
                    "Renovacion Aceptada",
                    f"Tu renovacion ha sido aceptada. Proxima renovacion: {new_renewal[:10] if new_renewal else 'N/A'}"
                ))
            except:
                pass

        await interaction.response.send_message(embed=success_embed("Renovacion aceptada"))

    @app_commands.command(name="renovacion-rechazar", description="Rechazar una renovacion")
    @is_media_staff()
    async def reject_renewal(self, interaction: discord.Interaction, 
                             renewal_id: int,
                             razon: str):
        await db.execute("""
            UPDATE renewals SET status = 'RECHAZADA', reviewed_by = ?, review_notes = ?
            WHERE id = ?
        """, (interaction.user.id, razon, renewal_id))

        renewal = await db.fetchone("SELECT discord_id FROM renewals WHERE id = ?", (renewal_id,))
        if renewal:
            await db.log_action("RENOVACION_RECHAZADA", renewal["discord_id"], interaction.user.id, razon)

        await interaction.response.send_message(embed=error_embed("Renovacion rechazada", razon))

class RenewalModal(discord.ui.Modal, title="Solicitud de Renovacion"):
    minecraft_ign = discord.ui.TextInput(label="Nick de Minecraft", required=True)
    platform = discord.ui.TextInput(label="Plataforma", required=True)
    current_followers = discord.ui.TextInput(label="Seguidores actuales", required=True)
    content_posted = discord.ui.TextInput(label="Contenido publicado (descripcion)", required=True, style=discord.TextStyle.paragraph)
    video_count = discord.ui.TextInput(label="Numero de videos", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        existing = await db.fetchone(
            "SELECT * FROM renewals WHERE discord_id = ? AND status = 'PENDIENTE'",
            (interaction.user.id,)
        )
        if existing:
            await interaction.response.send_message(
                embed=error_embed("Ya tienes una renovacion pendiente"), ephemeral=True
            )
            return

        renewal_id = await db.execute_and_get_id("""
            INSERT INTO renewals 
            (discord_id, minecraft_ign, platform, current_followers, content_posted, video_count, status)
            VALUES (?, ?, ?, ?, ?, ?, 'PENDIENTE')
        """, (interaction.user.id, self.minecraft_ign.value, self.platform.value,
              self.current_followers.value, self.content_posted.value, self.video_count.value))

        guild = interaction.guild
        staff_role = guild.get_role(CONFIG.MEDIA_STAFF_ROLE_ID)

        embed = create_embed(
            "Nueva Renovacion Pendiente",
            f"**De:** {interaction.user.mention}\n"
            f"**MC:** {self.minecraft_ign.value}\n"
            f"**ID:** `{renewal_id}`\n\n"
            f"Usa `/renovacion-aceptar {renewal_id}` o `/renovacion-rechazar {renewal_id}`"
        )

        pending_ch = discord.utils.get(guild.text_channels, name="renovaciones-pendientes")
        if pending_ch:
            await pending_ch.send(
                f"{staff_role.mention if staff_role else ''}", embed=embed
            )

        await db.log_action("NUEVA_RENOVACION", interaction.user.id, interaction.user.id,
                           f"ID: {renewal_id}")

        await interaction.response.send_message(
            embed=success_embed("Renovacion solicitada", "El equipo revisara tu solicitud pronto."),
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Renewals(bot))
