import praw
import json
import discord
import time
import os
import asyncio

tokenfile = open('tokens.json', 'r')
tokens = json.load(tokenfile)
discordtoken = tokens['Discord']['token']
reddittokens = tokens['Reddit']

reddit = praw.Reddit(client_id=reddittokens['client_id'],
                     client_secret=reddittokens['client_secret'],
                     username=reddittokens['username'],
                     password=reddittokens['password'],
                     user_agent=reddittokens['user_agent'])

client = discord.Client()
prefix = 'm!'
maxsize = 100


@client.event
async def on_ready():
    print('bot ready')


class InputError(Exception):
    pass


class SpaceError(Exception):
    pass


class FilenameError(Exception):
    pass


def create_subfolder(name):
    dirname = os.path.dirname(__file__)
    create_folder(dirname + '/' + name)
    return dirname + '/' + name


def create_folder(path):
    try:
        if os.path.isdir(path):
            print("Error: The directory you're attempting to create already exists")  # or just pass
        else:
            os.makedirs(path)
    except IOError as exception:
        raise IOError('%s: %s' % (path, exception.strerror))
    return None


def parse_message(message):
    if message.startswith(prefix):
        parsed_message = message[len(prefix):]
        parsed_message = parsed_message.split(' ')
        parsed_message = parsed_message[1:]
        for i in range(1, 10):
            parsed_message.append('``empty``')
        print(parsed_message)
        return parsed_message
    else:
        return False


async def reddit_harvest_start(msg):
    try:
        subreddit = reddit.subreddit(msg[2])
        posts = subreddit.new(limit=1)
        for post in posts:
            print(post.title)
    except Exception as e:
        raise InputError(msg[2] + ' is not a valid subreddit')
        return

    if msg[3] == 'stream':
        if msg[4] == 'comments':
            # TODO
            print('stream comments')
        else:
            posts = subreddit.stream.submissions()
            if msg[4] == 'titles':
                # TODO
                print('stream titles')
            elif msg[4] == 'posts':
                # TODO
                print('stream posts')
            else:
                raise InputError('argument has to be [titles,posts,comments]\ncan\'t be ' + msg[4])
                return

    else:

        try:
            msg[5] = int(msg[5])
            if not (msg[5] > 5 and msg[5] < 500):
                raise InputError('argument has to be [5 < arg < 500] \ncan\'t be ' + str(msg[5]))
                return
        except:
            raise InputError('argument has to be [Integer, 5 < arg < 500] \ncan\'t be ' + msg[5])
            return

        if msg[3] == 'new':
            posts = subreddit.new(limit=msg[5])
            print('new')
        elif msg[3] == 'hot':
            posts = subreddit.hot(limit=msg[5])
            print('hot')
        elif str(msg[3])[:3] == 'top':
            if len(msg[3]) != 3:
                try:
                    posts = subreddit.top(str(msg[3])[4:len(msg[3]) - 1], limit=msg[5])
                except:
                    print(str(msg[3])[4:len(msg[3]) - 1])
                    raise InputError('top specifications have to be written like this: ``top(month)``')
                    return
                print('top(' + (str(msg[3])[4:len(msg[3]) - 1]) + ')')
            else:
                posts = subreddit.top(limit=msg[5])
        else:
            raise InputError('argument has to be [new,hot,top] \ncan\'t be ' + msg[3])
            return

        return posts


async def reddit_harvest(msg, channelid, posts):
    embed = discord.Embed(title='Searching 🔎', url='https://old.reddit.com/r/{}/{}'.format(msg[2], msg[3]), description='Searching the first {} {} in {} of {}'.format(msg[5], msg[4], msg[3], msg[2]), color=0x22f104)
    channel = client.get_channel(channelid)

    data = []
    if msg[4] == 'titles':
        await channel.send(embed=embed)
        async with channel.typing():
            for submission in posts:
                data.append(submission.title)
    elif msg[4] == 'posts':
        await channel.send(embed=embed)
        async with channel.typing():
            for submission in posts:
                data.append(submission.selftext)
    elif msg[4] == 'comments':
        await channel.send(embed=embed)
        async with channel.typing():
            i = 0
            for submission in posts:
                submission.comments.replace_more(limit=None)
                for comment in submission.comments.list():
                    data.append(comment.body)
                    i += 1
                    print(i)
                    if i >= msg[5]:
                        break
                if i >= msg[5]:
                    break
                print(i)
    else:
        raise InputError('argument has to be [titles,posts,comments] \ncan\'t be ' + msg[4])
        return

    return data


async def get_text(msgid, channelid, msg):
    channel = client.get_channel(channelid)
    message = await channel.get_message(msgid)

    await message.channel.send('Please paste your text here:')

    def check(m):
        return m.author == message.author and m.channel == message.channel
    try:
        text = await client.wait_for('message', check=check, timeout=20.0)
    except asyncio.TimeoutError:
        await message.channel.send('You took too long...')
        return False
    if msg[2] == '``empty``':
        await message.channel.send('Enter Filename:'.format(message))
        try:
            filename = await client.wait_for('message', check=check, timeout=20.0)
            filename = filename.content
        except asyncio.TimeoutError:
            await message.channel.send('You took too long...')
            return False
    else:
        filename = msg[2]

    returning = [filename, text]
    return returning


async def save_text(msgid, channelid, msg, filename, text):
    channel = client.get_channel(channelid)
    message = await channel.get_message(msgid)

    filename2 = 'Data/{}/{}.txt'.format(message.author, filename)

    try:
        await save_file(message.author, filename, text.content)
        return True
    except SpaceError as e:
        await message.channel.send(embed=space_embed(message.author))
        return False
    except FilenameError as e:
        await message.channel.send('Not a valid filename.')
        return False


