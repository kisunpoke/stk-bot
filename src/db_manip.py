"""Async functions for interacting with the MongoDB Atlas cluster.

!!None of the stuff below is final and it probably sucks so I'll change the structures later!!

The cluster structure is as follows:
-stk-cluster
    -test
        -test_data: use for anything
    -matches_and_scores
        -scores: collection of `Score` documents
        -matches: collection of `Match` documents
    -mappools
        -test_pool: use for anything
        -<pool_name>: collection of `Map` documents
        -meta: collection of {
            _id: str (shortened pool name; unique)
            long_name: str
            diff_ids: [str, str, ...]
        } documents
    -players_and_teams
        -players: collection of `Player` documents
        -teams: collection of `Team` documents
    -tournament_data
        -meta: a single `Meta` docuemnt
    -discord_users
        -discord_users: collection of `DiscordUser` documents

`Meta` documents have the following fields:
{
    _id: "main"
    full_name: str
    shorthand: str
    icon_url: str
    active_pool: str
}

`DiscordUser` documents have the following fields:
{
    _id: str (discord user id; guaranteed to be unique)
    osu_name: str
    osu_id: str
    team_name: str
    preferences: {
        use_images: bool #determines whether ASCII tables or images are used
    }
}

(note that this assumes a team vs format)
`Score` documents have the following fields:
{
    #osu does generate its own game id for each map in a match, but the below is more
    #usable for this bot
    _id: string = player_id-mp_id-mp_index,
    user_id: string,
    user_name: string*,
    score: int,
    combo: int,
    accuracy: double*, #Stored from 0 to 1!!
    mod_val: int,
    mods: [str, str, ...]*,
    hits: {
        300_count: int,
        100_count: int,
        50_count: int,
        miss_count: int,
    },
    team_total: int*,
    team: str, #1 or 2
    contrib: double*,
    score_difference: int*,
    diff_id: string (int, not pool-map format),
    match_id: string,
    match_name: string,
    match_index: int,
    map_type: string*,
    pool: string*,
    stage: string*,
}

`Match` documents have the following fields:
{
    _id: str (mp_id; guaranteed to be unique),
    ref_name: str,
    ref_id: str,
    scores: [str, str, ...], #Score document _id's
    blue_team_stats: {
        average_acc: double
        average_score: int (rounded)
        average_difference: int (rounded)
    },
    red_team_stats: {
        average_acc: double
        average_score: int (rounded)
        average_difference: int (rounded)
    },
    player_stats:{
        <player_id>:{
            username: str
            team: str (1/2)
            average_acc: double
            average_score: int (rounded)
            average_contrib: double
            scores: int
        }, ...
    }
}

`Map` documents have the following fields:
{
    _id: str (/b is guaranteed to be unique)
    scores: [str, str, ...] #Score document _id's
    pool_id: str (of NM1, HD2, HR3, etc)
    map_type: str (of NM, HD, HR, etc)
    map_url: str
    thumbnail_url: str
    #full_res_stored: false #when we do full-size map cards, this might be needed
    meta:{
        map_artist: str
        map_song: str
        map_diff: str
        map_creator: str
        star_rating: double
        bpm: double (or int)
        drain_time: int
    }
    stats:{
        picks: int
        bans: int
        total_scores: int
        average_score: double
        average_acc: double
        one_mils: int
    }
}

`Player` documents have the following fields:
{
    _id: string, #(of user id; guaranteed to be unique)
    user_name: str,
    user_lower: str
    team_name: string, #must be equivalent to _id of Team document
    pfp_url: str,
    scores: [str, str, ...], # (list of `Score` _id)
    cached:{**
        average_acc: double
        base_acc: double
        acc_rank: int
        average_score: double
        base_score: int
        score_rank: int
        average_contrib: double
        base_contrib: double
        contrib_rank: int
        maps_played: int
        maps_won: int
        maps_lost: int
        total_scores: int
        hits: {
            300_count: int
            100_count: int
            50_count: int
            miss_count: int
        }
        by_mod:{
            NM:{
                maps_played: int
                maps_won: int
                maps_lost: int
                total_scores: int #unused, because is same as maps_played
                average_acc: double
                base_acc: double
                average_score: double
                base_score: int
                average_contrib: double
                base_contrib: double
            },
            HD:{<same as nomod>},
            HR:{<same as nomod>},
            DT:{<same as nomod>},
            FM:{<same as nomod>},
        }
    }
}

`Team` documents have the following fields:
{
    _id: str #(we are certain teams should never have the same name)
    name_lower: str
    players: [str, str, ...] #(of player ids)
    scores: [str, str, ...] #(of score _ids)
    cached:{**
        average_acc: double
        base_acc: double
        acc_rank: int
        average_score: double
        base_score: int
        score_rank: int
        maps_played: int
        maps_won: int
        maps_lost: int
        total_scores: int
        hits: {
            300_count: int
            100_count: int
            50_count: int
            miss_count: int
        }
        by_mod:{
            NM:{
                maps_played: int
                maps_won: int
                maps_lost: int
                total_scores: int
                average_acc: double
                base_acc: double
                average_score: double
                base_score: int
                average_contrib: double
                base_contrib: double
            },
            HD:{<same as nomod>},
            HR:{<same as nomod>},
            DT:{<same as nomod>},
            FM:{<same as nomod>},
        }
    }
}

** - (re)calculated whenever a manual update occurs or a match is entered where they were a player
i don't know if i want to actually use these fields or just calcuate them as needed
will probably drop them if/when i decide the usage of this bot will probably be low enough

note that numbers that should not have numerical calculations performed on them are strings, 
not ints/floats as the data might suggest; this will hopefully improve clarity

also all accuracy is stored internally as a double from 0 to 1; they are not stored in xx.xx format
"""
import motor.motor_asyncio
import pprint
import collections
import os
import asyncio

