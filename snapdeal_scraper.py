import re
import time
import tempfile
import os
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

PLACEHOLDER_IMAGE = "https://placehold.co/300x400/EEE/31343C?text=No+Image"

def clean_price_text(price_text: str) -> int:
    """Extracts integer rupee value from text."""
    if not price_text:
        return 0
    m = re.search(r'[\d,]+', str(price_text).replace('₹','').replace('Rs','').replace(' ','')) 
    if m:
        return int(m.group(0).replace(',', ''))
    return 0


# 🧩 Setup Chrome WebDriver
def setup_driver(headless=True):
    chrome_options = Options()
    temp_dir = tempfile.mkdtemp(prefix="chrome_snapdeal_")
    chrome_options.add_argument(f"--user-data-dir={temp_dir}")
    if headless:
        chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option("prefs", {"profile.default_content_setting_values.notifications": 2})

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.temp_dir = temp_dir
    return driver


def get_element_text(driver, selectors, default="N/A"):
    """Try multiple selectors and return text of first found element."""
    for selector in selectors:
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            text = element.text.strip()
            if text:
                return text
        except:
            continue
    return default


def get_element_attribute(driver, selectors, attribute, default=""):
    """Try multiple selectors and return attribute of first found element."""
    for selector in selectors:
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            attr = element.get_attribute(attribute)
            if attr:
                return attr
        except:
            continue
    return default


# 📍 Enter pincode on product page
def enter_pincode_snapdeal(driver, pincode: str):
    print(f"📍 Setting pincode to {pincode}...")
    try:
        pincode_input = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "pincode"))
        )
        if pincode_input.is_displayed():
            pincode_input.clear()
            pincode_input.send_keys(pincode)
            time.sleep(1)
            check_btn = driver.find_element(By.ID, "checkServiceability")
            check_btn.click()
            print("   ✓ Pincode set successfully")
            time.sleep(3)
            return True
    except:
        print("   ⚠️ Could not find pincode field.")
    return False


# 📦 Extract clean delivery info
def extract_delivery_info(driver, pincode_entered=False):
    """Extracts delivery details clearly like 'Delivery in 4 - 6 days' or 'Delivery by 7 Nov, Friday'."""
    delivery_info = {'delivery_date': None, 'delivery_text': None}
    try:
        time.sleep(2)
        page_text = driver.find_element(By.TAG_NAME, "body").text

        # Pattern 1: "Delivery by 7 Nov, Friday"
        match = re.search(r"Deliver(?:ed|y)\s*(?:by)?\s*([\d]{1,2}\s+\w{3,}(?:,\s*\w+)?(?:\s+\d{4})?)", page_text, re.IGNORECASE)
        if match:
            delivery_date = match.group(1).strip()
            delivery_info['delivery_date'] = delivery_date
            delivery_info['delivery_text'] = f"Delivery by {delivery_date}"
            return delivery_info

        # Pattern 2: "Delivery in 4 - 6 days" or "Generally delivered in X - Y days"
        match = re.search(r"(?:Generally\s+)?(?:delivered|delivery)\s+in\s+(\d+\s*-\s*\d+\s*days?)", page_text, re.IGNORECASE)
        if match:
            days = match.group(1).strip()
            delivery_info['delivery_date'] = days
            delivery_info['delivery_text'] = f"Delivery in {days}"
            return delivery_info

        # Pattern 3: "Get it by 9 Nov"
        match = re.search(r"Get it by\s+([\d]{1,2}\s+\w{3,}(?:,\s*\w+)?)", page_text, re.IGNORECASE)
        if match:
            date = match.group(1).strip()
            delivery_info['delivery_date'] = date
            delivery_info['delivery_text'] = f"Delivery by {date}"
            return delivery_info

        # Pattern 4: fallback if pincode entered but no info found
        if pincode_entered:
            delivery_info['delivery_date'] = "Available"
            delivery_info['delivery_text'] = "Delivery available in your area"
            return delivery_info

    except Exception as e:
        print(f"⚠️ Delivery extraction failed: {e}")
    return delivery_info


