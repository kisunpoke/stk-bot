"""Async functions for interacting with the osu! api and prepping its data.

This uses the v1 endpoint because it is more stable. Use v2 when available or
necessary.
"""
import aiohttp
from enum import IntFlag

import db_manip

api_key = open("osukey").read()

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

async def get_player_data(username):
    #well that's kinda bad
    async with aiohttp.ClientSession() as session:
        player_request = await session.get(f'https://osu.ppy.sh/api/get_user?k={api_key}&u={username}')
        player_data = await player_request.json()
    #print(player_data)
    return player_data[0]

async def get_map_data(diff_id):
    async with aiohttp.ClientSession() as session:
        map_request = await session.get(f'https://osu.ppy.sh/api/get_beatmaps?k={api_key}&b={diff_id}')
        map_data = await map_request.json()
    '''
    thumbnail_url = f'https://b.ppy.sh/thumb/{map_data[0]["beatmapset_id"]}l.jpg'
    map_name = f'{map_data[0]["artist"]} - {map_data[0]["title"]}'
    data = {
        'map_url': map_url,
        'thumbnail_url': thumbnail_url,
        'map_name': map_name
    }
    return data
    '''
    return map_data[0]

async def get_match_data(match_id):
    async with aiohttp.ClientSession() as session:
        match_request = await session.get(f'https://osu.ppy.sh/api/get_match?k={api_key}&mp={match_id}')
        match_data = await match_request.json()
    return match_data

async def get_processed_match_data(match_id, map, ignore_threshold=1000, data=None, player_ids={}):
    #really this should be split up more...
    #intended for use with team vs
    #also has no clue if a player fails or not but since everything is NF it'll be ignored
    #also needs score threshhold to exclude refs (or abnormally low scores)
    """Returns a dict of match data tailored for stat calculation.
    
    `data` is expected to be the original JSON response, and is used in lieu of calling
    the osu! API - helpful if successive calls of this function for the same match occur. 
    Otherwise, `match_id` is used to get match data, then the nth `map` (zero-indexed) is 
    obtained and processed. If available, `player_ids` should be provided, a dict of `player_ids`
    (str) to `player_names` (str).

    This function aims to expose useful data not normally available from the get_match
    endpoint of the API.

    ```
    Returns the following dict:
    {
        "match_name": str,
        "match_url": f'https://osu.ppy.sh/community/matches/{match_id}',
        "diff_id": str,
        "diff_url": f'https://osu.ppy.sh/b/{diff_id}',
        "map_thumbnail": f'https://b.ppy.sh/thumb/{diff_id}l.jpg',
        "map_name": f'{artist} - {title}',
        "winner": str, #(1 or 2)
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
        match_data = await get_match_data(match_id)
    game_data = match_data["games"][int(map)]
    map_data = await get_map_data(game_data["beatmap_id"])
    #now we'll start number crunching and stuff
    
    #if head-to-head or tag co-op is selected
    if game_data['team_type'] in ('0', '1'):
        #currently unsupported!
        pass

    #if a team mode is selected
    if game_data['team_type'] in ('2', '3'):
        #determine who belongs in what team
        #as of now this is only used to get the number of players on a team, since we use
        #a conditional to add teams to the correct field anyways
        team_1_players = []
        team_2_players = []
        for index, player_score in enumerate(game_data['scores']):
            #player_ids[player_score["user_id"]] = ""
            if player_score["team"] == "1":
                team_1_players.append(player_score["user_id"])
            if player_score["team"] == "2":
                team_2_players.append(player_score["user_id"])
        #determine team scores
        team_1_score = 0
        team_2_score = 0
        for player_score in game_data["scores"]:
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

        #generate the individual lines that will be in the discord embed
        individual_scores = []
        for player_score in game_data["scores"]:
            #ignore if below minimum score threshold
            if int(player_score["score"]) < ignore_threshold:
                continue
            count_300 = int(player_score["count300"])
            count_100 = int(player_score["count100"])
            count_50 = int(player_score["count50"])
            count_miss = int(player_score["countmiss"])
            acc_count = count_300 + count_100 + count_50 + count_miss
            acc_value = (count_300+(count_100/3)+(count_50/6))/acc_count
            score = int(player_score["score"])
            contrib = score/team_1_score if player_score["team"] == "1" else score/team_2_score
            
            #if we don't currently know what the name of a certain player id is, look it up against the mongodb and osuapi, in that order
            #might fail if the player is restricted, not sure on that
            if not player_ids[player_score["user_id"]]:
                player_document = await (db_manip.getval("id", player_score["user_id"], "players_and_teams", "players"))
                if player_document == None:
                    #this means that we don't have this player saved for some reason
                    #so we'll go the alternative route, getting the username manually
                    #this'll probably happen if somebody tries to get a non-tournament mp
                    player_data = await get_player_data(player_score["user_id"])
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
        team_vs_final = {
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
        return team_vs_final