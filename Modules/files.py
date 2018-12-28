import discord
from discord.ext import commands
import os

datapath = 'Data'
bot = commands.Bot(command_prefix=['m!', 'm! '])


class SpaceError(Exception):
    pass


class FilenameError(Exception):
    pass


class Save:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='import', aliases=['save'])
    async def importer(self, ctx, inputtype: str, filname: str, *rest):
        """import a file or direct text into your personal folder"""
        filename = filname + '.txt'
        if inputtype == 'file':
            tempfile = 'Data/Temps/temp.txt'
            if len(ctx.message.attachments) != 0:
                await ctx.message.attachments[0].save(tempfile)
            else:
                findfile = False
                async for mess in ctx.channel.history(limit=10):
                    if len(mess.attachments) != 0:
                        await mess.attachments[0].save(tempfile)
                        findfile = True
                        break

                if not findfile:
                    ctx.send('File not found.')
                    return

            file = open(tempfile, 'r+')
            try:
                text = file.read()
            except Exception as e:
                await message.channel.send(e)
                os.remove(tempfile)
                return

            try:
                embed = await Files.save_file(text, ctx.author, filename)
            except SpaceError as e:
                await ctx.send(embed=space_embed(ctx.author))
                return
            except FilenameError as e:
                await ctx.send('Not a valid filename.')
                return

            os.remove(tempfile)

            await ctx.send(embed=embed)

        elif inputtype == 'text':
            try:
                embed = await Files.save_file(' '.join(rest), ctx.author, filename)
            except SpaceError as e:
                await ctx.send(embed=space_embed(ctx.author))
                return
            except FilenameError as e:
                await ctx.send('Not a valid filename.')
                return

            await ctx.send(embed=embed)
        else:
            ctx.send('Not a valid type (Must be either ``file`` or ``text``)')


class Files:
    maxsize = 100000000

    def __init__(self, bot):
        self.bot = bot
        self.temp = '{0}/{1}/'.format(datapath, 'Temps')

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

    def dirsize(path):
        return sum(os.path.getsize(path + '/' + f) for f in os.listdir(path) if os.path.isfile(path + '/' + f))

    def dircount(path):
        return sum(1 for f in os.listdir(path) if os.path.isfile(path + '/' + f))

    @classmethod
    async def save_file(self, filecontent, user, filename):
        path = self.get_userpath(user)
        filepath = '{}/{}'.format(path, filename)
        self.create_folder(self.get_userpath(user))
        size = self.dirsize(path)

        file = open(filepath, 'w+')
        file.write(filecontent)
        file.close()

        if self.dirsize(path) > self.maxsize:
            os.remove(filepath)
            raise SpaceError

        if len(os.path.split(os.path.realpath(file.name))[1]) < 5:
            os.remove(filepath)
            raise FilenameError

        length = len(filecontent)
        filesize = os.path.getsize(filepath)
        start = filecontent[0:min(length, 200)]
        size = self.dirsize(path)
        fileamount = self.dircount(path)

        embed = discord.Embed(title='File succesfully saved',
                              description='Saved as ``{}.txt``'.format(filename),
                              color=0x22f104)
        embed.add_field(name='Filesize:', value='{} bytes'.format(filesize), inline=True)
        embed.add_field(name='Charaters:', value='{} characters'.format(length), inline=True)
        embed.add_field(name='Storage', value='User {} has used {}/{} ({}%) of their space. With a total of {} files.'.format(user, size, self.maxsize, round(size / self.maxsize * 100), fileamount))
        embed.add_field(name='Beginning:', value='``{}``'.format(start), inline=False)

        return embed


def setup(bot):
    bot.add_cog(Save(bot))
    bot.add_cog(Files(bot))
