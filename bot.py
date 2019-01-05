import praw
import json
import discord
import time
import os
import asyncio
import markovify

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
maxsize = 10000000


@client.event
async def on_ready():
    print('bot ready')
    await client.change_presence(status=None, activity=discord.Game(name=prefix + 'help'))


class InputError(Exception):
    pass


class SpaceError(Exception):
    pass


class FilenameError(Exception):
    pass


class IntError(Exception):
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
        if parsed_message[0] != ' ':
            parsed_message = ' ' + parsed_message
        # parsed_message = parsed_message.split(' ')
        in_quotes = False
        parseder_message = []
        j = -1
        for i in range(len(parsed_message)):
            if parsed_message[i] == ' ':
                if in_quotes:
                    parseder_message[j] += parsed_message[i]
                else:
                    j += 1
                    parseder_message.append('')
            elif parsed_message[i] == '"':
                in_quotes = not in_quotes
            else:
                parseder_message[j] += parsed_message[i]
        parsed_message = parseder_message
        # parsed_message = parsed_message[1:]
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
            raise InputError('argument has to be [Integer, 5 < arg < 500] \ncan\'t be ' + str(msg[5]))
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
    if msg[4] == 'comments':
        embed.add_field(name='Info:', value='Harvesting comments can take up to 2 minutes', inline=False)
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
                submission.comments.replace_more(threshold=msg[5])
                for comment in submission.comments.list():
                    data.append(comment.body)
                    i += 1
                    print('comment:' + str(i))
                    if i >= msg[5]:
                        break
                if i >= msg[5]:
                    break
                print('new post')
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
        text = text.content
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


async def find_file(msgid, channelid, msg, filename):
    channel = client.get_channel(channelid)
    message = await channel.get_message(msgid)

    if len(message.attachments) != 0:
        await message.attachments[0].save(filename)
    else:
        findfile = False
        async for mess in message.channel.history(limit=10):
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
                return False

            await mess.attachments[0].save(filename)

    return True


def dirsize(path):
    return sum(os.path.getsize(path + '/' + f) for f in os.listdir(path) if os.path.isfile(path + '/' + f))


def dircount(path):
    return sum(1 for f in os.listdir(path) if os.path.isfile(path + '/' + f))


async def save_file(user, filename, filecontent):
    create_subfolder('Data/' + str(user))
    path = 'Data/{}/'.format(user)
    filepath = '{}/{}.txt'.format(path, filename)
    size = dirsize(path)

    file = open(filepath, 'w+')
    file.write(filecontent)
    file.close()

    if dirsize(path) > maxsize:
        os.remove(filepath)
        raise SpaceError

    if len(os.path.split(os.path.realpath(file.name))[1]) < 5:
        os.remove(filepath)
        raise FilenameError

    length = len(filecontent)
    filesize = os.path.getsize(filepath)
    start = filecontent[0:min(length, 200)]
    size = dirsize(path)
    fileamount = dircount(path)

    embed = discord.Embed(title='File succesfully saved',
                          description='Saved as ``{}.txt``'.format(filename),
                          color=0x22f104)
    embed.add_field(name='Filesize:', value='{} bytes'.format(filesize), inline=True)
    embed.add_field(name='Charaters:', value='{} characters'.format(length), inline=True)
    embed.add_field(name='Storage', value='User {} has used {}/{} ({}%) of their space. With a total of {} files.'.format(user, size, maxsize, round(size / maxsize * 100), fileamount))
    embed.add_field(name='Beginning:', value='``{}``'.format(start), inline=False)

    return embed


def space_embed(user):
    embed = discord.Embed(title='Not enough Space',
                          description='You already used {}/{} of your storage. \n (The file you are trying to save is too large)'.format(dirsize('Data/{}'.format(user)), maxsize),
                          color=0xff0000)
    return embed


def is_int(value, minimal, maximal):
    try:
        value2 = int(value)
        if not (value2 <= maximal and value2 >= minimal):
            raise IntError('argument has to be [{} < value < {}] \ncan\'t be {}'.format(minimal, maximal, value))
            return False
    except:
        raise IntError('argument has to be [Integer] \ncan\'t be {}'.format(value))

    return value2


