# config.py
from dataclasses import dataclass
from typing import Optional
import os
from dotenv import load_dotenv

@dataclass
class ProductListing:
    """Represents a product listing from the marketplace."""
    name: str
    price: float
    url: str
    image_url: str
    
    def __eq__(self, other):
        if not isinstance(other, ProductListing):
            return False
        return (self.name == other.name and 
                self.price == other.price and 
                self.url == other.url)

class Config:
    """Configuration management for the application."""
    def __init__(self):
        load_dotenv()
        self.DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
        self.DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
        self.WEBSITE_URL = "https://kfamarketplace.com/product/listing/?stock=in"
        self.BASE_URL = "https://kfamarketplace.com"
        self.MONITORING_INTERVAL = 43200  # 12 hours in seconds
        self.DATA_FILE = "previous_listings.json"
