"""Punto de entrada principal del bot EskMC Media Team."""
import discord
from discord.ext import commands
import asyncio
import os
from config import CONFIG
from database import db

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True

class EskMCBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=CONFIG.BOT_PREFIX,
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        await db.init()
        # Cargar cogs
        cogs_dir = "cogs"
        loaded = 0
        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    loaded += 1
                except Exception as e:
                    print(f"[ERROR] No se pudo cargar {filename}: {e}")
        print(f"[OK] {loaded} modulos cargados.")

        # Sincronizar comandos slash con el servidor especifico
        if CONFIG.GUILD_ID:
            guild = discord.Object(id=CONFIG.GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            print(f"[OK] {len(synced)} comandos slash sincronizados en el servidor.")
        else:
            synced = await self.tree.sync()
            print(f"[OK] {len(synced)} comandos slash sincronizados globalmente.")

    async def on_ready(self):
        print(f"[OK] Bot conectado como {self.user}")
        print(f"[OK] En {len(self.guilds)} servidor(es)")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="el Media Team de EskMC"
            )
        )

    async def on_command_error(self, ctx, error):
        from utils.embeds import error_embed
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=error_embed("Permisos insuficientes", str(error)))
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=error_embed("Argumento faltante", f"Uso: `{ctx.command.usage or ctx.command.signature}`"))
        else:
            await ctx.send(embed=error_embed("Error", str(error)))

bot = EskMCBot()

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    from utils.embeds import error_embed
    if interaction.response.is_done():
        await interaction.followup.send(embed=error_embed("Error", str(error)), ephemeral=True)
    else:
        await interaction.response.send_message(embed=error_embed("Error", str(error)), ephemeral=True)

async def main():
    async with bot:
        await bot.start(CONFIG.DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
