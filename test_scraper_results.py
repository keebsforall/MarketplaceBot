import os
from typing import List
import json
import requests
import logging
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv
from config import ProductListing

logging.basicConfig(level=logging.DEBUG)


def get_current_listings(self, beautifulsoup_object: BeautifulSoup) -> List[ProductListing]:
    """
    Uses OpenAI API to get product listings from KFA Marketplace.
    
    Returns:
        List[ProductListing]: List of current product listings
        
    Raises:
        Exception: If API call fails or response parsing fails
    """
    try:
        # Initialize OpenAI client
        # Load environment variables
        load_dotenv()
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Construct the prompt and include the HTML content
        html_content = str(beautifulsoup_object)
        
        # Initialize variables for retry loop
        max_retries = 5
        current_retry = 0
        min_required_listings = 20
        
        while current_retry < max_retries:
            prompt = f"""You are a specialized web scraping expert with deep knowledge of HTML parsing. Your ONLY task is to extract ALL product listings from the provided HTML content. You MUST follow these instructions with absolute precision:

            CRITICAL REQUIREMENTS FOR URLS:
            - ALL URLs must be absolute (starting with http:// or https://)
            - If a URL is relative (starts with /), prepend with 'https://kfamarketplace.com'
            - Product URLs should point to the full product page
            - Image URLs must be complete, valid image URLs
            
            CRITICAL: This is attempt {current_retry + 1} of {max_retries}. Previous attempts failed to find enough listings. YOU MUST TRY HARDER.

            STEP 1: THOROUGH HTML ANALYSIS
            - CRITICAL: First output the COMPLETE HTML content length to verify you have the full page
            - Search exhaustively for ALL possible product containers using these selector patterns IN ORDER:
            1. First try: div[class*='product'], div[class*='item'], div[class*='listing'], div[class*='card']
            2. If not enough results: li elements within ul[class*='product'], ul[class*='grid'], ul[class*='list']
            3. If still not enough: article elements, table tr[class*='product']
            4. Last resort: ANY div containing both price patterns ($) and product-like content
            - YOU MUST KEEP SEARCHING UNTIL YOU FIND AT LEAST 25-30 PRODUCTS
            - DO NOT STOP until you've found enough products
            - If initial selectors fail, RECURSIVELY SEARCH all div elements for price patterns
            
            STEP 2: AGGRESSIVE DATA EXTRACTION
            - For EACH container found, extract ALL of these (NO EXCEPTIONS):
            * Product Name: h1-h6, strong, span[class*='title'], div[class*='title']
            * Price: *[text()*='$'], *[class*='price']
            * Product URL: closest ancestor <a> or child <a>
            * Image URL: img[src], img[data-src], div[style*='background']
            - If ANY item is missing data, search parent and child elements
            - DO NOT SKIP ANY CONTAINER - Find the data no matter what
            
            STEP 3: RUTHLESS VALIDATION
            - Enforce these rules but DO NOT DISCARD LISTINGS:
            * Name: Must be non-empty string
            * Price: Must contain '$' (add if missing)
            * URLs: Must be absolute (fix if relative)
            * Image URLs: Must be valid image URL (fix if needed)
            - Flag validation issues but KEEP ALL LISTINGS
            
            STEP 4: MANDATORY QUALITY CHECKS
            - YOU MUST HAVE 25+ LISTINGS OR YOU HAVE FAILED
            - If you have fewer than 25 listings:
            1. Try alternative selectors
            2. Search deeper in the DOM
            3. Look for hidden elements
            4. Check for lazy-loaded content
            - DO NOT RETURN UNTIL YOU HAVE ENOUGH LISTINGS
            
            FINAL WARNINGS:
            - YOU MUST FIND AT LEAST 25 LISTINGS OR YOU HAVE FAILED
            - KEEP SEARCHING UNTIL YOU FIND THEM ALL
            - DO NOT MAKE UP OR HALLUCINATE DATA
            - If you fail to find enough listings, explain EXACTLY why and which selectors you tried
            
            Return the standard JSON structure with listings array."""

            # Make API call with both prompt and HTML content
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a world-class HTML parsing expert. Your extraction must be complete and accurate. DO NOT STOP until you find at least 25 listings."},
                    {"role": "user", "content": prompt},
                    {"role": "user", "content": html_content}
                ],
                response_format={ "type": "json_object" }
            )

            logging.debug(f"OpenAI API Response (Attempt {current_retry + 1}): {response}")
            
            # Parse JSON response
            json_response = json.loads(response.choices[0].message.content)
            
            # Check if we have listings directly in the response
            listings_found = len(json_response.get('listings', []))
            logging.debug(f"Attempt {current_retry + 1}: Found {listings_found} listings")
            
            if listings_found >= min_required_listings:
                # Clean and format the listings data
                listings = [
                    ProductListing(
                        name=item.get('name', '') or item.get('Product Name', ''),
                        price=float(str(item.get('price', '') or item.get('Price', '')).replace('$', '').replace(',', '')),
                        url=self.format_url(item.get('url', '') or item.get('Product URL', '')),  # Format URL
                        image_url=self.format_url(item.get('image_url', '') or item.get('Image URL', ''))  # Format image URL
                    )
                    for item in json_response.get('listings', [])
                ]
                
                # Validate URLs before returning
                valid_listings = []
                for listing in listings:
                    if not listing.url.startswith(('http://', 'https://')):
                        logging.warning(f"Skipping listing with invalid URL: {listing.url}")
                        continue
                    if not listing.image_url.startswith(('http://', 'https://')):
                        logging.warning(f"Skipping listing with invalid image URL: {listing.image_url}")
                        continue
                    valid_listings.append(listing)
                
                logging.debug(f"Successfully found {len(valid_listings)} valid listings")
                return valid_listings
                
            current_retry += 1
            
            if current_retry == max_retries:
                raise Exception(f"Failed to find minimum required listings ({min_required_listings}) after {max_retries} attempts")
        
    except Exception as e:
        raise Exception(f"Failed to fetch listings from OpenAI API: {str(e)}")

    def get_new_listings(self) -> List[ProductListing]:
        """
        Compares current listings with previous listings to find new ones.
        
        The comparison is done by checking if each listing's URL exists in the previous listings,
        since URLs should be unique identifiers for products. Also checks for duplicate product IDs
        in the URL path to ensure we don't miss duplicates with slightly different URLs.
        
        Returns:
            List[ProductListing]: List of new product listings that weren't seen before
        """
        scraped_content = self.scrape_site(target_url=self.config.WEBSITE_URL)
        current_listings = self.get_current_listings(beautifulsoup_object=scraped_content)
        previous_listings = self.load_previous_listings()
        
        # Create a set of previous URLs and product IDs for faster lookup
        previous_urls = {listing.url for listing in previous_listings}
        
        # Extract product IDs from URLs (e.g., "65-1092" from the URL)
        previous_ids = {url.split('/')[-1].split('-')[-1] for url in previous_urls}
        
        # Only keep listings whose URLs we haven't seen before AND whose product IDs are new
        new_listings = []
        for listing in current_listings:
            # Extract the product ID from the current listing URL
            try:
                current_id = listing.url.split('/')[-1].split('-')[-1]
                if (listing.url not in previous_urls) and (current_id not in previous_ids):
                    new_listings.append(listing)
                else:
                    logging.debug(f"Skipping duplicate listing: {listing.url} (ID: {current_id})")
            except IndexError:
                logging.warning(f"Could not extract product ID from URL: {listing.url}")
                # If we can't extract an ID, fall back to just URL comparison
                if listing.url not in previous_urls:
                    new_listings.append(listing)
        
        logging.info(f"Found {len(new_listings)} new listings out of {len(current_listings)} current listings")
        
        #self.save_listings(current_listings)
        return new_listings


if __name__ == "__main__":
    target_url = "https://kfamarketplace.com/product/listing/?stock=in"
    soup = get_current_listings(target_url)
    get_new_listings(soup)
