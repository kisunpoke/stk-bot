"""Match-related commands/cogs."""

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
        """Add this match to the database and update the involved players' data."""
        pass

    @commands.command()
    async def deletematch(self, ctx, match):
        """Delete this match from the database and update the involved players' data."""
        pass