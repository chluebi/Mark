import praw
import json
import discord
from discord.ext import commands
import time
import os
import asyncio
import markovify

tokenfile = open('tokens.json', 'r')
tokens = json.load(tokenfile)
datapath = 'Data'

bot = commands.Bot(command_prefix=['m!', 'm! '])


class Files:
    def __init__(self, bot):
        self.bot = bot
        self.temp = '{0}/{1}/'.format(datapath, 'Temps')

    @classmethod
    @staticmethod
    def get_userpath(user):
        return '{0}/{1}/'.format(datapath, user)

    def create_folder(path):
        try:
            if os.path.isdir(path):
                print("Error: The directory you're attempting to create already exists")  # or just pass
            else:
                os.makedirs(path)
        except IOError as exception:
            raise IOError('%s: %s' % (path, exception.strerror))
        return None


bot.add_cog(Files(bot))


@bot.event
async def on_ready():
    print('Logged in as:\n{0} (ID: {0.id})'.format(bot.user))

bot.run(tokens['Discord']['token'])
