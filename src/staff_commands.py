"""Administrative commands/cogs."""

#add a setting that changes whether or not this bot automatically updates the rebuild spreadsheet?

import discord
from discord.ext import commands
import db_manip
import pprint
import asyncio

import prompts
import osuapi
import db_get

#technically not used anywhere right now but here for future implementation
def has_role(role_id):
    async def predicate(ctx):
        staff_role = discord.utils.get(ctx.guild.roles, id=role_id)
        if staff_role in ctx.message.author.roles:
            return True
        else:
            return False
    return commands.check(predicate)

class StaffCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #limit usage to those with staff role only
    async def cog_check(self, ctx):
        staff_role = discord.utils.get(ctx.guild.roles, id=773752811539791902)
        if staff_role in ctx.message.author.roles:
            return True
        else:
            return False

    @commands.command()
    async def addmatch(self, ctx, match_id, bans=None, ignore_indexes=None, stage=None,  referee_id=None):
        """Add this match to the database and update all relevant data.

        This includes calls to update player and mappool data, as well as confirmation.
        """
        if await db_get.get_match_document(match_id):
            await prompts.error_embed(self.bot, ctx, "That match seems to have already been added!")
            return None

        ref_data = None
        ref_name = None
        ref_id = None
        if referee_id is not None:
            ref_data = await osuapi.get_player_data(referee_id)
            ref_name = ref_data["username"]
            ref_id = ref_data["user_id"]

        prompt = (f"Are these correct?\n\n"
                  f"**Match ID:** {match_id}\n"
                  f"**Bans:** {bans if bans else '-'}\n"
                  f"**Ignore indexes:** {ignore_indexes if ignore_indexes else '-'}\n"
                  f"**Stage:** {stage if stage else '-'}\n"
                  f"**Referee name:** {ref_id if ref_id else '-'}\n"
                  f"**Referee ID:** {ref_name if ref_name else '-'}\n\n"
                  f"(The command order is `match_id, bans, indexes, stage, referee`.))")
        footer = (f"Please make sure you're only putting commas with no spaces between"
                  f"your bans and indexes - `NM1,HR1` and `0,1,3`, for example. Put your "
                  f"stage name (and other multi-word parameters) in quotes.")
        if await prompts.confirmation_dialog(self.bot, ctx, prompt, footer):
            match_data = [[match_id, ref_id, ref_name, stage, bans, ignore_indexes]]
            await db_manip.add_scores(match_data)
            await ctx.send("ok, added match")
        else:
            await ctx.send("ok, maybe some other time")
    
    @addmatch.error
    async def addmatch_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await prompts.error_embed(self.bot, ctx, "You must be part of staff to add a match!", error)
        elif isinstance(error, commands.MissingRequiredArgument):
            await prompts.error_embed(self.bot, ctx, "Command order is `match_id, bans, indexes, stage, referee`"
                                                     " - see `help addmatch` for more info")
        else:
            await prompts.error_embed(self.bot, ctx, "An error occurred:", error)


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

    #limit usage to admins only
    async def cog_check(self, ctx):
        staff_role = discord.utils.get(ctx.guild.roles, id=773765194152411176)
        if staff_role in ctx.message.author.roles:
            return True
        else:
            return False
    
    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await prompts.error_embed(self.bot, ctx, "You must be an admin to use these commands!", error)
        else:
            await prompts.error_embed(self.bot, ctx, "An error occurred:", error)

    @commands.command(hidden=True)
    async def getval(self, ctx, key, value, db, collection):
        """Find and send the MongoDB document with key:value in db[collection], pretty-printed."""
        document = await db_manip.getval(key, value, db, collection)
        pprint_doc = pprint.pformat(document, indent=4)
        await ctx.send(pprint_doc)

    @commands.command(hidden=True)
    async def setval(self, ctx, key, value, db, collection):
        """Insert a MongoDB document with key:value in db[collection]."""
        await db_manip.setval(value)
        await ctx.send("done")

    @commands.command(hidden=True)
    async def deleteval(self, ctx, key, value, db='test', collection='test-data'):
        """Delete the MongoDB document with key:value in db[collection]."""
        await db_manip.deleteval(key, value, db, collection)
        await ctx.send("done")

    @commands.command(hidden=True)
    async def rebuildall(self, ctx, sheet_id=None):
        """Rebuild the *entire* cluster from scratch from the specified gsheet id.
        
        Does not include the DiscordUser database. Use individual deletion if you 
        find the need to delete a DiscordUser document, or wipe the whole thing."""
        if sheet_id is not None:
            if await prompts.confirmation_dialog(self.bot, ctx, "Rebuild all?"):
                await ctx.send("ok, processing")
                await db_manip.rebuild_all(self.bot, ctx, sheet_id)
        else:
            msg = ("hardcoded IDs:\n"
                   "STK8 data (full): 1OfLrz4o-Qt5k_JvpVl8CSiZsRt-veiFlFkuG8G0BnzU\n"
                   "STK8 data (minimal): -\n"
                   "STK9 data: -")
            await prompts.std_embed(self.bot, ctx, msg)

    
    

    ''' #unused
    #honestly at this point you may as well rebuild all lol
    #but likely the best way would be to do an inverse add_score, where you would
    #do -= everywhere a += is present, including child functions
    #it is possible, but it would be rather bothersome
    @commands.command()
    async def deletematch(self, ctx, match):
        """Delete this match from the database and update the involved players' data."""
        pass

    #there is virtually never a need to remove or modify a team after the tournament's
    #started (i.e., scores are being added) - so no implementation
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
            response = await prompts.confirmation_dialog(self.bot, ctx, confirmation_msg, footer)
            if response:
                await ctx.send(f"ok, deleting the team {team_name}")
                #won't uncomment for now
                #await db_manip.add_players_and_teams(player_data)
                await ctx.send("ok, done; you may also want to update this team on the data spreadsheet")
            else:
                await ctx.send("Canceled.")

    #same reason as above, just modify the target sheet instead
    @commands.command()
    async def addteam(self, ctx, team_name, *players):
        """Add a new team to the database.
        
        - `team_name` is a `str` of the new team's name.
        - `players` is an unlimited amount of players.
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
        response = await prompts.confirmation_dialog(self.bot, ctx, confirmation_msg, footer)
        if response:
            await ctx.send(f"ok, adding the team {player_data}")
            #won't uncomment for now
            #await db_manip.add_players_and_teams(player_data)
            await ctx.send("ok, done; you may also want to consider adding this team to the data spreadsheet")
        else:
            await ctx.send("Canceled.")
    '''