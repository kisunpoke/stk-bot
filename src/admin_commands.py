"""Administrative commands/cogs."""
import discord
from discord.ext import commands
import db_manip
import pprint

class AdminConfigCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
class AdminDatabaseCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def getval(self, ctx, key, value, db, collection):
        """Find and send the MongoDB document with key:value in db[collection], pretty-printed."""
        document = await db_manip.getval(key, value, db, collection)
        pprint_doc = pprint.pformat(document, indent=4)
        await ctx.send(pprint_doc)

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
        