import osuapi
import db_get
import prompts

#to implement pagination we can use cursor.skip()
#see https://docs.mongodb.com/manual/reference/method/cursor.skip/
#and https://stackoverflow.com/questions/57159663/mongodb-get-element-in-the-middle-of-a-find-sort-result-using-nodejs-native-driv
db_url = os.getenv("db_url")

client = motor.motor_asyncio.AsyncIOMotorClient(db_url)

async def getval(key, value, db='test', collection='test-data'):
    """Find and return the MongoDB document with key:value in db[collection]."""
    db = client[db]
    collection = db[collection]
    document = await collection.find_one({key: value})
    return document

async def setval(key, value, db='test', collection='test-data'):
    """Insert the document with key:value in db[collection]."""
    db = client[db]
    collection = db[collection]
    document = {key: value}
    result = await collection.insert_one(document)
    print('result %s' % repr(result.inserted_id))
    return ("done")

async def deleteval(key, value, db='test', collection='test-data'):
    """Delete the document with key:value in db[collection]."""
    db = client[db]
    collection = db[collection]
    document = {key: value}
    result = await collection.delete_one(document)
    print(result)

async def add_meta(meta_data):
    """Create and add the meta document."""
    db = client['tournament_data']
    collection = db['meta']

    document = {
        "_id": "main",
        "full_name": meta_data[0][1],
        "shorthand": meta_data[1][1],
        "icon_url": meta_data[2][1],
        "active_pool": meta_data[4][1]
    }
    await collection.insert_one(document)

async def add_pools(pool_data):
    """Update the `mappools` database with `pool_data`.
    
    Individual maps in `pool_data` are a list of the format 
    `[round, diff_id, mod, pool_id]`, all of which are `str`.
    - `round` is a comma+space separated string and is treated as an identifier;
    if empty, this map is assumed to belong to the same mappool as the last. If 
    it is not empty, then the current mappool (and thus db collection) is changed
    acccordingly and a new document in `meta` is added.
    - `diff_id` is the beatmap diff's ID (/b, not /s).
    - `mod` is the two-letter code denoting this map's mods. Valid mods include
    `HD`, `HR`, `DT`, `FM`, and `TB`.
    - `pool_id` is the unique mod+id for this mappool, such as `NM1`.
    """
    db = client['mappools']

    meta_docs = []
    
    current_pool_collection = None
    current_pool_docs = []
    current_pool_ids = []
    current_metadata = []
    for map in pool_data:
        if map[0] != '':
            #this signifies that we are on a new mappool
            #so we now insert/generate all of the existing documents
            #don't do unless a pool is currently being created
            if current_pool_collection:
                await current_pool_collection.insert_many(current_pool_docs)
                #now we add the previous pool's metadata
                pool_long = current_metadata[0] #ex. Round of 32
                pool_short = current_metadata[1] #ex. Ro32

                meta_document = {
                    "_id": pool_short,
                    "long_name": pool_long,
                    "diff_ids": current_pool_ids
                }
                meta_docs.append(meta_document)
            
            #the last "map" in a bulk add should always be ["END", ...]
            #otherwise the the last pool will not be added
            if map[0] == "END":
                break
            else:
                #generate the metadata of this new pool and set the new pool collection
                current_metadata = map[0].split(", ")
                current_pool_collection = db[current_metadata[1]]
                #reset doc and id lists 
                current_pool_docs = []
                current_pool_ids = []
        #get and process map data
        map_data = await osuapi.get_map_data(map[1])
        #print(map_data)
        #note how we do not make any additional calculations to bpm or drain time
        #we can do that elsewhere, not here
        map_document = {
            '_id': map[1],
            'scores': [],
            'pool_id': map[3],
            'map_type': map[2],
            'map_url': f'https://osu.ppy.sh/b/{map[1]}',
            'thumbnail_url': f'https://b.ppy.sh/thumb/{map_data["beatmapset_id"]}l.jpg',
            'meta':{
                'map_artist': map_data["artist"],
                'map_song': map_data["title"],
                'map_diff': map_data["version"],
                'map_creator': map_data["creator"],
                'star_rating': map_data["difficultyrating"],
                'bpm': map_data["bpm"],
                'drain_time': map_data["total_length"],
            },
            'stats':{
                'picks': 0,
                'bans': 0,
                'total_scores': 0,
                'average_score': 0.0,
                'average_acc': 0.0,
                'one_mils': 0
            }
        }
        current_pool_docs.append(map_document)
        current_pool_ids.append(map[1])
    #add metadata docs
    meta_collection = db['meta']
    await meta_collection.insert_many(meta_docs)

