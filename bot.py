import discord
from discord.ext import commands
from discord import app_commands
import os
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.members = True         # Needed for member info
intents.presences = True       # Needed for online status
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

GUILD_ID = int(os.getenv("GUILD_ID"))

# Load valid players from UsersList.txt
def load_users_list():
    try:
        with open("UsersList.txt", "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    except Exception as e:
        print(f"Error loading UsersList.txt: {e}")
        return set()

valid_players = load_users_list()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        guild_obj = discord.Object(id=GUILD_ID)
        await bot.tree.sync(guild=guild_obj)
        print("Slash commands synced!")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if str(message.channel.id) != os.getenv("VERIFICATION_CHANNEL_ID"):
        return
    
    # Only process if user has default nickname or no nickname
    if message.author.nick is not None and message.author.nick != message.author.name:
        return
    
    msg_content = message.content.strip()
    
    global valid_players
    valid_players = load_users_list()
    
    if msg_content in valid_players:
        guild = message.guild
        already_taken = False
        for member in guild.members:
            # Check if nickname or username matches and it's not this member
            if (member.nick == msg_content or member.name == msg_content) and member.id != message.author.id:
                already_taken = True
                break
        if already_taken:
            print(f"Nickname '{msg_content}' already taken.")
            return
        
        try:
            player_role = discord.utils.get(guild.roles, name="player")
            if player_role is None:
                print("Role 'player' not found.")
                return
            
            await message.author.edit(nick=msg_content)
            await message.author.add_roles(player_role)
            print(f"User {message.author} verified with nickname '{msg_content}'.")
        except Exception as e:
            print(f"Failed to set nickname or role: {e}")
    else:
        print(f"Invalid nickname attempt: {msg_content}")

    await bot.process_commands(message)

# --- Slash Commands ---

@bot.tree.command(name="hello", description="Say hello!")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello, {interaction.user.mention}!")

@bot.tree.command(name="serverinfo", description="Show server info")
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    total_members = guild.member_count
    online_members = sum(m.status != discord.Status.offline for m in guild.members)
    bots = sum(m.bot for m in guild.members)

    embed = discord.Embed(title="Server Info", color=discord.Color.blue())
    embed.add_field(name="Total Members", value=str(total_members))
    embed.add_field(name="Online Members", value=str(online_members))
    embed.add_field(name="Bots", value=str(bots))
    embed.add_field(name="About", value="Protanki Enjoyers is an open server created by **unknown**, you can invite your friends (if you want).")

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="react", description="React to a message (admin only)")
@app_commands.describe(message_id="ID of the message", emoji="Emoji to react with")
async def react(interaction: discord.Interaction, message_id: str, emoji: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You must be an administrator to use this command.", ephemeral=True)
        return

    try:
        channel = interaction.channel
        msg = await channel.fetch_message(int(message_id))
        await msg.add_reaction(emoji)
        await interaction.response.send_message(f"Reacted to message {message_id} with {emoji}")
    except Exception as e:
        await interaction.response.send_message(f"Failed to add reaction: {e}", ephemeral=True)

@bot.tree.command(name="avatar", description="Get a user's avatar")
@app_commands.describe(user="Select a user")
async def avatar(interaction: discord.Interaction, user: discord.Member):
    avatar_url = user.display_avatar.replace(size=256, static_format="png")
    embed = discord.Embed(title=f"{user.display_name}'s Avatar", color=discord.Color.green())
    embed.set_image(url=avatar_url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="say", description="Make the bot say something (admin only)")
@app_commands.describe(text="Text to say")
async def say(interaction: discord.Interaction, text: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You must be an administrator to use this command.", ephemeral=True)
        return
    await interaction.response.send_message(text)

# --- End commands ---

keep_alive()
bot.run(os.getenv("TOKEN"))
