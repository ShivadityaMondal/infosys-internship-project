import concurrent.futures
from amazon_scraper import scrape_amazon_lowest_price, get_browser 
from flipkart_scraper import scrape_flipkart
from snapdeal_scraper import scrape_snapdeal
import re

# NOTE: Using scrape_amazon_lowest_price and scrape_flipkart (which return single detailed dicts) 
# instead of scrape_amazon_search (which returns a list of simple dicts) for better data quality.

def clean_price(price_text):
    """Extract numeric price from text"""
    if not price_text:
        return 0
    
    # Remove currency symbols and commas, extract numbers
    price_match = re.search(r'[\d,]+\.?\d*', str(price_text))
    if price_match:
        price_str = price_match.group().replace(',', '')
        try:
            return float(price_str)
        except ValueError:
            return 0
    return 0

def validate_deal(deal, site):
    """
    Validate and clean deal data, and standardize keys for Streamlit display.
    """
    price_value = deal.get('price')
    clean_price_value = clean_price(price_value)
    
    if not deal or not isinstance(deal, dict) or clean_price_value <= 0:
        return None

    # --- Standardize Keys for app.py display ---
    
    # Clean URL
    url = deal.get('url', '#')
    if not isinstance(url, str) or not url.startswith(("http://", "https://")):
        url = "https://" + url.lstrip("/")
        
    # Clean Image URL
    img = deal.get('image', 'https://placehold.co/300x400/EEE/31343C?text=No+Image')
    if not isinstance(img, str) or not img.startswith(("http://", "https://")):
        img = 'https://placehold.co/300x400/EEE/31343C?text=No+Image'
    
    # Map scraper keys to display keys used in app.py
    standard_deal = {
        # Required for sorting/filtering/display
        'Website': site,
        'price_float': clean_price_value, # Used for sorting
        'Price (₹)': clean_price_value,    # Used for display and logic
        'URL': url,
        'Image': img,
        
        # Details required by the display loop
        'Title': deal.get('title', 'Product Title N/A'),
        'Rating': deal.get('rating', deal.get('stars', 'N/A')), # Handles both Amazon/Flipkart keys
        'Reviews': deal.get('review_count', deal.get('reviews', 'N/A')), # Handles both Amazon/Flipkart keys
        'Delivery Date': deal.get('delivery_date', 'N/A'),
        'Error': deal.get('error', None)
    }
        
    return standard_deal


def get_all_prices(product: str, pincode: str = None):
    """
    Fetches prices from all platforms and returns all results sorted by price.
    Returns: list of dicts (standardized)
    """
    browser = None
    all_results = []
    
    try:
        # Get browser for Amazon (Selenium)
        browser = get_browser(headless=True)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as exe:
            futures = {
                # These scrapers are expected to return a single dict with full details
                exe.submit(scrape_flipkart, product, pincode): "Flipkart", 
                exe.submit(scrape_amazon_lowest_price, product, pincode, browser): "Amazon",
                
                # Snapdeal returns a list of simple dicts (price, url, image) from the search page
                exe.submit(scrape_snapdeal, product): "Snapdeal"
            }

            for fut in concurrent.futures.as_completed(futures):
                site = futures[fut]
                try:
                    data = fut.result()
                    
                    if not data:
                        all_results.append({'Website': site, 'Error': 'No products found or fetch failed'})
                        continue

                    # Handle Snapdeal's list of simple results
                    if site == "Snapdeal" and isinstance(data, list):
                        for item in data:
                            validated_item = validate_deal(item, site)
                            if validated_item:
                                all_results.append(validated_item)
                    
                    # Handle Amazon/Flipkart's single detailed dict result
                    elif isinstance(data, dict):
                        validated_item = validate_deal(data, site)
                        if validated_item:
                            all_results.append(validated_item)
                        else:
                            all_results.append({'Website': site, 'Error': data.get('error', 'Price not found or fetch failed')})
                            
                    else:
                        all_results.append({'Website': site, 'Error': 'Unexpected data format'})
                        
                except Exception as e:
                    all_results.append({'Website': site, 'Error': f'Thread Error: {str(e)}'})

        # Sort by the standardized float price key
        all_results.sort(key=lambda x: x.get("price_float", float('inf')))
        
        return all_results
        
    except Exception as e:
        print(f"🚨 Error in get_all_prices (main thread): {str(e)}")
        return []
    finally:
        if browser:
            # Quit the browser instance started for Amazon
            browser.quit()

def get_price(product: str, pincode: str = None):
    """
    Alias for get_all_prices to satisfy app.py's import requirement.
    It returns the full list of deals, which app.py then sorts and displays.
    """
    return get_all_prices(product, pincode)