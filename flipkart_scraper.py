import re
import requests
from bs4 import BeautifulSoup
from difflib import SequenceMatcher

PLACEHOLDER_IMAGE = "https://placehold.co/300x400/EEE/31343C?text=No+Image"

# Common accessory/related product keywords to filter out
ACCESSORY_KEYWORDS = [
    'case', 'cover', 'stand', 'holder', 'mount', 'adapter', 'cable', 'charger',
    'screen protector', 'tempered glass', 'earphone', 'headphone', 'bag', 'pouch','covers',
    'stylus', 'pen', 'accessory', 'combo', 'kit', 'set of', 'pack of', 'bundle',
    'replacement', 'spare', 'belt', 'strap', 'band', 'clip', 'sleeve', 'skin',
    'decal', 'sticker', 'cleaner', 'wipe', 'protector', 'guard', 'film','pads'
]

def clean_price_text(price_text: str) -> int:
    """Extracts integer rupee value from text."""
    if not price_text:
        return 0
    m = re.search(r'[\d,]+', str(price_text).replace('₹','').replace('Rs',''))
    if m:
        return int(m.group(0).replace(',', ''))
    return 0

def clean_delivery_text(delivery_text: str) -> str:
    """Cleans delivery text by removing unwanted characters and promotional text"""
    if not delivery_text or delivery_text == "Delivery information not available":
        return delivery_text
    
    
    delivery_text = re.sub(r'FREE delivery', '', delivery_text, flags=re.IGNORECASE)
    delivery_text = re.sub(r'on your first order', '', delivery_text, flags=re.IGNORECASE)
    delivery_text = re.sub(r'Details.*', '', delivery_text, flags=re.IGNORECASE)
    
    cleaned_text = delivery_text.replace('?', '').strip()
    
    
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    cleaned_text = re.sub(r'^,\s*', '', cleaned_text) 
    cleaned_text = cleaned_text.strip()
    
    return cleaned_text if cleaned_text else "Delivery information not available"

