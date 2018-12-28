from discord.ext import commands
import discord

import json

tokenfile = open('tokens.json', 'r')
tokens = json.load(tokenfile)
bot = commands.Bot(command_prefix=['m!', 'm! '])

startup_extensions = ['files']


@bot.event
async def on_ready():
    print('Logged in as:\n{0} (ID: {0.id})'.format(bot.user))


if __name__ == '__main__':
    for extension in startup_extensions:
        try:
            bot.load_extension('Modules.{}'.format(extension))
            print('{} extension loaded'.format(extension))
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load extension {}\n{}'.format(extension, exc))
    bot.run(tokens['Discord']['token'])
