import discord
from discord.ext import commands
import discord.utils
from discord import Color
import asyncio
from translate import Translator
import datetime as dt
from datetime import datetime
import time
import pytz
from PIL import Image
from random import randint
import os
from gtts import gTTS
import youtube_dl
from youtube_search import YoutubeSearch
import pymongo
import validators
from urllib.parse import urlparse
from functools import partial


mongo_pswrd = os.environ["MONGODB_PASSWORD"]
client = pymongo.MongoClient(f"mongodb+srv://RaucherAdler:{mongo_pswrd}@cluster0.klsio.mongodb.net/RoboterVogel?retryWrites=true&w=majority")
db = client["RoboterVogel"]


def add_to_queue(guild_id, attributes):
    g_coll = db[f"{guild_id}"]
    entries_doc = g_coll["entries"]
    position = entries_doc.count_documents({})
    attributes["id"] = position
    entries_doc.insert_one(attributes)
    return (position + 1)


def next_in_queue(guild_id):
    g_coll = db[f"{guild_id}"]
    entries = g_coll["entries"]
    entry = entries.find_one_and_delete({"id" : 0})
    np_coll = g_coll["now_playing"]
    if entry != None:
        np_coll.insert_one(entry)
    else:
        entry = entries.find_one_and_delete({})
        if entry != None:
            np_coll.insert_one(entry)
    entries.update_many({}, {"$inc" : {"id" : -1}})
    return entry


intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.presences = True


client = commands.AutoShardedBot(command_prefix = '/', intents=intents)


client.remove_command('help')


@client.event
async def on_ready():
   await client.change_presence(activity=discord.Activity(status=discord.Status.online, type=discord.ActivityType.playing, name=f'Your Mother in {len(client.guilds)} Servers'))
   print('Bot ist bereit!')


@client.event
async def on_member_join(member):
    g_coll = db[f"{member.guild.id}"]
    role_config = g_coll["role_config"]
    if role_config.find_one({}) != None:
        rc_doc = role_config.find_one({})
        channel_name = rc_doc["channel"]
        channelname = discord.utils.get(member.guild.channels, id=channel_name)
        await channelname.send(f'{member} ist {member.guild.name} beigetretten!')
        try:
            await member.send(f'Willkommen bei {member.guild.name}, {member.mention}!')
        except:
            pass
        role_id = rc_doc["role"]
        role = member.guild.get_role(role_id)
        await member.add_roles(role)
        await channelname.send(f'{member.mention} wurde die Rolle gegeben: {role}!')


@client.event
async def on_member_remove(member):
    g_coll = db[f"{member.guild.id}"]
    role_config = g_coll["role_config"]
    rc_doc = role_config.find_one({})
    channel_id = rc_doc["channel"]
    channelname = discord.utils.get(member.guild.channels, id=channel_id)
    if channelname != None:
        async for entry in member.guild.audit_logs(limit=1):
            if entry.action == 'kick' or entry.action == 'ban':
                if entry.user.id != member.id:
                    await channelname.send(f'{member} hat {member.guild.name} verlassen!')
            else:
                await channelname.send(f'{member} hat {member.guild.name} verlassen!')


@client.event
async def on_guild_join(guild):
    owner = guild.owner
    info_embed = discord.Embed(color=Color.dark_red())
    info_embed.add_field(name='Über Roboter Vogel:',value='\nRoboterVogel wurde von Raucher Adler#1521 gemacht!', inline=True)
    info_embed.add_field(name='Für mehr Information:', value='\nUse `/help` for a list of available commands or message me direcly.\n- Adler', inline=True)
    info_embed.set_footer(text=owner, icon_url=owner.avatar_url)
    if owner.bot == True:
        pass
    else:    
        await owner.send(f'Hallo, Ich bin RoboterVogel, dein neuer Bot!\nhttps://discord.gg/6GFQcFHjSK', embed=info_embed)
    await client.change_presence(activity=discord.Activity(status=discord.Status.online, type=discord.ActivityType.playing, name=f'Your Mother in {len(client.guilds)} Servers'))
    

@client.event
async def on_guild_remove(guild):
    await client.change_presence(activity=discord.Activity(status=discord.Status.online, type=discord.ActivityType.playing, name=f'Your Mother in {len(client.guilds)} Servers'))
    g_coll = db[guild.id]
    g_coll.drop()


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    raise error

