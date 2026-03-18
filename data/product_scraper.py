import os
import requests
from bs4 import BeautifulSoup
import pathlib
from datetime import datetime
from data.database import db, Product
import config

def download_image(url, save_path):
    try:
        response = requests.get(url, stream=True, timeout=10)
        if response.status_code == 200:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return save_path
    except Exception as e:
        print(f"Error downloading {url}: {e}")
    return None

def scrape_product_page(url):
    try:
        response = requests.get(url, timeout=15)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # This is based on standard Shopify/common e-commerce patterns 
        # adjusted for relaxfashionwear.in structure seen in web search
        name = soup.find('h1').text.strip() if soup.find('h1') else "Unknown Product"
        
        # Price extraction (heuristic)
        price_text = ""
        price_elem = soup.find(class_=lambda x: x and 'price' in x.lower())
        if price_elem:
            price_text = price_elem.text.strip().replace('₹', '').replace(',', '').split('.')[0]
        price = int(''.join(filter(str.isdigit, price_text))) if any(c.isdigit() for c in price_text) else 0
        
        description = ""
        desc_elem = soup.find(class_=lambda x: x and ('description' in x.lower() or 'content' in x.lower()))
        if desc_elem:
            description = desc_elem.text.strip()
            
        images = []
        base_url = "https://www.relaxfashionwear.in"
        # -- IMAGES (Better selectors for Shopify/WooCommerce) --
        img_selectors = [
            "meta[property='og:image']",
            "img.product-featured-img",
            "img.ProductItem__Image",
            ".product-single__photo img",
            ".woocommerce-product-gallery__image img",
            ".product-gallery img",
            ".main-product-image img",
            "img[id^='ProductPhotoImg']",
            "img[class*='product-main-image']",
            "img[src*='/products/']"
        ]
        
        for sel in img_selectors:
            if sel.startswith("meta"):
                tag = soup.select_one(sel)
                if tag and tag.get("content"):
                    img_url = tag.get("content")
                    if img_url.startswith("//"): img_url = "https:" + img_url
                    images.append(img_url)
            else:
                for img in soup.select(sel):
                    src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
                    if src:
                        if src.startswith("//"): src = "https:" + src
                        elif src.startswith("/"): src = base_url + src
                        if src not in images:
                            images.append(src)
        
        # If no images found, try any large image
        if not images:
            for img in soup.find_all("img"):
                src = img.get("src") or img.get("data-src")
                if src and any(x in src.lower() for x in ["product", "img", "item", "p-"]):
                    if src.startswith("//"): src = "https:" + src
                    elif src.startswith("/"): src = base_url + src
                    if src not in images:
                        images.append(src)
        
        # Category (heuristic from breadcrumbs or URL)
        category = "Uncategorized"
        if 'men' in url.lower(): category = "Men"
        elif 'women' in url.lower(): category = "Women"
        elif 'kids' in url.lower(): category = "Kids"
        elif 'biker' in url.lower(): category = "Biker"
        
        return {
            "name": name,
            "price": price,
            "description": description,
            "images": images,
            "category": category,
            "website_url": url
        }
    except Exception as e:
        print(f"Error scraping {url}: {e}")
    return None

def scrape_products():
    base_url = "https://www.relaxfashionwear.in"
    try:
        response = requests.get(base_url, timeout=15)
        soup = BeautifulSoup(response.text, 'lxml')
        
        product_links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/products/' in href:
                if href.startswith('/'):
                    href = base_url + href
                product_links.add(href)
        
        scraped_data = []
        for link in list(product_links)[:20]: # Limit to 20 for safety
            data = scrape_product_page(link)
            if data:
                # Save to database
                from data.database import db, Product
                existing = Product.query.filter_by(name=data['name']).first()
                if not existing:
                    p = Product(
                        name           = data['name'],
                        price          = data['price'],
                        category       = data['category'],
                        website_url    = data['website_url'],
                        description    = data['description'],
                        primary_image  = data['images'][0] if data['images'] else None,
                        all_images     = ",".join(data['images']) if data['images'] else "",
                        scraped_at     = datetime.utcnow()
                    )
                    db.session.add(p)
                    db.session.commit()
                    scraped_data.append(p.to_dict())
                else:
                    # Update existing product
                    existing.price = data['price']
                    existing.category = data['category']
                    existing.description = data['description']
                    existing.website_url = data['website_url']
                    existing.scraped_at = datetime.utcnow()
                    if not existing.primary_image and data['images']:
                        existing.primary_image = data['images'][0]
                    existing.all_images = ",".join(data['images']) if data['images'] else existing.all_images
                    db.session.commit()
                    scraped_data.append(existing.to_dict())
                
        return scraped_data
    except Exception as e:
        print(f"Scraper error: {e}")
        raise e
