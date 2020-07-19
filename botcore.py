#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple core for Discord bot with dynamic extension support.
"""

from datetime import datetime, timedelta, timezone
import logging, logging.config

from omegaconf import OmegaConf

import discord
from discord.ext import commands
from discord.utils import sleep_until

logging.config.fileConfig('logging.conf')

async def send_dm(user, txt):
    """Send a direct/private message to one user."""
    channel = user.dm_channel
    if channel is None:
        channel = await user.create_dm()
    msg = await channel.send(txt)
    return msg

class CoreCog(commands.Cog):
    def __init__(self, bot):
        """The mother of all cogs."""
        super().__init__()
        # Information about our Bot:
        self.bot = bot

    @commands.command(name='shutdown', help="Get to the chopper!")
    @commands.has_role('admin')
    async def do_shutdown(self, ctx, delay: int=3, total: bool=False):
        await ctx.send(f'{self.bot.user.name} is going down!')
        for channel in self.bot.channelcat.channels:
            await channel.send(f'Shutdown in {delay} seconds...get to the chopper!')
        shutdown_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
        await sleep_until(shutdown_at)

        # If total shutdown, remove category and channels:
        if total:
            # Channels are not automatically deleted when the category is!
            for channel in self.bot.channelcat.channels:
                 await channel.delete()
            await self.bot.channelcat.delete()
        await self.bot.close()

    @commands.command(name='load_ext', help="Load an extension from this bot's local filesystem.")
    @commands.is_owner()
    async def do_load_extension(self, ctx, extension: str):
        try:
            self.bot.load_extension(extension)
            logging.info(f'Loaded extension: {extension}.')
        except commands.ExtensionAlreadyLoaded:
            self.bot.reload_extension(extension)
            logging.info(f'Reloaded extension: {extension}.')

        # Extension setup() cannot be a coroutine; we use this trickery
        #  to excute anything requiring async:
        new_cog = self.bot.get_cog(extension)
        if hasattr(new_cog, 'post_init'):
            await new_cog.post_init()
            logging.info(f'post_init complete: {extension}.')

    @commands.command(name='unload_ext', help="Unload an extension from this bot.")
    @commands.is_owner()
    async def do_unload_extension(self, ctx, extension: str):
        try:
            self.bot.unload_extension(extension)
            logging.info(f'Unloaded extension {extension}')
        except commands.ExtensionNotLoaded:
            logging.warn(f'unload_ext: Extension {extension} is not currently loaded.')


class BotCore(commands.Bot):
    """The mother of all Bots."""
    def __init__(self, config):
        super().__init__(config.CMD_PREFIX)
        self.add_cog(CoreCog(self))
        self.GUILDNAME = config.DISCORD_GUILD
        self.CATEGORY = config.CATEGORY
        self.LOBBYNAME = config.LOBBY

    async def on_ready(self):
        logging.info(f'{self.user.name} has connected to Discord!')

        # Find our guild
        guild = discord.utils.find(lambda g: g.name == self.GUILDNAME, self.guilds)
        self.the_guild = guild
        logging.debug(f'\nNow on guild {guild}.')

        # Check for a category on this guild; set it up if needed
        cat = discord.utils.find(lambda c: c.name == self.CATEGORY, guild.categories)
        if cat is None:
            self.channelcat = await guild.create_category(self.CATEGORY)
            logging.debug(f'\nCreated category {self.channelcat} for later use.')
        else:
            self.channelcat = cat
            logging.debug(f'\nUsing existing category {self.channelcat}.')

        # Check for a lobby-type channel within the category; set up if needed
        lobby = discord.utils.find(lambda c: c.name == self.LOBBYNAME, self.channelcat.channels)
        if lobby is None:
            self.lobby = await self.channelcat.create_text_channel(name=self.LOBBYNAME)
            logging.debug(f'\nSet up #{self.lobby} within {self.channelcat}.')
        else:
            self.lobby = lobby
            logging.debug(f'\nUsing existing lobby {self.lobby}.')
        lobby_msg = await self.lobby.send(f'{self.user.name} is now lurking in the #{self.lobby}.')

        # Find our owner and send dm the ready_msg
        info = await self.application_info()
        self.owner = info.owner
        ready_msg = f'Now listening in the lobby:\n{lobby_msg.jump_url}'
        await send_dm(self.owner, ready_msg)


if __name__ == "__main__":
    CONFIG = OmegaConf.load('config.yaml').discopig
    bot = BotCore(CONFIG)
    bot.run(CONFIG.DISCORD_TOKEN)
    print('Shutdown complete!')
