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
        img_elems = soup.find_all('img')
        for img in img_elems:
            src = img.get('src') or img.get('data-src')
            if src and ('products' in src.lower() or 'cdn' in src.lower()):
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = 'https://www.relaxfashionwear.in' + src
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
                # Check if product exists
                product = Product.query.filter_by(name=data['name']).first()
                if not product:
                    product = Product(name=data['name'])
                    db.session.add(product)
                
                product.price = data['price']
                product.description = data['description']
                product.category = data['category']
                product.website_url = data['website_url']
                product.scraped_at = datetime.utcnow()
                
                if data['images']:
                    product.all_images = ",".join(data['images'])
                    # Download first image as primary
                    primary_url = data['images'][0]
                    safe_name = "".join([c for c in data['name'] if c.isalnum() or c==' ']).rstrip()
                    save_dir = os.path.join("assets", "products", safe_name)
                    save_path = os.path.join(save_dir, "primary.jpg")
                    local_path = download_image(primary_url, save_path)
                    if local_path:
                        product.primary_image = local_path
                
                db.session.commit()
                scraped_data.append(product.to_dict())
                
        return scraped_data
    except Exception as e:
        print(f"Scraper error: {e}")
        raise e