def get_product_details(product_url: str, pincode: str = None):
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        cookies = {}
        if pincode:
            cookies['pincode'] = pincode
        
        resp = requests.get(product_url, headers=headers, cookies=cookies, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        details = {}
        
        # Extract title
        title_tag = soup.find("span", {"class": "VU-ZEz"}) or soup.find("h1", {"class": "yhB1nd"})
        details['title'] = title_tag.text.strip() if title_tag else "No title found"
        
        # Extract image
        image_tag = soup.find("img", {"class": "_0DkuPH"}) or soup.find("img", {"class": "_396cs4"})
        details['image'] = image_tag.get('src') if image_tag and image_tag.get('src') else PLACEHOLDER_IMAGE
        
        # Extract rating and review count
        rating_tag = soup.find("div", {"class": "XQDdHH"})
        details['rating'] = rating_tag.text.strip() if rating_tag else "No rating"
        
        review_tag = soup.find("span", {"class": "Wphh3N"})
        if review_tag:
            review_text = review_tag.text.strip()
            number = review_text.split()[0] if review_text else "0"
            details['reviews'] = f"{number} Ratings"

        else:
            details['reviews'] = "0 Ratings"
        
        # Extract star rating
        star_tag = soup.find("div", {"class": "XQDdHH"})
        details['stars'] = star_tag.text.strip() if star_tag else "N/A"
        
        # Enhanced delivery date extraction with multiple methods
        delivery_date = None
        
        # Method 1: Look for delivery date in specific delivery sections (avoid promotional text)
        delivery_selectors = [
            "div._2JC05C",  # Standard delivery info
            "div._2pe-Z2",  # Delivery section
            "div._3XINqE",  # Delivery info
            "div._2U41Hu",  # Delivery details
        ]
        
        for selector in delivery_selectors:
            delivery_tags = soup.select(selector)
            for tag in delivery_tags:
                text = tag.get_text(strip=True)
                # Look for actual delivery dates (contains day/month patterns)
                if re.search(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b', text, re.IGNORECASE):
                    if not re.search(r'first order', text, re.IGNORECASE):  # Skip promotional text
                        delivery_date = text
                        break
            if delivery_date:
                break
        
       
        if not delivery_date:
            delivery_classes = ["_2P_LDn", "_2hqNhN", "_3XINqE", "cfnhBl"]
            for cls in delivery_classes:
                delivery_tag = soup.find("div", {"class": cls})
                if delivery_tag:
                    text = delivery_tag.get_text(strip=True)
                    # Check if it contains actual date information, not promotional
                    if (any(word in text.lower() for word in ['delivery', 'delivers', 'get it by']) and
                        not re.search(r'first order', text, re.IGNORECASE)):
                        delivery_date = text
                        break
        
       
        if not delivery_date:
            all_text = soup.get_text()
            delivery_patterns = [
                r'Delivery by[^.]*?(\d{1,2}\s+\w+(?:\s+\d{4})?(?:\s*,\s*\w+)?)',
                r'Get it by[^.]*?(\d{1,2}\s+\w+(?:\s+\d{4})?(?:\s*,\s*\w+)?)',
                r'Delivers by[^.]*?(\d{1,2}\s+\w+(?:\s+\d{4})?(?:\s*,\s*\w+)?)',
                r'Expected delivery[^.]*?(\d{1,2}\s+\w+(?:\s+\d{4})?(?:\s*,\s*\w+)?)'
            ]
            
            for pattern in delivery_patterns:
                delivery_match = re.search(pattern, all_text, re.IGNORECASE)
                if delivery_match:
                    full_match = delivery_match.group(0)
                    if not re.search(r'first order', full_match, re.IGNORECASE):
                        delivery_date = full_match
                        break
        
        if not delivery_date and pincode:
            pincode_sections = soup.find_all(string=re.compile(r'delivery|delivers', re.IGNORECASE))
            for section in pincode_sections:
                parent = section.find_parent()
                if parent:
                    text = parent.get_text(strip=True)
                    # Look for actual delivery dates, not promotional
                    if (re.search(r'\d{1,2}\s+\w+', text) and 
                        not re.search(r'first order', text, re.IGNORECASE)):
                        delivery_date = text
                        break
        
        
        if delivery_date:
            details['delivery_date'] = clean_delivery_text(delivery_date)
        else:
            details['delivery_date'] = "Delivery information not available"
        
        price_tag = soup.find("div", {"class": "Nx9bqj"}) or soup.find("div", {"class": "_30jeqj"})
        details['price'] = clean_price_text(price_tag.text) if price_tag else 0
        
       
        discount_tag = soup.find("div", {"class": "UkUFwK"})
        details['discount'] = discount_tag.text.strip() if discount_tag else "No discount"
        
        highlights = []
        highlight_section = soup.find_all("li", {"class": "_7eSDEY"})
        for hl in highlight_section[:5]:  
            highlights.append(hl.text.strip())
        details['highlights'] = highlights if highlights else ["No highlights available"]
        
        seller_tag = soup.find("div", {"id": "sellerName"})
        details['seller'] = seller_tag.text.strip() if seller_tag else "Seller information not available"
        
        
        if details['delivery_date'] == "Delivery information not available":
            print(f"\nDEBUG: Could not find delivery info for {details['title']}")
            print(f"Pincode used: {pincode}")
        
        return details
        
    except Exception as e:
        print(f"Error fetching product details: {e}")
        return {
            'title': 'Error fetching details',
            'image': PLACEHOLDER_IMAGE,
            'rating': 'N/A',
            'reviews': '0',
            'stars': 'N/A',
            'delivery_date': 'N/A',
            'price': 0,
            'discount': 'N/A',
            'highlights': [],
            'seller': 'N/A'
        }

def scrape_flipkart(query: str, pincode: str = None):
    """
    Uses Requests and BeautifulSoup to scrape Flipkart.
    Returns dict with lowest priced product details.
    """
    search_url = f"https://www.flipkart.com/search?q={query.replace(' ', '%20')}"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        resp = requests.get(search_url, headers=headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        products = []
        
        product_containers = soup.find_all("div", {"class": "_1AtVbE"})
        for container in product_containers:
            product_link = container.find("a", {"class": "_1fQZEK"})
            if product_link and product_link.get("href"):
                product_url = "https://www.flipkart.com" + product_link["href"]
                price_tag = container.find("div", {"class": "_30jeqj"})
                if price_tag and price_tag.text:
                    price = clean_price_text(price_tag.text)
                    if price > 0:
                        products.append({
                            "price": price,
                            "url": product_url
                        })
        
        if not products:
            product_links = soup.find_all('a', href=re.compile(r'/p/'))
            for link in product_links:
                if link.get('href'):
                    product_url = "https://www.flipkart.com" + link['href']
                    parent = link.find_parent('div')
                    if parent:
                        price_elements = parent.find_all(string=re.compile(r'₹'))
                        for price_element in price_elements:
                            price_value = clean_price_text(price_element)
                            if price_value > 100:
                                products.append({
                                    "price": price_value,
                                    "url": product_url
                                })
                                break
        
        if products:
            lowest_product = min(products, key=lambda x: x['price'])
            
            details = get_product_details(lowest_product['url'], pincode)
            details['url'] = lowest_product['url']
            
            return details
        
        return None

    except Exception as e:
        print(f"Flipkart extraction error: {e}")
        return None


# just to debug
'''if __name__ == "__main__":
    result = scrape_flipkart("headphone", pincode="688524")
    if result:
        print(f"\n{'='*60}")
        print(f"Title: {result['title']}")
        print(f"Price: ₹{result['price']}")
        print(f"Rating: {result['rating']} ({result['reviews']} reviews)")
        print(f"Delivery: {result['delivery_date']}")
        print(f"Discount: {result['discount']}")
        print(f"Seller: {result['seller']}")
        print(f"Image: {result['image']}")
        print(f"URL: {result['url']}")
        print(f"Highlights: {', '.join(result['highlights'])}")
        print(f"{'='*60}\n")
    else:
        print("No products found!")'''