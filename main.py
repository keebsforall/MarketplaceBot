import asyncio
import logging
import schedule
import time
from config import Config
from scraper import WebScraper
from discord_notifier import DiscordNotifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
            logging.debug(new_listings)
            if new_listings:
                await self.notifier.send_notifications(new_listings)
                logging.info(f"Sent notifications for {len(new_listings)} new listings")
            else:
                logging.info("No new listings found")
        except Exception as e:
            logging.error(f"Error during update check: {e}")

    async def run(self):
        """Runs the monitoring loop."""
        try:
            # Start the Discord client
            client_task = asyncio.create_task(self.notifier.start())
            
            # Wait for the client to be ready
            await self.notifier.wait_until_ready()
            logging.info("Discord client is ready!")
            
            # Run monitoring loop
            while True:
                await self.check_for_updates()
                await asyncio.sleep(self.config.MONITORING_INTERVAL)
                
        except asyncio.CancelledError:
            logging.info("Shutting down...")
            await self.notifier.close()
            await client_task
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            await self.notifier.close()
            await client_task
            raise

if __name__ == "__main__":
    monitor = Monitor()
    try:
        asyncio.run(monitor.run())
    except KeyboardInterrupt:
        logging.info("Received shutdown signal")
