import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import json
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
WELCOME_ROLE_ID = int(os.getenv('WELCOME_ROLE_ID', '0'))
WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID', '0'))
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID', '0'))
BIRTHDAY_CHANNEL_ID = int(os.getenv('BIRTHDAY_CHANNEL_ID', '0'))
BIRTHDAY_ROLE_ID = int(os.getenv('BIRTHDAY_ROLE_ID', '0'))

# Bot Setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='/', intents=intents)

# Beautiful Symbols
SEPARATOR = "──────────────────────────"
SEPARATOR_FANCY = "────────── 𓆩✧𓆪 ──────────"
SERVER_TAG = "Hαƚɾҽԃ"
BULLET = "ㆍノ"

# Colors
COLOR_DEFAULT = discord.Color.from_rgb(25, 25, 112)  # Dark Blue
COLOR_SUCCESS = discord.Color.green()  # Green
COLOR_ERROR = discord.Color.red()  # Red

# Database files
STATS_FILE = "member_stats.json"
WARNINGS_FILE = "warnings.json"
ROLE_BUTTONS_FILE = "role_buttons.json"
BIRTHDAYS_FILE = "birthdays.json"

# ============================================================================
# DATABASE FUNCTIONS
# ============================================================================


def load_stats():
    """Load member stats from file"""
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_stats(stats):
    """Save member stats to file"""
    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f, indent=2)


