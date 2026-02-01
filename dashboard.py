"""
FbotDiscord Web Dashboard
Modern web interface with Discord OAuth2, live stats, and server management.
"""

import os
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from quart import Quart, render_template, redirect, url_for, session, request, jsonify
from quart_discord import DiscordOAuth2Session, requires_authorization, Unauthorized
import discord
from discord.ext import commands
from collections import defaultdict

# Dashboard configuration
app = Quart(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
app.config["DISCORD_CLIENT_ID"] = os.getenv("DISCORD_CLIENT_ID")
app.config["DISCORD_CLIENT_SECRET"] = os.getenv("DISCORD_CLIENT_SECRET")
app.config["DISCORD_REDIRECT_URI"] = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:5000/callback")
app.config["DISCORD_BOT_TOKEN"] = os.getenv("DISCORD_TOKEN")

discord_oauth = DiscordOAuth2Session(app)

# Global bot instance (will be set by main bot)
bot_instance: Optional[commands.Bot] = None

def set_bot_instance(bot: commands.Bot):
    """Set the bot instance for the dashboard."""
    global bot_instance
    bot_instance = bot

@app.route("/")
async def index():
    """Home page."""
    if await discord_oauth.authorized:
        user = await discord_oauth.fetch_user()
        return await render_template("index.html", user=user, bot=bot_instance)
    return await render_template("landing.html", bot=bot_instance)

@app.route("/login")
async def login():
    """Initiate Discord OAuth2 login."""
    return await discord_oauth.create_session(scope=["identify", "guilds"])

@app.route("/callback")
async def callback():
    """OAuth2 callback."""
    try:
        await discord_oauth.callback()
        return redirect(url_for("dashboard"))
    except Exception as e:
        return f"Error during OAuth: {str(e)}", 400

@app.route("/logout")
async def logout():
    """Logout user."""
    discord_oauth.revoke()
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
@requires_authorization
async def dashboard():
    """Main dashboard page."""
    user = await discord_oauth.fetch_user()
    guilds = await discord_oauth.fetch_guilds()
    
    # Filter guilds where bot is present
    bot_guilds = [g for g in guilds if bot_instance and bot_instance.get_guild(int(g.id))]
    
    return await render_template("dashboard.html", user=user, guilds=bot_guilds, bot=bot_instance)

@app.route("/server/<int:guild_id>")
@requires_authorization
async def server_dashboard(guild_id: int):
    """Server-specific dashboard."""
    user = await discord_oauth.fetch_user()
    guilds = await discord_oauth.fetch_guilds()
    
    # Check if user has access to this guild
    if not any(g.id == str(guild_id) for g in guilds):
        return "Access Denied", 403
    
    guild = bot_instance.get_guild(guild_id) if bot_instance else None
    if not guild:
        return "Bot not in this server", 404
    
    return await render_template("server.html", user=user, guild=guild, bot=bot_instance)

@app.route("/api/stats")
@requires_authorization
async def api_stats():
    """Get bot statistics."""
    if not bot_instance:
        return jsonify({"error": "Bot not connected"}), 503
    
    stats = {
        "guilds": len(bot_instance.guilds),
        "users": sum(g.member_count for g in bot_instance.guilds),
        "channels": sum(len(g.channels) for g in bot_instance.guilds),
        "commands": len(bot_instance.tree.get_commands()),
        "latency": round(bot_instance.latency * 1000, 2),
        "uptime": str(datetime.utcnow() - bot_instance.start_time) if hasattr(bot_instance, 'start_time') else "Unknown"
    }
    
    return jsonify(stats)

@app.route("/api/server/<int:guild_id>/stats")
@requires_authorization
async def api_server_stats(guild_id: int):
    """Get server statistics."""
    guild = bot_instance.get_guild(guild_id) if bot_instance else None
    if not guild:
        return jsonify({"error": "Server not found"}), 404
    
    # Count by status
    online = sum(1 for m in guild.members if m.status == discord.Status.online)
    idle = sum(1 for m in guild.members if m.status == discord.Status.idle)
    dnd = sum(1 for m in guild.members if m.status == discord.Status.dnd)
    offline = sum(1 for m in guild.members if m.status == discord.Status.offline)
    
    stats = {
        "name": guild.name,
        "icon": str(guild.icon.url) if guild.icon else None,
        "members": {
            "total": guild.member_count,
            "online": online,
            "idle": idle,
            "dnd": dnd,
            "offline": offline,
            "bots": sum(1 for m in guild.members if m.bot),
            "humans": sum(1 for m in guild.members if not m.bot)
        },
        "channels": {
            "total": len(guild.channels),
            "text": len(guild.text_channels),
            "voice": len(guild.voice_channels),
            "categories": len(guild.categories)
        },
        "roles": len(guild.roles),
        "emojis": len(guild.emojis),
        "boosts": guild.premium_subscription_count,
        "boost_level": guild.premium_tier,
        "created_at": guild.created_at.isoformat()
    }
    
    return jsonify(stats)

@app.route("/api/server/<int:guild_id>/members")
@requires_authorization
async def api_server_members(guild_id: int):
    """Get server members list."""
    guild = bot_instance.get_guild(guild_id) if bot_instance else None
    if not guild:
        return jsonify({"error": "Server not found"}), 404
    
    # Limit to 100 members for performance
    members = []
    for member in list(guild.members)[:100]:
        members.append({
            "id": member.id,
            "name": member.name,
            "display_name": member.display_name,
            "avatar": str(member.display_avatar.url),
            "status": str(member.status),
            "bot": member.bot,
            "joined_at": member.joined_at.isoformat() if member.joined_at else None,
            "roles": [{"id": r.id, "name": r.name, "color": str(r.color)} for r in member.roles if r.name != "@everyone"]
        })
    
    return jsonify({"members": members, "total": guild.member_count})

@app.route("/api/server/<int:guild_id>/config", methods=["GET", "POST"])
@requires_authorization
async def api_server_config(guild_id: int):
    """Get or update server configuration."""
    if request.method == "GET":
        # Get current config
        config = bot_instance.config.get(str(guild_id), {}) if bot_instance else {}
        return jsonify(config)
    
    elif request.method == "POST":
        # Update config
        data = await request.get_json()
        if bot_instance and hasattr(bot_instance, 'config'):
            if str(guild_id) not in bot_instance.config:
                bot_instance.config[str(guild_id)] = {}
            
            bot_instance.config[str(guild_id)].update(data)
            bot_instance.save_config()
            
            return jsonify({"success": True, "message": "Configuration updated"})
        
        return jsonify({"error": "Bot not available"}), 503

@app.route("/api/server/<int:guild_id>/logs")
@requires_authorization
async def api_server_logs(guild_id: int):
    """Get recent logs for a server."""
    # This would require storing logs in memory or database
    # For now, return mock data
    logs = [
        {
            "type": "member_join",
            "user": "TestUser#1234",
            "timestamp": datetime.utcnow().isoformat(),
            "details": "Member joined the server"
        }
    ]
    
    return jsonify({"logs": logs})

@app.errorhandler(Unauthorized)
async def redirect_unauthorized(e):
    """Redirect unauthorized users to login."""
    return redirect(url_for("login"))

@app.errorhandler(404)
async def not_found(e):
    """404 error handler."""
    return await render_template("404.html"), 404

@app.errorhandler(500)
async def internal_error(e):
    """500 error handler."""
    return await render_template("500.html"), 500

def run_dashboard(bot: commands.Bot, host: str = "0.0.0.0", port: int = 5000):
    """Run the dashboard server."""
    set_bot_instance(bot)
    bot.start_time = datetime.utcnow()
    
    from hypercorn.asyncio import serve
    from hypercorn.config import Config
    
    config = Config()
    config.bind = [f"{host}:{port}"]
    config.use_reloader = False
    
    print(f"🌐 Dashboard starting on http://{host}:{port}")
    print(f"📝 Login URL: http://localhost:{port}/login")
    
    return serve(app, config)