# 🛍️ Get full product details
def get_snapdeal_product_details(driver, product_url: str, pincode: str = None):
    try:
        driver.get(product_url)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)

        details = {}
        pincode_entered = False
        if pincode:
            pincode_entered = enter_pincode_snapdeal(driver, pincode)

        # Title
        details['title'] = get_element_text(driver, [
            "h1.pdp-e-i-head", "h1[itemprop='name']", "h1.product-title", "h1"
        ], "No title found")

        # Image
        details['image'] = get_element_attribute(driver, [
            "img.cloudzoom", "img[itemprop='image']", "img.product-image", "img.pdpCarouselImg"
        ], 'src', PLACEHOLDER_IMAGE)

        # ⭐ Rating
        rating_text = get_element_text(driver, [
            "span[itemprop='ratingValue']", "span.avrg-rating", "div.avrg-rating", "div.pdp-e-i-rating"
        ], "No rating")
        match = re.search(r"(\d+(\.\d+)?)", rating_text)
        details['rating'] = match.group(1) if match else "No rating"

        # 💬 Reviews ("223 Ratings")
        review_text = get_element_text(driver, [
            "span[itemprop='ratingCount']", "span.total-rating", "a.product-rating-count", "span.review-count"
        ], "0")
        match = re.search(r"(\d+)", review_text.replace(",", ""))
        if match:
            details['reviews'] = f"{match.group(1)} Ratings"
        else:
            details['reviews'] = review_text.strip() if "rating" in review_text.lower() else "0 Ratings"

        # 📦 Delivery info
        delivery_info = extract_delivery_info(driver, pincode_entered)
        details['delivery_date'] = delivery_info.get('delivery_date', "Check on website")
        details['delivery_text'] = delivery_info.get('delivery_text', "Enter pincode on website for delivery info")

        # 💰 Price
        price_text = get_element_text(driver, [
            "span.pdp-final-price", "span.payBlkBig", "span[itemprop='price']", "span.lfloat.product-price"
        ], "0")
        details['price'] = clean_price_text(price_text)

        # MRP
        mrp_text = get_element_text(driver, [
            "span.pdp-mrp", "span.lfloat.markedPrice", "span.strikedPriceText"
        ], "0")
        details['original_price'] = clean_price_text(mrp_text)

        # Discount
        details['discount'] = get_element_text(driver, [
            "span.percent-desc", "div.percent-desc", "span.pdp-discount"
        ], "No discount")

        # Seller
        details['seller'] = get_element_text(driver, [
            "div.seller-name", "a.seller-link", "span[itemprop='seller']"
        ], "N/A")

        # Stock
        try:
            add_to_cart = driver.find_element(By.CSS_SELECTOR, "div#add-cart-button-id, button.buy-button")
            details['in_stock'] = add_to_cart.is_displayed() and add_to_cart.is_enabled()
        except:
            details['in_stock'] = False

        return details

    except Exception as e:
        print(f"❌ Error fetching details: {e}")
        return None


# 🔍 Main scraping logic
def scrape_snapdeal(query: str, pincode: str = None, headless: bool = True):
    driver = None
    try:
        driver = setup_driver(headless)
        search_url = f"https://www.snapdeal.com/search?keyword={query.replace(' ', '+')}"
        driver.get(search_url)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)

        product_links = [a.get_attribute('href') for a in driver.find_elements(By.XPATH, "//a[contains(@href, '/product/')]")]
        unique_links = list(dict.fromkeys(product_links))
        print(f"Found {len(unique_links)} products.")

        lowest_price, lowest_url = None, None
        for url in unique_links[:5]:
            try:
                driver.get(url)
                price_text = get_element_text(driver, ["span.payBlkBig", "span[itemprop='price']"], "")
                price = clean_price_text(price_text)
                if price and (lowest_price is None or price < lowest_price):
                    lowest_price, lowest_url = price, url
            except:
                continue

        if lowest_url:
            details = get_snapdeal_product_details(driver, lowest_url, pincode)
            if details:
                details['url'] = lowest_url
                return details
        return None

    finally:
        if driver:
            temp_dir = getattr(driver, 'temp_dir', None)
            driver.quit()
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    import json
    result = scrape_snapdeal(query="wireless mouse", pincode="533247", headless=True)
    print(json.dumps(result, indent=4, ensure_ascii=False))