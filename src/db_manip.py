"""Async functions for interacting with the MongoDB Atlas cluster.

!!None of the stuff below is final and it probably sucks so I'll change the structures later!!

The cluster structure is as follows:
-stk-cluster
    -test
        -test_data: use for anything
    -scores
        -test_pool: use for anything
        -<pool_name>: collection of `Score` documents
    -mappools
        -test_pool: use for anything
        -<pool_name>: collection of `Map` documents
        -meta: collection of {
            _id: pool_name_short as str
            long_name: str
        } documents
    -players_and_teams
        -players: collection of `Player` documents
        -teams: collection of `Team` documents
    -tournament_data
        -meta: a single `Meta` docuemnt

`Meta` documents have the following fields:
{
    full_name: str
    shorthand: str
    icon_url: str
}

`Score` documents have the following fields:
{
    _id: string (maybe we'll not generate this and just let MongoDB do it)
    user_id: string
    user_name: string*
    score: int
    combo: int
    accuracy: double*
    mod_val: int
    mods: [str, str, ...]*
    hits: {
        300_count: int
        100_count: int
        50_count: int
        miss_count: int
    }
    team_total: int*
    score_difference: int*
    map_id: string (int, not pool-map format)
    match_id: string
    match_name: string
    pool: string*
    stage: string*
}
* - is not provided by osu! api and must be calculated here

`Map` documents have the following fields:
{
    _id: str (/b is guaranteed to be unique)
    pool_id: str
    map_type: str (of NM, HD, HR, etc)
    map_url: str
    thumbnail_url: str
    meta:{
        map_artist: str
        map_song: str
        map_diff: str
        map_creator: str
        star_rating: decimal
        bpm: decimal
        drain_time: int
    }
}

`Player` documents have the following fields:
{
    _id: string (of user id; guaranteed to be unique)
    user_name: string
    team_name: string
    scores: [str, str, ...] (list of `Score` _id)
    cached:{**
        average_acc: double
        acc_rank: int
        average_score: double (to two decimals)
        score_rank: int
        average_contrib: double
        contrib_rank: int
        maps_played: int
        maps_won: int
        maps_lost: int
        hits: {
            300_count: int
            100_count: int
            50_count: int
            miss_count: int
        }
        1_miss_plays: int
        pfp_url: str
    }
}

`Team` documents have the following fields:
{
    _id: str (we are certain teams should never have the same name)
    players: [str, str, ...] (of player ids)
    cached:{**
        average_acc: double
        acc_rank: int
        average_score: double (to two decimals)
        score_rank: int
        average_contrib: double
        contrib_rank: int
    }
}

** - (re)calculated whenever a manual update occurs or a match is entered where they were a player
i don't know if i want to actually use these fields or just calcuate them as needed
will probably drop them if/when i decide the usage of this bot will probably be low enough

note that numbers that should not have numerical calculations performed
on them is a string, not an int as the data might suggest
"""
import motor.motor_asyncio
import pprint

import osuapi

#to implement pagination we can use cursor.skip()
#see https://docs.mongodb.com/manual/reference/method/cursor.skip/
#and https://stackoverflow.com/questions/57159663/mongodb-get-element-in-the-middle-of-a-find-sort-result-using-nodejs-native-driv
db_url = open("dburl").read()

client = motor.motor_asyncio.AsyncIOMotorClient(db_url)
db = client['test']
collection = db['test-data']

async def getval(value):
    """Get pymongo stuff ala motor"""
    document = await collection.find_one({'i': value})
    pprint.pprint(document)
    return document

async def setval(value):
    """Set pymongo stuff ala motor"""
    document = {'i': value}
    result = await collection.insert_one(document)
    print('result %s' % repr(result.inserted_id))
    return ("done")

#move to util, maybe?
#see https://stackoverflow.com/questions/38758668/grouping-functions-by-using-classes-in-python
async def add_meta(meta_data):
    """"""
    db = client['tournament_data']
    collection = db['meta']

    print(meta_data)
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
    
    current_collection = None
    current_pool = []
    current_pool_name = ""
    for map in pool_data:
        if map[0] != '':
            #this signifies that we are on a new mappool
            #we expect the first map to always have an identifier
            collection = db['meta']
            pool_meta = map[0].split(", ")
            pool_long = pool_meta[0]
            pool_short = pool_meta[1]

            document = {
                "_id": pool_short,
                "long_name": pool_long
            }
            await collection.insert_one(document)

            current_pool_name = pool_short
            current_collection = db[pool_short]
        #get and process map data
        map_data = await osuapi.get_map_data(map[1])
        #print(map_data)
        map_data = map_data[0]
        #note how we do not make any additional calculations to bpm or drain time
        #we can do that elsewhere, not here
        document = {
            '_id': map[1],
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
            }
        }
        await current_collection.insert_one(document)

async def add_players_and_teams(player_data):
    """Update the `tournament_data` database from `player_data`.
    
    *This function is not intended for updating existing players.*\n
    `player_data` is a list of teams and either player names or player IDs.
    Because the osu! API will automatically attempt to determine if the entered value
    is an ID or a username, there is no need to have validation or maintain
    a strict format. However, purely-numerical names may be more difficult to
    deal with.
    The list is in the format `[team_name, player_1, player_2, ...]`, all `str`.
    - `team_name` is a str of the team name. It is used as an _id and thus must be
    unique (as it should be).
    - `player_<n>` is a player associated with `team_name`. An individual document
    for each player is created in the `players` collection."""
    db = client['players_and_teams']
    team_collection = db['teams']
    player_collection = db['players']

    for team in player_data:
        #first, add the new team
        players = team[1:]
        player_data = [await osuapi.get_player_data(username) for username in players]
        player_ids = [player['user_id'] for player in player_data]
        team_document = {
            '_id': team[0],
            'players': players,
            'cached':{
                'average_acc': 0.00,
                'acc_rank': 0,
                'average_score': 0.00,
                'score_rank': 0,
                'average_contrib': 0.00,
                'contrib_rank': 0
            }
        }
        await team_collection.insert_one(team_document)
        #then iterate over each player id
        #really we don't do anything with player_data but at least you can expand it easily
        for player_index, player_id in enumerate(player_ids):
            player_document = {
                "_id": player_id,
                'user_name': player_data[player_index]['username'],
                'team_name': team[0],
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
            await player_collection.insert_one(player_document)
 
async def add_scores(matches_data):
    """"""
    pass

async def rebuild_all(sheet_id, ctx):
    """Drops ALL non-test databases, then rebuilds them using gsheet data."""
    databases = ['scores', 'mappools', 'players_and_teams', 'tournament_data']
    steps = 5
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

#gsheet functions
#ill figure out where to put this later

async def get_all_gsheet_data(sheet_id):
    #this WILL block the bot during execution
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
        'matches': 'matches!A2:E',
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