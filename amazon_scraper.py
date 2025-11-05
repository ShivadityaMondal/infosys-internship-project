import time
import random
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
#uvicorn main:app --reload                                                                                                                                         
PLACEHOLDER_IMAGE = "https://placehold.co/300x400/EEE/31343C?text=No+Image"

def clean_price_text(price_text: str) -> int:
    """Extracts integer rupee value from text."""
    if not price_text:
        return 0
    m = re.search(r'[\d,]+', str(price_text).replace('₹','').replace('Rs',''))
    if m:
        return int(m.group(0).replace(',', ''))
    return 0

def random_delay(a=1.0, b=2.5):
    time.sleep(random.uniform(a, b))

def get_browser(headless=True):
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("start-maximized")
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    service = Service(ChromeDriverManager().install())
    browser = webdriver.Chrome(service=service, options=opts)
    return browser

def scrape_amazon_search(query: str, browser):
   
    url = f"https://www.amazon.in/s?k={query.replace(' ', '+')}"
    browser.get(url)
    random_delay(3, 5)
    soup = BeautifulSoup(browser.page_source, "html.parser")

    results = []
    for div in soup.select("div[data-component-type='s-search-result']"):
        try:
            link = div.select_one("a.a-link-normal.s-no-outline")
            if not link:
                continue
            href = link.get("href")
            product_url = "https://www.amazon.in" + href
            price_el = div.select_one("span.a-price-whole")
            price = clean_price_text(price_el.text if price_el else "")
            img = div.select_one("img.s-image")
            image_url = img.get("src") if img else PLACEHOLDER_IMAGE
            if price > 0:
                results.append({"price": price, "url": product_url, "image": image_url})
        except Exception:
            continue
    return results

def change_pincode(browser, pincode: str):
    try:
       
        location_btn = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.ID, "contextualIngressPtLabel"))
        )
        location_btn.click()
        random_delay(1, 2)
        
        # Enter pincode
        pincode_input = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "GLUXZipUpdateInput"))
        )
        pincode_input.clear()
        pincode_input.send_keys(pincode)
        random_delay(0.5, 1)
        
        # Click apply button
        apply_btn = browser.find_element(By.CSS_SELECTOR, "input[aria-labelledby='GLUXZipUpdate-announce']")
        apply_btn.click()
        random_delay(2, 3)
        
        # Close the popover if still open
        try:
            done_btn = browser.find_element(By.CSS_SELECTOR, "button[name='glowDoneButton']")
            done_btn.click()
            random_delay(1, 2)
        except:
            pass
            
        return True
    except Exception as e:
        print(f"Could not change pincode: {e}")
        return False

