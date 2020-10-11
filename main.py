import discord
from discord.ext import commands
import discord.utils
from translate import Translator
from datetime import datetime
import pytz


intents = discord.Intents.default()
intents.members = True


client = commands.Bot(command_prefix = '/', intents=intents)
client.remove_command('help')


@client.event
async def on_ready():
   await client.change_presence(activity=discord.Activity(status=discord.Status.online, type=discord.ActivityType.playing, name='Your Mom'))
   print('Bot ist bereit!')

@client.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.channels, name='def-role')
    async for message in channel.history(limit=1, oldest_first=True):
        role_name = message.content
    async for message in channel.history(limit=1):
        channel_name = message.content
    print(f'{member} ist {member.guild.name} beigetretten!')
    channelname = discord.utils.get(member.guild.channels, name=channel_name)
    await channelname.send(f'{member.mention} ist {member.guild.name} beigetretten!')
    await member.send(f'Willkommen bei {member.guild.name}, {member.mention}!')
    if channel == None:
        pass
    else:
        role = discord.utils.get(member.guild.roles, name=role_name)
        await member.add_roles(role)
        await channel.send(f'{member.mention} wurde die Rolle gegeben: {role}!')

@client.group(name='Misc.')
async def Misc():
    pass

@client.group()
async def Moderation():
    pass

@client.group(name='Translation/Conversion')
async def TranslationConversion():
    pass

@client.group()
async def Chat():
    pass

@Misc.command(description='Pings bots latency')
async def ping(ctx):
    await ctx.send(f'Pong! `{round(client.latency * 1000)}ms`')

@Moderation.command(description='Clears a given number of messages')
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount=0):
    await ctx.channel.purge(limit=amount+1)

@Moderation.command(description='Kicks a given user')
@commands.has_permissions(kick_members=True)
async def kick(ctx, user: discord.Member, *, reason=None):
    await user.kick(reason=reason)
    await ctx.send(f"{user.mention} wurde getretten!")

@Moderation.command(description='Bans a given user')
@commands.has_permissions(ban_members=True)
async def ban(ctx, user: discord.Member, *, reason=None):
    await user.ban(reason=reason)
    await ctx.send(f"{user.mention} wurde verboten!")


@Moderation.command(description='Unbans a given user')
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, member):
    banned_users = await ctx.guild.bans()
    member_name, member_discriminator = member.split('#')

    for ban_entry in banned_users:
        user = ban_entry.user

        if (user.name, user.discriminator) == (member_name, member_discriminator):
            await ctx.guild.unban(user)
            await ctx.send(f'{user.mention} wurde nicht verboten!')

@Moderation.command(description='Unbans all banned users')
@commands.has_permissions(ban_members=True)
async def unbanall(ctx):
    banned_users = await ctx.guild.bans()

    for ban_entry in banned_users:
        user = ban_entry.user
        await ctx.guild.unban(user)
        await ctx.send(f'{user.mention} wurde nicht verboten!')


@Misc.command(description='test')
async def test(ctx):
    await ctx.send(f'Es vermisst nie.')

@TranslationConversion.command(aliases=['translate'], description='Translate text (currently only supports German')
async def _translate(ctx, message):
    translator = Translator(to_lang="German")
    translation = translator.translate(message)
    await ctx.send(translation)


@Moderation.command(description='Gives role to a given user')
@commands.has_permissions(manage_roles=True)
async def giverole(ctx, member : discord.Member, role):
    role = discord.utils.get(ctx.guild.roles, name=role)
    if role == None:
        ctx.send('Diese Rolle existiert nicht! Bitte überprüfen Sie auf Tippfehler!')
    else:
        await member.add_roles(role)
        await ctx.send(f'{member.mention} wurde die Rolle gegeben: {role}!')

@Moderation.command(description='Remvoes role from a given user')
@commands.has_permissions(manage_roles=True)
async def removerole(ctx, member : discord.Member, role):
    
    role = discord.utils.get(ctx.guild.roles, name=role)
    if role == None:
        ctx.send('Diese Rolle existiert nicht! Bitte überprüfen Sie auf Tippfehler!')
    else:        
        await member.remove_roles(role)
        await ctx.send(f'Rolle: {role} wurde vom {member.mention} entfernt!')

