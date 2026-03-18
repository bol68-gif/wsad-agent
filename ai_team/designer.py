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
        """Full visual pipeline. Returns dict with image paths."""
        product_name = brief.get("product_name", "RF Product")
        template     = brief.get("template", "dark_cinematic")

        self.log_and_broadcast(
            f"🎨 [Designer] VISUAL PIPELINE STARTING — Product: {product_name} | Template: {template}",
            "WORKING"
        )
        os.makedirs(config.GENERATED_DIR, exist_ok=True)
        assets = {"final_image": "", "story_image": "", "ratios": {}, "success": False}

        # STEP 1 — Find product image
        self.log_and_broadcast(
            f"🎨 [Designer] Step 1/8 — Searching assets/products/ for {product_name}...",
            "WORKING"
        )
        product_image = self.get_product_image(product_name)

        if not product_image:
            self.log_and_broadcast(
                f"⚠️ [Designer] No product image found — generating text-only fallback. Upload images at /products",
                "WARNING"
            )
            fallback = self._generate_text_only_image(brief)
            assets["final_image"] = fallback
            if post_id:
                self._save_image_to_post(post_id, fallback)
            return assets

        self.log_and_broadcast(f"✅ [Designer] Image found — {product_image}", "IMAGE FOUND")

        try:
            # STEP 2 — Remove background
            self.log_and_broadcast("🎨 [Designer] Step 2/8 — Removing background with rembg AI...", "WORKING")
            from visual.enhancer import remove_background
            no_bg = remove_background(product_image)
            self.log_and_broadcast(f"✅ [Designer] Background removed — {os.path.basename(no_bg)}", "BG REMOVED")

            # STEP 3 — Upscale
            self.log_and_broadcast("🎨 [Designer] Step 3/8 — Upscaling 2x with LANCZOS...", "WORKING")
            from visual.enhancer import upscale_image
            upscaled = upscale_image(no_bg, scale=2)
            self.log_and_broadcast(f"✅ [Designer] Upscaled 2x — {os.path.basename(upscaled)}", "UPSCALED")

            # STEP 4 — Brand overlay
            self.log_and_broadcast("🎨 [Designer] Step 4/8 — Applying logo + website + price overlay...", "WORKING")
            from visual.brand_overlay import apply_overlay
            overlaid = apply_overlay(upscaled, brief)
            self.log_and_broadcast(f"✅ [Designer] Brand overlay done — logo + relaxfashionwear.in + Rs{brief.get('price','')}", "OVERLAY DONE")

            # STEP 5 — Template
            self.log_and_broadcast(f"🎨 [Designer] Step 5/8 — Applying {template} template...", "WORKING")
            from visual.templates import apply_template
            templated = apply_template(overlaid, template, brief)
            self.log_and_broadcast(f"✅ [Designer] Template '{template}' applied", "TEMPLATE DONE")

            # STEP 6 — Teal color grade
            self.log_and_broadcast("🎨 [Designer] Step 6/8 — Teal cinematic color grade via OpenCV...", "WORKING")
            from visual.color_grader import apply_teal_grade
            graded = apply_teal_grade(templated)
            self.log_and_broadcast("✅ [Designer] Teal grade applied — cinematic look done", "GRADED")

            # STEP 7 — Rain effects
            self.log_and_broadcast("🎨 [Designer] Step 7/8 — Adding rain overlay effects...", "WORKING")
            from visual.rain_effects import apply_rain
            final = apply_rain(graded, intensity="medium")
            self.log_and_broadcast(f"✅ [Designer] Rain effects applied — {os.path.basename(final)}", "RAIN DONE")

            # STEP 8 — All aspect ratios
            self.log_and_broadcast("🎨 [Designer] Step 8/8 — Generating 1:1, 4:5, 9:16 ratios...", "WORKING")
            from visual.templates import generate_all_ratios
            ratios = generate_all_ratios(final)
            self.log_and_broadcast(
                f"✅ [Designer] {len(ratios)} ratios ready — Feed 1080x1080 | Portrait 1080x1350 | Story 1080x1920",
                "ALL RATIOS DONE"
            )

            assets["final_image"] = final
            assets["story_image"] = ratios.get("9_16", final)
            assets["ratios"]      = ratios
            assets["success"]     = True

            self.log_and_broadcast(
                f"🎨 [Designer] ✅ FULL PIPELINE COMPLETE — "
                f"Final: {os.path.basename(final)} | "
                f"Ratios: {list(ratios.keys())}",
                "VISUAL COMPLETE"
            )

            if post_id:
                self._save_image_to_post(post_id, final)
            self._send_visual_preview(brief, final, post_id)
            return assets

        except Exception as e:
            self.log_and_broadcast(f"❌ [Designer] Pipeline error: {str(e)[:200]}", "ERROR")
            fallback = self._generate_text_only_image(brief)
            assets["final_image"] = fallback
            if post_id:
                self._save_image_to_post(post_id, fallback)
            return assets

    def get_product_image(self, product_name):
        """Find product image in assets/products/ folder."""
        try:
            products_dir = os.path.join("assets", "products")
            if not os.path.exists(products_dir):
                self.log_and_broadcast(
                    "⚠️ [Designer] assets/products/ folder missing — create it and upload images at /products page",
                    "WARNING"
                )
                return None

            name_clean = product_name.lower().replace(" ", "").replace("-", "")

            for item in os.listdir(products_dir):
                item_clean = item.lower().replace(" ", "").replace("-", "")
                item_path  = os.path.join(products_dir, item)

                if os.path.isdir(item_path):
                    if name_clean in item_clean or item_clean in name_clean:
                        images = [f for f in os.listdir(item_path)
                                  if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
                        if images:
                            return os.path.join(item_path, images[0])
                elif os.path.isfile(item_path):
                    if name_clean in item_clean and any(
                        item_path.lower().endswith(ext)
                        for ext in ['.jpg', '.jpeg', '.png', '.webp']
                    ):
                        return item_path

            # Fallback — any available image
            self.log_and_broadcast(
                f"⚠️ [Designer] No exact match for '{product_name}' — using any available product image",
                "WARNING"
            )
            for item in os.listdir(products_dir):
                item_path = os.path.join(products_dir, item)
                if os.path.isdir(item_path):
                    images = [f for f in os.listdir(item_path)
                              if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
                    if images:
                        return os.path.join(item_path, images[0])
                elif item.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    return item_path

            return None
        except Exception as e:
            self.log_and_broadcast(f"❌ [Designer] Image search error: {str(e)[:100]}", "ERROR")
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
