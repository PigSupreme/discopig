#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple core for Discord bot with dynamic extension support.
"""

from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands
from discord.utils import sleep_until

LOGFILE = 'botcore.log'
import logging
logging.basicConfig(filename=LOGFILE, filemode='w', level=logging.INFO)

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename=LOGFILE, encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

from omegaconf import OmegaConf

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
            msg_text = f'Loaded extension: {extension}.'
        except commands.ExtensionAlreadyLoaded:
            self.bot.reload_extension(extension)
            msg_text = f'Reloaded extension: {extension}.'
        logging.info(msg_text)

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
            msg_text = f'Unloaded extension {extension}'
        except commands.ExtensionNotLoaded:
            msg_text = f'No extension {extension} to unload.'
        await send_dm(ctx.author, msg_text)


class BotCore(commands.Bot):
    """The mother of all Bots."""
    def __init__(self, config):
        super().__init__(config.CMD_PREFIX)
        self.add_cog(CoreCog(self))
        self.GUILDNAME = config.DISCORD_GUILD
        self.CATEGORY = config.CATEGORY
        self.LOBBYNAME = config.LOBBY

    async def on_ready(self):
        ready_msg = f'{self.user.name} has connected to Discord!'

        # Find our guild
        guild = discord.utils.find(lambda g: g.name == self.GUILDNAME, self.guilds)
        self.the_guild = guild
        ready_msg += f'\nNow on guild {guild}.'

        # Check for a category on this guild; set it up if needed
        cat = discord.utils.find(lambda c: c.name == self.CATEGORY, guild.categories)
        if cat is None:
            self.channelcat = await guild.create_category(self.CATEGORY)
            ready_msg += f'\nCreated category {self.channelcat} for later use.'
        else:
            self.channelcat = cat
            ready_msg += f'\nUsing existing category {self.channelcat}.'

        # Check for a lobby-type channel within the category; set up if needed
        lobby = discord.utils.find(lambda c: c.name == self.LOBBYNAME, self.channelcat.channels)
        if lobby is None:
            self.lobby = await self.channelcat.create_text_channel(name=self.LOBBYNAME)
            ready_msg += f'\nSet up #{self.lobby} within {self.channelcat}.'
        else:
            self.lobby = lobby
            ready_msg += f'\nUsing existing lobby {self.lobby}.'
        lobby_msg = await self.lobby.send(f'{self.user.name} is now lurking in the #{self.lobby}.')
        ready_msg += f'\n{lobby_msg.jump_url}'

        # Find our owner and send dm the ready_msg
        info = await self.application_info()
        self.owner = info.owner
        await send_dm(self.owner, ready_msg)


if __name__ == "__main__":
    CONFIG = OmegaConf.load('config.yaml').discopig
    bot = BotCore(CONFIG)
    bot.run(CONFIG.DISCORD_TOKEN)
    print('Shutdown complete!')
