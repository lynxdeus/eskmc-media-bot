"""Sistema de gestion de followers para creadores."""
import discord
from discord import app_commands
from discord.ext import commands
from database import db
from utils.embeds import success_embed, error_embed, info_embed
from utils.checks import is_media_staff

class FollowersModal(discord.ui.Modal, title="Actualizar tus Seguidores"):
    followers = discord.ui.TextInput(
        label="Cantidad de seguidores",
        placeholder="Ejemplo: 1500",
        required=True
    )
    platform = discord.ui.TextInput(
        label="Plataforma principal",
        placeholder="YouTube / TikTok / Twitch / Instagram",
        required=True
    )
    proof_link = discord.ui.TextInput(
        label="Link de prueba (opcional)",
        placeholder="https://...",
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        creator = await db.get_creator(interaction.user.id)
        if not creator:
            await interaction.response.send_message(
                embed=error_embed("No eres creador del Media Team"), ephemeral=True
            )
            return

        try:
            new_followers = int(self.followers.value)
        except ValueError:
            await interaction.response.send_message(
                embed=error_embed("La cantidad debe ser un numero valido"), ephemeral=True
            )
            return

        old_followers = creator["followers"] or 0

        await db.execute(
            "UPDATE creators SET followers = ?, platform = ? WHERE discord_id = ?",
            (new_followers, self.platform.value, interaction.user.id)
        )

        await db.log_action("FOLLOWERS_ACTUALIZADOS", interaction.user.id, interaction.user.id,
                           f"{old_followers} -> {new_followers} en {self.platform.value}")

        proof_text = f"\n**Prueba:** {self.proof_link.value}" if self.proof_link.value else ""

        await interaction.response.send_message(
            embed=success_embed(
                "Seguidores actualizados",
                f"Tus seguidores han sido actualizados.\n"
                f"**Anterior:** {old_followers}\n"
                f"**Nuevo:** {new_followers}\n"
                f"**Plataforma:** {self.platform.value}"
                f"{proof_text}"
            ), ephemeral=True
        )

class Followers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="followers-update", description="Actualizar tu cantidad de seguidores")
    async def followers_update(self, interaction: discord.Interaction):
        creator = await db.get_creator(interaction.user.id)
        if not creator:
            await interaction.response.send_message(
                embed=error_embed("No eres creador del Media Team"), ephemeral=True
            )
            return

        modal = FollowersModal()
        await interaction.response.send_modal(modal)

    @app_commands.command(name="followers-set", description="Establecer followers de un creador (Staff)")
    @is_media_staff()
    async def followers_set(self, interaction: discord.Interaction,
                            usuario: discord.Member,
                            cantidad: int,
                            plataforma: str = None):
        creator = await db.get_creator(usuario.id)
        if not creator:
            await interaction.response.send_message(
                embed=error_embed("El usuario no es creador del Media Team"), ephemeral=True
            )
            return

        old_followers = creator["followers"] or 0

        if plataforma:
            await db.execute(
                "UPDATE creators SET followers = ?, platform = ? WHERE discord_id = ?",
                (cantidad, plataforma, usuario.id)
            )
        else:
            await db.execute(
                "UPDATE creators SET followers = ? WHERE discord_id = ?",
                (cantidad, usuario.id)
            )

        await db.log_action("FOLLOWERS_EDITADOS_STAFF", usuario.id, interaction.user.id,
                           f"{old_followers} -> {cantidad}")

        platform_text = f" | Plataforma: {plataforma}" if plataforma else ""

        await interaction.response.send_message(
            embed=success_embed(
                "Followers actualizados",
                f"{usuario.mention}\n"
                f"**Anterior:** {old_followers}\n"
                f"**Nuevo:** {cantidad}"
                f"{platform_text}"
            )
        )

    @app_commands.command(name="followers-view", description="Ver followers de un creador")
    async def followers_view(self, interaction: discord.Interaction,
                              usuario: discord.Member = None):
        target = usuario or interaction.user
        creator = await db.get_creator(target.id)

        if not creator:
            await interaction.response.send_message(
                embed=error_embed("El usuario no es creador del Media Team"), ephemeral=True
            )
            return

        followers = creator["followers"] or 0
        platform = creator["platform"] or "No especificada"
        rank = creator["rank"] or "N/A"

        # Calcular posicion en el leaderboard
        all_creators = await db.fetchall(
            "SELECT discord_id FROM creators WHERE status != 'RETIRADO' ORDER BY followers DESC"
        )
        position = next((i+1 for i, c in enumerate(all_creators) if c["discord_id"] == target.id), None)
        total = len(all_creators)

        embed = info_embed(
            f"Seguidores de {target.display_name}",
            f"**Cantidad:** `{followers}`\n"
            f"**Plataforma:** {platform}\n"
            f"**Rango:** {rank}\n"
            f"**Posicion global:** #{position} de {total}\n\n"
            f"Usa `/followers-update` para actualizar tus seguidores."
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="followers-top", description="Top creadores por seguidores")
    async def followers_top(self, interaction: discord.Interaction,
                            limite: int = 10):
        if limite > 25:
            limite = 25

        top = await db.fetchall(
            """SELECT * FROM creators 
            WHERE status != 'RETIRADO' 
            ORDER BY followers DESC 
            LIMIT ?""",
            (limite,)
        )

        if not top:
            await interaction.response.send_message(
                embed=error_embed("No hay creadores registrados"), ephemeral=True
            )
            return

        description = ""
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟",
                   "1️⃣1️⃣", "1️⃣2️⃣", "1️⃣3️⃣", "1️⃣4️⃣", "1️⃣5️⃣", "1️⃣6️⃣", "1️⃣7️⃣", "1️⃣8️⃣", "1️⃣9️⃣", "2️⃣0️⃣",
                   "2️⃣1️⃣", "2️⃣2️⃣", "2️⃣3️⃣", "2️⃣4️⃣", "2️⃣5️⃣"]

        for i, creator in enumerate(top):
            member = interaction.guild.get_member(creator["discord_id"])
            name = member.display_name if member else f"Usuario {creator['discord_id']}"
            platform = creator['platform'] or "N/A"
            followers = creator['followers'] or 0
            rank = creator['rank'] or "MEDIA"

            description += (
                f"{medals[i]} **{name}** | `{followers:,}` followers | "
                f"{platform} | {rank}\n"
            )

        embed = info_embed(
            f"📊 TOP {len(top)} POR SEGUIDORES",
            description
        )
        embed.set_footer(text="EskMC Media Team | Usa /followers-update para actualizar")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="followers-platform", description="Top creadores por plataforma")
    async def followers_platform(self, interaction: discord.Interaction,
                                  plataforma: str,
                                  limite: int = 10):
        if limite > 25:
            limite = 25

        top = await db.fetchall(
            """SELECT * FROM creators 
            WHERE status != 'RETIRADO' AND UPPER(platform) = UPPER(?)
            ORDER BY followers DESC 
            LIMIT ?""",
            (plataforma, limite)
        )

        if not top:
            await interaction.response.send_message(
                embed=error_embed(f"No hay creadores en {plataforma}"), ephemeral=True
            )
            return

        description = ""
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        for i, creator in enumerate(top):
            member = interaction.guild.get_member(creator["discord_id"])
            name = member.display_name if member else f"Usuario {creator['discord_id']}"
            followers = creator['followers'] or 0
            rank = creator['rank'] or "MEDIA"

            description += (
                f"{medals[i]} **{name}** | `{followers:,}` followers | {rank}\n"
            )

        embed = info_embed(
            f"📊 TOP {plataforma.upper()}",
            description
        )

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Followers(bot))
