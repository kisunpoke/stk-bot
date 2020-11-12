"""Async functions for generating and returning images.

Includes team/player card generation and image-based statistics as needed.
These functions only take documents to allow for validation at the command level.
"""
#https://stackoverflow.com/questions/33101935/convert-pil-image-to-byte-array
from PIL import Image, ImageFont, ImageDraw
import matplotlib.pyplot as plt
import io

import db_get
from utils import percentage, comma_sep
import image_handling

fonts = {
    "s": ImageFont.truetype("src/static/Renogare-Regular.otf", 20),
    "m": ImageFont.truetype("src/static/Renogare-Regular.otf", 27),
    "l": ImageFont.truetype("src/static/Renogare-Regular.otf", 40)
}

async def make_team_best(score_docs, current_page, max_page, mod_filter = None):
    """Generate and return a team score leaderboard(as a discord.py-compatible image).
    
    - `score_docs` is an array of score documents, 10 or fewer, of the team's scores.
    This should be found through `db_get.get_top_team_scores()` prior to calling this function.
    (This allows for mod filtering at the command level.)
    - `current_page` is the page from `db_get`.
    - `max_page` is also the max page from `db_get`.
    - `mod_filter` is the mod these documents are filtered by, if applicable.
    
    `current_page` and `max_page` are used solely for the page indicator in the upper-left of
    the image."""
    def draw_std(x, y, text, font="m"):
        #looool
        draw.text((x, y), str(text), (255, 255, 255), font=fonts[font], align='center', anchor="mm")

    def truncate(text, font="m"):
        """Truncates long strings to the desired max width and adds an ellipsis if needed."""
        max_width = 487

        font = fonts["m"]
        ellipsis_width, _ = font.getsize("...")

        width, _ = font.getsize(text)
        if width>max_width:
            while width>(max_width-ellipsis_width):
                text = text[:-1]
                width, _ = font.getsize(text)
            text += "..."
        return text

    player_card_base_img_fp = "src/static/teambest.png"
    img = Image.open(player_card_base_img_fp, mode='r')

    draw = ImageDraw.Draw(img)

    #header
    player_doc = await db_get.get_player_document(score_docs[0]["user_id"])
    team_doc = await db_get.get_team_document(player_doc["team_name"])
    player_names = [(await db_get.get_player_document(player))["user_name"] for player in team_doc["players"]]
    draw_std(640, 65, team_doc["_id"], "l") #team name
    draw_std(640, 105, " • ".join(player_names)) #player list

    #page number
    page_text = f"(page {current_page} of {max_page})" 
    if mod_filter:
        page_text += f" ({mod_filter})"
    draw.text((36, 137), page_text, (255, 255, 255), font=fonts["s"], align='left', anchor="lm")

    colors = {
        "NM":(165,165,165),
        "HD":(255,192,0),
        "HR":(255,0,0),
        "DT":(0,176,240),
        "FM":(146,208,80),
        "TB":(146,208,80)
    }
    #table
    #x-dists: 70,116(left),266,876,1035,1172
    #y-dist: 39 each row
    for row, score in enumerate(score_docs):
        map_doc = await db_get.get_map_document(score["diff_id"])

        banner_fp = await image_handling.get_banner_fp(map_doc["set_id"])
        banner = Image.open(banner_fp, mode='r')
        banner = banner.resize((139,37))

        y_pos = (row*39)+216

        draw_std(76, y_pos, (current_page-1)*10+row+1) #numerical ranking
        draw_std(267, y_pos, score["user_name"]) #player name
        #tuple refers to top-left corner, so half the banner's height is subtracted
        img.paste(banner, (406,y_pos-19)) #map banner
        draw.line([546,y_pos-19,546,y_pos+19], colors[score["map_type"]], 5) #modline
        meta = map_doc["meta"]
        full_name = meta["map_artist"]+" - "+meta["map_song"]+" ["+meta["map_diff"]+"]"
        draw.text((556, y_pos), truncate(full_name), (255, 255, 255), font=fonts["m"],
                   align='left', anchor="lm") #map name

        draw_std(1160, y_pos, comma_sep(score["score"])) #score

    img_binary = io.BytesIO()
    img.save(img_binary, 'PNG')
    img_binary.seek(0)
    return img_binary

