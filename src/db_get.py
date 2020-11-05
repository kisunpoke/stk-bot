"""Functions exclusively for getting and manipulating db documents (not adding/changing)."""

import motor.motor_asyncio
import pprint
import collections
import math

import osuapi
import db_manip

db_url = open("dburl").read()

client = motor.motor_asyncio.AsyncIOMotorClient(db_url)

async def determine_pool(map_id):
    """Figure out what pool this `map_id` belongs in.
    
    Returns shorthand pool notation, equivalent to the collection name in 
    the `mappools` database. Returns `None` on fail."""
    db = client["mappools"]
    collection = db["meta"]
    cursor = collection.find()
    #well i'd hope we never end up with 100 pools
    for meta_document in await cursor.to_list(length=100):
        if map_id in meta_document["diff_ids"]:
            return meta_document["_id"]
    return None

async def get_meta_document():
    """Gets the tournament-wide meta document.
    
    If the meta document does not exist, returns None."""
    db = client["tournament_data"]
    meta_collection = db["meta"]
    return await meta_collection.find_one({'_id': "main"})


async def get_user_document(discord_id):
    """Get the DiscordUser document associated with a Discord ID.
    
    If this fails, generates a new DiscordUser document and returns
    the newly-created (though empty) document. (This guarantees a document
    is always returned.)"""
    db = client['discord_users']
    discord_user_collection = db['discord_users']
    user_document = await discord_user_collection.find_one({'_id': discord_id})
    if not user_document:
        await db_manip.create_discord_user(discord_id)
        user_document = await discord_user_collection.find_one({'_id': discord_id})
    return user_document

async def get_player_document(player):
    """Get the player document associated with `player`.
    
    This will assume user ID (field _id) and then username, in that order.
    If both fail, returns `None`."""
    db = client['players_and_teams']
    player_collection = db['players']
    player_document = await player_collection.find_one({'_id': player})
    if not player_document:
        #mongodb queries are case-sensitive
        #i think it is marginally faster for a collection of this size to simply cache
        #lowercase usernames than it is to perform regex and force a lowercase result
        player_document_2 = await player_collection.find_one({'user_lower': player.lower()})
        if not player_document_2:
            return None
        else:
            return player_document_2
    else:
        return player_document

async def get_name_from_user(discord_id, *, return_player):
    """Get the osu! ID or team associated with `discord_id`.
    
    If `return_player` is True, returns the osu! ID. Otherwise, returns
    the team name (same as _id of associated Team document).
    If no osu! ID is associated, returns `None`."""
    user_doc = await get_user_document(discord_id)
    if not user_doc["osu_id"]:
        return None
    else:
        if return_player:
            return user_doc["osu_id"]
        else:
            return user_doc["team_name"]

async def get_team_document(team):
    """Get the team document associated with `team_name`.
    
    `team_name` should be an exact match of an _id in the teams collection.
    However, `name_lower` is the actual field queried.
    If a document cannot be found, `None` is returned."""
    db = client['players_and_teams']
    team_collection = db['teams']
    return await team_collection.find_one({'name_lower': team.lower()})

async def get_map_document(id, pool=None):
    """Get the document associated with `id`.
    
    If `pool=None`, then `id` is treated as a beatmap ID first.
    If conversion to `int` fails (i.e. letters have been passed)
    or a database loookup fails, `id` is treated as shorthand notation
    `<mod><id>`, as in "NM1" or "HR2". The pool currently set as active in
    the Meta document will be used. If this fails, `None` is returned.
    
    `pool` should be equivalent to a collection name (F/GF/GS/QF...)."""
    db = client['mappools']
    try:
        int(id)
        #id is only numbers, and is probably a /b id
        if not pool:
            pool = await determine_pool(id)
        pool_collection = db[pool]
        return await pool_collection.find_one({'_id': id})
    except:
        #id is in mod-index format, like NM1 or TB1
        if not pool:
            meta_doc = await get_meta_document()
            pool = meta_doc['active_pool']
        pool_collection = db[pool]
        return await pool_collection.find_one({'pool_id': id.upper()})

async def get_match_document(match_id):
    """Get the match document associated with `match_id`.
    
    `match_id` must be an exact match of an _id in the matches collection.
    Lobby names are not acceptable. If the match cannot be found, `None` is returned."""
    #lobby names aren't acceptable because we don't store them lol
    db = client['matches_and_scores']
    matches_collection = db['matches']
    return await matches_collection.find_one({'_id': match_id})

