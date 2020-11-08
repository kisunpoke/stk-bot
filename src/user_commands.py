"""End-user commands for retrieving statistics and defining personal settings."""

import discord
from discord.ext import commands
import pprint

import osuapi
import db_get
import db_manip
import prompts
import image_manip

class UserConfigCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #temporary home
    @commands.command()
    async def helptest(self, ctx, command):
        import utils #yes yes i'll move it later
        embed = await utils.help_generator(command)
        await ctx.send(embed=embed)

    @commands.command()
    async def setuser(self, ctx, *user):
        """Associate this osu! username/id with this Discord ID.
        
        Either username or ID is valid, and the name does not need to be enclosed
        in quotes. If that player has not yet been registered in the database, it
        will refuse to associate them with that username. (No document will be created
        or modified as a result.)
        
        Successful player association will also automatically associate them with a team.
        This will allow the Discord user to use some player/team-related stat commands
        without having to define their username."""
        #first we check if we already have a discord document for them
        #we should assume it exists to prevent a mongodb add error
        #even if they don't follow through with adding themselves, we should still create
        #the document anyways
        user_doc = await db_get.get_user_document(ctx.message.author.id)
        user = " ".join([str(part) for part in user])
        player_doc = await db_get.get_player_document(user)
        if not player_doc:
            error = ("Couldn't find that tournament player. Try enclosing your name in quotes "
                     "`(\"\")` or using your actual osu! user ID. Note that non-tournament players "
                     "can't be registered!")
            await prompts.error_embed(self.bot, ctx, error)
            return None
        check_msg = (f"Is this you?\n\n"
                     f"osu! username: {player_doc['user_name']}\n"
                     f"osu! ID: {player_doc['_id']}\n"
                     f"Team: {player_doc['team_name']}\n")
        if await prompts.confirmation_dialog(self.bot, ctx, check_msg):
            user_doc["osu_name"] = player_doc["user_name"]
            user_doc["osu_id"] = player_doc["_id"]
            user_doc["team_name"] = player_doc["team_name"]
            await db_manip.update_discord_user(ctx.message.author.id, user_doc)
            ok_msg = (f"Done! You are now {player_doc['user_name']}. "
                      f"You should now be able to use some stat commands without "
                      f"needing to type in your name or team.")
            await ctx.send(ok_msg)

    @commands.command(aliases=["forgetme", "unset"])
    async def unsetuser(self, ctx):
        """Reset all DiscordUser document fields for this user."""
        user_doc = await db_get.get_user_document(ctx.message.author.id)
        osu_name = user_doc["osu_name"]
        if osu_name is None:
            await prompts.std_embed(self.bot, ctx, "You aren't associated with an osu! player!")
        else:
            if await prompts.confirmation_dialog(self.bot, ctx, f"Do you want to stop being {osu_name}?"):
                user_doc["osu_name"] = None
                user_doc["osu_id"] = None
                user_doc["team_name"] = None
                await db_manip.update_discord_user(ctx.message.author.id, user_doc)
                await ctx.send(f"Done - you are no longer {osu_name}.")

    @commands.command(aliases=["userinfo", "me"])
    async def whois(self, ctx, user: discord.Member = None):
        """Get the osu! player data associated with a user."""
        if user is None:
            #implying themselves
            user_doc = await db_get.get_user_document(ctx.message.author.id)
        else:
            user_doc = await db_get.get_user_document(user.id)

        if user_doc["osu_name"] is not None:
            display_name = ctx.message.author.display_name if user==None else user.display_name
            msg = (f"Information for {display_name}:\n\n"
                f"osu! username: {user_doc['osu_name']}\n"
                f"osu! ID: {user_doc['osu_id']}\n"
                f"Team: {user_doc['team_name']}\n")
            await prompts.std_embed(self.bot, ctx, msg)
        else:
            if user is None:
                await ctx.send(f"You haven't set your osu! username.")
            else:
                await ctx.send(f"{user.display_name} hasn't set their osu! username.")

    
    @whois.error
    async def whois_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await prompts.error_embed(self.bot, ctx, "You need to mention one user (or nobody)!", error)
    
    @commands.command(hidden=True)
    async def showconfigs(self, ctx):
        """Show the configs associated with this discord ID.
        
        If this command is run without the discord ID already existing in the
        database, then a DiscordUser document is created."""
        pass

    @commands.command(hidden=True)
    async def setconfig(self, ctx, config, value):
        """Change the config associated with this discord ID.
        
        If this command is run without the discord ID already existing in the
        database, then a DiscordUser document is created."""
        pass

