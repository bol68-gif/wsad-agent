"""
templates.py — Relax Fashionwear
6 premium Instagram templates with proper product placement.
Inspired by Zeel, boAt, Decathlon India feed quality.

Product image is placed LARGE and correctly positioned on the RIGHT.
Text zone on the LEFT — no overlap.
Drop shadow, teal rim light, proper text zones — Zeel quality.
"""

import os
import time
import requests
import tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import cv2
import numpy as np
import config

# ── SIZES ────────────────────────────────────────────────────────────────────
SIZES = {
    "1x1":   (1080, 1080),
    "4x5":   (1080, 1350),
    "9x16":  (1080, 1920),
}

COLORS = {
    "teal":      (0, 128, 128),
    "dark_teal": (0, 80, 80),
    "black":     (10, 10, 10),
    "white":     (255, 255, 255),
    "grey":      (40, 40, 40),
    "red":       (220, 38, 38),
    "gold":      (245, 158, 11),
}

# ── HELPERS ──────────────────────────────────────────────────────────────────

def _get_font(size, bold=False):
    """Load font from config or fallback"""
    font_path = config.FONTS_DIR / ("BebasNeue-Bold.ttf" if bold else "Montserrat-Medium.ttf")
    if not font_path.exists():
        return ImageFont.load_default()
    return ImageFont.truetype(str(font_path), size)

def _add_rim_light(product_img, color=COLORS["teal"]):
    """Adds a subtle teal rim glow around the product edges"""
    if product_img.mode != 'RGBA':
        return product_img
    
    # Extract alpha mask
    alpha = product_img.getchannel('A')
    
    # Create glow
    glow = Image.new('RGBA', product_img.size, color + (0,))
    draw = ImageDraw.Draw(glow)
    
    # Outer glow
    mask_blur = alpha.filter(ImageFilter.GaussianBlur(radius=15))
    glow_img = Image.new('RGBA', product_img.size, color + (100,))
    glow_final = Image.composite(glow_img, Image.new('RGBA', product_img.size, (0,0,0,0)), mask_blur)
    
    # Inner rim light
    inner_mask = alpha.filter(ImageFilter.GaussianBlur(radius=2))
    rim = Image.new('RGBA', product_img.size, color + (255,))
    rim_final = Image.composite(rim, Image.new('RGBA', product_img.size, (0,0,0,0)), inner_mask)
    
    # Combine
    combined = Image.alpha_composite(glow_final, rim_final)
    return Image.alpha_composite(combined, product_img)

def _add_drop_shadow(product_img):
    """Adds a grounded shadow under the product"""
    shadow_w = int(product_img.width * 0.8)
    shadow_h = int(product_img.height * 0.1)
    shadow = Image.new('RGBA', (shadow_w, shadow_h), (0,0,0,0))
    draw = ImageDraw.Draw(shadow)
    draw.ellipse([0, 0, shadow_w, shadow_h], fill=(0,0,0,80))
    return shadow.filter(ImageFilter.GaussianBlur(radius=15))

# ── TEMPLATES ────────────────────────────────────────────────────────────────

