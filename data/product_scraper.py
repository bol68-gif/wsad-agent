import os 
import re 
import requests 
from bs4 import BeautifulSoup 
from datetime import datetime 
import config 
 
BASE_URL = "https://www.relaxfashionwear.in" 
 
# All known product slugs from relaxfashionwear.in 
# These are hardcoded because the site is Next.js 
# and dynamic content doesn't render in basic HTTP requests 
PRODUCT_SLUGS = [ 
    "mens-raincoat-eliteshield", 
    "premium-double-layer-rain-suit-for-men-men-s-urban-suit-jacket-pant", 
    "men-s-classic-raincoat", 
    "pro-biker-rain-suit", 
    "womens-long-raincoat", 
    "kids-cartoon-raincoat", 
    "kids-solid-raincoat", 
    "kids-rain-suit", 
    "poncho-raincoat", 
    "windcheater-jacket", 
    "reversible-rain-jacket", 
    "hi-vis-orange-safety-raincoat", 
    "hi-vis-green-safety-raincoat", 
] 
 
# Complete product catalog with known images from site 
# Image URLs confirmed by visiting actual pages 
PRODUCT_CATALOG = [ 
    { 
        "slug":     "mens-raincoat-eliteshield", 
        "name":     "EliteShield Rain Set", 
        "category": "Biker", 
        "price":    1599, 
        "images": [ 
            "https://res.cloudinary.com/dipnajpc1/image/upload/v1773572785/z10fqqfx5zibnrfhhzma.jpg", 
            "https://res.cloudinary.com/dipnajpc1/image/upload/v1773572793/lez2ecmfquwmaeuidijf.jpg", 
            "https://res.cloudinary.com/dipnajpc1/image/upload/v1773572803/jxvrkkiowon41rg7cvnw.png", 
            "https://res.cloudinary.com/dipnajpc1/image/upload/v1773572809/llx11f4pyixwwselbqav.png", 
            "https://res.cloudinary.com/dipnajpc1/image/upload/v1773572815/wvhg6dkgwtggjeqr0wn8.png", 
        ], 
        "features": ["Heat sealed seams", "3000mm waterproof", "Reflective strips", "Breathable mesh"], 
        "description": "Top-selling double-layered raincoat. 100% waterproof PVC-coated nylon, heat-sealed seams, reinforced zipper.", 
        "url": f"{BASE_URL}/product/mens-raincoat-eliteshield" 
    }, 
    { 
        "slug":     "urban-suit", 
        "name":     "Urban Rain Suit", 
        "category": "Men", 
        "price":    1450, 
        "images": [ 
            f"{BASE_URL}/images/product-images/blueyellow1.webp", 
        ], 
        "features": ["Lightweight fabric", "Compact pouch", "Adjustable hood", "Double zipper"], 
        "description": "Modern urban design with superior water resistance. For office commuters and city riders.", 
        "url": f"{BASE_URL}/product/premium-double-layer-rain-suit-for-men-men-s-urban-suit-jacket-pant" 
    }, 
    { 
        "slug":     "classic-raincoat", 
        "name":     "Classic Rain Set", 
        "category": "Men", 
        "price":    1399, 
        "images": [ 
            f"{BASE_URL}/images/product-images/green1.webp", 
        ], 
        "features": ["Durable PVC", "Classic fit", "Sealed pockets", "Elastic cuffs"], 
        "description": "Durable and stylish classic raincoat for everyday use.", 
        "url": f"{BASE_URL}/product/men-s-classic-raincoat" 
    }, 
    { 
        "slug":     "pro-biker-rain-suit", 
        "name":     "Pro Biker Rain Set", 
        "category": "Biker", 
        "price":    1599, 
        "images": [ 
            f"{BASE_URL}/images/product-images/bluebiker1.webp", 
        ], 
        "features": ["Jacket + Pant set", "Anti-flap design", "Reflective safety strips", "Highway grade"], 
        "description": "Heavy-duty biker rain suit. Engineered for highway riding and heavy downpours.", 
        "url": f"{BASE_URL}/product/pro-biker-rain-suit" 
    }, 
    { 
        "slug":     "womens-long-raincoat", 
        "name":     "Women Long Rain Coat", 
        "category": "Women", 
        "price":    1399, 
        "images": [ 
            f"{BASE_URL}/images/product-images/womenlong1.webp", 
        ], 
        "features": ["Full length protection", "Stylish design", "Fits over saree/kurta", "Lightweight"], 
        "description": "Full-length protection for maximum coverage. Stylish and functional for working women.", 
        "url": f"{BASE_URL}/product/womens-long-raincoat" 
    }, 
    { 
        "slug":     "kids-cartoon-raincoat", 
        "name":     "Kids Cartoon Rain Set", 
        "category": "Kids", 
        "price":    899, 
        "images": [ 
            f"{BASE_URL}/images/product-images/kidscartoon1.webp", 
        ], 
        "features": ["Cartoon prints", "Bag cover included", "Easy zipper", "Reflective strips"], 
        "description": "Colorful cartoon printed raincoat for kids. Keeps them dry and happy.", 
        "url": f"{BASE_URL}/product/kids-cartoon-raincoat" 
    }, 
    { 
        "slug":     "kids-solid-raincoat", 
        "name":     "Kids Solid Rain Set", 
        "category": "Kids", 
        "price":    899, 
        "images": [ 
            f"{BASE_URL}/images/product-images/kidssolid1.webp", 
        ], 
        "features": ["Solid colors", "School bag cover", "Durable material", "Safe for kids"], 
        "description": "Solid color raincoat for kids. Simple and elegant.", 
        "url": f"{BASE_URL}/product/kids-solid-raincoat" 
    }, 
    { 
        "slug":     "kids-rain-suit", 
        "name":     "Kids Rain Suit", 
        "category": "Kids", 
        "price":    999, 
        "images": [ 
            f"{BASE_URL}/images/product-images/kidssuit1.webp", 
        ], 
        "features": ["Full suit jacket+pant", "Premium material", "School ready", "Waterproof"], 
        "description": "Full protection rain suit for kids. Premium quality.", 
        "url": f"{BASE_URL}/product/kids-rain-suit" 
    }, 
    { 
        "slug":     "poncho", 
        "name":     "Poncho", 
        "category": "Unisex", 
        "price":    599, 
        "images": [ 
            f"{BASE_URL}/images/product-images/poncho1.webp", 
        ], 
        "features": ["One size fits all", "Easy to wear", "Budget friendly", "Compact"], 
        "description": "Simple and effective rain poncho. Good for short trips.", 
        "url": f"{BASE_URL}/product/poncho" 
    }, 
    { 
        "slug":     "windcheater", 
        "name":     "Windcheater", 
        "category": "Unisex", 
        "price":    799, 
        "images": [ 
            f"{BASE_URL}/images/product-images/windcheater1.webp", 
        ], 
        "features": ["Wind resistant", "Lightweight", "Casual style", "Youth appeal"], 
        "description": "Lightweight windcheater. Perfect for college students and young adults.", 
        "url": f"{BASE_URL}/product/windcheater" 
    }, 
    { 
        "slug":     "reversible-jacket", 
        "name":     "Reversible Rain Jacket", 
        "category": "Unisex", 
        "price":    1599, 
        "images": [ 
            f"{BASE_URL}/images/product-images/reversible1.webp", 
        ], 
        "features": ["Two looks in one", "Fully waterproof", "Premium fashion", "Versatile"], 
        "description": "Versatile reversible jacket. Two looks in one, fully waterproof.", 
        "url": f"{BASE_URL}/product/reversible-rain-jacket" 
    }, 
    { 
        "slug":     "hiviz-orange", 
        "name":     "Hi-Vis Orange Safety", 
        "category": "Safety", 
        "price":    1199, 
        "images": [ 
            f"{BASE_URL}/images/product-images/hiviz-orange1.webp", 
        ], 
        "features": ["High visibility orange", "Industrial grade", "Reflective tape", "Safety certified"], 
        "description": "High visibility orange safety raincoat for industrial and road workers.", 
        "url": f"{BASE_URL}/product/hi-vis-orange-safety-raincoat" 
    }, 
    { 
        "slug":     "hiviz-green", 
        "name":     "Hi-Vis Green Safety", 
        "category": "Safety", 
        "price":    1199, 
        "images": [ 
            f"{BASE_URL}/images/product-images/hiviz-green1.webp", 
        ], 
        "features": ["High visibility green", "Security grade", "Reflective tape", "All weather"], 
        "description": "High visibility green safety raincoat for security and road workers.", 
        "url": f"{BASE_URL}/product/hi-vis-green-safety-raincoat" 
    }, 
] 
 
 
def download_image(url, save_path): 
    """Download image from URL and save locally""" 
    try: 
        headers = { 
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" 
        } 
        response = requests.get(url, stream=True, timeout=15, headers=headers) 
        if response.status_code == 200: 
            os.makedirs(os.path.dirname(save_path), exist_ok=True) 
            with open(save_path, 'wb') as f: 
                for chunk in response.iter_content(1024): 
                    f.write(chunk) 
            return save_path 
        else: 
            print(f"Image download failed {url} — status {response.status_code}") 
    except Exception as e: 
        print(f"Error downloading {url}: {e}") 
    return None 
 
 
