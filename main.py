import discord
from discord.ext import commands
import discord.utils
from translate import Translator

client = commands.Bot(command_prefix = '/')

@client.event
async def on_ready():
   await client.change_presence(status=discord.Status.online, activity=None)
   print('Bot ist fertig.')


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
            return

@client.command()
async def unbanall(ctx):
    banned_users = await ctx.guild.bans()

    for ban_entry in banned_users:
        user = ban_entry.user
        await ctx.guild.unban(user)
        await ctx.send(f'{user.mention} wurde nicht verboten.')

@client.event
async def on_user_join(member, *, ctx):
    print(f'{member} has joined the server')
    ctx.send(f"{member.mention} has joined the server.")
    await client.send(f'Welcome to the server, {member.mention}')

@client.command()
async def test(ctx):
    await ctx.send(f'Es vermisst nie.')

@client.command(aliases=['translate'])
async def echo(ctx, message):
    translator = Translator(to_lang="German")
    translation = translator.translate(message)
    await ctx.send(translation)

@client.command(name="giverole", description="Gives role to a given user")
async def giverole(ctx, member : discord.Member, * role: discord.Role):
    role = discord.utils.get(member.guild.roles, name=role)
    print(role)
    await member.add_roles(role)
    await ctx.send(f'{role} has been added to {member}')
#this doesn't work yet ^

@client.command(aliases=['commands'])
async def _help(self, ctx):
    helptext = "```"
    for command in self.bot.commands:
        helptext+=f"{command}\n"
    helptext+="```"
    await ctx.send(helptext)

key = 'NzYyNzY4MTE4MjEyMDY3MzI4.X3t9Kg.pLG6YLPVdbNqL9FI1iijx3YJ4T4'
client.run(key)
