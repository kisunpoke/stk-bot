"""Varied embed prompts."""

import discord
import asyncio

async def confirmation_dialog(bot, ctx, content, footer=""):
    """Generate and send a reaction-based confirmation dialog."""
    em_msg = discord.Embed(description=content)
    if footer:
        em_msg.set_footer(text=footer)
    conf_message = await ctx.send(embed=em_msg)
    await conf_message.add_reaction('✅')
    await conf_message.add_reaction('❌')

    def check(reaction, user):
        #verify that the user who initiated the command is reacting to the right message
        #(also ignore any other reactoins)
        return user == ctx.author and reaction.message.id == conf_message.id and reaction.emoji in ('❌', '✅')

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=20.0, check=check)
        await conf_message.delete()
    except asyncio.TimeoutError:
        #we could delete the confirmation message here
        await ctx.send('Response timed out.')
    else:
        if reaction.emoji == '✅':
            return True
        else:
            return False

async def error_embed(bot, ctx, content, footer=""):
    """Generate and send an error message."""
    em_msg = discord.Embed(description=content, color=0xFF0000)
    if footer:
        em_msg.set_footer(text=footer)
    await ctx.send(embed=em_msg)

async def std_embed(bot, ctx, content, footer=""):
    """Generate and send a standard embed message."""
    em_msg = discord.Embed(description=content)
    if footer:
        em_msg.set_footer(text=footer)
    await ctx.send(embed=em_msg)