def load_warnings():
    """Load warnings from file"""
    if os.path.exists(WARNINGS_FILE):
        with open(WARNINGS_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_warnings(warnings):
    """Save warnings to file"""
    with open(WARNINGS_FILE, 'w') as f:
        json.dump(warnings, f, indent=2)


def load_birthdays():
    """Load birthdays from file"""
    if os.path.exists(BIRTHDAYS_FILE):
        with open(BIRTHDAYS_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_birthdays(birthdays):
    """Save birthdays to file"""
    with open(BIRTHDAYS_FILE, 'w') as f:
        json.dump(birthdays, f, indent=2)


def load_role_buttons():
    """Load role button config"""
    if os.path.exists(ROLE_BUTTONS_FILE):
        with open(ROLE_BUTTONS_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_role_buttons(config):
    """Save role button config"""
    with open(ROLE_BUTTONS_FILE, 'w') as f:
        json.dump(config, f, indent=2)


# ============================================================================
# KEEP-ALIVE HEARTBEAT
# ============================================================================

@tasks.loop(minutes=5)
async def keep_alive():
    """Keep bot alive by sending a heartbeat every 5 minutes"""
    print(f"Heartbeat: Bot is still alive! ({datetime.now().strftime('%H:%M:%S')})")


@keep_alive.before_loop
async def before_keep_alive():
    """Wait until bot is ready before starting heartbeat"""
    await bot.wait_until_ready()
    print("Keep-Alive heartbeat started!")


# ============================================================================
# BIRTHDAY CHECK TASK
# ============================================================================

@tasks.loop(hours=1)
async def check_birthdays():
    """Check for birthdays every hour"""
    if BIRTHDAY_CHANNEL_ID == 0:
        return

    birthday_channel = bot.get_channel(BIRTHDAY_CHANNEL_ID)
    if not birthday_channel:
        return

    birthdays = load_birthdays()
    today = datetime.now().strftime("%d.%m")
    
    checked_today_file = "birthdays_checked_today.json"
    checked_today = {}
    if os.path.exists(checked_today_file):
        with open(checked_today_file, 'r') as f:
            checked_today = json.load(f)
    
    # Prüfe alle Geburtstage
    for user_id, birthday_data in birthdays.items():
        birthday_date = birthday_data['date']
        user_name = birthday_data['name']
        
        # Wenn heute Geburtstag ist und wir haben noch nicht gratuliert
        if birthday_date == today and user_id not in checked_today:
            try:
                user = await bot.fetch_user(int(user_id))
                
                embed = discord.Embed(
                    title=SEPARATOR_FANCY,
                    description=f"Happy Birthday {user.mention}!",
                    color=COLOR_DEFAULT
                )
                embed.add_field(
                    name=f"{BULLET} Congratulations!",
                    value=f"Happy Birthday, {user_name}!\n\nWe hope you had a wonderful day!",
                    inline=False
                )
                embed.set_footer(text=f"{SERVER_TAG} Server")
                
                await birthday_channel.send(embed=embed)
                print(f"Birthday message sent for {user_name}")
                
                # Speichern dass wir heute schon gratuliert haben
                checked_today[user_id] = today
                with open(checked_today_file, 'w') as f:
                    json.dump(checked_today, f, indent=2)
            
            except Exception as e:
                print(f"Error sending birthday message: {e}")
    
    # Reset checked_today um Mitternacht
    if datetime.now().hour == 0:
        if os.path.exists(checked_today_file):
            os.remove(checked_today_file)


@check_birthdays.before_loop
async def before_check_birthdays():
    """Wait until bot is ready"""
    await bot.wait_until_ready()
    print("Birthday check task started!")


# ============================================================================
# EVENTS
# ============================================================================


@bot.event
async def on_ready():
    """Called when bot goes online"""
    print(f'Bot is online as {bot.user}')
    print(f'Active in {len(bot.guilds)} server(s)')

    # Start keep-alive heartbeat
    if not keep_alive.is_running():
        keep_alive.start()
        print("Keep-Alive loop started!")

    # Start birthday check
    if not check_birthdays.is_running():
        check_birthdays.start()
        print("Birthday check loop started!")

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} Slash Commands GLOBALLY")

        for guild in bot.guilds:
            try:
                await bot.tree.sync(guild=guild)
                print(f"Synced commands to guild: {guild.name}")
            except Exception as e:
                print(f"Error syncing to {guild.name}: {e}")
    except Exception as e:
        print(f"Error syncing commands: {e}")

    # Bot Status
    activity = discord.Activity(type=discord.ActivityType.playing,
                                name="Combat Warriors")
    await bot.change_presence(activity=activity)


@bot.event
async def on_member_join(member):
    """Called when a new user joins"""
    try:
        if WELCOME_ROLE_ID != 0:
            role = member.guild.get_role(WELCOME_ROLE_ID)
            if role:
                await member.add_roles(role)
                print(f"Assigned role {role.name} to {member.name}")

        if WELCOME_CHANNEL_ID != 0:
            welcome_channel = bot.get_channel(WELCOME_CHANNEL_ID)
            if welcome_channel:
                embed = discord.Embed(
                    title=f"Welcome to {SERVER_TAG}",
                    description=
                    f"Welcome {member.mention}!\n\nWe're excited to have you join our All Girls Combat Warriors community!",
                    color=COLOR_DEFAULT)
                embed.set_thumbnail(url=member.avatar.url if member.
                                    avatar else member.default_avatar.url)
                embed.add_field(name="Note",
                                value="Please read the rules and have fun!",
                                inline=False)
                await welcome_channel.send(embed=embed)

    except Exception as e:
        print(f"Error on member join: {e}")


@bot.event
async def on_message(message):
    """Track message count for leaderboard"""
    if message.author.bot:
        return

    # Update stats
    stats = load_stats()
    user_id = str(message.author.id)

    if user_id not in stats:
        stats[user_id] = {"messages": 0, "name": message.author.name}

    stats[user_id]["messages"] += 1
    stats[user_id]["name"] = message.author.name
    save_stats(stats)

    await bot.process_commands(message)


@bot.event
async def on_message_delete(message):
    """Log deleted messages"""
    if message.author.bot or LOG_CHANNEL_ID == 0:
        return

    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if not log_channel:
        return

    embed = discord.Embed(
        title="Message Deleted",
        description=
        f"Author: {message.author.mention}\nChannel: {message.channel.mention}",
        color=COLOR_ERROR)
    embed.add_field(name="Content",
                    value=message.content or "No text content",
                    inline=False)
    embed.set_footer(text=f"User ID: {message.author.id}")

    await log_channel.send(embed=embed)


@bot.event
async def on_message_edit(before, after):
    """Log edited messages"""
    if before.author.bot or LOG_CHANNEL_ID == 0 or before.content == after.content:
        return

    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if not log_channel:
        return

    embed = discord.Embed(
        title="Message Edited",
        description=
        f"Author: {before.author.mention}\nChannel: {before.channel.mention}",
        color=COLOR_DEFAULT)
    embed.add_field(name="Before",
                    value=before.content or "No text",
                    inline=False)
    embed.add_field(name="After",
                    value=after.content or "No text",
                    inline=False)
    embed.set_footer(text=f"User ID: {before.author.id}")

    await log_channel.send(embed=embed)


# ============================================================================
# SLASH COMMANDS - INFO
# ============================================================================


@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    """Show bot ping"""
    embed = discord.Embed(
        title="Pong",
        description=f"Latency: {round(bot.latency * 1000)}ms",
        color=COLOR_SUCCESS)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="membercount", description="Show total server members")
async def membercount(interaction: discord.Interaction):
    """Show how many members are in the server"""
    embed = discord.Embed(
        title="Server Statistics",
        description=f"Total Members: {interaction.guild.member_count}",
        color=COLOR_DEFAULT)
    embed.add_field(name="Info",
                    value="All active members in the Hatred server",
                    inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="leaderboard", description="Show message leaderboard")
async def leaderboard(interaction: discord.Interaction):
    """Show top message senders"""
    stats = load_stats()

    if not stats:
        embed = discord.Embed(title="Leaderboard",
                              description="No data yet",
                              color=COLOR_DEFAULT)
        await interaction.response.send_message(embed=embed)
        return

    # Sort by messages
    sorted_stats = sorted(stats.items(),
                          key=lambda x: x[1]['messages'],
                          reverse=True)[:10]

    embed = discord.Embed(
        title=f"────────── {SERVER_TAG} Leaderboard ──────────",
        color=COLOR_DEFAULT)

    for idx, (user_id, data) in enumerate(sorted_stats, 1):
        embed.add_field(name=f"{BULLET} #{idx} - {data['name']}",
                        value=f"Messages: {data['messages']}",
                        inline=False)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="rules", description="Show server rules")