#redundant yes but it made more sense to me    
async def get_top_player_scores(player_id, page=1, mod=None):
    """Get the top n scores (as documents) of a player, filtered by mod if defined, and the max page.
    
    Returns the tuple `([<documents>], max_page)`.
    
    Parameters:
    - `player_id` can be either a username or a user ID and will be passed to
    `get_player_document()`. User ID is preferred.
    - `page` determines the top scores to be returned. Pagination is done on a 10 score
    per page basis; if `page*10` exceeds the total number of scores of the player plus 10,
    then the last reasonable page is used instead. For example, a player with 22 scores has
    pages of 1-10, 11-20, and 21-22. Page 4 will redirect to 21-22. Values less than 1 redirect
    to page 1. Starts at 1; is *not* zero-indexed.
    - `mod` is the mod, in shorthand notation (NM/HR/...) to filter scores with. Shorthand pool 
    prefixes are used, with valid mods in the array `["NM", "HR", "HD", "DT", "FM"]`.
    
    Note this function does no additional work towards generating a Discord embed. If the player
    is not found, this function returns `(None, None)`. If no scores are found but the player exists, 
    `([], 0)` is returned."""
    db = client['players_and_teams']
    player_collection = db['players']
    player_document = await get_player_document(player_id)
    if player_document is None:
        return (None, None)
    scores = player_document["scores"]
    
    #the number of scores depends on what scores were requested
    mod_mapping = {
        None: player_document["cached"]["maps_played"],
        "NM": player_document["cached"]["by_mod"]["NM"]["maps_played"],
        "HD": player_document["cached"]["by_mod"]["HD"]["maps_played"],
        "HR": player_document["cached"]["by_mod"]["HR"]["maps_played"],
        "DT": player_document["cached"]["by_mod"]["DT"]["maps_played"],
        "FM": player_document["cached"]["by_mod"]["FM"]["maps_played"],
    }

    max_page = math.ceil(mod_mapping[mod]/10)
    if page < 0:
        page = 1
    if page > max_page:
        #24 scores -> 2.4 -> 3 pages; 40 scores -> 4 -> 4 pages, etc
        page = max_page
    #i am not actually sure if querying based on the list of scores or simply
    #doing a full query is faster
    score_collection = client['matches_and_scores']['scores']
    if not mod:
        cursor = score_collection.find({'_id': {'$in': scores}}).sort("score", -1).skip((page-1)*10).limit(10)
    else:
        cursor = score_collection.find({'_id': {'$in': scores}, 'map_type': mod}).sort("score", -1).skip((page-1)*10).limit(10)
    return (await cursor.to_list(length=10), max_page)

async def get_top_team_scores(team_name, page=1, mod=None):
    """Get the top n scores (as documents) of a team, filtered by mod if defined, and the max page.
    
    Returns the tuple `([<documents>], max_page)`.
    
    Parameters:
    - `team_name` must be an exact match of the team name.
    - `page` determines the top scores to be returned. Pagination is done on a 10 score
    per page basis; if `page*10` exceeds the total number of scores of the player plus 10,
    then the last reasonable page is used instead. For example, a player with 22 scores has
    pages of 1-10, 11-20, and 21-22. Page 4 will redirect to 21-22.
    - `mod` is the mod, in shorthand notation (NM/HR/...) to filter scores with. Shorthand pool 
    prefixes are used, with valid mods in the array `["NM", "HR", "HD", "DT", "FM"]`.
    
    Note this function does no additional work towards generating a Discord embed. If the player
    is not found, this function returns `(None, None)`. If no scores are found but the player exists, 
    `([], 0)` is returned."""
    db = client['players_and_teams']
    team_collection = db['teams']
    team_document = await get_team_document(team_name)
    if team_document is None:
        return (None, None)
    scores = team_document["scores"]

    #the number of scores depends on what scores were requested
    mod_mapping = {
        None: team_document["cached"]["maps_played"],
        "NM": team_document["cached"]["by_mod"]["NM"]["maps_played"],
        "HD": team_document["cached"]["by_mod"]["HD"]["maps_played"],
        "HR": team_document["cached"]["by_mod"]["HR"]["maps_played"],
        "DT": team_document["cached"]["by_mod"]["DT"]["maps_played"],
        "FM": team_document["cached"]["by_mod"]["FM"]["maps_played"],
    }

    max_page = math.ceil(mod_mapping[mod]/10)
    if page < 0:
        page = 1
    if page > max_page:
        #24 scores -> 2.4 -> 3 pages; 40 scores -> 4 -> 4 pages, etc
        page = max_page
    #i am not actually sure if querying based on the list of scores or simply
    #doing a full query is faster
    score_collection = client['matches_and_scores']['scores']
    if not mod:
        cursor = score_collection.find({'_id': {'$in': scores}}).sort("score", -1).skip((page-1)*10).limit(10)
    else:
        cursor = score_collection.find({'_id': {'$in': scores}, 'map_type': mod}).sort("score", -1).skip((page-1)*10).limit(10)
    return (await cursor.to_list(length=10), max_page)