class Moderation(commands.Cog):

    def __init__(self, client):
        self.client = client


    @client.command(description='Clears a given number of messages', usage='/clear <Number of posts>')
    @commands.has_permissions(manage_messages=True)
    async def clear(ctx, amount=0):
        await ctx.channel.purge(limit=amount+1)


    @client.command(description='Kicks a given user', usage='/kick <Mention User>')
    @commands.has_permissions(kick_members=True)
    async def kick(ctx, user: discord.Member, *, reason=None):
        await ctx.send('https://tenor.com/view/deathstar-gif-10649959')
        await ctx.send(f"{user} wurde getretten!")
        await user.kick(reason=reason)
        if user.bot != True:
            try:
                await user.send(f'Sie wurden vom {ctx.message.author} vom {ctx.guild.name} getretten!')
                if reason!= None:
                    await user.send(f'Grund: {reason}')
            except:
                pass


    @client.command(description='Bans a given user', usage='/ban <Mention User>')
    @commands.has_permissions(ban_members=True)
    async def ban(ctx, user: discord.Member, *, reason=None):
        await ctx.send('https://tenor.com/view/deathstar-gif-10649959')
        await ctx.send(f"{user} wurde verboten!")
        await user.ban(reason=reason, delete_message_days=0)
        if user.bot != True:
            try:
                await user.send(f'Sie wurden vom {ctx.message.author} vom {ctx.guild.name} gesperrt!')
                if reason != None:
                    await user.send(f'Grund: {reason}')
            except:
                pass


    @client.command(description='Unbans a given user', usage='/unban <Username (i.e. Raucher Adler#1220)>')
    @commands.has_permissions(ban_members=True)
    async def unban(ctx, *, member):
        banned_users = await ctx.guild.bans()
        member_name, member_discriminator = member.split('#')

        for ban_entry in banned_users:
            user = ban_entry.user

            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                await ctx.send(f'{user} wurde nicht verboten!')


    @client.command(description='Unbans all banned users', usage='/unbanall')
    @commands.has_permissions(ban_members=True)
    async def unbanall(ctx):
        banned_users = await ctx.guild.bans()

        for ban_entry in banned_users:
            user = ban_entry.user
            await ctx.guild.unban(user)
            await ctx.send(f'{user} wurde nicht verboten!')


    @client.command(description='Gives role to a given user', usage='/giverole <Mention User> <Role Name>')
    @commands.has_permissions(manage_roles=True)
    async def giverole(ctx, member : discord.Member, *, role):
        role = discord.utils.get(ctx.guild.roles, name=role)
        if role == None:
            await ctx.send('Diese Rolle existiert nicht! Bitte überprüfen Sie auf Tippfehler!')
        else:
            await member.add_roles(role)
            await ctx.send(f'{member.mention} wurde die Rolle gegeben: {role}!')


    @client.command(description='Remvoes role from a given user', usage='/removerole <Mention User> <Role Name>')
    @commands.has_permissions(manage_roles=True)
    async def removerole(ctx, member : discord.Member, *, role):
        role = discord.utils.get(ctx.guild.roles, name=role)
        if role == None:
            await ctx.send('Diese Rolle existiert nicht! Bitte überprüfen Sie auf Tippfehler!')
        else:        
            await member.remove_roles(role)
            await ctx.send(f'Rolle: {role} wurde vom {member.mention} entfernt!')


    @client.command(description='Setup command for automatic role assignment', usage="/autorole <Default Role Name> <Main Channel Name> (Don't mention Role/Channel)")
    @commands.has_permissions(manage_roles=True)
    async def autorole(ctx, role, channel):
        drole = discord.utils.get(ctx.guild.roles, name=role)
        if drole == None:
            await ctx.send('Diese Rolle existiert nicht! Bitte überprüfen Sie auf Tippfehler!')
        sendchannel = discord.utils.get(ctx.guild.channels, name=channel)
        if sendchannel == None:
                await ctx.send('Diese Kanal existiert nicht! Bitte überprüfen Sie auf Tippfehler!')
        elif sendchannel != None and drole != None:
                def_role = {'role' : drole.id, 'channel' : sendchannel.id}
                g_coll = db[f"{ctx.guild.id}"]
                role_config = g_coll["role_config"]
                if role_config.find_one({}) != None:
                    role_config.delete_many({})
                role_config.insert_one(def_role)
                await ctx.send(f'Neue Standardrolle ist {role}!')


    @client.command(name='help', aliases=['Help', 'h', 'H'], description='Shows all available commands', usage='/help <Command (Optional)>')
    async def _help(ctx, commandarg=None):
        help_embed = discord.Embed(title='Help — Here is a list of available commands:', color=Color.dark_red())
        help_embed.set_footer(text=ctx.message.author, icon_url=ctx.message.author.avatar_url)
        if commandarg == None:
            for command in client.commands:
                if command.hidden != True:
                    if command.name[0] == '_':
                        aliases = list(set(command.aliases))
                        name = aliases[0]
                    else:
                        name = command.name
                    text = f'Name: `{name}`\nDescription: `{command.description}`\nUsage: `{command.usage}`'
                    help_embed.add_field(name=name, value=text, inline=True)
        else:
            command = discord.utils.get(client.commands, name=commandarg)
            if command != None:
                if command.hidden != True:
                    aliases = list(set(command.aliases))
                    if len(aliases) != 0:
                        aliases = ', '.join(aliases)
                        help_text = f'Name: `{command.name}`\nDescription: `{command.description}`\nUsage: `{command.usage}`\nAliases: `{aliases}`'
                    else:
                        help_text = f'Name: `{command.name}`\nDescription: `{command.description}`\nUsage: `{command.usage}`'
                    help_embed.add_field(name=command.name, value=help_text, inline=True)
                else:
                    await ctx.send('Denied')
            else:       
                for command in client.commands:
                    if command.name[0] == '_':
                        aliases = list(set(command.aliases))
                        name = aliases[0]
                    else:
                        name = command.name
                    text = f'Name: `{name}`\nDescription: `{command.description}`\nUsage: `{command.usage}`'
                    help_embed.add_field(name=name, value=text, inline=True)
        await ctx.send(embed=help_embed)



    @client.command(description='Info on RoboterVogel', usage='/info')
    async def info(ctx):
        info_embed = discord.Embed(name='Info', color=Color.dark_red())
        info_embed.add_field(name='Über Roboter Vogel:',value='\nRoboterVogel wurde von Raucher Adler#1521 gemacht!', inline=True)
        info_embed.add_field(name='Für mehr Information:', value='\nUse `/help` for a list of available commands or message me direcly.\n- Adler', inline=True)
        info_embed.set_footer(text=ctx.message.author, icon_url=ctx.message.author.avatar_url)
        await ctx.send(embed=info_embed)
        await ctx.send('https://discord.gg/6GFQcFHjSK')


    @client.command(description='Gets guild stats such as number of users, etc.', usage='/stats')
    async def stats(ctx):
        stats_embed = discord.Embed(name='Guild Stats', color=Color.dark_red())
        members = ctx.guild.members
        online_member_number = 0
        total_member_number = 0
        bot_number = 0
        for member in members:
            offline = discord.Status.offline
            status = member.status
            if status == offline:
                if member.bot == False:
                    total_member_number =  total_member_number + 1
                else:
                    bot_number = bot_number + 1
            elif status != offline:
                if member.bot == False:
                    total_member_number = total_member_number + 1
                    online_member_number = online_member_number + 1
                else:
                    bot_number = bot_number + 1
        stats_embed.add_field(name='Active Members: ', value=f'{online_member_number}', inline=True)
        stats_embed.add_field(name='Total Members: ', value=f'{total_member_number}', inline=True)
        stats_embed.add_field(name='Bots: ', value=f'{bot_number}', inline=True)
        stats_embed.add_field(name='Note:', value='Active Members/Total Members discludes all bots', inline=True)
        stats_embed.add_field(name='Inhaber:', value=f'{ctx.guild.owner}', inline=True)
        stats_embed.add_field(name='Server erstellt am:', value=f'{ctx.guild.created_at} (UTC)', inline=True)
        stats_embed.add_field(name='Shard ID:', value=f'{ctx.guild.shard_id}', inline=True)
        stats_embed.set_footer(text=ctx.message.author, icon_url=ctx.message.author.avatar_url)
        await ctx.send(embed=stats_embed)


    @client.command(aliases=['Nickname', 'Nick'], description="Changes a given user's nickname", usage='/nickname <Mention Member> <Nickname>')
    @commands.has_permissions(manage_nicknames=True)
    async def nickname(ctx, member : discord.Member, *, nickname):
        await member.edit(nick=nickname)


    @client.command(aliases=['Profile', 'whois', 'Whois'], description='Fetches user info such as account age, name, etc.', usage='/profile <Mention Member (Optional)>')
    async def profile(ctx, member : discord.Member=None):
        if member == None:
            member = ctx.message.author
        profile_embed = discord.Embed(title=f'User — {member}', color=Color.dark_red())
        profile_embed.set_thumbnail(url=member.avatar_url)
        profile_embed.set_footer(text=ctx.message.author, icon_url=ctx.message.author.avatar_url)
        profile_embed.add_field(name='Name:', value=f'`{member}`', inline=True)
        profile_embed.add_field(name='Nickname:', value=f'`{member.nick}`', inline=True)
        profile_embed.add_field(name='User ID:', value=f'`{member.id}`', inline=True)
        profile_embed.add_field(name='Avatar URL:', value=f"[{member}'s Avatar]({member.avatar_url})", inline=True)
        profile_embed.add_field(name='Status:', value=f'`{member.raw_status}`', inline=True)
        profile_embed.add_field(name='Bot:', value=f'`{member.bot}`', inline=True)
        profile_embed.add_field(name=f'Joined {ctx.guild.name} at:', value=f'`{member.joined_at} (UTC)`', inline=True)
        profile_embed.add_field(name='Account creation time:', value=f'`{member.created_at} (UTC)`', inline=True)
        await ctx.send(embed=profile_embed)