async def rules(interaction: discord.Interaction):
    """Send server rules"""
    embed = discord.Embed(title=f"──────── {SERVER_TAG} Rules ────────",
                          color=COLOR_DEFAULT)
    embed.add_field(name=f"{BULLET} Respect",
                    value="Treat all members with respect and kindness",
                    inline=False)
    embed.add_field(name=f"{BULLET} No Spam",
                    value="Do not spam messages or content",
                    inline=False)
    embed.add_field(name=f"{BULLET} NSFW Content",
                    value="Keep NSFW content to designated channels only",
                    inline=False)
    embed.add_field(name=f"{BULLET} No Cheating",
                    value="Cheating and exploits are strictly forbidden",
                    inline=False)
    embed.add_field(name=f"{BULLET} No Discrimination",
                    value="Discrimination is not tolerated",
                    inline=False)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="userinfo", description="Show information about a user")
@app_commands.describe(user="The user you want info about")
async def userinfo(interaction: discord.Interaction,
                   user: discord.User = None):
    """Show user information"""
    if user is None:
        user = interaction.user

    try:
        member = await interaction.guild.fetch_member(user.id)
        joined = member.joined_at.strftime('%d.%m.%Y')
    except:
        joined = "Unknown"

    # Get stats
    stats = load_stats()
    messages = stats.get(str(user.id), {}).get('messages', 0)
    
    # Get birthday
    birthdays = load_birthdays()
    birthday = birthdays.get(str(user.id), {}).get('date', 'Not set')

    embed = discord.Embed(title=user.name, color=COLOR_DEFAULT)
    embed.set_thumbnail(
        url=user.avatar.url if user.avatar else user.default_avatar.url)
    embed.add_field(name=f"{BULLET} ID", value=user.id, inline=True)
    embed.add_field(name=f"{BULLET} Joined", value=joined, inline=True)
    embed.add_field(name=f"{BULLET} Messages", value=messages, inline=True)
    embed.add_field(name=f"{BULLET} Birthday", value=birthday, inline=True)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="help", description="Show all available commands")
