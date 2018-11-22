import praw
import json
import discord
import time
import os

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


@client.event
async def on_message(message):
    msg = parse_message(message.content)
    if not msg:
        return
    else:
        if msg[0] == 'harvest':

            if msg[1] == 'reddit':
                try:
                    subreddit = reddit.subreddit(msg[2])
                    posts = subreddit.new(limit=1)
                    for post in posts:
                        print(post.title)
                except:
                    await message.channel.send(msg[2] + ' is not a valid subreddit')
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
                            await message.channel.send('argument has to be [titles,posts,comments]\ncan\'t be ' + msg[4])
                            return

                else:

                    try:
                        msg[5] = int(msg[5])
                        if not (msg[5] > 5 and msg[5] < 500):
                            await message.channel.send('argument has to be [5 < arg < 500] \ncan\'t be ' + str(msg[5]))
                            return
                    except:
                        await message.channel.send('argument has to be [Integer, 5 < arg < 500] \ncan\'t be ' + msg[5])
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
                                await message.channel.send('top specifications have to be written like this: ``top(month)``')
                                return
                        print('top(' + (str(msg[3])[4:len(msg[3]) - 1]) + ')')
                    else:
                        await message.channel.send('argument has to be [new,hot,top] \ncan\'t be ' + msg[3])
                        return

                    embed = discord.Embed(title='Searching 🔎', url='https://old.reddit.com/r/{}/{}'.format(msg[2], msg[3]), description='Searching the first {} {} in {} of {}'.format(msg[5], msg[4], msg[3], msg[2]), color=0x22f104)
                    searchtime = time.time()

                    data = []
                    if msg[4] == 'titles':
                        await message.channel.send(embed=embed)
                        async with message.channel.typing():
                            for submission in posts:
                                data.append(submission.title)
                    elif msg[4] == 'posts':
                        await message.channel.send(embed=embed)
                        async with message.channel.typing():
                            for submission in posts:
                                data.append(submission.posts)
                    elif msg[4] == 'comments':
                        await message.channel.send(embed=embed)
                        async with message.channel.typing():
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
                        await message.channel.send('argument has to be [titles,posts,comments] \ncan\'t be ' + msg[4])
                        return

                    print(data)
                    embed = discord.Embed(title='Finished Searching', url='https://old.reddit.com/r/{}/{}'.format(msg[2], msg[3]), description='Found {} results.\nThe search took {} seconds'.format(len(data), time.time() - searchtime), color=0x22f104)
                    await message.channel.send(embed=embed)

                    unique_name = message.author.name + '#' + message.author.discriminator
                    create_subfolder('Data/' + unique_name)
                    filename = 'Data/{}/{}-{}-{}.txt'.format(unique_name, msg[2], msg[3], time.ctime())
                    file = open(filename, 'w+')
                    for element in data:
                        file.write(element)
                        file.write('\n')
                    file.close()

                    await message.channel.send(file=discord.File(filename))


client.run(discordtoken)
