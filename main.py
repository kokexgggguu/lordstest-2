import discord
from discord.ext import commands, tasks
import asyncio
import os
import json
import logging
from datetime import datetime, timedelta
import pytz
from bot.commands import setup_commands
from bot.match_manager import MatchManager
from bot.utils import load_data, save_data
from keep_alive import keep_alive, start_self_ping

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class DiscordBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)
        self.match_manager = MatchManager(self)
        self.settings = load_data('data/settings.json', {
            'allowed_channels': [],
            'log_channel': None,
            'admin_roles': []
        })
        
    async def on_ready(self):
        logger.info(f'🔥 {self.user} has connected to Discord!')
        logger.info(f'🌍 Connected to {len(self.guilds)} guilds')
        total_members = sum(guild.member_count or 0 for guild in self.guilds)
        logger.info(f'👥 Serving {total_members} members')
        
        await self.tree.sync()
        logger.info('⚡ Slash commands synced!')
        
        # Set bot status to online and active
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="🏆 Managing matches | /create_match"
            )
        )
        
        # Start the match reminder task
        self.check_matches.start()
        logger.info('🔥 Discord Bot is now ONLINE and READY! 🚀')
        
    async def on_message(self, message):
        # Log bot messages to designated channel
        if message.author == self.user and self.settings.get('log_channel'):
            try:
                log_channel = self.get_channel(self.settings['log_channel'])
                if log_channel and isinstance(log_channel, discord.TextChannel) and message.channel.id != self.settings['log_channel']:
                    embed = discord.Embed(
                        title="🤖 Bot Activity",
                        description=f"Bot sent a message in {message.channel.mention}",
                        color=0x00ff00,
                        timestamp=datetime.utcnow()
                    )
                    embed.add_field(name="Content", value=message.content[:1000] if message.content else "Embed message", inline=False)
                    await log_channel.send(embed=embed)
            except Exception as e:
                logger.error(f"Error logging bot activity: {e}")
        
        await self.process_commands(message)
    
    @tasks.loop(minutes=1)
    async def check_matches(self):
        """Check for matches that need reminders or are starting soon"""
        await self.match_manager.check_match_reminders()
    
    @check_matches.before_loop
    async def before_check_matches(self):
        await self.wait_until_ready()

# Initialize bot
bot = DiscordBot()

# Setup commands
setup_commands(bot)

if __name__ == "__main__":
    # Start keep-alive system
    logger.info("🔥 Starting Discord Bot with Keep-Alive system...")
    keep_alive()
    start_self_ping()
    
    # Get bot token from environment
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        logger.error("DISCORD_BOT_TOKEN environment variable not set!")
        exit(1)
    
    logger.info("🚀 Bot is ready to launch! Keep-Alive system active!")
    # Run the bot
    bot.run(token)