async def help_command(interaction: discord.Interaction):
    """Show help for all commands"""
    embed = discord.Embed(title=f"──────── {SERVER_TAG} Commands ────────",
                          description="Here are all available commands:",
                          color=COLOR_DEFAULT)

    embed.add_field(name=f"{BULLET} Admin/Mod Commands",
                    value="`/embed` - Create a formatted message\n"
                    "`/announce` - Send announcement\n"
                    "`/warn` - Warn a member\n"
                    "`/kick` - Kick a member\n"
                    "`/ban` - Ban a member\n"
                    "`/role_button` - Create reaction role button\n"
                    "`/welcome_setup` - Set welcome role",
                    inline=False)

    embed.add_field(name=f"{BULLET} Birthday Commands",
                    value="`/birthday set` - Set your birthday\n"
                    "`/birthday view` - View your birthday\n"
                    "`/birthday list` - View all birthdays\n"
                    "`/birthday remove` - Remove your birthday\n"
                    "`/birthday test` - Test birthday message",
                    inline=False)

    embed.add_field(name=f"{BULLET} Info Commands",
                    value="`/ping` - Show bot latency\n"
                    "`/membercount` - Show member count\n"
                    "`/leaderboard` - Show message leaderboard\n"
                    "`/userinfo` - Show user information\n"
                    "`/help` - Show this message",
                    inline=False)

    embed.set_footer(text=f"{SERVER_TAG} Server")
    await interaction.response.send_message(embed=embed)


# ============================================================================
# BIRTHDAY COMMANDS
# ============================================================================

