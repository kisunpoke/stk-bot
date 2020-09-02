import discord
from discord.ext import commands
import random


class Greetings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def hello(self, ctx):
        """Says hello"""
        await ctx.send('smh')

    @commands.command()
    async def getvals(self, ctx):
        """Get pymongo stuff ala motor"""
        pass

    @commands.command()
    async def maplbex(self, ctx):
        embed = discord.Embed(title='Leaderboards')
        embed.set_thumbnail(url="https://b.ppy.sh/thumb/70257l.jpg")
        embed.set_author(name='Leaderboards for nano - Exist [Existence]',url="https://osu.ppy.sh/beatmapsets/70257#osu/202072")
        rank = ""
        player = ""
        combo = ""
        acc = ""
        score = ""
        hits = ""
        '''
        for i in range(0,8):
            rank += str(i) + "\n"
            player += "player %s\n"%i
            combo += "{:,}".format(random.randint(0,1000)) + "\n"
            acc += str(random.randint(0,10000)/100)+"\n"
            score += "{:,}".format(random.randint(0,1000000))+"\n"
            hits += "1000/00/00/00\n"
        '''
        player += "Score (rank) • Acc\n"
        combo += "Pool - ID\n"
        acc += "Match - Index\n"
        for i in range(0,8):
            player += "1,000,000 (**#5**) • 100.00%\n"
            combo += "GF - NM1\n"
            acc += "61234562 - 4\n"
        #embed.add_field(name='#', value=rank, inline=True)    
        embed.add_field(name='Player', value=player, inline=True)
        embed.add_field(name='Combo', value=combo, inline=True)
        embed.add_field(name='Acc', value=acc, inline=True)
        #embed.add_field(name='Score', value=score, inline=True)
        #embed.add_field(name='Hits', value=hits, inline=True)
        embed.set_footer(text="Use !!map Q NM1 stats for general map stats.")
        await ctx.channel.send(ctx.message.channel, embed=embed)