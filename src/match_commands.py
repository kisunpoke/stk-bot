"""Match-related commands/cogs."""

import discord
from discord.ext import commands
import osuapi
import db_manip
from enum import IntFlag
import pprint

class Mods(IntFlag):
    "Enum of the osu! mods exposed by the API."
    NM = 0,
    NF = 1,
    EZ = 2,
    TD = 4,
    HD = 8,
    HR = 16,
    SD = 32,
    DT = 64,
    RX = 128,
    HT = 256,
    NC = 512,
    FL = 1024,
    AT = 2048,
    SO = 4096,
    AP = 8192,
    PF = 16384,
    _4K = 32768,
    _5K = 65536,
    _6K = 131072,
    _7K = 262144,
    _8K = 524288,
    FI = 1048576,
    RD = 2097152,
    CN = 4194304,
    TP = 8388608,
    _9K = 16777216,
    CO = 33554432,
    _1K = 67108864,
    _3K = 134217728,
    _2K = 268435456,
    V2 = 536870912,
    MR = 1073741824

    def to_list(self):
        """Returns a list of strings represented by this enumeration."""
        mod_list = str(self).split("|")
        mod_list[0] = mod_list[0].split("Mods.")[1]
        return mod_list

async def get_individual_match_data(match_id, map, data=None, player_ids=None):
    #really this should be split up more...
    #intended for use with team vs
    #also has no clue if a player fails or not but since everything is NF it'll be ignored
    #also needs score threshhold to exclude refs (or abnormally low scores)
    """Returns a dict of match data tailored for stat calculation.
    
    `data` is expected to be the original JSON response, and is used in lieu of 
    calling the osu! API. Otherwise, `match_id` is used to get match data, then the nth
    `map` (zero-indexed) is obtained and processed.

    This function aims to expose useful data not normally available from the get_match
    endpoint of the API.
    **player_ids is not yet fully implemented!!**

    ```
    Returns the following dict:
    {
        "match_name": str,
        "match_url": f'https://osu.ppy.sh/community/matches/{match_id}',
        "diff_id": str,
        "diff_url": f'https://osu.ppy.sh/b/{diff_id}',
        "map_thumbnail": f'https://b.ppy.sh/thumb/{diff_id}l.jpg',
        "map_name": f'{artist} - {title}',
        "winner": str (1 or 2),
        "score_difference": float,
        "team_1_score": int,
        "team_2_score": int, 
        "team_1_score_avg": float,
        "team_2_score_avg": float,
        "individual_scores": [
            {
                "user_id": str,
                "user_name": str,
                "score": int,
                "combo": int,
                "accuracy": float,
                "mod_val": int,
                "mods": [str, str, ...],
                "hits": {
                    "300_count": int,
                    "100_count": int,
                    "50_count": int,
                    "miss_count": int
                },
                "team_contrib": float
                "team": str
            }, ...
        ]
        "start_time": str,
        "scoring_type": str,
        "team_type": str,
        "play_mode": str
    }
    ```
    """
    match_data = data
    if not match_data:
        match_data = await osuapi.get_match_data(match_id)
    game_data = match_data["games"][int(map)]
    map_data = await osuapi.get_map_data(game_data["beatmap_id"])
    #now we'll start number crunching and stuff
    
    #determine who belongs in what team, assuming a team mode is selected
    if game_data['team_type'] in ('2', '3'):
        #does this dict even do anything
        player_ids = {}
        team_1_players = []
        team_2_players = []
        for index, player_score in enumerate(game_data['scores']):
            player_ids[player_score["user_id"]] = ""
            if player_score["team"] == "1":
                team_1_players.append(player_score["user_id"])
            if player_score["team"] == "2":
                team_2_players.append(player_score["user_id"])
        #determine team scores
        team_1_score = 0
        team_2_score = 0
        for player_score in game_data["scores"]:
            #i actually spent a solid hour wondering why this wasn't working cuz i used 1 instead of "1"
            if player_score["team"] == "1":
                #print(f'Adding {int(player_score["score"])} to team 1\'s score {team_1_score}')
                team_1_score += int(player_score["score"])
            else:
                #print(f'Adding {int(player_score["score"])} to team 2\'s score {team_2_score}')
                team_2_score += int(player_score["score"])
        #print(f'Team 1 score is {team_1_score}')
        #who won
        if team_1_score != team_2_score:
            winner = "Blue" if team_1_score > team_2_score else "Red"
        else:
            winner = "Tie"
        #score diff
        score_diff = abs(team_1_score-team_2_score)

        individual_scores = []
        for player_score in game_data["scores"]:
            count_300 = int(player_score["count300"])
            count_100 = int(player_score["count100"])
            count_50 = int(player_score["count50"])
            count_miss = int(player_score["countmiss"])
            acc_count = count_300 + count_100 + count_50 + count_miss
            acc_value = (count_300+(count_100/3)+(count_50/6))/acc_count
            score = int(player_score["score"])
            contrib = score/team_1_score if player_score["team"] == "1" else score/team_2_score
            #so it occurred to me the logic here is flawed
            #there should be a player_id dict passed, None by default
            #but will fix later
            if not player_ids[player_score["user_id"]]:
                player_document = await (db_manip.getval("id", player_score["user_id"], "players_and_teams", "players"))
                if player_document == None:
                    #this means that we don't have this player saved for some reason
                    #so we'll go the alternative route, getting the username manually
                    #this'll probably happen if somebody tries to get a non-tournament mp
                    player_data = await osuapi.get_player_data(player_score["user_id"])
                    player_name = player_data["username"]
                else:
                    player_name = player_document["user_name"]
                player_ids[player_score["user_id"]] = player_name
            individual_score = {
                "user_id": player_score["user_id"],
                "user_name": player_name,
                "score": score,
                "combo": int(player_score["maxcombo"]),
                "accuracy": acc_value,
                "mod_val": int(game_data["mods"]),
                "mods": Mods(int(game_data["mods"])).to_list(),
                "hits": {
                    "300_count": count_300,
                    "100_count": count_100,
                    "50_count": count_50,
                    "miss_count": count_miss
                },
                "team_contrib": contrib,
                "team": player_score["team"]
            }
            individual_scores.append(individual_score)
    final = {
        "match_name": match_data["match"]["name"],
        "match_url": f'https://osu.ppy.sh/community/matches/{match_id}',
        "diff_id": game_data["beatmap_id"],
        "diff_url": f'https://osu.ppy.sh/b/{game_data["beatmap_id"]}',
        "map_thumbnail": f'https://b.ppy.sh/thumb/{map_data["beatmapset_id"]}l.jpg',
        "map_name": f'{map_data["artist"]} - {map_data["title"]} [{map_data["version"]}]',
        "winner": winner,
        "score_difference": score_diff,
        "team_1_score": team_1_score,
        "team_2_score": team_2_score, 
        "team_1_score_avg": round(team_1_score/len(team_1_players),2),
        "team_2_score_avg": round(team_2_score/len(team_2_players),2),
        "individual_scores": individual_scores,
        "start_time": game_data["start_time"],
        "scoring_type": game_data["scoring_type"],
        "team_type": game_data["team_type"],
        "play_mode": game_data["play_mode"]
    }
    return final