def is_float(value, minimal, maximal):
    try:
        value2 = float(value)
        if not (value2 <= maximal and value2 >= minimal):
            raise IntError('argument has to be [{} < value < {}] \ncan\'t be {}'.format(minimal, maximal, value))
            return False
    except:
        raise IntError('argument has to be [Integer] \ncan\'t be {}'.format(value))

    return value2


def find_user(user, list):
    for member in list:
        if member.name.lower() == user.lower():
            return member.id
        if member.id == user.lower():
            return member.id
        if member.display_name.lower() == user.lower():
            return member.id
        if str(member).lower() == user.lower():
            return member.id

    return None


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

            try:
                embed = await save_file(message.author, returning[0], returning[1])
            except SpaceError as e:
                await message.channel.send(embed=space_embed(message.author))
                return
            except FilenameError as e:
                await message.channel.send('Not a valid filename.')
                return

            filename = returning[0]

            await message.channel.send(embed=embed)

        if msg[1] == 'file':

            tempfile = 'Data/Temps/tempfile.txt'.format(message.author)

            if msg[2] == '``empty``':
                await message.channel.send('Enter Filename:')

                def check2(m):
                    return m.author == message.author and m.channel == message.channel
                try:
                    filename = await client.wait_for('message', check=check2, timeout=20.0)
                    filename = filename.content
                except asyncio.TimeoutError:
                    await message.channel.send('You took too long...')
                    return
            else:
                filename = msg[2]

            if not await find_file(msgid, channelid, msg, tempfile):
                print('huh')
                return

            file = open(tempfile, 'r+')

            try:
                text = file.read()
            except Exception as e:
                await message.channel.send(e)
                os.remove(tempfile)
                return

            try:
                embed = await save_file(message.author, filename, text)
            except SpaceError as e:
                await message.channel.send(embed=space_embed(message.author))
                return
            except FilenameError as e:
                await message.channel.send('Not a valid filename.')
                return

            os.remove(tempfile)

            await message.channel.send(embed=embed)

    if msg[0] == 'markovify' or msg[0] == 'generate':

        try:
            msg[3] = is_int(msg[3], 1, 1000)
        except IntError as e:
            await message.channel.send(e.args[0])
            return

        if msg[4] != '``empthy``':
            try:
                msg[4] = is_float(msg[4], 0.2, 0.9)
            except IntError as e:
                await message.channel.send(e.args[0])
                return

        endcharacters = []
        if msg[5] != '``empthy``':
            try:
                end = msg[5]
                end = end[1:len(end) - 1]

                endarray = end.split('|')

                for char in endarray:
                    endcharacters.append(char[0])

                print(endcharacters)
            except Exception:
                print('duh')

        if msg[1] == 'fromfile':
            path = 'Data/{}/'.format(message.author)
            allfiles = [file.replace('.txt', '') for file in os.listdir(path)]
            print(allfiles)
            if msg[2] in allfiles:
                filename = os.listdir(path)[allfiles.index(msg[2])]
                file = open(os.path.join(path, filename), 'r+')
                filetext = file.read()
                file.close()

                for char in endcharacters:
                    filetext.replace(char, char + '\n')

                starttime = time.time()
                model = markovify.NewlineText(filetext)

                sentences = []
                async with message.channel.typing():
                    while len(sentences) < msg[3] and (time.time() - starttime) < 120:
                        sentence = model.make_short_sentence(200, tries=100, max_overlap_ratio=msg[4])
                        print(sentence)
                        if not sentence in sentences and sentence is not None:
                            sentences.append(sentence)

                sentences_text = '\n'.join(sentences)

                embed = discord.Embed(title='Generated Sentences',
                                      description='Generated {} sentences'.format(len(sentences),
                                                                                  color=0x22f104))
                embed.add_field(name='Time: ', value='It took {} seconds.'.format(round((time.time() - starttime) * 100) / 100), inline=False)
                if len(sentences_text) < 1000:
                    embed.add_field(name='Text: ', value='```\n{}\n```'.format(sentences_text), inline=False)
                else:
                    for i in range(min(round(len(sentences_text) / 1000), 5)):
                        embed.add_field(name='Text: ', value='```\n{}\n```'.format(sentences_text[i * 1000:(i + 1) * 1000]), inline=False)

                await message.channel.send(embed=embed)

                filename = 'Data/Temps/generated.txt'
                file = open(filename, 'w+')
                file.write(sentences_text)
                file.close()

                await message.channel.send(file=discord.File(filename))
                os.remove(filename)
            else:
                await message.channel.send('File not found, use ``{} user {}`` to show your files'.format(prefix, message.author))

    if msg[0] == 'user':
        user = find_user(msg[1], message.channel.guild.members)
        user = client.get_user(user)
        path = 'Data/{}/'.format(user)

        if user == None:
            await message.channel.send('User {} not found'.format(msg[1]))
        else:
            embed = discord.Embed(title=user.display_name, description='{0.name}#{0.discriminator}'.format(user), color=0x00fbff)
            embed.set_thumbnail(url=user.avatar_url)
            if os.path.isdir('Data/{}/'.format(user)):
                embed.add_field(name='size', value='{} bytes'.format(dirsize(path)), inline=True)
                embed.add_field(name='amount', value='{} files'.format(dircount(path)), inline=True)
                allfiles = ''
                for f in os.listdir(path):
                    if os.path.isfile(path + '/' + f):
                        allfiles = '{}{} || {} bytes \n'.format(allfiles, f, os.path.getsize(path + '/' + f))
                embed.add_field(name='files', value=allfiles, inline=False)
            await message.channel.send(embed=embed)

    if msg[0] == 'delete':
        if os.path.isfile('Data/{}/{}'.format(message.author, msg[1])) or os.path.isfile('Data/{}/{}.txt'.format(message.author, msg[1])):
            await message.channel.send('Please write ``confirm`` to confirm to delete ``{}``'.format(msg[1]))

            def check(m):
                return m.author == message.author and m.channel == message.channel and m.content == 'confirm'
            try:
                text = await client.wait_for('message', check=check, timeout=10.0)
                text = text.content
            except asyncio.TimeoutError:
                await message.channel.send('You took too long...')
                return
            else:
                if msg[1].endswith('.txt'):
                    os.remove('Data/{}/{}'.format(message.author, msg[1]))
                else:
                    os.remove('Data/{}/{}.txt'.format(message.author, msg[1]))
                await message.channel.send('File removed')
        else:
            await message.channel.send('File ``{}`` not found'.format(msg[1]))

    if msg[0] == 'deepfry':
        try:
            msg[3] = is_int(msg[3], 1, 1000)
        except IntError as e:
            await message.channel.send(e.args[0])
            return

        if msg[4] != '``empthy``':
            try:
                msg[4] = is_float(msg[4], 0.4, 0.9)
            except IntError as e:
                await message.channel.send(e.args[0])
                return
        try:
            msg[5] = is_int(msg[5], 1, 100000)
        except IntError as e:
            await message.channel.send(e.args[0])
            return
        endcharacters = []
        if msg[6] != '``empthy``':
            try:
                end = msg[6]
                end = end[1:len(end) - 1]

                endarray = end.split('|')

                for char in endarray:
                    endcharacters.append(char[0])

                print(endcharacters)
            except Exception:
                print('duh')

        if msg[1] == 'fromfile':
            path = 'Data/{}/'.format(message.author)
            allfiles = [file.replace('.txt', '') for file in os.listdir(path)]
            print(allfiles)
            if msg[2] in allfiles:
                filename = os.listdir(path)[allfiles.index(msg[2])]
                file = open(os.path.join(path, filename), 'r+')
                filetext = file.read()
                file.close()

                for char in endcharacters:
                    filetext.replace(char, char + '\n')

                starttime = time.time()

                sentences = filetext
                async with message.channel.typing():
                    model = markovify.NewlineText(sentences)
                    sentences = []
                    i = 0
                    while i < msg[5] and (time.time() - starttime) < 180:
                        i += 1
                        while len(sentences) < msg[3] and (time.time() - starttime) < 180:
                            sentence = model.make_sentence(tries=100, max_overlap_ratio=msg[4])
                            print(sentence)
                            if not sentence in sentences and sentence is not None:
                                sentences.append(sentence)
                        sentences_text = '\n'.join(sentences)
                        print('layer {} done'.format(i))

                embed = discord.Embed(title='Deepfried Sentences',
                                      description='Generated {} sentences'.format(len(sentences),
                                                                                  color=0x22f104))
                embed.add_field(name='Time: ', value='It took {} seconds.'.format(round((time.time() - starttime) * 100) / 100), inline=False)
                if len(sentences_text) < 1000:
                    embed.add_field(name='Text: ', value='```\n{}\n```'.format(sentences_text), inline=False)
                else:
                    for i in range(min(round(len(sentences_text) / 1000), 5)):
                        embed.add_field(name='Text: ', value='```\n{}\n```'.format(sentences_text[i * 1000:(i + 1) * 1000]), inline=False)

                await message.channel.send(embed=embed)

                filename = 'Data/Temps/generated.txt'
                file = open(filename, 'w+')
                file.write(sentences_text)
                file.close()

                await message.channel.send(file=discord.File(filename))
                os.remove(filename)
            else:
                await message.channel.send('File not found, use ``{} user {}`` to show your files'.format(prefix, message.author))

    if msg[0] == 'invite':
        await message.channel.send('Invite link: <{}>'.format('https://discordapp.com/oauth2/authorize?client_id=506186669842628628&scope=bot&permissions=3072'))

    if msg[0] == 'help' or msg[0] == 'info':
        embed = discord.Embed(title='Help menu', description='This is fun text manipulation bot.', color=0x22f104)
        embed.add_field(name='Prefix', value=prefix)
        cmd = []
        cmd.append('``harvest reddit <subreddit> [new|hot|top([hour,day,week,month,year])] [titles|posts|comments] <amount:10-500>``')
        cmd[0] = cmd[0] + '\n Gets the specified amount of content from a subreddit. (Comments take up to 3 minutes)'
        cmd.append('``save [file|text] <filename>``')
        cmd[1] = cmd[1] + '\n Saves content to your personal storage for later use. If ``file`` is given, you need to send a file with the message.'
        cmd.append('``delete <filename>``')
        cmd[2] = cmd[2] + '\n Deletes a file in your storage.'
        cmd.append('``generate fromfile <filename> <amount> <max_overlap_ratio:0.3-0.9> *<split_characters>``')
        cmd[3] = cmd[3] + '\n Generates Markov sentences and sends them as file.'
        cmd[3] = cmd[3] + '\n max_overlap_ratio: The ratio of how much of the generated sententes can be the same as the training data'
        cmd[3] = cmd[3] + '\n split_characters: The characters you want the text to be split by into sentences, the default is just line breaks. '
        cmd[3] = cmd[3] + 'You write it as the following: (character1|character2|...) example: (.|!|?)'
        cmd.append('``deepfry fromfile <filename> <amount> <max_overlap_ratio:0.3-0.9> <repetitions> *<split_characters>``')
        cmd[4] = cmd[4] + '\n This is the same as ``generate`` but instead of doing it once it does it ``<repetions>`` amount of times and uses its output as input everytime.'
        cmd.append('``user <username>``')
        cmd[5] = cmd[5] + '\n Display user info.'

        for c in cmd:
            embed.add_field(name=c.split('\n')[0], value='\n'.join(c.split('\n')[1:]))
        embed.add_field(name='Invite link:', value='<https://discordapp.com/oauth2/authorize?client_id=506186669842628628&scope=bot&permissions=3072>')
        await message.channel.send(embed=embed)

    '''
    if msg[0] == 'logs':
        async for mess in message.channel.history(limit=2):
            print(mess.content)

    if msg[0] == 'size':
        print(dirsize('Data/{}/'.format(message.author)))

    if msg[0] == 'folder':
        path = 'Data/{}/'.format(message.author)
        for f in os.listdir(path):
            print(os.path.getsize('{}/{}'.format(path, f)))
    '''


client.run(discordtoken)
