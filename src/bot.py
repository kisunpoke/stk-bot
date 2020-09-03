"""Main bot script"""
import discord
from discord.ext import commands

from aaaa import Greetings
import admin_commands
import match_commands
import team_commands

#use environment variables for these later
token = open("token").read()
api_key = open("osukey").read()

bot = commands.Bot(command_prefix='!!')

bot.add_cog(Greetings(bot))
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

