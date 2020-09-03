"""Administrative commands/cogs."""
import discord
from discord.ext import commands
import db_manip

class AdminConfigCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def forceupdate(self, ctx):
        pass

class AdminDatabaseCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def getval(self, ctx, value):
        """Generate and return a player card (as a direct image)."""
        e = await db_manip.getval(value)
        import pprint
        pprint.pprint(e)
        await ctx.send("done")

    @commands.command()
    async def setval(self, ctx, value):
        """Generate and return a player card (as a direct image)."""
        await db_manip.setval(value)
        await ctx.send("done")
