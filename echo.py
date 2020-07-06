#!/usr/bin/env python3
"""
echo.py

Simple Discord bot extension via cogs.
"""

from discord.ext import commands

class Echo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_msg = None
        self.prefix = bot.command_prefix

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore my messages and bot commands
        if message.author == self.bot.user:
            return
        if message.content.startswith(self.prefix):
            return
        # Update the last message for later playback
        self.last_msg = {'channel': message.channel.name,
                         'author': message.author.name,
                         'content': message.content,
                         'url': message.jump_url}

    @commands.command(name="echo")
    async def do_echo(self, ctx):
        """Reposts the last non-command message across all channels."""
        if self.last_msg:
            await ctx.send('On #{channel}, {author} said...\n\n{content}\n\n{url}'.format_map(self.last_msg))
        else:
            await ctx.send("Haven't heard a thing.")

def setup(bot):
    bot.add_cog(Echo(bot))