async def add_players_and_teams(player_data, *, create_index=False):
    """Update the `tournament_data` database from `player_data`.
    
    *This function is not intended for updating existing players.*

    `player_data` is a list of teams and either player names or player IDs.
    Because the osu! API will automatically attempt to determine if the entered value
    is an ID or a username, there is no need to have validation or maintain
    a strict format. However, purely-numerical names may be more difficult to
    deal with.
    The list is in the format `[[team_name, player_1, player_2, ...], [...], ...]`, all `str`.
    - `team_name` is a str of the team name. It is used as an _id and thus must be
    unique (as it should be).
    - `player_<n>` is a player associated with `team_name`. An individual document
    for each player is created in the `players` collection.
    
    If this function is used to initialize the player/team database, then
    `create_index` should be True. This will create indexes on rankable fields
    (both the rank and the value itself - average_acc *and* acc_rank, for example).

    Note that players and teams are initialized with cached statistics, like average score
    and acc, set to zero. Players are treated as unranked if their rank is equal to 0 or they
    have zero scores. This means that after score addition, players should always have their 
    ranks updated."""
    db = client['players_and_teams']
    team_collection = db['teams']
    player_collection = db['players']

    team_documents = []
    player_documents = []

    #since this isn't going to magically change while we're adding players
    #we ok
    cached_mod_base = {
        "maps_played": 0,
        "maps_won": 0,
        "maps_lost": 0,
        "total_scores": 0,
        "average_acc": 0.00,
        "base_acc": 0.00,
        "average_score": 0.00,
        "base_score": 0,
        "average_contrib": 0.00, #these just go unused for team docs
        "base_contrib": 0.00,
    }

    for team in player_data:
        #first, add the new team
        players = team[1:]
        player_data = [await osuapi.get_player_data(username) for username in players]
        player_ids = [player['user_id'] for player in player_data]
        team_document = {
            '_id': team[0],
            'name_lower': team[0].lower(),
            'players': player_ids,
            'scores': [],
            'cached':{
                'average_acc': 0.00,
                'base_acc': 0.00, 
                'acc_rank': 0,
                'average_score': 0.00,
                'base_score': 0.00, 
                'score_rank': 0,
                'maps_played': 0,
                'maps_won': 0,
                'maps_lost': 0,
                'total_scores': 0,
                'hits':{
                    '300_count': 0,
                    '100_count': 0,
                    '50_count': 0,
                    'miss_count': 0,
                },
                "by_mod":{
                        "NM": cached_mod_base,
                        "HD": cached_mod_base,
                        "HR": cached_mod_base,
                        "DT": cached_mod_base,
                        "FM": cached_mod_base
                    }
            }
        }
        team_documents.append(team_document)

        #then iterate over each player id
        #really we don't do anything with player_data but at least you can expand it easily
        for player_index, player_id in enumerate(player_ids):
            player_document = {
                "_id": player_id,
                'user_name': player_data[player_index]['username'],
                'user_lower': player_data[player_index]['username'].lower(),
                'team_name': team[0],
                'pfp_url': f"https://a.ppy.sh/{player_id}",
                'scores': [],
                'cached':{
                    'average_acc': 0.00,
                    'base_acc': 0.00,
                    'acc_rank': 0,
                    'average_score': 0.00,
                    'base_score': 0,
                    'score_rank': 0,
                    'average_contrib': 0.00,
                    'base_contrib': 0.00,
                    'contrib_rank': 0,
                    'maps_played': 0,
                    'maps_won': 0,
                    'maps_lost': 0,
                    'hits':{
                        '300_count': 0,
                        '100_count': 0,
                        '50_count': 0,
                        'miss_count': 0,
                    },
                    "by_mod":{
                        "NM": cached_mod_base,
                        "HD": cached_mod_base,
                        "HR": cached_mod_base,
                        "DT": cached_mod_base,
                        "FM": cached_mod_base
                    }
                }
            }
            player_documents.append(player_document)
    await player_collection.insert_many(player_documents)
    await team_collection.insert_many(team_documents)

    if create_index:
        for field in ["average_acc", "average_score", "average_contrib", "acc_rank", "score_rank",
                      "contrib_rank", "user_name", "user_lower"]:
            await player_collection.create_index([(field, -1)])
        for field in ["average_acc", "average_score", "acc_rank", "score_rank", "name_lower"]:
            await team_collection.create_index([(field, -1)])

