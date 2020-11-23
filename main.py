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
import json
import validators
from urllib.parse import urlparse
from functools import partial


mongo_pswrd = os.environ["MONGODB_PASSWORD"]
client = pymongo.MongoClient(f"mongodb+srv://RaucherAdler:{mongo_pswrd}@cluster0.klsio.mongodb.net/RoboterVogel?retryWrites=true&w=majority")
db = client["RoboterVogel"]
collection = db["queues"]


def add_to_queue(guild_id, attributes):
    g_coll = collection[f"{guild_id}"]
    entries = g_coll["entries"] 
    entries.insert_one(attributes)
    position = g_coll.count_documents({f"{guild_id}" : "entries"}) #does this, just not correctly.
    return position


def next_in_queue(guild_id):
    g_coll = collection[f"{guild_id}"]
    iterate = 0
    for entry in g_coll.find():
        if iterate == 0:
            if entry:
                entry_val = entry
                db.collection.delete_one({f"{guild_id}" : "entries"})
                return entry_val
        iterate =+ 1


def _handle_queue(loop, guild_id, voice_client):
    asyncio.run_coroutine_threadsafe(play_next(next_in_queue(collection[f"{guild_id}"]), voice_client), loop)


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


async def play_next(entry, vc):
    if entry != None:
        name = entry["name"]
        duration = entry["duration"]
        source = entry["source"]
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
        song_embed = discord.Embed(name='Song', color=Color.dark_red())
        song_embed.add_field(name='Title:', value=f'[{name}]({link})', inline=True)
        song_embed.add_field(name='Duration:', value=f'{video_duration}', inline=True)
        song_embed.set_thumbnail(url=thumbnail)
        song_embed.set_footer(text=requested_by, icon_url=requested_by.avatar_url)
        source = discord.FFmpegOpusAudio(source=source, executable='ffmpeg')
        await channel.send("Jetzt Spielen:", embed=song_embed)
        vc.play(source=source, after=partial(_handle_queue, vc.loop, guild_id, vc))

@client.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.channels, name='def-role')
    async for message in channel.history(limit=1, oldest_first=True):
        role_id =  int(message.content)
    async for message in channel.history(limit=1):
        channel_name = message.content
    channelname = discord.utils.get(member.guild.channels, name=channel_name)
    await channelname.send(f'{member.mention} ist {member.guild.name} beigetretten!')
    if member.bot != True:
        await member.send(f'Willkommen bei {member.guild.name}, {member.mention}!')
    if channel == None:
        pass
    else:
        role = member.guild.get_role(role_id)
        await member.add_roles(role)
        await channelname.send(f'{member.mention} wurde die Rolle gegeben: {role}!')


@client.event
async def on_member_remove(member):
    channel = discord.utils.get(member.guild.channels, name='def-role')
    async for message in channel.history(limit=1):
        channel_name = message.content
    channelname = discord.utils.get(member.guild.channels, name=channel_name)
    if channelname == None:
        pass
    else:
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
        await owner.send(f'Hallo, Ich bin RoboterVogel, dein neuer Bot!\nhttps://discord.gg/ngutyTFPuS', embed=info_embed)
    await client.change_presence(activity=discord.Activity(status=discord.Status.online, type=discord.ActivityType.playing, name=f'Your Mother in {len(client.guilds)} Servers'))
    

@client.event
async def on_guild_remove(guild):
    await client.change_presence(activity=discord.Activity(status=discord.Status.online, type=discord.ActivityType.playing, name=f'Your Mother in {len(client.guilds)} Servers'))


