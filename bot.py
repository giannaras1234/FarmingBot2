import discord
from discord.ext import commands
import os
import asyncio
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.messages = True

bot = commands.Bot(command_prefix="/", intents=intents)

# Load valid players from UsersList.txt
def load_users_list():
    try:
        with open("UsersList.txt", "r") as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        print("[ERROR] UsersList.txt not found.")
        return set()

valid_players = load_users_list()

@bot.event
async def on_ready():
    print(f"[READY] Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    channel_id = os.getenv("VERIFICATION_CHANNEL_ID")
    if str(message.channel.id) != str(channel_id):
        return

    print(f"[DEBUG] Message in verification channel: '{message.content}' from {message.author}")

    if message.author.nick is not None and message.author.nick != message.author.name:
        print("[DEBUG] User already has a nickname, skipping.")
        return

    nickname = message.content.strip()

    global valid_players
    valid_players = load_users_list()

    print(f"[DEBUG] Valid players: {valid_players}")
    if nickname not in valid_players:
        print(f"[DEBUG] '{nickname}' is NOT in valid player list.")
        return

    guild = message.guild

    for member in guild.members:
        if (member.nick == nickname or member.name == nickname) and member.id != message.author.id:
            print(f"[DEBUG] Nickname '{nickname}' is already taken by {member}.")
            return

    try:
        role = discord.utils.get(guild.roles, name="player")
        if role is None:
            print("[ERROR] 'player' role not found in the server.")
            return

        await message.author.edit(nick=nickname)
        await message.author.add_roles(role)
        print(f"[SUCCESS] Set nickname and role for {message.author} to '{nickname}'")

    except Exception as e:
        print(f"[ERROR] Could not set nickname or role: {e}")

    await bot.process_commands(message)

# Slash Commands
@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello, {ctx.author.mention}!")

@bot.command()
async def serverinfo(ctx):
    guild = ctx.guild
    await ctx.send(f"Server name: {guild.name}\nTotal members: {guild.member_count}")

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    await ctx.send(member.avatar.url)

@bot.command()
async def react(ctx):
    message = await ctx.send("React to this message!")
    await message.add_reaction("❤")

@bot.command()
async def say(ctx, *, text: str):
    await ctx.send(text)

# Keep the bot alive with Flask (for Render hosting)
keep_alive()

# Run the bot with token from environment variable
bot.run(os.getenv("DISCORD_TOKEN"))