async def add_scores(matches_data, *, create_index=False, ctx=None):
    """Update literally everything related to scores.
    
    This function:
    - Adds both `Match` and `Score` documents to the `scores` database.
    - Updates the statistics of the teams and players involved.
    - Updates the statistics of the maps played.
    (at least partially by calling more functions)

    Takes the list `matches_data`, which is expected to be in the format
    `[match_id, referee_id, referee_name, stage, bans, ignore_to_index]`.
    - `match_id` is the MP id of the match.
    - `referee_id` is the referee's user ID. This can be used to ignore
    the referee's scores in a match.
    - `referee_name` is the referee's username.
    - `stage` is the formal stage of that match, as in "Round of 32" or
    "Loser's Bracket Finals."
    - `bans` is a `str` of comma-separated map ids.
    - `ignore_to_index` is the index of the last map to be ignored, with
    all maps before it ignroed as well.

    If this function is used to initialize the score/match database, then
    `create_index` should be True. This will create an index on the "score"
    field. (Since the _ids of scores per match/map/player/etc are stored, we
    only index by score here, not a compound index)

    If desired, `ctx` can be passed to send messages to the Discord channel where
    the command was called.

    As of now, this function is designed exclusively for tournament matches. Attempting
    to use this function for non-tournament matches will fail.
    """
    #so that feels like a lot, will split later as necessary

    #For each match:
    # - Get all score data via get_individual_match_info().
    # - Get pool meta document and collection based on shorthand pool notation.
    # - Generate associated `Score` documents, saving the _id. Ignore if score is below minimum threshold or if map is not in the specified mappool.
    # - Generate the associated `Match` document using data from the calls of get_individual_match_info().
    # - Update mappool entry using the beatmap ID with the _ids of `Score` documents.
    # - Insert docs. (or at whatever point feels correct)
    # - During the above, save a list of all unique players seen.
    # - Get the player docs for each of these players. (if a player can't be found, ignore them)
    # - Update player docs with new stats.
    # - Get a list of unique team docs from the players.
    # - Update team docs with new stats.
    player_id_cache = {} #we use one global cache for this entire process

    #to be batch uploaded upon completion
    score_documents = []
    #{"mp_id": [score_document, ...], ...}
    # no need to be a defaultdict since all valid docs are added at once
    matches_documents = {}
    #{"team_name": [score_document, ...], ...}
    team_documents = collections.defaultdict(list)
    #{"player_id": [score_document, ...], ...}
    player_documents = collections.defaultdict(list)
    #{"diff_id": [score_document, ...], ...}
    map_documents = collections.defaultdict(list)
    #{"diff_id": <ban count as `int`>}
    ban_documents = collections.defaultdict(int)
    for match in matches_data:
        api_match_data = await osuapi.get_match_data(match[0])
        if not api_match_data['games']:
            continue

        match_documents = []
        #we don't determine the pool name until we're inside the for loop
        #which is why processing this match's bans ended up inside
        #i can't think of any better alternatives that wouldn't do the same pool-finding process anyways
        bans_processed = False

        for index, game_data in enumerate(api_match_data["games"]):
            #ignoring maps if they are either not in pool or explicitly ignored
            #this wasn't tested before committing!!! if something breaks on next rebuild
            #blame it on this right here
            if index in [int(map_index) for map_index in match[5].split(",")]:
                continue
            processed = await osuapi.process_match_data(match[0], index, data=api_match_data, player_ids=player_id_cache)
            if processed == None:
                continue
            player_id_cache = processed["player_ids"]
            pool_name = await db_get.determine_pool(processed["diff_id"])
            #this map isn't in the pool; don't go any further
            if not pool_name:
                continue
            
            #process bans
            if not bans_processed:
                for ban_shorthand in [str(banned_id) for banned_id in match[4].split(",")]:
                    #print(f"Processing {ban_shorthand} for {pool_name} (stage {match[3]}, id {match[0]})")
                    ban_id = (await db_get.get_map_document(ban_shorthand, pool_name))["_id"]
                    #print(f"was resolved to {ban_id}")
                    ban_documents[ban_id] += 1
                    bans_processed = True

            map_type = (await db_get.get_map_document(processed["diff_id"], pool_name))["map_type"]
            #oh my god the function complexity lol
            for score in processed["individual_scores"]:
                #this format is theoretically always unique and can yield score information in itself
                #we could also use the game id given by the osu api for each map in a match,
                #but this is more useful
                id = f"{score['user_id']}-{match[0]}-{index}"

                winner_dict = {
                    "Blue": "1",
                    "Red": "2"
                }

                #generate score document
                score_document = {
                    "_id": id,
                    "user_id": score["user_id"],
                    "user_name": score["user_name"],
                    "score": score["score"],
                    "combo": score["combo"],
                    "accuracy": score["accuracy"],
                    "mod_val": score["mod_val"],
                    "mods": score["mods"],
                    "hits": {
                        "300_count": score["hits"]["300_count"],
                        "100_count": score["hits"]["100_count"],
                        "50_count": score["hits"]["50_count"],
                        "miss_count": score["hits"]["miss_count"]
                    },
                    "team_total": processed["team_1_score"] if score["team"] == "1" else processed["team_2_score"],
                    "team": score["team"],
                    "contrib": score["score"]/processed["team_1_score"] if score["team"] == "1" else score["score"]/processed["team_2_score"],
                    "score_difference": processed["score_difference"] if winner_dict[processed["winner"]] == score["team"] else -(processed["score_difference"]),
                    "diff_id": processed["diff_id"],
                    "match_id": processed["match_id"],
                    "match_name": processed["match_name"],
                    "match_index": index,
                    "map_type": map_type,
                    "pool": pool_name,
                    "stage": match[3]
                }

                score_documents.append(score_document)
                match_documents.append(score_document)

                player_documents[score['user_id']].append(score_document)
                team_documents[score['team_name']].append(score_document)
                map_documents[processed['diff_id']].append(score_document)
        '''
        import pprint
        print(f"for id {match[0]}:")
        pprint.pprint(api_match_data)
        print(api_match_data["match"])
        print(api_match_data["match"]["match_id"])
        print(match[0])
        '''
        matches_documents[match[0]] = match_documents
    '''
    import pprint
    pprint.pprint(matches_documents)
    pprint.pprint(team_documents)
    '''

    score_db = client["matches_and_scores"]
    score_collection = score_db["scores"]
    
    if ctx:
        await ctx.send("finishing up score insertion (7/12)")
    await score_collection.insert_many(score_documents)
    #supposedly index creation after inserting data is faster so it's after the fx above    
    if create_index:
        #descending: all scores
        await score_collection.create_index([("score", -1)])

    if ctx:
        await ctx.send("updating player stats (8/12)")
    await update_player_stats(player_documents)
    if ctx:
        await ctx.send("updating team stats (9/12)")
    await update_team_stats(team_documents)
    if ctx:
        await ctx.send("updating match stats (10/12)")
    await create_match_stats(matches_documents)
    if ctx:
        await ctx.send("updating map stats (11/12)")
    await update_map_stats(map_documents, ban_documents)
    if ctx:
        await ctx.send("updating ranks (12/12)")
    await update_ranks()

