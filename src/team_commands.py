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

    @commands.command()
    async def card(self, ctx, player):
        """Generate and return a player card (as a direct image)."""
        img = Image.open("src/static/black.png", mode='r') #Replace infoimgimg.png with your background image.

        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("src/static/Nunito-Regular.ttf", 100) #Make sure you insert a valid font from your folder.
        draw.text((200, 0), "Information:", (255, 255, 255), font=font) #draws Information
        #this just did not work
        #i guess you have to seek before you actually do the thing
        #solution from here: #https://stackoverflow.com/questions/63209888/send-pillow-image-on-discord-without-saving-the-image
        #imgByteArr = io.BytesIO()
        #img.save(imgByteArr, format='PNG')
        #imgByteArr = imgByteArr.getvalue()
        #print(imgByteArr)
        with io.BytesIO() as img_binary:
            img.save(img_binary, 'PNG')
            img_binary.seek(0)
            await ctx.send(file=discord.File(fp=img_binary, filename='player_card.png'))

    @commands.command()
    async def efa(self, ctx, player):
        """Generate and return a player card (as a direct image)."""
        
        img = Image.open("src/static/black.png", mode='r') #Replace infoimgimg.png with your background image.
        imgByteArr = io.BytesIO()
        img.save(imgByteArr, format='PNG')
        imgByteArr = imgByteArr.getvalue()
        #print()
        print(imgByteArr)
        #await ctx.send("done")
        await ctx.send(file=discord.File(imgByteArr, "player_card.png"))