class Chat(commands.Cog):

    def __init__(self, client):
        self.client = client


    @client.command(aliases=['hello', 'hallo', 'begruessung', 'begrüßung', 'greeting', 'gruessen', 'grüßen'], description='Greets user, or sends gretting to a different user', usage='/greet < Mention User (optional)>')
    async def greet(ctx, member : discord.Member=None):
        tz_CDT = pytz.timezone('America/Chicago')
        now_CDT = datetime.now(tz_CDT)
        hour_CDT = now_CDT.hour
        if hour_CDT in range(5, 10):
            time_of_day = 'Morgen'
            word_ending = 'en'
        elif hour_CDT in range(11, 17):
            time_of_day = 'Tag'
            word_ending = 'en'
        elif hour_CDT in range(18, 21):
            time_of_day = 'Abend'
            word_ending = 'en'
        elif hour_CDT in range(22, 23) or range(0, 4):
            time_of_day = 'Nacht'
            word_ending = 'e'

        good = 'Gut' + word_ending
        author_id = ctx.message.author.id
        if author_id == 767633160765702145 and member == None:
            await ctx.send(f'{good} {time_of_day}, Vater!')
        elif author_id != 767633160765702145 and member == None:
            await ctx.send(f'{good} {time_of_day}, {ctx.message.author.mention}!')
        elif member != None:
            if member.id == 762768118212067328:
                await ctx.send(f'Hallo {ctx.message.author.mention}, wie gehts?')
            else:
                await ctx.send(f'Grüße von {ctx.message.author.mention}, {member.mention}!')


    @client.command(aliases=['geburtstag'], description='Sends birthday message for a user', usage='/birthday <Mention User>')
    async def birthday(ctx, member : discord.Member):
        bday_role = discord.utils.get(ctx.guild.roles, name='Geburtstagskind')
        if bday_role == None:
            bday_role = await ctx.guild.create_role(name='Geburtstagskind', reason='Es ist Geburtstagszeit.')
        has_role = discord.utils.get(member.roles, name='Geburtstagskind')
        if has_role == None:
            await member.add_roles(bday_role)
        else:
            pass
        await ctx.send(f'Alles gute zum geburtstag, {member.mention}!  :tada:\nJetzt singen wir alle das Geburtstagslied:')
        embed_name = 'Geburtstagslied :birthday:'
        embed_text = 'Zum Geburtstag viel Glück!\nZum Geburtstag viel Glück!\nZum Geburtstag liebe {name}!\nZum Geburtstag viel Glück!'.format(name=member.name)
        lyric_embed = discord.Embed(name=embed_name, color=Color.dark_red())
        lyric_embed.add_field(name=embed_name, value=embed_text)
        lyric_embed.set_footer(text=member, icon_url=member.avatar_url)
        await ctx.send(embed=lyric_embed)
        await asyncio.sleep(86400)
        await member.remove_roles(bday_role)


    @client.command(description='Pings bots latency', usage='/ping')
    async def ping(ctx):
        await ctx.send(f'Pong! `{round(client.latency * 1000)}ms`')


    @client.command(aliases=['randpng', 'randimg', 'pic', 'image'], description='Generates a random image', usage='/randomimage <Width (Optional)> <Height (Optional)>')
    async def randomimage(ctx, size_width=128, size_height=128):
        size = (size_width, size_height)           
        if size_width > 2000 and size_height > 2000:
            await ctx.send('Zu groß!')
        else:
            image = Image.new('RGB', size)
            for X in range(0, size_width):
                for Y in range(0, size_width):
                    rvalue = str(randint(0, 255))
                    gvalue = str(randint(0, 255))
                    bvalue = str(randint(0, 255))
                    rgb = rvalue + gvalue + bvalue
                    rgb = int(rgb)
                    coord = (X,Y)
                    image.putpixel(coord, rgb)
            image.save('image.png')
            if os.stat('image.png').st_size >= ctx.guild.filesize_limit:
                await ctx.send(f'Zu groß!')
            elif os.stat('image.png').st_size < ctx.guild.filesize_limit:
                await ctx.send(file=discord.File('image.png'))
                os.remove('image.png')


    @client.command(aliases=['zeit', 'Time', 'Zeit'], description='Tells the time', usage='/time')
    async def time(ctx):
        time_embed = discord.Embed(name='time', color=Color.dark_red())
        date = dt.date.today()
        formatted_date = date.strftime('%d/%m/%Y')
        weekday = date.strftime('%A')
        monthtext = date.strftime('%B')
        translator = Translator(to_lang='German')
        weekday_DE = translator.translate(weekday)
        monthtext_DE = translator.translate(monthtext)
        time_embed.add_field(name='Das Datum', value=f'Heute haben wir {weekday_DE} den {date.strftime("%d")}{"."} {monthtext_DE}{","} ({formatted_date})', inline=True)
        GMT = pytz.timezone('GMT')
        GMT_time = datetime.now(GMT)
        time_embed.add_field(name='Zeit(GMT):', value=f'{GMT_time.strftime("%I:%M:%S%p")} {"/"} {GMT_time.strftime("%H:%M:%S")}', inline=True)
        time_since_epoch = time.time()
        time_embed.add_field(name='Zeit seit Epoche:', value=f'{time_since_epoch}s', inline=True)
        time_embed.set_footer(text=ctx.message.author, icon_url=ctx.message.author.avatar_url)
        await ctx.send(embed=time_embed)


    @client.command(aliases=['Font','fraktur', 'Fraktur'], description='Converts a given text into the Fraktur Font.', usage='/font <Message>')
    async def font(ctx, *, message):
        new_message = ''
        latin_uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        latin_lowercase = 'abcdefghijklmnopqrstuvwxyz'
        fraktur_uppercase = "𝔄𝔅ℭ𝔇𝔈𝔉𝔊ℌℑ𝔍𝔎𝔏𝔐𝔑𝔒𝔓𝔔ℜ𝔖𝔗𝔘𝔙𝔚𝔛𝔜ℨ"
        fraktur_lowercase = "𝔞𝔟𝔠𝔡𝔢𝔣𝔤𝔥𝔦𝔧𝔨𝔩𝔪𝔫𝔬𝔭𝔮𝔯𝔰𝔱𝔲𝔳𝔴𝔵𝔶𝔷"
        for letter in message:
            if letter in latin_uppercase:
                index = latin_uppercase.index(letter)
                fraktur_letter = fraktur_uppercase[index]
            elif letter in latin_lowercase:
                index = latin_lowercase.index(letter)
                fraktur_letter = fraktur_lowercase[index]
            else:
                fraktur_letter = letter
            new_message = new_message + fraktur_letter
        await ctx.send(new_message)


