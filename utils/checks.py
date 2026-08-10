"""Verificaciones de permisos."""
import discord
from discord.ext import commands
from config import CONFIG

def is_media_manager():
    async def predicate(ctx):
        manager_role = discord.utils.get(ctx.guild.roles, id=CONFIG.MEDIA_MANAGER_ROLE_ID)
        if manager_role in ctx.author.roles or ctx.author.guild_permissions.administrator:
            return True
        raise commands.MissingPermissions(["Media Manager"])
    return commands.check(predicate)

def is_media_staff():
    async def predicate(ctx):
        manager_role = discord.utils.get(ctx.guild.roles, id=CONFIG.MEDIA_MANAGER_ROLE_ID)
        staff_role = discord.utils.get(ctx.guild.roles, id=CONFIG.MEDIA_STAFF_ROLE_ID)
        if manager_role in ctx.author.roles or staff_role in ctx.author.roles or ctx.author.guild_permissions.administrator:
            return True
        raise commands.MissingPermissions(["Media Staff"])
    return commands.check(predicate)
