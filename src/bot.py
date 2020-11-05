"""Main bot script"""
import discord
from discord.ext import commands

import staff_commands
import match_commands
import user_commands

'''to do:

change db_manip to accept a list of maps to ignore, rather than just the first n
implement cards (render leaderboards, player stats, team stats, etc)
implement text stats (same as above but text-only)
/tmp for downloaded assets
deployment + integration with env vars
full match stats under match_commands.py
better help formatting w/ send_command_help(command) (see docs) - https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.HelpCommand.send_command_help
^needs examples
'''


#use environment variables for these later
token = open("token").read()

bot = commands.Bot(command_prefix=commands.when_mentioned_or("!!"))

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
    await ctx.send(f"The following error occurred: {exception}")
'''

bot.run(token)