async def make_team_card(team_doc):
    """Generate and return a team card (as a discord.py-compatible image) based on a team document.
    
    - `team_doc` is a team document."""
    def draw_std(x, y, text, font="m"):
        #looool
        draw.text((x, y), str(text), (255, 255, 255), font=fonts[font], align='center', anchor="mm")
    stat = team_doc['cached']

    player_card_base_img_fp = "src/static/teamcard.png"
    img = Image.open(player_card_base_img_fp, mode='r')
    draw = ImageDraw.Draw(img)

    #header
    '''
    players_str = ""
    for player in team_doc["players"]:
        player_name = (await db_get.get_player_document(player))["user_name"]
        players_str += player_name+" • "
    players_str = players_str[:-3] #cut excess bullet point and spaces
    '''
    #same as above, but this is how it originally was before i wrote tb/pb
    player_names = [(await db_get.get_player_document(player))["user_name"] for player in team_doc["players"]]
    draw_std(640, 65, team_doc["_id"], "l") #team name
    draw_std(640, 105, " • ".join(player_names)) #players, bullet-separated

    #average accuracy
    draw_std(335, 218, percentage(stat['average_acc'])) #accuracy value
    draw_std(335, 245, "#"+str(stat["acc_rank"]), "s") #accuracy rank

    #average score
    draw_std(945, 218, comma_sep(stat['average_score'])) #score value
    draw_std(945, 245, "#"+str(stat["score_rank"]), "s") #score rank

    #stat row
    draw_std(104, 335, stat['maps_played']) #playcount
    if stat['maps_played'] != 0:
        wr_str = str(stat["maps_won"])+"/"+str(stat['maps_lost'])+" ("+percentage(stat["maps_won"]/stat["maps_played"])+")"
    else:
        wr_str = "-"
    draw_std(311, 335, wr_str) #w/r(wr%)
    draw_std(742, 335, comma_sep(stat["hits"]["300_count"])) #300s
    draw_std(886, 335, comma_sep(stat["hits"]["100_count"])) #100s
    draw_std(1028, 335, comma_sep(stat["hits"]["50_count"])) #50s
    draw_std(1173, 335, comma_sep(stat["hits"]["miss_count"])) #misss

    #table
    #x-dists: 180,345,548,702,840
    #y-dist: 39 each row starting from 565
    mods = ["NM", "HD", "HR", "DT", "FM"]
    for i in range(0,5):
        row_pos = 526 + 39*i
        mod_stat = stat["by_mod"][mods[i]]
        draw_std(180, row_pos, mod_stat["maps_played"]) #played
        if mod_stat["maps_played"] != 0:
            mod_wr_str = str(mod_stat["maps_won"])+"/"+str(mod_stat['maps_lost'])+" ("+percentage(mod_stat["maps_won"]/mod_stat["maps_played"])+")"
        else:
            mod_wr_str = "-"
        draw_std(345, row_pos, mod_wr_str) #w/l (wr%)
        draw_std(548, row_pos, comma_sep(mod_stat["average_score"])) #average score
        draw_std(702, row_pos, percentage(mod_stat["average_acc"])) #average acc
        draw_std(840, row_pos, "-")#average contrib - unused for teams

    #pie chart
    #note: iterating over stat["by_mod"] works because dicts are insertion-ordered in python
    #since in db_manip we insert them in a certain order
    #otherwise the colors would be wrong if, for example, stat["by_mod"] returned the mod names
    #alphabetically ordered
    #you may want to hardcode the mod list instead of using stat["by_mod"] if the colors are jank
    if stat["maps_played"] != 0:
        data = [stat["by_mod"][mod_name]["maps_played"] for mod_name in stat["by_mod"]]
        colors = ["#A5A5A5", "#FFC000", "#FF0000", "#00B0F0", "#92D050"]

        fig1, ax1 = plt.subplots(figsize=(3.5, 3.5)) #default is 100dpi, so 350px by 350px
        ax1.pie(data, colors=colors)
        ax1.axis('equal')

        #to binary and into pillow
        #https://stackoverflow.com/questions/8598673/how-to-save-a-pylab-figure-into-in-memory-file-which-can-be-read-into-pil-image/8598881
        plt_binary = io.BytesIO()
        plt.savefig(plt_binary, format='png', transparent=True)
        plt_binary.seek(0)
        plt_img = Image.open(plt_binary)

        #https://stackoverflow.com/questions/5324647/how-to-merge-a-transparent-png-image-with-another-image-using-pil
        #the alpha channel is used as the mask; transparent=True parameter actually saves as transparent
        img.paste(plt_img, (918, 382), plt_img)

    #you need to seek to 0 for it to work:
    #solution from here: #https://stackoverflow.com/questions/63209888/send-pillow-image-on-discord-without-saving-the-image
    #file-like object
    img_binary = io.BytesIO()
    img.save(img_binary, 'PNG')
    img_binary.seek(0)
    return img_binary

