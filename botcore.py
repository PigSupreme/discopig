#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple core for Discord bot with dynamic extension support.
"""

from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands
from discord.utils import sleep_until

from omegaconf import OmegaConf
conf = OmegaConf.load('config.yaml').discopig
GUILD = conf.DISCORD_GUILD
TOKEN = conf.DISCORD_TOKEN
CATEGORY = conf.CATEGORY
LOBBY = conf.LOBBY

bot = commands.Bot(command_prefix='!')

async def send_dm(user, txt):
    channel = user.dm_channel
    if channel is None:
        channel = await user.create_dm()
    msg = await channel.send(txt)
    return msg

@bot.event
async def on_ready():
    ready_msg = f'{bot.user} has connected to Discord!'

    # Find our guild
    guild = discord.utils.find(lambda g: g.name == GUILD, bot.guilds)
    bot.the_guild = guild
    ready_msg += f'\nNow on guild {guild}'

    # Check for a category on this guild; set it up if needed
    cat = discord.utils.find(lambda c: c.name == CATEGORY, guild.categories)
    if cat is None:
        bot.channelcat = await guild.create_category(CATEGORY)
        ready_msg += f'\nCreated category {bot.channelcat} for later use.'
    else:
        bot.channelcat = cat
        ready_msg += f'\nUsing existing category {bot.channelcat}.'

    # Check for a lobby-type channel within the category; set up if needed
    lobby = discord.utils.find(lambda c: c.name == LOBBY, bot.channelcat.channels)
    if lobby is None:
        bot.lobby = await bot.channelcat.create_text_channel(name=LOBBY)
        ready_msg += f'\nSet up #{bot.lobby} within {bot.channelcat}.'
    else:
        bot.lobby = lobby
        ready_msg += f'\nUsing existing lobby {bot.lobby}.'
    lobby_msg = await bot.lobby.send(f'{bot.user} is now lurking in the #{bot.lobby}.')
    ready_msg += f'\n{lobby_msg.jump_url}'

    # Find our owner and send dm the ready_msg
    info = await bot.application_info()
    bot.owner = info.owner
    await send_dm(bot.owner, ready_msg)

@bot.command(name='load_ext')
@commands.is_owner()
async def do_load_extension(ctx, extension: str):
    try:
        bot.load_extension(extension)
        msg_text = f'Loaded extension: {extension}'
    except commands.ExtensionAlreadyLoaded:
        bot.reload_extension(extension)
        msg_text = f'Reloaded extension: {extension}'
    # Extension setup() cannot be a coroutine; we use this trickery
    #  to excute anything requiring async:
    cmd = bot.get_command('post_init')
    if cmd:
        if ctx:
            await ctx.invoke(cmd)
            await send_dm(ctx.author, msg_text)
        # Dynamic reload doesn't provide a context, so...
        else:
            await cmd.__call__()
        bot.remove_command('post_init')

@bot.command(name='unload_ext')
@commands.is_owner()
async def do_unload_extension(ctx, extension: str):
    try:
        bot.unload_extension(extension)
        msg_text = f'Unloaded extension {extension}'
    except commands.ExtensionNotLoaded:
        msg_text = f'No extension {extension} to unload.'
    send_dm(ctx.author, msg_text)

@bot.command(name='shutdown', help="(Admin only) Get to the chopper!")
@commands.has_role('admin')
async def do_shutdown(ctx, delay: int=3, total: bool=False):
    await ctx.send(f'{bot.user} is going down!')
    for channel in bot.channelcat.channels:
        await channel.send(f'Shutdown in {delay} seconds...get to the chopper!')
    shutdown_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
    await sleep_until(shutdown_at)

    # If total shutdown, remove category and channels:
    if total:
        # Channels are not automatically deleted when the category is!
        for channel in bot.channelcat.channels:
             await channel.delete()
        await bot.channelcat.delete()
    await bot.close()

if __name__ == "__main__":
    bot.run(TOKEN)
    print('Shutdown complete!')
