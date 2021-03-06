#!/usr/bin/env python3
"""
ghupdate.py

Discord bot extension for grabbing GitHub updates; WIP.
"""

import subprocess
from discord.ext import commands
from omegaconf import OmegaConf

conf = OmegaConf.load('config.yaml').ghupdate

class GitHubUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.hook = None
        self.hook_chan = None
        self.remsha = None
        self.mysha= None

    # botcore will autorun this after loading
    @commands.command(help="Pay no attention to the man behind the curtain.")
    async def post_init(self, ctx=None):
        """Do asynch things on startup/reload."""
        # Use the webhook to find its channel; store for later use.
        if ctx:
            guildhooks = await ctx.guild.webhooks()
        else:
            guildhooks = await self.bot.the_guild.webhooks()
        for wh in guildhooks:
            if wh.url == conf.HOOK_URL:
                self.hook = wh
                break
        self.hook_chan = wh.channel

        # If ctx is none, we just reloaded after a git pull...
        # ...otherwise, this is the initial load, so check for updates.
        if ctx:
            await ctx.send('Auto-checking for repository updates...')
            await ctx.invoke(self.do_git_update)
        else:
            await self.hook_chan.send('Dynamic reload successful!')
            # Todo: Is this really needed? Check botcore.py reload code.
            self.bot.remove_command('post_init')

    def is_from_webhook(self, msg):
        """Used internally to ignore anything except GitHub webhook updates."""
        if self.hook_chan and msg.channel != self.hook_chan:
            return
        if msg.webhook_id and msg.webhook_id == self.hook.id:
            return msg.author.name == 'GitHub'

    @commands.Cog.listener()
    async def on_message(self, msg):
        """Listen for GitHub webhooks events and check for updates."""
        if self.is_from_webhook(msg):
            await self.do_git_update(None)

    @commands.command(name="findsha")
    @commands.is_owner()
    async def get_latest_sha(self, ctx=None):
        """Re-check for the most recent remote/local commits."""
        # Find the last message posted by the webhook from GitHub
        async for msg in self.hook_chan.history():
            if self.is_from_webhook(msg):
                emb = msg.embeds[0] # There should be only one!
                # If on the right branch, grab the short SHA for this commit
                if emb.title.startswith(f'[{conf.BRANCH}]'):
                    remsha = emb.description[1: emb.description.find(']')]
                    self.remsha = remsha[1:-1]
                    break

        # Grab the SHA for most recent local commit (strip enclosing quotes)
        sp = subprocess.run(['git', 'show', '--pretty=format:"%H"', '--no-notes', '--no-patch'], stdout=subprocess.PIPE, encoding='utf-8')
        self.mysha = sp.stdout[1:-1]

        # If invoked as a command, report the results
        if ctx:
            await ctx.invoke(self.show_latest_shas)

    @commands.command(name="gupdate")
    @commands.is_owner()
    async def do_git_update(self, ctx=None):
        """Check for updates; pull and reload if needed."""
        if ctx:
            await ctx.invoke(self.get_latest_sha)
        else:
            await self.get_latest_sha(None)
            ctx = self.hook_chan

        if self.mysha.startswith(self.remsha):
            await ctx.send(f'No update needed.')
        else:
            async with ctx.typing():
                sp = subprocess.run(['git', 'pull', '--ff-only'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
                if sp.returncode:   # Meaning git pull returned an error
                    await ctx.send(f'* Update failed:\n{sp.stdout}\n{sp.stderr}')
                else:
                    await ctx.send(f'* Update succeeded:\n {sp.stdout}')
                    await self.bot.get_command('load_ext').__call__(None, 'ghupdate')

    @commands.command(name="shasha", help="Show most recent remote/local commits.")
    async def show_latest_shas(self, ctx):
        await ctx.send(f'* Remote SHA: {self.remsha}\n* Bot SHA: {self.mysha}')


def setup(bot):
    the_cog = GitHubUpdate(bot)
    bot.add_cog(the_cog)