class Conversion(commands.Cog):

    def __init__(self, client):
        self.client = client


    @client.command(name='translate', description='Translate text (currently only supports German)', usage='/translate <Message>')
    async def _translate(ctx, *, message):
        translator = Translator(to_lang="German")
        translation = translator.translate(message)
        await ctx.send(translation)


    @client.command(aliases=['FCP'], description='Converts USD to FCP (Far Cry Primal)', usage='/fcp <Amount of USD>')
    async def fcp(ctx, *, amount):
        server = ['this server', 'This Server', 'server', 'Server']
        if amount in server:
            FCP = 1
            await ctx.send(f'`{amount}` ≈ `{FCP} FCP`')
        else:    
            amount = amount.replace('$', '')
            usdtofcp = 1 / 30
            FCP = float(usdtofcp) * float(amount)
            await ctx.send(f'`{amount} USD` ≈ `{FCP} FCP`')


    @client.command(aliases=['USD'], description='Converts FCP (Far Cry Primal) to USD', usage='/usd <Amount of FCP>')
    async def usd(ctx, *, amount):
        amount = amount.replace('FCPfcp', '')
        fcptousd = 30
        USD = float(fcptousd) * float(amount)
        await ctx.send(f'`{amount} FCP` ≈ `{USD} USD`')



