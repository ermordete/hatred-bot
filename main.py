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
EMBED_EDITOR_ROLE_ID = 1477298626689765410
TICKET_SUPPORT_ROLE_ID = int(os.getenv('TICKET_SUPPORT_ROLE_ID', '0'))

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
EMBEDS_FILE = "embeds.json"
STICKY_FILE = "sticky_messages.json"
TICKETS_FILE = "tickets.json"

# ============================================================================
# DATABASE FUNCTIONS
# ============================================================================

def load_embeds():
    if os.path.exists(EMBEDS_FILE):
        with open(EMBEDS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_embeds(embeds):
    with open(EMBEDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(embeds, f, indent=2, ensure_ascii=False)

def load_sticky():
    if os.path.exists(STICKY_FILE):
        with open(STICKY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_sticky(sticky):
    with open(STICKY_FILE, 'w', encoding='utf-8') as f:
        json.dump(sticky, f, indent=2, ensure_ascii=False)

def load_tickets():
    if os.path.exists(TICKETS_FILE):
        with open(TICKETS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_tickets(tickets):
    with open(TICKETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tickets, f, indent=2, ensure_ascii=False)

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
# HELPER FUNCTION: Dict zu Embed konvertieren
# ============================================================================

def dict_to_embed(embed_data: dict) -> discord.Embed:
    try:
        color_hex = embed_data.get('color', '#191b70')
        color = discord.Color(int(color_hex.replace('#', ''), 16))
        
        embed = discord.Embed(
            title=embed_data.get('title'),
            description=embed_data.get('description'),
            color=color
        )
        
        if embed_data.get('author_name'):
            embed.set_author(
                name=embed_data.get('author_name'),
                icon_url=embed_data.get('author_icon')
            )
        
        if embed_data.get('thumbnail'):
            embed.set_thumbnail(url=embed_data.get('thumbnail'))
        
        if embed_data.get('image'):
            embed.set_image(url=embed_data.get('image'))
        
        for field in embed_data.get('fields', []):
            embed.add_field(
                name=field.get('name'),
                value=field.get('value'),
                inline=field.get('inline', False)
            )
        
        if embed_data.get('footer_text'):
            embed.set_footer(
                text=embed_data.get('footer_text'),
                icon_url=embed_data.get('footer_icon')
            )
        
        if embed_data.get('timestamp'):
            embed.timestamp = datetime.now()
        
        return embed
    except Exception as e:
        print(f"Error converting dict to embed: {e}")
        return None

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
# Stickies
# ============================================================================

@tasks.loop(minutes=10)
async def update_stickies():
    """Update sticky messages every 10 minutes"""
    sticky = load_sticky()
    
    for guild_id, channels in sticky.items():
        guild = bot.get_guild(int(guild_id))
        if not guild:
            continue
            
        for channel_id, sticky_data in channels.items():
            channel = guild.get_channel(int(channel_id))
            if not channel:
                continue
            
            if not sticky_data.get('enabled'):
                continue
            
            try:
                # Lösche alte Sticky Message
                if sticky_data.get('message_id'):
                    try:
                        old_msg = await channel.fetch_message(int(sticky_data['message_id']))
                        await old_msg.delete()
                    except:
                        pass
                
                # Sende neue Sticky Message
                embed = discord.Embed(
                    title=sticky_data.get('title', 'Sticky Message'),
                    description=sticky_data.get('content', ''),
                    color=COLOR_DEFAULT
                )
                embed.set_footer(text=f"{SERVER_TAG} Sticky Message")
                
                new_msg = await channel.send(embed=embed)
                sticky[guild_id][channel_id]['message_id'] = str(new_msg.id)
                
            except Exception as e:
                print(f"Error updating sticky: {e}")
    
    save_sticky(sticky)

@update_stickies.before_loop
async def before_update_stickies():
    await bot.wait_until_ready()
    print("Sticky message update task started!")


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
# IMAGE LINK COMMAND
# ============================================================================

@bot.tree.command(name="imagelink", description="Bild/GIF hochladen und Discord Link bekommen")
@app_commands.describe(image="Das Bild oder GIF das du hochladen möchtest")
async def imagelink(interaction: discord.Interaction, image: discord.Attachment = None):
    embed_role = interaction.guild.get_role(EMBED_EDITOR_ROLE_ID)
    if not embed_role or embed_role not in interaction.user.roles:
        error_embed = discord.Embed(
            title="Permission Denied",
            description=f"Du brauchst die <@&{EMBED_EDITOR_ROLE_ID}> Role!",
            color=COLOR_ERROR
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return
    
    if not image:
        error_embed = discord.Embed(
            title="Kein Bild gefunden",
            description="Bitte lade ein Bild oder GIF hoch!",
            color=COLOR_ERROR
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return
    
    valid_types = ['image/png', 'image/jpeg', 'image/gif', 'image/webp']
    if image.content_type not in valid_types:
        error_embed = discord.Embed(
            title="Ungültiger Dateityp",
            description=f"Erlaubte Typen: PNG, JPG, GIF, WebP",
            color=COLOR_ERROR
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return
    
    if image.size > 8 * 1024 * 1024:
        error_embed = discord.Embed(
            title="Datei zu groß",
            description="Max. Größe: 8 MB",
            color=COLOR_ERROR
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return
    
    discord_link = image.url
    
    success_embed = discord.Embed(
        title="Bild erfolgreich hochgeladen!",
        description="Dein Discord Image Link wurde erstellt:",
        color=COLOR_SUCCESS
    )
    success_embed.add_field(
        name=f"{BULLET} Link",
        value=f"`{discord_link}`",
        inline=False
    )
    success_embed.add_field(
        name=f"{BULLET} Größe",
        value=f"{round(image.size / 1024, 2)} KB",
        inline=True
    )
    success_embed.add_field(
        name=f"{BULLET} Dateityp",
        value=f"{image.content_type.split('/')[-1].upper()}",
        inline=True
    )
    success_embed.set_image(url=discord_link)
    success_embed.set_footer(text=f"{SERVER_TAG} Image Link System")
    
    await interaction.response.send_message(embed=success_embed)

# ============================================================================
# EMBED COMMANDS
# ============================================================================

@bot.tree.command(name="embed", description="Embed Management")
@app_commands.describe(
    action="create, list, delete, edit, send, preview",
    name="Embed name",
    title="Titel",
    description="Beschreibung",
    color="Hex Farbe",
    image="Image Link",
    thumbnail="Thumbnail Link"
)
async def embed_command(
    interaction: discord.Interaction,
    action: str,
    name: str = None,
    title: str = None,
    description: str = None,
    color: str = None,
    image: str = None,
    thumbnail: str = None
):
    embed_role = interaction.guild.get_role(EMBED_EDITOR_ROLE_ID)
    if not embed_role or embed_role not in interaction.user.roles:
        error_embed = discord.Embed(
            title="Permission Denied",
            description=f"Du brauchst die <@&{EMBED_EDITOR_ROLE_ID}> Role!",
            color=COLOR_ERROR
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return
    
    action = action.lower()
    embeds = load_embeds()
    guild_id = str(interaction.guild.id)
    
    if guild_id not in embeds:
        embeds[guild_id] = {}
    
    if action == "create":
        if not name:
            error = discord.Embed(title="Error", description="Name erforderlich!", color=COLOR_ERROR)
            await interaction.response.send_message(embed=error, ephemeral=True)
            return
        
        if name in embeds[guild_id]:
            error = discord.Embed(title="Error", description=f"Embed existiert bereits!", color=COLOR_ERROR)
            await interaction.response.send_message(embed=error, ephemeral=True)
            return
        
        embeds[guild_id][name] = {
            "title": "Neues Embed",
            "description": "Beschreibung",
            "color": "#191b70",
            "thumbnail": None,
            "image": None,
            "author_name": None,
            "author_icon": None,
            "footer_text": None,
            "footer_icon": None,
            "fields": [],
            "timestamp": False,
            "created_by": interaction.user.name,
            "created_at": datetime.now().isoformat()
        }
        
        save_embeds(embeds)
        success = discord.Embed(title="Embed Created", description=f"Embed `{name}` erstellt!", color=COLOR_SUCCESS)
        await interaction.response.send_message(embed=success, ephemeral=True)
    
    elif action == "list":
        if not embeds[guild_id]:
            info = discord.Embed(title="Keine Embeds", description="Keine Embeds vorhanden!", color=COLOR_DEFAULT)
            await interaction.response.send_message(embed=info, ephemeral=True)
            return
        
        list_embed = discord.Embed(title="Alle Embeds", color=COLOR_DEFAULT)
        for embed_name in embeds[guild_id].keys():
            list_embed.add_field(name=f"{BULLET} {embed_name}", value="✅", inline=False)
        
        await interaction.response.send_message(embed=list_embed, ephemeral=True)
    
    elif action == "delete":
        if not name or name not in embeds[guild_id]:
            error = discord.Embed(title="Error", description="Embed nicht gefunden!", color=COLOR_ERROR)
            await interaction.response.send_message(embed=error, ephemeral=True)
            return
        
        del embeds[guild_id][name]
        save_embeds(embeds)
        success = discord.Embed(title="Deleted", description=f"Embed `{name}` gelöscht!", color=COLOR_SUCCESS)
        await interaction.response.send_message(embed=success, ephemeral=True)
    
    elif action == "edit":
        if not name or name not in embeds[guild_id]:
            error = discord.Embed(title="Error", description="Embed nicht gefunden!", color=COLOR_ERROR)
            await interaction.response.send_message(embed=error, ephemeral=True)
            return
        
        if title:
            embeds[guild_id][name]["title"] = title
        if description:
            embeds[guild_id][name]["description"] = description
        if color:
            embeds[guild_id][name]["color"] = color if color.startswith('#') else '#' + color
        if image:
            embeds[guild_id][name]["image"] = image
        if thumbnail:
            embeds[guild_id][name]["thumbnail"] = thumbnail
        
        save_embeds(embeds)
        success = discord.Embed(title="Updated", description=f"Embed `{name}` aktualisiert!", color=COLOR_SUCCESS)
        await interaction.response.send_message(embed=success, ephemeral=True)
    
    elif action == "preview":
        if not name or name not in embeds[guild_id]:
            error = discord.Embed(title="Error", description="Embed nicht gefunden!", color=COLOR_ERROR)
            await interaction.response.send_message(embed=error, ephemeral=True)
            return
        
        preview = dict_to_embed(embeds[guild_id][name])
        if preview:
            await interaction.response.send_message(embed=preview, ephemeral=True)
    
    elif action == "send":
        if not name or name not in embeds[guild_id]:
            error = discord.Embed(title="Error", description="Embed nicht gefunden!", color=COLOR_ERROR)
            await interaction.response.send_message(embed=error, ephemeral=True)
            return
        
        try:
            embed_to_send = dict_to_embed(embeds[guild_id][name])
            if embed_to_send:
                await interaction.channel.send(embed=embed_to_send)
                success = discord.Embed(title="Sent", description="Embed versendet!", color=COLOR_SUCCESS)
                await interaction.response.send_message(embed=success, ephemeral=True)
        except Exception as e:
            error = discord.Embed(title="Error", description=f"Fehler: {str(e)}", color=COLOR_ERROR)
            await interaction.response.send_message(embed=error, ephemeral=True)

# ============================================================================
# STICKY MESSAGE COMMANDS
# ============================================================================

@bot.tree.command(name="sticky", description="Sticky Message Management")
@app_commands.describe(
    action="create, stop, start, delete, list",
    title="Titel der Sticky Message",
    content="Inhalt der Sticky Message"
)
async def sticky_command(
    interaction: discord.Interaction,
    action: str,
    title: str = None,
    content: str = None
):
    """Sticky Message System"""
    
    embed_role = interaction.guild.get_role(EMBED_EDITOR_ROLE_ID)
    if not embed_role or embed_role not in interaction.user.roles:
        error_embed = discord.Embed(
            title="Permission Denied",
            description=f"Du brauchst die <@&{EMBED_EDITOR_ROLE_ID}> Role!",
            color=COLOR_ERROR
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return
    
    action = action.lower()
    sticky = load_sticky()
    guild_id = str(interaction.guild.id)
    channel_id = str(interaction.channel.id)
    
    if guild_id not in sticky:
        sticky[guild_id] = {}
    
    if action == "create":
        if not title or not content:
            error = discord.Embed(
                title="Error",
                description="Title und Content erforderlich!",
                color=COLOR_ERROR
            )
            await interaction.response.send_message(embed=error, ephemeral=True)
            return
        
        sticky[guild_id][channel_id] = {
            "title": title,
            "content": content,
            "enabled": True,
            "message_id": None,
            "created_by": interaction.user.name,
            "created_at": datetime.now().isoformat()
        }
        
        save_sticky(sticky)
        
        success = discord.Embed(
            title="Sticky Created",
            description=f"Sticky Message in {interaction.channel.mention} erstellt!",
            color=COLOR_SUCCESS
        )
        success.add_field(name=f"{BULLET} Title", value=title, inline=False)
        success.add_field(name=f"{BULLET} Content", value=content, inline=False)
        await interaction.response.send_message(embed=success, ephemeral=True)
    
    elif action == "stop":
        if channel_id not in sticky[guild_id]:
            error = discord.Embed(
                title="Error",
                description="Keine Sticky Message in diesem Channel!",
                color=COLOR_ERROR
            )
            await interaction.response.send_message(embed=error, ephemeral=True)
            return
        
        sticky[guild_id][channel_id]["enabled"] = False
        save_sticky(sticky)
        
        success = discord.Embed(
            title="Sticky Stopped",
            description="Sticky Message gestoppt!",
            color=COLOR_SUCCESS
        )
        await interaction.response.send_message(embed=success, ephemeral=True)
    
    elif action == "start":
        if channel_id not in sticky[guild_id]:
            error = discord.Embed(
                title="Error",
                description="Keine Sticky Message in diesem Channel!",
                color=COLOR_ERROR
            )
            await interaction.response.send_message(embed=error, ephemeral=True)
            return
        
        sticky[guild_id][channel_id]["enabled"] = True
        save_sticky(sticky)
        
        success = discord.Embed(
            title="Sticky Started",
            description="Sticky Message gestartet!",
            color=COLOR_SUCCESS
        )
        await interaction.response.send_message(embed=success, ephemeral=True)
    
    elif action == "delete":
        if channel_id not in sticky[guild_id]:
            error = discord.Embed(
                title="Error",
                description="Keine Sticky Message in diesem Channel!",
                color=COLOR_ERROR
            )
            await interaction.response.send_message(embed=error, ephemeral=True)
            return
        
        del sticky[guild_id][channel_id]
        save_sticky(sticky)
        
        success = discord.Embed(
            title="Sticky Deleted",
            description="Sticky Message gelöscht!",
            color=COLOR_SUCCESS
        )
        await interaction.response.send_message(embed=success, ephemeral=True)
    
    elif action == "list":
        if not sticky[guild_id]:
            info = discord.Embed(
                title="Keine Stickies",
                description="Keine Sticky Messages vorhanden!",
                color=COLOR_DEFAULT
            )
            await interaction.response.send_message(embed=info, ephemeral=True)
            return
        
        list_embed = discord.Embed(
            title="Alle Sticky Messages",
            color=COLOR_DEFAULT
        )
        
        for ch_id, data in sticky[guild_id].items():
            channel = interaction.guild.get_channel(int(ch_id))
            status = "🟢 Aktiv" if data.get("enabled") else "🔴 Gestoppt"
            list_embed.add_field(
                name=f"{BULLET} {channel.mention if channel else 'Unbekannt'}",
                value=f"{status}\nTitle: {data.get('title')}",
                inline=False
            )
        
        await interaction.response.send_message(embed=list_embed, ephemeral=True)

# ============================================================================
# TICKET SYSTEM COMMANDS
# ============================================================================

@bot.tree.command(name="ticket", description="Ticket System")
@app_commands.describe(
    action="create, close, delete, list, add, remove",
    reason="Grund für das Ticket (nur für create)"
)
async def ticket_command(
    interaction: discord.Interaction,
    action: str,
    reason: str = None
):
    """Ticket System"""
    
    action = action.lower()
    tickets = load_tickets()
    guild_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)
    
    if guild_id not in tickets:
        tickets[guild_id] = {}
    
    if action == "create":
        if not reason:
            reason = "Kein Grund angegeben"
        
        # Erstelle Ticket Channel
        ticket_name = f"ticket-{len(tickets[guild_id]) + 1}"
        
        try:
            # Finde oder erstelle Category
            category = discord.utils.find(
                lambda c: c.name == "Tickets" and isinstance(c, discord.CategoryChannel),
                interaction.guild.categories
            )
            
            if not category:
                category = await interaction.guild.create_category("Tickets")
            
            # Erstelle Channel
            ticket_channel = await category.create_text_channel(
                ticket_name,
                topic=f"Ticket von {interaction.user.name} - {reason}"
            )
            
            # Speichere Ticket Info
            tickets[guild_id][str(ticket_channel.id)] = {
                "user_id": user_id,
                "user_name": interaction.user.name,
                "reason": reason,
                "created_at": datetime.now().isoformat(),
                "status": "open"
            }
            
            save_tickets(tickets)
            
            # Sende Willkommens-Nachricht
            embed = discord.Embed(
                title=f"Ticket #{len(tickets[guild_id])}",
                description=f"Willkommen {interaction.user.mention}!",
                color=COLOR_DEFAULT
            )
            embed.add_field(
                name=f"{BULLET} Grund",
                value=reason,
                inline=False
            )
            embed.add_field(
                name=f"{BULLET} Status",
                value="🟢 Offen",
                inline=False
            )
            embed.set_footer(text=f"{SERVER_TAG} Ticket System")
            
            await ticket_channel.send(embed=embed)
            
            success = discord.Embed(
                title="Ticket Created",
                description=f"Ticket erstellt: {ticket_channel.mention}",
                color=COLOR_SUCCESS
            )
            await interaction.response.send_message(embed=success, ephemeral=True)
        
        except Exception as e:
            error = discord.Embed(
                title="Error",
                description=f"Fehler beim Erstellen des Tickets: {str(e)}",
                color=COLOR_ERROR
            )
            await interaction.response.send_message(embed=error, ephemeral=True)
    
    elif action == "close":
        channel_id = str(interaction.channel.id)
        
        if channel_id not in tickets[guild_id]:
            error = discord.Embed(
                title="Error",
                description="Das ist kein Ticket Channel!",
                color=COLOR_ERROR
            )
            await interaction.response.send_message(embed=error, ephemeral=True)
            return
        
        tickets[guild_id][channel_id]["status"] = "closed"
        save_tickets(tickets)
        
        closed_embed = discord.Embed(
            title="Ticket Closed",
            description="Dieses Ticket wurde geschlossen!",
            color=COLOR_SUCCESS
        )
        await interaction.channel.send(embed=closed_embed)
        
        success = discord.Embed(
            title="Closed",
            description="Ticket geschlossen!",
            color=COLOR_SUCCESS
        )
        await interaction.response.send_message(embed=success, ephemeral=True)
    
    elif action == "delete":
        channel_id = str(interaction.channel.id)
        
        if channel_id not in tickets[guild_id]:
            error = discord.Embed(
                title="Error",
                description="Das ist kein Ticket Channel!",
                color=COLOR_ERROR
            )
            await interaction.response.send_message(embed=error, ephemeral=True)
            return
        
        del tickets[guild_id][channel_id]
        save_tickets(tickets)
        
        await interaction.channel.delete()
    
    elif action == "list":
        if not tickets[guild_id]:
            info = discord.Embed(
                title="Keine Tickets",
                description="Keine Tickets vorhanden!",
                color=COLOR_DEFAULT
            )
            await interaction.response.send_message(embed=info, ephemeral=True)
            return
        
        list_embed = discord.Embed(
            title="Alle Tickets",
            color=COLOR_DEFAULT
        )
        
        for ch_id, data in tickets[guild_id].items():
            status = "🟢 Offen" if data.get("status") == "open" else "🔴 Geschlossen"
            list_embed.add_field(
                name=f"{BULLET} Ticket von {data.get('user_name')}",
                value=f"{status}\nGrund: {data.get('reason')}",
                inline=False
            )
        
        await interaction.response.send_message(embed=list_embed, ephemeral=True)

# ============================================================================
# LEADERBOARD & STAT COMMANDS
# ============================================================================

@bot.tree.command(name="leaderboard", description="Message Leaderboard")
async def leaderboard(interaction: discord.Interaction):
    stats = load_stats()

    if not stats:
        embed = discord.Embed(title="Leaderboard", description="Keine Daten!", color=COLOR_DEFAULT)
        await interaction.response.send_message(embed=embed)
        return

    sorted_stats = sorted(stats.items(), key=lambda x: x[1]['messages'], reverse=True)[:10]

    embed = discord.Embed(
        title=f"────────── {SERVER_TAG} Leaderboard ──────────",
        color=COLOR_DEFAULT
    )

    for idx, (user_id, data) in enumerate(sorted_stats, 1):
        embed.add_field(
            name=f"{BULLET} #{idx} - {data['name']}",
            value=f"Messages: {data['messages']}",
            inline=False
        )

    await interaction.response.send_message(embed=embed)


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