async def make_player_best(score_docs, current_page, max_page, mod_filter = None):
    """Generate and return a player score leaderboard (as a discord.py-compatible image).
    
    - `score_docs` is an array of score documents, 10 or fewer, of the player's scores.
    This should be found through `db_get.get_top_player_scores()` prior to calling this function.
    (This allows for mod filtering at the command level.)
    - `current_page` is the page from `db_get`.
    - `max_page` is also the page from `db_get`.
    - `mod_filter` is the mod these documents are filtered by, if applicable.
    
    `current_page` and `max_page` are used solely for the page indicator in the upper-left of
    the image."""
    def draw_std(x, y, text, font="m"):
        #looool
        draw.text((x, y), str(text), (255, 255, 255), font=fonts[font], align='center', anchor="mm")

    def truncate(text, font="m"):
        """Truncates long strings to the desired max width and adds an ellipsis if needed."""
        max_width = 510

        font = fonts["m"]
        ellipsis_width, _ = font.getsize("...")

        width, _ = font.getsize(text)
        if width>max_width:
            while width>(max_width-ellipsis_width):
                #repeatedly cut off characters until we can shove the ellipsis in 
                text = text[:-1]
                width, _ = font.getsize(text)
            text += "..."
        return text
    player_card_base_img_fp = "src/static/playerbest.png"
    img = Image.open(player_card_base_img_fp, mode='r')

    draw = ImageDraw.Draw(img)

    #header
    player_doc = await db_get.get_player_document(score_docs[0]["user_id"])
    draw_std(640, 65, player_doc["user_name"], "l") #player
    draw_std(640, 105, player_doc["team_name"]) #team name

    #page number
    page_text = f"(page {current_page} of {max_page})" 
    if mod_filter:
        page_text += f" ({mod_filter})"
    draw.text((36, 137), page_text, (255, 255, 255), font=fonts["s"], align='left', anchor="lm")

    colors = {
        "NM":(165,165,165),
        "HD":(255,192,0),
        "HR":(255,0,0),
        "DT":(0,176,240),
        "FM":(146,208,80),
        "TB":(146,208,80)
    }
    #table
    #x-dists: 70,116(left),266,876,1035,1172
    #y-dist: 39 each row, starting from 216
    for row, score in enumerate(score_docs):
        map_doc = await db_get.get_map_document(score["diff_id"])

        banner_fp = await image_handling.get_banner_fp(map_doc["set_id"])
        banner = Image.open(banner_fp, mode='r')
        banner = banner.resize((139,37))

        y_pos = (row*39)+216

        draw_std(70, y_pos, (current_page-1)*10+row+1) #numerical ranking
        
        #tuple refers to top-left corner, so half the banner's height is subtracted
        img.paste(banner, (117,y_pos-19)) #map banner
        draw.line([257,y_pos-19,257,y_pos+19], colors[score["map_type"]], 5) #modline
        meta = map_doc["meta"]
        full_name = meta["map_artist"]+" - "+meta["map_song"]+" ["+meta["map_diff"]+"]"
        draw.text((267, y_pos), truncate(full_name), (255, 255, 255), font=fonts["m"],
                   align='left', anchor="lm") #map name

        draw_std(876, y_pos, comma_sep(score["score"])) #score
        draw_std(1035, y_pos, percentage(score["accuracy"])) #acc
        draw_std(1172, y_pos, comma_sep(score["combo"])+"x") #combo

    img_binary = io.BytesIO()
    img.save(img_binary, 'PNG')
    img_binary.seek(0)
    return img_binary

