"""Async functions for generating and returning images.

Includes team/player card generation and image-based statistics as needed.
"""
#https://stackoverflow.com/questions/33101935/convert-pil-image-to-byte-array
from PIL import Image, ImageFont, ImageDraw
import io

import db_get
from utils import percentage, comma_sep

fonts = {
    "s": ImageFont.truetype("src/static/Renogare-Regular.otf", 20),
    "m": ImageFont.truetype("src/static/Renogare-Regular.otf", 27),
    "l": ImageFont.truetype("src/static/Renogare-Regular.otf", 40)
}

'''
async def make_player_card(player):
    """Generate and return a player card (as a direct image)."""
    img = Image.open(player_card_base_img_fp, mode='r')

    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("src/static/Nunito-Regular.ttf", 100)
    draw.text((200, 0), "Information:", (255, 255, 255), font=font)
    #i guess you have to seek before you actually do the thing
    #solution from here: #https://stackoverflow.com/questions/63209888/send-pillow-image-on-discord-without-saving-the-image
    with io.BytesIO() as img_binary:
        img.save(img_binary, 'PNG')
        img_binary.seek(0)
        return img_binary
'''

async def make_team_card(team_doc):
    #note: team_doc has no implementation
    #team_doc is not found here to allow for validation at the command level
    """Generate and return a team card (as a discord.py-compatible image) based on a team document."""
    def draw_std(x, y, text, font="m"):
        #looool
        draw.text((x, y), str(text), (255, 255, 255), font=fonts[font], align='center', anchor="mm")

    stat = team_doc['cached']

    player_card_base_img_fp = "src/static/team-bg.png"
    img = Image.open(player_card_base_img_fp, mode='r')
    draw = ImageDraw.Draw(img)

    #header
    players_str = ""
    for player in team_doc["players"]:
        player_name = (await db_get.get_player_document(player))["user_name"]
        players_str += player_name+" • "
    players_str = players_str[:-3] #cut excess bullet point and spaces
    draw_std(640, 65, team_doc["_id"], "l") #team name
    draw_std(640, 105, players_str) #players, bullet-separated

    #average accuracy
    draw_std(335, 218, percentage(stat['average_acc'])) #accuracy value
    draw_std(335, 245, "#"+str(stat["acc_rank"]), "s") #accuracy rank

    #average score
    draw_std(945, 218, comma_sep(stat['average_score'])) #score value
    draw_std(945, 245, "#"+str(stat["score_rank"]), "s") #score rank

    #stat row
    draw_std(104, 335, stat['maps_played']) #playcount
    wr_str = str(stat["maps_won"])+"/"+str(stat['maps_lost'])+" ("+percentage(stat["maps_won"]/stat["maps_played"])+")"
    draw_std(311, 335, wr_str) #w/r(wr%)
    draw_std(742, 335, comma_sep(stat["hits"]["300_count"])) #300s
    draw_std(886, 335, comma_sep(stat["hits"]["100_count"])) #100s
    draw_std(1028, 335, comma_sep(stat["hits"]["50_count"])) #50s
    draw_std(1173, 335, comma_sep(stat["hits"]["miss_count"])) #misss

    #table
    #x-dists: 180,345,548,702,840
    #y-dist: 39 each row starting from 565
    row_pos = [526, 565, 604, 643, 682]
    mods = ["NM", "HD", "HR", "DT", "FM"]
    for i in range(0,5):
        mod_stat = stat["by_mod"][mods[i]]
        draw_std(180, row_pos[i], mod_stat["maps_played"]) #played
        mod_wr_str = wr_str = str(mod_stat["maps_won"])+"/"+str(mod_stat['maps_lost'])+" ("+percentage(mod_stat["maps_won"]/mod_stat["maps_played"])+")"
        draw_std(345, row_pos[i], mod_wr_str) #w/l (wr%)
        draw_std(548, row_pos[i], comma_sep(mod_stat["average_score"])) #average score
        draw_std(702, row_pos[i], percentage(mod_stat["average_acc"])) #average acc
        draw_std(840, row_pos[i], "-")#average contrib - unused for teams

    #right plot
    #unimp.

    #i guess you have to seek before you actually do the thing
    #solution from here: #https://stackoverflow.com/questions/63209888/send-pillow-image-on-discord-without-saving-the-image
    #file-like object
    img_binary = io.BytesIO()
    img.save(img_binary, 'PNG')
    img_binary.seek(0)
    return img_binary

'''
async def make_player_best(player, data):
    """Generate and return a player score leaderboard (as a discord.py-compatible image)."""
    pass

async def make_team_card(player, data):
    """Generate and return a team card (as a discord.py-compatible image)."""
    pass

async def make_team_best(player, data):
    """Generate and return a team score leaderboard(as a discord.py-compatible image)."""
    pass

async def make_map_best(player, data):
    """Generate and return a map leaderboard (as a discord.py-compatible image_."""
    pass

async def make_map_card(player, data):
    """Generate and return a map stats card (as a discord.py-compatible image)."""
    pass
'''