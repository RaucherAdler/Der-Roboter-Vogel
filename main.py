import discord
from discord.ext import commands
import discord.utils

client = commands.Bot(command_prefix = '/')


@client.event
async def on_ready():
   await client.change_presence(status=discord.Status.online, activity=None)
   print('Bot ready')



@client.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round(client.latency * 1000)}ms')

@client.command()
#@commands.has_permissions(administrator=True)
async def clear(ctx, amount=0):
    await ctx.channel.purge(limit=amount+1)

@client.command()
#@commands.has_permissions(kick_members=True)
async def kick(ctx, user: discord.Member, *, reason=None):
    await user.kick(reason=reason)
    await ctx.send(f"{user} have been kicked sucessfully.")

@client.command()
#@commands.has_permissions(ban_members=True)
async def ban(ctx, user: discord.Member, *, reason=None):
    await user.ban(reason=reason)
    await ctx.send(f"{user} have been banned sucessfully.")


@client.command()
async def unban(ctx, *, member):
    banned_users = await ctx.guild.bans()
    member_name, member_discriminator = member.split('#')

    for ban_entry in banned_users:
        user = ban_entry.user

        if (user.name, user.discriminator) == (member_name, member_discriminator):
            await ctx.guild.unban(user)
            await ctx.send(f'Unbanned {user.mention}.')
            return

@client.command()
async def unbanall(ctx):
    banned_users = await ctx.guild.bans()

    for ban_entry in banned_users:
        user = ban_entry.user
        await ctx.guild.unban(user)
        await ctx.send(f'Unbanned {user.mention}.')

@client.event
async def on_user_join(user, *, ctx):
    print(f'{user} has joined the server')
    ctx.send(f"{user} has joined the server.")
    await user.send(f'Welcome to the server, {user}')

@client.command()
async def test(ctx):
    await ctx.send(f'It never misses.')

@client.command()
async def echo(ctx, message):
    await ctx.send(message)

@client.command()
async def giverole(ctx, member : discord.Member, * role: discord.Role):
    role = discord.utils.get(member.guild.roles, name=role)
    print(role)
    await member.add_roles(role)
    await ctx.send(f'{role} has been added to {member}')
#this doesn't work yet ^

f = open('key.txt')
key = f.read()
client.run(key)
