"""Async functions for generating and returning images.

Includes team/player card generation and image-based statistics as needed.
"""
#https://stackoverflow.com/questions/33101935/convert-pil-image-to-byte-array
from PIL import Image, ImageFont, ImageDraw
import io

import db_get

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
    """Generate and return a player card (as a discord.py-compatible image).
    
    `data` is a map containing the following information:
    ```
    {
        player_name: str,
    }
    ```"""
    def draw_std(x, y, text, font="m"):
        #looool
        draw.text((x, y), text, (255, 255, 255), font=fonts[font], align='center', anchor="mm")

    player_card_base_img_fp = "src/static/team-bg.png"
    img = Image.open(player_card_base_img_fp, mode='r')

    draw = ImageDraw.Draw(img)

    #header
    draw_std(640, 65, "Player 1, player 23  oife", "l")
    draw_std(640, 105, "Player 1, player 23  oife")

    #average accuracy
    draw_std(335, 218, "Player 1, player 23  oife")
    draw_std(335, 245, "Player 1, player 23  oife", "s")

    #average score
    draw_std(945, 218, "Player 1, player 23  oife")
    draw_std(945, 245, "Player 1, player 23  oife", "s")

    #stat row
    draw_std(104, 335, "9,999")
    draw_std(311, 335, "9,999")
    draw_std(742, 335, "9,999")
    draw_std(886, 335, "9,999")
    draw_std(1028, 335, "9,999")
    draw_std(1173, 335, "9,999")

    #table
    #x-dists: 180,345,548,702,840
    #y-dist: 39 each row
    for row_pos in range(526, 721, 39):
        draw_std(180, row_pos, "9,999")
        draw_std(345, row_pos, "9,999")
        draw_std(548, row_pos, "9,999")
        draw_std(702, row_pos, "9,999")
        draw_std(840, row_pos, "9,999")

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