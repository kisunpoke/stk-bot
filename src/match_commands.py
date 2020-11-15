"""Match-related commands/cogs."""

import discord
from discord.ext import commands

import osuapi
import db_manip
import db_get
import pprint
import prompts
from utils import comma_sep, percentage

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

    @commands.command(aliases=["matchstats","gm"])
    async def getmatch(self, ctx, match, map=None):
        """Get score and statistics data for a match.
        
        Parameters:
        - `match` is the mp id.
        - `map` is the map index.
        If no map is defined, then returns general match statistics if available. If map index is defined,
        returns match statistic for that specific map. Internally decremented by one to make zero-indexed.
        If index is defined, works on any match, regardless of if it was played in the tournament or not."""
        if map is not None:
            await ctx.trigger_typing()
            data = await osuapi.process_match_data(match, int(map)-1)
            if data is None:
                await prompts.error_embed(self.bot, ctx, "Something went wrong... Are you sure this is a valid mp and your map number is correct?")
            embed_data = await make_getmatch_embed(data)
            em_msg = discord.Embed(description=embed_data["embed_description"],
                                color=embed_data["embed_color"],
                                url=data["diff_url"],
                                title=data["map_name"])
            em_msg.set_thumbnail(url=data["map_thumbnail"])
            em_msg.set_footer(text=embed_data["footer"])
            em_msg.set_author(name=data["match_name"],url=data["match_url"])
            await ctx.send(embed=em_msg)
        else:
            await ctx.trigger_typing()
            #raw unreadability
            match_doc = await db_get.get_match_document(match)
            if not match_doc:
                await prompts.error_embed(self.bot, ctx, "Couldn't find that match... "
                                                         "(Only tournament matches are allowed; ensure you're using the MP id)")
                return None
            
            blue_team_name = "Blue Team"
            red_team_name = "Red Team"

            ps = match_doc["player_stats"]
            blue_string = ""
            red_string = ""
            for player_id in ps:
                stat = ps[player_id]
                player_string = f"**{stat['user_name']}** -  {comma_sep(stat['average_score'])} avg pts | {percentage(stat['average_acc'])} avg acc | {percentage(stat['average_contrib'])} avg contrib\n"
                if ps[player_id]["team"] == "1":
                    blue_string += player_string
                    if blue_team_name == "Blue Team":
                        player_doc = await db_get.get_player_document(player_id)
                        blue_team_name = player_doc["team_name"]
                elif ps[player_id]["team"] == "2":
                    red_string += player_string
                    if red_team_name == "Red Team":
                        player_doc = await db_get.get_player_document(player_id)
                        red_team_name = player_doc["team_name"]

            b_t = match_doc["blue_team_stats"]
            r_t = match_doc["red_team_stats"]
            msg =  (f"__Overall Statistics__\n"
                    f"**{blue_team_name}** - {comma_sep(b_t['average_score'], 2)} avg pts | {percentage(b_t['average_acc'])} avg acc | {comma_sep(b_t['average_difference'], 2)} avg diff\n"
                    f"**{red_team_name}** - {comma_sep(r_t['average_score'], 2)} avg pts | {percentage(r_t['average_acc'])} avg acc | {comma_sep(r_t['average_difference'], 2)} avg diff\n"
                    f"\n"
                    f"__Individual Statistics__\n"
                    f"**{blue_team_name}**\n"
                    f"{blue_string}"
                    f"\n"
                    f"**{red_team_name}**\n"
                    f"{red_string}")
            embed = discord.Embed(description=msg)
            embed.set_author(name=match_doc["match_name"], url=f"https://osu.ppy.sh/mp/{match}")
            embed.set_footer(text=f"You can use \"getmatch {match} <index>\" for statistics on a specific map.")
            await ctx.send(embed=embed)
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

    #if someone really wants to watch a match, just look at mp link or stream instead lol
    #https://github.com/Rapptz/discord.py/blob/master/examples/background_task.py for future implementation
    '''
    @commands.command()
    async def trackmatch(self, ctx, match, map=1):
        """Start tracking a match, returning embeds similar to `getmatch()` with an index."""
        pass
    '''