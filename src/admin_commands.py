"""Administrative commands/cogs."""

#add a setting that changes whether or not this bot automatically updates the rebuild spreadsheet?

import discord
from discord.ext import commands
import db_manip
import pprint
import asyncio

async def confirmation_dialog(bot, ctx, content):
    """Generate and send a reaction-based confirmation dialog."""
    #em_msg = discord.Embed(description=content)
    conf_message = await ctx.send(content)
    await conf_message.add_reaction('✅')
    await conf_message.add_reaction('❌')

    def check(reaction, user):
        print("checking")
        print(f"{user} == {ctx.author}: {user == ctx.author}")
        print(f"{str(reaction.emoji)} == '✅': {str(reaction.emoji) == '✅'}")
        print(f"{reaction.message} == {conf_message}: {reaction.message == conf_message}")
        #return user == ctx.author and str(reaction.emoji) == '✅' and reaction.message.id == conf_message.id
        return user == ctx.author and reaction.message.id == conf_message.id

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=10.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send('hurry up lol')
    else:
        await ctx.send(f'{reaction.emoji}')

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
    async def forcerebuild(self, ctx, sheet_id=None):
        """Rebuild the *entire* database from scratch from the specified gsheet id."""
        if sheet_id is not None:
            await ctx.send("ok, processing")
            data = await db_manip.rebuild_all(sheet_id, ctx)
            await ctx.send("done")
        else:
            #now actually make the list; ids should be a hyperlink
            await ctx.send("here's a hardcoded list of gsheet ids")

    @commands.command()
    async def addteam(self, ctx, team_name, players):
        """Add a new team to the database.
        
        - `team_name` is a `str` of the new team's name.
        - `players` is a comma-separated list of the players.
        """
        player_data = [team_name]
        for player in players.split(","):
            player_data.append(player)

        player_str = "\n".join(players.split(","))

        confirmation_msg = (
            f"You are adding the following team:\n\n"
            f"**{team_name}\n**"
            f"{player_str}\n\n"
            f"Is this correct?"
        )

        await confirmation_dialog(self.bot, ctx, confirmation_msg)
        '''
        await ctx.send(f"ok, adding the team {player_data}")
        #here should be an embed with yes/no reactions, deleted on reaction
        #confirm if this is the desired action

        #won't uncomment for now
        #await db_manip.add_players_and_teams(player_data)
        await ctx.send("ok, done; you may also want to consider adding this team to the data spreadsheet")
        '''
