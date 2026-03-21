""" 
designer.py — Relax Fashionwear 
Bulletproof visual pipeline. 
ALWAYS generates an image — never returns empty. 
""" 
 
from ai_team.base_agent import BaseAgent 
import os 
import config 
 
 
class Designer(BaseAgent): 
    def __init__(self): 
        super().__init__( 
            name        = "Designer", 
            role        = "Senior Brand Designer", 
            personality = """ 
You are RF Senior Brand Designer. 
Teal aesthetic specialist. Every pixel builds trust. 
Your visuals stop the scroll in 0.3 seconds. 
            """ 
        ) 
 
    def create_post_assets(self, brief, caption, post_id=None): 
        product_name = brief.get("product_name", "RF Product") 
        template     = brief.get("template", "dark_cinematic") 
 
        self.log_and_broadcast( 
            f"🎨 Designer starting for: {product_name} | Template: {template}", 
            "WORKING" 
        ) 
 
        os.makedirs(str(config.GENERATED_DIR), exist_ok=True) 
        final_image = None 
 
        # ── ATTEMPT 1: Real product image pipeline ── 
        try: 
            product_image = self.get_product_image(product_name) 
            self.log_and_broadcast( 
                f"Product image search result: {product_image}", 
                "WORKING" 
            ) 
 
            if product_image: 
                self.log_and_broadcast( 
                    f"Using product image: {str(product_image)[:80]}", 
                    "IMAGE FOUND" 
                ) 
                from visual.templates import apply_template 
                final_image = apply_template(product_image, template, brief) 
                self.log_and_broadcast( 
                    f"Template applied: {final_image}", 
                    "TEMPLATE DONE" 
                ) 
        except Exception as e: 
            self.log_and_broadcast( 
                f"Product pipeline error: {str(e)[:120]}", 
                "WARNING" 
            ) 
            final_image = None 
 
        # ── ATTEMPT 2: Fallback brand image — ALWAYS works ── 
        if not final_image or not os.path.exists(str(final_image)): 
            self.log_and_broadcast( 
                "Using branded fallback image", 
                "FALLBACK" 
            ) 
            try: 
                from visual.templates import _create_no_image_fallback 
                final_image = _create_no_image_fallback(brief, template) 
                self.log_and_broadcast( 
                    f"Fallback created: {final_image}", 
                    "FALLBACK DONE" 
                ) 
            except Exception as e: 
                self.log_and_broadcast( 
                    f"Fallback failed: {str(e)[:80]} — creating emergency image", 
                    "ERROR" 
                ) 
                final_image = self._emergency_image(brief) 
 
        # ── SAVE TO DATABASE ── 
        if final_image and os.path.exists(str(final_image)): 
            if post_id: 
                self._save_image_to_post(post_id, final_image) 
            self.log_and_broadcast( 
                f"✅ Image ready: {os.path.basename(str(final_image))}", 
                "VISUAL COMPLETE" 
            ) 
        else: 
            self.log_and_broadcast( 
                "⚠️ No image generated — post will show placeholder", 
                "WARNING" 
            ) 
            final_image = "" 
 
        # Generate ratios 
        ratios = {} 
        if final_image and os.path.exists(str(final_image)): 
            try: 
                from visual.templates import generate_all_ratios 
                ratios = generate_all_ratios(final_image) 
            except Exception as e: 
                self.log_and_broadcast(f"Ratios error: {str(e)[:60]}", "WARNING") 
 
        assets = { 
            "final_image": final_image, 
            "story_image": ratios.get("9_16", final_image), 
            "ratios":      ratios, 
            "success":     bool(final_image) 
        } 
 
        # Send Telegram preview 
        try: 
            self._send_visual_preview(brief, final_image, post_id) 
        except Exception as e: 
            self.log_and_broadcast(f"Telegram preview: {str(e)[:60]}", "WARNING") 
 
        return assets 
 
    def _emergency_image(self, brief): 
        """Last resort — pure PIL, no dependencies, always works""" 
        try: 
            from PIL import Image, ImageDraw 
            import time 
            W, H  = 1080, 1080 
            name  = brief.get("product_name", "RF Product") 
            price = str(brief.get("price", "")) 
 
            img  = Image.new("RGB", (W, H), (0, 90, 90)) 
            draw = ImageDraw.Draw(img) 
 
            # Simple text 
            font = None 
            try: 
                from PIL import ImageFont 
                font = ImageFont.truetype( 
                    str(config.ASSETS_DIR / "fonts" / "BebasNeue-Regular.ttf"), 80) 
            except: 
                font = ImageFont.load_default() 
 
            draw.text((W//2, 200), "RELAX FASHIONWEAR", 
                      font=font, fill=(255,255,255), anchor="mm") 
            draw.text((W//2, 400), name.upper(), 
                      font=font, fill=(255,255,0), anchor="mm") 
            if price: 
                draw.text((W//2, 560), f"Rs. {price}", 
                          font=font, fill=(255,255,255), anchor="mm") 
            draw.rectangle([0, H-80, W, H-40], fill=(180,20,20)) 
            draw.text((W//2, H-60), "FLAT Rs89 OFF — PREPAID", 
                      font=font, fill=(255,255,255), anchor="mm") 
            draw.rectangle([0, H-40, W, H], fill=(0,40,40)) 
            draw.text((W//2, H-20), "relaxfashionwear.in", 
                      font=font, fill=(0,200,200), anchor="mm") 
 
            path = str(config.GENERATED_DIR / f"emergency_{int(time.time())}.jpg") 
            img.save(path, quality=95) 
            self.log_and_broadcast(f"Emergency image created: {path}", "EMERGENCY") 
            return path 
        except Exception as e: 
            self.log_and_broadcast(f"Emergency image failed: {e}", "ERROR") 
            return "" 
 
    def get_product_image(self, product_name): 
        """Get product image — DB first, then folder, then URL download""" 
        import requests, tempfile 
 
        name_key = product_name.lower().strip() 
 
        KNOWN_URLS = { 
            "eliteshield rain set":   "https://res.cloudinary.com/dipnajpc1/image/upload/v1773572785/z10fqqfx5zibnrfhhzma.jpg", 
            "urban rain suit":        "https://www.relaxfashionwear.in/images/product-images/blueyellow1.webp", 
            "classic rain set":       "https://www.relaxfashionwear.in/images/product-images/green1.webp", 
            "pro biker rain set":     "https://www.relaxfashionwear.in/images/product-images/bluebiker1.webp", 
            "women long rain coat":   "https://www.relaxfashionwear.in/images/product-images/womenlong1.webp", 
            "kids cartoon rain set":  "https://www.relaxfashionwear.in/images/product-images/kidscartoon1.webp", 
            "kids solid rain set":    "https://www.relaxfashionwear.in/images/product-images/kidssolid1.webp", 
            "kids rain suit":         "https://www.relaxfashionwear.in/images/product-images/kidssuit1.webp", 
            "poncho":                 "https://www.relaxfashionwear.in/images/product-images/poncho1.webp", 
            "windcheater":            "https://www.relaxfashionwear.in/images/product-images/windcheater1.webp", 
            "reversible rain jacket": "https://www.relaxfashionwear.in/images/product-images/reversible1.webp", 
            "hi-vis orange safety":   "https://www.relaxfashionwear.in/images/product-images/hiviz-orange1.webp", 
            "hi-vis green safety":    "https://www.relaxfashionwear.in/images/product-images/hiviz-green1.webp", 
        } 
 
        # Step 1 — Check DB 
        try: 
            from dashboard.app import get_app 
            app = get_app() 
            with app.app_context(): 
                from data.database import Product 
                for p in Product.query.filter_by(active=True).all(): 
                    if p.name.lower().strip() == name_key: 
                        if p.primary_image: 
                            img = p.primary_image.strip() 
                            if img.startswith("http"): 
                                return self._download_url(img) 
                            if os.path.exists(img): 
                                return img 
                        if p.all_images: 
                            for img in p.all_images.split(","): 
                                img = img.strip() 
                                if img and img != 'None': 
                                    if img.startswith("http"): 
                                        return self._download_url(img) 
                                    if os.path.exists(img): 
                                        return img 
        except Exception as e: 
            self.log_and_broadcast(f"DB lookup: {str(e)[:60]}", "WARNING") 
 
        # Step 2 — Known URLs 
        for key, url in KNOWN_URLS.items(): 
            if key in name_key or any( 
                    w in name_key for w in key.split() 
                    if w not in ['set','rain','the','a']): 
                downloaded = self._download_url(url) 
                if downloaded: 
                    return downloaded 
 
        # Step 3 — Local folder fuzzy search 
        try: 
            products_dir = os.path.join("assets", "products") 
            if os.path.exists(products_dir): 
                name_words = [w for w in product_name.lower().split() 
                              if w not in ['set','rain','the','a','and','coat']] 
                best, best_score = None, 0 
                for item in os.listdir(products_dir): 
                    item_path  = os.path.join(products_dir, item) 
                    item_lower = item.lower().replace("_"," ").replace("-"," ") 
                    score      = sum(1 for w in name_words if w in item_lower) 
                    if score > best_score: 
                        if os.path.isdir(item_path): 
                            imgs = [f for f in os.listdir(item_path) 
                                    if f.lower().endswith(('.jpg','.jpeg','.png','.webp'))] 
                            if imgs: 
                                best_score = score 
                                best       = os.path.join(item_path, imgs[0]) 
                        elif item.lower().endswith(('.jpg','.jpeg','.png','.webp')): 
                            best_score = score 
                            best       = item_path 
                if best and best_score > 0: 
                    return best 
                # Any image at all 
                for item in os.listdir(products_dir): 
                    item_path = os.path.join(products_dir, item) 
                    if os.path.isdir(item_path): 
                        imgs = [f for f in os.listdir(item_path) 
                                if f.lower().endswith(('.jpg','.jpeg','.png','.webp'))] 
                        if imgs: 
                            self.log_and_broadcast( 
                                f"Using fallback image from products folder", "WARNING") 
                            return os.path.join(item_path, imgs[0]) 
        except Exception as e: 
            self.log_and_broadcast(f"Folder search: {str(e)[:60]}", "ERROR") 
 
        return None 
 
    def _download_url(self, url): 
        """Download image URL to temp file""" 
        import requests, tempfile, time 
        try: 
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"} 
            resp    = requests.get(url, timeout=20, headers=headers) 
            if resp.status_code == 200 and len(resp.content) > 1000: 
                ext = ".webp" if ".webp" in url else ( 
                      ".png"  if ".png"  in url else ".jpg") 
                os.makedirs(str(config.GENERATED_DIR), exist_ok=True) 
                path = str(config.GENERATED_DIR / f"prod_{int(time.time())}{ext}") 
                with open(path, "wb") as f: 
                    f.write(resp.content) 
                self.log_and_broadcast( 
                    f"Downloaded: {os.path.basename(path)} ({len(resp.content)//1024}KB)", 
                    "IMAGE READY" 
                ) 
                return path 
            else: 
                self.log_and_broadcast( 
                    f"Download failed: {resp.status_code} — {url[:60]}", "WARNING") 
        except Exception as e: 
            self.log_and_broadcast(f"Download error: {str(e)[:80]}", "WARNING") 
        return None 
 
    def _save_image_to_post(self, post_id, image_path): 
        """Save image path to DB — explicit logging""" 
        try: 
            from dashboard.app import get_app 
            app = get_app() 
            with app.app_context(): 
                from data.database import db, Post 
                post = Post.query.get(post_id) 
                if post: 
                    post.image_path = str(image_path) 
                    db.session.commit() 
                    self.log_and_broadcast( 
                        f"✅ Saved image to Post #{post_id}: {os.path.basename(str(image_path))}", 
                        "SAVED" 
                    ) 
                else: 
                    self.log_and_broadcast( 
                        f"Post #{post_id} not found in DB", "ERROR") 
        except Exception as e: 
            self.log_and_broadcast( 
                f"Save to DB failed: {str(e)[:100]}", "ERROR") 
 
    def _send_visual_preview(self, brief, image_path, post_id): 
        """Send image to Telegram""" 
        try: 
            if not image_path or not os.path.exists(str(image_path)): 
                return 
            from distribution.telegram_bot import send_image 
            send_image( 
                str(image_path), 
                f"🎨 Visual Ready!\n" 
                f"Product: {brief.get('product_name')}\n" 
                f"Template: {brief.get('template')}\n" 
                f"Post #{post_id}" 
            ) 
        except Exception as e: 
            self.log_and_broadcast( 
                f"Telegram preview skipped: {str(e)[:60]}", "WARNING") 
 
    def select_template(self, brief): 
        category  = brief.get("category", "").lower() 
        post_type = brief.get("post_type", "static").lower() 
        if "biker"  in category:    return "dark_cinematic" 
        if "women"  in category:    return "premium_minimal" 
        if "kids"   in category:    return "lifestyle_emotion" 
        if "safety" in category:    return "feature_breakdown" 
        if "carousel" in post_type: return "feature_breakdown" 
        return "dark_cinematic" 
