"""Match-related commands/cogs."""

import discord
from discord.ext import commands

async def get_individual_match_data(match_id, map, data=None):
    """Returns a dict of match data tailored for generating match embeds for `getmatch()`.
    
    `data` is expected to be the original JSON response, and is used in lieu of 
    calling the osu! API. Otherwise, `match_id` is used to get match data, then the nth
    `map` (zero-indexed) is obtained and statcrunched.
    ```
    Returns the following dict:
    {
        "match_name": str,
        "match_url": f'https://osu.ppy.sh/community/matches/{match_id}',
        "diff_id": str,
        "diff_url": f'https://osu.ppy.sh/b/{diff_id}',
        "map_thumbnail": f'https://b.ppy.sh/thumb/{diff_id}l.jpg',
        "map_name": f'{artist} - {title}',
        "winner": str (1 or 2),
        "score_difference": float,
        "team_1_score": int,
        "team_2_score": int, 
        "team_1_score_avg": float,
        "team_2_score_avg": float,
        "embed_friendly": <a long str>,
        "footer": str
        "individual_scores": [
            {
                "user_id": str,
                "user_name": str,
                "score": int,
                "combo": int,
                "accuracy": float,
                "mod_val": int,
                "mods": [str, str, ...],
                "hits": {
                    "300_count": int,
                    "100_count": int,
                    "50_count": int,
                    "miss_count": int
                },
                "team": str (1 or 2)
                "team_contrib": float
            }, ...
        ]
    }
    ```
    """
    pass

async def get_list_of_matches(match_id):
    """Returns a newline, numbered list of the first 20 matches played in a lobby."""
    pass

class MatchCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def getmatch(self, ctx, match, map=1):
        """Get score and statistics data for the nth map of a match."""
        pass

    @commands.command()
    async def trackmatch(self, ctx, match, map=1):
        """Start tracking a match, returning embeds similar to `getmatch()`."""
        pass

    @commands.command()
    async def addmatch(self, ctx, match):
        """Add this match to the database and update all relevant data.

        This includes calls to update player and mappool data.
        """
        pass

    @commands.command()
    async def deletematch(self, ctx, match):
        """Delete this match from the database and update the involved players' data."""
        pass