class Moderation(commands.Cog):

    def __init__(self, client):
        self.client = client


    @client.command(description='Clears a given number of messages', usage='`/clear <Number of posts>`')
    @commands.has_permissions(manage_messages=True)
    async def clear(ctx, amount=0):
        await ctx.channel.purge(limit=amount+1)


    @client.command(description='Kicks a given user', usage='`/kick <Mention User>`')
    @commands.has_permissions(kick_members=True)
    async def kick(ctx, user: discord.Member, *, reason=None):
        await ctx.send('https://tenor.com/view/deathstar-gif-10649959')
        await ctx.send(f"{user} wurde getretten!")
        if user.bot != True:
            await user.send(f'Sie wurden vom {ctx.message.author} vom {ctx.guild.name} getretten!')
            if reason!= None:
                await user.send(f'Grund: {reason}')    
        await user.kick(reason=reason)


    @client.command(description='Bans a given user', usage='`/ban <Mention User> <Delete Messages from given number of Days tops 7 (Optional)>`')
    @commands.has_permissions(ban_members=True)
    async def ban(ctx, user: discord.Member, *, reason=None, delete_message_days=0):
        await ctx.send('https://tenor.com/view/deathstar-gif-10649959')
        await ctx.send(f"{user} wurde verboten!")
        if user.bot != True:
            await user.send(f'Sie wurden vom {ctx.message.author} vom {ctx.guild.name} gesperrt!')
            if reason != None:
                await user.send(f'Grund: {reason}')
        await user.ban(reason=reason, delete_message_days=delete_message_days)


    @client.command(description='Unbans a given user', usage='`/unban <User Name (i.e. Raucher Adler#1220)>`')
    @commands.has_permissions(ban_members=True)
    async def unban(ctx, *, member):
        banned_users = await ctx.guild.bans()
        member_name, member_discriminator = member.split('#')

        for ban_entry in banned_users:
            user = ban_entry.user

            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                await ctx.send(f'{user} wurde nicht verboten!')


    @client.command(description='Unbans all banned users', usage='`/unbanall`')
    @commands.has_permissions(ban_members=True)
    async def unbanall(ctx):
        banned_users = await ctx.guild.bans()

        for ban_entry in banned_users:
            user = ban_entry.user
            await ctx.guild.unban(user)
            await ctx.send(f'{user} wurde nicht verboten!')


    @client.command(description='Gives role to a given user', usage='`/giverole <Mention User> <Role Name>`')
    @commands.has_permissions(manage_roles=True)
    async def giverole(ctx, member : discord.Member, role):
        role = discord.utils.get(ctx.guild.roles, name=role)
        if role == None:
            await ctx.send('Diese Rolle existiert nicht! Bitte überprüfen Sie auf Tippfehler!')
        else:
            await member.add_roles(role)
            await ctx.send(f'{member.mention} wurde die Rolle gegeben: {role}!')


    @client.command(description='Remvoes role from a given user', usage='`/removerole <Mention User> <Role Name>`')
    @commands.has_permissions(manage_roles=True)
    async def removerole(ctx, member : discord.Member, role):
        role = discord.utils.get(ctx.guild.roles, name=role)
        if role == None:
            await ctx.send('Diese Rolle existiert nicht! Bitte überprüfen Sie auf Tippfehler!')
        else:        
            await member.remove_roles(role)
            await ctx.send(f'Rolle: {role} wurde vom {member.mention} entfernt!')


    @client.command(description='Setup Command for automatic role assignment', usage='`/autorole <Default Role Name> <Main Channel Name>`')
    @commands.has_permissions(manage_roles=True)
    async def autorole(ctx, role, channel):
        drole = discord.utils.get(ctx.guild.roles, name=role)
        if drole == None:
            await ctx.send('Diese Rolle existiert nicht! Bitte überprüfen Sie auf Tippfehler!')
        else:  
            defchannel = discord.utils.get(ctx.guild.channels, name='def-role')
            if defchannel != None:
                await defchannel.delete()      
            overwrites = {ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),ctx.guild.me: discord.PermissionOverwrite(read_messages=True)}
            newchannel = await ctx.guild.create_text_channel('def-role', overwrites=overwrites, topic='Auto generated channel by RoboterVogel, DO NOT delete or make any messages here.')   
            await newchannel.send(f'{int(drole.id)}')
        sendchannel = discord.utils.get(ctx.guild.channels, name=channel)
        if sendchannel == None:
                await ctx.send('Diese Kanal existiert nicht! Bitte überprüfen Sie auf Tippfehler!')
        else:
                await newchannel.send(f'{channel}')
                await ctx.send(f'Neue Standardrolle ist {role}!')


    @client.command(name='help', description='Lists all commands & their usages', usage='`/help`')
    async def _help(ctx, commandarg=None):
        if commandarg == None:
            help_embed = discord.Embed(title='Help — Here is a list of available commands:', color=Color.dark_red())
            help_embed.set_footer(text=ctx.message.author, icon_url=ctx.message.author.avatar_url)

            for command in client.commands:
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
                help_embed = discord.Embed(title=command.name, color=Color.dark_red())
                help_embed.set_footer(text=ctx.message.author, icon_url=ctx.author.avatar_url)
                aliases = list(set(command.aliases))
                if len(aliases) != 0:
                    aliases = ', '.join(aliases)
                    help_text = f'Name: `{command.name}`\nDescription: `{command.description}`\nUsage: `{command.usage}`\nAliases: `{aliases}`'
                else:
                    help_text = f'Name: `{command.name}`\nDescription: `{command.description}`\nUsage: `{command.usage}`'
                help_embed.add_field(name=command.name, value=help_text, inline=True)
            else:
                help_embed = discord.Embed(title='Help — Here is a list of available commands:', color=Color.dark_red())
                help_embed.set_footer(text=ctx.message.author, icon_url=ctx.message.author.avatar_url)
                    
                for command in client.commands:
                    if command.name[0] == '_':
                        aliases = list(set(command.aliases))
                        name = aliases[0]
                    else:
                        name = command.name
                    text = f'Name: `{name}`\nDescription: `{command.description}`\nUsage: `{command.usage}`'
                    help_embed.add_field(name=name, value=text, inline=True)
        await ctx.send(embed=help_embed)


    @client.command(description='Info on RoboterVogel', usage='`/info`')
    async def info(ctx):
        info_embed = discord.Embed(name='Info', color=Color.dark_red())
        info_embed.add_field(name='Über Roboter Vogel:',value='\nRoboterVogel wurde von Raucher Adler#1521 gemacht!', inline=True)
        info_embed.add_field(name='Für mehr Information:', value='\nUse `/help` for a list of available commands or message me direcly.\n- Adler', inline=True)
        info_embed.set_footer(text=ctx.message.author, icon_url=ctx.message.author.avatar_url)
        await ctx.send(embed=info_embed)
        await ctx.send('https://discord.gg/ngutyTFPuS')


    @client.command(description='Gets guild stats such as number of users, etc.', usage='`/stats`')
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


    @client.command(aliases=['Nickname', 'Nick'], description="Changes a given user's nickname", usage='`/nickname <Mention Member> <Nickname>`')
    @commands.has_permissions(manage_nicknames=True)
    async def nickname(ctx, member : discord.Member, nickname):
        await member.edit(nick=nickname)


    @client.command(description='Transfers ownership of current guild (Note: In order for this command to work, you must first manually transfer ownership to the bot (which to my knowledge is not possible) so it is best to just manually transfer ownership.)', usage='`/transfer_ownership <Mention Member>`')
    @commands.has_permissions(manage_guild=True)
    async def transfer_ownership(ctx, member : discord.Member):
        try:
            await ctx.guild.edit(owner=member)
            await ctx.send(f'Das Eigentum an {ctx.guild.name} wurde auf {member} übertragen.')
        except:
            await ctx.send('Error')