async def update_player_stats(player_dict):
    """Update player statistics.
    
    `player_dict` is a `dict` of user IDs (as strings) to
    a list of Score documents generated by `add_score()`. User IDs should
    be identical to the _id of Player documents.
    This function pulls existing player stats and updates them
    accordingly. Note that statistics are not cached for individual
    mods.

    Players that can't be found based on ID are ignored.
    
    Cached ranks should be recalculated following individual score addition."""
    db = client['players_and_teams']
    player_collection = db['players']
    for player_id in player_dict:
        player_document = await player_collection.find_one({'_id': player_id})
        if player_document == None:
            print(f"Lookup for player {player_id} failed!!")
            pprint.pprint(player_dict[player_id])
            continue
        stat = player_document['cached']

        for score in player_dict[player_id]:
            stat['base_acc'] += score['accuracy']
            stat['base_score'] += score['score']
            stat['base_contrib'] += score['contrib']
            stat['maps_played'] += 1
            #i highly doubt we will ever encounter a tie but 
            #it's treated as neither a loss nor a win
            if score['score_difference'] > 0:
                stat['maps_won'] += 1
            elif score['score_difference'] < 0:
                stat['maps_lost'] += 1
            stat['hits']['300_count'] += score['hits']['300_count']
            stat['hits']['100_count'] += score['hits']['100_count']
            stat['hits']['50_count'] += score['hits']['50_count']
            stat['hits']['miss_count'] += score['hits']['miss_count']

            #per-mod stat changes
            if score['map_type'] == "TB":
                mod_stat = stat['by_mod']["FM"]
            else:
                mod_stat = stat['by_mod'][score['map_type']]
            mod_stat['base_acc'] += score['accuracy']
            mod_stat['base_score'] += score['score']
            mod_stat['base_contrib'] += score['contrib']
            
            mod_stat['maps_played'] += 1
            if score['score_difference'] > 0:
                mod_stat['maps_won'] += 1
            elif score['score_difference'] < 0:
                mod_stat['maps_lost'] += 1

            #and add to the player's list of scores
            player_document['scores'].append(score['_id'])
        
        #recalculate baselines back to an average
        stat['average_acc'] = stat['base_acc'] / stat['maps_played'] 
        stat['average_score'] = stat['base_score'] / stat['maps_played'] 
        stat['average_contrib'] = stat['base_contrib'] / stat['maps_played']

        #then for mods as well
        for mod in stat['by_mod']:
            mod_stat = stat['by_mod'][mod]
            if mod_stat['maps_played'] != 0:
                mod_stat['average_acc'] = mod_stat['base_acc'] / mod_stat['maps_played'] 
                mod_stat['average_score'] = mod_stat['base_score'] / mod_stat['maps_played'] 
                mod_stat['average_contrib'] = mod_stat['base_contrib'] / mod_stat['maps_played'] 

        #pprint.pprint(player_document)
        
        #and update the player document
        await player_collection.replace_one({'_id': player_id}, player_document)