async def make_getmatch_embed(data):
    """Generate the embed description and other components for a getmatch() command.
    
    As with its parent, remember that this currently does not support non team-vs.
    `data` is expected to be the output of `get_individual_match_data()`.
    The following `dict` is returned:
    ```
    {
        "embed_description": str,
        "footer": str,
        "embed_color": int (as color hex),
    }
    ```
    """
    scores = data["individual_scores"]
    team_1_score_strings = []
    team_2_score_strings = []

    for individual_score in scores:
        #at first i thought doing this would make the actual score_string more readable
        #now i'm not very sure
        player_name = individual_score["user_name"]
        score_val = individual_score["score"]
        maxcombo = individual_score["combo"]
        accuracy = individual_score["accuracy"]
        count_300 = individual_score["hits"]["300_count"]
        count_100 = individual_score["hits"]["100_count"]
        count_50 = individual_score["hits"]["50_count"]
        count_miss = individual_score["hits"]["miss_count"]
        accuracy = '{:.2%}'.format(accuracy)
        score_val = "{:,}".format(score_val)
        maxcombo = "{:,}".format(maxcombo)
        score_string = (f'**{player_name}** - {score_val} ({maxcombo}x) ({accuracy} - {count_300}/{count_100}/{count_50}/{count_miss})')
        team_1_score_strings.append(score_string) if individual_score["team"] == "1" else team_2_score_strings.append(score_string)

    team_1_score_string = "\n".join(team_1_score_strings)
    team_2_score_string = "\n".join(team_2_score_strings)
    
    winner_string = {
        "Blue": f"Blue team wins by {'{:,}'.format(data['score_difference'])}!",
        "Red": f"Red team wins by {'{:,}'.format(data['score_difference'])}!",
        "Tie": "Tie!"}
    winner_color = {
        "Blue": 0x0000FF,
        "Red": 0xFF0000,
        "Tie": 0x808080}
    embed_desc = (
        f'**{winner_string[data["winner"]]}**\n\n'
        f'__Blue Team__ ({"{:,}".format(data["team_1_score"])} points, {"{:,}".format(data["team_1_score_avg"])} average)\n'
        f'{team_1_score_string}\n\n'
        f'__Red Team__ ({"{:,}".format(data["team_2_score"])} points, {"{:,}".format(data["team_2_score_avg"])} average)\n'
        f'{team_2_score_string}')

    #footer stuff
    scoring_types = {
        '0': 'Score',
        '1': 'Accuracy',
        '2': 'Combo',
        '3': 'Score v2'}
    team_types = {
        '0': 'Head-to-head',
        '1': 'Tag Co-op',
        '2': 'Team VS',
        '3': 'Tag Team VS'}
    play_modes = {
        '0': 'osu!',
        '1': 'Taiko',
        '2': 'CTB',
        '3': 'osu!mania'}
    embed_footer = (f'Played at {data["start_time"]} UTC | '
                f'Win condition: {scoring_types[data["scoring_type"]]} | '
                f'{team_types[data["team_type"]]} | '
                f'{play_modes[data["play_mode"]]}')

    final = {
        "embed_description": embed_desc,
        "footer": embed_footer,
        "embed_color": winner_color[data["winner"]],
    }
    return final

