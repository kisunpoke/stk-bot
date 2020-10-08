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
        -discord_users: collection of `DiscordUser` documents

`Meta` documents have the following fields:
{
    full_name: str
    shorthand: str
    icon_url: str
}

`DiscordUser` documents have the following fields:
{
    _id: str (discord user id; guaranteed to be unique)
    osu_name: str
    osu_id: str
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
    match_index: string,
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
    pool_id: str
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
    user_name: string,
    team_name: string,
    pfp_url: str,
    scores: [str, str, ...], # (list of `Score` _id)
    cached:{**
        average_acc: double,
        acc_rank: int,
        average_score: double,
        score_rank: int,
        maps_played: int,
        maps_won: int,
        maps_lost: int,
        hits: {
            300_count: int,
            100_count: int,
            50_count: int,
            miss_count: int
        }
    }
}

`Team` documents have the following fields:
{
    _id: str #(we are certain teams should never have the same name)
    players: [str, str, ...] #(of player ids)
    scores: [str, str, ...] #(of score _ids)
    cached:{**
        average_acc: double
        acc_rank: int
        average_score: double
        score_rank: int
        maps_played: int
        maps_won: int
        maps_lost: int
        hits: {
            300_count: int
            100_count: int
            50_count: int
            miss_count: int
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

import osuapi

#to implement pagination we can use cursor.skip()
#see https://docs.mongodb.com/manual/reference/method/cursor.skip/
#and https://stackoverflow.com/questions/57159663/mongodb-get-element-in-the-middle-of-a-find-sort-result-using-nodejs-native-driv
db_url = open("dburl").read()

client = motor.motor_asyncio.AsyncIOMotorClient(db_url)

async def getval(key, value, db='test', collection='test-data'):
    """Find and return the MongoDB document with key:value in db[collection]."""
    db = client[db]
    collection = db[collection]
    document = await collection.find_one({key: value})
    return document

async def setval(key, value, db='test', collection='test-data'):
    """..."""
    db = client[db]
    collection = db[collection]
    document = {key: value}
    result = await collection.insert_one(document)
    print('result %s' % repr(result.inserted_id))
    return ("done")

async def deleteval(key, value, db='test', collection='test-data'):
    """Delete the document with key: value in db[collection]."""
    db = client[db]
    collection = db[collection]
    document = {key: value}
    result = await collection.delete_one(document)
    print(result)

#move to util, maybe?

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

async def determine_team(user_id):
    """Figure out what team this `user_id` belongs in.
    
    Returns the full name of the team, equivalent to its `_id` in 
    the `teams` collection of the `players_and_teams` database."""
    db = client["players_and_teams"]
    collection = db["teams"]
    cursor = collection.find()
    #200 teams seems reasonable i assume
    for team_document in await cursor.to_list(length=200):
        if user_id in team_document["players"]:
            return team_document["_id"]
    return None

async def add_meta(meta_data):
    """"""
    db = client['tournament_data']
    collection = db['meta']

    document = {
        "full_name": meta_data[0][1],
        "shorthand": meta_data[1][1],
        "icon_url": meta_data[2][1]
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

async def add_players_and_teams(player_data):
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
    
    Note that players and teams are initialized with some cached statistics, like average score
    and acc, set to zero."""
    db = client['players_and_teams']
    team_collection = db['teams']
    player_collection = db['players']

    team_documents = []
    player_documents = []

    for team in player_data:
        #first, add the new team
        players = team[1:]
        player_data = [await osuapi.get_player_data(username) for username in players]
        player_ids = [player['user_id'] for player in player_data]
        team_document = {
            '_id': team[0],
            'players': player_ids,
            'scores': [],
            'cached':{
                'average_acc': 0,
                'acc_rank': 0,
                'average_score': 0.00,
                'score_rank': 0,
                'maps_played': 0,
                'maps_won': 0,
                'maps_lost': 0,
                'hits':{
                    '300_count': 0,
                    '100_count': 0,
                    '50_count': 0,
                    'miss_count': 0,
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
                'team_name': team[0],
                'pfp_url': f"https://a.ppy.sh/{player_id}",
                'scores': [],
                'cached':{
                    'average_acc': 0,
                    'acc_rank': 0,
                    'average_score': 0.00,
                    'score_rank': 0,
                    'average_contrib': 0.00,
                    'contrib_rank': 0,
                    'maps_played': 0,
                    'maps_won': 0,
                    'maps_lost': 0,
                    'hits':{
                        '300_count': 0,
                        '100_count': 0,
                        '50_count': 0,
                        'miss_count': 0,
                    }
                }
            }
            player_documents.append(player_document)
    await player_collection.insert_many(player_documents)
    await team_collection.insert_many(team_documents)

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
    for match in matches_data:
        api_match_data = await osuapi.get_match_data(match[0])
        if not api_match_data['games']:
            continue

        match_documents = []

        for index, game_data in enumerate(api_match_data["games"]):
            #ignore the first n maps as specified by the match data
            if index <= int(match[5]):
                continue
            processed = await osuapi.process_match_data(match[0], index, data=api_match_data, player_ids=player_id_cache)
            if processed == None:
                continue
            player_id_cache = processed["player_ids"]
            pool_name = await determine_pool(processed["diff_id"])
            #this map isn't in the pool; don't go any further
            if not pool_name:
                continue
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
        ctx.send("finishing up score insertion (7/11)")
    await score_collection.insert_many(score_documents)
    #supposedly index creation after inserting data is faster so it's after the fx above    
    if create_index:
        #descending: all scores
        await score_collection.create_index(("score", -1))

    if ctx:
        ctx.send("updating player stats (8/11)")
    await update_player_stats(player_documents)
    if ctx:
        ctx.send("updating team stats (9/11)")
    await update_team_stats(team_documents)
    if ctx:
        ctx.send("updating match stats (10/11)")
    await create_match_stats(matches_documents)
    if ctx:
        ctx.send("updating map stats (11/11)")
    await update_map_stats(map_documents)
    #await update_ranks


async def update_player_stats(player_dict):
    """Update player statistics.
    
    `player_dict` is a `dict` of user IDs (as strings) to
    a list of Score documents generated by `add_score()`. User IDs should
    be identical to the _id of Player documents.
    This function pulls existing player stats and updates them
    accordingly. Note that statistics are not cached for individual
    mods.
    
    Cached ranks should be recalculated following individual score addition."""
    db = client['players_and_teams']
    player_collection = db['players']
    for player_id in player_dict:
        player_document = await player_collection.find_one({'_id': player_id})
        if player_document == None:
            print(f"Lookup for player {player_id} failed!!")
            continue
        stat = player_document['cached']
        #theoretically no need to call every single score that's already stored in the player's document
        baseline_acc = stat['average_acc'] * stat['maps_played']
        baseline_score = stat['average_score'] * stat['maps_played']
        baseline_contrib = stat['average_contrib'] * stat['maps_played']

        for score in player_dict[player_id]:
            baseline_acc += score['accuracy']
            baseline_score += score['score']
            baseline_contrib += score['contrib']
            stat['maps_played'] += 1
            if score['score_difference'] > 0:
                stat['maps_won'] += 1
            elif score['score_difference'] < 0:
                stat['maps_lost'] += 1
            stat['hits']['300_count'] += score['hits']['300_count']
            stat['hits']['100_count'] += score['hits']['100_count']
            stat['hits']['50_count'] += score['hits']['50_count']
            stat['hits']['miss_count'] += score['hits']['miss_count']
            player_document['scores'].append(score['_id'])
        
        #recalculate baselines back to an average
        stat['average_acc'] = baseline_acc / stat['maps_played'] 
        stat['average_score'] = baseline_score / stat['maps_played'] 
        stat['average_contrib'] = baseline_contrib / stat['maps_played'] 

        #pprint.pprint(player_document)
        
        #and update the document
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
            continue
        stat = team_document['cached']
        #theoretically no need to call every single score that's already stored in the player's document
        baseline_acc = stat['average_acc'] * stat['maps_played']
        baseline_score = stat['average_score'] * stat['maps_played']

        for score in team_dict[team_name]:
            baseline_acc += score['accuracy']
            baseline_score += score['score']
            stat['maps_played'] += 1
            if score['score_difference'] > 0:
                stat['maps_won'] += 1
            elif score['score_difference'] < 0:
                stat['maps_lost'] += 1
            stat['hits']['300_count'] += score['hits']['300_count']
            stat['hits']['100_count'] += score['hits']['100_count']
            stat['hits']['50_count'] += score['hits']['50_count']
            stat['hits']['miss_count'] += score['hits']['miss_count']
            team_document['scores'].append(score['_id'])
        
        #recalculate baselines back to an average
        stat['average_acc'] = baseline_acc / stat['maps_played'] 
        stat['average_score'] = baseline_score / stat['maps_played'] 

        #pprint.pprint(team_document)
        
        #and update the document
        await team_collection.replace_one({'_id': team_name}, team_document)

async def update_map_stats(map_dict):
    """Update map statistics.
    
    `map_dict` is a `dict` of diff ids (as strings) to
    a list of Score documents generated by `add_score()`. Diff ids should be
    identical to the _id of Map documents.
    
    (not implemented: indexing on score?)
    (also not implemented: bans)"""
    db = client['mappools']
    for diff_id in map_dict:
        #here we store the distinct matches, adding it to the pick count at the end
        unique_match_ids = []
        #collections are split by pool, but fortunately we store the pool in the Score doc
        pool_collection = map_dict[diff_id]["pool"]
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
        stat['average_acc'] = baseline_acc / stat['maps_played'] 
        stat['average_score'] = baseline_score / stat['maps_played'] 

        #for maps, add the number of picks
        stat['picks'] += len(unique_match_ids)

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

async def get_all_gsheet_data(sheet_id):
    #this will (should?) block the bot during execution
    #however, this is desired as we don't want other things to happen while we're doing this
    import pickle
    import os.path
    from googleapiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
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
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

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

async def rebuild_all(sheet_id, ctx):
    """Drops ALL non-test databases, then rebuilds them using gsheet data."""
    databases = ['mappools', 'players_and_teams', 'tournament_data', 'matches_and_scores']
    #total number of steps because i'm lazy
    steps = 11
    await ctx.send(f"dropping databases... (1/{steps})")
    for database in databases:
        await client.drop_database(database)
        print("dropped %s"%database)
    await ctx.send(f"getting gsheet info... (2/{steps})")
    data = await get_all_gsheet_data(sheet_id)
    await ctx.send(f"building meta db (3/{steps})")
    await add_meta(data['meta'])
    await ctx.send(f"building mappool db (4/{steps})")
    await add_pools(data['pools'])
    await ctx.send(f"building team and player db (5/{steps})")
    await add_players_and_teams(data['teams'])
    await ctx.send(f"building scores (6/{steps}) - this will take a while")
    await add_scores(data['matches'], create_index=True, ctx=ctx)
    await ctx.send("done!!")
