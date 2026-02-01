import os
import logging
import asyncio
from typing import Optional, Literal, Dict, List
from datetime import datetime, timedelta
import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv
import json
from collections import defaultdict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('discord_bot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

class ModernBot(commands.Bot):
    """Modern Discord bot with slash commands and cogs."""
    
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.members = True
        intents.presences = True
        intents.message_content = True
        intents.moderation = True  # For bans/kicks
        intents.guilds = True
        intents.voice_states = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None  # We'll create a custom one
        )
        
        # Tracking data
        self.log_channels: Dict[int, Dict[str, int]] = {}  # guild_id: {event_type: channel_id}
        self.user_activity: Dict[int, Dict] = defaultdict(lambda: {
            'messages': 0,
            'voice_time': 0,
            'joins': 0,
            'leaves': 0
        })
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from file."""
        try:
            with open('config.json', 'r') as f:
                data = json.load(f)
                self.log_channels = {int(k): v for k, v in data.get('log_channels', {}).items()}
        except FileNotFoundError:
            self.log_channels = {}
    
    def save_config(self) -> None:
        """Save configuration to file."""
        with open('config.json', 'w') as f:
            json.dump({'log_channels': self.log_channels}, f, indent=2)
    
    async def setup_hook(self) -> None:
        """Called when the bot is starting up."""
        # Load cogs
        await self.add_cog(UserInfoCog(self))
        await self.add_cog(UtilityCog(self))
        await self.add_cog(AdvancedCog(self))
        await self.add_cog(TrackingCog(self))
        await self.add_cog(AutoLoggerCog(self))
        await self.add_cog(AutomationCog(self))
        await self.add_cog(ModernInteractionsCog(self))
        await self.add_cog(SuperAdvancedCog(self))
        await self.add_cog(ChannelManagementCog(self))
        await self.add_cog(InsaneFeaturesCog(self))
        
        # Sync commands globally (or to specific guild for testing)
        logger.info("Syncing command tree...")
        await self.tree.sync()
        logger.info("Command tree synced!")
    
    async def on_ready(self) -> None:
        """Called when bot is ready."""
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        logger.info(f'Connected to {len(self.guilds)} guilds')
        logger.info('------')
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="/help for commands"
            )
        )

class UserInfoView(discord.ui.View):
    """Interactive view with buttons for user info."""
    
    def __init__(self, member: discord.Member) -> None:
        super().__init__(timeout=180)
        self.member = member
    
    @discord.ui.button(label="Show Permissions", style=discord.ButtonStyle.primary, emoji="🔐")
    async def show_permissions(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Show detailed permissions."""
        permissions = [perm[0].replace('_', ' ').title() for perm in self.member.guild_permissions if perm[1]]
        
        embed = discord.Embed(
            title=f"Permissions for {self.member.display_name}",
            description='\n'.join(f"✅ {perm}" for perm in permissions[:20]),
            color=discord.Color.green()
        )
        
        if len(permissions) > 20:
            embed.set_footer(text=f"And {len(permissions) - 20} more permissions...")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="Avatar", style=discord.ButtonStyle.secondary, emoji="🖼️")
    async def show_avatar(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Show full-size avatar."""
        avatar_url = self.member.display_avatar.url
        embed = discord.Embed(
            title=f"{self.member.display_name}'s Avatar",
            color=discord.Color.blurple()
        )
        embed.set_image(url=avatar_url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class UserInfoCog(commands.Cog):
    """User information commands."""
    
    def __init__(self, bot: ModernBot) -> None:
        self.bot = bot
    
    @app_commands.command(name="userinfo", description="Get MAXIMUM detailed information about a user")
    @app_commands.describe(member="The member to get info about (defaults to you)")
    async def userinfo_slash(self, interaction: discord.Interaction, member: Optional[discord.Member] = None) -> None:
        """Modern slash command for user info - MAXIMUM INFORMATION."""
        await interaction.response.defer()  # This might take a moment
        
        member = member or interaction.user
        
        # Fetch full user data (includes banner, accent color, etc.)
        try:
            user = await self.bot.fetch_user(member.id)
        except:
            user = member
        
        # Create main embed with maximum info
        roles = [role.mention for role in member.roles if role.name != '@everyone']
        
        # Color priority: accent color > role color > default
        color = user.accent_color or member.color if member.color != discord.Color.default() else discord.Color.blue()
        
        embed = discord.Embed(
            title="📊 Complete User Analysis",
            description=f"**Full profile data for {member.mention}**",
            color=color,
            timestamp=discord.utils.utcnow()
        )
        
        # Banner if available
        if user.banner:
            embed.set_image(url=user.banner.url)
        
        # Set thumbnail to avatar
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # === IDENTITY SECTION ===
        identity_info = []
        identity_info.append(f"**Display Name:** {member.display_name}")
        identity_info.append(f"**Username:** {member.name}")
        if member.nick:
            identity_info.append(f"**Nickname:** {member.nick}")
        identity_info.append(f"**User ID:** `{member.id}`")
        if member.discriminator != "0":
            identity_info.append(f"**Discriminator:** #{member.discriminator}")
        identity_info.append(f"**Mention:** {member.mention}")
        embed.add_field(name="🪪 Identity", value='\n'.join(identity_info), inline=False)
        
        # === USER TYPE & FLAGS ===
        type_info = []
        type_info.append(f"**Bot Account:** {'✅ Yes' if member.bot else '❌ No'}")
        type_info.append(f"**System Account:** {'✅ Yes' if member.system else '❌ No'}")
        
        # User badges/flags
        flags = []
        if user.public_flags:
            flag_mapping = {
                'staff': '🛡️ Discord Staff',
                'partner': '🤝 Partnered Server Owner',
                'hypesquad': '⚡ HypeSquad Events',
                'bug_hunter': '🐛 Bug Hunter',
                'hypesquad_bravery': '🟣 HypeSquad Bravery',
                'hypesquad_brilliance': '🔴 HypeSquad Brilliance',
                'hypesquad_balance': '🟢 HypeSquad Balance',
                'early_supporter': '⭐ Early Supporter',
                'bug_hunter_level_2': '🐛 Bug Hunter Level 2',
                'verified_bot_developer': '✅ Early Verified Bot Developer',
                'verified_bot': '✅ Verified Bot',
                'discord_certified_moderator': '🔨 Discord Certified Moderator',
                'bot_http_interactions': '🔗 HTTP Interactions Bot',
                'active_developer': '⚙️ Active Developer'
            }
            
            for flag_name, display_name in flag_mapping.items():
                if getattr(user.public_flags, flag_name, False):
                    flags.append(display_name)
        
        if flags:
            type_info.append(f"**Badges:** {', '.join(flags)}")
        else:
            type_info.append("**Badges:** None")
        
        embed.add_field(name="🏅 Type & Badges", value='\n'.join(type_info), inline=True)
        
        # === STATUS & PRESENCE ===
        status_info = []
        status_emojis = {
            'online': '🟢 Online',
            'idle': '🟡 Idle',
            'dnd': '🔴 Do Not Disturb',
            'offline': '⚫ Offline/Invisible'
        }
        status_info.append(f"**Status:** {status_emojis.get(str(member.status), str(member.status))}")
        
        # Platform-specific status
        if member.desktop_status != discord.Status.offline:
            status_info.append(f"**Desktop:** {status_emojis.get(str(member.desktop_status), '🖥️')}")
        if member.mobile_status != discord.Status.offline:
            status_info.append(f"**Mobile:** {status_emojis.get(str(member.mobile_status), '📱')}")
        if member.web_status != discord.Status.offline:
            status_info.append(f"**Web:** {status_emojis.get(str(member.web_status), '🌐')}")
        
        # Activities
        if member.activities:
            for activity in member.activities:
                if isinstance(activity, discord.Spotify):
                    status_info.append(f"**🎵 Spotify:** {activity.title} by {activity.artist}")
                elif isinstance(activity, discord.Game):
                    status_info.append(f"**🎮 Playing:** {activity.name}")
                elif isinstance(activity, discord.Streaming):
                    status_info.append(f"**📹 Streaming:** {activity.name}")
                elif isinstance(activity, discord.CustomActivity):
                    emoji = f"{activity.emoji} " if activity.emoji else ""
                    status_info.append(f"**💭 Custom:** {emoji}{activity.name or 'No status'}")
                else:
                    status_info.append(f"**Activity:** {activity.name}")
        else:
            status_info.append("**Activity:** None")
        
        embed.add_field(name="📡 Status & Presence", value='\n'.join(status_info), inline=True)
        
        # === VOICE STATE ===
        if member.voice:
            voice_info = []
            voice_info.append(f"**Channel:** {member.voice.channel.mention}")
            voice_info.append(f"**Muted:** {'✅' if member.voice.mute or member.voice.self_mute else '❌'}")
            voice_info.append(f"**Deafened:** {'✅' if member.voice.deaf or member.voice.self_deaf else '❌'}")
            voice_info.append(f"**Streaming:** {'✅' if member.voice.self_stream else '❌'}")
            voice_info.append(f"**Video:** {'✅' if member.voice.self_video else '❌'}")
            if member.voice.requested_to_speak_at:
                voice_info.append(f"**Stage Request:** <t:{int(member.voice.requested_to_speak_at.timestamp())}:R>")
            embed.add_field(name="🎙️ Voice State", value='\n'.join(voice_info), inline=False)
        
        # === ROLES ===
        embed.add_field(
            name=f"🎭 Roles ({len(roles)})",
            value=' '.join(roles[:15]) if roles else 'No roles',
            inline=False
        )
        if len(roles) > 15:
            embed.add_field(name="➕", value=f"... and {len(roles) - 15} more roles", inline=False)
        
        # === PERMISSIONS ===
        key_perms = []
        if member.guild_permissions.administrator:
            key_perms.append("👑 Administrator")
        if member.guild_permissions.manage_guild:
            key_perms.append("⚙️ Manage Server")
        if member.guild_permissions.manage_roles:
            key_perms.append("🎭 Manage Roles")
        if member.guild_permissions.manage_channels:
            key_perms.append("📝 Manage Channels")
        if member.guild_permissions.kick_members:
            key_perms.append("🥾 Kick Members")
        if member.guild_permissions.ban_members:
            key_perms.append("🔨 Ban Members")
        if member.guild_permissions.manage_messages:
            key_perms.append("🗑️ Manage Messages")
        if member.guild_permissions.mention_everyone:
            key_perms.append("📢 Mention Everyone")
        if member.guild_permissions.manage_webhooks:
            key_perms.append("🪝 Manage Webhooks")
        
        if key_perms:
            embed.add_field(name="🔐 Key Permissions", value='\n'.join(key_perms), inline=True)
        
        # === SERVER MEMBER INFO ===
        server_info = []
        server_info.append(f"**Joined Server:** <t:{int(member.joined_at.timestamp())}:F>")
        server_info.append(f"**Join Position:** #{sorted(interaction.guild.members, key=lambda m: m.joined_at).index(member) + 1}")
        if member.premium_since:
            server_info.append(f"**Server Booster:** ✅ Since <t:{int(member.premium_since.timestamp())}:R>")
        else:
            server_info.append("**Server Booster:** ❌")
        
        if member.timed_out_until:
            server_info.append(f"**⏰ Timed Out Until:** <t:{int(member.timed_out_until.timestamp())}:F>")
        
        server_info.append(f"**Pending Verification:** {'✅ Yes' if member.pending else '❌ No'}")
        embed.add_field(name="🏰 Server Info", value='\n'.join(server_info), inline=True)
        
        # === ACCOUNT INFO ===
        account_info = []
        account_info.append(f"**Created:** <t:{int(member.created_at.timestamp())}:F>")
        account_age_days = (discord.utils.utcnow() - member.created_at).days
        account_info.append(f"**Account Age:** {account_age_days} days ({account_age_days // 365} years)")
        if user.accent_color:
            account_info.append(f"**Accent Color:** `{str(user.accent_color)}`")
        account_info.append(f"**Avatar URL:** [Click here]({member.display_avatar.url})")
        if user.banner:
            account_info.append(f"**Banner URL:** [Click here]({user.banner.url})")
        
        embed.add_field(name="📅 Account Info", value='\n'.join(account_info), inline=True)
        
        # === AVATAR VARIATIONS ===
        avatar_links = []
        avatar_links.append(f"[Default]({member.display_avatar.replace(format='png', size=1024).url})")
        avatar_links.append(f"[WebP]({member.display_avatar.replace(format='webp', size=1024).url})")
        avatar_links.append(f"[JPG]({member.display_avatar.replace(format='jpg', size=1024).url})")
        if member.display_avatar.is_animated():
            avatar_links.append(f"[GIF]({member.display_avatar.replace(format='gif', size=1024).url})")
        embed.add_field(name="🖼️ Avatar Formats", value=' • '.join(avatar_links), inline=False)
        
        embed.set_footer(
            text=f"Requested by {interaction.user} • All available data extracted",
            icon_url=interaction.user.display_avatar.url
        )
        
        # Create interactive view with more options
        view = UserInfoView(member)
        
        await interaction.followup.send(embed=embed, view=view)
    
    @commands.hybrid_command(name="whois", description="Quick user lookup")
    async def whois(self, ctx: commands.Context, member: Optional[discord.Member] = None) -> None:
        """Hybrid command - works as both ! and / command."""
        member = member or ctx.author
        
        embed = discord.Embed(
            description=f"**{member.mention}** - {member.display_name}\n"
                       f"ID: `{member.id}`\n"
                       f"Created: <t:{int(member.created_at.timestamp())}:R>\n"
                       f"Joined: <t:{int(member.joined_at.timestamp())}:R>",
            color=member.color
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)

class UtilityCog(commands.Cog):
    """Utility commands."""
    
    def __init__(self, bot: ModernBot) -> None:
        self.bot = bot
        self.ctx_menu = app_commands.ContextMenu(
            name='Get User Info',
            callback=self.context_menu_userinfo,
        )
        self.bot.tree.add_command(self.ctx_menu)
    
    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(self.ctx_menu.name, type=self.ctx_menu.type)
    
    async def context_menu_userinfo(self, interaction: discord.Interaction, member: discord.Member) -> None:
        """Right-click context menu for user info."""
        embed = discord.Embed(
            description=f"**{member.mention}**\n"
                       f"ID: `{member.id}`\n"
                       f"Status: {member.status}\n"
                       f"Joined: <t:{int(member.joined_at.timestamp())}:R>",
            color=member.color
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="help", description="Show bot commands and features")
    async def help_command(self, interaction: discord.Interaction) -> None:
        """Modern help command."""
        embed = discord.Embed(
            title="🤖 Bot Commands",
            description="Here are all available commands:",
            color=discord.Color.blurple()
        )
        
        embed.add_field(
            name="📋 User Commands",
            value="</userinfo:0> - Detailed user information with interactive buttons\n"
                  "</whois:0> - Quick user lookup\n"
                  "Right-click user → Apps → Get User Info",
            inline=False
        )
        
        embed.add_field(
            name="🛠️ Utility",
            value="</help:0> - Show this message\n"
                  "</ping:0> - Check bot latency\n"
                  "</serverinfo:0> - Server information",
            inline=False
        )
        
        embed.add_field(
            name="🚀 Advanced",
            value="</snipe:0> - See deleted messages\n"
                  "</editsnipe:0> - See edited messages\n"
                  "</poll:0> - Create polls\n"
                  "</avatar:0> - Get avatars in all formats\n"
                  "</banner:0> - Get user/server banners\n"
                  "</serveranalytics:0> - Detailed server stats\n"
                  "</membercount:0> - Member count graph\n"
                  "</rolemenu:0> - Create role selection menu\n"
                  "</afk:0> - Set AFK status",
            inline=False
        )
        
        embed.add_field(
            name="🔍 Tracking & Logging",
            value="</setlog:0> - Set up auto-logging channels\n"
                  "</tracking:0> - View user tracking data\n"
                  "</membertrack:0> - Deep member profile\n"
                  "</serverstats:0> - Live server statistics\n"
                  "</activity:0> - Server activity heatmap\n"
                  "</auditlog:0> - View recent audit logs",
            inline=False
        )
        
        embed.add_field(
            name="🤖 Automations",
            value="</autowelcome:0> - Setup welcome messages\n"
                  "</autorole:0> - Auto-assign roles on join\n"
                  "</autoresponse:0> - Auto-reply to keywords\n"
                  "</automod:0> - Configure auto-moderation\n"
                  "</ticket:0> - Create ticket system",
            inline=False
        )
        
        embed.add_field(
            name="✨ Modern Interactions",
            value="</embed:0> - Create custom embeds\n"
                  "</dropdown:0> - Create dropdown menus\n"
                  "</giveaway:0> - Start interactive giveaway\n"
                  "</verify:0> - Setup verification system",
            inline=False
        )
        
        embed.add_field(
            name="🚀 Super Advanced",
            value="</starboard:0> - Popular messages board\n"
                  "</suggest:0> - Suggestion system with voting\n"
                  "</remind:0> - Set personal reminders\n"
                  "</transcript:0> - Export chat history\n"
                  "</schedule:0> - Schedule messages\n"
                  "</backup:0> - Backup server settings\n"
                  "</massaction:0> - Mass ban/role/kick\n"
                  "</customcmd:0> - Create custom commands",
            inline=False
        )
        
        embed.add_field(
            name="📺 Channel Management",
            value="</jointocreate:0> - Auto voice channels\n"
                  "</tempvoice:0> - Temporary voice channel\n"
                  "</clonechannel:0> - Clone any channel\n"
                  "</channeltemplate:0> - Save/load channel templates\n"
                  "</autocategory:0> - Auto-create categories\n"
                  "</channelstats:0> - Live stats channels\n"
                  "</lockdown:0> - Lock/unlock channels\n"
                  "</nuke:0> - Clone & delete channel",
            inline=False
        )
        
        embed.set_footer(text="Tip: You can also use ! prefix for some commands")
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="ping", description="Check bot latency")
    async def ping(self, interaction: discord.Interaction) -> None:
        """Check bot latency."""
        latency = round(self.bot.latency * 1000)
        
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Latency: **{latency}ms**",
            color=discord.Color.green() if latency < 100 else discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="serverinfo", description="Get server information")
    async def serverinfo(self, interaction: discord.Interaction) -> None:
        """Get server information."""
        guild = interaction.guild
        
        embed = discord.Embed(
            title=guild.name,
            description=guild.description or "No description",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.add_field(name="👑 Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="🆔 Server ID", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="📅 Created", value=f"<t:{int(guild.created_at.timestamp())}:R>", inline=True)
        
        embed.add_field(name="👥 Members", value=guild.member_count, inline=True)
        embed.add_field(name="💬 Channels", value=len(guild.channels), inline=True)
        embed.add_field(name="😀 Emojis", value=len(guild.emojis), inline=True)
        
        embed.add_field(name="🎭 Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="🚀 Boost Level", value=guild.premium_tier, inline=True)
        embed.add_field(name="💎 Boosts", value=guild.premium_subscription_count or 0, inline=True)
        
        await interaction.response.send_message(embed=embed)

class AdvancedCog(commands.Cog):
    """Advanced crazy commands."""
    
    def __init__(self, bot: ModernBot) -> None:
        self.bot = bot
        self.snipe_cache = {}  # Store deleted messages
        self.edit_cache = {}   # Store edited messages
    
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        """Cache deleted messages for snipe command."""
        if message.author.bot:
            return
        self.snipe_cache[message.channel.id] = {
            'content': message.content,
            'author': message.author,
            'time': discord.utils.utcnow(),
            'attachments': [att.url for att in message.attachments]
        }
    
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        """Cache edited messages for editsnipe command."""
        if before.author.bot or before.content == after.content:
            return
        self.edit_cache[before.channel.id] = {
            'before': before.content,
            'after': after.content,
            'author': before.author,
            'time': discord.utils.utcnow()
        }
    
    @app_commands.command(name="snipe", description="See the most recently deleted message in this channel")
    async def snipe(self, interaction: discord.Interaction) -> None:
        """Show the last deleted message."""
        data = self.snipe_cache.get(interaction.channel_id)
        
        if not data:
            await interaction.response.send_message("❌ No recently deleted messages!", ephemeral=True)
            return
        
        embed = discord.Embed(
            description=data['content'] or "*No text content*",
            color=discord.Color.red(),
            timestamp=data['time']
        )
        embed.set_author(name=f"{data['author']}", icon_url=data['author'].display_avatar.url)
        embed.set_footer(text="Deleted")
        
        if data['attachments']:
            embed.add_field(name="📎 Attachments", value='\n'.join(data['attachments'][:3]), inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="editsnipe", description="See the most recently edited message in this channel")
    async def editsnipe(self, interaction: discord.Interaction) -> None:
        """Show the last edited message."""
        data = self.edit_cache.get(interaction.channel_id)
        
        if not data:
            await interaction.response.send_message("❌ No recently edited messages!", ephemeral=True)
            return
        
        embed = discord.Embed(color=discord.Color.orange(), timestamp=data['time'])
        embed.set_author(name=f"{data['author']}", icon_url=data['author'].display_avatar.url)
        embed.add_field(name="📝 Before", value=data['before'] or "*No text*", inline=False)
        embed.add_field(name="✏️ After", value=data['after'] or "*No text*", inline=False)
        embed.set_footer(text="Edited")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="poll", description="Create an advanced poll with reactions")
    @app_commands.describe(
        question="The poll question",
        option1="First option",
        option2="Second option",
        option3="Third option (optional)",
        option4="Fourth option (optional)",
        option5="Fifth option (optional)"
    )
    async def poll(
        self, 
        interaction: discord.Interaction,
        question: str,
        option1: str,
        option2: str,
        option3: Optional[str] = None,
        option4: Optional[str] = None,
        option5: Optional[str] = None
    ) -> None:
        """Create an interactive poll."""
        options = [option1, option2]
        if option3: options.append(option3)
        if option4: options.append(option4)
        if option5: options.append(option5)
        
        emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']
        
        embed = discord.Embed(
            title="📊 " + question,
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        description = []
        for i, option in enumerate(options):
            description.append(f"{emojis[i]} {option}")
        
        embed.description = '\n\n'.join(description)
        embed.set_footer(text=f"Poll by {interaction.user}", icon_url=interaction.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        
        for i in range(len(options)):
            await message.add_reaction(emojis[i])
    
    @app_commands.command(name="rolemenu", description="Create a self-role menu with buttons")
    @app_commands.describe(title="Title of the role menu")
    async def rolemenu(self, interaction: discord.Interaction, title: str) -> None:
        """Create an interactive role selection menu."""
        
        class RoleButton(discord.ui.Button):
            def __init__(self, role: discord.Role):
                super().__init__(
                    label=role.name,
                    style=discord.ButtonStyle.primary,
                    custom_id=f"role_{role.id}"
                )
                self.role = role
            
            async def callback(self, interaction: discord.Interaction):
                member = interaction.user
                if self.role in member.roles:
                    await member.remove_roles(self.role)
                    await interaction.response.send_message(f"❌ Removed {self.role.mention}", ephemeral=True)
                else:
                    await member.add_roles(self.role)
                    await interaction.response.send_message(f"✅ Added {self.role.mention}", ephemeral=True)
        
        class RoleView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)
        
        embed = discord.Embed(
            title=f"🎭 {title}",
            description="Click buttons below to add/remove roles!",
            color=discord.Color.blurple()
        )
        
        view = RoleView()
        # Add some example roles (you'd want to make this configurable)
        for role in interaction.guild.roles[:5]:
            if role.name != "@everyone" and not role.managed:
                view.add_item(RoleButton(role))
                embed.add_field(name=role.name, value="Click to toggle", inline=True)
        
        await interaction.response.send_message(embed=embed, view=view)
    
    @app_commands.command(name="avatar", description="Get user avatar in all sizes and formats")
    @app_commands.describe(member="The member whose avatar to get")
    async def avatar(self, interaction: discord.Interaction, member: Optional[discord.Member] = None) -> None:
        """Get avatar in multiple formats and sizes."""
        member = member or interaction.user
        
        embed = discord.Embed(
            title=f"🖼️ {member.display_name}'s Avatar",
            color=member.color
        )
        embed.set_image(url=member.display_avatar.url)
        
        # Add all format links
        formats = []
        for size in [128, 256, 512, 1024, 2048]:
            links = []
            links.append(f"[PNG]({member.display_avatar.replace(format='png', size=size).url})")
            links.append(f"[WebP]({member.display_avatar.replace(format='webp', size=size).url})")
            links.append(f"[JPG]({member.display_avatar.replace(format='jpg', size=size).url})")
            if member.display_avatar.is_animated():
                links.append(f"[GIF]({member.display_avatar.replace(format='gif', size=size).url})")
            formats.append(f"**{size}px:** {' • '.join(links)}")
        
        embed.description = '\n'.join(formats)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="banner", description="Get user or server banner")
    @app_commands.describe(member="The member whose banner to get (leave empty for server banner)")
    async def banner(self, interaction: discord.Interaction, member: Optional[discord.Member] = None) -> None:
        """Get user or server banner."""
        if member:
            # User banner
            user = await self.bot.fetch_user(member.id)
            if user.banner:
                embed = discord.Embed(
                    title=f"🎨 {member.display_name}'s Banner",
                    color=member.color
                )
                embed.set_image(url=user.banner.url)
                embed.description = f"[Download Banner]({user.banner.url})"
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(f"❌ {member.mention} doesn't have a banner!", ephemeral=True)
        else:
            # Server banner
            guild = interaction.guild
            if guild.banner:
                embed = discord.Embed(
                    title=f"🎨 {guild.name}'s Banner",
                    color=discord.Color.blurple()
                )
                embed.set_image(url=guild.banner.url)
                embed.description = f"[Download Banner]({guild.banner.url})"
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("❌ This server doesn't have a banner!", ephemeral=True)
    
    @app_commands.command(name="serveranalytics", description="Get detailed server analytics and insights")
    async def serveranalytics(self, interaction: discord.Interaction) -> None:
        """Advanced server analytics."""
        await interaction.response.defer()
        
        guild = interaction.guild
        
        # Calculate statistics
        total_members = guild.member_count
        humans = len([m for m in guild.members if not m.bot])
        bots = total_members - humans
        online = len([m for m in guild.members if m.status != discord.Status.offline])
        
        # Role statistics
        roles_with_members = [(role, len(role.members)) for role in guild.roles if len(role.members) > 0]
        roles_with_members.sort(key=lambda x: x[1], reverse=True)
        
        # Channel statistics
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        # Emoji statistics
        static_emojis = len([e for e in guild.emojis if not e.animated])
        animated_emojis = len([e for e in guild.emojis if e.animated])
        
        embed = discord.Embed(
            title=f"📊 {guild.name} Analytics",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Member breakdown
        member_info = []
        member_info.append(f"**Total Members:** {total_members}")
        member_info.append(f"**👤 Humans:** {humans} ({humans/total_members*100:.1f}%)")
        member_info.append(f"**🤖 Bots:** {bots} ({bots/total_members*100:.1f}%)")
        member_info.append(f"**🟢 Online:** {online} ({online/total_members*100:.1f}%)")
        embed.add_field(name="👥 Members", value='\n'.join(member_info), inline=True)
        
        # Channel breakdown
        channel_info = []
        channel_info.append(f"**💬 Text:** {text_channels}")
        channel_info.append(f"**🎙️ Voice:** {voice_channels}")
        channel_info.append(f"**📁 Categories:** {categories}")
        channel_info.append(f"**Total:** {len(guild.channels)}")
        embed.add_field(name="📺 Channels", value='\n'.join(channel_info), inline=True)
        
        # Server features
        features = []
        if 'COMMUNITY' in guild.features:
            features.append("✅ Community")
        if 'VERIFIED' in guild.features:
            features.append("✅ Verified")
        if 'PARTNERED' in guild.features:
            features.append("✅ Partnered")
        if 'DISCOVERABLE' in guild.features:
            features.append("✅ Discoverable")
        if 'VANITY_URL' in guild.features:
            features.append(f"✅ Vanity URL: {guild.vanity_url_code}")
        
        if features:
            embed.add_field(name="⭐ Features", value='\n'.join(features[:5]), inline=True)
        
        # Top roles
        top_roles = []
        for role, count in roles_with_members[:5]:
            if role.name != "@everyone":
                top_roles.append(f"{role.mention}: {count} members")
        if top_roles:
            embed.add_field(name="🏆 Top Roles", value='\n'.join(top_roles), inline=False)
        
        # Boost info
        boost_info = []
        boost_info.append(f"**Level:** {guild.premium_tier}/3")
        boost_info.append(f"**Boosts:** {guild.premium_subscription_count}")
        boost_info.append(f"**Boosters:** {len(guild.premium_subscribers)}")
        embed.add_field(name="💎 Boost Status", value='\n'.join(boost_info), inline=True)
        
        # Emoji info
        emoji_info = []
        emoji_info.append(f"**Static:** {static_emojis}/{guild.emoji_limit}")
        emoji_info.append(f"**Animated:** {animated_emojis}/{guild.emoji_limit}")
        emoji_info.append(f"**Total:** {len(guild.emojis)}/{guild.emoji_limit*2}")
        embed.add_field(name="😀 Emojis", value='\n'.join(emoji_info), inline=True)
        
        # Server age
        age_days = (discord.utils.utcnow() - guild.created_at).days
        embed.add_field(
            name="🎂 Server Age",
            value=f"{age_days} days ({age_days // 365} years)\nCreated: <t:{int(guild.created_at.timestamp())}:R>",
            inline=True
        )
        
        embed.set_footer(text="Server Analytics • Real-time data")
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="afk", description="Set yourself as AFK with a custom message")
    @app_commands.describe(reason="Why you're AFK")
    async def afk(self, interaction: discord.Interaction, reason: str = "AFK") -> None:
        """Set AFK status (would need database for persistence)."""
        embed = discord.Embed(
            description=f"💤 {interaction.user.mention} is now AFK: {reason}",
            color=discord.Color.yellow()
        )
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="membercount", description="Show server member count with graph")
    async def membercount(self, interaction: discord.Interaction) -> None:
        """Show member count."""
        guild = interaction.guild
        
        total = guild.member_count
        humans = len([m for m in guild.members if not m.bot])
        bots = total - humans
        
        embed = discord.Embed(
            title=f"👥 {guild.name} Member Count",
            color=discord.Color.blue()
        )
        
        # Create a simple text-based bar
        human_bar = "█" * int((humans/total) * 20)
        bot_bar = "█" * int((bots/total) * 20)
        
        embed.add_field(
            name=f"👤 Humans: {humans}",
            value=f"`{human_bar}` {humans/total*100:.1f}%",
            inline=False
        )
        embed.add_field(
            name=f"🤖 Bots: {bots}",
            value=f"`{bot_bar}` {bots/total*100:.1f}%",
            inline=False
        )
        embed.add_field(name="📊 Total", value=str(total), inline=False)
        
        await interaction.response.send_message(embed=embed)

class TrackingCog(commands.Cog):
    """Advanced tracking and monitoring commands."""
    
    def __init__(self, bot: ModernBot) -> None:
        self.bot = bot
    
    @app_commands.command(name="setuplogchannels", description="Auto-create and configure all logging channels")
    @app_commands.describe(
        category_name="Name for the logging category (default: 'Logs')",
        setup_type="Create all channels or single channel for everything"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setuplogchannels(
        self,
        interaction: discord.Interaction,
        category_name: str = "📋 Server Logs",
        setup_type: Literal['separate', 'single'] = 'separate'
    ) -> None:
        """Auto-create logging channels with proper configuration."""
        await interaction.response.defer()
        
        guild = interaction.guild
        
        # Create category
        category = await guild.create_category(
            name=category_name,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(
                    read_messages=False,
                    send_messages=False
                ),
                guild.me: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True
                )
            }
        )
        
        created_channels = []
        
        if setup_type == 'single':
            # Create single channel for all logs
            channel = await guild.create_text_channel(
                name="all-logs",
                category=category,
                topic="All server events are logged here"
            )
            
            if guild.id not in self.bot.log_channels:
                self.bot.log_channels[guild.id] = {}
            
            self.bot.log_channels[guild.id]['all'] = channel.id
            created_channels.append(('all', channel))
        
        else:
            # Create separate channels for each log type
            log_types = [
                ('members', '👥-member-logs', 'Member joins, leaves, updates'),
                ('messages', '💬-message-logs', 'Deleted and edited messages'),
                ('voice', '🎙️-voice-logs', 'Voice channel activity'),
                ('roles', '🎭-role-logs', 'Role changes and updates'),
                ('channels', '📺-channel-logs', 'Channel creation, deletion, updates'),
                ('moderation', '🔨-moderation-logs', 'Bans, kicks, timeouts'),
                ('server', '⚙️-server-logs', 'Server updates, emojis, invites')
            ]
            
            if guild.id not in self.bot.log_channels:
                self.bot.log_channels[guild.id] = {}
            
            for event_type, channel_name, topic in log_types:
                channel = await guild.create_text_channel(
                    name=channel_name,
                    category=category,
                    topic=topic
                )
                
                self.bot.log_channels[guild.id][event_type] = channel.id
                created_channels.append((event_type, channel))
        
        # Save configuration
        self.bot.save_config()
        
        # Create summary embed
        embed = discord.Embed(
            title="✅ Logging Channels Created!",
            description=f"Successfully set up logging in **{category.name}**",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        
        channels_list = '\n'.join([f"**{event_type}** → {channel.mention}" for event_type, channel in created_channels])
        embed.add_field(name="📋 Configured Channels", value=channels_list, inline=False)
        
        embed.add_field(
            name="🔐 Permissions",
            value="Channels are hidden from @everyone and only visible to administrators.",
            inline=False
        )
        
        embed.add_field(
            name="✏️ Customize",
            value="You can use `/setlog` to change individual log destinations anytime!",
            inline=False
        )
        
        embed.set_footer(text=f"Created by {interaction.user}")
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="setlog", description="Set up auto-logging for different events")
    @app_commands.describe(
        event_type="Type of events to log",
        channel="Channel to send logs to"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setlog(
        self, 
        interaction: discord.Interaction,
        event_type: Literal['all', 'members', 'messages', 'voice', 'roles', 'channels', 'moderation', 'server'],
        channel: discord.TextChannel
    ) -> None:
        """Set up logging channels."""
        guild_id = interaction.guild_id
        
        if guild_id not in self.bot.log_channels:
            self.bot.log_channels[guild_id] = {}
        
        self.bot.log_channels[guild_id][event_type] = channel.id
        self.bot.save_config()
        
        embed = discord.Embed(
            title="✅ Logging Configured",
            description=f"**Event Type:** {event_type}\n**Channel:** {channel.mention}",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="What will be logged:",
            value=self._get_event_description(event_type),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    def _get_event_description(self, event_type: str) -> str:
        """Get description of what events will be logged."""
        descriptions = {
            'all': '🌐 Everything (all events below)',
            'members': '👤 Joins, leaves, username changes, nickname changes',
            'messages': '💬 Deleted messages, edited messages, bulk deletes',
            'voice': '🎙️ Join/leave voice, mute/unmute, stream start/stop',
            'roles': '🎭 Role created, deleted, updated, member role changes',
            'channels': '📺 Channel created, deleted, updated, permission changes',
            'moderation': '🔨 Bans, unbans, kicks, timeouts, warnings',
            'server': '⚙️ Server updates, emoji changes, sticker changes'
        }
        return descriptions.get(event_type, 'Unknown')
    
    @app_commands.command(name="tracking", description="View detailed tracking data for a user")
    @app_commands.describe(member="The member to track")
    async def tracking(self, interaction: discord.Interaction, member: Optional[discord.Member] = None) -> None:
        """View user tracking data."""
        member = member or interaction.user
        data = self.bot.user_activity[member.id]
        
        embed = discord.Embed(
            title=f"📊 Tracking Data: {member.display_name}",
            color=member.color,
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        embed.add_field(name="💬 Messages Sent", value=f"{data['messages']:,}", inline=True)
        embed.add_field(name="🎙️ Voice Time", value=f"{data['voice_time']} minutes", inline=True)
        embed.add_field(name="🔄 Server Joins", value=str(data['joins']), inline=True)
        embed.add_field(name="👋 Server Leaves", value=str(data['leaves']), inline=True)
        
        embed.set_footer(text="Live tracking data")
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="membertrack", description="Get COMPLETE tracking profile of a member")
    @app_commands.describe(member="Member to analyze")
    async def membertrack(self, interaction: discord.Interaction, member: Optional[discord.Member] = None) -> None:
        """Deep member tracking with ALL information."""
        await interaction.response.defer()
        member = member or interaction.user
        
        embed = discord.Embed(
            title=f"🔍 Complete Profile Analysis",
            description=f"Comprehensive tracking data for {member.mention}",
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Account basics
        account_age = (discord.utils.utcnow() - member.created_at).days
        server_age = (discord.utils.utcnow() - member.joined_at).days
        
        embed.add_field(
            name="⏰ Time Stats",
            value=f"**Account Age:** {account_age} days\n"
                  f"**Server Age:** {server_age} days\n"
                  f"**Join Position:** #{sorted(interaction.guild.members, key=lambda m: m.joined_at).index(member) + 1}",
            inline=True
        )
        
        # Current status
        embed.add_field(
            name="📊 Current Status",
            value=f"**Status:** {member.status}\n"
                  f"**Activity:** {member.activity.name if member.activity else 'None'}\n"
                  f"**Voice:** {'Yes' if member.voice else 'No'}",
            inline=True
        )
        
        # Role count and permissions
        role_count = len([r for r in member.roles if r.name != '@everyone'])
        admin = member.guild_permissions.administrator
        
        embed.add_field(
            name="🎭 Roles & Perms",
            value=f"**Roles:** {role_count}\n"
                  f"**Top Role:** {member.top_role.mention}\n"
                  f"**Administrator:** {'✅ Yes' if admin else '❌ No'}",
            inline=True
        )
        
        # Activity data
        data = self.bot.user_activity[member.id]
        embed.add_field(
            name="📈 Activity Metrics",
            value=f"**Messages:** {data['messages']:,}\n"
                  f"**Voice Time:** {data['voice_time']} min\n"
                  f"**Joins/Leaves:** {data['joins']}/{data['leaves']}",
            inline=True
        )
        
        # Boost info
        boost_info = "✅ Boosting" if member.premium_since else "❌ Not boosting"
        if member.premium_since:
            boost_info += f"\nSince: <t:{int(member.premium_since.timestamp())}:R>"
        
        embed.add_field(name="💎 Boost Status", value=boost_info, inline=True)
        
        # Moderation status
        mod_info = []
        if member.timed_out_until:
            mod_info.append(f"⏰ Timed out until: <t:{int(member.timed_out_until.timestamp())}:R>")
        else:
            mod_info.append("✅ No active timeout")
        
        embed.add_field(name="🔨 Moderation", value='\n'.join(mod_info), inline=True)
        
        embed.set_footer(text="Real-time comprehensive tracking")
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="serverstats", description="Live server statistics and tracking")
    async def serverstats(self, interaction: discord.Interaction) -> None:
        """Real-time server statistics."""
        await interaction.response.defer()
        
        guild = interaction.guild
        
        # Calculate real-time stats
        now = discord.utils.utcnow()
        online = len([m for m in guild.members if m.status != discord.Status.offline])
        in_voice = len([m for m in guild.members if m.voice])
        streaming = len([m for m in guild.members if m.voice and m.voice.self_stream])
        boosters = len(guild.premium_subscribers)
        
        embed = discord.Embed(
            title=f"📊 Live Server Statistics",
            description=f"Real-time data for **{guild.name}**",
            color=discord.Color.blue(),
            timestamp=now
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Live member stats
        embed.add_field(
            name="👥 Members (Live)",
            value=f"**Total:** {guild.member_count}\n"
                  f"**🟢 Online:** {online}\n"
                  f"**🎙️ In Voice:** {in_voice}\n"
                  f"**📹 Streaming:** {streaming}",
            inline=True
        )
        
        # Booster stats
        embed.add_field(
            name="💎 Boost Stats",
            value=f"**Level:** {guild.premium_tier}/3\n"
                  f"**Boosts:** {guild.premium_subscription_count}\n"
                  f"**Boosters:** {boosters}",
            inline=True
        )
        
        # Content stats
        total_emojis = len(guild.emojis)
        total_stickers = len(guild.stickers)
        total_roles = len(guild.roles)
        
        embed.add_field(
            name="📦 Content",
            value=f"**Emojis:** {total_emojis}\n"
                  f"**Stickers:** {total_stickers}\n"
                  f"**Roles:** {total_roles}",
            inline=True
        )
        
        # Calculate activity scores
        total_msgs = sum(data['messages'] for data in self.bot.user_activity.values())
        total_voice = sum(data['voice_time'] for data in self.bot.user_activity.values())
        
        embed.add_field(
            name="📈 Tracked Activity",
            value=f"**Messages:** {total_msgs:,}\n"
                  f"**Voice Time:** {total_voice:,} min",
            inline=True
        )
        
        embed.set_footer(text="🔴 Live • Updates in real-time")
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="activity", description="Show server activity patterns")
    async def activity(self, interaction: discord.Interaction) -> None:
        """Show activity heatmap and patterns."""
        guild = interaction.guild
        
        # Get member status breakdown
        online = len([m for m in guild.members if m.status == discord.Status.online])
        idle = len([m for m in guild.members if m.status == discord.Status.idle])
        dnd = len([m for m in guild.members if m.status == discord.Status.dnd])
        offline = len([m for m in guild.members if m.status == discord.Status.offline])
        
        embed = discord.Embed(
            title="📊 Server Activity Overview",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        # Status breakdown with bars
        total = guild.member_count
        embed.add_field(
            name="🟢 Online",
            value=f"`{'█' * int((online/total) * 20)}` {online} ({online/total*100:.1f}%)",
            inline=False
        )
        embed.add_field(
            name="🟡 Idle",
            value=f"`{'█' * int((idle/total) * 20)}` {idle} ({idle/total*100:.1f}%)",
            inline=False
        )
        embed.add_field(
            name="🔴 DND",
            value=f"`{'█' * int((dnd/total) * 20)}` {dnd} ({dnd/total*100:.1f}%)",
            inline=False
        )
        embed.add_field(
            name="⚫ Offline",
            value=f"`{'█' * int((offline/total) * 20)}` {offline} ({offline/total*100:.1f}%)",
            inline=False
        )
        
        # Most active users
        top_users = sorted(
            [(user_id, data['messages']) for user_id, data in self.bot.user_activity.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        if top_users:
            top_text = []
            for user_id, msgs in top_users:
                user = guild.get_member(user_id)
                if user:
                    top_text.append(f"{user.mention}: {msgs:,} messages")
            
            if top_text:
                embed.add_field(name="🏆 Most Active", value='\n'.join(top_text), inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="auditlog", description="View recent audit log entries")
    @app_commands.describe(limit="Number of entries to show (max 25)")
    @app_commands.checks.has_permissions(view_audit_log=True)
    async def auditlog(self, interaction: discord.Interaction, limit: int = 10) -> None:
        """View server audit logs."""
        await interaction.response.defer()
        
        limit = min(limit, 25)
        entries = []
        
        async for entry in interaction.guild.audit_logs(limit=limit):
            action_icons = {
                discord.AuditLogAction.kick: "👢",
                discord.AuditLogAction.ban: "🔨",
                discord.AuditLogAction.unban: "✅",
                discord.AuditLogAction.member_update: "👤",
                discord.AuditLogAction.member_role_update: "🎭",
                discord.AuditLogAction.channel_create: "➕",
                discord.AuditLogAction.channel_delete: "❌",
                discord.AuditLogAction.message_delete: "🗑️",
            }
            
            icon = action_icons.get(entry.action, "📝")
            timestamp = f"<t:{int(entry.created_at.timestamp())}:R>"
            target = entry.target.name if hasattr(entry.target, 'name') else str(entry.target)
            
            entries.append(f"{icon} **{entry.action.name}** by {entry.user.mention}\n"
                         f"Target: {target} • {timestamp}")
        
        embed = discord.Embed(
            title="📜 Recent Audit Log",
            description='\n\n'.join(entries) if entries else "No recent entries",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        await interaction.followup.send(embed=embed)

class AutoLoggerCog(commands.Cog):
    """Automatic event logging system."""
    
    def __init__(self, bot: ModernBot) -> None:
        self.bot = bot
    
    async def send_log(self, guild_id: int, event_type: str, embed: discord.Embed) -> None:
        """Send log to configured channel."""
        if guild_id not in self.bot.log_channels:
            return
        
        log_config = self.bot.log_channels[guild_id]
        channel_id = log_config.get(event_type) or log_config.get('all')
        
        if channel_id:
            try:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    await channel.send(embed=embed)
            except Exception as e:
                logger.error(f"Failed to send log: {e}")
    
    # === MEMBER EVENTS ===
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Track member joins."""
        self.bot.user_activity[member.id]['joins'] += 1
        
        embed = discord.Embed(
            title="👋 Member Joined",
            description=f"{member.mention} joined the server",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Account Created", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="Member #", value=str(member.guild.member_count), inline=True)
        embed.set_footer(text=f"User ID: {member.id}")
        
        await self.send_log(member.guild.id, 'members', embed)
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        """Track member leaves."""
        self.bot.user_activity[member.id]['leaves'] += 1
        
        embed = discord.Embed(
            title="👋 Member Left",
            description=f"{member.mention} left the server",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        if member.joined_at:
            days_in_server = (discord.utils.utcnow() - member.joined_at).days
            embed.add_field(name="Time in Server", value=f"{days_in_server} days", inline=True)
        
        roles = [r.mention for r in member.roles if r.name != '@everyone']
        if roles:
            embed.add_field(name="Roles", value=' '.join(roles[:5]), inline=False)
        
        embed.set_footer(text=f"User ID: {member.id}")
        
        await self.send_log(member.guild.id, 'members', embed)
    
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        """Track member updates (nickname, roles, etc)."""
        embed = None
        
        # Nickname change
        if before.nick != after.nick:
            embed = discord.Embed(
                title="✏️ Nickname Changed",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Member", value=after.mention, inline=False)
            embed.add_field(name="Before", value=before.nick or "*None*", inline=True)
            embed.add_field(name="After", value=after.nick or "*None*", inline=True)
            embed.set_thumbnail(url=after.display_avatar.url)
        
        # Role changes
        elif before.roles != after.roles:
            added = [r for r in after.roles if r not in before.roles]
            removed = [r for r in before.roles if r not in after.roles]
            
            embed = discord.Embed(
                title="🎭 Roles Updated",
                description=f"Role changes for {after.mention}",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            
            if added:
                embed.add_field(name="➕ Added", value=' '.join([r.mention for r in added]), inline=False)
            if removed:
                embed.add_field(name="➖ Removed", value=' '.join([r.mention for r in removed]), inline=False)
            
            embed.set_thumbnail(url=after.display_avatar.url)
        
        # Timeout
        elif before.timed_out_until != after.timed_out_until:
            if after.timed_out_until:
                embed = discord.Embed(
                    title="⏰ Member Timed Out",
                    description=f"{after.mention} was timed out",
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(name="Until", value=f"<t:{int(after.timed_out_until.timestamp())}:F>")
            else:
                embed = discord.Embed(
                    title="✅ Timeout Removed",
                    description=f"{after.mention} timeout was removed",
                    color=discord.Color.green(),
                    timestamp=discord.utils.utcnow()
                )
        
        if embed:
            embed.set_footer(text=f"User ID: {after.id}")
            await self.send_log(after.guild.id, 'members', embed)
    
    # === MESSAGE EVENTS ===
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Track messages."""
        if not message.author.bot and message.guild:
            self.bot.user_activity[message.author.id]['messages'] += 1
    
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        """Log deleted messages."""
        if message.author.bot:
            return
        
        embed = discord.Embed(
            title="🗑️ Message Deleted",
            description=message.content[:1024] if message.content else "*No text content*",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        embed.add_field(name="Message ID", value=f"`{message.id}`", inline=True)
        
        if message.attachments:
            attachments = '\n'.join([att.url for att in message.attachments[:3]])
            embed.add_field(name="Attachments", value=attachments, inline=False)
        
        embed.set_footer(text=f"Author ID: {message.author.id}")
        
        await self.send_log(message.guild.id, 'messages', embed)
    
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        """Log edited messages."""
        if before.author.bot or before.content == after.content:
            return
        
        embed = discord.Embed(
            title="✏️ Message Edited",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_author(name=str(before.author), icon_url=before.author.display_avatar.url)
        embed.add_field(name="Channel", value=before.channel.mention, inline=False)
        embed.add_field(name="Before", value=before.content[:1024] if before.content else "*Empty*", inline=False)
        embed.add_field(name="After", value=after.content[:1024] if after.content else "*Empty*", inline=False)
        embed.add_field(name="Jump to Message", value=f"[Click here]({after.jump_url})", inline=False)
        embed.set_footer(text=f"Author ID: {before.author.id} • Message ID: {before.id}")
        
        await self.send_log(before.guild.id, 'messages', embed)
    
    # === VOICE EVENTS ===
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        """Track voice activity."""
        embed = None
        
        # Joined voice
        if before.channel is None and after.channel is not None:
            embed = discord.Embed(
                title="🎙️ Joined Voice Channel",
                description=f"{member.mention} joined {after.channel.mention}",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
        
        # Left voice
        elif before.channel is not None and after.channel is None:
            embed = discord.Embed(
                title="👋 Left Voice Channel",
                description=f"{member.mention} left {before.channel.mention}",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
        
        # Moved channels
        elif before.channel != after.channel and after.channel is not None:
            embed = discord.Embed(
                title="🔄 Moved Voice Channels",
                description=f"{member.mention} moved channels",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="From", value=before.channel.mention, inline=True)
            embed.add_field(name="To", value=after.channel.mention, inline=True)
        
        # Started streaming
        elif not before.self_stream and after.self_stream:
            embed = discord.Embed(
                title="📹 Started Streaming",
                description=f"{member.mention} started streaming in {after.channel.mention}",
                color=discord.Color.purple(),
                timestamp=discord.utils.utcnow()
            )
        
        if embed:
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"User ID: {member.id}")
            await self.send_log(member.guild.id, 'voice', embed)
    
    # === MODERATION EVENTS ===
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User) -> None:
        """Log bans."""
        embed = discord.Embed(
            title="🔨 Member Banned",
            description=f"{user.mention} was banned from the server",
            color=discord.Color.dark_red(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"User ID: {user.id}")
        
        # Try to get ban reason from audit log
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
                if entry.target.id == user.id:
                    embed.add_field(name="Banned by", value=entry.user.mention, inline=True)
                    if entry.reason:
                        embed.add_field(name="Reason", value=entry.reason, inline=True)
                    break
        except:
            pass
        
        await self.send_log(guild.id, 'moderation', embed)
    
    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User) -> None:
        """Log unbans."""
        embed = discord.Embed(
            title="✅ Member Unbanned",
            description=f"{user.mention} was unbanned",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"User ID: {user.id}")
        
        await self.send_log(guild.id, 'moderation', embed)

    # === CHANNEL EVENTS ===
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel) -> None:
        """Log channel creation."""
        embed = discord.Embed(
            title="➕ Channel Created",
            description=f"New channel: {channel.mention}",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Type", value=str(channel.type), inline=True)
        embed.add_field(name="Channel ID", value=f"`{channel.id}`", inline=True)
        
        await self.send_log(channel.guild.id, 'channels', embed)
    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        """Log channel deletion."""
        embed = discord.Embed(
            title="❌ Channel Deleted",
            description=f"Deleted: **{channel.name}**",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Type", value=str(channel.type), inline=True)
        embed.add_field(name="Channel ID", value=f"`{channel.id}`", inline=True)
        
        await self.send_log(channel.guild.id, 'channels', embed)
    
    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel) -> None:
        """Log channel updates."""
        changes = []
        
        if before.name != after.name:
            changes.append(f"**Name:** {before.name} → {after.name}")
        
        if hasattr(before, 'topic') and hasattr(after, 'topic') and before.topic != after.topic:
            changes.append(f"**Topic changed**")
        
        if changes:
            embed = discord.Embed(
                title="✏️ Channel Updated",
                description=f"Changes to {after.mention}",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Changes", value='\n'.join(changes), inline=False)
            
            await self.send_log(after.guild.id, 'channels', embed)
    
    # === ROLE EVENTS ===
    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role) -> None:
        """Log role creation."""
        embed = discord.Embed(
            title="🎭 Role Created",
            description=f"New role: {role.mention}",
            color=role.color or discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Role ID", value=f"`{role.id}`", inline=True)
        embed.add_field(name="Color", value=str(role.color), inline=True)
        
        await self.send_log(role.guild.id, 'roles', embed)
    
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role) -> None:
        """Log role deletion."""
        embed = discord.Embed(
            title="❌ Role Deleted",
            description=f"Deleted: **{role.name}**",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Role ID", value=f"`{role.id}`", inline=True)
        
        await self.send_log(role.guild.id, 'roles', embed)
    
    # === SERVER EVENTS ===
    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild) -> None:
        """Log server updates."""
        changes = []
        
        if before.name != after.name:
            changes.append(f"**Name:** {before.name} → {after.name}")
        
        if before.icon != after.icon:
            changes.append("**Icon changed**")
        
        if before.banner != after.banner:
            changes.append("**Banner changed**")
        
        if before.description != after.description:
            changes.append("**Description changed**")
        
        if before.premium_tier != after.premium_tier:
            changes.append(f"**Boost Level:** {before.premium_tier} → {after.premium_tier} 🎉")
        
        if changes:
            embed = discord.Embed(
                title="⚙️ Server Updated",
                description='\n'.join(changes),
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            
            await self.send_log(after.id, 'server', embed)
    
    # === EMOJI/STICKER EVENTS ===
    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild: discord.Guild, before: List[discord.Emoji], after: List[discord.Emoji]) -> None:
        """Log emoji updates."""
        added = [e for e in after if e not in before]
        removed = [e for e in before if e not in after]
        
        if added:
            embed = discord.Embed(
                title="😀 Emoji Added",
                description='\n'.join([f"{e} `:{e.name}:`" for e in added]),
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            await self.send_log(guild.id, 'server', embed)
        
        if removed:
            embed = discord.Embed(
                title="❌ Emoji Removed",
                description='\n'.join([f"`:{e.name}:`" for e in removed]),
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            await self.send_log(guild.id, 'server', embed)
    
    # === INVITE EVENTS ===
    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite) -> None:
        """Log invite creation."""
        embed = discord.Embed(
            title="🔗 Invite Created",
            description=f"New invite: `{invite.code}`",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Created by", value=invite.inviter.mention if invite.inviter else "Unknown", inline=True)
        embed.add_field(name="Channel", value=invite.channel.mention, inline=True)
        if invite.max_uses:
            embed.add_field(name="Max Uses", value=str(invite.max_uses), inline=True)
        if invite.max_age:
            embed.add_field(name="Expires In", value=f"{invite.max_age}s", inline=True)
        
        await self.send_log(invite.guild.id, 'server', embed)
    
    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite) -> None:
        """Log invite deletion."""
        embed = discord.Embed(
            title="🗑️ Invite Deleted",
            description=f"Deleted: `{invite.code}`",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        
        await self.send_log(invite.guild.id, 'server', embed)
    
    # === THREAD EVENTS ===
    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread) -> None:
        """Log thread creation."""
        embed = discord.Embed(
            title="🧵 Thread Created",
            description=f"New thread: {thread.mention}",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Created by", value=thread.owner.mention if thread.owner else "Unknown", inline=True)
        embed.add_field(name="Parent Channel", value=thread.parent.mention if thread.parent else "Unknown", inline=True)
        
        await self.send_log(thread.guild.id, 'channels', embed)
    
    @commands.Cog.listener()
    async def on_thread_delete(self, thread: discord.Thread) -> None:
        """Log thread deletion."""
        embed = discord.Embed(
            title="🗑️ Thread Deleted",
            description=f"Deleted: **{thread.name}**",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        
        await self.send_log(thread.guild.id, 'channels', embed)
    
    # === REACTION EVENTS ===
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        """Log reactions on important messages."""
        # Only log in specific scenarios (you can customize this)
        pass
    
    # === BULK DELETE ===
    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: List[discord.Message]) -> None:
        """Log bulk message deletion."""
        if not messages:
            return
        
        channel = messages[0].channel
        guild = messages[0].guild
        
        embed = discord.Embed(
            title="🗑️ Bulk Message Delete",
            description=f"**{len(messages)}** messages deleted in {channel.mention}",
            color=discord.Color.dark_red(),
            timestamp=discord.utils.utcnow()
        )
        
        # Show some message previews
        preview = []
        for msg in messages[:5]:
            if msg.content:
                preview.append(f"**{msg.author}:** {msg.content[:50]}...")
        
        if preview:
            embed.add_field(name="Sample Messages", value='\n'.join(preview), inline=False)
        
        await self.send_log(guild.id, 'messages', embed)

class AutomationCog(commands.Cog):
    """Advanced automation features."""
    
    def __init__(self, bot: ModernBot) -> None:
        self.bot = bot
        self.welcome_config = {}  # guild_id: {channel_id, message}
        self.auto_roles = {}  # guild_id: [role_ids]
        self.auto_responses = {}  # guild_id: {trigger: response}
        self.automod_config = {}  # guild_id: {rules}
    
    @app_commands.command(name="autowelcome", description="Setup automatic welcome messages")
    @app_commands.describe(
        channel="Channel to send welcome messages",
        message="Welcome message (use {user} for mention, {server} for server name)"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def autowelcome(self, interaction: discord.Interaction, channel: discord.TextChannel, message: str) -> None:
        """Configure auto-welcome messages."""
        self.welcome_config[interaction.guild_id] = {
            'channel_id': channel.id,
            'message': message
        }
        
        # Preview
        preview = message.replace('{user}', interaction.user.mention).replace('{server}', interaction.guild.name)
        
        embed = discord.Embed(
            title="✅ Auto-Welcome Configured",
            description="New members will receive this message:",
            color=discord.Color.green()
        )
        embed.add_field(name="Channel", value=channel.mention, inline=False)
        embed.add_field(name="Preview", value=preview, inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Send welcome message and auto-assign roles."""
        guild_id = member.guild.id
        
        # Welcome message
        if guild_id in self.welcome_config:
            config = self.welcome_config[guild_id]
            channel = self.bot.get_channel(config['channel_id'])
            if channel:
                message = config['message'].replace('{user}', member.mention).replace('{server}', member.guild.name)
                
                embed = discord.Embed(
                    title=f"👋 Welcome to {member.guild.name}!",
                    description=message,
                    color=discord.Color.green()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=f"Member #{member.guild.member_count}")
                
                await channel.send(content=member.mention, embed=embed)
        
        # Auto-roles
        if guild_id in self.auto_roles:
            roles_to_add = []
            for role_id in self.auto_roles[guild_id]:
                role = member.guild.get_role(role_id)
                if role:
                    roles_to_add.append(role)
            
            if roles_to_add:
                try:
                    await member.add_roles(*roles_to_add, reason="Auto-role on join")
                except Exception as e:
                    logger.error(f"Failed to add auto-roles: {e}")
    
    @app_commands.command(name="autorole", description="Auto-assign roles when members join")
    @app_commands.describe(role="Role to automatically assign")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def autorole(self, interaction: discord.Interaction, role: discord.Role) -> None:
        """Configure auto-roles."""
        guild_id = interaction.guild_id
        
        if guild_id not in self.auto_roles:
            self.auto_roles[guild_id] = []
        
        if role.id in self.auto_roles[guild_id]:
            self.auto_roles[guild_id].remove(role.id)
            await interaction.response.send_message(f"❌ Removed {role.mention} from auto-roles", ephemeral=True)
        else:
            self.auto_roles[guild_id].append(role.id)
            await interaction.response.send_message(f"✅ Added {role.mention} to auto-roles", ephemeral=True)
    
    @app_commands.command(name="autoresponse", description="Setup automatic responses to keywords")
    @app_commands.describe(
        trigger="Keyword to trigger response",
        response="Message to send when triggered"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def autoresponse(self, interaction: discord.Interaction, trigger: str, response: str) -> None:
        """Configure auto-responses."""
        guild_id = interaction.guild_id
        
        if guild_id not in self.auto_responses:
            self.auto_responses[guild_id] = {}
        
        self.auto_responses[guild_id][trigger.lower()] = response
        
        embed = discord.Embed(
            title="✅ Auto-Response Added",
            color=discord.Color.green()
        )
        embed.add_field(name="Trigger", value=f"`{trigger}`", inline=True)
        embed.add_field(name="Response", value=response, inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Handle auto-responses."""
        if message.author.bot or not message.guild:
            return
        
        guild_id = message.guild.id
        if guild_id in self.auto_responses:
            content_lower = message.content.lower()
            for trigger, response in self.auto_responses[guild_id].items():
                if trigger in content_lower:
                    await message.reply(response, mention_author=False)
                    break
    
    @app_commands.command(name="automod", description="Configure auto-moderation rules")
    @app_commands.describe(
        rule_type="Type of auto-mod rule",
        action="Action to take"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def automod(
        self,
        interaction: discord.Interaction,
        rule_type: Literal['spam', 'caps', 'links', 'invites', 'mentions'],
        action: Literal['delete', 'warn', 'timeout', 'kick']
    ) -> None:
        """Configure auto-moderation."""
        guild_id = interaction.guild_id
        
        if guild_id not in self.automod_config:
            self.automod_config[guild_id] = {}
        
        self.automod_config[guild_id][rule_type] = action
        
        embed = discord.Embed(
            title="✅ Auto-Mod Configured",
            description=f"**Rule:** {rule_type}\n**Action:** {action}",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed)

class ModernInteractionsCog(commands.Cog):
    """Modern Discord interactions - modals, dropdowns, buttons."""
    
    def __init__(self, bot: ModernBot) -> None:
        self.bot = bot
    
    @app_commands.command(name="embed", description="Create a custom embed with a builder")
    async def embed_builder(self, interaction: discord.Interaction) -> None:
        """Interactive embed builder with modal."""
        
        class EmbedModal(discord.ui.Modal, title="Embed Builder"):
            embed_title = discord.ui.TextInput(
                label="Title",
                placeholder="Enter embed title...",
                required=True,
                max_length=256
            )
            
            description = discord.ui.TextInput(
                label="Description",
                placeholder="Enter description...",
                style=discord.TextStyle.paragraph,
                required=True,
                max_length=4000
            )
            
            color = discord.ui.TextInput(
                label="Color (hex code)",
                placeholder="#5865F2",
                required=False,
                max_length=7
            )
            
            footer = discord.ui.TextInput(
                label="Footer",
                placeholder="Footer text...",
                required=False,
                max_length=2048
            )
            
            async def on_submit(self, interaction: discord.Interaction):
                # Parse color
                color = discord.Color.blurple()
                if self.color.value:
                    try:
                        color = discord.Color(int(self.color.value.replace('#', ''), 16))
                    except:
                        pass
                
                embed = discord.Embed(
                    title=self.embed_title.value,
                    description=self.description.value,
                    color=color,
                    timestamp=discord.utils.utcnow()
                )
                
                if self.footer.value:
                    embed.set_footer(text=self.footer.value)
                
                await interaction.response.send_message(embed=embed)
        
        await interaction.response.send_modal(EmbedModal())
    
    @app_commands.command(name="dropdown", description="Create a dropdown menu for role selection")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def dropdown_menu(self, interaction: discord.Interaction) -> None:
        """Create a dropdown role menu."""
        
        class RoleSelect(discord.ui.Select):
            def __init__(self, roles: List[discord.Role]):
                options = [
                    discord.SelectOption(label=role.name, value=str(role.id), emoji="🎭")
                    for role in roles[:25]  # Max 25 options
                ]
                
                super().__init__(
                    placeholder="Select roles to add/remove...",
                    min_values=1,
                    max_values=len(options),
                    options=options
                )
            
            async def callback(self, interaction: discord.Interaction):
                member = interaction.user
                selected_role_ids = [int(value) for value in self.values]
                
                added = []
                removed = []
                
                for role_id in selected_role_ids:
                    role = interaction.guild.get_role(role_id)
                    if role:
                        if role in member.roles:
                            await member.remove_roles(role)
                            removed.append(role.mention)
                        else:
                            await member.add_roles(role)
                            added.append(role.mention)
                
                response = []
                if added:
                    response.append(f"✅ Added: {', '.join(added)}")
                if removed:
                    response.append(f"❌ Removed: {', '.join(removed)}")
                
                await interaction.response.send_message('\n'.join(response), ephemeral=True)
        
        class RoleView(discord.ui.View):
            def __init__(self, roles: List[discord.Role]):
                super().__init__(timeout=None)
                self.add_item(RoleSelect(roles))
        
        # Get assignable roles
        roles = [r for r in interaction.guild.roles if not r.managed and r.name != "@everyone"][:25]
        
        if not roles:
            await interaction.response.send_message("❌ No assignable roles found!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🎭 Role Selection",
            description="Select roles from the dropdown below!",
            color=discord.Color.blurple()
        )
        
        view = RoleView(roles)
        await interaction.response.send_message(embed=embed, view=view)
    
    @app_commands.command(name="giveaway", description="Start an interactive giveaway")
    @app_commands.describe(
        prize="What you're giving away",
        duration="Duration in minutes",
        winners="Number of winners"
    )
    async def giveaway(self, interaction: discord.Interaction, prize: str, duration: int, winners: int = 1) -> None:
        """Start a giveaway with button entries."""
        
        end_time = discord.utils.utcnow() + timedelta(minutes=duration)
        entries = set()
        
        class GiveawayButton(discord.ui.Button):
            def __init__(self):
                super().__init__(
                    label="🎉 Enter Giveaway",
                    style=discord.ButtonStyle.success,
                    custom_id="giveaway_enter"
                )
            
            async def callback(self, interaction: discord.Interaction):
                user_id = interaction.user.id
                if user_id in entries:
                    entries.remove(user_id)
                    await interaction.response.send_message("❌ Entry removed!", ephemeral=True)
                else:
                    entries.add(user_id)
                    await interaction.response.send_message("✅ Entry added! Good luck!", ephemeral=True)
                
                # Update embed
                embed = interaction.message.embeds[0]
                embed.set_field_at(2, name="📊 Entries", value=str(len(entries)), inline=True)
                await interaction.message.edit(embed=embed)
        
        class GiveawayView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)
                self.add_item(GiveawayButton())
        
        embed = discord.Embed(
            title="🎉 GIVEAWAY 🎉",
            description=f"**Prize:** {prize}\n\nClick the button below to enter!",
            color=discord.Color.gold(),
            timestamp=end_time
        )
        embed.add_field(name="🏆 Winners", value=str(winners), inline=True)
        embed.add_field(name="⏰ Ends", value=f"<t:{int(end_time.timestamp())}:R>", inline=True)
        embed.add_field(name="📊 Entries", value="0", inline=True)
        embed.set_footer(text="Ends at")
        
        await interaction.response.send_message(embed=embed, view=GiveawayView())
    
    @app_commands.command(name="verify", description="Create a verification system")
    @app_commands.describe(role="Role to give after verification")
    @app_commands.checks.has_permissions(administrator=True)
    async def verify_system(self, interaction: discord.Interaction, role: discord.Role) -> None:
        """Create verification button."""
        
        class VerifyButton(discord.ui.Button):
            def __init__(self, role: discord.Role):
                super().__init__(
                    label="✅ Verify",
                    style=discord.ButtonStyle.success,
                    custom_id=f"verify_{role.id}"
                )
                self.role = role
            
            async def callback(self, interaction: discord.Interaction):
                member = interaction.user
                
                if self.role in member.roles:
                    await interaction.response.send_message("✅ You're already verified!", ephemeral=True)
                else:
                    await member.add_roles(self.role)
                    await interaction.response.send_message(f"✅ Verified! You now have the {self.role.mention} role!", ephemeral=True)
        
        class VerifyView(discord.ui.View):
            def __init__(self, role: discord.Role):
                super().__init__(timeout=None)
                self.add_item(VerifyButton(role))
        
        embed = discord.Embed(
            title="✅ Verification Required",
            description=f"Click the button below to get the {role.mention} role!",
            color=discord.Color.green()
        )
        embed.add_field(name="Why verify?", value="This helps us keep the server safe and organized.", inline=False)
        
        view = VerifyView(role)
        await interaction.response.send_message(embed=embed, view=view)
    
    @app_commands.command(name="ticket", description="Create a support ticket system")
    @app_commands.describe(category="Category to create tickets in")
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_system(self, interaction: discord.Interaction, category: discord.CategoryChannel) -> None:
        """Create ticket system with button."""
        
        class TicketButton(discord.ui.Button):
            def __init__(self, category: discord.CategoryChannel):
                super().__init__(
                    label="🎫 Create Ticket",
                    style=discord.ButtonStyle.primary,
                    custom_id="create_ticket"
                )
                self.category = category
            
            async def callback(self, interaction: discord.Interaction):
                guild = interaction.guild
                user = interaction.user
                
                # Create ticket channel
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                    guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                }
                
                ticket_channel = await guild.create_text_channel(
                    name=f"ticket-{user.name}",
                    category=self.category,
                    overwrites=overwrites
                )
                
                embed = discord.Embed(
                    title="🎫 Support Ticket",
                    description=f"Hello {user.mention}! Support will be with you shortly.",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Need help?", value="Please describe your issue in detail.", inline=False)
                
                await ticket_channel.send(content=user.mention, embed=embed)
                await interaction.response.send_message(f"✅ Ticket created: {ticket_channel.mention}", ephemeral=True)
        
        class TicketView(discord.ui.View):
            def __init__(self, category: discord.CategoryChannel):
                super().__init__(timeout=None)
                self.add_item(TicketButton(category))
        
        embed = discord.Embed(
            title="🎫 Support Tickets",
            description="Need help? Click the button below to create a support ticket!",
            color=discord.Color.blue()
        )
        embed.add_field(name="📌 Instructions", value="1. Click the button\n2. Wait for your ticket channel\n3. Describe your issue", inline=False)
        
        view = TicketView(category)
        await interaction.response.send_message(embed=embed, view=view)

class SuperAdvancedCog(commands.Cog):
    """Super advanced features - starboard, suggestions, reminders, etc."""
    
    def __init__(self, bot: ModernBot) -> None:
        self.bot = bot
        self.starboard_config = {}  # guild_id: {channel_id, threshold}
        self.starboard_messages = {}  # message_id: starboard_message_id
        self.suggestions = {}  # guild_id: {channel_id}
        self.reminders = []  # List of reminders
        self.custom_commands = {}  # guild_id: {trigger: response}
        self.scheduled_messages = []  # List of scheduled messages
        self.check_reminders.start()
        self.check_scheduled.start()
    
    def cog_unload(self) -> None:
        self.check_reminders.cancel()
        self.check_scheduled.cancel()
    
    # === STARBOARD ===
    @app_commands.command(name="starboard", description="Setup starboard for popular messages")
    @app_commands.describe(
        channel="Channel to send starred messages",
        threshold="Number of ⭐ reactions needed (default: 3)"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def starboard(self, interaction: discord.Interaction, channel: discord.TextChannel, threshold: int = 3) -> None:
        """Setup starboard."""
        self.starboard_config[interaction.guild_id] = {
            'channel_id': channel.id,
            'threshold': threshold
        }
        
        embed = discord.Embed(
            title="⭐ Starboard Configured!",
            description=f"Messages with **{threshold}** ⭐ reactions will be posted to {channel.mention}",
            color=discord.Color.gold()
        )
        
        await interaction.response.send_message(embed=embed)
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        """Handle starboard reactions."""
        if str(payload.emoji) != '⭐':
            return
        
        if payload.guild_id not in self.starboard_config:
            return
        
        config = self.starboard_config[payload.guild_id]
        channel = self.bot.get_channel(payload.channel_id)
        
        if not channel:
            return
        
        try:
            message = await channel.fetch_message(payload.message_id)
        except:
            return
        
        # Count star reactions
        star_count = 0
        for reaction in message.reactions:
            if str(reaction.emoji) == '⭐':
                star_count = reaction.count
                break
        
        if star_count < config['threshold']:
            return
        
        # Don't repost if already on starboard
        if payload.message_id in self.starboard_messages:
            return
        
        starboard_channel = self.bot.get_channel(config['channel_id'])
        if not starboard_channel:
            return
        
        # Create starboard embed
        embed = discord.Embed(
            description=message.content or "*No text content*",
            color=discord.Color.gold(),
            timestamp=message.created_at
        )
        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
        embed.add_field(name="Source", value=f"[Jump to message]({message.jump_url})", inline=False)
        
        if message.attachments:
            embed.set_image(url=message.attachments[0].url)
        
        embed.set_footer(text=f"⭐ {star_count} | #{channel.name}")
        
        starboard_msg = await starboard_channel.send(embed=embed)
        self.starboard_messages[payload.message_id] = starboard_msg.id
    
    # === SUGGESTIONS ===
    @app_commands.command(name="setupsuggestions", description="Setup suggestion system")
    @app_commands.describe(channel="Channel for suggestions")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setupsuggestions(self, interaction: discord.Interaction, channel: discord.TextChannel) -> None:
        """Setup suggestions channel."""
        self.suggestions[interaction.guild_id] = {'channel_id': channel.id}
        
        embed = discord.Embed(
            title="💡 Suggestions System Configured!",
            description=f"Suggestions will be posted to {channel.mention}",
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="suggest", description="Submit a suggestion")
    @app_commands.describe(suggestion="Your suggestion")
    async def suggest(self, interaction: discord.Interaction, suggestion: str) -> None:
        """Submit a suggestion."""
        if interaction.guild_id not in self.suggestions:
            await interaction.response.send_message("❌ Suggestions are not set up in this server!", ephemeral=True)
            return
        
        channel_id = self.suggestions[interaction.guild_id]['channel_id']
        channel = self.bot.get_channel(channel_id)
        
        if not channel:
            await interaction.response.send_message("❌ Suggestion channel not found!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="💡 New Suggestion",
            description=suggestion,
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text=f"Suggestion by {interaction.user}")
        
        msg = await channel.send(embed=embed)
        await msg.add_reaction('✅')
        await msg.add_reaction('❌')
        await msg.add_reaction('🤷')
        
        await interaction.response.send_message("✅ Suggestion submitted!", ephemeral=True)
    
    # === REMINDERS ===
    @app_commands.command(name="remind", description="Set a reminder")
    @app_commands.describe(
        time="Time in minutes",
        reminder="What to remind you about"
    )
    async def remind(self, interaction: discord.Interaction, time: int, reminder: str) -> None:
        """Set a personal reminder."""
        remind_time = discord.utils.utcnow() + timedelta(minutes=time)
        
        self.reminders.append({
            'user_id': interaction.user.id,
            'channel_id': interaction.channel_id,
            'time': remind_time,
            'reminder': reminder
        })
        
        embed = discord.Embed(
            title="⏰ Reminder Set!",
            description=f"I'll remind you in **{time}** minutes",
            color=discord.Color.blue()
        )
        embed.add_field(name="Reminder", value=reminder, inline=False)
        embed.add_field(name="Time", value=f"<t:{int(remind_time.timestamp())}:R>", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @tasks.loop(seconds=30)
    async def check_reminders(self) -> None:
        """Check for due reminders."""
        now = discord.utils.utcnow()
        due_reminders = [r for r in self.reminders if r['time'] <= now]
        
        for reminder in due_reminders:
            try:
                channel = self.bot.get_channel(reminder['channel_id'])
                user = await self.bot.fetch_user(reminder['user_id'])
                
                if channel and user:
                    embed = discord.Embed(
                        title="⏰ Reminder!",
                        description=reminder['reminder'],
                        color=discord.Color.gold()
                    )
                    await channel.send(content=user.mention, embed=embed)
                
                self.reminders.remove(reminder)
            except Exception as e:
                logger.error(f"Failed to send reminder: {e}")
    
    @check_reminders.before_loop
    async def before_check_reminders(self) -> None:
        await self.bot.wait_until_ready()
    
    # === TRANSCRIPT ===
    @app_commands.command(name="transcript", description="Export channel message history")
    @app_commands.describe(
        limit="Number of messages to export (max 1000)",
        format_type="Output format"
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def transcript(
        self,
        interaction: discord.Interaction,
        limit: int = 100,
        format_type: Literal['text', 'json'] = 'text'
    ) -> None:
        """Export channel messages."""
        await interaction.response.defer()
        
        limit = min(limit, 1000)
        messages = []
        
        async for message in interaction.channel.history(limit=limit, oldest_first=True):
            messages.append(message)
        
        if format_type == 'text':
            content = []
            content.append(f"Transcript of #{interaction.channel.name}")
            content.append(f"Exported: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
            content.append(f"Messages: {len(messages)}")
            content.append("=" * 50)
            content.append("")
            
            for msg in messages:
                timestamp = msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
                content.append(f"[{timestamp}] {msg.author}: {msg.content}")
                if msg.attachments:
                    for att in msg.attachments:
                        content.append(f"  📎 {att.url}")
                content.append("")
            
            transcript_text = '\n'.join(content)
        else:
            import json
            transcript_data = []
            for msg in messages:
                transcript_data.append({
                    'id': msg.id,
                    'author': str(msg.author),
                    'author_id': msg.author.id,
                    'content': msg.content,
                    'timestamp': msg.created_at.isoformat(),
                    'attachments': [att.url for att in msg.attachments]
                })
            transcript_text = json.dumps(transcript_data, indent=2)
        
        # Save to file
        filename = f"transcript_{interaction.channel.name}_{discord.utils.utcnow().strftime('%Y%m%d_%H%M%S')}.{'txt' if format_type == 'text' else 'json'}"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(transcript_text)
        
        with open(filename, 'rb') as f:
            file = discord.File(f, filename=filename)
            await interaction.followup.send(
                content=f"📄 Exported {len(messages)} messages",
                file=file
            )
        
        # Clean up
        import os
        os.remove(filename)
    
    # === SCHEDULED MESSAGES ===
    @app_commands.command(name="schedule", description="Schedule a message to be sent later")
    @app_commands.describe(
        channel="Channel to send message",
        minutes="Minutes from now",
        message="Message to send"
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def schedule(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        minutes: int,
        message: str
    ) -> None:
        """Schedule a message."""
        send_time = discord.utils.utcnow() + timedelta(minutes=minutes)
        
        self.scheduled_messages.append({
            'channel_id': channel.id,
            'time': send_time,
            'message': message
        })
        
        embed = discord.Embed(
            title="📅 Message Scheduled!",
            description=f"Message will be sent to {channel.mention} in **{minutes}** minutes",
            color=discord.Color.blue()
        )
        embed.add_field(name="Time", value=f"<t:{int(send_time.timestamp())}:F>", inline=False)
        embed.add_field(name="Preview", value=message[:1024], inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @tasks.loop(seconds=30)
    async def check_scheduled(self) -> None:
        """Check for scheduled messages."""
        now = discord.utils.utcnow()
        due_messages = [m for m in self.scheduled_messages if m['time'] <= now]
        
        for scheduled in due_messages:
            try:
                channel = self.bot.get_channel(scheduled['channel_id'])
                if channel:
                    await channel.send(scheduled['message'])
                self.scheduled_messages.remove(scheduled)
            except Exception as e:
                logger.error(f"Failed to send scheduled message: {e}")
    
    @check_scheduled.before_loop
    async def before_check_scheduled(self) -> None:
        await self.bot.wait_until_ready()
    
    # === SERVER BACKUP ===
    @app_commands.command(name="backup", description="Backup server settings (channels, roles)")
    @app_commands.checks.has_permissions(administrator=True)
    async def backup(self, interaction: discord.Interaction) -> None:
        """Create server backup."""
        await interaction.response.defer()
        
        guild = interaction.guild
        
        backup_data = {
            'name': guild.name,
            'description': guild.description,
            'verification_level': str(guild.verification_level),
            'roles': [],
            'channels': [],
            'categories': []
        }
        
        # Backup roles
        for role in guild.roles:
            if role.name != '@everyone':
                backup_data['roles'].append({
                    'name': role.name,
                    'color': str(role.color),
                    'permissions': role.permissions.value,
                    'hoist': role.hoist,
                    'mentionable': role.mentionable
                })
        
        # Backup channels
        for channel in guild.channels:
            if isinstance(channel, discord.CategoryChannel):
                backup_data['categories'].append({
                    'name': channel.name,
                    'position': channel.position
                })
            else:
                backup_data['channels'].append({
                    'name': channel.name,
                    'type': str(channel.type),
                    'category': channel.category.name if channel.category else None,
                    'position': channel.position
                })
        
        # Save to file
        import json
        filename = f"backup_{guild.name}_{discord.utils.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2)
        
        with open(filename, 'rb') as f:
            file = discord.File(f, filename=filename)
            
            embed = discord.Embed(
                title="💾 Server Backup Created!",
                description=f"Backup includes:\n"
                           f"• **{len(backup_data['roles'])}** roles\n"
                           f"• **{len(backup_data['channels'])}** channels\n"
                           f"• **{len(backup_data['categories'])}** categories",
                color=discord.Color.green()
            )
            
            await interaction.followup.send(embed=embed, file=file)
        
        # Clean up
        import os
        os.remove(filename)
    
    # === MASS ACTIONS ===
    @app_commands.command(name="massban", description="Ban multiple users at once")
    @app_commands.describe(
        user_ids="User IDs separated by spaces",
        reason="Reason for bans"
    )
    @app_commands.checks.has_permissions(ban_members=True)
    async def massban(self, interaction: discord.Interaction, user_ids: str, reason: str = "Mass ban") -> None:
        """Mass ban users."""
        await interaction.response.defer(ephemeral=True)
        
        ids = user_ids.split()
        banned = []
        failed = []
        
        for user_id in ids:
            try:
                user = await self.bot.fetch_user(int(user_id))
                await interaction.guild.ban(user, reason=reason)
                banned.append(str(user))
            except Exception as e:
                failed.append(f"{user_id}: {str(e)}")
        
        embed = discord.Embed(
            title="🔨 Mass Ban Complete",
            color=discord.Color.red()
        )
        
        if banned:
            embed.add_field(name=f"✅ Banned ({len(banned)})", value='\n'.join(banned[:10]), inline=False)
        if failed:
            embed.add_field(name=f"❌ Failed ({len(failed)})", value='\n'.join(failed[:10]), inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="massrole", description="Add/remove role from multiple users")
    @app_commands.describe(
        role="Role to add/remove",
        action="Add or remove",
        members="Members (mention or IDs)"
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    async def massrole(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
        action: Literal['add', 'remove'],
        members: str
    ) -> None:
        """Mass role assignment."""
        await interaction.response.defer(ephemeral=True)
        
        # Parse members
        member_list = []
        for mention in members.split():
            try:
                # Try to extract ID from mention or use as ID directly
                user_id = int(mention.strip('<@!>'))
                member = interaction.guild.get_member(user_id)
                if member:
                    member_list.append(member)
            except:
                pass
        
        success = 0
        failed = 0
        
        for member in member_list:
            try:
                if action == 'add':
                    await member.add_roles(role)
                else:
                    await member.remove_roles(role)
                success += 1
            except:
                failed += 1
        
        embed = discord.Embed(
            title=f"🎭 Mass Role {action.title()}",
            description=f"**Role:** {role.mention}\n**Success:** {success}\n**Failed:** {failed}",
            color=discord.Color.green() if failed == 0 else discord.Color.orange()
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    # === CUSTOM COMMANDS ===
    @app_commands.command(name="customcmd", description="Create custom commands")
    @app_commands.describe(
        trigger="Command trigger (without prefix)",
        response="What the bot should respond"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def customcmd(self, interaction: discord.Interaction, trigger: str, response: str) -> None:
        """Create custom commands."""
        guild_id = interaction.guild_id
        
        if guild_id not in self.custom_commands:
            self.custom_commands[guild_id] = {}
        
        self.custom_commands[guild_id][trigger.lower()] = response
        
        embed = discord.Embed(
            title="✅ Custom Command Created!",
            description=f"**Trigger:** `!{trigger}`\n**Response:** {response}",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed)
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Handle custom commands."""
        if message.author.bot or not message.guild:
            return
        
        if not message.content.startswith('!'):
            return
        
        guild_id = message.guild.id
        if guild_id not in self.custom_commands:
            return
        
        trigger = message.content[1:].split()[0].lower()
        
        if trigger in self.custom_commands[guild_id]:
            response = self.custom_commands[guild_id][trigger]
            await message.reply(response)

class ChannelManagementCog(commands.Cog):
    """Advanced channel creation and management."""
    
    def __init__(self, bot: ModernBot) -> None:
        self.bot = bot
        self.join_to_create = {}  # guild_id: {channel_id, category_id}
        self.temp_channels = {}  # channel_id: owner_id
        self.channel_templates = {}  # guild_id: {name: template_data}
        self.stats_channels = {}  # guild_id: {type: channel_id}
        self.update_stats.start()
    
    def cog_unload(self) -> None:
        self.update_stats.cancel()
    
    # === JOIN TO CREATE ===
    @app_commands.command(name="jointocreate", description="Setup join-to-create voice channels")
    @app_commands.describe(
        category="Category for created channels",
        channel_name="Name of the join-to-create channel"
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    async def jointocreate(
        self,
        interaction: discord.Interaction,
        category: discord.CategoryChannel,
        channel_name: str = "➕ Join to Create"
    ) -> None:
        """Setup join-to-create system."""
        # Create the join channel
        join_channel = await interaction.guild.create_voice_channel(
            name=channel_name,
            category=category
        )
        
        self.join_to_create[interaction.guild_id] = {
            'channel_id': join_channel.id,
            'category_id': category.id
        }
        
        embed = discord.Embed(
            title="✅ Join-to-Create Setup!",
            description=f"When members join {join_channel.mention}, a voice channel will be auto-created for them!",
            color=discord.Color.green()
        )
        embed.add_field(name="📁 Category", value=category.name, inline=True)
        embed.add_field(name="🎙️ Join Channel", value=join_channel.mention, inline=True)
        embed.add_field(
            name="ℹ️ Features",
            value="• Auto-creates private voice channel\n"
                  "• Owner can control channel\n"
                  "• Auto-deletes when empty\n"
                  "• Unlimited channels",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ) -> None:
        """Handle join-to-create and temp channel cleanup."""
        guild_id = member.guild.id
        
        # Join-to-create
        if guild_id in self.join_to_create:
            config = self.join_to_create[guild_id]
            
            # User joined the join-to-create channel
            if after.channel and after.channel.id == config['channel_id']:
                category = self.bot.get_channel(config['category_id'])
                
                if category:
                    # Create personal voice channel
                    overwrites = {
                        member.guild.default_role: discord.PermissionOverwrite(connect=True),
                        member: discord.PermissionOverwrite(
                            connect=True,
                            speak=True,
                            manage_channels=True,
                            move_members=True,
                            mute_members=True,
                            deafen_members=True
                        )
                    }
                    
                    new_channel = await member.guild.create_voice_channel(
                        name=f"{member.display_name}'s Channel",
                        category=category,
                        overwrites=overwrites
                    )
                    
                    self.temp_channels[new_channel.id] = member.id
                    
                    # Move member to their channel
                    await member.move_to(new_channel)
        
        # Cleanup empty temp channels
        if before.channel and before.channel.id in self.temp_channels:
            if len(before.channel.members) == 0:
                try:
                    await before.channel.delete()
                    del self.temp_channels[before.channel.id]
                except:
                    pass
    
    # === TEMPORARY VOICE ===
    @app_commands.command(name="tempvoice", description="Create a temporary voice channel")
    @app_commands.describe(
        name="Channel name",
        user_limit="User limit (0 = unlimited)",
        private="Make channel private"
    )
    async def tempvoice(
        self,
        interaction: discord.Interaction,
        name: str,
        user_limit: int = 0,
        private: bool = False
    ) -> None:
        """Create temporary voice channel."""
        overwrites = None
        
        if private:
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(connect=False),
                interaction.user: discord.PermissionOverwrite(
                    connect=True,
                    manage_channels=True,
                    move_members=True
                )
            }
        
        channel = await interaction.guild.create_voice_channel(
            name=name,
            user_limit=user_limit,
            overwrites=overwrites
        )
        
        self.temp_channels[channel.id] = interaction.user.id
        
        embed = discord.Embed(
            title="✅ Temporary Voice Channel Created!",
            description=f"Created: {channel.mention}",
            color=discord.Color.green()
        )
        embed.add_field(name="Owner", value=interaction.user.mention, inline=True)
        embed.add_field(name="User Limit", value=str(user_limit) if user_limit > 0 else "Unlimited", inline=True)
        embed.add_field(name="Private", value="Yes" if private else "No", inline=True)
        embed.add_field(
            name="⚠️ Note",
            value="Channel will auto-delete when empty!",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    # === CLONE CHANNEL ===
    @app_commands.command(name="clonechannel", description="Clone any channel with all settings")
    @app_commands.describe(
        channel="Channel to clone",
        name="Name for the cloned channel (optional)"
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    async def clonechannel(
        self,
        interaction: discord.Interaction,
        channel: discord.abc.GuildChannel,
        name: Optional[str] = None
    ) -> None:
        """Clone a channel."""
        await interaction.response.defer()
        
        new_name = name or f"{channel.name}-copy"
        
        cloned = await channel.clone(name=new_name, reason=f"Cloned by {interaction.user}")
        
        embed = discord.Embed(
            title="✅ Channel Cloned!",
            description=f"**Original:** {channel.mention}\n**Clone:** {cloned.mention}",
            color=discord.Color.green()
        )
        embed.add_field(
            name="📋 Copied Settings",
            value="• Permissions\n• Category\n• Topic/Description\n• Slowmode\n• NSFW flag",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)
    
    # === CHANNEL TEMPLATES ===
    @app_commands.command(name="savetemplate", description="Save a channel as a template")
    @app_commands.describe(
        channel="Channel to save as template",
        template_name="Name for the template"
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    async def savetemplate(
        self,
        interaction: discord.Interaction,
        channel: discord.abc.GuildChannel,
        template_name: str
    ) -> None:
        """Save channel as template."""
        guild_id = interaction.guild_id
        
        if guild_id not in self.channel_templates:
            self.channel_templates[guild_id] = {}
        
        # Save channel data
        template_data = {
            'type': str(channel.type),
            'name': channel.name,
            'category': channel.category.name if channel.category else None,
            'position': channel.position
        }
        
        # Add type-specific data
        if isinstance(channel, discord.TextChannel):
            template_data['topic'] = channel.topic
            template_data['slowmode'] = channel.slowmode_delay
            template_data['nsfw'] = channel.nsfw
        elif isinstance(channel, discord.VoiceChannel):
            template_data['bitrate'] = channel.bitrate
            template_data['user_limit'] = channel.user_limit
        
        self.channel_templates[guild_id][template_name] = template_data
        
        embed = discord.Embed(
            title="✅ Template Saved!",
            description=f"Template **{template_name}** created from {channel.mention}",
            color=discord.Color.green()
        )
        embed.add_field(name="Use with", value=f"`/loadtemplate {template_name}`", inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="loadtemplate", description="Create channel from template")
    @app_commands.describe(template_name="Name of the template to load")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def loadtemplate(self, interaction: discord.Interaction, template_name: str) -> None:
        """Load and create channel from template."""
        guild_id = interaction.guild_id
        
        if guild_id not in self.channel_templates or template_name not in self.channel_templates[guild_id]:
            await interaction.response.send_message("❌ Template not found!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        template = self.channel_templates[guild_id][template_name]
        
        # Find category if specified
        category = None
        if template.get('category'):
            for cat in interaction.guild.categories:
                if cat.name == template['category']:
                    category = cat
                    break
        
        # Create channel based on type
        if 'text' in template['type']:
            channel = await interaction.guild.create_text_channel(
                name=template['name'],
                topic=template.get('topic'),
                slowmode_delay=template.get('slowmode', 0),
                nsfw=template.get('nsfw', False),
                category=category
            )
        elif 'voice' in template['type']:
            channel = await interaction.guild.create_voice_channel(
                name=template['name'],
                bitrate=template.get('bitrate', 64000),
                user_limit=template.get('user_limit', 0),
                category=category
            )
        else:
            await interaction.followup.send("❌ Unsupported channel type!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="✅ Channel Created from Template!",
            description=f"Created {channel.mention} from template **{template_name}**",
            color=discord.Color.green()
        )
        
        await interaction.followup.send(embed=embed)
    
    # === AUTO CATEGORY ===
    @app_commands.command(name="autocategory", description="Auto-create category when channels are full")
    @app_commands.describe(
        base_name="Base name for categories",
        max_channels="Max channels per category"
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    async def autocategory(
        self,
        interaction: discord.Interaction,
        base_name: str,
        max_channels: int = 50
    ) -> None:
        """Setup auto-category creation."""
        # Create first category
        category = await interaction.guild.create_category(name=f"{base_name} 1")
        
        embed = discord.Embed(
            title="✅ Auto-Category System Setup!",
            description=f"Created category: **{category.name}**",
            color=discord.Color.green()
        )
        embed.add_field(
            name="🔄 How it works",
            value=f"When a category reaches {max_channels} channels, a new one will be auto-created!",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    # === CHANNEL STATS ===
    @app_commands.command(name="channelstats", description="Create live statistics channels")
    @app_commands.describe(
        stat_type="Type of stat to display",
        category="Category for the stats channel"
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    async def channelstats(
        self,
        interaction: discord.Interaction,
        stat_type: Literal['members', 'bots', 'online', 'channels', 'roles', 'boosts'],
        category: Optional[discord.CategoryChannel] = None
    ) -> None:
        """Create live stats channel."""
        await interaction.response.defer()
        
        guild = interaction.guild
        
        # Calculate stat
        stat_names = {
            'members': ('Members', guild.member_count),
            'bots': ('Bots', len([m for m in guild.members if m.bot])),
            'online': ('Online', len([m for m in guild.members if m.status != discord.Status.offline])),
            'channels': ('Channels', len(guild.channels)),
            'roles': ('Roles', len(guild.roles)),
            'boosts': ('Boosts', guild.premium_subscription_count or 0)
        }
        
        name, value = stat_names[stat_type]
        
        # Create voice channel (can't be joined, just displays info)
        channel = await guild.create_voice_channel(
            name=f"📊 {name}: {value}",
            category=category,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(connect=False)
            }
        )
        
        if guild.id not in self.stats_channels:
            self.stats_channels[guild.id] = {}
        
        self.stats_channels[guild.id][stat_type] = channel.id
        
        embed = discord.Embed(
            title="✅ Live Stats Channel Created!",
            description=f"Channel: {channel.mention}\n\nUpdates automatically every 5 minutes!",
            color=discord.Color.green()
        )
        
        await interaction.followup.send(embed=embed)
    
    @tasks.loop(minutes=5)
    async def update_stats(self) -> None:
        """Update stats channels."""
        for guild_id, stats in self.stats_channels.items():
            guild = self.bot.get_guild(guild_id)
            if not guild:
                continue
            
            for stat_type, channel_id in stats.items():
                channel = guild.get_channel(channel_id)
                if not channel:
                    continue
                
                # Calculate new value
                stat_values = {
                    'members': ('Members', guild.member_count),
                    'bots': ('Bots', len([m for m in guild.members if m.bot])),
                    'online': ('Online', len([m for m in guild.members if m.status != discord.Status.offline])),
                    'channels': ('Channels', len(guild.channels)),
                    'roles': ('Roles', len(guild.roles)),
                    'boosts': ('Boosts', guild.premium_subscription_count or 0)
                }
                
                if stat_type in stat_values:
                    name, value = stat_values[stat_type]
                    new_name = f"📊 {name}: {value}"
                    
                    if channel.name != new_name:
                        try:
                            await channel.edit(name=new_name)
                        except:
                            pass
    
    @update_stats.before_loop
    async def before_update_stats(self) -> None:
        await self.bot.wait_until_ready()
    
    # === LOCKDOWN ===
    @app_commands.command(name="lockdown", description="Lock/unlock a channel")
    @app_commands.describe(
        channel="Channel to lock/unlock (current if not specified)",
        action="Lock or unlock"
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lockdown(
        self,
        interaction: discord.Interaction,
        action: Literal['lock', 'unlock'],
        channel: Optional[discord.TextChannel] = None
    ) -> None:
        """Lock or unlock a channel."""
        channel = channel or interaction.channel
        
        if action == 'lock':
            await channel.set_permissions(
                interaction.guild.default_role,
                send_messages=False,
                reason=f"Locked by {interaction.user}"
            )
            
            embed = discord.Embed(
                title="🔒 Channel Locked",
                description=f"{channel.mention} has been locked. Members cannot send messages.",
                color=discord.Color.red()
            )
        else:
            await channel.set_permissions(
                interaction.guild.default_role,
                send_messages=None,
                reason=f"Unlocked by {interaction.user}"
            )
            
            embed = discord.Embed(
                title="🔓 Channel Unlocked",
                description=f"{channel.mention} has been unlocked. Members can send messages again.",
                color=discord.Color.green()
            )
        
        await interaction.response.send_message(embed=embed)
    
    # === NUKE ===
    @app_commands.command(name="nuke", description="Clone channel and delete original (clears all messages)")
    @app_commands.describe(channel="Channel to nuke (current if not specified)")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def nuke(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None) -> None:
        """Nuke a channel (clone and delete)."""
        channel = channel or interaction.channel
        
        # Confirm
        embed = discord.Embed(
            title="⚠️ Confirm Nuke",
            description=f"Are you sure you want to nuke {channel.mention}?\n\n"
                       "This will:\n"
                       "• Delete all messages\n"
                       "• Clone the channel\n"
                       "• Keep all settings",
            color=discord.Color.orange()
        )
        
        class ConfirmView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)
                self.value = None
            
            @discord.ui.button(label="Confirm Nuke", style=discord.ButtonStyle.danger)
            async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.value = True
                self.stop()
            
            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.value = False
                self.stop()
        
        view = ConfirmView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
        await view.wait()
        
        if view.value:
            # Clone and delete
            new_channel = await channel.clone(reason=f"Nuked by {interaction.user}")
            await channel.delete(reason=f"Nuked by {interaction.user}")
            
            embed = discord.Embed(
                title="💥 Channel Nuked!",
                description=f"Channel has been nuked and recreated!\n\nAll messages have been cleared.",
                color=discord.Color.green()
            )
            await new_channel.send(embed=embed)
        else:
            await interaction.edit_original_response(content="❌ Nuke cancelled", embed=None, view=None)

class InsaneFeaturesCog(commands.Cog):
    """Absolutely insane features - reaction roles, auto-purge, anti-raid, leveling, economy."""
    
    def __init__(self, bot: ModernBot) -> None:
        self.bot = bot
        self.reaction_roles = {}  # message_id: {emoji: role_id}
        self.auto_purge = {}  # channel_id: {days, running}
        self.anti_raid = {}  # guild_id: {enabled, threshold, action}
        self.member_levels = defaultdict(lambda: {'xp': 0, 'level': 0, 'messages': 0})
        self.member_economy = defaultdict(lambda: {'balance': 100, 'bank': 0})
        self.join_tracker = defaultdict(list)  # guild_id: [timestamps]
        self.auto_responders = {}  # guild_id: {pattern: response}
        self.purge_tasks = {}
    
    # === REACTION ROLES ===
    @app_commands.command(name="reactionrole", description="Setup reaction roles on any message")
    @app_commands.describe(
        message_id="ID of the message",
        emoji="Emoji to react with",
        role="Role to assign"
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    async def reactionrole(
        self,
        interaction: discord.Interaction,
        message_id: str,
        emoji: str,
        role: discord.Role
    ) -> None:
        """Setup reaction roles."""
        try:
            msg_id = int(message_id)
            message = await interaction.channel.fetch_message(msg_id)
        except:
            await interaction.response.send_message("❌ Invalid message ID!", ephemeral=True)
            return
        
        if msg_id not in self.reaction_roles:
            self.reaction_roles[msg_id] = {}
        
        self.reaction_roles[msg_id][emoji] = role.id
        
        # Add reaction to message
        try:
            await message.add_reaction(emoji)
        except:
            pass
        
        embed = discord.Embed(
            title="✅ Reaction Role Added!",
            description=f"React with {emoji} on [this message]({message.jump_url}) to get {role.mention}",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed)
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        """Handle reaction role assignment."""
        if payload.user_id == self.bot.user.id:
            return
        
        if payload.message_id not in self.reaction_roles:
            return
        
        emoji_str = str(payload.emoji)
        if emoji_str not in self.reaction_roles[payload.message_id]:
            return
        
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        
        role_id = self.reaction_roles[payload.message_id][emoji_str]
        role = guild.get_role(role_id)
        member = guild.get_member(payload.user_id)
        
        if role and member:
            try:
                await member.add_roles(role, reason="Reaction role")
            except:
                pass
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent) -> None:
        """Handle reaction role removal."""
        if payload.user_id == self.bot.user.id:
            return
        
        if payload.message_id not in self.reaction_roles:
            return
        
        emoji_str = str(payload.emoji)
        if emoji_str not in self.reaction_roles[payload.message_id]:
            return
        
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        
        role_id = self.reaction_roles[payload.message_id][emoji_str]
        role = guild.get_role(role_id)
        member = guild.get_member(payload.user_id)
        
        if role and member:
            try:
                await member.remove_roles(role, reason="Reaction role removed")
            except:
                pass
    
    # === AUTO PURGE ===
    @app_commands.command(name="autopurge", description="Auto-delete messages older than X days")
    @app_commands.describe(
        channel="Channel to auto-purge",
        days="Delete messages older than X days",
        interval_hours="Check interval in hours (default: 24)"
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def autopurge(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        days: int,
        interval_hours: int = 24
    ) -> None:
        """Setup auto-purge for old messages."""
        self.auto_purge[channel.id] = {
            'days': days,
            'interval': interval_hours,
            'running': True
        }
        
        embed = discord.Embed(
            title="✅ Auto-Purge Configured!",
            description=f"Messages older than **{days} days** in {channel.mention} will be auto-deleted.",
            color=discord.Color.green()
        )
        embed.add_field(name="Check Interval", value=f"Every {interval_hours} hours", inline=True)
        embed.add_field(name="Status", value="🟢 Active", inline=True)
        
        await interaction.response.send_message(embed=embed)
        
        # Start purge task
        self.bot.loop.create_task(self.purge_task(channel.id))
    
    async def purge_task(self, channel_id: int) -> None:
        """Background task to purge old messages."""
        while channel_id in self.auto_purge and self.auto_purge[channel_id]['running']:
            try:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    days = self.auto_purge[channel_id]['days']
                    cutoff = discord.utils.utcnow() - timedelta(days=days)
                    
                    deleted = 0
                    async for message in channel.history(limit=None, after=cutoff):
                        if message.created_at < cutoff:
                            try:
                                await message.delete()
                                deleted += 1
                            except:
                                pass
                    
                    if deleted > 0:
                        logger.info(f"Auto-purged {deleted} messages from {channel.name}")
                
                # Wait for interval
                interval = self.auto_purge[channel_id]['interval']
                await asyncio.sleep(interval * 3600)
            except Exception as e:
                logger.error(f"Auto-purge error: {e}")
                break
    
    # === ANTI-RAID PROTECTION ===
    @app_commands.command(name="antiraid", description="Configure anti-raid protection")
    @app_commands.describe(
        enabled="Enable or disable",
        threshold="Max joins per minute before triggering",
        action="Action to take on raid detection"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def antiraid(
        self,
        interaction: discord.Interaction,
        enabled: bool,
        threshold: int = 5,
        action: Literal['kick', 'ban', 'alert'] = 'alert'
    ) -> None:
        """Configure anti-raid system."""
        self.anti_raid[interaction.guild_id] = {
            'enabled': enabled,
            'threshold': threshold,
            'action': action
        }
        
        embed = discord.Embed(
            title="🛡️ Anti-Raid Protection",
            color=discord.Color.green() if enabled else discord.Color.red()
        )
        embed.add_field(name="Status", value="🟢 Enabled" if enabled else "🔴 Disabled", inline=True)
        embed.add_field(name="Threshold", value=f"{threshold} joins/min", inline=True)
        embed.add_field(name="Action", value=action.title(), inline=True)
        embed.add_field(
            name="ℹ️ How it works",
            value=f"If more than {threshold} members join within 1 minute, the bot will {action} them.",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Track joins for anti-raid."""
        guild_id = member.guild.id
        
        if guild_id not in self.anti_raid or not self.anti_raid[guild_id]['enabled']:
            return
        
        now = discord.utils.utcnow()
        self.join_tracker[guild_id].append(now)
        
        # Remove old timestamps (older than 1 minute)
        cutoff = now - timedelta(minutes=1)
        self.join_tracker[guild_id] = [t for t in self.join_tracker[guild_id] if t > cutoff]
        
        # Check if threshold exceeded
        threshold = self.anti_raid[guild_id]['threshold']
        if len(self.join_tracker[guild_id]) > threshold:
            action = self.anti_raid[guild_id]['action']
            
            if action == 'kick':
                try:
                    await member.kick(reason="Anti-raid protection")
                except:
                    pass
            elif action == 'ban':
                try:
                    await member.ban(reason="Anti-raid protection")
                except:
                    pass
            elif action == 'alert':
                # Try to notify admins
                for channel in member.guild.text_channels:
                    if channel.permissions_for(member.guild.me).send_messages:
                        embed = discord.Embed(
                            title="🚨 Possible Raid Detected!",
                            description=f"**{len(self.join_tracker[guild_id])}** members joined in the last minute!",
                            color=discord.Color.red(),
                            timestamp=discord.utils.utcnow()
                        )
                        embed.add_field(name="Latest Join", value=member.mention, inline=True)
                        await channel.send(embed=embed)
                        break
    
    # === LEVELING SYSTEM ===
    @app_commands.command(name="rank", description="Check your rank and level")
    @app_commands.describe(member="Member to check (optional)")
    async def rank(self, interaction: discord.Interaction, member: Optional[discord.Member] = None) -> None:
        """Check member rank."""
        member = member or interaction.user
        data = self.member_levels[member.id]
        
        # Calculate level from XP
        xp = data['xp']
        level = data['level']
        xp_for_next = (level + 1) * 100
        
        embed = discord.Embed(
            title=f"📊 Rank - {member.display_name}",
            color=member.color
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        embed.add_field(name="🎯 Level", value=str(level), inline=True)
        embed.add_field(name="⭐ XP", value=f"{xp}/{xp_for_next}", inline=True)
        embed.add_field(name="💬 Messages", value=str(data['messages']), inline=True)
        
        # Progress bar
        progress = int((xp / xp_for_next) * 20)
        bar = "█" * progress + "░" * (20 - progress)
        embed.add_field(name="Progress", value=f"`{bar}` {int((xp/xp_for_next)*100)}%", inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="leaderboard", description="Show server leaderboard")
    @app_commands.describe(board_type="Type of leaderboard")
    async def leaderboard(
        self,
        interaction: discord.Interaction,
        board_type: Literal['level', 'messages', 'balance'] = 'level'
    ) -> None:
        """Show leaderboard."""
        guild = interaction.guild
        
        if board_type in ['level', 'messages']:
            sorted_members = sorted(
                [(uid, data) for uid, data in self.member_levels.items()],
                key=lambda x: x[1][board_type if board_type == 'level' else 'messages'],
                reverse=True
            )[:10]
            
            embed = discord.Embed(
                title=f"🏆 Top 10 - {board_type.title()}",
                color=discord.Color.gold()
            )
            
            for i, (user_id, data) in enumerate(sorted_members, 1):
                member = guild.get_member(user_id)
                if member:
                    value = data['level'] if board_type == 'level' else data['messages']
                    medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"#{i}"
                    embed.add_field(
                        name=f"{medal} {member.display_name}",
                        value=f"Level {data['level']}" if board_type == 'level' else f"{data['messages']} messages",
                        inline=False
                    )
        
        else:  # balance
            sorted_members = sorted(
                [(uid, data) for uid, data in self.member_economy.items()],
                key=lambda x: x[1]['balance'] + x[1]['bank'],
                reverse=True
            )[:10]
            
            embed = discord.Embed(
                title="🏆 Top 10 - Richest",
                color=discord.Color.gold()
            )
            
            for i, (user_id, data) in enumerate(sorted_members, 1):
                member = guild.get_member(user_id)
                if member:
                    total = data['balance'] + data['bank']
                    medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"#{i}"
                    embed.add_field(
                        name=f"{medal} {member.display_name}",
                        value=f"💰 ${total:,}",
                        inline=False
                    )
        
        await interaction.response.send_message(embed=embed)
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Award XP for messages."""
        if message.author.bot or not message.guild:
            return
        
        user_id = message.author.id
        data = self.member_levels[user_id]
        
        # Award XP (5-15 per message)
        import random
        xp_gain = random.randint(5, 15)
        data['xp'] += xp_gain
        data['messages'] += 1
        
        # Check for level up
        xp_needed = (data['level'] + 1) * 100
        if data['xp'] >= xp_needed:
            data['level'] += 1
            data['xp'] = 0
            
            # Level up message
            embed = discord.Embed(
                title="🎉 Level Up!",
                description=f"{message.author.mention} reached **Level {data['level']}**!",
                color=discord.Color.gold()
            )
            try:
                await message.reply(embed=embed, mention_author=False)
            except:
                pass
    
    # === ECONOMY SYSTEM ===
    @app_commands.command(name="balance", description="Check your balance")
    @app_commands.describe(member="Member to check")
    async def balance(self, interaction: discord.Interaction, member: Optional[discord.Member] = None) -> None:
        """Check balance."""
        member = member or interaction.user
        data = self.member_economy[member.id]
        
        embed = discord.Embed(
            title=f"💰 {member.display_name}'s Balance",
            color=discord.Color.gold()
        )
        embed.add_field(name="💵 Cash", value=f"${data['balance']:,}", inline=True)
        embed.add_field(name="🏦 Bank", value=f"${data['bank']:,}", inline=True)
        embed.add_field(name="💎 Total", value=f"${data['balance'] + data['bank']:,}", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="daily", description="Claim your daily reward")
    async def daily(self, interaction: discord.Interaction) -> None:
        """Daily reward."""
        data = self.member_economy[interaction.user.id]
        
        import random
        reward = random.randint(100, 500)
        data['balance'] += reward
        
        embed = discord.Embed(
            title="🎁 Daily Reward!",
            description=f"You received **${reward:,}**!",
            color=discord.Color.green()
        )
        embed.add_field(name="New Balance", value=f"${data['balance']:,}", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="pay", description="Pay another user")
    @app_commands.describe(member="Member to pay", amount="Amount to pay")
    async def pay(self, interaction: discord.Interaction, member: discord.Member, amount: int) -> None:
        """Pay another user."""
        if member.bot:
            await interaction.response.send_message("❌ You can't pay bots!", ephemeral=True)
            return
        
        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
            return
        
        sender_data = self.member_economy[interaction.user.id]
        
        if sender_data['balance'] < amount:
            await interaction.response.send_message("❌ Insufficient balance!", ephemeral=True)
            return
        
        receiver_data = self.member_economy[member.id]
        
        sender_data['balance'] -= amount
        receiver_data['balance'] += amount
        
        embed = discord.Embed(
            title="💸 Payment Sent!",
            description=f"{interaction.user.mention} paid {member.mention} **${amount:,}**",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed)
    
    # === MESSAGE COMMANDS ===
    @app_commands.command(name="slowmode", description="Set slowmode with auto-adjust")
    @app_commands.describe(
        delay="Slowmode delay in seconds (0 to disable)",
        auto_adjust="Auto-adjust based on activity"
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode(
        self,
        interaction: discord.Interaction,
        delay: int,
        auto_adjust: bool = False
    ) -> None:
        """Set slowmode."""
        await interaction.channel.edit(slowmode_delay=delay)
        
        embed = discord.Embed(
            title="⏱️ Slowmode Updated",
            description=f"Slowmode set to **{delay} seconds**" if delay > 0 else "Slowmode disabled",
            color=discord.Color.blue()
        )
        
        if auto_adjust:
            embed.add_field(
                name="🔄 Auto-Adjust Enabled",
                value="Slowmode will automatically adjust based on channel activity",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="roleall", description="Give role to all members")
    @app_commands.describe(
        role="Role to assign",
        filter_type="Filter members"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def roleall(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
        filter_type: Literal['all', 'humans', 'bots'] = 'all'
    ) -> None:
        """Give role to all members."""
        await interaction.response.defer()
        
        members = interaction.guild.members
        
        if filter_type == 'humans':
            members = [m for m in members if not m.bot]
        elif filter_type == 'bots':
            members = [m for m in members if m.bot]
        
        success = 0
        failed = 0
        
        for member in members:
            if role not in member.roles:
                try:
                    await member.add_roles(role, reason=f"Role all by {interaction.user}")
                    success += 1
                except:
                    failed += 1
        
        embed = discord.Embed(
            title="✅ Mass Role Assignment Complete",
            description=f"Assigned {role.mention} to members",
            color=discord.Color.green()
        )
        embed.add_field(name="✅ Success", value=str(success), inline=True)
        embed.add_field(name="❌ Failed", value=str(failed), inline=True)
        embed.add_field(name="📊 Total", value=str(len(members)), inline=True)
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="clearroles", description="Remove all roles from a user")
    @app_commands.describe(member="Member to clear roles from")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def clearroles(self, interaction: discord.Interaction, member: discord.Member) -> None:
        """Clear all roles from a member."""
        await interaction.response.defer()
        
        roles_to_remove = [r for r in member.roles if r.name != '@everyone' and not r.managed]
        
        try:
            await member.remove_roles(*roles_to_remove, reason=f"Cleared by {interaction.user}")
            
            embed = discord.Embed(
                title="✅ Roles Cleared",
                description=f"Removed **{len(roles_to_remove)}** roles from {member.mention}",
                color=discord.Color.green()
            )
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

if __name__ == "__main__":
    bot = ModernBot()
    bot.run(TOKEN, log_handler=None)  # We're using our own logging
