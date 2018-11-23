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


@client.event
async def on_ready():
    print('bot ready')


class InputError(Exception):
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


async def reddit_harvest(msg, channelid, embed, posts):
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


@client.event
async def on_message(message):
    msg = parse_message(message.content)
    if not msg:
        return

    if msg[0] == 'harvest':

        if msg[1] == 'reddit':
            try:
                posts = await reddit_harvest_start(msg)
            except InputError as e:
                await message.channel.send(e.args[0])
                return

            embed = discord.Embed(title='Searching 🔎', url='https://old.reddit.com/r/{}/{}'.format(msg[2], msg[3]), description='Searching the first {} {} in {} of {}'.format(msg[5], msg[4], msg[3], msg[2]), color=0x22f104)
            searchtime = time.time()

            try:
                data = await reddit_harvest(msg, message.channel.id, embed, posts)
            except InputError as e:
                await message.channel.send(e.args[0])
                return

            print(data)
            embed = discord.Embed(title='Finished Searching', url='https://old.reddit.com/r/{}/{}'.format(msg[2], msg[3]), description='Found {} results.\nThe search took {} seconds'.format(len(data), time.time() - searchtime), color=0x22f104)
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


client.run(discordtoken)