def template_dark_cinematic(canvas, product, brief):
    """Zeel Style: Deep black background with teal accent lighting"""
    draw = ImageDraw.Draw(canvas)
    W, H = canvas.size
    
    # 1. Background Gradient
    for y in range(H):
        r = int(10 + (y/H)*15)
        g = int(10 + (y/H)*30)
        b = int(10 + (y/H)*30)
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    
    # Teal side glow
    glow = Image.new('RGBA', (W, H), (0,0,0,0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse([W*0.6, H*0.2, W*1.2, H*0.8], fill=COLORS["teal"] + (40,))
    canvas.paste(glow.filter(ImageFilter.GaussianBlur(30)), (0,0), glow)

    # 2. Product Placement (RIGHT)
    pw = int(W * 0.82)
    ph = int(product.height * (pw / product.width))
    product = product.resize((pw, ph), Image.LANCZOS)
    product = _add_rim_light(product)
    
    # Shadow
    shadow = _add_drop_shadow(product)
    canvas.paste(shadow, (int(W*0.35), int(H*0.75)), shadow)
    
    # Product
    canvas.paste(product, (int(W*0.25), int(H*0.15)), product)

    # 3. Text Zone (LEFT)
    draw.text((60, H*0.2), brief.get("product_name", "RF").upper(), font=_get_font(80, True), fill=COLORS["white"])
    draw.text((60, H*0.2 + 90), brief.get("category", "RAINWEAR").upper(), font=_get_font(30), fill=COLORS["teal"])
    
    # Price Tag
    draw.rectangle([60, H*0.7, 280, H*0.7 + 60], fill=COLORS["teal"])
    draw.text((85, H*0.7 + 10), f"Rs {brief.get('price', '1599')}", font=_get_font(35, True), fill=COLORS["white"])

def template_premium_minimal(canvas, product, brief):
    """Clean white/grey minimalist look"""
    draw = ImageDraw.Draw(canvas)
    W, H = canvas.size
    canvas.paste(COLORS["white"], [0, 0, W, H])
    
    # Accent bar
    draw.rectangle([0, 0, 40, H], fill=COLORS["teal"])
    
    # Product
    pw = int(W * 0.75)
    ph = int(product.height * (pw / product.width))
    product = product.resize((pw, ph), Image.LANCZOS)
    canvas.paste(product, (int(W*0.3), int(H*0.2)), product)
    
    # Text
    draw.text((100, H*0.3), brief.get("product_name", "RF"), font=_get_font(70, True), fill=COLORS["black"])
    draw.text((100, H*0.3 + 80), "PREMIUM COLLECTION", font=_get_font(25), fill=COLORS["grey"])

def template_urgency_offer(canvas, product, brief):
    """Bold teal with Red Urgency offer"""
    draw = ImageDraw.Draw(canvas)
    W, H = canvas.size
    
    # Teal Gradient
    for i in range(H):
        color = (0, int(80 + (i/H)*48), int(80 + (i/H)*48))
        draw.line([(0, i), (W, i)], fill=color)

    # Product
    pw = int(W * 0.8)
    ph = int(product.height * (pw / product.width))
    product = product.resize((pw, ph), Image.LANCZOS)
    canvas.paste(product, (int(W*0.3), int(H*0.2)), product)

    # Offer Badge
    draw.ellipse([60, 60, 260, 260], fill=COLORS["red"])
    draw.text((100, 110), "Rs 89", font=_get_font(40, True), fill=COLORS["white"])
    draw.text((115, 160), "OFF", font=_get_font(30, True), fill=COLORS["white"])

def template_feature_breakdown(canvas, product, brief):
    """Dark grid with numbered features"""
    draw = ImageDraw.Draw(canvas)
    W, H = canvas.size
    canvas.paste(COLORS["black"], [0, 0, W, H])
    
    # Grid lines
    for i in range(0, W, 100): draw.line([(i, 0), (i, H)], fill=(30, 30, 30))
    for i in range(0, H, 100): draw.line([(0, i), (W, i)], fill=(30, 30, 30))

    # Product
    pw = int(W * 0.6)
    ph = int(product.height * (pw / product.width))
    product = product.resize((pw, ph), Image.LANCZOS)
    canvas.paste(product, (int(W*0.4), int(H*0.25)), product)

    # Features
    features = brief.get("features", ["Heat Sealed", "3000mm Waterproof", "Reflective"])
    for i, f in enumerate(features[:4]):
        y = H*0.3 + (i*120)
        draw.ellipse([60, y, 100, y+40], fill=COLORS["teal"])
        draw.text((72, y+8), str(i+1), font=_get_font(20, True), fill=COLORS["white"])
        draw.text((120, y+5), f.upper(), font=_get_font(25, True), fill=COLORS["white"])

def template_lifestyle_emotion(canvas, product, brief):
    """Blurred atmospheric background with product focus"""
    draw = ImageDraw.Draw(canvas)
    W, H = canvas.size
    
    # Dark Greenish background
    canvas.paste((10, 30, 30), [0, 0, W, H])
    
    # Product
    pw = int(W * 0.85)
    ph = int(product.height * (pw / product.width))
    product = product.resize((pw, ph), Image.LANCZOS)
    product = _add_rim_light(product)
    canvas.paste(product, (int(W*0.1), int(H*0.15)), product)

    # Emotional text at bottom
    text = "READY FOR THE MONSOON"
    tw = draw.textlength(text, font=_get_font(40, True))
    draw.text(((W-tw)//2, H*0.85), text, font=_get_font(40, True), fill=COLORS["white"])

def template_social_proof(canvas, product, brief):
    """Review style with stars"""
    draw = ImageDraw.Draw(canvas)
    W, H = canvas.size
    canvas.paste((15, 25, 20), [0, 0, W, H])

    # Product (Small on side)
    pw = int(W * 0.5)
    ph = int(product.height * (pw / product.width))
    product = product.resize((pw, ph), Image.LANCZOS)
    canvas.paste(product, (int(W*0.5), int(H*0.4)), product)

    # Review box
    draw.rectangle([50, H*0.2, W-50, H*0.35], fill=(30, 40, 35), outline=COLORS["teal"], width=2)
    
    # Stars
    stars = "★★★★★"
    draw.text((80, H*0.23), stars, font=_get_font(30), fill=COLORS["gold"])
    
    review = "Best quality raincoat I've used. \nTotally waterproof even in heavy rain!"
    draw.text((80, H*0.28), review, font=_get_font(25), fill=COLORS["white"])

# ── ROUTER ───────────────────────────────────────────────

def apply_template(image_path, template_name, brief):
    """Main router — handles both local files and remote URLs""" 
    import tempfile 
    import requests

    # 1. Handle URL images
    if image_path and image_path.startswith("http"): 
        try: 
            headers = {"User-Agent": "Mozilla/5.0"} 
            resp    = requests.get(image_path, timeout=15, headers=headers) 
            if resp.status_code == 200: 
                ext  = ".jpg" if "jpg" in image_path else ( 
                       ".png" if "png" in image_path else ".webp") 
                os.makedirs(str(config.GENERATED_DIR), exist_ok=True)
                tmp  = tempfile.NamedTemporaryFile( 
                    delete=False, suffix=ext, 
                    dir=str(config.GENERATED_DIR)) 
                tmp.write(resp.content) 
                tmp.close() 
                image_path = tmp.name 
                print(f"Downloaded URL to temp file: {image_path}") 
            else:
                return _create_no_image_fallback(brief, template_name) 
        except Exception as e: 
            print(f"URL download error: {e}") 
            return _create_no_image_fallback(brief, template_name) 

    if not image_path or not os.path.exists(image_path):
        return _create_no_image_fallback(brief, template_name)

    try:
        # Load and prepare product image (transparency is key)
        product = Image.open(image_path).convert("RGBA")
        
        # Crop empty edges
        bbox = product.getbbox()
        if bbox: product = product.crop(bbox)

        # Create base canvas (1:1 Square)
        canvas = Image.new("RGB", SIZES["1x1"], (0, 0, 0))

        # Apply specific template
        templates = {
            "dark_cinematic":    template_dark_cinematic,
            "premium_minimal":   template_premium_minimal,
            "urgency_offer":     template_urgency_offer,
            "feature_breakdown": template_feature_breakdown,
            "lifestyle_emotion": template_lifestyle_emotion,
            "social_proof":      template_social_proof
        }
        
        func = templates.get(template_name, template_dark_cinematic)
        func(canvas, product, brief)

        # Save result
        filename = f"post_{int(time.time())}.jpg"
        save_path = config.GENERATED_DIR / filename
        canvas.save(str(save_path), quality=95)
        
        return str(save_path)

    except Exception as e:
        print(f"Template Error: {e}")
        import traceback
        traceback.print_exc()
        return _create_no_image_fallback(brief, template_name)

def _create_no_image_fallback(brief, template_name):
    """Creates a professional text-only post if image fails"""
    W, H = SIZES["1x1"]
    canvas = Image.new("RGB", (W, H), COLORS["black"])
    draw = ImageDraw.Draw(canvas)
    
    # Teal border
    draw.rectangle([20, 20, W-20, H-20], outline=COLORS["teal"], width=5)
    
    # Text
    name = brief.get("product_name", "RELAX FASHIONWEAR")
    tw = draw.textlength(name, font=_get_font(60, True))
    draw.text(((W-tw)//2, H*0.4), name, font=_get_font(60, True), fill=COLORS["white"])
    
    cat = brief.get("category", "PREMIUM RAINWEAR")
    tw2 = draw.textlength(cat, font=_get_font(30))
    draw.text(((W-tw2)//2, H*0.5), cat, font=_get_font(30), fill=COLORS["teal"])
    
    filename = f"fallback_{int(time.time())}.jpg"
    save_path = config.GENERATED_DIR / filename
    canvas.save(str(save_path), quality=90)
    return str(save_path)

def generate_all_ratios(image_path):
    """Generate all Instagram aspect ratios from base image"""
    if not image_path or not os.path.exists(image_path):
        return {}
    ratios = {}
    try:
        base = Image.open(image_path).convert("RGB")
        for ratio_name, (W, H) in SIZES.items():
            bw, bh = base.size
            scale  = max(W/bw, H/bh)
            nw, nh = int(bw*scale), int(bh*scale)
            scaled = base.resize((nw, nh), Image.LANCZOS)
            
            canvas = Image.new("RGB", (W, H), (0,0,0))
            x      = (W - nw) // 2
            y      = (H - nh) // 2
            canvas.paste(scaled, (x, y))
            out = config.GENERATED_DIR / f"ratio_{ratio_name}_{int(time.time())}.jpg"
            canvas.save(str(out), quality=95)
            ratios[ratio_name] = str(out)
    except Exception as e:
        print(f"[RATIOS] Error: {e}")
    return ratios