async def update_team_stats(team_dict):
    """Update team statistics.
    
    `player_dict` is a `dict` of team names (as strings) to
    a list of Score documents generated by `add_score()`. Team names should be
    identical to the _id of Team documents.
    This function pulls existing player stats and updates them
    accordingly. Note that statistics are not cached for individual
    mods.
    
    Cached ranks should be recalculated following individual score addition."""
    db = client['players_and_teams']
    team_collection = db['teams']
    for team_name in team_dict:
        team_document = await team_collection.find_one({'_id': team_name})
        if team_document == None:
            print(f"Lookup for team {team_name} failed!!")
            pprint.pprint(team_dict[team_name])
            continue
        processed_maps = []
        stat = team_document['cached']
        #theoretically no need to call every single score that's already stored in the player's document

        for score in team_dict[team_name]:
            #main
            stat['base_acc'] += score['accuracy']
            stat['base_score'] += score['score']
            stat['total_scores'] += 1 #usually two per map
            if score['match_id']+str(score['match_index']) not in processed_maps:
                #only one per map
                stat['maps_played'] += 1
                if score['score_difference'] > 0:
                    stat['maps_won'] += 1
                elif score['score_difference'] < 0:
                    stat['maps_lost'] += 1
            stat['hits']['300_count'] += score['hits']['300_count']
            stat['hits']['100_count'] += score['hits']['100_count']
            stat['hits']['50_count'] += score['hits']['50_count']
            stat['hits']['miss_count'] += score['hits']['miss_count']

            #per-mod stat changes
            if score['map_type'] == "TB":
                mod_stat = stat['by_mod']["FM"]
            else:
                mod_stat = stat['by_mod'][score['map_type']]
            mod_stat['base_acc'] += score['accuracy']
            mod_stat['base_score'] += score['score']
            mod_stat['total_scores'] += 1
            
            if score['match_id']+str(score['match_index']) not in processed_maps:
                mod_stat['maps_played'] += 1
                if score['score_difference'] > 0:
                    mod_stat['maps_won'] += 1
                elif score['score_difference'] < 0:
                    mod_stat['maps_lost'] += 1
                #formatted match_id-match_index, always unique per individual map played
                processed_maps.append(score['match_id']+str(score['match_index']))

            #add score id 
            team_document['scores'].append(score['_id'])
        
        #recalculate baselines back to an average
        #the team size (in an individual map)
        stat['average_acc'] = stat['base_acc'] / stat['total_scores']
        stat['average_score'] = stat['base_score'] / stat['total_scores']

        #then for mods as well
        for mod in stat['by_mod']:
            mod_stat = stat['by_mod'][mod]
            if mod_stat['maps_played'] != 0:
                mod_stat['average_acc'] = mod_stat['base_acc'] / mod_stat['total_scores'] 
                mod_stat['average_score'] = mod_stat['base_score'] / mod_stat['total_scores'] 

        #pprint.pprint(team_document)
        
        #and update the document
        await team_collection.replace_one({'_id': team_name}, team_document)

async def update_map_stats(map_dict, ban_dict):
    """Update map statistics.
    
    - `map_dict` is a `dict` of diff ids (as strings) to
    a list of Score documents generated by `add_score()`. Diff ids should be
    identical to the _id of Map documents.
    - `ban_dict` is a `dict` of diff ids (as strings) to ints representing ban count.
    For maps that aren't banned (and thus aren't in `ban_dict`), `defaultdict` will return
    0 for that map anyways.
    
    (not implemented: indexing on score?)"""
    db = client['mappools']
    for diff_id in map_dict:
        #here we store the distinct matches, adding it to the pick count at the end
        unique_match_ids = []
        #collections are split by pool, but fortunately we store the pool in the Score doc
        #we'll just take the first such doc
        pool_collection = db[map_dict[diff_id][0]["pool"]]
        map_document = await pool_collection.find_one({'_id': diff_id})
        if map_document == None:
            #which means something has gone horribly wrong
            print(f"Lookup for map {diff_id} failed!!")
            continue
        stat = map_document['stats']
        #theoretically no need to call every single score that's already stored in the player's document
        baseline_acc = stat['average_acc'] * stat['total_scores']
        baseline_score = stat['average_score'] * stat['total_scores']

        for score in map_dict[diff_id]:
            baseline_acc += score['accuracy']
            baseline_score += score['score']
            stat['total_scores'] += 1
            
            #technically speaking we could get away with this
            #stat['picks'] += 0.25
            #but if we were to ever change the players per team, or
            #some unexpected thing came up, it would be difficult to fix
            #so we'll just count the maps instead and work from there

            if score['match_id'] not in unique_match_ids:
                unique_match_ids.append(score['match_id'])

            map_document['scores'].append(score['_id'])
        
        #recalculate baselines back to an average
        stat['average_acc'] = baseline_acc / stat['total_scores'] 
        stat['average_score'] = baseline_score / stat['total_scores'] 

        #for maps, add the number of picks (and also update bans)
        stat['picks'] += len(unique_match_ids)
        stat['bans'] += ban_dict[diff_id]
        #pprint.pprint(map_document)
        
        #and update the document
        await pool_collection.replace_one({'_id': diff_id}, map_document)

