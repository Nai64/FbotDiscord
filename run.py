"""
Run both the Discord bot and web dashboard together.
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def main():
    """Run bot and dashboard concurrently."""
    from bot import ModernBot, TOKEN
    from dashboard import run_dashboard
    
    # Initialize bot
    bot = ModernBot()
    
    # Create tasks
    bot_task = asyncio.create_task(bot.start(TOKEN))
    dashboard_task = asyncio.create_task(run_dashboard(bot))
    
    # Run both concurrently
    await asyncio.gather(bot_task, dashboard_task)

if __name__ == "__main__":
    print("🚀 Starting FbotDiscord with Web Dashboard...")
    print("=" * 50)
    asyncio.run(main())
