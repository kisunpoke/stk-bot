"""End-user commands for retrieving statistics and defining personal settings."""

import discord
from discord.ext import commands
import pprint

import osuapi
import db_get
import db_manip
#yes yes unqualified functions bad
from admin_commands import error_embed

class UserConfigCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def setuser(self, ctx, *, user):
        """Associate this osu! username/id with this Discord ID.
        
        Either username or ID is valid, and the name does not need to be enclosed
        in quotes. If that player has not yet been registered in the database, it
        will refuse to associate them with that username. (No document will be created
        or modified as a result.)
        
        Successful player association will also automatically associate them with a team.
        This will allow the Discord user to use some player/team-related stat commands
        without having to define their username."""
        #first we check if they even exist; 
        user_doc = await db_get.get_user_document(ctx.message.author.id)
        if not user_doc:
            await db_manip.create_discord_user(ctx.message.author.id)
        player_doc = await db_get.get_player_document(user)
        if not player_doc:
            error = ("Couldn't find that tournament player. Try enclosing your name in quotes "
                     "`(\")` or using your actual osu! user ID. Note that non-tournament players "
                     "can't be registered!")
            await error_embed(self, ctx, error)
            return None
        user_doc["osu_name"] = player_doc["user_name"]
        user_doc["osu_id"] = player_doc["_id"]
        user_doc["team_name"] = player_doc["team_name"]
        db_manip.update_discord_user(ctx.message.author.id, user_doc)




    @commands.command()
    async def showconfigs(self, ctx):
        """Show the configs associated with this discord ID.
        
        If this command is run without the discord ID already existing in the
        database, then a DiscordUser document is created."""
        

    @commands.command()
    async def setconfig(self, ctx, config, value):
        """Change the config associated with this discord ID.
        
        If this command is run without the discord ID already existing in the
        database, then a DiscordUser document is created."""
        pass

class UserStatsCommands(commands.Cog):
    #except for matches, of course...
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(aliases=["ps"])
    async def playerstats(self, ctx, *, user=None):
        """Post the stats of a user.
        
        If no user is defined, then it is assumed to be the one associated with that
        Discord ID. If the invoker has no associated osu! user, tells the invoker to associate
        themselves with a username/user id."""
        pass

    @commands.command(aliases=["ts"])
    async def teamstats(self, ctx, *, team=None):
        """Post the stats of a team.
        
        If no team is defined, then it is assumed to be the one associated with that
        Discord ID. If the invoker has no associated osu! user, tells the invoker to associate
        themselves with a username/user id, which implicitly associates them with a team."""
        pass

    @commands.command(aliases=["pb"])
    async def playerbest(self, ctx, page=1, user=None, mod=None):
        """Post the nth page of a user's best scores, filtered by mod if defined.
        
        -`page` determines what set of 10 scores is returned (1-10, 11-10, ...). See
        db_get.get_top_player_scores() for more.
        -`user` is the username or user ID of the player to lookup. If not defined, the
        osu! user associated with the invoker's Discord ID is used. If no osu! user can be
        associated, then asks the user to use `setuser` or explicitly define the username.
        -`mod` is the shorthand mod to filter scores by. Valid options are likely
        `["NM", "HR", "HD", "DT", and "FM"]`. Note these mods are associated with shorthand pool
        IDs, not the *actual* mods played. TB = FM.
        
        (Formally, the database command can take both - however, we probably want map types.
        Also, freemod doesn't yield individual mods, nor do we check for them.)
        
        Parameters are ordered in the manner they are most likely needed to be defined. Notably,
        if only two parameters are defined, we assume that the `user` parameter actually refers to
        a mod. If that matches the set of valid mods, then it is accepted and the user is assumed to be
        the osu! user associated with that Discord ID. Of course, if no user is associated with that Discord
        ID, it will ask them to use `setuser`."""
        pass

    @commands.command(aliases=["tb"])
    async def teambest(self, ctx, page=1, team=None, mod=None):
        """Post the nth page of a user's best scores, filtered by mod if defined.
        
        -`page` determines what set of 10 scores is returned (1-10, 11-10, ...). See
        db_get.get_top_player_scores() for more.
        -`user` is the username or user ID of the player to lookup. If not defined, the
        osu! user associated with the invoker's Discord ID is used. If no osu! user can be
        associated, then asks the user to use `setuser` or explicitly define the username.
        -`mod` is the shorthand mod to filter scores by. Valid options are likely
        `["NM", "HR", "HD", "DT", and "FM"]`. Note these mods are associated with shorthand pool
        IDs, not the *actual* mods played. TB = FM.
        
        (Formally, the database command can take both - however, we probably want map types.
        Also, freemod doesn't yield individual mods, nor do we check for them.)"""
        pass

    @commands.command(aliases=["sbp", "serverbestp"])
    async def serverbest(self, ctx, leaderboard, page=1, mod=None):
        """Post the leaderboard rankings of every score.
        
        - `leaderboard` is any of "acc", "score", or "contrib." 
        - `page` works the same as every similar command; 10 per page, redirects for <1
        or > the maximum.
        - `mod` can be any of ["NM", "HD", "HR", "DT", or "FM"]."""
        pass

    @commands.command(aliases=["avglbp", "averagelbp"])
    async def averageleaderboardp(self, ctx, leaderboard, page=1):
        """Get the best players of the given statistic.
        
        `leaderboard` is any of "acc", "score", or "contrib." `page` works
        the same as every other paginated command."""
        pass

    @commands.command(aliases=["avglbp", "averagelbp"])
    async def averageleaderboardp(self, ctx, leaderboard, page=1):
        """Get the best players of the given statistic.
        
        `leaderboard` is any of "acc", "score", or "contrib." `page` works
        the same as every other paginated command.""" 
        pass
    
    @commands.command(aliases=["avglbt", "averagelbt"])
    async def averageleaderboardt(self, ctx, leaderboard, page=1):
        """Get the best teams of the given statistic.
        
        `leaderboard` is either "acc" or "score". `page` works
        the same as every other paginated command.""" 
        pass