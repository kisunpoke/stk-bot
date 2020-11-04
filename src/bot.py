"""Main bot script"""
import discord
from discord.ext import commands

import admin_commands
import match_commands
import user_commands

'''timeline:


implement per-mod cached

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

bot = commands.Bot(command_prefix=commands.when_mentioned_or("!!"))

bot.add_cog(admin_commands.AdminDatabaseCommands(bot))
bot.add_cog(match_commands.MatchCommands(bot))
bot.add_cog(user_commands.UserConfigCommands(bot))
bot.add_cog(user_commands.UserStatsCommands(bot))

@bot.event
async def on_ready():
    print('ready!')

'''
@bot.event
async def on_command_error(ctx, exception):
    #check the exception type - command not found, params incorrect, runtime error, etc.
    print(exception)
    await ctx.send(f"The following error occurred: {exception}")
'''

bot.run(token)

