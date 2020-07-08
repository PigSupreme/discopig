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
    def __init__(self, bot, branch=None):
        self.bot = bot
        self.hook = None
        self.hook_chan = None
        self.remsha = None
        self.mysha = None
        self.branch_tag = f'[{conf.GH_REPO}:{branch}]'

    # botcore will autorun this after loading
    @commands.command(help="Pay no attention to the man behind the curtain.")
    async def post_init(self, ctx=None):
        """Do async things on startup/reload."""
        # Use the webhook to find its channel; store for later use.
        # Can't do this in setup/__init__ since Guild.webhooks() is a coro.
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
            await ctx.send(f'Auto-checking for repository updates on {self.branch_tag}...')
            await ctx.invoke(self.get_latest_sha)
            if self.mysha.startswith(self.remsha):
                await ctx.send('...no update neeed.')
            else:
                await self.do_git_update()
        else:
            print('Dynamic reload?')
            await self.hook_chan.send('Dynamic reload successful!')

    def is_from_webhook(self, msg):
        """Used internally to ignore anything except GitHub webhook updates."""
        if self.hook_chan and msg.channel != self.hook_chan:
            return
        if msg.webhook_id and msg.webhook_id == self.hook.id:
            return msg.author.name == 'GitHub'

    async def last_hook_commit_msg_embed(self):
        # Find the last message posted by the webhook from GitHub...
        # ...but make sure it matches our current branch.
        async for msg in self.hook_chan.history():
            if self.is_from_webhook(msg):
                emb = msg.embeds[0] # There should be only one!
                if emb.title.startswith(self.branch_tag):
                    return emb

    @commands.Cog.listener()
    async def on_message(self, msg):
        """Listen for GitHub webhooks events and check for updates."""
        if self.is_from_webhook(msg):
            await self.get_latest_sha(None)
            if self.mysha.startswith(self.remsha):
                await msg.channel.send(f'No update needed.')
            else:
                await msg.channel.send(f'Attempting update to {self.remsha}...')
                await self.do_git_update()

    @commands.command(name="findsha")
    @commands.is_owner()
    async def get_latest_sha(self, ctx=None):
        """Re-check for the most recent remote/local commits."""
        emb = await self.last_hook_commit_msg_embed()
        remsha = emb.description[1: emb.description.find(']')]
        self.remsha = remsha[1:-1]

        # Grab the SHA for most recent local commit (strip enclosing quotes)
        sp = subprocess.run(['git', 'show', '--pretty=format:"%H"', '--no-notes', '--no-patch'], stdout=subprocess.PIPE, encoding='utf-8')
        self.mysha = sp.stdout[1:-1]

        # If invoked as a command, report the results
        if ctx:
            await ctx.invoke(self.show_latest_shas)

    @commands.command(name="gupdate", help="Manual update (TODO: just use git pull?)")
    @commands.is_owner()
    async def check_for_updates(self, ctx):
        # TODO: Use git pull here instead?
        await ctx.send(f'Manually checking for updates on {self.branch_tag}...')
        await ctx.invoke(self.get_latest_sha)
        if self.mysha.startswith(self.remsha):
            await ctx.send('...no update neeed.')
        else:
            await self.do_git_update()

    async def do_git_update(self):
        """Do a git pull and reload the cog if needed."""
        sp = subprocess.run(['git', 'pull', '--ff-only'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
        if sp.returncode:   # Meaning git pull returned an error
            raise RuntimeError(f'Git pull failed:\n{sp.stdout}\n{sp.stderr}')
        # TODO: Determine what actually needs to be reloaded.
        # For now, just reload this cog.
        await self.bot.get_command('load_ext').__call__(None, 'ghupdate')

    @commands.command(name="shasha", help="Show most recent remote/local commits.")
    async def show_latest_shas(self, ctx):
        await ctx.send(f'* Remote SHA: {self.remsha}\n* Bot SHA: {self.mysha}')


def setup(bot):
    sp = subprocess.run(['git', 'branch', '--show-current'], stdout=subprocess.PIPE, encoding='utf-8')
    if sp.returncode:
        raise RuntimeError('Cannot get local git branch.')
    the_cog = GitHubUpdate(bot, sp.stdout.rstrip())
    bot.add_cog(the_cog)
