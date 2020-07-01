#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Work in progress...write a real docstring here.
"""

import pathlib

from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands
from discord.ext.commands import CommandError
from discord.utils import sleep_until

from omegaconf import OmegaConf

import princess


class GameInfo(object):
    """Helper class for storing game/player information"""
    def __init__(self, game=None, p1=None, p2=None):
        self.game = game
        self.p1 = p1
        self.p2 = p2

    def __str__(self):
        if self.game == None:
            return 'No current game.'
        else:
            return f'{self.game.status_str}\n * Player 1: {self.p1}\n * Player 2: {self.p2}'

def has_active_game(ctx):
    """Command check: Is there an active game?"""
    try:
        pcog = ctx.cog
        game = pcog.game_info(ctx).game
        return game.is_active
    except:
        return False

def is_active_player(ctx):
    """Command check: Has message author joined the game?"""
    try:
        info = ctx.cog.game_info(ctx)
        return ctx.author in (info.p1, info.p2)
    except:
        return False

class PrincessCog(commands.Cog):
# TODO: Replace print with logging...
# ...could log to a Discord channel!

    def __init__(self, bot, conf):
        super().__init__()
        # The Bot we're attached to and its User
        self.bot = bot
        self.user = None
        self.uname = None
        # Configuration parameters
        self.conf = conf
        # Channel Category for Discord
        self.gamecat = None
        # Lobby channel on Discord
        self.lobbyname = None
        # Our Discord Guild
        self.guild = None
        # Discord role for players; used for Command checks
        self.prole = None
        # Information about current games
        self.info = {f'{(n+1):02}': GameInfo() for n in range(conf.MAX_GAMES)}

    def game_info(self, ctx):
        """Convenience function for internal use only."""
        if ctx.channel == self.lobby:
            return None
        # Channel names start with 'game', info keys do not
        key = ctx.channel.name[4:]
        if isinstance(self.info[key], GameInfo):
            return self.info[key]
        return None

    @commands.Cog.listener()
    async def on_ready(self):
        """Discord event...."""
        bot = self.bot
        self.user = bot.user
        self.uname = bot.user.name
        print(f'{self.uname} has connected to Discord!')

        # Find our guild
        guild = discord.utils.find(lambda g: g.name == self.conf.DISCORD_GUILD, bot.guilds)
        self.guild = guild
        print(f'Now on guild {guild}')

        # Check for a category on this guild; set it up if needed
        cat = discord.utils.find(lambda c: c.name == self.conf.CATEGORY, guild.categories)
        if cat is None:
            self.gamecat = await guild.create_category(self.conf.CATEGORY)
            print(f'Created category {self.gamecat} for later use.')
        else:
            self.gamecat = cat
            print(f'Using existing category {self.gamecat}.')

        # Check for a lobby-type channel within the category; set up if needed
        lobby = discord.utils.find(lambda c: c.name == self.conf.LOBBY, self.gamecat.channels)
        if lobby is None:
            self.lobby = await self.gamecat.create_text_channel(name=self.conf.LOBBY)
            print(f'Set up {self.lobby} within {self.gamecat}')
        else:
            self.lobby = lobby
            print(f'Using existing lobby {self.lobby}')

        await self.lobby.send(f'{self.uname} is now lurking in #{self.lobby}!')
        await self.lobby.send('Use !create to make a game. Use !help for general help.')

        # Set up player role...
        rolename = self.conf.PLAYER_ROLE
        role = discord.utils.find(lambda r: r.name == rolename, guild.roles)
        if role:
            print(f'Using existing role: {rolename}')
        else:
            role = await guild.create_role(name=rolename)
            print(f'Created new role: {rolename}')
        self.prole = role

        print(f'{self.uname} is ready to go!')

    @commands.command(name='shutdown')
    @commands.has_role('admin')
    async def do_shutdown(self, ctx, delay: int=3):
        """[Admin only] Get to the chopper!"""

        await ctx.send(f'{self.uname} is going down!')
        for channel in self.gamecat.channels:
            await channel.send(f'Shutdown in {delay} seconds...get to the chopper!')
        shutdown_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
        await sleep_until(shutdown_at)

        # Remove the player role (but don't delete it...why?)
        for m in self.prole.members:
            await m.remove_roles(self.prole)

        # Channels are not automatically deleted when the category is!
        for channel in self.gamecat.channels:
            await channel.delete()

        # Delete the category and shutdown the bot.
        # TODO: Remove the Cog instead of shutdown?
        await self.gamecat.delete(reason='Admin shutdown.')
        await self.bot.close()

    @commands.command(name='create')
    async def do_create(self, ctx):
        """[Lobby only] Create a new channel and set-up a game there."""
        # Silently ignore all non-lobby channels
        if ctx.channel != self.lobby:
            return

        # Look for an unused game slot
        game_id = None
        for key, info in self.info.items():
            if info.game == None:
                game_id = key
                break
        if not game_id:
            ctx.send('All game slots are full...try again later.')
            return

        # Create the new game.
        new_game = princess.Game()
        new_game.reset_game()

        # Create a channel and assign creator to Player 1.
        creator = ctx.author
        await creator.add_roles(self.prole)

        new_name = f'game{game_id}'
        new_channel = await self.gamecat.create_text_channel(new_name)
        self.info[game_id] = GameInfo(new_game, creator)
        msg = await new_channel.send(f'Game is here...{creator.name} is the Princess.')
        await ctx.send(f'Created {new_name} on {new_channel.name}.\nJump to channel: {msg.jump_url}')


    @commands.command(name='reset')
    @commands.check(is_active_player)
#    @commands.has_role(PLAYER_ROLE)
    async def do_reset(self, ctx):
        """Reset an existing game."""
        info = self.game_info(ctx)
        game = info.game
        if game:
            if game.is_active:
                raise CommandError('Attempting to restart a game in progress.')
            game.reset_game()

            # This assume whoever does !reset will be the Princess
            member = ctx.author
            # Swap players if the un-princess did the !reset
            if info.p1 != member:
                info.p2 = info.p1
                info.p1 = member
        else:
            await ctx.send('No existing game on this channel.')

    @commands.command(name='start')
    async def do_start(self, ctx):
        """Start a game (after both players have joined)."""
        info = self.game_info(ctx)
        plist = (info.p1, info.p2)
        if None in plist:
            await ctx.send('Still waiting for players to !join.')
            return
        game = info.game
        member = ctx.author
        if game and member in plist:
            game.start_game()
            await ctx.send(f'Starting game....\n * {plist[0].name} is the princess...\n * {plist[1].name} is not.')
            await plist[0].create_dm()
            await plist[0].dm_channel.send(f'Princess Charlotte is {game.princess}.')

    @commands.command(name='info')
    async def do_info(self, ctx):
        """Get info on game status/players."""
        info = self.game_info(ctx)
        await ctx.send(info)

    @commands.command(name='join')
    async def do_join(self, ctx):
        """Join an existing game."""
        member = ctx.author
        # Check for a game and empty player slot
        info = self.game_info(ctx)
        if not info.game:
            ctx.send(f'No game on this channel!\nUse "!create" in {self.lobby}')
            return
        if not info.p1:
            info.p1 = member
            await ctx.send(f'Added {member.name} as the Princess.')
            await member.add_roles(self.prole)
        elif not info.p2:
            info.p2 = member
            await ctx.send(f'Added {member.name} as the un-Princess.')
            await member.add_roles(self.prole)
        else:
            await ctx.send(f'{ctx.channel} is full.')

    @commands.command(name='turn')
    @commands.check(is_active_player)
    @commands.check(has_active_game)
#    @commands.has_role(PLAYER_ROLE)
    async def do_turn(self, ctx):
        """Start the next turn."""
        game = self.game_info(ctx).game
        if not game:
            return

        game.start_turn() # Will raise GameError if needed
        lines = [f'**Start of turn {game.turn}**\n({game.current_str} chooses first):']
        lines.extend(game.available_chars)
        await ctx.send('\n * '.join(lines))

    @commands.command(name='choose')
    @commands.check(is_active_player)
    @commands.check(has_active_game)
#    @commands.has_role(PLAYER_ROLE)
    async def do_choose(self, ctx, char):
        """Choose a character and simulate action."""
        game = self.game_info(ctx).game
        if not game:
            return

        game.choose_char(char) # Will raise GameError if needed
        await ctx.send(f'{char} would be doing...something here.')
        avail = game.available_chars
        if avail == []:  # End the turn...
            await ctx.send(f'**End of turn {game.turn}**')
            game.end_turn()
        else:
            lines = [f'({game.current_str} chooses next):']
            lines.extend(avail)
            await ctx.send('\n * '.join(lines))

    @commands.command(name='clue')
    @commands.check(is_active_player)
    @commands.check(has_active_game)
#    @commands.has_role(PLAYER_ROLE)
    async def do_clue(self, ctx):
        """Get a clue (by private DM)."""
        game = self.game_info(ctx).game
        if not game:
            return

        clue = game.draw_clue() # Will raise GameError if needed
        member = ctx.author
        await member.create_dm()
        await member.dm_channel.send(f'{clue} is not the princess!')
        await ctx.send(f'Gave a secret clue to {member}.')

    @commands.command(name='unmask')
    @commands.check(is_active_player)
    @commands.check(has_active_game)
#    @commands.has_role(PLAYER_ROLE)
    async def do_unmask(self, ctx, character):
        """Check if the given character is the princess (ends game)."""
        game = self.game_info(ctx).game
        if not game:
            return

        try:
            game.unmask_princess(character)
        except ValueError as error:
            msg = error.args[0]
            await ctx.send(msg)
        except princess.GameOver as endgame:
            await ctx.send(f'Game over...{endgame.winner} wins!')
            await ctx.send(f'Charlotte was {endgame.princess}!')

if __name__ == "__main__":
    config_file = pathlib.Path(__file__).parent.absolute() / 'config.yaml'
    conf = OmegaConf.load(str(config_file))
    TOKEN = conf.discopig.DISCORD_TOKEN
    GUILD = conf.discopig.DISCORD_GUILD
    the_bot = commands.Bot(conf.discopig.CMD_PREFIX)
    the_bot.add_cog(PrincessCog(the_bot, conf.discopig))
    the_bot.run(TOKEN)
    print('Shutdown complete!')
