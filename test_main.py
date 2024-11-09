import asyncio
import logging
import schedule
import time
from config import Config
from scraper import WebScraper
from discord_notifier import DiscordNotifier

# Set up detailed logging to help debug connection issues
# Force logging to console
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ],
    force=True  # Ensure logging config is applied even if already configured
)

class Monitor:
    """Main application class that coordinates monitoring and notifications."""
    
    def __init__(self):
        self.config = Config()
        self.scraper = WebScraper(self.config)
        self.notifier = DiscordNotifier(self.config)
        
    async def check_for_updates(self):
        """Checks for new listings and sends notifications if found."""
        try:
            new_listings = self.scraper.get_new_listings()
            logging.debug(f"Found listings: {new_listings}")
            if new_listings:
                await self.notifier.send_notifications(new_listings)
                logging.info(f"Sent notifications for {len(new_listings)} new listings")
            else:
                logging.info("No new listings found")
        except Exception as e:
            logging.error(f"Error during update check: {str(e)}")
            raise  # Re-raise to ensure errors are visible

    async def run(self):
        """Runs the monitoring loop."""
        try:
            # First log the connection attempt
            logging.info("Connecting to Discord...")
            # Add debug logging for Discord client state
            logging.debug(f"Discord client intents: {self.notifier.client.intents}")
            logging.debug("Attempting Discord connection with configured token...")
            
            # Start the Discord client connection
            asyncio.create_task(self.notifier.client.start(self.config.DISCORD_TOKEN))
            
            # Add debug logging between operations
            logging.debug("Discord client.start() completed, waiting for ready state...")
            
            await self.notifier.client.wait_until_ready()
            
            # Only log success after confirmed ready
            logging.info("Successfully connected to Discord!")
            # Log additional connection details to help debug
            logging.info(f"Connected with client ID: {self.notifier.client.user.id}")
            logging.info(f"Connected to {len(self.notifier.client.guilds)} guilds")
            logging.info(f"Target channel ID: {self.config.DISCORD_CHANNEL_ID}")
            
            # Verify channel access
            channel = self.notifier.client.get_channel(self.config.DISCORD_CHANNEL_ID)
            if channel is None:
                raise ConnectionError(f"Could not access channel {self.config.DISCORD_CHANNEL_ID}. Please verify channel ID and bot permissions.")
            logging.info(f"Successfully verified access to channel: {channel.name}")
            
            # Begin the monitoring loop
            while True:
                try:
                    await self.check_for_updates()
                except Exception as e:
                    logging.error(f"Error in monitoring loop: {str(e)}")
                    # Continue running even if an update check fails
                await asyncio.sleep(self.config.MONITORING_INTERVAL)
                
        except Exception as e:
            logging.error(f"Critical error in Discord connection: {str(e)}")
            # Add more detailed error info to help debug connection issues
            logging.error(f"Client ready state: {self.notifier.client.is_ready()}")
            logging.error(f"Client latency: {self.notifier.client.latency}")
            logging.error(f"Client status: {self.notifier.client.status}")
            logging.error(f"Client activity: {self.notifier.client.activity}")
            raise  # Re-raise to prevent silent failures

if __name__ == "__main__":
    monitor = Monitor()
    asyncio.run(monitor.run())