async def create_match_stats(match_dict):
    """Create match documents.
    
    `match_dict` is a `dict` of match ids (as strings) to
    a list of Score documents generated by `add_score()`. Match ids
    will be used as the `_id` of the generated Match document.

    Also note this assumes a Team VS format.
    
    (not implemented: bans)"""
    db = client['matches_and_scores']
    match_collection = db['matches']
    match_docs = []
    for mp_id in match_dict:
        match_document = {
            '_id': mp_id,
            'ref_name': None,
            'ref_id': None,
            'scores': [],
            'blue_team_stats': {
                'average_acc': 0,
                'average_score': 0,
                'average_difference': 0
            },
            'red_team_stats': {
                'average_acc': 0,
                'average_score': 0,
                'average_difference': 0
            },
            'player_stats':{}
        }
        blue_scores = 0
        red_scores = 0
        #the equivalent of `baseline_acc/score` is stored in the stats fields until the end

        for score in match_dict[mp_id]:
            #modify team stats
            if score['team'] == "1":
                stat = match_document['blue_team_stats']
                stat['average_acc'] += score['accuracy']
                stat['average_score'] += score['score']
                stat['average_difference'] += score['score_difference']
                blue_scores += 1
            else:
                stat = match_document['red_team_stats']
                stat['average_acc'] += score['accuracy']
                stat['average_score'] += score['score']
                stat['average_difference'] += score['score_difference']
                red_scores += 1
            
            #modify player stat for this match
            if score['user_id'] not in match_document['player_stats']:
                match_document['player_stats'][score['user_id']] = {
                    'user_name': score['user_name'],
                    'team': score['team'],
                    'average_acc': 0,
                    'average_score': 0,
                    'average_contrib': 0,
                    'scores': 0
                }
            player_stat = match_document['player_stats'][score['user_id']]
            player_stat['average_acc'] += score['accuracy']
            player_stat['average_score'] += score['score']
            player_stat['average_contrib'] += score['contrib']
            player_stat['scores'] += 1

            match_document['scores'].append(score['_id'])
        
        #recalculate baselines back to an average
        for stat in ['average_acc', 'average_score', 'average_difference']:
            match_document['blue_team_stats'][stat] /= blue_scores
            match_document['red_team_stats'][stat] /= red_scores

        for player in match_document['player_stats']:
            indiv_stat = match_document['player_stats'][player]
            indiv_stat['average_acc'] /= indiv_stat['scores']
            indiv_stat['average_score'] /= indiv_stat['scores']
            indiv_stat['average_contrib'] /= indiv_stat['scores']

        #pprint.pprint(team_document)
        
        #add generated doc for batch insert
        match_docs.append(match_document)
    #actually perform batch insert
    await match_collection.insert_many(match_docs)

async def update_ranks():
    """Iterate through every team and player document and update their ranks.
    
    This is achieved by sorting documents by the required field, converting it to a list,
    and then using `enumerate()` to determine its position in the list. If the number of scores
    for that player or team is equal to zero, that team remains unranked."""
    equivs = {
        "cached.average_acc": "acc_rank",
        "cached.average_score": "score_rank",
        "cached.average_contrib": "contrib_rank"
    }
    db = client["players_and_teams"]
    player_collection = db["players"]
    team_collection = db["teams"]
    for field in ["cached.average_acc", "cached.average_score", "cached.average_contrib"]:
        cursor = player_collection.find().sort(field, -1)
        #i would imagine we never get that many players
        for index, player_document in enumerate(await cursor.to_list(length=1000)):
            #pprint.pprint(player_document)
            if player_document["cached"]["maps_played"] != 0:
                player_document["cached"][equivs[field]] = index+1
                await player_collection.replace_one({'_id': player_document["_id"]}, player_document)
    for field in ["cached.average_acc", "cached.average_score"]:
        cursor = team_collection.find().sort(field, -1)
        #i would imagine we never get that many teams
        for index, team_document in enumerate(await cursor.to_list(length=1000)):
            if team_document["cached"]["maps_played"] != 0:
                team_document["cached"][equivs[field]] = index+1
                await team_collection.replace_one({'_id': team_document["_id"]}, team_document)

    #there were some alternate methods, but this is the one i understand best