async def make_player_card(player_doc):
    """Generate and return a team card (as a discord.py-compatible image).
    
    - `player_doc` is a player document."""
    def draw_std(x, y, text, font="m"):
        #looool
        draw.text((x, y), str(text), (255, 255, 255), font=fonts[font], align='center', anchor="mm")
    stat = player_doc['cached']
    
    player_card_base_img_fp = "src/static/playercard.png"
    img = Image.open(player_card_base_img_fp, mode='r')

    draw = ImageDraw.Draw(img)

    #header
    draw_std(640, 65, player_doc["user_name"], "l") #player
    draw_std(640, 105, player_doc["team_name"]) #team name

    #average accuracy
    draw_std(185, 218, percentage(stat["average_acc"]))
    draw_std(185, 245, "#"+str(stat["acc_rank"]), "s")

    #average score
    draw_std(640, 218, comma_sep(stat["average_score"]))
    draw_std(640, 245, "#"+str(stat["score_rank"]), "s")

    #average contrib
    draw_std(1106, 218, percentage(stat["average_contrib"]))
    draw_std(1106, 245, "#"+str(stat["contrib_rank"]), "s")

    #stat row
    draw_std(104, 335, stat['maps_played']) #playcount
    if stat['maps_played'] != 0:
        wr_str = str(stat["maps_won"])+"/"+str(stat['maps_lost'])+" ("+percentage(stat["maps_won"]/stat["maps_played"])+")"
    else:
        wr_str = "-"
    draw_std(311, 335, wr_str) #w/r(wr%)
    draw_std(742, 335, comma_sep(stat["hits"]["300_count"])) #300s
    draw_std(886, 335, comma_sep(stat["hits"]["100_count"])) #100s
    draw_std(1028, 335, comma_sep(stat["hits"]["50_count"])) #50s
    draw_std(1173, 335, comma_sep(stat["hits"]["miss_count"])) #misss

    #table
    #x-dists: 180,345,548,702,840
    #y-dist: 39 each row starting from 526
    mods = ["NM", "HD", "HR", "DT", "FM"]
    for i in range(0,5):
        row_pos = 526 + 39*i
        mod_stat = stat["by_mod"][mods[i]]
        draw_std(180, row_pos, mod_stat["maps_played"]) #played
        if mod_stat["maps_played"] != 0:
            mod_wr_str = str(mod_stat["maps_won"])+"/"+str(mod_stat['maps_lost'])+" ("+percentage(mod_stat["maps_won"]/mod_stat["maps_played"])+")"
        else:
            mod_wr_str = "-"
        draw_std(345, row_pos, mod_wr_str) #w/l (wr%)
        draw_std(548, row_pos, comma_sep(mod_stat["average_score"])) #average score
        draw_std(702, row_pos, percentage(mod_stat["average_acc"])) #average acc
        draw_std(840, row_pos, percentage(mod_stat["average_contrib"]))#average contrib - unused for teams

    #pie chart
    #note: iterating over stat["by_mod"] works because dicts are insertion-ordered in python
    #since in db_manip we insert them in a certain order
    #otherwise the colors would be wrong if, for example, stat["by_mod"] returned the mod names
    #alphabetically ordered
    #you may want to hardcode the mod list instead of using stat["by_mod"] if the colors are jank
    if stat['maps_played'] != 0:
        data = [stat["by_mod"][mod_name]["maps_played"] for mod_name in stat["by_mod"]]
        colors = ["#A5A5A5", "#FFC000", "#FF0000", "#00B0F0", "#92D050"]

        fig1, ax1 = plt.subplots(figsize=(3.5, 3.5)) #default is 100dpi, so 350px by 350px
        ax1.pie(data, colors=colors)
        ax1.axis('equal')

        #to binary and into pillow
        #https://stackoverflow.com/questions/8598673/how-to-save-a-pylab-figure-into-in-memory-file-which-can-be-read-into-pil-image/8598881
        plt_binary = io.BytesIO()
        plt.savefig(plt_binary, format='png', transparent=True)
        plt_binary.seek(0)
        plt_img = Image.open(plt_binary)

        #https://stackoverflow.com/questions/5324647/how-to-merge-a-transparent-png-image-with-another-image-using-pil
        #the alpha channel is used as the mask; transparent=True parameter actually saves as transparent
        img.paste(plt_img, (918, 382), plt_img)

    #you need to seek to 0 for it to work:
    #solution from here: #https://stackoverflow.com/questions/63209888/send-pillow-image-on-discord-without-saving-the-image
    #file-like object
    img_binary = io.BytesIO()
    img.save(img_binary, 'PNG')
    img_binary.seek(0)
    return img_binary

