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

from princess import PrincessGame, PLAYER, GameOver

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
CATEGORY = 'PRINCESS'
LOBBY = 'gamelobby'
PLAYER_ROLE = 'GamePlayer'
MAX_GAMES = 10

bot = commands.Bot(command_prefix='!')

# TODO: This should be a method once we subclass Bot.
# Could also use the on_command_error Bot event?
@bot.command(name='_get_game', enabled=False)
async def _get_game(ctx):
    """Convenience function for internal use only."""
    try:
        game = bot.current_games[ctx.channel]
    except KeyError:
        # TODO: Use a custom CommandError instead?
        game = None
    return game

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
    bot.get_game_from_ctx = bot.get_command('_get_game')

    # Set up player role...
    role = discord.utils.find(lambda r: r.name == PLAYER_ROLE, guild.roles)
    if role:
        print(f'Using existing role: {PLAYER_ROLE}')
    else:
        role = await guild.create_role(name='GamePlayer')
        print(f'Created new role: {PLAYER_ROLE}')
    bot.prole = role

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
    new_game = PrincessGame(new_channel)

    bot.current_games[new_channel] = new_game
    msg = await new_channel.send(f'Game is here...waiting for players.')
    await msg.pin()  # For testing only.
    await bot.lobby.send(f'Created game {this_game} in {bot.gamecat}.\n{msg.jump_url}')
    await ctx.author.add_roles(bot.prole)

@bot.command(name='reset', help='Reset the game.')
@commands.has_role(PLAYER_ROLE)
async def do_reset(ctx):
    """Reset an existing game on this channel."""
    game = await bot.get_game_from_ctx.__call__(ctx)
    # TODO: Can probably remove the if..else block, and...
    # ...instead catch problems with on_command_error events.
    if game:
        # TODO: Most of this will need a rewrite once we...
        # ...finalize the PrincessGame interface.
        game.reset()
        game.start_game()

        # This is assuming whoever does !reset is the princess
        member = ctx.author
        await member.create_dm()
        await ctx.send(f'Starting game....{member.name} is not a princess, but plays one on Discord.')
        await member.dm_channel.send(f'Princess Charlotte is {game.princess}.')
        game.add_player(princess=member)
        # TODO: Swap players if the un-princess did the !reset
    else:
        await ctx.send('No existing game on this channel.')

@bot.command(name='join', help='Join the game as the un-princess.')
async def do_join(ctx):
    game = await bot.get_game_from_ctx.__call__(ctx)
    member = ctx.author
    if game.player[PLAYER.OTHER]:
        await member.dm_channel.send(f'{ctx.channel} is full.')
    if member == game.player[PLAYER.PRINCESS]:
        await ctx.send(f"{member.name} is already the Princess!")
    else:
        game.add_player(other=member)
        await member.add_roles(PLAYER_ROLE)

@bot.command(name='turn', help='Start the next turn.')
@commands.has_role(PLAYER_ROLE)
async def do_turn(ctx):
    game = await bot.get_game_from_ctx.__call__(ctx)
    # TODO: Check that the game has actually started.
    turn = game.turn
    # TODO: Get this info directly from game instead
    leader = ('Princess', 'Other')[turn % 2]
    lines = [f'Characters for turn {turn} ({leader} chooses first):']
    lines.extend(game.start_turn())
    await ctx.send('\n * '.join(lines))

@bot.command(name='clue', help='Get a clue (in secret!)')
@commands.has_role(PLAYER_ROLE)
async def do_clue(ctx):
    game = await bot.get_game_from_ctx.__call__(ctx)
    clue = game.get_clue()
    if clue:
        member = ctx.author
        await member.create_dm()
        await member.dm_channel.send(f'{clue} is not the princess!')
        await ctx.send(f'Gave a secret clue to {member}.')
    else:
        await ctx.send('No clues available!')

@bot.command(name='unmask', help="Check if a character is the princess (ends game).")
@commands.has_role(PLAYER_ROLE)
async def do_unmask(ctx, character):
    game = await bot.get_game_from_ctx.__call__(ctx)
    try:
        game.unmask_princess(character)
    except ValueError as error:
        msg = error.args[0]
        await ctx.send(msg)
    except GameOver as endgame:
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

    # Remove the player role (but don't delete it)
    for m in bot.prole.members:
        await m.remove_roles(bot.prole)

    # Channels are not automatically deleted when the category is!
    for channel in bot.gamecat.channels:
        await channel.delete()

    await bot.gamecat.delete(reason='Admin shutdown.')
    await bot.close()

if __name__ == "__main__":
    random.seed()
    bot.run(TOKEN)
    print('Shutdown complete!')
