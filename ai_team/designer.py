"""
designer.py — Relax Fashionwear
Full visual pipeline:
  1. Find product image
  2. Remove background (rembg)
  3. Upscale 2x
  4. Brand overlay (logo + website + price)
  5. Template (dark_cinematic etc.)
  6. Teal color grade
  7. Rain effects
  8. All aspect ratios (1:1, 4:5, 9:16)
  9. Save to Post DB + send Telegram preview
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
Teal aesthetic specialist. Pelhar Factory aesthetic.
Every pixel either builds trust or destroys it.
You never let a distorted product pass.
Your visuals stop the scroll in 0.3 seconds.
            """
        )

    def create_post_assets(self, brief, caption, post_id=None): 
        """Simplified visual pipeline — skips rembg to prevent crashes""" 
        product_name = brief.get("product_name", "RF Product") 
        template     = brief.get("template", "dark_cinematic") 
    
        self.log_and_broadcast( 
            f"🎨 Building visual for {product_name}...", "WORKING") 
    
        os.makedirs(config.GENERATED_DIR, exist_ok=True) 
        assets = {"final_image": "", "story_image": "", "ratios": {}, "success": False} 
    
        try: 
            # Get product image 
            product_image = self.get_product_image(product_name) 
    
            if product_image: 
                self.log_and_broadcast( 
                    f"Product image found — building post...", "WORKING") 
    
                # Skip rembg — use image directly on template 
                from visual.templates import apply_template, generate_all_ratios 
    
                # Apply template directly — no background removal needed 
                final  = apply_template(product_image, template, brief) 
                ratios = generate_all_ratios(final) 
    
                assets["final_image"] = final 
                assets["story_image"] = ratios.get("9_16", final) 
                assets["ratios"]      = ratios 
                assets["success"]     = True 
    
                self.log_and_broadcast( 
                    f"✅ Post image ready — {os.path.basename(final)}", "VISUAL COMPLETE") 
            else: 
                self.log_and_broadcast( 
                    f"No product image — using text fallback", "WARNING") 
                from visual.templates import _create_no_image_fallback 
                final = _create_no_image_fallback(brief, template) 
                assets["final_image"] = final 
                assets["success"]     = bool(final) 
    
            if post_id and assets["final_image"]: 
                self._save_image_to_post(post_id, assets["final_image"]) 
    
            self._send_visual_preview(brief, assets["final_image"], post_id) 
            return assets 
    
        except Exception as e: 
            self.log_and_broadcast(f"Designer error: {str(e)[:150]}", "ERROR") 
            import traceback 
            traceback.print_exc() 
            return assets 

    def get_product_image(self, product_name): 
        """Find product image — checks DB first, then folder fuzzy match""" 
        import os 
    
        # METHOD 1 — Check database for stored image path 
        try: 
            from dashboard.app import get_app 
            app = get_app() 
            with app.app_context(): 
                from data.database import Product 
                products = Product.query.filter_by(active=True).all() 
                for p in products: 
                    if p.name.lower().strip() == product_name.lower().strip(): 
                        # Found exact match in DB 
                        if p.primary_image: 
                            img = p.primary_image.strip() 
                            # Direct URL (Cloudinary etc) 
                            if img.startswith("http"): 
                                self.log_and_broadcast( 
                                    f"Using DB image URL for {product_name}", "IMAGE FOUND") 
                                return img 
                            # Local path 
                            if os.path.exists(img): 
                                self.log_and_broadcast( 
                                    f"Using DB local image for {product_name}", "IMAGE FOUND") 
                                return img 
                        # Check all_images 
                        if p.all_images: 
                            for img in p.all_images.split(","): 
                                img = img.strip() 
                                if img and img != 'None': 
                                    if img.startswith("http"): 
                                        return img 
                                    if os.path.exists(img): 
                                        return img 
        except Exception as e: 
            self.log_and_broadcast(f"DB image lookup failed: {str(e)[:60]}", "WARNING") 
    
        # METHOD 2 — Fuzzy folder search in assets/products/ 
        try: 
            products_dir = os.path.join("assets", "products") 
            if not os.path.exists(products_dir): 
                return None 
    
            # Build search keywords from product name 
            # Remove common words that don't help matching 
            name_words = [w.lower() for w in product_name.split() 
                          if w.lower() not in ['set', 'rain', 'the', 'a', 'and']] 
    
            best_match = None 
            best_score = 0 
    
            for item in os.listdir(products_dir): 
                item_path = os.path.join(products_dir, item) 
                item_lower = item.lower().replace("_", " ").replace("-", " ") 
    
                # Score: how many keywords match 
                score = sum(1 for w in name_words if w in item_lower) 
    
                if score > best_score: 
                    # Check this folder/file has an image 
                    if os.path.isdir(item_path): 
                        imgs = [f for f in os.listdir(item_path) 
                                if f.lower().endswith(('.jpg','.jpeg','.png','.webp'))] 
                        if imgs: 
                            best_score = score 
                            best_match = os.path.join(item_path, imgs[0]) 
                    elif os.path.isfile(item_path) and item.lower().endswith( 
                            ('.jpg','.jpeg','.png','.webp')): 
                        best_score = score 
                        best_match = item_path 
    
            if best_match and best_score > 0: 
                self.log_and_broadcast( 
                    f"Fuzzy matched '{product_name}' to '{best_match}' (score={best_score})", 
                    "IMAGE FOUND" 
                ) 
                return best_match 
    
            # METHOD 3 — Use ANY available image as last resort 
            for item in os.listdir(products_dir): 
                item_path = os.path.join(products_dir, item) 
                if os.path.isdir(item_path): 
                    imgs = [f for f in os.listdir(item_path) 
                            if f.lower().endswith(('.jpg','.jpeg','.png','.webp'))] 
                    if imgs: 
                        img_path = os.path.join(item_path, imgs[0]) 
                        self.log_and_broadcast( 
                            f"No match for '{product_name}' — using fallback image", 
                            "WARNING" 
                        ) 
                        return img_path 
                elif os.path.isfile(item_path) and item.lower().endswith( 
                        ('.jpg','.jpeg','.png','.webp')): 
                    return item_path 
    
        except Exception as e: 
            self.log_and_broadcast(f"Folder search failed: {str(e)[:80]}", "ERROR") 
    
        return None 

    def _generate_text_only_image(self, brief):
        """Branded 1080x1080 teal text image when no product photo exists."""
        import time
        try:
            from PIL import Image, ImageDraw, ImageFont

            bg   = Image.new("RGB", (1080, 1080), (0, 128, 128))
            draw = ImageDraw.Draw(bg)

            product_name = brief.get("product_name", "Relax Fashionwear")
            price        = brief.get("price", "")

            try:
                font_big   = ImageFont.truetype(str(config.ASSETS_DIR / "fonts" / "BebasNeue-Regular.ttf"), 120)
                font_med   = ImageFont.truetype(str(config.ASSETS_DIR / "fonts" / "Montserrat-Bold.ttf"), 50)
                font_small = ImageFont.truetype(str(config.ASSETS_DIR / "fonts" / "Montserrat-Bold.ttf"), 35)
            except:
                font_big = font_med = font_small = ImageFont.load_default()

            draw.text((540, 80),   "RELAX FASHIONWEAR",  font=font_med,   fill=(255,255,255), anchor="mt")
            draw.text((540, 400),  product_name.upper(), font=font_big,   fill=(255,255,255), anchor="mm")
            if price:
                draw.text((540, 600), f"Rs.{price}",     font=font_med,   fill=(255,255,0),   anchor="mm")
            draw.rectangle([0, 900, 1080, 980], fill=(200, 0, 0))
            draw.text((540, 940),  "Flat Rs89 OFF — Prepaid Orders",      font=font_small, fill=(255,255,255), anchor="mm")
            draw.text((540, 1020), "relaxfashionwear.in",                  font=font_small, fill=(200,255,255), anchor="mm")

            timestamp   = int(time.time())
            output_path = config.GENERATED_DIR / f"text_only_{timestamp}.png"
            bg.save(str(output_path))

            self.log_and_broadcast(
                f"✅ [Designer] Text-only image created — upload product images at /products for real visuals",
                "FALLBACK IMAGE"
            )
            return str(output_path)

        except Exception as e:
            self.log_and_broadcast(f"❌ [Designer] Fallback image failed: {str(e)[:100]}", "ERROR")
            return ""

    def _save_image_to_post(self, post_id, image_path):
        """Save generated image path to Post database record."""
        try:
            from dashboard.app import get_app
            app = get_app()
            with app.app_context():
                from data.database import db, Post
                post = Post.query.get(post_id)
                if post:
                    post.image_path = image_path
                    db.session.commit()
                    self.log_and_broadcast(f"💾 [Designer] Image saved to Post #{post_id}", "SAVED")
        except Exception as e:
            self.log_and_broadcast(f"⚠️ [Designer] Could not save to DB: {str(e)[:80]}", "WARNING")

    def _send_visual_preview(self, brief, image_path, post_id):
        """Send image preview to Krishna's Telegram."""
        try:
            from distribution.telegram_bot import send_image
            send_image(
                image_path,
                f"🎨 Visual Ready!\n"
                f"Product: {brief.get('product_name')}\n"
                f"Template: {brief.get('template', 'dark_cinematic')}\n"
                f"Post #{post_id} — Approve in pipeline dashboard"
            )
            self.log_and_broadcast("📱 [Designer] Visual preview sent to Telegram", "TELEGRAM SENT")
        except Exception as e:
            self.log_and_broadcast(f"⚠️ [Designer] Telegram send skipped: {str(e)[:80]}", "WARNING")

    def select_template(self, brief):
        """Auto-select best template from brief."""
        category  = brief.get("category", "").lower()
        post_type = brief.get("post_type", "static").lower()
        ad        = brief.get("ad_potential", False)
        if "biker"  in category:   return "dark_cinematic"
        if "women"  in category:   return "premium_minimal"
        if "kids"   in category:   return "lifestyle_emotion"
        if "safety" in category:   return "feature_breakdown"
        if ad:                      return "urgency_offer"
        if "carousel" in post_type: return "feature_breakdown"
        return "dark_cinematic"