async def make_map_best(score_docs, current_page, max_page, player_score = None):
    """Generate and return a map leaderboard (as a discord.py-compatible image).
    
    - `score_docs` is an array of score documents, 10 or fewer, of the map's scores.
    This should be found through `db_get.get_top_map_scores()` prior to calling this function.
    - `current_page` is the page from `db_get`.
    - `max_page` is also the page from `db_get`.
    - `player_score` should be the best score document of the command invoker on this map,
    if applicable.
    
    `current_page` and `max_page` are used solely for the page indicator in the upper-left of
    the image."""
    pass

async def make_score_best(score_docs, current_page, max_page, mod_filter = None):
    """Generate and return the best scores of the tournament as an image.
    
    - `score_docs` is an array of score documents, 10 or fewer, of the best scores.
    This should be found through `db_get.get_top_team_scores()` prior to calling this function.
    - `current_page` is the page from `db_get`.
    - `max_page` is also the page from `db_get`.
    
    `current_page` and `max_page` are used solely for the page indicator in the upper-left of
    the image."""
    pass

async def make_averagep_best(player_docs, current_page, max_page, category, invoker_doc=None):
    """Generate and return the best players of the tournament in a certain category as an image.
    
    - `player_docs` is an array of player documents, 10 or fewer, of the map's scores.
    This should be found through `db_get.get_top_team_scores()` prior to calling this function.
    - `current_page` is the page from `db_get`.
    - `max_page` is also the page from `db_get`.
    - `category` should be the leaderboard category.
    - `invoker_doc` should be the player document of the command invoker, if applicable.
    
    `current_page` and `max_page` are used solely for the page indicator in the upper-left of
    the image."""
    pass

async def make_averaget_best(team_docs, current_page, max_page, category, invoker_doc=None):
    """Generate and return the best teams of the tournament in a certain category as an image.
    
    - `team_docs` is an array of player documents, 10 or fewer, of the map's scores.
    This should be found through `db_get.get_top_team_scores()` prior to calling this function.
    - `current_page` is the page from `db_get`.
    - `max_page` is also the page from `db_get`.
    - `category` should be the leaderboard category.
    - `invoker_doc` should be the team document of the command invoker, if applicable.
    
    `current_page` and `max_page` are used solely for the page indicator in the upper-left of
    the image."""
    pass