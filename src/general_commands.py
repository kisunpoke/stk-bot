"""Info/help commands."""

import discord
from discord.ext import commands
import pprint

class GeneralCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx, command=None):
        pass