async def get_all_gsheet_data(bot, ctx, sheet_id):
    """Get all GSheet data from the target sheet and run the OAuth flow if needed.
    
    While perhaps not the most secure way to be executing the flow, we use Discord for
    the authorization prompt as well as the access code entry. This is why `bot` and `ctx` are
    needed."""
    #theoretically we'll need this practically never so imports occur here
    #if we find a need to regularly rebuild databases from gsheets, then we can move this out
    import pickle
    import os.path
    from googleapiclient.discovery import build
    from google_auth_oauthlib.flow import Flow
    from google.auth.transport.requests import Request

    # If modifying these scopes, delete the file token.pickle.
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    #derived from https://google-auth-oauthlib.readthedocs.io/en/latest/reference/google_auth_oauthlib.flow.html

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            #https://google-auth-oauthlib.readthedocs.io/en/latest/reference/google_auth_oauthlib.flow.html#google_auth_oauthlib.flow.Flow.from_client_secrets_file
            #creates the flow instance
            flow = Flow.from_client_secrets_file(
                'google-credentials.json', SCOPES, redirect_uri='urn:ietf:wg:oauth:2.0:oob')

            #generate authorization url, the first step in oauth
            auth_url, _ = flow.authorization_url(prompt='consent')

            #inform the original invoker that this process has started.
            await ctx.send("Authorization is needed and the process has started. "
                           "(go to the channel that should've just pinged you - "
                           "if you weren't mentioned anywhere you shouldn't be using this)"
                           " You have 1 minute.")

            #send the url to a restricted chat
            #this chat should already be limited to people with access to the main google account/the sheet
            #this "restricted chat" thing might not be needed (especially if the sheet this bot's data will be based on is public)
            #but i'd say it doesn't hurt to hide things from people who don't need them 
            auth_channel = bot.get_channel(774881438817845289) #have this in the bot's meta document so it isn't hardcoded in the future
            auth_msg = await auth_channel.send(f'{ctx.message.author.mention}\n\n'
                                               f'An authorization event has been triggered. Please go to this URL: {auth_url}'
                                               f' and complete the process. Type the access code as your next message.'
                                               f' (Note: you need to complete this on the same account that has access to the'
                                               f' sheet ID you just entered!) You have 1 minute.')

            #wait for user response
            def check(m):
                return m.channel.id==774881438817845289

            try:
                msg = await bot.wait_for('message', timeout=60.0, check=check)
                await auth_msg.delete()
            except asyncio.TimeoutError:
                #delete to make sure it's clear the process must be restarted
                await auth_msg.delete()
                await auth_channel.send('Response timed out. Run through this process again.')
                #send to original invoking channel 
                await ctx.send("The authorization process failed.")
                return None
            else:
                if await prompts.confirmation_dialog(bot, ctx, f"Are you **SURE** this is the correct token?\n{msg.content}"):
                    flow.fetch_token(code=msg.content)
                    await ctx.send("The authorization process succeded; you should start seeing more msgs now")
                else:
                    await auth_channel.send("Ok. Start over.")
                    #send to original invoking channel 
                    await ctx.send("The authorization process failed.")
                    return None

            #flow.credentials can only be run AFTER fetch_token is called
            creds = flow.credentials
            #creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    #https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build
    #creds should be of type google.auth.credentials.Credentials, which is returned by flow.credentials
    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()

    output = {}

    ranges = {
        'meta': 'meta!A2:B',
        'matches': 'matches!A2:F',
        'pools': 'pools!A2:D',
        'teams': 'teams!A2:E'
    }

    for range_id in ranges:
        range_name = ranges[range_id]
        result = sheet.values().get(spreadsheetId=sheet_id,
                                    range=range_name).execute()
        output[range_id] = result.get('values', [])

        '''
        print("for %s:"%range)
        if not values:
            print('No data found.')
        else:
            for row in values:
                print(row)
        '''
    return output

async def rebuild_all(bot, ctx, sheet_id):
    """Drops ALL non-test databases, then rebuilds them using gsheet data.
    
    This DOES NOT drop the discord_users database."""
    databases = ['mappools', 'players_and_teams', 'tournament_data', 'matches_and_scores']
    #total number of steps because i'm lazy
    steps = 12
    await ctx.send(f"dropping databases... (1/{steps})")
    for database in databases:
        await client.drop_database(database)
        print("dropped %s"%database)
    await ctx.send(f"getting gsheet info... (2/{steps})")
    data = await get_all_gsheet_data(bot, ctx, sheet_id)
    await ctx.send(f"building meta db (3/{steps})")
    await add_meta(data['meta'])
    await ctx.send(f"building mappool db (4/{steps})")
    await add_pools(data['pools'])
    await ctx.send(f"building team and player db (5/{steps})")
    await add_players_and_teams(data['teams'], create_index=True)
    await ctx.send(f"building scores (6/{steps}) - this will take a while")
    await add_scores(data['matches'], create_index=True, ctx=ctx)
    await ctx.send("done!!")

async def create_discord_user(id):
    """Initialize a new DiscordUser document.
    
    Technically, also creates the discord_users collection and db if not
    already created."""
    db = client['discord_users']
    collection = db['discord_users']

    document = {
        "_id": id,
        "osu_name": None,
        "osu_id": None,
        "team_name": None,
        "preferences":{
            "use_images": None
        }
    }
    await collection.insert_one(document)

async def update_discord_user(id, document):
    """Update DiscordUser document."""
    db = client['discord_users']
    collection = db['discord_users']
    await collection.replace_one({'_id': id}, document)