class UserStatsCommands(commands.Cog):
    """Commands for all stats except individual matches.
    
    (This is because the match stats cog is partially tournament-independent, unlike
    these which don't really make sense without a tournament)
    """
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(aliases=["ps"])
    async def playerstats(self, ctx, *user):
        """Post the stats of a user.
        
        If no user is defined, then it is assumed to be the one associated with that
        Discord ID. If the invoker has no associated osu! user, tells the invoker to associate
        themselves with a username/user id."""
        if not user:
            user = await db_get.get_name_from_user(ctx.message.author.id, return_player=True)
            #means this discord user doesn't have any name set
            if not user:
                await prompts.error_embed(self, ctx, "I need a name - try `setuser <your osu! username/id>` if "
                                                     "you're referring to yourself.")
                return None
        player_document = await db_get.get_player_document(user)
        if player_document is None:
            error = ("Couldn't find that tournament player. Try enclosing your name in quotes "
                     "`(\"\")` or using your actual osu! user ID. Note that non-tournament players "
                     "don't have stats! (Also, I don't know if you've had a username change!)")
            await prompts.error_embed(self, ctx, error)
            return None
        player_url = f'https://osu.ppy.sh/u/{player_document["_id"]}'
        stat = player_document["cached"]

        #wow that's a tad unreadable
        msg = (f"STK8 stats for {player_document['user_name']}\n"
               f"\n"
               f"__Averages__\n"
               f"**Avg. Score:** {stat['average_score']} (#{stat['score_rank']})\n"
               f"**Avg. Accuracy:** {stat['average_acc']} (#{stat['acc_rank']})\n"
               f"**Avg. Contrib:** {stat['average_contrib']} (#{stat['contrib_rank']})\n"
               f"\n"
               f"__General__\n"
               f"**Hits (300/100/50/miss):** {stat['hits']['300_count']}/{stat['hits']['50_count']}/"
               f"{stat['hits']['100_count']}/{stat['hits']['miss_count']}\n"
               f"**Maps played:** {stat['maps_played']} (W/L: {stat['maps_won']}/{stat['maps_lost']}, "
               f"{'{:.2%}'.format(stat['maps_won']/stat['maps_played'])})\n"
               f"\n"
               f"__Mod Information__\n"
               f"sorry i forgot we don't have the technology for that yet lmao")
        em_msg = discord.Embed(description=msg)
        em_msg.set_author(name=player_document["user_name"], url=player_url)
        em_msg.set_thumbnail(url=player_document["pfp_url"])
        em_msg.set_footer(text=f"You can get a list of this player's scores with !!playerbest {player_document['user_name']}. "
                               f"You can also use !!playercard {player_document['user_name']} for their player card.")
        await ctx.send(embed=em_msg)

    @commands.command(aliases=["ts"])
    async def teamstats(self, ctx, *team):
        """Post the stats of a team.
        
        If no team is defined, then it is assumed to be the one associated with that
        Discord ID. If the invoker has no associated osu! user, tells the invoker to associate
        themselves with a username/user id, which implicitly associates them with a team."""
        team_name = " ".join(team)
        if team_name:
            team_doc = await db_get.get_team_document(team_name)
            if not team_doc:
                await prompts.error_embed(self, ctx, "Couldn't find that team...")
                return None
        else:
            team_name = await db_get.get_name_from_user(ctx.message.author.id, return_player=False)
            if not team_name:
                await prompts.error_embed(self, ctx, "I need a team name (or set your team with `setuser`)!")
            else:
                team_doc = await db_get.get_team_document(team_name)
        await ctx.trigger_typing()
        image_object = await image_manip.make_team_card(team_doc)
        await ctx.send(file=discord.File(fp=image_object, filename='team_stats_team_name.png'))

    @commands.command(aliases=["pb"])
    async def playerbest(self, ctx, *params):
        """Post the nth page of a user's best scores, filtered by mod if defined.
        
        The default parameter configuration is `playerbest <user> <page> <mod>`, all optional:
        -`user` is the username or user ID of the player to lookup. If not defined, the
        osu! user associated with the invoker's Discord ID is used. If no osu! user can be
        associated, then asks the user to use `setuser` or explicitly define the username.
        -`page` determines what set of 10 scores is returned (1-10, 11-10, ...). See
        db_get.get_top_player_scores() for more. Page 1 by default.
        -`mod` is the shorthand mod to filter scores by. Valid options are likely
        `["NM", "HR", "HD", "DT", and "FM"]`. Note these mods are associated with shorthand pool
        IDs, not the *actual* mods played. TB = FM. No filter by default (i.e. returns all scores).
        
        (Formally, the database command can take both - however, we probably want map types.
        Also, freemod doesn't yield individual mods, nor do we check for them.)

        Parameters are checked from last to first until something that is definitely not a mod
        or a page number is found, at which point that is assumed to be the username. Defaults
        apply if `user`, `page`, or `mod` wasn't changed by this check."""
        user = None
        page = 1
        mod = None
        #determine what each parameter MIGHT be, last to first
        for index in range(1,len(params)+1):
            if params[-index].upper() in ["NM", "HD", "HR", "DT", "FM"]:
                #fields in mongodb are case-sensitive
                mod = params[-index].upper()
            elif params[-index].isdigit() and int(params[-index])<1000:
                page = int(params[-index])
            else:
                #the remainder is assumed to be the username, at which point we stop
                if index == 1:
                    #slicing from zero doesn't work
                    user = " ".join(params)
                else:
                    user = " ".join(params[:-(index-1)])
                break
        if user is None:
            user = await db_get.get_name_from_user(ctx.message.author.id, return_player=True)
            if not user:
                await prompts.error_embed(self, ctx, "I need a name - try `setuser <your osu! username/id>` if "
                                                     "you're referring to yourself.")
                return None
        pprint.pprint(await db_get.get_top_player_scores(user, page, mod))
        #rendering goes here

    @commands.command(aliases=["tb"])
    async def teambest(self, ctx, *params):
        """Post the nth page of a team's best scores, filtered by mod if defined.
        
        The default parameter configuration is `playerbest <team> <page> <mod>`, all optional:
        -`team` is full name of the team to lookup. If not defined, the
        osu! user (and thus team) associated with the invoker's Discord ID is used. If no team can be
        associated, then asks the user to use `setuser` or explicitly define the team name.
        -`page` determines what set of 10 scores is returned (1-10, 11-10, ...). See
        db_get.get_top_player_scores() for more. Page 1 by default.
        -`mod` is the shorthand mod to filter scores by. Valid options are likely
        `["NM", "HR", "HD", "DT", and "FM"]`. Note these mods are associated with shorthand pool
        IDs, not the *actual* mods played. TB = FM. No filter by default (i.e. returns all scores).
        
        (Formally, the database command can take both - however, we probably want map types.
        Also, freemod doesn't yield individual mods, nor do we check for them.)

        Parameters are checked from last to first until something that is definitely not a mod
        or a page number is found, at which point that is assumed to be the username. Defaults
        apply if `team`, `page`, or `mod` wasn't changed by this check."""
        team = None
        page = 1
        mod = None
        #determine what each parameter MIGHT be, last to first
        for index in range(1,len(params)+1):
            if params[-index].upper() in ["NM", "HD", "HR", "DT", "FM"]:
                #fields in mongodb are case-sensitive
                mod = params[-index].upper()
            elif params[-index].isdigit() and int(params[-index])<1000:
                page = int(params[-index])
            else:
                #the remainder is assumed to be the username, at which point we stop
                if index == 1:
                    #slicing from zero doesn't work
                    team = " ".join(params)
                else:
                    team = " ".join(params[:-(index-1)])
                break
        if team is None:
            team = await db_get.get_name_from_user(ctx.message.author.id, return_player=False)
            if not team:
                await prompts.error_embed(self, ctx, "I need a team - try `setuser <your osu! username/id>` if "
                                                     "you're referring to your team.")
                return None
        pprint.pprint(await db_get.get_top_team_scores(team, page, mod))
        #rendering goes here

    @commands.command(aliases=["mb"])
    async def mapbest(self, ctx, map_id, page=1, pool=None):
        """Post the nth page of a map's best scores.
        
        - `map_id` can either be a beatmap ID (b/...) or standard notation
        (NM1, HR2, etc.)
        - `page` works the same as every similar command; 10 per page, redirects for <1
        or > the maximum.
        - `pool` is shorthand pool notation (QF, GF, Ro32, etc). Ignored if
        map_id is a beatmap ID."""
        pprint.pprint(await db_get.get_top_map_scores(map_id, page, pool))

    @commands.command(aliases=["sb"])
    async def serverbest(self, ctx, leaderboard="score", page=1, mod=None):
        """Post the leaderboard rankings of every score.
        
        - `leaderboard` is any of "acc", "score", or "contrib." 
        - `page` works the same as every similar command; 10 per page, redirects for <1
        or > the maximum.
        - `mod` can be any of ["NM", "HD", "HR", "DT", or "FM"]."""
        pprint.pprint(await db_get.get_top_tournament_scores(leaderboard, page, mod))

    @commands.command(aliases=["avglbp", "averageleaderboardp"])
    async def averagelbp(self, ctx, leaderboard="score", page=1):
        """Get the best players of the given statistic.
        
        -`leaderboard` is any of "acc", "score", or "contrib". 
        -`page` works the same as every other paginated command.""" 
        pprint.pprint(await db_get.get_top_tournament_players(leaderboard, page))

    @commands.command(aliases=["avglbt", "averageleaderboardt"])
    async def averagelbt(self, ctx, leaderboard="score", page=1):
        """Get the best teams of the given statistic.
        
        `leaderboard` is either "acc" or "score". `page` works
        the same as every other paginated command.""" 
        pprint.pprint(await db_get.get_top_tournament_teams(leaderboard, page))
    