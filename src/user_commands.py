"""End-user commands for retrieving statistics and defining personal settings."""

import discord
from discord.ext import commands
import osuapi
import db_manip
import pprint

class UserConfigCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def setuser(self, ctx, *, user):
        """Associate this osu! username/id with this discord ID.
        
        Either username or ID is valid, and the name does not need to be enclosed
        in quotes."""
        await ctx.send(user)

    @commands.command()
    async def setteam(self, ctx, *, team):
        await ctx.send(team)

    @commands.command()
    async def showconfigs(self, ctx):
        pass

    @commands.command()
    async def setconfig(self, ctx, config, value):
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