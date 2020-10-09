import discord
from discord.ext import commands
import discord.utils
from translate import Translator
import redis

client = commands.Bot(command_prefix = '/')
client.remove_command('help')

@client.event
async def on_message(message):
    channel_name = message.channel.name
    if channel_name == 'def-role':
        return message


@client.event
async def on_ready():
   await client.change_presence(status=discord.Status.online, activity=None)
   print('Bot ist bereit!')

@client.event
async def on_user_join(member, ctx):
    print(f'{member} has joined the server')
    await ctx.send(f'{member.mention} has joined the server.')
    await member.send(f'Welcome to the server, {member.mention}')
    autorole = on_message()
    role = discord.utils.get(ctx.guild.roles, name=autorole)
    await member.add_roles(role)
    await ctx.send(f'{member.mention} wurde die Rolle gegeben: {role}!')

@client.command()
async def ping(ctx):
    await ctx.send(f'Pong! `{round(client.latency * 1000)}ms`')

@client.command()
#@commands.has_permissions(administrator=True)
async def clear(ctx, amount=0):
    await ctx.channel.purge(limit=amount+1)

@client.command()
#@commands.has_permissions(kick_members=True)
async def kick(ctx, user: discord.Member, *, reason=None):
    await user.kick(reason=reason)
    await ctx.send(f"{user.mention} wurde getretten!")

@client.command()
#@commands.has_permissions(ban_members=True)
async def ban(ctx, user: discord.Member, *, reason=None):
    await user.ban(reason=reason)
    await ctx.send(f"{user.mention} wurde verboten!")


@client.command()
async def unban(ctx, *, member):
    banned_users = await ctx.guild.bans()
    member_name, member_discriminator = member.split('#')

    for ban_entry in banned_users:
        user = ban_entry.user

        if (user.name, user.discriminator) == (member_name, member_discriminator):
            await ctx.guild.unban(user)
            await ctx.send(f'{user.mention} wurde nicht verboten!')

@client.command()
async def unbanall(ctx):
    banned_users = await ctx.guild.bans()

    for ban_entry in banned_users:
        user = ban_entry.user
        await ctx.guild.unban(user)
        await ctx.send(f'{user.mention} wurde nicht verboten!')

@client.command()
async def test(ctx):
    await ctx.send(f'Es vermisst nie.')

@client.command(aliases=['translate'])
async def _translate(ctx, message):
    translator = Translator(to_lang="German")
    translation = translator.translate(message)
    await ctx.send(translation)

@client.command()
async def giverole(ctx, member : discord.Member, role):
    role = discord.utils.get(ctx.guild.roles, name=role)
    if role == None:
        ctx.send('Diese Rolle existiert nicht! Bitte überprüfen Sie auf Tippfehler!')
    else:
        await member.add_roles(role)
        await ctx.send(f'{member.mention} wurde die Rolle gegeben: {role}!')

@client.command()
async def removerole(ctx, member : discord.Member, role):
    
    role = discord.utils.get(ctx.guild.roles, name=role)
    if role == None:
        ctx.send('Diese Rolle existiert nicht! Bitte überprüfen Sie auf Tippfehler!')
    else:        
        await member.remove_roles(role)
        await ctx.send(f'Rolle: {role} wurde vom {member.mention} entfernt!')

@client.command()
async def defrole(ctx, role):
    role = discord.utils.get(ctx.guild.roles, name=role)
    if role == None:
        ctx.send('Diese Rolle existiert nicht! Bitte überprüfen Sie auf Tippfehler!')
    else:    
        botrole = discord.utlis.get(ctx.guild.roles, name='Der Roboter Vogel')
        perms = client.overwrites_for(botrole)
        perms.send_messages = False
        await ctx.guild.create_text_channel('def-role', overwrites=perms)
        await ctx.send(role)
        await ctx.send(f'Neue Standardrolle ist {role}!')


#temp disabled
#@client.command(aliases=['help'])
#async def _help(ctx):
#    helptext = "```"
#    for command in client.commands:
#        commandtext = name + ': ' + description + '\n'
#        helptext += commandtext
#    await ctx.send(helptext)


key = 'NzYyNzY4MTE4MjEyMDY3MzI4.X3t9Kg.pLG6YLPVdbNqL9FI1iijx3YJ4T4'
client.run(key)