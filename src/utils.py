"""stuff that doesn't fit anywhere right now, including help (which might get split into its own cog)"""

import discord

#yes zzz but shut
def percentage(value, precision=2):
    """Convert `float` to #.##% notation as `str`.
    
    A value of 1 = `"100.00%"`; 0.5 = `"50.00%"`"""
    return f"{value:.{precision}%}"
    

def comma_sep(value, precision=0):
    """Convert `int` to #,###.## notation as `str`"""
    #https://stackoverflow.com/questions/36626017/format-a-number-with-comma-separators-and-round-to-2-decimal-places-in-python-2
    return f"{value:,.{precision}f}"

async def help_generator(command):
    """Make the embed thing that's a pain to make or something
    
    Returns the embed itself, but doesn't send it."""
    info = help[command]
    embed = discord.Embed(description=info["signature"]+"\n"+info["summary"])

    embed.set_footer(text=f"help for {command} | i'm trying")

    embed.add_field(name="Parameters", value=info["parameters"], inline=False)
    embed.add_field(name="Examples", value=info["examples"], inline=False)
    return embed

#unfortunate
#markup is ok below

'''
"...":{
        "signature": ("**...** ..."),
        "summary":   ("*...*"),
        "parameters":(" - *...*: ...\n"
                      " - *...*: ...\n"
                      " - *...*: ...\n"
                      " - *...*: ..."),
        "examples":  (" - `...`: ...\n"
                      " - `...`: ...")
    },
'''

