"""End-user commands for retrieving statistics and defining personal settings."""

import discord
from discord.ext import commands
import osuapi
import db_manip
import pprint

class UserConfigCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["setusers"])
    async def setuser(self, ctx, *, user):
        await ctx.send(user)

    @commands.command()
    async def setteam(self, ctx, *, team):
        await ctx.send(team)

    @commands.command()
    async def showconfigs(self, ctx):
        pass

    @commands.command()
    async def setconfig(self, ctx, config, value):
        pass

class UserStatsCommands(commands.Cog):
    #except for matches, of course...
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def playerstats(self, ctx, *, user="f"):
        await ctx.send(user)

    @commands.command()
    async def teamstats(self, ctx, *, user="f"):
        await ctx.send(user)

    @commands.command()
    async def playerbest(self, ctx, mod, *, user="f"):
        await ctx.send(user)
        await ctx.send(dog)

    @commands.command()
    async def teambest(self, ctx, mod, *, user="f"):
        await ctx.send(user)