def scrape_product_details(product_url: str, browser, pincode: str = None):
    browser.get(product_url)
    random_delay(3, 5)
    if pincode:
        change_pincode(browser, pincode)
        random_delay(2, 3)
    
    soup = BeautifulSoup(browser.page_source, "html.parser")
    
    details = {
        "url": product_url,
        "title": "",
        "price": 0,
        "original_price": 0,
        "discount": "",
        "rating": 0.0,
        "review_count": 0,
        "image": PLACEHOLDER_IMAGE,
        "images": [],
        "delivery_date": "",
        "delivery_info": "",
        "availability": "",
        "brand": "",
        "description": "",
        "features": [],
        "specifications": {},
        "seller": "",
        "in_stock": False
    }
    
    # Title
    title_el = soup.select_one("#productTitle")
    if title_el:
        details["title"] = title_el.text.strip()
    
    # Price
    price_el = soup.select_one("span.a-price.aok-align-center.reinventPricePriceToPayMargin.priceToPay span.a-price-whole")
    if not price_el:
        price_el = soup.select_one("span.a-price-whole")
    if price_el:
        details["price"] = clean_price_text(price_el.text)
    
    # Original price (MRP)
    mrp_el = soup.select_one("span.a-price.a-text-price span.a-offscreen")
    if mrp_el:
        details["original_price"] = clean_price_text(mrp_el.text)
    
    # Discount
    discount_el = soup.select_one("span.savingsPercentage")
    if discount_el:
        details["discount"] = discount_el.text.strip()
    
    # Rating
    rating_el = soup.select_one("span.a-icon-alt")
    if rating_el:
        rating_text = rating_el.text.strip()
        match = re.search(r'([\d.]+)\s*out of', rating_text)
        if match:
            details["rating"] = float(match.group(1))
    
    # Review count
    # Review count
    review_el = soup.select_one("#acrCustomerReviewText")
    if review_el:
        review_text = review_el.text.strip()
        match = re.search(r'([\d,]+)', review_text)
        if match:
            details["review_count"] = f"{match.group(1).replace(',', '')} Ratings"
        else:
            details["review_count"] = "No Ratings"
    else:
        details["review_count"] = "No Ratings"

    
    # Main image
    img_el = soup.select_one("#landingImage")
    if not img_el:
        img_el = soup.select_one("#imgBlkFront")
    if img_el:
        details["image"] = img_el.get("src", PLACEHOLDER_IMAGE)
    
    # All images
    img_thumbs = soup.select("img.a-dynamic-image")
    for img in img_thumbs[:6]:  # Limit to 6 images
        img_url = img.get("src", "")
        if img_url and img_url not in details["images"]:
            details["images"].append(img_url)
    
    # Delivery date
    delivery_el = soup.select_one("#mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE_LARGE b")
    if not delivery_el:
        delivery_el = soup.select_one("span[data-csa-c-delivery-time]")
    if delivery_el:
        details["delivery_date"] = delivery_el.text.strip()
    
    # Delivery info
    delivery_info_el = soup.select_one("#mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE_LARGE")
    if delivery_info_el:
        details["delivery_info"] = delivery_info_el.text.strip()
    
    # Availability
    avail_el = soup.select_one("#availability span")
    if avail_el:
        avail_text = avail_el.text.strip()
        details["availability"] = avail_text
        details["in_stock"] = "in stock" in avail_text.lower() or "available" in avail_text.lower()
    
    # Brand
    brand_el = soup.select_one("#bylineInfo")
    if brand_el:
        details["brand"] = brand_el.text.strip().replace("Visit the ", "").replace(" Store", "").replace("Brand: ", "")
    
    # Product description
    desc_el = soup.select_one("#feature-bullets ul")
    if desc_el:
        features = []
        for li in desc_el.select("li"):
            text = li.text.strip()
            if text:
                features.append(text)
        details["features"] = features
    
    # Product description (alternate)
    if not details["features"]:
        desc_el = soup.select_one("#productDescription p")
        if desc_el:
            details["description"] = desc_el.text.strip()
    
    # Specifications
    spec_tables = soup.select("table.a-keyvalue")
    for table in spec_tables:
        rows = table.select("tr")
        for row in rows:
            cells = row.select("td")
            if len(cells) == 2:
                key = cells[0].text.strip()
                value = cells[1].text.strip()
                if key and value:
                    details["specifications"][key] = value
    
    # Seller info
    seller_el = soup.select_one("#sellerProfileTriggerId")
    if seller_el:
        details["seller"] = seller_el.text.strip()
    
    return details

def scrape_amazon_lowest_price(query: str, pincode: str = None, headless: bool = True):
    browser = get_browser(headless=headless)
    
    try:
        
        print(f"Searching for: {query}")
        products = scrape_amazon_search(query, browser)
        
        if not products:
            return {"error": "No products found"}
        
        print(f"Found {len(products)} products")
        
        lowest = min(products, key=lambda x: x['price'])
        print(f"Lowest price: ₹{lowest['price']} at {lowest['url']}")
        
        print("Fetching product details...")
        details = scrape_product_details(lowest['url'], browser, pincode)
        
        return details
        
    except Exception as e:
        return {"error": str(e)}
    
    finally:
        browser.quit()


#just to debug 
"""if __name__ == "__main__":
    # Search for a product and get lowest priced item details
    result = scrape_amazon_lowest_price(
        query="wireless mouse",
        pincode="682001",  # Optional: Pass pincode from frontend
        headless=False  # Set to True in production
    )
    
    # Print results
    print("\n" + "="*50)
    print("LOWEST PRICED PRODUCT DETAILS")
    print("="*50)
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"\nTitle: {result['title']}")
        print(f"Price: ₹{result['price']}")
        if result['original_price']:
            print(f"Original Price: ₹{result['original_price']}")
        if result['discount']:
            print(f"Discount: {result['discount']}")
        print(f"Rating: {result['rating']} stars ({result['review_count']} reviews)")
        print(f"Brand: {result['brand']}")
        print(f"Availability: {result['availability']}")
        print(f"In Stock: {result['in_stock']}")
        print(f"Delivery Date: {result['delivery_date']}")
        print(f"Delivery Info: {result['delivery_info']}")
        print(f"Seller: {result['seller']}")
        print(f"\nImage: {result['image']}")
        print(f"Product URL: {result['url']}")
        
        if result['features']:
            print(f"\nFeatures:")
            for feat in result['features'][:5]:  # Show first 5
                print(f"  • {feat}")
        
        if result['specifications']:
            print(f"\nSpecifications:")
            for key, val in list(result['specifications'].items())[:5]:  # Show first 5
                print(f"  • {key}: {val}")
# Call with pincode from frontend
result = scrape_amazon_lowest_price(
    query="laptop",
    pincode="688524",  # From frontend input
    headless=True
)
print(result)"""