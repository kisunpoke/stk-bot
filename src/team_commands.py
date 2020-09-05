"""Team and player bot commands/cogs."""

import discord
from discord.ext import commands
import random
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
#https://stackoverflow.com/questions/33101935/convert-pil-image-to-byte-array
import io

class PlayerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def best(self, ctx, player, page=1, mods=None):
        """Return the player's sorted best scores, 10 per page, filtered by mods if defined.
        
        The returned scores are equal to `(1+(page-1)*10)` to `page*10`.
        (1 to 10, 11 to 20, ...)\n
        `mods` is a `str` - `"NM"`, `"HR"`, `"HD"`, etc. 
        """
        #get player's score ids via db_manip...
        #get player's actual scores via db_manip (filtered, sorted, and skipped)
        #construct embed here
        await ctx.send('unimplemented')

    @commands.command()
    async def stats(self, ctx, player):
        """Return miscellaneous stats on a player."""
        #get player's score ids via db_manip...
        #get player's actual scores via db_manip
        '''
        STK8 Statistics for <player>
        #General
        Average Score: <val> *#1)
        Average Accuracy: <val> (#1)
        Average Team Contribution%: <val> (#1)
        #Score stats
        Maps played: val
        Map wins|losses: val|val (12.24% winrate)
        Hits: 1/1/1/1
        1,000,000+: 1
        Average difference (win): 43434
        Best score: 1,000,000 on <map_name_as_hyperlink>
        Worst score: 0 on <map_name_as_hyperlink> OR (pool-mapid: matchid)
        #Best scores:
        inline of Score - full_map_name
        #(footer)
        use !!best <player> for more scores, or !!card <player> for a player card
        '''
        pass