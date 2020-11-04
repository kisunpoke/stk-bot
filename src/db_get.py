"""Functions exclusively for getting and manipulating db documents (not adding/changing)."""

import motor.motor_asyncio
import pprint
import collections

import osuapi

db_url = open("dburl").read()

client = motor.motor_asyncio.AsyncIOMotorClient(db_url)

async def determine_pool(map_id):
    """Figure out what pool this `map_id` belongs in.
    
    Returns shorthand pool notation, equivalent to the collection name in 
    the `mappools` database."""
    db = client["mappools"]
    collection = db["meta"]
    cursor = collection.find()
    #well i'd hope we never end up with 100 pools
    for meta_document in await cursor.to_list(length=100):
        if map_id in meta_document["diff_ids"]:
            return meta_document["_id"]
    return None

async def get_user_document(discord_id):
    """Get the DiscordUser document associated with a Discord ID.
    
    If this fails, returns `None`."""
    db = client['discord_users']
    discord_user_collection = db['discord_users']
    return await discord_user_collection.find_one({'_id': discord_id})

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

async def get_map_document(id, pool=None):
    """Get the document associated with `id`.
    
    If `pool=None`, then `id` is treated as a beatmap ID first.
    If conversion to `int` fails (i.e. letters have been passed)
    or a database loookup fails, `id` is treated as shorthand notation
    `<mod><id>`, as in "NM1" or "HR2". The pool currently set as active in
    the Meta document will be used. If this fails, `None` is returned."""
    pass

async def get_team_document(team_name):
    """Get the team document associated with `team_name`.
    
    `team_name` must be an exact match of an _id in the teams collection.
    If a document cannot be found, `None` is returned."""
    pass

async def get_match_document(match_id):
    """Get the match document associated with `match_id`.
    
    `match_id` must be an exact match of an _id in the matches collection.
    Lobby names are not acceptable. If `int(match_id)` returns an error or
    the match cannot be found, `None` is returned."""
    pass

async def get_top_player_scores(player_id, page=1, mod=None):
    """Get the top n scores (as documents) of a player, filtered by mod if defined.
    
    The 

    - `player_id` can be either a username or a user ID and will be passed to
    `get_player_document()`. User ID is preferred.
    - `page` determines the top scores to be returned. Pagination is done on a 10 score
    per page basis; if `page*10` exceeds the total number of scores of the player plus 10,
    then the last reasonable page is used instead. For example, a player with 22 scores has
    pages of 1-10, 11-20, and 21-22. Page 4 will redirect to 21-22. Values less than 1 redirect
    to page 1.
    - `mod` is the mod, in shorthand notation (NM/HR/...) to filter scores with. If `use_mod_array`
    is `True`, then all shorthand names in the Mods enum at osuapi.py are valid. Otherwise,
    the shorthand pool prefixes are used, with valid mods likely including `["NM", "HR", "HD", "DT", 
    and "FM"]`.
    
    Note this function does no additional work towards generating a Discord embed. If the player
    is not found or has no valid scores, this function returns `None`."""
    pass

async def get_top_team_scores(team_name, page=1, mod=None, use_mod_array=False):
    """Get the top n scores (as documents) of a team, filtered by mod if defined.
    
    - `team_name` must be an exact match of the team name.
    - `page` determines the top scores to be returned. Pagination is done on a 10 score
    per page basis; if `page*10` exceeds the total number of scores of the player plus 10,
    then the last reasonable page is used instead. For example, a player with 22 scores has
    pages of 1-10, 11-20, and 21-22. Page 4 will redirect to 21-22.
    - `mod` is the mod, in shorthand notation (NM/HR/...) to filter scores with. If `use_mod_array`
    is `True`, then all shorthand names in the Mods enum at osuapi.py are valid. Otherwise,
    the shorthand pool prefixes are used, with valid mods likely including `["NM", "HR", "HD", "DT", 
    and "FM"]`.
    
    Note this function does no additional work towards generating a Discord embed. If the player
    is not found or has no valid scores, this function returns `None`."""
    pass

async def get_top_map_scores(map_id, page=1, pool=None):
    """Get the top n scores (as documents) of a map, filtered by mod if defined.
    
    - `map_id` can be either the shorthand name of the map in the pool ("NM1") or the full diff ID.
    If pool is not defined, then `map_id` must be the diff id. If `pool` is defined, then
    `map_id` can be either.
    - `page` determines the top scores to be returned. Pagination is done on a 10 score
    per page basis; if `page*10` exceeds the total number of scores of the player plus 10,
    then the last reasonable page is used instead. For example, a player with 22 scores has
    pages of 1-10, 11-20, and 21-22. Page 4 will redirect to 21-22.
    - `pool` is the shorthand pool name. If not defined, `map_id` must be a diff id resolvable with
    `db_get.determine_pool()`.
    
    Note this function does no additional work towards generating a Discord embed. If the player
    is not found or has no valid scores, this function returns `None`."""
    pass