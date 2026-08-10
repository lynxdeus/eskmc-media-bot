"""Sistema de solicitudes para unirse al Media Team."""
import discord
from discord import app_commands
from discord.ext import commands
from config import CONFIG
from database import db
from utils.embeds import create_embed, success_embed, error_embed, info_embed
from utils.checks import is_media_staff, is_media_manager

class FullApplicationModal(discord.ui.Modal, title="Solicitud Media Team"):
    minecraft_ign = discord.ui.TextInput(label="Nick de Minecraft", required=True)
    platform = discord.ui.TextInput(label="Plataforma (YouTube/TikTok/Twitch)", required=True)
    platform_link = discord.ui.TextInput(label="Link de tu canal", required=True)
    followers = discord.ui.TextInput(label="Seguidores actuales", required=True)
    avg_views = discord.ui.TextInput(label="Visualizaciones promedio", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        ticket_ch = await guild.create_text_channel(
            f"solicitud-{interaction.user.name}",
            overwrites=overwrites
        )

        app_id = await db.execute_and_get_id("""
            INSERT INTO applications 
            (discord_id, minecraft_ign, platform, platform_link, followers, avg_views, status)
            VALUES (?, ?, ?, ?, ?, ?, 'PENDIENTE')
        """, (interaction.user.id, self.minecraft_ign.value, self.platform.value,
              self.platform_link.value, self.followers.value, self.avg_views.value))

        manager_role = guild.get_role(CONFIG.MEDIA_MANAGER_ROLE_ID)
        embed = info_embed(
            "Nueva Solicitud Media",
            f"**De:** {interaction.user.mention}\n"
            f"**MC:** {self.minecraft_ign.value}\n"
            f"**Plataforma:** {self.platform.value}\n"
            f"**ID:** `{app_id}`\n\n"
            f"Usa `/application-review {app_id}` para gestionarla."
        )

        if manager_role:
            await ticket_ch.send(f"{manager_role.mention}", embed=embed)
        else:
            await ticket_ch.send(embed=embed)

        await db.log_action("NUEVA_SOLICITUD", interaction.user.id, interaction.user.id,
                           f"Solicitud #{app_id} - {self.platform.value}")

        await interaction.response.send_message(
            embed=success_embed("Solicitud enviada", f"Se creo tu ticket: {ticket_ch.mention}"),
            ephemeral=True
        )

class Applications(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="solicitar-media-panel", description="Envia el panel de solicitudes")
    @is_media_manager()
    async def application_panel(self, interaction: discord.Interaction):
        embed = create_embed(
            "Solicitar unirse al Media Team",
            "Haz clic en el boton de abajo para enviar tu solicitud.\n\n"
            "**Requisitos minimos:**\n"
            "- YouTube: 50+ subs, 1 video de EskMC\n"
            "- TikTok: 75+ seguidores, 1 video de EskMC\n"
            "- Twitch: 50+ seguidores, 1 stream"
        )
        view = ApplicationButtonView()
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="application-review", description="Revisar una solicitud pendiente")
    @is_media_staff()
    async def review_application(self, interaction: discord.Interaction, app_id: int):
        app = await db.fetchone("SELECT * FROM applications WHERE id = ?", (app_id,))
        if not app:
            await interaction.response.send_message(embed=error_embed("No encontrada"), ephemeral=True)
            return

        embed = create_embed(
            f"Solicitud #{app_id}",
            f"**Usuario:** <@{app['discord_id']}>\n"
            f"**MC Nick:** {app['minecraft_ign']}\n"
            f"**Plataforma:** {app['platform']}\n"
            f"**Link:** {app['platform_link']}\n"
            f"**Seguidores:** {app['followers']}\n"
            f"**Estado:** {app['status']}"
        )
        view = ReviewApplicationView(app_id, app['discord_id'])
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class ApplicationButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="SOLICITAR MEDIA", style=discord.ButtonStyle.green, custom_id="apply_media")
    async def apply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        existing = await db.fetchone(
            "SELECT * FROM applications WHERE discord_id = ? AND status = 'PENDIENTE'",
            (interaction.user.id,)
        )
        if existing:
            await interaction.response.send_message(
                embed=error_embed("Ya tienes una solicitud pendiente"), ephemeral=True
            )
            return

        modal = FullApplicationModal()
        await interaction.response.send_modal(modal)

class ReviewApplicationView(discord.ui.View):
    def __init__(self, app_id: int, user_id: int):
        super().__init__(timeout=None)
        self.app_id = app_id
        self.user_id = user_id

    @discord.ui.button(label="Aceptar", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        app = await db.fetchone("SELECT * FROM applications WHERE id = ?", (self.app_id,))
        if not app:
            return

        followers = int(app['followers']) if str(app['followers']).isdigit() else 0
        if followers >= 300:
            rank = "FAMOSO"
        elif followers >= 150:
            rank = "MEDIA+"
        else:
            rank = "MEDIA"

        await db.add_creator(app['discord_id'], app['minecraft_ign'], rank,
                            app['platform'], followers)

        await db.execute(
            "UPDATE applications SET status = 'ACEPTADA', reviewed_by = ? WHERE id = ?",
            (interaction.user.id, self.app_id)
        )

        guild = interaction.guild
        member = guild.get_member(self.user_id)
        rank_info = CONFIG.RANKS[rank]
        role = discord.utils.get(guild.roles, name=rank_info["role_name"])

        if member and role:
            await member.add_roles(role)

        welcome_embed = create_embed(
            "Bienvenido al Media Team!",
            f"{member.mention if member else f'<@{self.user_id}>'} ha sido aceptado como **{rank}**.\n\n"
            f"**Plataforma:** {app['platform']}\n"
            f"**Proxima renovacion:** 30 dias\n\n"
            f"Empieza a crear contenido para EskMC!"
        )

        welcome_ch = discord.utils.get(guild.text_channels, name="bienvenida-media")
        if welcome_ch:
            await welcome_ch.send(embed=welcome_embed)

        await db.log_action("SOLICITUD_ACEPTADA", self.user_id, interaction.user.id,
                           f"Rango asignado: {rank}")

        await interaction.response.send_message(embed=success_embed("Solicitud aceptada"), ephemeral=True)

    @discord.ui.button(label="Rechazar", style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        await db.execute(
            "UPDATE applications SET status = 'RECHAZADA', reviewed_by = ? WHERE id = ?",
            (interaction.user.id, self.app_id)
        )
        await db.log_action("SOLICITUD_RECHAZADA", self.user_id, interaction.user.id, "")
        await interaction.response.send_message(embed=error_embed("Solicitud rechazada"), ephemeral=True)

    @discord.ui.button(label="Revision", style=discord.ButtonStyle.gray)
    async def review(self, interaction: discord.Interaction, button: discord.ui.Button):
        await db.execute(
            "UPDATE applications SET status = 'EN REVISION', reviewed_by = ? WHERE id = ?",
            (interaction.user.id, self.app_id)
        )
        await interaction.response.send_message(embed=info_embed("En revision"), ephemeral=True)

async def setup(bot):
    await bot.add_cog(Applications(bot))