@Moderation.command(description='Setup Command for automatic role assignment')
@commands.has_permissions(manage_roles=True)
async def autorole(ctx, role, channel):
    drole = discord.utils.get(ctx.guild.roles, name=role)
    if drole == None:
        await ctx.send('Diese Rolle existiert nicht! Bitte überprüfen Sie auf Tippfehler!')
    else:    
        overwrites = {ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),ctx.guild.me: discord.PermissionOverwrite(read_messages=True)}
        newchannel = await ctx.guild.create_text_channel('def-role', overwrites=overwrites, topic='Auto generated channel by RoboterVogel, DO NOT delete or make any messages here.')   
        await newchannel.send(f'{role}')
    sendchannel = discord.utils.get(ctx.guild.channels, name=channel)
    if sendchannel == None:
            await ctx.send('Diese Kanal existiert nicht! Bitte überprüfen Sie auf Tippfehler!')
    else:
            await newchannel.send(f'{channel}')
            await ctx.send(f'Neue Standardrolle ist {role}!')


@TranslationConversion.command(aliases=['FCP'], description='Converts USD to FCP (Far Cry Primal)')
async def fcp(ctx, amount):
    if amount == 'this server' or 'This Server' or 'server' or 'Server':
        fcp = 1
        await ctx.send(f'`{amount} USD` ≈ `{fcp} FCP`')
    else:    
        amount = amount.replace('$', '')
        usdtofcp = 1 / 30
        fcp = float(usdtofcp) * float(amount)
        await ctx.send(f'`{amount} USD ≈ {fcp} FCP`')


@TranslationConversion.command(aliases=['USD'], description='Converts FCP (Far Cry Primal) to USD')
async def usd(ctx, amount):
    amount = amount.replace('FCPfcp', '')
    fcptousd = 30
    usd = float(fcptousd) * float(amount)
    if amount == 1:
        await ctx.send(f'`{amount} FCP` ≈ `{usd} USD` or `1 Server`')
    else:
        await ctx.send(f'`{amount} FCP` ≈ `{usd} USD`')

@Chat.command(aliases=['hello', 'hallo', 'begruessung', 'begrüßung', 'greeting', 'gruessen', 'grüßen'], description='Greets user, or sends gretting to a different user')
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
    if author_id == 755875742595678290 and member == None:
        await ctx.send(f'{good} {time_of_day}, Vater!')
    elif author_id != 755875742595678290 and member == None:
        await ctx.send(f'{good} {time_of_day}, {ctx.message.author.mention}!')
    if member != None:
        if member == 'all':
            await ctx.send(f'{good} {time_of_day}, @everyone!')
        else:
            if member.id == 762768118212067328:
                await ctx.send(f'Hallo {ctx.message.author.mention}, wie gehts?')
            else:
                await ctx.send(f'Grüße von {ctx.message.author.mention}, {member.mention}!')

@Chat.command(aliases=['geburtstag'])
async def birthday(ctx, member : discord.Member):
    await ctx.send(f'Alles gute zum geburtstag, {member.mention}!  :tada:')
    await ctx.send('Jetzt singen wir alle das Geburtstagslied:')
    embed_name = 'Geburtstagslied :birthday:'
    embed_text = 'Zum Geburtstag viel Glück!\nZum Geburtstag viel Glück!\nZum Geburtstag liebe {name}!\nZum Geburtstag viel Glück!'.format(name=member.mention)
    lyric_embed = discord.Embed(name=embed_name)
    lyric_embed.add_field(name=embed_name, value=embed_text)
    await ctx.send(embed=lyric_embed)
    


@Misc.command(aliases=['help'])
async def _help(ctx):
    help_embed = discord.Embed(name='help')
    helptext = ''
    for group in client.commands.Group:
        for command in client.commands:
            for alias in client.aliases:
                if command.name[0] == '_':
                    commandtext = 'Name: ' + command.aliases[0] + 'Description: ' + command.description
                else:
                    commandtext = 'Name:' + command.name + 'Aliases: (' + alias + ') ' + 'Description: ' + command.description + '\n'
                    helptext += commandtext
        help_embed.add_field(name=group, value=helptext)
    await ctx.send(embed=help_embed)


key = 'NzYyNzY4MTE4MjEyMDY3MzI4.X3t9Kg.pLG6YLPVdbNqL9FI1iijx3YJ4T4'
client.run(key)