help = {
    "getmatch":{
        "signature": ("**getmatch** <match_id> [map_index]"),
        "summary":   ("*Get score and statistics data for a match.*"),
        "parameters":(" - *match_id*: /mp link provided by osu!\n"
                      " - *map_index (optional)*: The map index. If not defined, then statistics for the entire match are posted. If defined, then statistics for the nth map are given."),
        "examples":  (" - `getmatch 59424609`: gets general match statistics for the match at https://osu.ppy.sh/mp/59424609\n"
                      " - `getmatch 59424609 2`: gets statistics for the second map played on the same multiplier lobby")
    },
    "getmatch":{
        "signature": ("**addmatch** <match_id> [ignore_indexes] [stage] [bans] [referee_id]"),
        "summary":   ("*Add a new match to the database. Ignores maps that aren’t in any tournament pool.*"),
        "parameters":(" - *match_id*: /mp link provided by osu!\n"
                      " - *ignore_index (optional)*: A comma-separated list (no spaces in between) of the match indices to ignore. Zero-indexed.\n"
                      " - *stage (optional)*: The full name of the current stage (Round of 32, Grand Finals, etc.)\n"
                      " - *bans (optional)*: A comma-separated list (no spaces in between) of the bans in shorthand notation (NM1, HR1, etc.)\n"
                      " - *referee_id (optional)*: The ID of the player who reffed the match. Currently unused."),
        "examples":  (" - `addmatch 59424609`: adds https://osu.ppy.sh/mp/59424609 to the database, updating map/player/etc. stats and some other things\n"
                      " - `addmatch 59424609 0,1,2,5`: same as above but ignores the first three maps and the sixth map in calculation\n"
                      " - `addmatch 59424609 0,1 “Round of 32” NM1,HR2`: ignores the first two maps (warmups), sets the stage to Round of 32, and notes that NM1 and HR2 were banned")
    },
    "setuser":{
        "signature": ("**setuser** <user>"),
        "summary":   ("*Link your Discord account to an osu! username and tournament team. (Only works if the player is in the tournament.) Removes the need to put your name or your team’s name in some commands.*"),
        "parameters":(" - *user*: Either your osu! user ID (all numbers) or your actual username. Spaces are allowed, but try putting your name in quotes if it doesn’t work for whatever reason."),
        "examples":  (" - `setuser ill onion`: links this Discord account to ill onion.")
    },
    "unsetuser":{
        "signature": ("**unsetuser/forgetme/unset**"),
        "summary":   ("*Unlink an osu! username from your Discord account. You will need to explicitly provide your team name and osu! username for stat commands again.*"),
        "parameters":("*none*"),
        "examples":  (" - `unset`: does what it says on the label")
    },
    "whois":{
        "signature": ("**whois/userinfo/me** <user>"),
        "summary":   ("*Shows the osu! username and team associated with that Discord account.*"),
        "parameters":(" - *user (optional)*: ...\n"),
        "examples":  (" - `whois @poke_player`: returns the tournament data associated with poke_player’s Discord account, if set\n"
                      " - *whois*: returns the tournament data associated with your own Discord account, if available\n"
                      " - `whois ill onion`: returns an error (probably)")
    },
    "averagelbp":{
        "signature": ("**averageleaderboardp/averagelbp/avglbp** [leaderboard_category] [page]"),
        "summary":   ("*Shows the players with the highest averages in the given statistic. 10 per page.*"),
        "parameters":(" - *leaderboard_category (optional)*: Sort by any of “score”, “acc”, or “contrib” (descending). “score” by default.\n"
                      " - *page (optional)*: The page to return. 1 by default.\n"
                      "Parameters can be ordered however you want."),
        "examples":  (" - `avglbp`: returns the first page of the players with the highest average score\n"
                      " - `avglbp acc`: returns the first page of the players with the highest average accuracy\n"
                      " - `avglbp contrib 4`: returns the fourth page of the players with the highest average contribution percentage\n"
                      " - `avglbp 6`: returns the sixth page of the players with the highest average score")
    },
    "averagelbt":{
        "signature": ("**averageleaderboardt/averagelbt/avglbt** [leaderboard_category] [page]"),
        "summary":   ("*Shows the teams with the highest averages in the given statistic. 10 per page.*"),
        "parameters":(" - *leaderboard_category (optional)*: Sort by either “score” or “acc” (descending). “score” by default.\n"
                      " - *page (optional)*: The page to return. 1 by default.\n"
                      "Parameters can be ordered however you want."),
        "examples":  (" - `avglbt`: returns the first page of the teams with the highest average score\n"
                      " - `avglbt acc`: returns the first page of the teams with the highest average accuracy\n"
                      " - `avglbt score 4`: returns the fourth page of the teams with the highest average score\n"
                      " - `avglbt 6`: returns the sixth page of the teams with the highest average score")
    },
    "serverbest":{
        "signature": ("**serverbest/sb** [leaderboard_category] [page] [mod]"),
        "summary":   ("*Shows the best scores (of the entire tournament) in the given statistic, filtered by mod if defined. 10 per page.*"),
        "parameters":(" - *leaderboard_category (optional)*: Sort by any of “score”, “acc”, or “contrib” (descending). “score” by default.\n"
                      " - *page (optional)*: The page to return. 1 by default.\n"
                      " - *mod (optional)*: The mod to filter scores by, with valid mods “NM”, “HD”, “HR”, “DT”, and “FM”. All scores (regardless of mod) returned by default. Tiebreaker is considered FM.\n"
                      "Parameters can be ordered however you want."),
        "examples":  (" - `serverbest`: returns the first page of scores with the highest score made in the tournament so far\n"
                      " - `serverbest score 4`: returns the fourth page of scores with the highest score\n"
                      " - `serverbest acc`: returns the first page of scores with the highest accuracy\n"
                      " - `serverbest acc 1 dt`: returns the first page of scores with the highest accuracy and doubletime played")
    },
    "mapbest":{
        "signature": ("**mapbest/mb** <map_id> [page] [pool]"),
        "summary":   ("*Shows the best scores of the selected map, filtered by mod if defined. 10 per page.*"),
        "parameters":(" - *map_id*: Can either be shorthand pool notation (NM1, HR2, etc) or a beatmap ID (b/123456 - listed on main sheet).\n"
                      " - *page (optional)*: The page to return. 1 by default.\n"
                      " - *pool (optional)*: The pool (in shorthand notation - Ro32, GS, QF, SF, etc.) If no pool is given, then the most recently-released pool used in a match is used. Ignored if a beatmap ID is provided."),
        "examples":  (" - `mapbest NM1`: returns the first page of the highest scores for NM1 in the most recent pool used in a match.\n"
                      " - `mapbest 1734126 2`: returns the second page of the highest scores for [https://osu.ppy.sh/b/1734126](https://osu.ppy.sh/b/1734126) (in this tournament).")
    },
    "playerbest":{
        "signature": ("**playerbest/pb** [user] [page] [mod]"),
        "summary":   ("*Shows the best plays for that user, filtered by mod if defined. 10 per page.*"),
        "parameters":(" - *user (optional)*: osu! username or osu! ID of the player. If you have a username set through `setuser`, leaving this field blank will default to the username you set. Spaces in a username are permitted (you shouldn’t have to quote your username in most cases).\n"
                      " - *page (optional)*: The page to return. 1 by default.\n"
                      " - *mod (optional)*: The mod to filter scores by, with valid mods “NM”, “HD”, “HR”, “DT”, and “FM”. All scores (regardless of mod) returned by default. Tiebreaker is considered FM.\n"
                      "Parameters can be ordered however you want, so long as you put the player name (if needed) first. Try enclosing names in quotes if it breaks anyways or use their osu! ID."),
        "examples":  (" - `pb`: returns your top 10 scores for the tournament (or kindly guides you towards `setuser`)\n"
                      " - `pb 3 HD`: returns the third page of your best HD scores\n"
                      " - `pb Ayarilli HR 2`: returns the second page of Ayarilli’s best HR scores\n"
                      " - `pb windows 10 pro 8 fm`: returns the eighth page of windows 10 pro’s best FM scores")
    },
    "playerstats":{
        "signature": ("**playerstats/ps** [user]"),
        "summary":   ("*Post the stats of a user.*"),
        "parameters":(" - *user (optional)*: osu! username or osu! ID of the player. If you have a username set through `setuser`, leaving this field blank will default to the username you set. Spaces in a username are permitted (you shouldn’t have to quote your username in most cases)."),
        "examples":  (" - `ps`: returns your own player stats (if username set)\n"
                      " - `ps ill onion`: returns ill onion’s player stats")
    },
    "teambest":{
        "signature": ("**teambest/tb** [team] [page] [mod]"),
        "summary":   ("*Shows the best plays for that team, filtered by mod if defined. 10 per page.*"),
        "parameters":(" - *team (optional)*: Team name. If you have a username set through `setuser`, leaving this field blank will default to the team you are associated with. Spaces in a team name are permitted (you shouldn’t have to quote the team name or use exact capitalization).\n"
                      " - *page (optional)*: The page to return. 1 by default.\n"
                      " - *mod (optional)*: The mod to filter scores by, with valid mods “NM”, “HD”, “HR”, “DT”, and “FM”. All scores (regardless of mod) returned by default. Tiebreaker is considered FM.\n"
                      "Parameters can be ordered however you want, so long as you put the team name (if needed) first. Try enclosing names in quotes if it breaks anyways."),
        "examples":  (" - `tb`: returns your team’s top 10 scores for the tournament (or kindly guides you towards `setuser`)\n"
                      " - `tb 3 HD`: returns the third page of your team’s best HD scores\n"
                      " - `tb idk 2 HR 2`: returns the second page of idk 2’s best HR scores\n"
                      " - `tb genshin impact w 2`: returns the second page of genshin impact w’s best scores")
    },
    "teamstats":{
        "signature": ("**teamstats/ts** [user]"),
        "summary":   ("*Post the stats of a team.*"),
        "parameters":(" - *team (optional)*: Team name. If you have a username set through `setuser`, leaving this field blank will default to the team you are associated with. Spaces in a team name are permitted (you shouldn’t have to quote the team name or use exact capitalization)."),
        "examples":  (" - `ts`: returns your own team’s stats (if username set)\n"
                      " - `ts idk`: returns idk’s team stats")
    }
}