class Voice(commands.Cog):

    def __init__(self, client):
        self.client = client
    
    context = commands.Context
    Loop = False


    def _handle_queue(self, error=None):
        ctx = Voice.context
        loop = client.loop
        guild_id = ctx.guild.id
        g_coll = db[f"{guild_id}"]
        np_coll = g_coll["now_playing"]
        np_coll.delete_many({})
        voice_client = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if Voice.Loop == False:
            entry = next_in_queue(guild_id)
        else:
            np_coll = g_coll["now_playing"]
            entry = np_coll.find_one({})
        if entry != None:
            asyncio.run_coroutine_threadsafe(Voice.play_next(entry, voice_client), loop)


    @client.command(name='play', aliases=['Play', 'p', 'P'], description='Plays Music from youtube', usage='/play <video link/title to search for>')
    async def _play(ctx, *, song):
        member_voice = ctx.message.author.voice
        if member_voice != None:
            member_voice_channel = member_voice.channel
            client_voice_channels = discord.utils.get(client.voice_clients, guild=ctx.guild)
            if client_voice_channels != None:
                client_voice_channel = client_voice_channels.channel
                if member_voice_channel != client_voice_channel:
                    await ctx.send(f'Derzeit in einem anderen Sprachkanal')
            else:
                await ctx.send(f'Jetzt `{member_voice_channel}` eingeben!')
                await member_voice_channel.connect()
            current_voice_client = discord.utils.get(client.voice_clients, channel=member_voice_channel)
            if validators.url(song) == True:
                link = song
                #parsed_link = urlparse(link) removing this for now, until I can implement feature for playlist
                result = YoutubeSearch(link, max_results=1).to_dict()
                for v in result:
                    thumbnails = v['thumbnails']
                    thumbnail = thumbnails[0]
            else:
                await ctx.send(f'Searching Youtube for `{song}`')
                result = YoutubeSearch(song, max_results=1).to_dict()
                for v in result:
                    url_suffix = v['url_suffix']
                    thumbnails = v['thumbnails']
                    thumbnail = thumbnails[0]
                    link = 'https://www.youtube.com' + url_suffix
            before_opts = '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
            logfile = open('ffmpeg.log', 'a+')
            opts = '-vn'
            ydl_opts = {'format' : 'bestaudio', 'noplaylist' : 'True', 'quiet' : 'True', 'simulate' : 'True'}
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                attr_dict = ydl.extract_info(link, download=False)
            video_title = attr_dict['title']
            duration = attr_dict['duration']
            ty_res = time.gmtime(duration)
            video_duration = time.strftime("%H:%M:%S", ty_res)
            song_embed = discord.Embed(name='Song', color=Color.dark_red())
            song_embed.add_field(name='Title:', value=f'[{video_title}]({link})', inline=True)
            song_embed.add_field(name='Duration:', value=f'{video_duration}', inline=True)
            song_embed.set_thumbnail(url=thumbnail)
            song_embed.set_footer(text=ctx.message.author, icon_url=ctx.message.author.avatar_url)
            source = attr_dict['formats'][0]['url']
            attributes : dict = {"name" : video_title, "duration" : duration, "thumbnail" : thumbnail, "requested_by_id" : ctx.message.author.id, "url" : link, "channel_id" : ctx.channel.id, "guildid" : ctx.guild.id}
            g_coll = db[f"{ctx.guild.id}"]
            np_coll = g_coll["now_playing"]
            if np_coll.find_one({}) != None:
                pos = add_to_queue(ctx.guild.id, attributes)
                song_embed.add_field(name='Position in queue:', value=pos, inline=True)
                song_embed.set_author(name='Zur Warteschlange hinzugefügt:', icon_url=ctx.message.author.avatar_url)
                await ctx.send(embed=song_embed)
            else:
                source = discord.FFmpegOpusAudio(source=source, executable='ffmpeg', before_options=before_opts, options=opts, stderr=logfile)
                song_embed.set_author(name='Jetzt Spielen:', icon_url=ctx.message.author.avatar_url)
                await ctx.send(embed=song_embed)
                Voice.context = ctx
                g_coll = db[f"{ctx.guild.id}"]
                np_coll = g_coll["now_playing"]
                np_coll.insert_one(attributes)
                current_voice_client.play(source, after=Voice._handle_queue)
        else:
            await ctx.send(f'Sie befinden sich nicht in einem Sprachkanal!')

    async def play_next(entry, vc):
        name = entry["name"]
        duration = entry["duration"]
        thumbnail = entry["thumbnail"]
        requested_by_id = entry["requested_by_id"]
        link = entry["url"]
        channel_id = entry["channel_id"]
        guild_id = entry["guildid"]
        ty_res = time.gmtime(duration)
        video_duration = time.strftime("%H:%M:%S", ty_res)
        guild = client.get_guild(guild_id)
        requested_by = guild.get_member(requested_by_id)
        channel = guild.get_channel(channel_id)
        ydl_opts = {'format' : 'bestaudio', 'noplaylist' : 'True', 'quiet' : 'True', 'simulate' : 'True'}
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            attr_dict = ydl.extract_info(link, download=False)
        source = attr_dict["formats"][0]["url"]
        song_embed = discord.Embed(name='Song', color=Color.dark_red())
        song_embed.add_field(name='Title:', value=f'[{name}]({link})', inline=True)
        song_embed.add_field(name='Duration:', value=f'{video_duration}', inline=True)
        song_embed.set_thumbnail(url=thumbnail)
        song_embed.set_footer(text=requested_by, icon_url=requested_by.avatar_url)
        song_embed.set_author(name='Jetzt Spielen:', icon_url=requested_by.avatar_url)
        before_opts = '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
        opts = '-vn'
        logfile = open('ffmpeg.log', 'a+')
        source = discord.FFmpegOpusAudio(source=source, executable='ffmpeg', before_options=before_opts, options=opts, stderr=logfile)
        if Voice.Loop == False:
            await channel.send(embed=song_embed)
        vc.play(source=source, after=Voice._handle_queue)


    @client.command(aliases=['Queue', 'q', 'Q'], description='Shows current queue', usage='/queue')
    async def queue(ctx):
        client_vc = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if client_vc != None:
            if client_vc.is_playing() or client_vc.is_paused():
                g_coll = db[f"{ctx.guild.id}"]
                entries = g_coll["entries"]
                np_coll = g_coll["now_playing"]
                np = np_coll.find_one({})
                queue_embed = discord.Embed(name='queue', color=Color.dark_red())
                queue_embed.set_author(name='Warteschlange', icon_url=ctx.message.author.avatar_url)
                np_rq_id = np["requested_by_id"]
                np_rb = ctx.guild.get_member(np_rq_id)
                f_dur = np["duration"]
                ty_res = time.gmtime(f_dur)
                fv_duration = time.strftime("%H:%M:%S", ty_res)
                queue_embed.add_field(name=f'Jetzt Spielen:\n', value=f'[{np["name"]}]({np["url"]}) | `{fv_duration} von: {np_rb}`\n', inline=False)
                queue_length = f_dur
                for entriesf in entries.find({}):
                    np_rb = entriesf["requested_by_id"]
                    np_rb_mem = ctx.guild.get_member(np_rb)
                    queue_length += entriesf["duration"]
                    duration = entriesf["duration"]
                    ty_res = time.gmtime(duration)
                    video_duration = time.strftime("%H:%M:%S", ty_res)
                    if entriesf["id"] == 0:
                        queue_embed.add_field(name='\n\nWarteschlange:\n', value=f'`{entriesf["id"] + 1})` [{entriesf["name"]}]({entriesf["url"]}) | `{video_duration} von: {np_rb_mem}`', inline=False)
                    else:
                        queue_embed.add_field(name=u'\u200b', value=f'`{entriesf["id"] + 1})` [{entriesf["name"]}]({entriesf["url"]}) | `{video_duration} von: {np_rb_mem}`', inline=False)
                ty_res = time.gmtime(queue_length)
                queue_duration = time.strftime("%H:%M:%S", ty_res)
                queue_embed.set_footer(text=f'{ctx.message.author} | Duration: {queue_duration}', icon_url=ctx.message.author.avatar_url)
                await ctx.send(embed=queue_embed)
            else:
                await ctx.send(f'Keine Medienspiele')
        else:
            await ctx.send(f'Derzeit nicht in Sprachkanal!')


    @client.command(description='Join Voice Channel', usage='/join')
    async def join(ctx):
        member = ctx.message.author
        member_voice = member.voice
        if member_voice != None:
            voice_channel = member_voice.channel
            bot_voice_client = discord.utils.get(client.voice_clients, guild=ctx.guild)
            if bot_voice_client == None:
                await ctx.send(f'Jetzt `{voice_channel}` eingeben!')
                await voice_channel.connect()
            elif bot_voice_client.channel == voice_channel:
                await ctx.send('Bereits im Sprachkanal!')
            else:    
                await ctx.send(f'Derzeit in einem anderen Sprachkanal')
        else:
            await ctx.send(f'Sie befinden sich nicht in einem Sprachkanal!')


    @client.command(aliases=['Leave', 'disconnect', 'Disconnect', 'dc', 'DC'],description='Leave Voice Channel', usage='/leave')
    async def leave(ctx):
        member = ctx.message.author
        member_voice = member.voice
        if member_voice != None:
            voice_channel = member_voice.channel
            client_voice_client = discord.utils.get(client.voice_clients, guild=ctx.guild)
            if client_voice_client != None:
                if client_voice_client.channel == voice_channel:
                    g_coll = db[f"{ctx.guild.id}"]
                    entries = g_coll ["entries"]
                    entries.delete_many({})
                    await client_voice_client.disconnect()
                    Voice.Loop = False
                    await ctx.send(f'Auf Wiedersehen!')
                else:
                    await ctx.send(f'Derzeit in einem anderen Sprachkanal')
            else:
                await ctx.send('Derzeit nicht in Sprachkanal!')
        else:
            await ctx.send(f'Sie befinden sich nicht in einem Sprachkanal!')


    @client.command(description='Ends current audio, stops queue', usage='/stop')
    async def stop(ctx):
        member = ctx.message.author
        voice_channel = member.voice.channel
        vc = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if voice_channel != None and vc != None:
            g_coll = db[f"{ctx.guild.id}"]
            entries = g_coll ["entries"]
            entries.delete_many({})
            vc.stop()
            await ctx.send('Medien gestoppt!')
        else:
            await ctx.send(f'Derzeit nicht in Sprachkanal!')


    @client.command(aliases=['TTS', 'texttospeech'], description='Sends a Text-to-Speech message into current VC', usage='/TTS <Message> <Language (Optional)>')
    async def tts(ctx, message, language='en'):
        member_voice_channel = ctx.message.author.voice.channel
        if member_voice_channel == None:
            await ctx.send(f'Sie befinden sich nicht in einem Sprachkanal!')
        else:
            client_voice_channels = discord.utils.get(client.voice_clients, guild=ctx.guild)
            if client_voice_channels != None:
                client_voice_channel = client_voice_channels.channel
                if member_voice_channel != client_voice_channel:
                    await ctx.send(f'Derzeit in einem anderen Sprachkanal!')
            else:
                await ctx.send(f'Jetzt `{member_voice_channel}` eingeben!')
                await member_voice_channel.connect()
            try:
                tts = gTTS(text=message, lang=language)
            except ValueError:
                tts = gTTS(text=message, lang='en')
            tts.save('message.mp3')
            source = discord.FFmpegOpusAudio(source='message.mp3', executable='ffmpeg')
            current_VoiceClient = discord.utils.get(client.voice_clients, guild=ctx.guild)
            current_VoiceClient.play(source=source, after=os.remove('message.mp3'))


    @client.command(description='Resumes current song', usage='/resume')
    async def resume(ctx):
        member_vc = ctx.message.author.voice
        client_vc = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if member_vc != None:
            if client_vc != None:
                if client_vc.channel == member_vc.channel:
                    if client_vc.is_paused():
                        client_vc.resume()
                        await ctx.send(f'Medien nicht angehalten!')
                    else:
                        await ctx.send(f'Keine Medienspiele!')
                else:
                    await ctx.send(f'Derzeit in einem anderen Sprachkanal!')
            else:
                await ctx.send(f'Derzeit nicht in Sprachkanal!')
        else:
            await ctx.send(f'Sie befinden sich nicht in einem Sprachkanal!')


    @client.command(description='Pauses current song', usage='/pause')
    async def pause(ctx):
        member_vc = ctx.message.author.voice
        client_vc = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if member_vc != None:
            if client_vc != None:
                if client_vc.channel == member_vc.channel:
                    if client_vc.is_playing():
                        client_vc.pause()
                        await ctx.send(f'Medien in Pause!')
                    else:
                        await ctx.send(f'Keine Medienspiele!')
                else:
                    await ctx.send(f'Derzeit in einem anderen Sprachkanal!')
            else:
                await ctx.send(f'Derzeit nicht in Sprachkanal!')
        else:
            await ctx.send(f'Sie befinden sich nicht in einem Sprachkanal!')


    @client.command(aliases=['s', 'S', 'Skip'], description='Skips current song', usage='/skip')
    async def skip(ctx):
        member_vc = ctx.message.author.voice
        client_vc = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if member_vc != None:
            if client_vc != None:
                if client_vc.channel == member_vc.channel:
                    if client_vc.is_playing() or client_vc.is_paused():
                        client_vc.stop()
                        await ctx.send(f'Übersprungene Medien!')
                    else:
                        await ctx.send(f'Keine Medienspiele!')
                else:
                    await ctx.send(f'Derzeit in einem anderen Sprachkanal!')
            else:
                await ctx.send(f'Derzeit nicht in Sprachkanal!')
        else:
            await ctx.send(f'Sie befinden sich nicht in einem Sprachkanal!')


    @client.command(aliases=['Clearqueue', 'cq', 'CQ'], description='Clears all entries in queue', usage='/clear_queue')
    async def clearqueue(ctx):
        member_vc = ctx.message.author.voice
        client_vc = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if member_vc != None:
            if client_vc != None:
                if client_vc.channel == member_vc.channel:
                    if client_vc.is_playing() or client_vc.is_paused():
                        g_coll = db[f"{ctx.guild.id}"]
                        entries = g_coll["entries"]
                        entries.delete_many({})
                        await ctx.send(f'Warteschlange gelöscht!')
                    else:
                        await ctx.send(f'Keine Medienspiele!')
                else:
                    await ctx.send(f'Derzeit in einem anderen Sprachkanal!')
            else:
                await ctx.send(f'Derzeit nicht in Sprachkanal!')
        else:
            await ctx.send(f'Sie befinden sich nicht in einem Sprachkanal!')


    @client.command(aliases=['now_playing', 'np', 'NP', 'Nowplaying'], description='Shows currently playing media', usage='/nowplaying')
    async def nowplaying(ctx):
        client_vc = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if client_vc != None:
            if client_vc.is_playing() or client_vc.is_paused():
                g_coll = db[f"{ctx.guild.id}"]
                np_coll = g_coll["now_playing"]
                np = np_coll.find_one({})
                np_title = np["name"]
                np_link = np["url"]
                np_thumbnail = np["thumbnail"]
                np_reqbyid = np["requested_by_id"]
                np_duration = np["duration"]
                song_embed = discord.Embed(name='Song', color=Color.dark_red())
                author = ctx.guild.get_member(np_reqbyid)
                ty_res = time.gmtime(np_duration)
                video_duration = time.strftime("%H:%M:%S", ty_res)
                song_embed.set_author(name='Jetzt Spielen:', icon_url=author.avatar_url)
                song_embed.set_thumbnail(url=np_thumbnail)
                song_embed.set_footer(text=ctx.message.author, icon_url=ctx.message.author.avatar_url)
                song_embed.add_field(name='Title:', value=f'[{np_title}]({np_link})', inline=True)
                song_embed.add_field(name='Duration:', value=f'{video_duration}')
                await ctx.send(embed=song_embed)
            else:
                await ctx.send(f'Keine Medienspiele!')
        else:
            await ctx.send(f'Derzeit nicht in Sprachkanal!')

    
    @client.command(name='loop', aliases=['l', 'L', 'Loop'], description='Loops currently playing media', usage='/loop')
    async def _loop(ctx):
        member_vc = ctx.message.author.voice
        client_vc = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if member_vc != None:
            if client_vc != None:
                if client_vc.channel == member_vc.channel:
                    if client_vc.is_playing() or client_vc.is_paused():
                        Voice.Loop = not Voice.Loop
                        if Voice.Loop == True:
                            await ctx.send('Medien wird geloopt!')
                        else:
                            await ctx.send('Medien wird nicht mehr geloopt!')
                    else:
                        await ctx.send(f'Keine Medienspiele!')
                else:
                    await ctx.send(f'Derzeit in einem anderen Sprachkanal!')
            else:
                await ctx.send(f'Derzeit nicht in Sprachkanal!')
        else:
            await ctx.send(f'Sie befinden sich nicht in einem Sprachkanal!')


    @client.command(aliases=['rm', 'RM', 'Remove', 'r', 'R'], description='Removes a given song from queue', usage='/remove <Number of entry in queue>')
    async def remove(ctx , *, entry_num : int):
        member_vc = ctx.message.author.voice
        client_vc = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if member_vc != None:
            if client_vc != None:
                if client_vc.channel == member_vc.channel:
                    if client_vc.is_playing() or client_vc.is_paused():
                        g_coll = db[f"{ctx.guild.id}"]
                        entries = g_coll["entries"]
                        entry_num -= 1
                        rm_entry = entries.find_one_and_delete({"id" : entry_num})
                        rm_name = rm_entry["name"]
                        await ctx.send(f'Entfernt: `{rm_name}`!')
                        for entry in entries:
                            entry_id = entry["id"]
                            entry_id = int(entry_id)
                            if entry_id > entry_num:
                                entries.update_one({"id" : entry_id}, {"$inc" : {"id" : -1}})
                    else:
                        await ctx.send(f'Keine Medienspiele!')
                else:
                    await ctx.send(f'Derzeit in einem anderen Sprachkanal!')
            else:
                await ctx.send(f'Derzeit nicht in Sprachkanal!')
        else:
            await ctx.send(f'Sie befinden sich nicht in einem Sprachkanal!')