class Chat(commands.Cog):

    def __init__(self, client):
        self.client = client


    @client.command(aliases=['hello', 'hallo', 'begruessung', 'begrüßung', 'greeting', 'gruessen', 'grüßen'], description='Greets user, or sends gretting to a different user', usage='`/greet < Mention User (optional)>`')
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


    @client.command(aliases=['geburtstag'], description='Sends birthday message for a user', usage='`/birthday <Mention User>`')
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


    @client.command(description='Pings bots latency', usage='`/ping`')
    async def ping(ctx):
        await ctx.send(f'Pong! `{round(client.latency * 1000)}ms`')


    @client.command(aliases=['randpng', 'randimg', 'pic', 'image'], description='Generates a random image', usage='`/randomimage <Width (Optional)> <Height (Optional)>`')
    async def randomimage(ctx, size_width=128, size_height=128):
        size = (size_width, size_height)           
        image = Image.new('RGB', size)
        for x in range(0, size[0]-1):
            for y in range(0, size[1]-1):
                coordinate = (x, y)
                rvalue = str(randint(0, 255))
                gvalue = str(randint(0, 255))
                bvalue = str(randint(0, 255))
                rgb = rvalue + gvalue + bvalue
                rgb = int(rgb)
                image.putpixel(coordinate, rgb)
        image.save('image.png')
        if os.stat('image.png').st_size >= 8388119:
            await ctx.send(f'Zu groß!')
        elif os.stat('image.png').st_size < 8388119:
            await ctx.send(file=discord.File('image.png'))
            os.remove('image.png')


    @client.command(aliases=['zeit', 'Time', 'Zeit'], description='Tells the time', usage='`/time`')
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


    @client.command(aliases=['Font','fraktur', 'Fraktur'], description='Converts a given text into the Fraktur Font.', usage='`/font <Message>`')
    async def font(ctx, message):
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


    @client.command(name='translate', description='Translate text (currently only supports German)', usage='`/translate <Message>`')
    async def _translate(ctx, message):
        translator = Translator(to_lang="German")
        translation = translator.translate(message)
        await ctx.send(translation)


    @client.command(aliases=['FCP'], description='Converts USD to FCP (Far Cry Primal)', usage='`/fcp <Amount of USD>`')
    async def fcp(ctx, amount):
        server = ['this server', 'This Server', 'server', 'Server']
        if amount in server:
            FCP = 1
            await ctx.send(f'`{amount}` ≈ `{FCP} FCP`')
        else:    
            amount = amount.replace('$', '')
            usdtofcp = 1 / 30
            FCP = float(usdtofcp) * float(amount)
            await ctx.send(f'`{amount} USD` ≈ `{FCP} FCP`')


    @client.command(aliases=['USD'], description='Converts FCP (Far Cry Primal) to USD', usage='`/usd <Amount of FCP>`')
    async def usd(ctx, amount):
        amount = amount.replace('FCPfcp', '')
        fcptousd = 30
        USD = float(fcptousd) * float(amount)
        await ctx.send(f'`{amount} FCP` ≈ `{USD} USD`')