async def get_top_map_scores(map_id, page=1, pool=None):
    """Get the top n scores (as documents) of a map.
    
    - `map_id` can be either the shorthand name of the map in the pool ("NM1") or the full diff ID.
    - `page` determines the top scores to be returned. Pagination is done on a 10 score
    per page basis; if `page*10` exceeds the total number of scores of the player plus 10,
    then the last reasonable page is used instead. For example, a player with 22 scores has
    pages of 1-10, 11-20, and 21-22. Page 4 will redirect to 21-22.
    - `pool` is the shorthand pool name. If not defined, `map_id` must be a diff id resolvable with
    `determine_pool()`.
    
    Note this function does no additional work towards generating a Discord embed. If the player
    is not found, this function returns `(None, None)`. If no scores are found but the player exists, 
    `([], 0)` is returned."""
    map_document = await get_map_document(map_id)
    if not map_document:
        return (None, None)
    scores = map_document["scores"]

    max_page = math.ceil(len(scores)/10)
    if page < 0:
        page = 1
    if page > max_page:
        page = max_page

    score_collection = client['matches_and_scores']['scores']
    cursor = score_collection.find({'_id': {'$in': scores}}).sort("score", -1).skip((page-1)*10).limit(10)
    return (await cursor.to_list(length=10), max_page)

async def get_top_tournament_players(leaderboard_field="score", page=1):
    """Get the best players (as documents) in a certain average category.
    
    Returns the tuple (<players>, max_pages).
    - `leaderboard` is any of `"acc"`, `"score"`, or `"contrib"`. `"score"` by default.
    - `page` determines the top scores to be returned. Pagination is done on a 10 score
    per page basis; if `page*10` exceeds the total number of scores of the player plus 10,
    then the last reasonable page is used instead. For example, a player with 22 scores has
    pages of 1-10, 11-20, and 21-22. Page 4 will redirect to 21-22.
    
    Note this function does no additional work towards generating a Discord embed.
    If no players are found, `([], 0)` is returned."""
    db = client['players_and_teams']
    player_collection = db['players']

    player_count = await player_collection.estimated_document_count()

    max_page = math.ceil(player_count/10)
    if page < 0:
        page = 1
    if page > max_page:
        page = max_page

    fields = {
        "score": "cached.average_score",
        "acc": "cached.average_acc",
        "contrib": "cached.average_contrib"
    }

    cursor = player_collection.find().sort(fields[leaderboard_field], -1).skip((page-1)*10).limit(10)
    return (await cursor.to_list(length=10), max_page)

async def get_top_tournament_teams(leaderboard_field="score", page=1):
    """Get the best teams (as documents) in a certain average category.
    
    Returns the tuple (<teams>, max_pages).
    - `leaderboard` is either `"acc"` or `"score"`. `"score"` by default.
    - `page` determines the top scores to be returned. Pagination is done on a 10 score
    per page basis; if `page*10` exceeds the total number of scores of the player plus 10,
    then the last reasonable page is used instead. For example, a player with 22 scores has
    pages of 1-10, 11-20, and 21-22. Page 4 will redirect to 21-22.
    
    Note this function does no additional work towards generating a Discord embed.
    If no teams are found, `([], 0)` is returned."""
    db = client['players_and_teams']
    team_collection = db['teams']

    team_count = await team_collection.estimated_document_count()

    max_page = math.ceil(team_count/10)
    if page < 0:
        page = 1
    if page > max_page:
        page = max_page

    fields = {
        "score": "cached.average_score",
        "acc": "cached.average_acc",
    }
    #if leaderboard_field not in fields return None ?

    cursor = team_collection.find().sort(fields[leaderboard_field], -1).skip((page-1)*10).limit(10)
    return (await cursor.to_list(length=10), max_page)

async def get_top_tournament_scores(leaderboard_field="score", page=1, mod=None):
    """Get the best scores (as documents) in a certain category.
    
    Returns the tuple (<scores>, max_pages).
    - `leaderboard` is any of `"acc"`, `"score"`, or `"contrib"`.
    - `page` determines the top scores to be returned. Pagination is done on a 10 score
    per page basis; if `page*10` exceeds the total number of scores of the player plus 10,
    then the last reasonable page is used instead. For example, a player with 22 scores has
    pages of 1-10, 11-20, and 21-22. Page 4 will redirect to 21-22.
    - `mod` is the mod, in shorthand notation (NM/HR/...) to filter scores with. Shorthand pool 
    prefixes are used, with valid mods in the array `["NM", "HR", "HD", "DT", "FM"]`.
    
    Note this function does no additional work towards generating a Discord embed. If the player
    is not found, this function returns `(None, None)`. If no scores are found, 
    `([], 0)` is returned."""
    pass