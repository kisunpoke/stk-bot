"""Administrative commands/cogs."""
import discord
from discord.ext import commands
import db_manip

class AdminConfigCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
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

    @commands.command()
    async def forceupdate(self, ctx, sheet_id):
        """Rebuild the *entire* database from scratch from the specified gsheet id."""
        await ctx.send("ok, processing")
        data = await db_manip.rebuild_all(sheet_id, ctx)
        await ctx.send("done")
        