class OP(commands.Cog):

    def __init__(self, client):
        self.client = client


    @client.command(hidden=True, aliases=['lg', 'LG'])
    async def listguilds(ctx):
        if client.is_owner(ctx.message.author):
            f = open('guilds.txt', 'a+')
            for guild in client.guilds:
                f.write(f'{guild.name} : {guild.id}\n')
            f.close()
            await ctx.send(file=discord.File('guilds.txt'))
            os.remove('guilds.txt')

    
    @client.command(hidden=True, aliases=['lm', 'LM'])
    async def listmembers(ctx, guild_id):
        if client.is_owner(ctx.message.owner):
            f = open('members.txt', 'a+')
            guild = await client.fetch_guild(guild_id)
            for member in guild.members:
                f.write(f'{member} / {member.nick} : {member.id}\n')
            f.write(f'Owner: {guild.owner.name}')
            f.close()
            await ctx.send(file=discord.File('members.txt'))
            os.remove('members.txt')


    @client.command(hidden=True, aliases=['gi', 'GI'])
    async def getinvite(ctx, guild_id):
        if client.is_owner(ctx.message.author):
            guild = await client.fetch_guild(guild_id)
            for channel in guild.text_channels:
                invite = await channel.create_invite()
                await ctx.send(invite)



def setup(client):
    client.add_cog(Moderation(client))
    client.add_cog(Chat(client))
    client.add_cog(Conversion(client))
    client.add_cog(Voice(client))
    client.add_cog(OP(client))

DISCORD_S3 = os.environ['DISCORD_TOKEN']     
client.run(DISCORD_S3)