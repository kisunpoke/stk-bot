"""General commands."""
#maybe help embed stuff?

import discord

async def help_generator(command):
    """Make the embed thing that's a pain to make or something
    
    Returns the embed itself, but doesn't send it."""
    info = help[command]
    embed = discord.Embed(description=info["signature"]+"\n"+info["summary"])

    embed.set_footer(text=f"help for {command} | i'm trying")

    embed.add_field(name="Parameters", value=info["parameters"], inline=False)
    embed.add_field(name="Examples", value=info["examples"], inline=False)
    return embed

#unfortunate
#mark is ok below
help = {
    "getmatch":{
        "signature": ("**getmatch** <match_id> [map_index]"),
        "summary":   ("*Get score and statistics data for a match.*"),
        "parameters":(" - *match_id*: /mp link provided by osu!\n"
                      " - *map_index (optional)*: The map index. If not defined, then statistics for the entire match are posted. If defined, then statistics for the nth map are given."),
        "examples":  (" - `getmatch 59424609`: gets general match statistics for the match at https://osu.ppy.sh/mp/59424609\n"
                      " - `getmatch 59424609 2`: gets statistics for the second map played on the same multiplier lobby")
    }
}