async def find_file(msgid, channelid, msg, filename):
    channel = client.get_channel(channelid)
    message = await channel.get_message(msgid)

    if len(message.attachments) != 0:
        await message.attachments[0].save(filename)
    else:
        findfile = False
        async for mess in message.channel.history(limit=3):
            if len(mess.attachments) != 0:
                await mess.attachments[0].save(filename)
                findfile = True
                break
        if not findfile:
            await message.channel.send('Please send your file here:')

            def check(m):
                check1 = m.author == message.author and m.channel == message.channel
                check2 = len(m.attachments) != 0
                return check1 and check2
            try:
                mess = await client.wait_for('message', check=check, timeout=20.0)
            except asyncio.TimeoutError:
                await message.channel.send('You took too long...')
                os.remove(filename)
                return False

            await mess.attachments[0].save(filename)

    return True


def dirsize(path):
    return sum(os.path.getsize(path + '/' + f) for f in os.listdir(path) if os.path.isfile(path + '/' + f))


async def save_file(user, filename, filecontent):
    path = 'Data/{}'.format(user)
    size = dirsize(path)

    filesize = len(filecontent) * 1.1

    if size + filesize > maxsize:
        raise SpaceError
    else:
        file = open('{}/{}.txt'.format(path, filename), 'w+')
        file.write(filecontent)
        file.close()

        if len(os.path.split(os.path.realpath(file.name))[1]) < 5:
            os.remove(os.path.realpath(file.name))
            raise FilenameError


def space_embed(user):
    embed = discord.Embed(title='Not enough Space',
                          description='You already used {}/{} of your storage. \n (The file you are trying to save is too large)'.format(dirsize('Data/{}'.format(user)), maxsize),
                          color=0xff0000)
    return embed


@client.event
async def on_message(message):
    msg = parse_message(message.content)
    if not msg:
        return

    msgid = message.id
    channelid = message.channel.id

    if msg[0] == 'harvest':

        if msg[1] == 'reddit':
            try:
                posts = await reddit_harvest_start(msg)
            except InputError as e:
                await message.channel.send(e.args[0])
                return

            searchtime = time.time()

            try:
                data = await reddit_harvest(msg, message.channel.id, posts)
            except InputError as e:
                await message.channel.send(e.args[0])
                return

            print(data)
            embed = discord.Embed(title='Finished Searching', url='https://old.reddit.com/r/{}/{}'.format(msg[2], msg[3]),
                                  description='Found {} results.\nThe search took {} seconds'.format(len(data), time.time() - searchtime),
                                  color=0x22f104)
            await message.channel.send(embed=embed)

            unique_name = message.author.name + '#' + message.author.discriminator
            create_subfolder('Data/' + unique_name + '/Text')
            filename = 'Data/{}/{}-{}-{}.txt'.format(unique_name, msg[2], msg[3], time.ctime())
            file = open(filename, 'w+')
            for element in data:
                file.write(element)
                file.write('\n')
            file.close()

            await message.channel.send(file=discord.File(filename))
            os.remove(filename)

            await message.channel.send('To save this file for later use, use ``{} save file <your_chosen_filename>``'.format(prefix))

    if msg[0] == 'save':

        if msg[1] == 'text':

            returning = await get_text(msgid, channelid, msg)
            if not returning:
                return

            if not await save_text(msgid, channelid, msg, returning[0], returning[1]):
                return

            filename = returning[0]

            embed = discord.Embed(title='Text succesfully saved',
                                  description='Saved as ``{}.txt``'.format(filename),
                                  color=0x22f104)
            await message.channel.send(embed=embed)

        if msg[1] == 'file':

            filename = 'Data/{}/tempfile.txt'.format(message.author)

            if not await find_file(msgid, channelid, msg, filename):
                print('huh')
                return

            file = open(filename, 'r+')

            try:
                text = file.read()
            except Exception as e:
                await message.channel.send(e)
                os.remove(filename)
                return
            length = len(text)
            size = os.path.getsize(filename)
            if size > 1000000:
                await message.channel.send('File too large')
                os.remove(filename)
                return
            start = text[0:min(length, 200)]

            if msg[2] == '``empty``':
                await message.channel.send('Enter Filename:'.format(message))

                def check2(m):
                    return m.author == message.author and m.channel == message.channel
                try:
                    filename2 = await client.wait_for('message', check=check2, timeout=20.0)
                    filename2 = filename2.content
                except asyncio.TimeoutError:
                    await message.channel.send('You took too long...')
                    return
            else:
                filename2 = msg[2]

            filename3 = 'Data/{}/{}.txt'.format(message.author, filename2)

            try:
                file = open(filename3, 'w+')
                file.write(text)
            except Exception as e:
                await message.channel.send('Not a valid filename.')
                print(e)
                return

            file.close()
            os.remove(filename)

            embed = discord.Embed(title='File succesfully saved',
                                  description='Saved as ``{}.txt``'.format(filename2),
                                  color=0x22f104)
            embed.add_field(name='Filesize:', value='{} bytes'.format(size), inline=True)
            embed.add_field(name='Charaters:', value='{} characters'.format(length), inline=True)
            embed.add_field(name='Beginning:', value='``{}``'.format(start), inline=False)
            await message.channel.send(embed=embed)

    if msg[0] == 'logs':
        async for mess in message.channel.history(limit=2):
            print(mess.content)

    if msg[0] == 'size':
        print(dir_size('Data/{}/'.format(message.author)))

    if msg[0] == 'folder':
        path = 'Data/{}/'.format(message.author)
        for f in os.listdir(path):
            print(os.path.getsize('{}/{}'.format(path, f)))


client.run(discordtoken)
