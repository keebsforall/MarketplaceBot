import discord
import logging
from typing import List
from config import ProductListing, Config
import asyncio

class DiscordNotifier:
    """Handles Discord notification logic."""
    
    def __init__(self, config: Config):
        """Initialize the Discord notifier with configuration."""
        self.config = config
        # Create minimal intents needed for basic functionality
        intents = discord.Intents.default()
        intents.guilds = True  # Required to see servers
        # We don't actually need message_content or guild_members for basic notifications
        
        self.client = discord.Client(intents=intents)
        self._ready = asyncio.Event()
        
        @self.client.event
        async def on_ready():
            """Event handler for when Discord client is ready."""
            logging.info(f'Connected to Discord as {self.client.user}')
            logging.info(f'Connected to following guilds:')
            for guild in self.client.guilds:
                logging.info(f'- {guild.name} (id: {guild.id})')
                for channel in guild.channels:
                    logging.info(f'  - {channel.name} (id: {channel.id})')
            
            self._ready.set()
            logging.info(f'Discord bot logged in and ready!')
    
    async def start(self):
        """Start the Discord client."""
        try:
            await self.client.start(self.config.DISCORD_TOKEN)
        except Exception as e:
            logging.error(f"Failed to start Discord client: {e}")
            raise
    
    async def close(self):
        """Close the Discord client."""
        try:
            await self.client.close()
        except Exception as e:
            logging.error(f"Failed to close Discord client: {e}")
            raise
    
    async def wait_until_ready(self):
        """Wait until the Discord client is ready."""
        await self._ready.wait()
    
    async def send_notifications(self, listings: List[ProductListing]):
        """
        Send notifications to Discord for new listings.
        
        Args:
            listings: List of new ProductListing objects to notify about
        """
        try:
            channel = self.client.get_channel(self.config.DISCORD_CHANNEL_ID)
            if not channel:
                raise ValueError(f"Could not find channel with ID {self.config.DISCORD_CHANNEL_ID}")
            
            for listing in listings:
                embed = discord.Embed(
                    title=listing.name,
                    url=listing.url,
                    color=discord.Color.blue()
                )
                embed.add_field(name="Price", value=f"${listing.price:.2f}")
                embed.set_image(url=listing.image_url)
                
                await channel.send(embed=embed)
                
        except Exception as e:
            logging.error(f"Failed to send Discord notification: {e}")
            raise
