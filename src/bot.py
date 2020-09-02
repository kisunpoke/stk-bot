import discord
from discord.ext import commands

#oops lol
token = open("token").read()
api_key = open("osukey").read()

bot = commands.Bot(command_prefix='!!')

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

