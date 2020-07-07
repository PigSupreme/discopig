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
    @commands.command()
    async def post_init(self, ctx=None):
        # Use the webhook to find its channel
        guildhooks = await ctx.guild.webhooks()
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

    def is_from_webhook(self, msg):
        return msg.webhook_id == self.hook.id and msg.author.name == 'GitHub'

    @commands.Cog.listener()
    async def on_message(self, msg):
        if self.is_from_webhook(msg):
            await self.do_git_update()

    @commands.command(name="findsha", help="Re-check for most recent remote/local commits.")
    @commands.is_owner()
    async def get_latest_sha(self, ctx=None):
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

    @commands.command(name="gupdate", help="Manually check for updates.")
    @commands.is_owner()
    async def do_git_update(self, ctx=None):
        if ctx:
            await ctx.invoke(self.get_latest_sha)
        else:
            await self.get_latest_sha()
            ctx = self.hook_chan

        if self.mysha.startswith(self.remsha):
            await ctx.send(f'No update needed.')
        else:
            async with ctx.typing():
                sp = subprocess.run(['git', 'pull', '--ff-only'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
                if sp.returncode:   # git pull returned an error
                    await ctx.send(f'* Update failed:\n{sp.stdout}\n{sp.stderr}')
                else:
                    await ctx.send(f'* Update succeeded:\n {sp.stdout}')
                    self.bot.reload_extension('ghupdate')

    @commands.command(name="shasha", help="Show most recent remote/local commits.")
    async def show_latest_shas(self, ctx):
        await ctx.send(f'* Remote SHA: {self.remsha}\n* Bot SHA: {self.mysha}')


def setup(bot):
    the_cog = GitHubUpdate(bot)
    bot.add_cog(the_cog)
