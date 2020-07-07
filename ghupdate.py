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

    def is_from_webhook(self, msg):
        # Todo: Return the embed to avoid duplicate code?
        return msg.webhook_id == self.hook.id and msg.author.name == 'GitHub'

    @commands.Cog.listener()
    async def on_message(self, msg):
        if self.is_from_webhook(msg):
            await self.hook_chan.send('Rawr webhook!')
            async with self.hook_chan.typing():
                sp = subprocess.run(['git', 'pull', '--ff-only'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
                await self.hook_chan.send(f'Updated:\n{sp.stdout}\n{sp.stderr}')

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
            if self.is_from_webhook(msg):
                emb = msg.embeds[0]
                # If on the right branch, grab the short SHA for this commit
                if emb.title.startswith(f'[{conf.BRANCH}]'):
                    remsha = emb.description[1: emb.description.find(']')]
                    self.remsha = remsha[1:-1]
                    break

        # Grab the SHA for most recent local commit (strip enclosing quotes)
        sp = subprocess.run(['git', 'show', '--pretty=format:"%H"', '--no-notes', '--no-patch'], stdout=subprocess.PIPE, encoding='utf-8')
        self.mysha = sp.stdout[1:-1]

    @commands.command(name="gupdate")
    async def do_git_update(self, ctx):
        await ctx.send(f'Checking {self.mysha} versus remote {self.remsha}...')
        if self.mysha.startswith(self.remsha):
            await ctx.send(f'No update needed.')
        else:
            async with ctx.typing():
                sp = subprocess.run(['git', 'pull', '--ff-only'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
                await ctx.send(f'Updated:\n{sp.stdout}\n{sp.stderr}')

    @commands.command(name="remsha")
    async def show_remote_latest_sha(self, ctx):
        await ctx.send(f"Remote's most recent commit: SHA = {self.remsha}")

    @commands.command(name="mysha")
    async def show_my_latest_sha(self, ctx):
        await ctx.send(f'My most recent commit: SHA = {self.mysha}')

def setup(bot):
    the_cog = GitHubUpdate(bot)
    bot.add_cog(the_cog)

    # botcore will autorun this after loading
    @commands.command()
    async def post_init(ctx):
        await the_cog.get_latest_sha(ctx)
    bot.add_command(post_init)
