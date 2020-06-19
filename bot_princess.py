#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Work in progress...write a real docstring here.
"""

import os
import random
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands
from dotenv import load_dotenv
from discord.utils import sleep_until

import princess

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
CATEGORY = 'PRINCESS'
LOBBY = 'gamelobby'
MAX_GAMES = 10

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

    # Find our guild
    guild = discord.utils.find(lambda g: g.name == GUILD, bot.guilds)
    bot.the_guild = guild
    print(f'Now on guild {guild}')

    # Check for a category on this guild; set it up if needed
    cat = discord.utils.find(lambda c: c.name == CATEGORY, guild.categories)
    if cat is None:
        bot.gamecat = await guild.create_category(CATEGORY)
        print(f'Created category {bot.gamecat} for later use.')
    else:
        bot.gamecat = cat
        print(f'Using existing category {bot.gamecat}.')

    # Check for a lobby-type channel within the category; set up if needed
    lobby = discord.utils.find(lambda c: c.name == LOBBY, bot.gamecat.channels)
    if lobby is None:
        bot.lobby = await bot.gamecat.create_text_channel(name=LOBBY)
        print(f'Set up {bot.lobby} within {bot.gamecat}')
    else:
        bot.lobby = lobby
        print(f'Using existing lobby {bot.lobby}')

    await bot.lobby.send(f'{bot.user} is now lurking in the #{bot.lobby}')

    # Set up information about active games here...
    bot.current_games = dict()
    bot.next_game_id = 1

    print(f'{bot.user} is ready to go!')

@bot.command(name='create', help='Create a new channel and set-up a game there.')
async def do_newgame(ctx):
    # Only respond to this in the lobby channel
    if ctx.channel != bot.lobby:
        return

    this_game = bot.next_game_id
    bot.next_game_id += 1

    new_name = f'game{this_game}'
    new_channel = await bot.gamecat.create_text_channel(new_name)
    new_game = princess.PrincessGame(new_channel)

    bot.current_games[new_channel] = new_game
    msg = await new_channel.send(f'Game is here...waiting for players.')
    await msg.pin()  # For testing only.
    await bot.lobby.send(f'Created game {this_game} in {bot.gamecat}.\n{msg.jump_url}')

@bot.command(name='reset', help='Reset the game.')
async def do_reset(ctx):
    # Check if there's an existing game on this channel
    # TODO: Can probably simplify with dynamic channel permissions...
    # ...or @command.check predicates?
    channel = ctx.channel
    try:
        game = bot.current_games[channel]
    # Silently ignore non-game channels
    except KeyError:
        return
    # TODO: Some kind of confirmation here?
    the_princess = game.reset()

    # This is assuming whoever does !reset is the princess
    member = ctx.author
    await member.create_dm()
    await ctx.send(f'Starting game....{member} is not a princess, but plays one on Discord.')
    await member.dm_channel.send(f'Princess Charlotte is {the_princess}.')

# TODO:
#@bot.command(name='join', help='Join the game as the un-princess.')
#

@bot.command(name='turn', help='Start the next turn.')
async def do_turn(ctx):
    # Check if there's an existing game on this channel
    # TODO: Can probably simplify with dynamic channel permissions...
    # ...or @command.check predicates?
    channel = ctx.channel
    try:
        game = bot.current_games[channel]
    # Silently ignore non-game channels
    except KeyError:
        return

    turn = game.turn
    # TODO: Check that this picks the correct leading player for this turn:
    leader = ('Princess', 'Other')[turn % 2]
    lines = [f'Characters for turn {turn+1} ({leader} chooses first):']
    lines.extend(game.start_turn())
    await ctx.send('\n * '.join(lines))

@bot.command(name='clue', help='Get a clue (in secret!)')
async def do_clue(ctx):
    # Check if there's an existing game on this channel
    # TODO: Can probably simplify with dynamic channel permissions...
    # ...or @command.check predicates?
    channel = ctx.channel
    try:
        game = bot.current_games[channel]
    # Silently ignore non-game channels
    except KeyError:
        return

    clue = game.get_clue()
    if clue:
        member = ctx.author
        await member.create_dm()
        await member.dm_channel.send(f'{clue} is not the princess!')
        await ctx.send(f'Gave a secret clue to {member}.')
    else:
        await ctx.send('No clues available!')

@bot.command(name='unmask', help="Check if a character is the princess (ends game).")
async def do_unmask(ctx, character):
    # Check if there's an existing game on this channel
    # TODO: Can probably simplify with dynamic channel permissions...
    # ...or @command.check predicates?
    channel = ctx.channel
    try:
        game = bot.current_games[channel]
    # Silently ignore non-game channels
    except KeyError:
        return

    try:
        game.unmask_princess(character)
    except ValueError as error:
        msg = error.args[0]
        await ctx.send(msg)
    except princess.GameOver as endgame:
        await ctx.send(f'Game over...{endgame.winner} wins!')
        await ctx.send(f'Charlotte was {endgame.princess}!')

@bot.command(name='shutdown', help="(Admin only) Get to the chopper!")
@commands.has_role('admin')
async def do_shutdown(ctx, delay: int=30):
    await ctx.send(f'{bot.user} is going down!')
    for channel in bot.gamecat.channels:
        await channel.send(f'Shutdown in {delay} seconds...get to the chopper!')
    shutdown_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
    await sleep_until(shutdown_at)
    # Channels are not automatically deleted when the category is!
    for channel in bot.gamecat.channels:
        await channel.delete()

    await bot.gamecat.delete(reason='Admin shutdown.')
    await bot.close()

if __name__ == "__main__":
    random.seed()
    bot.run(TOKEN)
    print('Shutdown complete!')
