#!/usr/bin/env python3
"""
ghupdate.py

Discord bot extension for grabbing GitHub updates; WIP.
"""

import subprocess
import discord.utils
from discord.ext import commands
from omegaconf import OmegaConf

GIT_NOPULL = 'Already up to date.'

class GitHubUpdate(commands.Cog, name ='ghupdate'):
    def __init__(self, bot, config):
        super().__init__()
        # The bot running this cog
        self.bot = bot
        # Information about the Discord webhook:
        self.HOOK_GUILDNAME = config.HOOK_GUILDNAME
        self.HOOK_URL = config.HOOK_URL
        self.hook = None
        self.hook_chan = None
        # Remote and local commit SHAs
        self.remsha = None
        self.mysha = None
        # GitHub Repo and branch information:
        self.branch_tag = f'[{config.GH_REPO}:{config.BRANCH}]'

    async def post_init(self, ctx=None):
        """Do async things after extension setup."""
        # Use the webhook to find its channel; store for later use.
        self.guild = discord.utils.find(lambda g: g.name == self.HOOK_GUILDNAME, self.bot.guilds)
        guildhooks = await self.guild.webhooks()
        self.hook = discord.utils.find(lambda h: h.url == self.HOOK_URL, guildhooks)
        self.hook_chan = self.hook.channel

        # Check for updates and reload if needed.
        msg_chan = self.bot.lobby  # TODO: Change to self.hook_chan
        await msg_chan.send(f'Auto-checking for repository updates on {self.branch_tag}...')
        await self.get_latest_sha()
        if self.mysha.startswith(self.remsha):
            await msg_chan.send('...no update neeed.')
        else:
            await msg_chan.send(' ...attemping automatic update...')
            update_msg = await self.do_git_update()
            if update_msg:
                await msg_chan.send(update_msg)

    async def do_git_update(self):
        """Do a git pull and reload any updates."""
        sp = subprocess.run(['git', 'pull', '--ff-only'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
        if sp.returncode:   # Meaning git pull returned an error
            raise RuntimeError(f'Git pull failed:\n{sp.stdout}\n{sp.stderr}')
        else:
            if sp.stdout.strip() == GIT_NOPULL:
                return ' ...local repo is ahead of remote?'
            else:
                return sp.stdout
                # TODO: Determine if other extensions need to be reloaded.

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

    @commands.command(name="shasha", help="Show most recent remote/local commits.")
    async def show_latest_shas(self, ctx):
        await ctx.send(f'* Remote SHA: {self.remsha}\n* Bot SHA: {self.mysha[:7]}')


def setup(bot):
    CONFIG = OmegaConf.load('config.yaml').ghupdate
    the_cog = GitHubUpdate(bot, CONFIG)
    bot.add_cog(the_cog)