async def get_list_of_matches(match_id):
    """Returns a newline, numbered list of the first 20 matches played in a lobby."""
    pass

async def process_match(match_id):
    pass

class MatchCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def getmatch(self, ctx, match, map=None):
        """Get score and statistics data for a match."""
        #need to check against mongodb if match has already been played
        if map is not None:
            data = await get_individual_match_data(match, map)
            embed_data = await make_getmatch_embed(data)
            em_msg = discord.Embed(description=embed_data["embed_description"],
                                color=embed_data["embed_color"],
                                url=data["diff_url"],
                                title=data["map_name"])
            em_msg.set_thumbnail(url=data["map_thumbnail"])
            em_msg.set_footer(text=embed_data["footer"])
            em_msg.set_author(name=data["match_name"],url=data["match_url"])
            await ctx.send(embed=em_msg)
        elif map == "list":
            #show the first 20 maps played
            pass
        else:
            #show some match stats
            '''
            STK7: (Plastic Assimilation) vs. (Cherry Gum)
            Blue Team | 4 - 5 | Red Team

            **Match Statistics**    
            Stat                      Blue Team        Red Team
            Avg. Score
            Avg. Accuracy
            Avg. Score Difference

            **Individual Statistics**
            __Blue Team__
            **Player** - 123,445 avg pts | 100.00% avg acc | 100.00% avg contrib
            **Player** - 123,445 avg pts | 100.00% avg acc | 100.00% avg contrib

            __Red Team__
            **Player** - 123,445 avg pts | 100.00% avg acc | 100.00% avg contrib
            **Player** - 123,445 avg pts | 100.00% avg acc | 100.00% avg contrib

            footer:
            Use `getmatch <mp_id> list` for a list of maps played or `getmatch <mp_id> <index>` for
            individual map data!

            '''
            pass

    @commands.command()
    async def trackmatch(self, ctx, match, map=1):
        """Start tracking a match, returning embeds similar to `getmatch()`."""
        pass

    @commands.command()
    async def addmatch(self, ctx, match):
        """Add this match to the database and update all relevant data.

        This includes calls to update player and mappool data.
        """
        pass

    @commands.command()
    async def deletematch(self, ctx, match):
        """Delete this match from the database and update the involved players' data."""
        pass