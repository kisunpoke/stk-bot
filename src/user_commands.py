"""End-user commands for retrieving statistics and defining personal settings."""

import discord
from discord.ext import commands
import pprint

import osuapi
import db_get
import db_manip
import prompts
import image_manip
from utils import percentage, comma_sep

class UserConfigCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
    
    @commands.command(aliases=["pc"])
    async def playercard(self, ctx, *player):
        """Post the player card of a player.
        
        If no user is defined, then it is assumed to be the one associated with that
        Discord ID. If the invoker has no associated osu! user, tells the invoker to associate
        themselves with a username/user id."""
        player_name = " ".join(player)
        if player_name:
            player_doc = await db_get.get_player_document(player_name)
            if not player_doc:
                error = ("Couldn't find that tournament player. Try enclosing your name in quotes "
                         "`(\"\")` or using your actual osu! user ID. Note that non-tournament players "
                         "don't have stats! (Also, I don't know if you've had a username change until "
                         "I'm updated - but you can still use your osu! ID.)")
                await prompts.error_embed(self, ctx, error)
                return None
        else:
            player_name = await db_get.get_name_from_user(ctx.message.author.id, return_player=True)
            if not player_name:
                await prompts.error_embed(self, ctx, "I need a player name (or set your name with `setuser`)!")
                return None
            else:
                player_doc = await db_get.get_player_document(player_name)
        await ctx.trigger_typing()
        image_object = await image_manip.make_player_card(player_doc)
        await ctx.send(file=discord.File(fp=image_object, filename=f'player_stats_{player_name}.png'))

    @commands.command(aliases=["ps"])
    async def playerstats(self, ctx, *player):
        """Post the stats of a user in text form.
        
        If no user is defined, then it is assumed to be the one associated with that
        Discord ID. If the invoker has no associated osu! user, tells the invoker to associate
        themselves with a username/user id."""
        player_name = " ".join(player)
        if player_name:
            player_doc = await db_get.get_player_document(player_name)
            if not player_doc:
                error = ("Couldn't find that tournament player. Try enclosing your name in quotes "
                         "`(\"\")` or using your actual osu! user ID. Note that non-tournament players "
                         "don't have stats! (Also, I don't know if you've had a username change until "
                         "I'm updated - but you can still use your osu! ID.)")
                await prompts.error_embed(self, ctx, error)
                return None
        else:
            player_name = await db_get.get_name_from_user(ctx.message.author.id, return_player=True)
            if not player_name:
                await prompts.error_embed(self, ctx, "I need a player name (or set your name with `setuser`)!")
                return None
            else:
                player_doc = await db_get.get_player_document(player_name)
        player_url = f'https://osu.ppy.sh/u/{player_doc["_id"]}'
        stat = player_doc["cached"]

        #mods
        mod_string = ""
        for mod in stat["by_mod"]:
            mod_stat = stat["by_mod"][mod]
            if mod_stat['maps_played'] == 0:
                text = "*None played.*"
            else:
                text = (f"**{mod}:**\n"
                        f"W/L: {mod_stat['maps_won']}/{mod_stat['maps_lost']} - "
                        f"{percentage(mod_stat['maps_won']/mod_stat['maps_played'])} winrate\n"
                        f"{comma_sep(mod_stat['average_score'])} avg. score, {percentage(mod_stat['average_acc'])} avg. acc, {percentage(mod_stat['average_contrib'])} avg. contrib\n\n")
            mod_string += text

        #raw unreadability
        msg = (f"__Averages__\n"
               f"**Avg. Score:** {comma_sep(stat['average_score'])} (#{stat['score_rank']})\n"
               f"**Avg. Accuracy:** {percentage(stat['average_acc'])} (#{stat['acc_rank']})\n"
               f"**Avg. Contrib:** {percentage(stat['average_contrib'])} (#{stat['contrib_rank']})\n"
               f"\n"
               f"__General__\n"
               f"**Hits (300/100/50/miss):** {comma_sep(stat['hits']['300_count'])}/{comma_sep(stat['hits']['100_count'])}/"
               f"{comma_sep(stat['hits']['50_count'])}/{comma_sep(stat['hits']['miss_count'])}\n"
               f"**Maps played:** {stat['maps_played']} (W/L: {stat['maps_won']}/{stat['maps_lost']}, "
               f"{percentage(stat['maps_won']/stat['maps_played'])})\n"
               f"\n"
               f"__Mod Information__\n"
               f"{mod_string}")
        em_msg = discord.Embed(description=msg)
        em_msg.set_author(name=player_doc["user_name"]+" - "+player_doc['team_name'], url=player_url)
        em_msg.set_thumbnail(url=player_doc["pfp_url"])
        em_msg.set_footer(text=f"You can get a list of this player's scores with \"pb {player_doc['user_name']}\". "
                               f"You can also use \"pc {player_doc['user_name']}\" for their player card.")
        await ctx.send(embed=em_msg)

    @commands.command(aliases=["pb"])
    async def playerbest(self, ctx, *params):
        """Post the nth page of a user's best scores, filtered by mod if defined.
        
        The default parameter configuration is `playerbest <user> <page> <mod>`, all optional:
        -`user` is the username or user ID of the player to lookup. If not defined, the
        osu! user associated with the invoker's Discord ID is used. If no osu! user can be
        associated, then asks the user to use `setuser` or explicitly define the username.
        (Note: `player_name` internally is referred to as the `user` externally, as the enduser
        doesn't need to make the distinction between Discord user and osu! user.)
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
        player_name = None
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
                    player_name = " ".join(params)
                else:
                    player_name = " ".join(params[:-(index-1)])
                break
        if player_name:
            score_docs, page, max_page = await db_get.get_top_player_scores(player_name, page, mod)
            if score_docs is None and max_page is None:
                error = ("Couldn't find that tournament player. Try enclosing your name in quotes "
                         "`(\"\")` or using your actual osu! user ID. Note that non-tournament players "
                         "don't have stats! (Also, I don't know if you've had a username change until "
                         "I'm updated - but you can still use your osu! ID.)")
                await prompts.error_embed(self, ctx, error)
                return None
            elif max_page == 0:
                await prompts.error_embed(self, ctx, "This player doesn't seem to have scores yet.")
                return None
        else:
            player_name = await db_get.get_name_from_user(ctx.message.author.id, return_player=True)
            if not player_name:
                await prompts.error_embed(self, ctx, "I need a player name (or set your name with `setuser`)!")
                return None
            else:
                score_docs, page, max_page = await db_get.get_top_player_scores(player_name, page, mod)
        await ctx.trigger_typing()
        image_object = await image_manip.make_player_best(score_docs, page, max_page, mod)
        await ctx.send(file=discord.File(fp=image_object, filename=f'team_stats_{player_name}.png'))

    @commands.command(aliases=["tc"])
    async def teamcard(self, ctx, *team):
        """Post the team card of a team.
        
        If no team is defined, then it is assumed to be the one associated with that
        Discord ID. If the invoker has no associated team, tells the invoker to associate
        themselves with a username/user id."""
        team_name = " ".join(team)
        if team_name:
            team_doc = await db_get.get_team_document(team_name)
            if not team_doc:
                await prompts.error_embed(self, ctx, "Couldn't find that team... (Try using quotes?)")
                return None
        else:
            team_name = await db_get.get_name_from_user(ctx.message.author.id, return_player=False)
            if not team_name:
                await prompts.error_embed(self, ctx, "I need a team name (or set your team with `setuser`)!")
                return None
            else:
                team_doc = await db_get.get_team_document(team_name)
        await ctx.trigger_typing()
        image_object = await image_manip.make_team_card(team_doc)
        await ctx.send(file=discord.File(fp=image_object, filename=f'team_stats_{team_name}.png'))

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
                await prompts.error_embed(self, ctx, "Couldn't find that team... (Try using quotes?)")
                return None
        else:
            team_name = await db_get.get_name_from_user(ctx.message.author.id, return_player=False)
            if not team_name:
                await prompts.error_embed(self, ctx, "I need a team name (or set your team with `setuser`)!")
                return None
            else:
                team_doc = await db_get.get_team_document(team_name)
        stat = team_doc["cached"]

        #mods
        mod_string = ""
        for mod in stat["by_mod"]:
            mod_stat = stat["by_mod"][mod]
            if mod_stat['maps_played'] == 0:
                text = "*None played.*"
            else:
                text = (f"**{mod}:**\n"
                        f"W/L: {mod_stat['maps_won']}/{mod_stat['maps_lost']} - "
                        f"{percentage(mod_stat['maps_won']/mod_stat['maps_played'])} winrate\n"
                        f"{comma_sep(mod_stat['average_score'])} avg. score, {percentage(mod_stat['average_acc'])} avg. acc\n\n")
            mod_string += text

        player_names = [(await db_get.get_player_document(player))["user_name"] for player in team_doc["players"]]

        #raw unreadability
        msg =  (f"__Averages__\n"
                f"**Avg. Score:** {comma_sep(stat['average_score'])} (#{stat['score_rank']})\n"
                f"**Avg. Accuracy:** {percentage(stat['average_acc'])} (#{stat['acc_rank']})\n"
                f"\n"
                f"__General__\n"
                f"**Hits (300/100/50/miss):** {comma_sep(stat['hits']['300_count'])}/{comma_sep(stat['hits']['100_count'])}/"
                f"{comma_sep(stat['hits']['50_count'])}/{comma_sep(stat['hits']['miss_count'])}\n"
                f"**Maps played:** {stat['maps_played']} (W/L: {stat['maps_won']}/{stat['maps_lost']}, "
                f"{percentage(stat['maps_won']/stat['maps_played'])})\n"
                f"\n"
                f"__Mod Information__\n"
                f"{mod_string}")
        em_msg = discord.Embed(description=msg)
        em_msg.set_author(name=team_doc["_id"]+" - "+' • '.join(player_names))
        em_msg.set_footer(text=f"You can get a list of this team's scores with \"tb {team_doc['_id']}\". "
                                f"You can also use \"tc {team_doc['_id']}\" for their team card.")
        await ctx.send(embed=em_msg)

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
        team_name = None
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
                    team_name = " ".join(params)
                else:
                    team_name = " ".join(params[:-(index-1)])
                break
        if team_name:
            score_docs, page, max_page = await db_get.get_top_team_scores(team_name, page, mod)
            if score_docs is None and max_page is None:
                await prompts.error_embed(self, ctx, "Couldn't find that team... (Try using quotes?)")
                return None
            elif max_page == 0:
                await prompts.error_embed(self, ctx, "This team doesn't seem to have scores yet.")
                return None
        else:
            team_name = await db_get.get_name_from_user(ctx.message.author.id, return_player=False)
            if not team_name:
                await prompts.error_embed(self, ctx, "I need a team name (or set your team with `setuser`)!")
                return None
            else:
                score_docs, page, max_page = await db_get.get_top_team_scores(team_name, page, mod)
        await ctx.trigger_typing()
        image_object = await image_manip.make_team_best(score_docs, page, max_page, mod)
        await ctx.send(file=discord.File(fp=image_object, filename=f'team_stats_{team_name}.png'))
    
    @commands.command(aliases=["ms"])
    async def mapstats(self, ctx, map_id, pool=None):
        """Post the nth page of a map's best scores.
        
        - `map_id` can either be a beatmap ID (b/...) or standard notation
        (NM1, HR2, etc.)
        - `pool` is shorthand pool notation (QF, GF, Ro32, etc). Ignored if
        map_id is a beatmap ID."""
        pprint.pprint(await db_get.get_map_document(map_id, pool))

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

#use the same bg and card system as teambest
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
    