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
    -tournament_data
        -players: collection of `Player` documents
        -teams: collection of `Team` documents

`Score` documents have the following fields:
{
    _id: string (of format "<user_id>-<timestamp>")
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
    map_id: str
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
    scores: [str, str, ...] (list of `Score` _id)
    cached:{**
        average_acc: double
        acc_rank: int
        average_score: double (to two decimals)
        score_rank: int
        average_contrib: double
        contrib_rank: int
        best_score: str (of `Score` _id)
        worst_score: str (of `Score` _id)
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
    name: str
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