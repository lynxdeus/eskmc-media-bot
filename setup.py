"""Comando /setup-media para inicializar el servidor."""
import discord
from discord import app_commands
from discord.ext import commands
from config import CONFIG
from utils.embeds import create_embed, success_embed, error_embed

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup-media", description="Configura la estructura completa del Media Team")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_media(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild

        from database import db
        config = await db.fetchone("SELECT setup_completed FROM server_config WHERE guild_id = ?", (guild.id,))
        if config and config["setup_completed"]:
            await interaction.followup.send(embed=error_embed("Ya configurado", "Este servidor ya tiene la estructura del Media Team."))
            return

        created_channels = []
        created_roles = []

        # ===== CREAR ROLES AUTOMATICAMENTE =====
        roles_to_create = ["MEDIA", "MEDIA+", "FAMOSO", "PARTNER", "O-MEDIA"]
        role_ids = {}

        for role_name in roles_to_create:
            existing = discord.utils.get(guild.roles, name=role_name)
            if existing:
                role_ids[role_name] = existing.id
                created_roles.append(f"{role_name} (ya existia)")
            else:
                try:
                    new_role = await guild.create_role(
                        name=role_name,
                        mentionable=True,
                        reason="Setup EskMC Media Bot"
                    )
                    role_ids[role_name] = new_role.id
                    created_roles.append(f"{role_name} (creado)")
                except Exception as e:
                    created_roles.append(f"{role_name} (ERROR: {e})")

        # Guardar IDs de roles en la base de datos
        await db.execute("""
            INSERT OR REPLACE INTO server_config 
            (guild_id, log_channel_id, manager_role_id, staff_role_id, 
             role_media, role_media_plus, role_famoso, role_partner, role_o_media, setup_completed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            guild.id, 
            CONFIG.LOG_CHANNEL_ID, 
            CONFIG.MEDIA_MANAGER_ROLE_ID, 
            CONFIG.MEDIA_STAFF_ROLE_ID,
            role_ids.get("MEDIA", 0),
            role_ids.get("MEDIA+", 0),
            role_ids.get("FAMOSO", 0),
            role_ids.get("PARTNER", 0),
            role_ids.get("O-MEDIA", 0)
        ))

        # ===== CREAR CATEGORIAS Y CANALES =====

        # INFORMACION
        cat_info = await guild.create_category("INFORMACION")
        info_channels = [
            "bienvenida-media", "reglamento-media", "requisitos-media",
            "beneficios-media", "renovaciones", "faq-media", "anuncios-media"
        ]
        for name in info_channels:
            ch = await guild.create_text_channel(name, category=cat_info)
            created_channels.append(ch.mention)

        # MEDIA TEAM
        cat_media = await guild.create_category("MEDIA TEAM")
        media_channels = [
            "chat-media", "contenido-media", "ideas-contenido",
            "colaboraciones", "campanas", "media-challenges"
        ]
        for name in media_channels:
            ch = await guild.create_text_channel(name, category=cat_media)
            created_channels.append(ch.mention)

        # COMPETICIONES
        cat_comp = await guild.create_category("COMPETICIONES")
        comp_channels = [
            "ranking-media", "creador-del-mes", "recompensas", "eventos-media"
        ]
        for name in comp_channels:
            ch = await guild.create_text_channel(name, category=cat_comp)
            created_channels.append(ch.mention)

        # SOLICITUDES
        cat_sol = await guild.create_category("SOLICITUDES")
        sol_channels = [
            "solicitar-media", "solicitar-renovacion",
            "solicitar-ascenso", "solicitar-partner", "soporte-media"
        ]
        for name in sol_channels:
            ch = await guild.create_text_channel(name, category=cat_sol)
            created_channels.append(ch.mention)

        # MEDIA MANAGEMENT (privado)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True)
        }
        cat_mgmt = await guild.create_category("MEDIA MANAGEMENT", overwrites=overwrites)
        mgmt_channels = [
            "media-log", "media-database", "solicitudes-pendientes",
            "renovaciones-pendientes", "ascensos-pendientes",
            "estadisticas-media", "configuracion-media"
        ]
        for name in mgmt_channels:
            ch = await guild.create_text_channel(name, category=cat_mgmt)
            created_channels.append(ch.mention)

        # Mensaje de bienvenida
        welcome_ch = discord.utils.get(guild.text_channels, name="bienvenida-media")
        if welcome_ch:
            embed = create_embed(
                "Bienvenido al Media Team de EskMC",
                "Este es el centro de gestion para todos los creadores de contenido.\n\n"
                "Usa los canales de **SOLICITUDES** para unirte o gestionar tu membresia.\n\n"
                "Consulta los requisitos y beneficios en los canales superiores!"
            )
            await welcome_ch.send(embed=embed)

        # Resumen
        roles_text = "\n".join([f"- {r}" for r in created_roles])
        await interaction.followup.send(
            embed=success_embed(
                "Setup completado",
                f"**Roles creados:**\n{roles_text}\n\n"
                f"**Canales creados:** {len(created_channels)}\n\n"
                f"**IMPORTANTE:** Configura manualmente los permisos de los roles "
                f"Media Manager y Media Staff en la categoria MEDIA MANAGEMENT."
            )
        )

async def setup(bot):
    await bot.add_cog(Setup(bot))
