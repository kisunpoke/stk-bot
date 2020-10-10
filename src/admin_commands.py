"""Administrative commands/cogs."""

#add a setting that changes whether or not this bot automatically updates the rebuild spreadsheet?

import discord
from discord.ext import commands
import db_manip
import pprint
import asyncio

async def confirmation_dialog(bot, ctx, content, footer=""):
    """Generate and send a reaction-based confirmation dialog."""
    em_msg = discord.Embed(description=content)
    if footer:
        em_msg.set_footer(text=footer)
    conf_message = await ctx.send(embed=em_msg)
    await conf_message.add_reaction('✅')
    await conf_message.add_reaction('❌')

    def check(reaction, user):
        #verify that the user who initiated the command is reacting to the right message
        #(also ignore any other reactoins)
        return user == ctx.author and reaction.message.id == conf_message.id and reaction.emoji in ('❌', '✅')

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=20.0, check=check)
        await conf_message.delete()
    except asyncio.TimeoutError:
        #we could delete the confirmation message here
        await ctx.send('Response timed out.')
    else:
        if reaction.emoji == '✅':
            return True
        else:
            return False

async def error_embed(bot, ctx, content, footer=""):
    """Generate and send an error message."""
    em_msg = discord.Embed(description=content, color=0xFF0000)
    if footer:
        em_msg.set_footer(text=footer)
    await ctx.send(embed=em_msg)

class AdminConfigCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def updateconfig(self, ctx, setting, value):
        pass

    @commands.command()
    async def listconfigs(self, ctx):
        pass
    
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
    async def setval(self, ctx, key, value, db, collection):
        """Insert a MongoDB document with key:value in db[collection]."""
        await db_manip.setval(value)
        await ctx.send("done")

    @commands.command()
    async def deleteval(self, ctx, key, value, db='test', collection='test-data'):
        """Delete the MongoDB document with key:value in db[collection]."""
        await db_manip.deleteval(key, value, db, collection)
        await ctx.send("done")

    @commands.command()
    async def rebuildall(self, ctx, sheet_id=None):
        """Rebuild the *entire* database from scratch from the specified gsheet id."""
        if sheet_id is not None:
            if await confirmation_dialog(self.bot, ctx, "Rebuild all?"):
                await ctx.send("ok, processing")
                await db_manip.rebuild_all(sheet_id, ctx)
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
        footer = "If you are adding many at once, you may want to consider using !!rebuildplayers."
        response = await confirmation_dialog(self.bot, ctx, confirmation_msg, footer)
        if response:
            await ctx.send(f"ok, adding the team {player_data}")
            #won't uncomment for now
            #await db_manip.add_players_and_teams(player_data)
            await ctx.send("ok, done; you may also want to consider adding this team to the data spreadsheet")
        else:
            await ctx.send("Canceled.")

    @commands.command()
    async def deleteteam(self, ctx, team_name):
        """Delete `team_name` from the database."""
        #team_document = await
        team_document = None
        if team_document is None:
            await ctx.send("Couldn't find that team. Use quotes if there are spaces.")
        else:
            player_str = "\n".join(team_document['players'])
            confirmation_msg = (
                f"You are deleting the following team:\n\n"
                f"**{team_name}\n**"
                f"{player_str}\n\n"
                f"Are you sure?"
            )
            footer = "If you are editing/deleting many at once, you may want to consider using !!rebuildplayers."
            response = await confirmation_dialog(self.bot, ctx, confirmation_msg, footer)
            if response:
                await ctx.send(f"ok, deleting the team {team_name}")
                #won't uncomment for now
                #await db_manip.add_players_and_teams(player_data)
                await ctx.send("ok, done; you may also want to update this team on the data spreadsheet")
            else:
                await ctx.send("Canceled.")

    @commands.command()
    async def addmatch(self, ctx, match, pool_id, stage, bans=None, referee_id=None):
        """Add this match to the database and update all relevant data.

        This includes calls to update player and mappool data, as well as confirmation.
        """
        #get match data via osuapi
        #get list of maps from mappool meta doc based on pool_id
        #return list of matches that used a map from the specified pool_id
        #generate a confirmation embed
        #actually execute db_manip funct
        pass

    @commands.command()
    async def deletematch(self, ctx, match):
        """Delete this match from the database and update the involved players' data."""
        pass
