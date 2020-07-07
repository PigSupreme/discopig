#!/usr/bin/env python3
"""
ghupdate.py

Discord bot extension for grabbing GitHub updates; WIP.
"""

from discord.ext import commands
from omegaconf import OmegaConf

conf = OmegaConf.load('config.yaml').ghupdate

class GitHubUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.hook = None
        self.hook_chan = None
        self.sha = None

    @commands.command(name="findsha")
    async def get_latest_sha(self, ctx):
        # Use the webhook to find its channel
        guildhooks = await ctx.guild.webhooks()
        for wh in guildhooks:
            if wh.url == conf.HOOK_URL:
                self.hook = wh
                break
        self.hook_chan = wh.channel

        # Find the last message posted by the webhook from GitHub
        async for msg in self.hook_chan.history():
            if msg.webhook_id == self.hook.id and msg.author.name == 'GitHub':
                emb = msg.embeds[0]
                # If on the right branch, grab the short SHA for this commit
                if emb.title.startswith(f'[{conf.BRANCH}]'):
                    self.sha = emb.description[1: emb.description.find(']')]
                    break

    @commands.command(name="sha")
    async def show_latest_sha(self, ctx):
        await ctx.send(f'Most recent commit: SHA = {self.sha}')

def setup(bot):
    the_cog = GitHubUpdate(bot)
    bot.add_cog(the_cog)

    # botcore will autorun this after loading
    @commands.command()
    async def post_init(ctx):
        await the_cog.get_latest_sha(ctx)
    bot.add_command(post_init)

    # TODO: Make sure we're up to date
