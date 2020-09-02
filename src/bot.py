#region Imports
import discord
from discord.ext import commands

from aaaa import Greetings

import motor.motor_asyncio
#endregion

#region initialization

#use environment variables for these later
token = open("token").read()
api_key = open("osukey").read()
db_url = open("dburl").read()

bot = commands.Bot(command_prefix='!!')

bot.add_cog(Greetings(bot))
#endregion

#region mongodb testing
client = motor.motor_asyncio.AsyncIOMotorClient(db_url)
db = client['test']
collection = db['test-data']
@bot.command()
async def getval(ctx, value):
    """Get pymongo stuff ala motor"""
    document = await collection.find_one({'i': value})
    import pprint
    pprint.pprint(document)

@bot.command()
async def setval(ctx, value):
    """Set pymongo stuff ala motor"""
    document = {'i': value}
    result = await collection.insert_one(document)
    print('result %s' % repr(result.inserted_id))
#endregion

@bot.event
async def on_ready():
    print('ready!')

@bot.command(pass_context=True)
async def test(ctx,page=None):
    if page:
        await ctx.channel.send(f'{page} requested.')
    else:
        await ctx.channel.send("Default requested.")

bot.run(token)

