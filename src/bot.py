"""Main bot script"""
import discord
from discord.ext import commands

import admin_commands
import match_commands
import team_commands

'''timeline:

link gsheets
update and generate player forms from sheeted teams+players - admin
update and generate mappool db from sheeted pool fields - admin
get test data from stk6

(won't wrap the above in async since they should rarely be called and must always be run before anything else happens)

score document generation from list of match ids
ability to hold session prefs (current mappool, image generation disabled, scorewatch interval)
implement player text stats and scores
team text stats and scores
player card?
image version of player scores
team card?
image version of team scores
map stats (text)
matplot score histogram
map leaderboard (text)
map stats (image)
map leaderboard(image)
match game (text), per individual map
match stats (text), overall match details
'''


#use environment variables for these later
token = open("token").read()

bot = commands.Bot(command_prefix='!!')

bot.add_cog(team_commands.PlayerCommands(bot))
bot.add_cog(admin_commands.AdminDatabaseCommands(bot))

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