def scrape_product_page_live(slug): 
    """ 
    Try to scrape live data from product page. 
    Extracts images from img tags with Cloudinary or /images/ src. 
    """ 
    url = f"{BASE_URL}/product/{slug}" 
    try: 
        headers = { 
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" 
        } 
        resp = requests.get(url, timeout=15, headers=headers) 
        if resp.status_code != 200: 
            return [] 
 
        soup = BeautifulSoup(resp.text, "lxml") 
        images = [] 
 
        for img in soup.find_all("img"): 
            src = (img.get("src") or img.get("data-src") or 
                   img.get("data-lazy-src") or "") 
            if not src: 
                continue 
            # Only product images — from Cloudinary or product-images path 
            if ("cloudinary" in src or 
                "product-images" in src or 
                "product" in src.lower()): 
                if src.startswith("//"): 
                    src = "https:" + src 
                elif src.startswith("/"): 
                    src = BASE_URL + src 
                # Skip logos, icons, tiny images 
                if any(x in src for x in ["logo", "icon", "favicon", "background"]): 
                    continue 
                if src not in images: 
                    images.append(src) 
 
        return images 
    except Exception as e: 
        print(f"Live scrape failed for {slug}: {e}") 
        return [] 
 
 
def scrape_products(): 
    """ 
    Main scraper — uses hardcoded catalog + tries to fetch 
    live images for each product. 
    """ 
    from data.database import db, Product 
    from dashboard.socketio_events import broadcast_log 
 
    broadcast_log("System", "SCRAPING", 
        f"Starting product scrape from relaxfashionwear.in...") 
 
    scraped = [] 
 
    for product_data in PRODUCT_CATALOG: 
        try: 
            name    = product_data["name"] 
            slug    = product_data["slug"] 
            images  = list(product_data["images"])  # Start with known images 
 
            broadcast_log("System", "SCRAPING", 
                f"Scraping {name}...") 
 
            # Try to get additional live images 
            live_images = scrape_product_page_live(slug) 
            for img in live_images: 
                if img not in images: 
                    images.append(img) 
 
            # Download first 3 images locally 
            local_images = [] 
            products_dir = os.path.join("assets", "products", 
                slug.replace("-", "_")) 
            os.makedirs(products_dir, exist_ok=True) 
 
            for i, img_url in enumerate(images[:3]): 
                ext = "webp" if ".webp" in img_url else ( 
                      "png"  if ".png"  in img_url else "jpg") 
                save_path = os.path.join(products_dir, f"image_{i+1}.{ext}") 
 
                # Skip if already downloaded 
                if os.path.exists(save_path): 
                    local_images.append(save_path) 
                    continue 
 
                downloaded = download_image(img_url, save_path) 
                if downloaded: 
                    local_images.append(downloaded) 
                    broadcast_log("System", "IMAGE SAVED", 
                        f"{name} image {i+1} downloaded") 
 
            primary_image = local_images[0] if local_images else ( 
                            images[0]      if images       else None) 
 
            # Save or update in database 
            existing = Product.query.filter_by(name=name).first() 
 
            if not existing: 
                p = Product( 
                    name          = name, 
                    category      = product_data["category"], 
                    price         = product_data["price"], 
                    description   = product_data.get("description", ""), 
                    features      = ", ".join(product_data.get("features", [])), 
                    website_url   = product_data["url"], 
                    primary_image = primary_image, 
                    all_images    = ",".join(images), 
                    priority      = "HIGH" if product_data["price"] >= 1400 else "MEDIUM", 
                    active        = True, 
                    scraped_at    = datetime.utcnow() 
                ) 
                db.session.add(p) 
                broadcast_log("System", "PRODUCT ADDED", 
                    f"Added {name} — Rs{product_data['price']}") 
            else: 
                existing.category      = product_data["category"] 
                existing.price         = product_data["price"] 
                existing.description   = product_data.get("description", "") 
                existing.features      = ", ".join(product_data.get("features", [])) 
                existing.website_url   = product_data["url"] 
                existing.all_images    = ",".join(images) 
                existing.scraped_at    = datetime.utcnow() 
                if not existing.primary_image or not os.path.exists( 
                        existing.primary_image or ""): 
                    existing.primary_image = primary_image 
                broadcast_log("System", "PRODUCT UPDATED", 
                    f"Updated {name}") 
 
            db.session.commit() 
 
            scraped.append({ 
                "name":          name, 
                "images_found":  len(images), 
                "local_images":  len(local_images), 
                "primary_image": primary_image 
            }) 
 
        except Exception as e: 
            broadcast_log("System", "ERROR", 
                f"Failed to process {product_data.get('name','?')}: {str(e)[:80]}") 
            print(f"Product error: {e}") 
 
    broadcast_log("System", "SCRAPE COMPLETE", 
        f"Done — {len(scraped)} products processed") 
    return scraped 
 
 
def get_products_from_catalog(): 
    """ 
    Returns product catalog without scraping — instant. 
    Use this to seed DB without downloading images. 
    """ 
    from data.database import db, Product 
 
    for product_data in PRODUCT_CATALOG: 
        existing = Product.query.filter_by( 
            name=product_data["name"]).first() 
        if not existing: 
            p = Product( 
                name          = product_data["name"], 
                category      = product_data["category"], 
                price         = product_data["price"], 
                description   = product_data.get("description", ""), 
                features      = ", ".join(product_data.get("features", [])), 
                website_url   = product_data["url"], 
                primary_image = product_data["images"][0] if product_data["images"] else None, 
                all_images    = ",".join(product_data["images"]), 
                priority      = "HIGH", 
                active        = True 
            ) 
            db.session.add(p) 
    db.session.commit() 
    return Product.query.all() 
