"""Match-related commands/cogs."""

import discord
from discord.ext import commands
import osuapi
import db_manip
import pprint

async def make_getmatch_embed(data):
    """Generate the embed description and other components for a getmatch() command.
    
    As with its parent, remember that this currently does not support non team-vs.
    `data` is expected to be the output of `get_individual_match_data()`.
    The following `dict` is returned:
    ```
    {
        "embed_description": str,
        "footer": str,
        "embed_color": int (as color hex),
    }
    ```
    """
    scores = data["individual_scores"]
    team_1_score_strings = []
    team_2_score_strings = []

    for individual_score in scores:
        #at first i thought doing this would make the actual score_string more readable
        #now i'm not very sure
        player_name = individual_score["user_name"]
        score_val = individual_score["score"]
        maxcombo = individual_score["combo"]
        accuracy = individual_score["accuracy"]
        count_300 = individual_score["hits"]["300_count"]
        count_100 = individual_score["hits"]["100_count"]
        count_50 = individual_score["hits"]["50_count"]
        count_miss = individual_score["hits"]["miss_count"]
        accuracy = '{:.2%}'.format(accuracy)
        score_val = "{:,}".format(score_val)
        maxcombo = "{:,}".format(maxcombo)
        score_string = (f'**{player_name}** - {score_val} ({maxcombo}x) ({accuracy} - {count_300}/{count_100}/{count_50}/{count_miss})')
        team_1_score_strings.append(score_string) if individual_score["team"] == "1" else team_2_score_strings.append(score_string)

    team_1_score_string = "\n".join(team_1_score_strings)
    team_2_score_string = "\n".join(team_2_score_strings)
    
    winner_string = {
        "Blue": f"Blue team wins by {'{:,}'.format(data['score_difference'])}!",
        "Red": f"Red team wins by {'{:,}'.format(data['score_difference'])}!",
        "Tie": "Tie!"}
    winner_color = {
        "Blue": 0x0000FF,
        "Red": 0xFF0000,
        "Tie": 0x808080}
    embed_desc = (
        f'**{winner_string[data["winner"]]}**\n\n'
        f'__Blue Team__ ({"{:,}".format(data["team_1_score"])} points, {"{:,}".format(data["team_1_score_avg"])} average)\n'
        f'{team_1_score_string}\n\n'
        f'__Red Team__ ({"{:,}".format(data["team_2_score"])} points, {"{:,}".format(data["team_2_score_avg"])} average)\n'
        f'{team_2_score_string}')

    #footer stuff
    scoring_types = {
        '0': 'Score',
        '1': 'Accuracy',
        '2': 'Combo',
        '3': 'Score v2'}
    team_types = {
        '0': 'Head-to-head',
        '1': 'Tag Co-op',
        '2': 'Team VS',
        '3': 'Tag Team VS'}
    play_modes = {
        '0': 'osu!',
        '1': 'Taiko',
        '2': 'CTB',
        '3': 'osu!mania'}
    embed_footer = (f'Played at {data["start_time"]} UTC | '
                f'Win condition: {scoring_types[data["scoring_type"]]} | '
                f'{team_types[data["team_type"]]} | '
                f'{play_modes[data["play_mode"]]}')

    final = {
        "embed_description": embed_desc,
        "footer": embed_footer,
        "embed_color": winner_color[data["winner"]],
    }
    return final

async def make_matchlist_embed(data):
    """Returns a newline, numbered list of the first 20 matches played in a lobby."""
    pass

async def make_matchstats_embed(data):
    """Generate the embed for the general match statistics of a match.
    
    Uses MongoDB calls.
    """
    pass
    #get mongodb doc from match_id
    #if not available, tell the user statistics on this match haven't been calculated

    #consider using get_individual_match_data instead?

class MatchCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def getmatch(self, ctx, match, map=None):
        """Get score and statistics data for a match.
        
        Works on any match, regardless of if it was played in the tournament or not.
        - `match` is the mp id.
        - `map` is the map index. If `map = "list"`, then sends a list of the first twenty maps played.
        If no map is defined, then returns general match statistics if available. If map index is defined,
        returns match statistic for that specific map."""
        if map is not None:
            data = await osuapi.process_match_data(match, map)
            if data is None:
                await ctx.send("Something went wrong... Are you sure this is a valid mp and your index is correct?")
            embed_data = await make_getmatch_embed(data)
            em_msg = discord.Embed(description=embed_data["embed_description"],
                                color=embed_data["embed_color"],
                                url=data["diff_url"],
                                title=data["map_name"])
            em_msg.set_thumbnail(url=data["map_thumbnail"])
            em_msg.set_footer(text=embed_data["footer"])
            em_msg.set_author(name=data["match_name"],url=data["match_url"])
            await ctx.send(embed=em_msg)
        elif map == "list":
            #show the first 20 maps played
            pass
        else:
            #show some match stats
            '''
            STK7: (Plastic Assimilation) vs. (Cherry Gum)
            Blue Team | 4 - 5 | Red Team

            **Match Statistics**    
            Stat                      Blue Team        Red Team
            Avg. Score
            Avg. Accuracy
            Avg. Score Difference

            **Individual Statistics**
            __Blue Team__
            **Player** - 123,445 avg pts | 100.00% avg acc | 100.00% avg contrib
            **Player** - 123,445 avg pts | 100.00% avg acc | 100.00% avg contrib

            __Red Team__
            **Player** - 123,445 avg pts | 100.00% avg acc | 100.00% avg contrib
            **Player** - 123,445 avg pts | 100.00% avg acc | 100.00% avg contrib

            footer:
            Use `getmatch <mp_id> list` for a list of maps played or `getmatch <mp_id> <index>` for
            individual map data!

            '''
            pass

    @commands.command()
    async def trackmatch(self, ctx, match, map=1):
        """Start tracking a match, returning embeds similar to `getmatch()`."""
        pass