class Voice(commands.Cog):

    def __init__(self, client):
        self.client = client


    @client.command(description='Join Voice Channel', usage='`/join`')
    async def join(ctx):
        member = ctx.message.author
        voice_channel = member.voice.channel
        if voice_channel != None:
            bot_voice_client = discord.utils.get(client.voice_clients, guild=ctx.guild)
            if bot_voice_client == None:
                await ctx.send(f'Jetzt `{voice_channel}` eingeben!')
                await voice_channel.connect()
            else:
                await ctx.send(f'Derzeit in einem anderen Sprachkanal')
        else:
            await ctx.send(f'Sie befinden sich nicht in einem Sprachkanal!')


    @client.command(description='Leave Voice Channel', usage='`/leave`')
    async def leave(ctx):
        member = ctx.message.author
        voice_channel = member.voice.channel
        vc = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if voice_channel != None and vc != None:
            await vc.disconnect()
            await ctx.send(f'Auf Wiedersehen!')
            db.collection.delete_one({f"{ctx.guild.id}" : "entries"})
        else:
            await ctx.send(f'Derzeit nicht in Sprachkanal!')


    @client.command(aliases=['TTS', 'texttospeech'], description='Sends a Text-to-Speech message into current VC', usage='`/TTS <Message> <Language (Optional)>`')
    async def tts(ctx, message, language='en'):
        member_voice_channel = ctx.message.author.voice.channel
        if member_voice_channel == None:
            await ctx.send(f'Sie befinden sich nicht in einem Sprachkanal!')
        else:
            client_voice_channels = discord.utils.get(client.voice_clients, guild=ctx.guild)
            if client_voice_channels != None:
                client_voice_channel = client_voice_channels.channel
                if member_voice_channel != client_voice_channel:
                    await ctx.send(f'Derzeit in einem anderen Sprachkanal')
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


    @client.command(aliases=['Music', 'musik', 'Musik', 'p', 'P'], description='Plays Music from youtube', usage='`/music <video/title to search for>`')
    async def music(ctx, song):
        member_voice_channel = ctx.message.author.voice.channel
        if member_voice_channel == None:
            await ctx.send(f'Sie befinden sich nicht in einem Sprachkanal!')
        else:
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
            parsed_link = urlparse(link)
            if parsed_link.path == 'watch':
                result = YoutubeSearch(link, max_results=1).to_dict()
                for v in result:
                    thumbnails = v['thumbnails']
                    thumbnail = thumbnails[0]
            elif parsed_link.path == 'playlist':
                await ctx.send('Wiedergabelisten noch nicht unterstützt!')
        else:
            await ctx.send(f'Searching Youtube for `{song}`')
            result = YoutubeSearch(song, max_results=1).to_dict()
            for v in result:
                url_suffix = v['url_suffix']
                thumbnails = v['thumbnails']
                thumbnail = thumbnails[0]
                link = 'https://www.youtube.com' + url_suffix
        before_opts = '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
        opts = '-vn'
        ydl_opts = {'format' : 'bestaudio', 'noplaylist' : 'True'}
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
            attributes : dict = {"name" : video_title, "duration" : duration, "source" : source, "thumbnail" : thumbnail, "requested_by_id" : ctx.message.author.id, "url" : link, "channel_id" : ctx.channel.id, "guildid" : ctx.guild.id}
            if current_voice_client.is_playing():
                pos = add_to_queue(ctx.guild.id, attributes)
                song_embed.add_field(name='Position in queue:', value=f'{pos}', inline=True)
                await ctx.send(f'Zur Warteschlange hinzugefügt:', embed=song_embed)
            else:
                source = discord.FFmpegOpusAudio(source=source, executable='ffmpeg', before_options=before_opts, options=opts)
                song_embed.add_field(name='Position in queue:', value=0, inline=True)
                await ctx.send(f'Jetzt Spielen:', embed=song_embed)
                current_voice_client.play(source, after=partial(_handle_queue, current_voice_client.loop, ctx.guild.id, current_voice_client))


    @client.command(description='Resumes current song', usage='`/resume`')
    async def resume(ctx):
        member_vc = ctx.message.author.voice.channel
        client_vc = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if member_vc != None:
            if client_vc != None:
                if client_vc.channel == member_vc:
                    if client_vc.is_paused():
                        client_vc.resume()
                        await ctx.send(f'Medien nicht angehalten')
                    else:
                        await ctx.send(f'Keine Medienspiele')
                else:
                    await ctx.send(f'Derzeit in einem anderen Sprachkanal')
            else:
                await ctx.send(f'Derzeit nicht in Sprachkanal!')
        else:
            await ctx.send(f'Sie befinden sich nicht in einem Sprachkanal!')


    @client.command(description='Pauses current song', usage='`/pause`')
    async def pause(ctx):
        member_vc = ctx.message.author.voice.channel
        client_vc = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if member_vc != None:
            if client_vc != None:
                if client_vc.channel == member_vc:
                    if client_vc.is_playing():
                        client_vc.pause()
                        await ctx.send(f'Medien in Pause')
                    else:
                        await ctx.send(f'Keine Medienspiele')
                else:
                    await ctx.send(f'Derzeit in einem anderen Sprachkanal')
            else:
                await ctx.send(f'Derzeit nicht in Sprachkanal!')
        else:
            await ctx.send(f'Sie befinden sich nicht in einem Sprachkanal!')


    @client.command(description='Stops current song', usage='`/stop`')
    async def stop(ctx):
        member_vc = ctx.message.author.voice.channel
        client_vc = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if member_vc != None:
            if client_vc != None:
                if client_vc.channel == member_vc:
                    if client_vc.is_playing() or client_vc.is_paused():
                        client_vc.stop()
                        db.collection.delete_one({f"{ctx.guild.id}" : "entries"})
                        await ctx.send(f'Medien stehen an')
                    else:
                        await ctx.send(f'Keine Medienspiele')
                else:
                    await ctx.send(f'Derzeit in einem anderen Sprachkanal')
            else:
                await ctx.send(f'Derzeit nicht in Sprachkanal!')
        else:
            await ctx.send(f'Sie befinden sich nicht in einem Sprachkanal!')


def setup(client):
    client.add_cog(Moderation(client))
    client.add_cog(Chat(client))
    client.add_cog(Conversion(client))
    client.add_cog(Voice(client))

DISCORD_S3 = os.environ['DISCORD_TOKEN']     
client.run(DISCORD_S3)