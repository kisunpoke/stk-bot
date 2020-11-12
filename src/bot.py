"""Main bot script"""
import discord
from discord.ext import commands

import os
#checks if in development or deployment
#config var on heroku is on_heroku=TRUE
#os.getenv() instead of os.environ[] because using os.environ will return KeyError, getenv() returns None
if os.getenv("on_heroku") != "TRUE":
    from dotenv import load_dotenv
    load_dotenv(dotenv_path="main.env")

import general_commands
import staff_commands
import match_commands
import user_commands

import prompts

'''to do:

pp/rank from most recent update
^leaderboard?
update only players/mappool/meta etc
match adding
full match stats under match_commands.py
implement cards (render leaderboards, player stats, team stats, etc)
implement text stats (same as above but text-only) #https://discordpy.readthedocs.io/en/latest/faq.html#how-do-i-use-a-local-image-file-for-an-embed-image for histograms and others
for leaderboards, show where the user stands on any given page
argparser for UserStatsCommands
list of pools?
proper error handling
make roles and other things not hardcoded
proper admin help
admin commands

teamcard
playercard
teamstats
playerstats
mapbest
maplb

'''

token = os.getenv("bot_token")

bot = commands.Bot(command_prefix=commands.when_mentioned_or("!!"))

bot.remove_command('help')

bot.add_cog(general_commands.GeneralCommands(bot))
bot.add_cog(staff_commands.AdminDatabaseCommands(bot))
bot.add_cog(staff_commands.StaffCommands(bot))
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
    await prompts.error_embed(bot, ctx, f"The following error occurred: {exception}")
'''

bot.run(token)

