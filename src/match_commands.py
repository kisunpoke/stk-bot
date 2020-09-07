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

async def get_individual_match_data(match_id, map, data=None):
    #really this should be split up more...
    #intended for use with team vs
    #also has no clue if a player fails or not
    """Returns a dict of match data tailored for generating match embeds for `getmatch()`.
    
    `data` is expected to be the original JSON response, and is used in lieu of 
    calling the osu! API. Otherwise, `match_id` is used to get match data, then the nth
    `map` (zero-indexed) is obtained and statcrunched.
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
        "embed_description": str (very, very long),
        "footer": str,
        "embed_color": hex (0x......)
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
            }, ...
        ]
    }
    ```
    """
    match_data = data
    if not match_data:
        match_data = await osuapi.get_match_data(match_id)
    game_data = match_data["games"][map]
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

        team_1_score_strings = []
        team_2_score_strings = []

        individual_scores = []
        for player_score in game_data["scores"]:
            count_300 = int(player_score["count300"])
            count_100 = int(player_score["count100"])
            count_50 = int(player_score["count50"])
            count_miss = int(player_score["countmiss"])
            acc_count = count_300 + count_100 + count_50 + count_miss
            acc_value = (count_300+(count_100/3)+(count_50/6))/acc_count
            accuracy = '{:.2%}'.format(acc_value)
            score_val = "{:,}".format(int(player_score["score"]))
            maxcombo = "{:,}".format(int(player_score["maxcombo"]))
            #so it occurred to me the logic here is flawed
            #there should be a player_id dict passed, None by default
            #but will fix later
            if not player_ids[player_score["user_id"]]:
                player_document = await (db_manip.getval("id", player_score["user_id"], "players_and_teams", "players"))
                if player_document == None:
                    #this means that we don't have this player saved for some reason
                    #so we'll go the alternative route, getting the username manually
                    player_data = await osuapi.get_player_data(player_score["user_id"])
                    player_name = player_data["username"]
                else:
                    player_name = player_document["user_name"]
                player_ids[player_score["user_id"]] = player_name
            if player_score["team"] == "1":
                contrib = int(player_score["score"])/team_1_score
                team_1_score_strings.append(f'**{player_name}** - {score_val} ({maxcombo}x) ({accuracy} - {count_300}/{count_100}/{count_50}/{count_miss})')
            elif player_score["team"] == "2":
                contrib = int(player_score["score"])/team_2_score
                team_2_score_strings.append((f'**{player_name}** - {score_val} ({maxcombo}x) ({accuracy} - {count_300}/{count_100}/{count_50}/{count_miss})'))
            individual_score = {
                "user_id": player_score["user_id"],
                "user_name": player_name,
                "score": player_score["score"],
                "combo": player_score["maxcombo"],
                "accuracy": acc_value,
                "mod_val": int(game_data["mods"]),
                "mods": Mods(int(game_data["mods"])).to_list(),
                "hits": {
                    "300_count": count_300,
                    "100_count": count_100,
                    "50_count": count_50,
                    "miss_count": count_miss
                },
                "team_contrib": contrib
            }
        team_1_score_string = "\n".join(team_1_score_strings)
        team_2_score_string = "\n".join(team_2_score_strings)
        
        winner_string = {
            "Blue": f"Blue team wins by {score_diff}!",
            "Red": f"Red team wins by {score_diff}!",
            "Tie": "Tie!"
        }
        winner_color = {
            "Blue": 0x0000FF,
            "Red": 0xFF0000,
            "Tie": 0x808080
        }
        embed_desc = (
            f'**{winner_string}**\n\n'
            f'__Blue Team__ ({team_1_score} points, {round(team_1_score/len(team_1_players),2)} average)'
            f'{team_1_score_string}\n\n'
            f'__Red Team__ ({team_2_score} points, {round(team_2_score/len(team_2_players),2)} average)'
            f'{team_2_score_string}'
        )
    else:
        #wheeze
        raise ValueError("You are trying to process a non team-vs match; this isn't currently supported.")

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
    embed_footer = (f'Played at {game_data["start_time"]} UTC | '
              f'Win condition: {scoring_types[game_data["scoring_type"]]} | '
              f'{team_types[game_data["team_type"]]} | '
              f'{play_modes[game_data["play_mode"]]}')

    final = {
        "match_name": match_data["match"]["match_id"],
        "match_url": f'https://osu.ppy.sh/community/matches/{match_id}',
        "diff_id": game_data["beatmap_id"],
        "diff_url": f'https://osu.ppy.sh/b/{game_data["beatmap_id"]}',
        "map_thumbnail": f'https://b.ppy.sh/thumb/{game_data["beatmap_id"]}l.jpg',
        "map_name": f'{map_data["artist"]} - {map_data["title"]} [{map_data["version"]}]',
        "winner": winner,
        "score_difference": score_diff,
        "team_1_score": team_1_score,
        "team_2_score": team_2_score, 
        "team_1_score_avg": round(team_1_score/len(team_1_players),2),
        "team_2_score_avg": round(team_2_score/len(team_2_players),2),
        "winner_color": winner_color[winner],
        "embed_description": embed_desc,
        "footer": embed_footer,
        "individual_scores": individual_scores
    }
    return final

async def get_list_of_matches(match_id):
    """Returns a newline, numbered list of the first 20 matches played in a lobby."""
    pass

class MatchCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def getmatch(self, ctx, match, map=1):
        """Get score and statistics data for the nth map of a match."""
        data = await get_individual_match_data(match, map)
        pprint.pprint(data)
        await ctx.send("done...")

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