@bot.tree.command(name="birthday", description="Birthday commands")
@app_commands.describe(
    action="set, view, list, remove, or test",
    date="Your birthday in DD.MM format (only for set)"
)
async def birthday(interaction: discord.Interaction, action: str, date: str = None):
    """Manage birthdays"""
    
    # Prüfe ob User Birthday Announcement Role hat
    birthday_role = interaction.guild.get_role(BIRTHDAY_ROLE_ID)
    if birthday_role and birthday_role not in interaction.user.roles:
        embed = discord.Embed(
            title="Permission Denied",
            description=f"You need the {birthday_role.mention} role to use this command",
            color=COLOR_ERROR
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    action = action.lower()
    birthdays = load_birthdays()
    user_id = str(interaction.user.id)
    
    # SET BIRTHDAY
    if action == "set":
        if not date:
            embed = discord.Embed(
                title="Error",
                description="Please provide your birthday in DD.MM format (e.g., 25.12)",
                color=COLOR_ERROR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            # Validiere das Format
            datetime.strptime(date, "%d.%m")
            
            birthdays[user_id] = {
                "name": interaction.user.name,
                "date": date
            }
            save_birthdays(birthdays)
            
            embed = discord.Embed(
                title="Birthday Set",
                description=f"Your birthday has been set to {date}",
                color=COLOR_SUCCESS
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        except ValueError:
            embed = discord.Embed(
                title="Invalid Format",
                description="Please use DD.MM format (e.g., 25.12 for December 25)",
                color=COLOR_ERROR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # VIEW OWN BIRTHDAY
    elif action == "view":
        if user_id not in birthdays:
            embed = discord.Embed(
                title="No Birthday Set",
                description="You haven't set your birthday yet. Use /birthday set DD.MM",
                color=COLOR_ERROR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        birthday_date = birthdays[user_id]['date']
        embed = discord.Embed(
            title="Your Birthday",
            description=f"Your birthday is set to: {birthday_date}",
            color=COLOR_DEFAULT
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # LIST ALL BIRTHDAYS
    elif action == "list":
        if not birthdays:
            embed = discord.Embed(
                title="Birthday List",
                description="No birthdays registered yet",
                color=COLOR_DEFAULT
            )
            await interaction.response.send_message(embed=embed)
            return
        
        # Sort by date
        sorted_birthdays = sorted(birthdays.items(), 
                                 key=lambda x: x[1]['date'])
        
        embed = discord.Embed(
            title=f"────────── {SERVER_TAG} Birthday List ──────────",
            color=COLOR_DEFAULT
        )
        
        for user_id, data in sorted_birthdays:
            embed.add_field(
                name=f"{BULLET} {data['name']}",
                value=f"Birthday: {data['date']}",
                inline=False
            )
        
        embed.set_footer(text=f"{SERVER_TAG} Server")
        await interaction.response.send_message(embed=embed)
    
    # REMOVE BIRTHDAY
    elif action == "remove":
        if user_id not in birthdays:
            embed = discord.Embed(
                title="No Birthday Set",
                description="You haven't set your birthday yet",
                color=COLOR_ERROR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        del birthdays[user_id]
        save_birthdays(birthdays)
        
        embed = discord.Embed(
            title="Birthday Removed",
            description="Your birthday has been removed",
            color=COLOR_SUCCESS
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # TEST BIRTHDAY MESSAGE
    elif action == "test":
        if BIRTHDAY_CHANNEL_ID == 0:
            embed = discord.Embed(
                title="Error",
                description="Birthday channel is not configured",
                color=COLOR_ERROR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            birthday_channel = bot.get_channel(BIRTHDAY_CHANNEL_ID)
            if not birthday_channel:
                embed = discord.Embed(
                    title="Error",
                    description="Birthday channel not found",
                    color=COLOR_ERROR
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Sende Test-Nachricht
            embed = discord.Embed(
                title=SEPARATOR_FANCY,
                description=f"Happy Birthday {interaction.user.mention}!",
                color=COLOR_DEFAULT
            )
            embed.add_field(
                name=f"{BULLET} Congratulations!",
                value=f"Happy Birthday, {interaction.user.name}!\n\nWe hope you had a wonderful day!",
                inline=False
            )
            embed.set_footer(text=f"{SERVER_TAG} Server - TEST MESSAGE")
            
            await birthday_channel.send(embed=embed)
            
            # Bestätigung
            confirm = discord.Embed(
                title="Test Message Sent",
                description=f"Birthday message sent to {birthday_channel.mention}",
                color=COLOR_SUCCESS
            )
            await interaction.response.send_message(embed=confirm, ephemeral=True)
        
        except Exception as e:
            error = discord.Embed(
                title="Error",
                description=f"Failed to send test message: {e}",
                color=COLOR_ERROR
            )
            await interaction.response.send_message(embed=error, ephemeral=True)
    
    else:
        embed = discord.Embed(
            title="Invalid Action",
            description="Use: set, view, list, remove, or test",
            color=COLOR_ERROR
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ============================================================================
# ADMIN COMMANDS - MESSAGES & ANNOUNCEMENTS
# ============================================================================


@bot.tree.command(name="embed", description="Create a formatted message")
@app_commands.describe(
    title="Message title",
    description="Message content",
    color="Color: pink, red, blue, green, purple, gold, orange")
async def send_embed(interaction: discord.Interaction,
                     title: str,
                     description: str,
                     color: str = "pink"):
    """Create a formatted embed message"""

    if not interaction.user.guild_permissions.manage_messages:
        embed = discord.Embed(
            title="Permission Denied",
            description="You need 'Manage Messages' permission",
            color=COLOR_ERROR)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    colors = {
        'pink': discord.Color.pink(),
        'red': discord.Color.red(),
        'blue': discord.Color.blue(),
        'green': discord.Color.green(),
        'purple': discord.Color.purple(),
        'gold': discord.Color.gold(),
        'orange': discord.Color.orange()
    }

    if color.lower() in colors:
        color_obj = colors[color.lower()]
    else:
        try:
            color_obj = discord.Color(int(color.replace('#', ''), 16))
        except:
            color_obj = COLOR_DEFAULT

    embed = discord.Embed(title=title,
                          description=description,
                          color=color_obj)
    embed.set_footer(text=f"{SERVER_TAG} Server",
                     icon_url=interaction.guild.icon.url
                     if interaction.guild.icon else None)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="announce", description="Send announcement")
@app_commands.describe(channel="Target channel",
                       message="Announcement message")
async def announce(interaction: discord.Interaction,
                   channel: discord.TextChannel, message: str):
    """Send announcement to a channel"""

    if not interaction.user.guild_permissions.manage_messages:
        embed = discord.Embed(
            title="Permission Denied",
            description="You need 'Manage Messages' permission",
            color=COLOR_ERROR)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    try:
        embed = discord.Embed(title=SEPARATOR_FANCY,
                              description=message,
                              color=COLOR_DEFAULT)
        embed.set_footer(text=f"{SERVER_TAG} Server")
        await channel.send(embed=embed)

        confirm = discord.Embed(
            title="Announcement Sent",
            description=f"Message sent to {channel.mention}!",
            color=COLOR_SUCCESS)
        await interaction.response.send_message(embed=confirm, ephemeral=True)
    except Exception as e:
        error = discord.Embed(title="Error",
                              description=f"Failed to send: {e}",
                              color=COLOR_ERROR)
        await interaction.response.send_message(embed=error, ephemeral=True)


# ============================================================================
# MODERATION COMMANDS
# ============================================================================


@bot.tree.command(name="warn", description="Warn a member")
@app_commands.describe(member="Member to warn", reason="Reason for warning")
async def warn(interaction: discord.Interaction,
               member: discord.Member,
               reason: str = "No reason provided"):
    """Warn a member"""

    if not interaction.user.guild_permissions.moderate_members:
        embed = discord.Embed(title="Permission Denied",
                              description="You need moderation permissions",
                              color=COLOR_ERROR)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    warnings = load_warnings()
    user_id = str(member.id)

    if user_id not in warnings:
        warnings[user_id] = []

    warnings[user_id].append({
        "reason": reason,
        "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "mod": interaction.user.name
    })

    save_warnings(warnings)
    warn_count = len(warnings[user_id])

    embed = discord.Embed(title="Member Warned",
                          description=f"{member.mention} has been warned",
                          color=COLOR_ERROR)
    embed.add_field(name=f"{BULLET} Reason", value=reason, inline=False)
    embed.add_field(name=f"{BULLET} Total Warnings",
                    value=warn_count,
                    inline=False)
    embed.set_footer(text=f"Warned by {interaction.user.name}")

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="kick", description="Kick a member")
@app_commands.describe(member="Member to kick", reason="Reason for kick")
async def kick(interaction: discord.Interaction,
               member: discord.Member,
               reason: str = "No reason provided"):
    """Kick a member"""

    if not interaction.user.guild_permissions.kick_members:
        embed = discord.Embed(title="Permission Denied",
                              description="You need kick permissions",
                              color=COLOR_ERROR)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    try:
        await member.kick(reason=reason)

        embed = discord.Embed(title="Member Kicked",
                              description=f"{member.mention} has been kicked",
                              color=COLOR_SUCCESS)
        embed.add_field(name=f"{BULLET} Reason", value=reason, inline=False)
        embed.set_footer(text=f"Kicked by {interaction.user.name}")

        await interaction.response.send_message(embed=embed)
    except Exception as e:
        error = discord.Embed(title="Error",
                              description=f"Could not kick member: {e}",
                              color=COLOR_ERROR)
        await interaction.response.send_message(embed=error, ephemeral=True)


@bot.tree.command(name="ban", description="Ban a member")
@app_commands.describe(member="Member to ban", reason="Reason for ban")
async def ban(interaction: discord.Interaction,
              member: discord.Member,
              reason: str = "No reason provided"):
    """Ban a member"""

    if not interaction.user.guild_permissions.ban_members:
        embed = discord.Embed(title="Permission Denied",
                              description="You need ban permissions",
                              color=COLOR_ERROR)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    try:
        await member.ban(reason=reason)

        embed = discord.Embed(title="Member Banned",
                              description=f"{member.mention} has been banned",
                              color=COLOR_SUCCESS)
        embed.add_field(name=f"{BULLET} Reason", value=reason, inline=False)
        embed.set_footer(text=f"Banned by {interaction.user.name}")

        await interaction.response.send_message(embed=embed)
    except Exception as e:
        error = discord.Embed(title="Error",
                              description=f"Could not ban member: {e}",
                              color=COLOR_ERROR)
        await interaction.response.send_message(embed=error, ephemeral=True)


# ============================================================================
# REACTION ROLE BUTTONS
# ============================================================================


class RoleButton(discord.ui.View):

    def __init__(self, role_id: int):
        super().__init__(timeout=None)
        self.role_id = role_id

    @discord.ui.button(label="Get Role", style=discord.ButtonStyle.blurple)
    async def role_button(self, interaction: discord.Interaction,
                          button: discord.ui.Button):
        """Give user the role when they click the button"""
        role = interaction.guild.get_role(self.role_id)

        if not role:
            embed = discord.Embed(title="Error",
                                  description="Role not found",
                                  color=COLOR_ERROR)
            await interaction.response.send_message(embed=embed,
                                                    ephemeral=True)
            return

        try:
            if role in interaction.user.roles:
                await interaction.user.remove_roles(role)
                embed = discord.Embed(
                    title="Role Removed",
                    description=f"{role.mention} has been removed",
                    color=COLOR_SUCCESS)
            else:
                await interaction.user.add_roles(role)
                embed = discord.Embed(
                    title="Role Added",
                    description=f"{role.mention} has been added",
                    color=COLOR_SUCCESS)

            await interaction.response.send_message(embed=embed,
                                                    ephemeral=True)
        except Exception as e:
            error = discord.Embed(title="Error",
                                  description=f"Could not assign role: {e}",
                                  color=COLOR_ERROR)
            await interaction.response.send_message(embed=error,
                                                    ephemeral=True)


@bot.tree.command(name="role_button",
                  description="Create a button to get a role")
@app_commands.describe(role="The role to assign",
                       title="Button label (what it should say)")
async def role_button(interaction: discord.Interaction,
                      role: discord.Role,
                      title: str = "Get Role"):
    """Create a reaction role button"""

    if not interaction.user.guild_permissions.manage_roles:
        embed = discord.Embed(
            title="Permission Denied",
            description="You need role management permissions",
            color=COLOR_ERROR)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    try:
        view = RoleButton(role.id)
        button = view.children[0]
        button.label = title

        embed = discord.Embed(
            title=f"Click to get {role.name}",
            description="Click the button below to receive this role!",
            color=COLOR_DEFAULT)
        embed.set_footer(text=f"{SERVER_TAG} Server")

        await interaction.response.send_message(embed=embed, view=view)
    except Exception as e:
        error = discord.Embed(title="Error",
                              description=f"Could not create button: {e}",
                              color=COLOR_ERROR)
        await interaction.response.send_message(embed=error, ephemeral=True)


@bot.tree.command(name="welcome_setup",
                  description="Set welcome role for new members")
@app_commands.describe(role="The role new members will receive")
async def welcome_setup(interaction: discord.Interaction, role: discord.Role):
    """Set the role new members receive"""

    if not interaction.user.guild_permissions.manage_roles:
        embed = discord.Embed(title="Permission Denied",
                              description="You need Administrator permissions",
                              color=COLOR_ERROR)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    try:
        embed = discord.Embed(
            title="Welcome Role Set",
            description=f"New members will now receive: {role.mention}",
            color=COLOR_SUCCESS)
        embed.add_field(name="Note",
                        value=f"Role ID: {role.id}\n\n"
                        f"Please update your `.env` file with:\n"
                        f"`WELCOME_ROLE_ID={role.id}`\n\n"
                        f"Then restart the bot!",
                        inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        error = discord.Embed(title="Error",
                              description=f"Error: {e}",
                              color=COLOR_ERROR)
        await interaction.response.send_message(embed=error, ephemeral=True)


# ============================================================================
# ERROR HANDLING
# ============================================================================


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction,
                               error: app_commands.AppCommandError):
    """Handle slash command errors"""
    if isinstance(error, app_commands.MissingPermissions):
        embed = discord.Embed(title="Permission Denied",
                              description="You don't have permission!",
                              color=COLOR_ERROR)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(title="Error Occurred",
                              description=str(error),
                              color=COLOR_ERROR)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        print(f"Error: {error}")


# ============================================================================
# BOT START
# ============================================================================

if __name__ == "__main__":
    print("Starting Hatred Bot with Birthday Module and Keep-Alive Heartbeat...")
    print("Bot will keep itself alive every 5 minutes!")
    print("Birthday check runs every hour!")
    print("Using color scheme: Dark Blue (default), Green (success), Red (error)")
    bot.run(TOKEN)
