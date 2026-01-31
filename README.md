# 🤖 FbotDiscord - Ultimate Discord Bot

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Discord.py](https://img.shields.io/badge/Discord.py-2.0+-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discordpy.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)](https://github.com)

> **A modern, feature-rich Discord bot with 100+ commands, advanced automation, and comprehensive server management tools.**

---

## ✨ Features Overview

### 🎯 **Core Features**
- ✅ **Modern Slash Commands** - All commands use Discord's native `/` command system
- ✅ **Hybrid Commands** - Support for both `/` and `!` prefix commands
- ✅ **Interactive UI** - Buttons, dropdowns, modals, and context menus
- ✅ **Auto-Logging** - Comprehensive event tracking and logging
- ✅ **Auto-Moderation** - Built-in moderation rules and actions
- ✅ **Channel Automation** - Join-to-create, temp channels, stats channels
- ✅ **Custom Commands** - Create your own server-specific commands
- ✅ **Advanced Analytics** - Real-time server statistics and insights

---

## 📋 Command Categories

### 👤 User Information
| Command | Description |
|---------|-------------|
| `/userinfo` | Get **MAXIMUM** detailed user information with interactive buttons |
| `/whois` | Quick user lookup with essential info |
| `/avatar` | Get user avatars in all sizes and formats |
| `/banner` | View user or server banners |
| `/membertrack` | Complete member tracking profile with all data |

### 🛠️ Utility Commands
| Command | Description |
|---------|-------------|
| `/help` | Show all available commands |
| `/ping` | Check bot latency |
| `/serverinfo` | Detailed server information |
| `/serveranalytics` | Advanced server analytics with breakdowns |
| `/activity` | Server activity heatmap with status distribution |
| `/membercount` | Visual member count with progress bars |

### 🚀 Advanced Features
| Command | Description |
|---------|-------------|
| `/snipe` | See the last deleted message in channel |
| `/editsnipe` | See before/after of edited messages |
| `/poll` | Create interactive polls with reactions |
| `/rolemenu` | Create button-based role selection menus |

### 🔍 Tracking & Logging
| Command | Description |
|---------|-------------|
| `/setuplogchannels` | Auto-create all logging channels in one command |
| `/setlog` | Configure logging for specific event types |
| `/tracking` | View detailed user activity tracking |
| `/serverstats` | Live server statistics |
| `/auditlog` | View recent audit log entries |

### 🤖 Automations
| Command | Description |
|---------|-------------|
| `/autowelcome` | Setup automatic welcome messages for new members |
| `/autorole` | Auto-assign roles when members join |
| `/autoresponse` | Create auto-replies to keywords |
| `/automod` | Configure auto-moderation rules |

### ✨ Modern Interactions
| Command | Description |
|---------|-------------|
| `/embed` | Interactive embed builder with modal form |
| `/dropdown` | Create dropdown role selection menus |
| `/giveaway` | Start interactive giveaways with button entries |
| `/verify` | Setup verification system with buttons |
| `/ticket` | Create support ticket system |

### 🌟 Super Advanced
| Command | Description |
|---------|-------------|
| `/starboard` | Setup starboard for popular messages (⭐ reactions) |
| `/setupsuggestions` | Configure suggestion system |
| `/suggest` | Submit suggestions with voting |
| `/remind` | Set personal reminders |
| `/transcript` | Export channel message history (text/JSON) |
| `/schedule` | Schedule messages to send later |
| `/backup` | Backup server settings and structure |
| `/massban` | Ban multiple users at once |
| `/massrole` | Add/remove roles from multiple users |
| `/customcmd` | Create custom server commands |

### 📺 Channel Management
| Command | Description |
|---------|-------------|
| `/jointocreate` | Setup join-to-create voice channels |
| `/tempvoice` | Create temporary voice channels |
| `/clonechannel` | Clone any channel with all settings |
| `/savetemplate` | Save channel as reusable template |
| `/loadtemplate` | Create channel from saved template |
| `/channelstats` | Create live statistics channels |
| `/lockdown` | Lock/unlock channels instantly |
| `/nuke` | Clone and delete channel (clear all messages) |
| `/autocategory` | Setup auto-category creation |

---

## 🎨 Auto-Logging Events

The bot automatically logs **EVERYTHING** happening in your server:

### 👥 Member Events
- Member joins (with account age, member #)
- Member leaves (with time in server, roles)
- Nickname changes
- Role changes (added/removed)
- Timeouts applied/removed

### 💬 Message Events
- Deleted messages (content + attachments)
- Edited messages (before/after)
- Bulk message deletes
- Message count per user

### 🎙️ Voice Events
- Voice channel joins/leaves
- Channel switches
- Started/stopped streaming
- Mute/unmute, deafen/undeafen

### 🎭 Role Events
- Role created/deleted
- Role updates
- Role color/permission changes

### 📺 Channel Events
- Channel created/deleted
- Channel name/topic changes
- Permission updates

### 🔨 Moderation Events
- Bans/unbans (with reason and moderator)
- Kicks
- Timeouts

### ⚙️ Server Events
- Server name/icon/banner changes
- Boost level ups
- Emoji/sticker added/removed
- Invite created/deleted
- Thread created/deleted

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- Discord Bot Token ([Get one here](https://discord.com/developers/applications))
- Required Intents: `Members`, `Presences`, `Message Content`

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/FbotDiscord.git
   cd FbotDiscord
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   - Copy `.env.example` to `.env`
   - Add your Discord bot token:
   ```env
   DISCORD_TOKEN=your_bot_token_here
   ```

4. **Run the bot**
   ```bash
   python bot.py
   ```

---

## ⚙️ Configuration

### Setting Up Logging

**Quick Setup (Recommended):**
```
/setuplogchannels separate
```
This creates 7 dedicated log channels:
- 👥-member-logs
- 💬-message-logs
- 🎙️-voice-logs
- 🎭-role-logs
- 📺-channel-logs
- 🔨-moderation-logs
- ⚙️-server-logs

**Single Channel:**
```
/setuplogchannels single
```
All events go to one channel.

**Manual Setup:**
```
/setlog all #logs
```

### Setting Up Automation

**Welcome Messages:**
```
/autowelcome #welcome-channel "Welcome {user} to {server}! 🎉"
```

**Auto-Roles:**
```
/autorole @Member
```

**Auto-Responses:**
```
/autoresponse "hello" "Hi there! 👋"
```

---

## 🎮 Advanced Features Guide

### Join-to-Create Voice Channels
Perfect for gaming communities!

1. Create a category for voice channels
2. Run: `/jointocreate category:VoiceChannels`
3. When users join "➕ Join to Create", they get their own channel
4. Channel auto-deletes when empty

### Starboard System
Highlight popular messages!

1. Run: `/starboard #starboard 3`
2. Messages with 3+ ⭐ reactions appear in starboard
3. Automatic reposting with jump links

### Ticket System
Professional support system!

1. Create a "Tickets" category
2. Run: `/ticket category:Tickets`
3. Users click button to create private support channel
4. Auto-permissions setup

### Channel Stats
Live server statistics!

```
/channelstats members
/channelstats online
/channelstats boosts
```
Creates voice channels that update every 5 minutes.

---

## 📊 Data Storage

- **config.json** - Logging channel configurations
- **In-memory** - User activity tracking, reminders, scheduled messages
- **Auto-save** - Configuration persists between restarts

---

## 🔐 Required Permissions

### Bot Permissions
- `Administrator` (recommended) or:
  - Manage Channels
  - Manage Roles
  - Manage Messages
  - Manage Webhooks
  - Ban Members
  - Kick Members
  - Moderate Members
  - View Audit Log
  - Read Messages/View Channels
  - Send Messages
  - Embed Links
  - Attach Files
  - Read Message History
  - Add Reactions
  - Connect (voice)
  - Move Members

### Required Intents
Enable in Discord Developer Portal → Bot → Privileged Gateway Intents:
- ✅ Presence Intent
- ✅ Server Members Intent
- ✅ Message Content Intent

---

## 📦 Dependencies

```txt
discord.py>=2.0.0
python-dotenv>=1.0.0
```

All dependencies are listed in `requirements.txt`.

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 🐛 Bug Reports & Feature Requests

Found a bug or have an idea? [Open an issue](https://github.com/yourusername/FbotDiscord/issues)!

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🌟 Features Highlights

### 🎯 Why Choose FbotDiscord?

✅ **100+ Commands** - Everything you need in one bot  
✅ **Modern UI** - Buttons, dropdowns, modals, embeds  
✅ **Comprehensive Logging** - Never miss an event  
✅ **Channel Automation** - Dynamic voice channels, auto-stats  
✅ **Advanced Tracking** - Full user analytics and insights  
✅ **Production Ready** - Error handling, logging, type hints  
✅ **Constantly Updated** - Modern Discord.py features  
✅ **Easy Setup** - One command logging setup  

---

## 💡 Usage Examples

### Create a Complete Server Setup
```
1. /setuplogchannels separate
2. /autowelcome #welcome "Welcome {user}!"
3. /autorole @Member
4. /jointocreate category:Voice
5. /channelstats members
6. /starboard #starboard 3
7. /ticket category:Support
```

### Moderate Your Server
```
/lockdown lock
/massban 123456789 987654321 reason:"Spam"
/auditlog 25
/transcript 500
```

### Engage Your Community
```
/poll "What should we add?" option1:"Games" option2:"Music"
/giveaway prize:"Nitro" duration:1440 winners:3
/suggest "Add a gaming category"
```

---

## 📞 Support

Need help? Join our support server: [Discord Server Link](#)

Or DM the developer: `YourUsername#0000`

---

## 🙏 Acknowledgments

- Built with [discord.py](https://github.com/Rapptz/discord.py)
- Inspired by modern Discord bot best practices
- Thanks to all contributors!

---

## ⚡ Performance

- **Fast Response Time** - Optimized command handling
- **Efficient Logging** - Async operations for all events
- **Memory Optimized** - Smart caching and cleanup
- **Scalable** - Works for servers of any size

---

<div align="center">

### Made with ❤️ by [YourName]

**[⭐ Star this repo](https://github.com/yourusername/FbotDiscord)** • **[🐛 Report Bug](https://github.com/yourusername/FbotDiscord/issues)** • **[✨ Request Feature](https://github.com/yourusername/FbotDiscord/issues)**

</div>

---

## 📸 Screenshots

### User Info Command
![User Info](screenshots/userinfo.png)

### Logging System
![Logging](screenshots/logging.png)

### Interactive Embeds
![Embeds](screenshots/embeds.png)

*Add screenshots in `/screenshots` folder*

---

## 🔮 Roadmap

- [ ] Dashboard web interface
- [ ] Database integration (PostgreSQL)
- [ ] Music commands
- [ ] Economy system
- [ ] Leveling system
- [ ] Custom embeds designer
- [ ] Multi-language support

---

**⚠️ Disclaimer:** This bot is provided as-is. Always test in a development server before deploying to production.

**🔒 Security:** Never share your bot token. Add `.env` to `.gitignore`.

**📜 Terms:** By using this bot, you agree to comply with Discord's Terms of Service.
