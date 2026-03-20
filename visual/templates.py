import os
import time
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import cv2
import numpy as np
import config

# ── CANVAS SIZES ─────────────────────────────────────────
SIZES = {
    "1x1":    (1080, 1080),
    "4x5":    (1080, 1350),
    "9x16":   (1080, 1920),
    "16x9":   (1920, 1080),
    "191x1":  (1200, 628),
}

def _get_font(name, size):
    paths = [
        config.ASSETS_DIR / "fonts" / f"{name}.ttf",
        config.ASSETS_DIR / "fonts" / f"{name}-Regular.ttf",
        config.ASSETS_DIR / "fonts" / f"{name}-Bold.ttf",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(str(p), size)
        except:
            continue
    return ImageFont.load_default()

def _save(img, prefix):
    os.makedirs(config.GENERATED_DIR, exist_ok=True)
    path = config.GENERATED_DIR / f"{prefix}_{int(time.time())}.jpg"
    img.convert("RGB").save(str(path), quality=95)
    return str(path)

def _place_product(bg, product_path, scale=0.75, position="center"):
    try:
        prod = Image.open(product_path).convert("RGBA")
        w, h = bg.size
        max_w = int(w * scale)
        max_h = int(h * scale)
        prod.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
        pw, ph = prod.size
        if position == "center":
            x = (w - pw) // 2
            y = (h - ph) // 2
        elif position == "right":
            x = w - pw - 40
            y = (h - ph) // 2
        elif position == "bottom_center":
            x = (w - pw) // 2
            y = h - ph - 60
        else:
            x = (w - pw) // 2
            y = (h - ph) // 2
        bg.paste(prod, (x, y), prod)
        return bg
    except Exception as e:
        print(f"Place product error: {e}")
        return bg

def _add_teal_rim_light(bg, product_path):
    try:
        arr  = np.array(bg.convert("RGB"))
        prod = Image.open(product_path).convert("RGBA")
        w, h = bg.size
        prod.thumbnail((int(w*0.75), int(h*0.75)), Image.Resampling.LANCZOS)
        pw, ph = prod.size
        cx = (w - pw) // 2
        cy = (h - ph) // 2
        alpha = np.array(prod)[:,:,3]
        glow  = np.zeros((h, w), dtype=np.float32)
        glow[cy:cy+ph, cx:cx+pw] = alpha / 255.0
        glow_blur = cv2.GaussianBlur(glow, (61, 61), 0) * 120
        teal = np.zeros_like(arr, dtype=np.float32)
        teal[:,:,0] = 0
        teal[:,:,1] = 128
        teal[:,:,2] = 128
        for c in range(3):
            arr[:,:,c] = np.clip(
                arr[:,:,c].astype(np.float32) + teal[:,:,c] * glow_blur / 255,
                0, 255
            ).astype(np.uint8)
        return Image.fromarray(arr)
    except Exception as e:
        return bg

def _draw_gradient_rect(draw, x1, y1, x2, y2, color1, color2, vertical=True):
    steps = y2 - y1 if vertical else x2 - x1
    for i in range(steps):
        t  = i / max(steps, 1)
        r  = int(color1[0] + (color2[0] - color1[0]) * t)
        g  = int(color1[1] + (color2[1] - color1[1]) * t)
        b  = int(color1[2] + (color2[2] - color1[2]) * t)
        if vertical:
            draw.line([(x1, y1+i), (x2, y1+i)], fill=(r,g,b))
        else:
            draw.line([(x1+i, y1), (x1+i, y2)], fill=(r,g,b))

# ────────────────────────────────────────────────────────
# TEMPLATE 1 — DARK CINEMATIC
# Premium dark background, teal rim light, rain texture
# Used for: Bikers, Monday factory, high-impact product shots
# ────────────────────────────────────────────────────────
def dark_cinematic(product_path, name, price, tagline=""):
    W, H = 1080, 1080
    # Dark gradient background
    bg   = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    draw = ImageDraw.Draw(bg)

    # Subtle dark gradient — bottom slightly lighter
    for y in range(H):
        t = y / H
        v = int(8 + t * 18)
        draw.line([(0,y),(W,y)], fill=(v, v+2, v+2, 255))

    # Teal accent lines — left and right edges
    draw.rectangle([0, 0, 6, H], fill=(0, 128, 128, 255))
    draw.rectangle([W-6, 0, W, H], fill=(0, 128, 128, 255))

    # Teal diagonal accent
    draw.polygon([(0,0),(120,0),(0,120)], fill=(0,95,95,200))

    # Place product with rim light
    bg = _add_teal_rim_light(bg, product_path)
    bg = _place_product(bg, product_path, scale=0.72, position="center")

    draw = ImageDraw.Draw(bg)

    # Brand name top
    f_brand = _get_font("Montserrat-Bold", 22)
    draw.text((W//2, 42), "RELAX FASHIONWEAR®",
              font=f_brand, fill=(0,128,128,255), anchor="mm")

    # Product name large
    f_name = _get_font("BebasNeue-Regular", 88)
    name_upper = name.upper()
    draw.text((W//2, H-200), name_upper,
              font=f_name, fill=(255,255,255,255), anchor="mm")

    # Price in teal
    if price:
        f_price = _get_font("Montserrat-Bold", 42)
        draw.text((W//2, H-130), f"Rs. {price}",
                  font=f_price, fill=(0,200,200,255), anchor="mm")

    # Tagline
    if tagline:
        f_tag = _get_font("Montserrat-Bold", 26)
        draw.text((W//2, H-80), tagline[:50],
                  font=f_tag, fill=(180,180,180,200), anchor="mm")

    # Website bottom
    f_web = _get_font("Montserrat-Bold", 22)
    draw.text((W//2, H-38), "relaxfashionwear.in",
              font=f_web, fill=(0,128,128,200), anchor="mm")

    # Offer strip
    draw.rectangle([0, H-22, W, H], fill=(0,95,95,255))
    f_offer = _get_font("Montserrat-Bold", 14)
    draw.text((W//2, H-11), "FLAT Rs89 OFF ON ALL PREPAID ORDERS",
              font=f_offer, fill=(255,255,255,255), anchor="mm")

    return _save(bg, "dark_cinematic")


# ────────────────────────────────────────────────────────
# TEMPLATE 2 — PREMIUM MINIMAL
# White/light background, clean typography, premium feel
# Used for: Women, professionals, premium positioning
# ────────────────────────────────────────────────────────
def premium_minimal(product_path, features, price):
    W, H = 1080, 1080
    bg   = Image.new("RGBA", (W, H), (252, 252, 252, 255))
    draw = ImageDraw.Draw(bg)

    # Teal accent bar left
    draw.rectangle([0, 0, 12, H], fill=(0, 128, 128, 255))

    # Light teal background panel top
    draw.rectangle([0, 0, W, 160], fill=(0, 95, 95, 255))

    # Brand name in header
    f_brand = _get_font("BebasNeue-Regular", 48)
    draw.text((W//2, 80), "RELAX FASHIONWEAR",
              font=f_brand, fill=(255,255,255,255), anchor="mm")

    # Product on right side
    bg = _place_product(bg, product_path, scale=0.55, position="right")
    draw = ImageDraw.Draw(bg)

    # Features on left
    f_feat = _get_font("Montserrat-Bold", 28)
    f_sub  = _get_font("Montserrat-Bold", 20)
    for i, feat in enumerate(features[:4]):
        y = 220 + i * 120
        # Teal dot
        draw.ellipse([40, y+6, 64, y+30], fill=(0,128,128,255))
        draw.text((80, y+4), feat[:35],
                  font=f_feat, fill=(20,20,20,255))

    # Price box
    draw.rectangle([40, 700, 380, 780], fill=(0,128,128,255), outline=(0,95,95), width=2)
    f_price = _get_font("BebasNeue-Regular", 56)
    draw.text((210, 740), f"Rs. {price}",
              font=f_price, fill=(255,255,255,255), anchor="mm")

    # Offer text
    f_offer = _get_font("Montserrat-Bold", 22)
    draw.text((210, 810), "Flat Rs89 OFF — Prepaid",
              font=f_offer, fill=(0,95,95,255), anchor="mm")

    # Website
    f_web = _get_font("Montserrat-Bold", 22)
    draw.text((W//2, H-40), "relaxfashionwear.in | +91 93213 84257",
              font=f_web, fill=(100,100,100,255), anchor="mm")

    # Bottom teal line
    draw.rectangle([0, H-8, W, H], fill=(0,128,128,255))

    return _save(bg, "premium_minimal")


# ────────────────────────────────────────────────────────
# TEMPLATE 3 — URGENCY OFFER
# High contrast, bold price, red urgency elements
# Used for: Friday offers, flash sales, ad campaigns
# ────────────────────────────────────────────────────────
def urgency_offer(product_path, price, offer_text):
    W, H = 1080, 1080
    bg   = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    draw = ImageDraw.Draw(bg)

    # Teal to dark gradient
    _draw_gradient_rect(draw, 0, 0, W, H//2,
                        (0, 95, 95), (0, 40, 40))
    _draw_gradient_rect(draw, 0, H//2, W, H,
                        (0, 40, 40), (5, 5, 15))

    # Diagonal teal accent shape
    draw.polygon([(0,0),(W,0),(W,300),(0,180)],
                 fill=(0,110,110,200))

    # Brand name
    f_brand = _get_font("BebasNeue-Regular", 52)
    draw.text((W//2, 60), "RELAX FASHIONWEAR",
              font=f_brand, fill=(255,255,255,230), anchor="mm")

    # Place product
    bg = _place_product(bg, product_path, scale=0.58, position="center")
    draw = ImageDraw.Draw(bg)

    # OFFER badge
    draw.ellipse([W//2-140, 280, W//2+140, 400],
                 fill=(220, 30, 30, 255))
    f_off = _get_font("BebasNeue-Regular", 56)
    draw.text((W//2, 340), "Rs89 OFF",
              font=f_off, fill=(255,255,255,255), anchor="mm")
    f_offsub = _get_font("Montserrat-Bold", 18)
    draw.text((W//2, 394), "ON ALL PREPAID ORDERS",
              font=f_offsub, fill=(255,200,200,255), anchor="mm")

    # Large price
    f_price = _get_font("BebasNeue-Regular", 130)
    draw.text((W//2, H-260), f"Rs.{price}",
              font=f_price, fill=(255,255,255,255), anchor="mm")

    # Urgency strip
    draw.rectangle([0, H-140, W, H-80], fill=(200, 20, 20, 255))
    f_urg = _get_font("BebasNeue-Regular", 44)
    draw.text((W//2, H-110), "LIMITED STOCK — ORDER NOW",
              font=f_urg, fill=(255,255,255,255), anchor="mm")

    # CTA
    draw.rectangle([0, H-80, W, H], fill=(0, 60, 60, 255))
    f_cta = _get_font("Montserrat-Bold", 26)
    draw.text((W//2, H-40), "relaxfashionwear.in  |  Prepaid = Rs89 OFF",
              font=f_cta, fill=(0,200,200,255), anchor="mm")

    return _save(bg, "urgency_offer")


# ────────────────────────────────────────────────────────
# TEMPLATE 4 — FEATURE BREAKDOWN
# Dark split layout, features list, technical credibility
# Used for: Wednesday education, retargeting ads
# ────────────────────────────────────────────────────────
def feature_breakdown(product_path, features):
    W, H = 1080, 1080
    bg   = Image.new("RGBA", (W, H), (10, 10, 12, 255))
    draw = ImageDraw.Draw(bg)

    # Left dark panel
    draw.rectangle([0, 0, W//2, H], fill=(14, 16, 20, 255))
    # Right slightly lighter
    draw.rectangle([W//2, 0, W, H], fill=(8, 8, 10, 255))

    # Teal divider line center
    draw.rectangle([W//2-2, 0, W//2+2, H], fill=(0,128,128,255))

    # Brand top
    f_brand = _get_font("BebasNeue-Regular", 38)
    draw.text((W//4, 50), "RELAX FASHIONWEAR",
              font=f_brand, fill=(0,128,128,255), anchor="mm")

    # "WHY RF?" heading
    f_why = _get_font("BebasNeue-Regular", 72)
    draw.text((W//4, 130), "WHY RF?",
              font=f_why, fill=(255,255,255,255), anchor="mm")

    # Features with teal checkmarks
    f_feat = _get_font("Montserrat-Bold", 28)
    f_sub  = _get_font("Montserrat-Bold", 19)
    feat_list = features[:5] if features else [
        "Heat Sealed Seams",
        "3000mm Waterproof",
        "Anti-Sweat Breathable",
        "Reflective Night Strips",
        "Factory Direct Price"
    ]
    for i, feat in enumerate(feat_list):
        y = 200 + i * 140
        # Teal checkmark circle
        draw.ellipse([30, y, 72, y+42], fill=(0,128,128,255))
        f_check = _get_font("Montserrat-Bold", 24)
        draw.text((51, y+21), "✓", font=f_check,
                  fill=(255,255,255,255), anchor="mm")
        draw.text((90, y+4), feat[:28],
                  font=f_feat, fill=(255,255,255,255))
        draw.text((90, y+38), "Industry leading quality",
                  font=f_sub, fill=(0,160,160,200))

    # Product on right
    bg = _place_product(bg, product_path, scale=0.52, position="right")
    draw = ImageDraw.Draw(bg)

    # Bottom CTA
    draw.rectangle([0, H-80, W, H], fill=(0,80,80,255))
    f_cta = _get_font("Montserrat-Bold", 26)
    draw.text((W//2, H-40), "relaxfashionwear.in  ·  Flat Rs89 OFF Prepaid",
              font=f_cta, fill=(255,255,255,255), anchor="mm")

    return _save(bg, "feature_breakdown")


# ────────────────────────────────────────────────────────
# TEMPLATE 5 — LIFESTYLE EMOTION
# Blurred background, emotional, cinematic feel
# Used for: Saturday lifestyle reels, aspirational content
# ────────────────────────────────────────────────────────
def lifestyle_emotion(product_path, hook_text):
    W, H = 1080, 1080
    bg   = Image.new("RGBA", (W, H), (5, 8, 12, 255))
    draw = ImageDraw.Draw(bg)

    # Dark atmospheric gradient
    _draw_gradient_rect(draw, 0, 0, W, H,
                        (5, 15, 20), (0, 5, 8))

    # Blurred product as background mood (large, blurred)
    try:
        mood = Image.open(product_path).convert("RGBA")
        mood = mood.resize((W, H), Image.Resampling.LANCZOS)
        mood = mood.filter(ImageFilter.GaussianBlur(radius=30))
        # Very dark overlay
        dark = Image.new("RGBA", (W, H), (0, 0, 0, 185))
        bg.paste(mood, (0, 0), mood)
        bg.paste(dark, (0, 0), dark)
    except:
        pass

    # Teal atmospheric glow top
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd   = ImageDraw.Draw(glow)
    for r in range(300, 0, -1):
        alpha = int((300 - r) / 300 * 40)
        gd.ellipse([W//2-r, -r, W//2+r, r], fill=(0,128,128,alpha))
    bg.alpha_composite(glow)

    # Place product sharp in foreground
    bg = _place_product(bg, product_path, scale=0.65, position="center")
    draw = ImageDraw.Draw(bg)

    # Hook text top — emotional
    f_hook = _get_font("BebasNeue-Regular", 72)
    # Text shadow
    if hook_text:
        lines = [hook_text[i:i+20] for i in range(0, len(hook_text), 20)]
        for li, line in enumerate(lines[:3]):
            y = 100 + li * 80
            draw.text((W//2+2, y+2), line,
                      font=f_hook, fill=(0,0,0,180), anchor="mt")
            draw.text((W//2, y), line,
                      font=f_hook, fill=(255,255,255,240), anchor="mt")

    # Brand subtle
    f_brand = _get_font("Montserrat-Bold", 22)
    draw.text((W//2, H-60), "RELAX FASHIONWEAR  ·  relaxfashionwear.in",
              font=f_brand, fill=(0,200,200,200), anchor="mm")

    # Bottom teal line
    draw.rectangle([0, H-6, W, H], fill=(0,128,128,255))

    return _save(bg, "lifestyle_emotion")


# ────────────────────────────────────────────────────────
# TEMPLATE 6 — SOCIAL PROOF
# Review-focused, trust-building, community feel
# Used for: Sunday social proof, testimonials
# ────────────────────────────────────────────────────────
def social_proof(product_path, review_text, rating=5):
    W, H = 1080, 1080
    bg   = Image.new("RGBA", (W, H), (8, 10, 14, 255))
    draw = ImageDraw.Draw(bg)

    # Dark gradient
    _draw_gradient_rect(draw, 0, 0, W, H,
                        (10, 14, 20), (4, 6, 10))

    # Teal header panel
    draw.rectangle([0, 0, W, 180], fill=(0, 80, 80, 255))

    # Brand
    f_brand = _get_font("BebasNeue-Regular", 52)
    draw.text((W//2, 60), "RELAX FASHIONWEAR",
              font=f_brand, fill=(255,255,255,255), anchor="mm")
    f_sub = _get_font("Montserrat-Bold", 24)
    draw.text((W//2, 128), "Real Customers. Real Reviews.",
              font=f_sub, fill=(0,200,200,200), anchor="mm")

    # Star rating
    stars = "★" * rating + "☆" * (5 - rating)
    f_star = _get_font("BebasNeue-Regular", 72)
    draw.text((W//2, 260), stars,
              font=f_star, fill=(255, 200, 0, 255), anchor="mm")

    # Review quote card
    draw.rounded_rectangle([60, 300, W-60, 600],
                            radius=20, fill=(18, 22, 30, 255),
                            outline=(0,100,100,255), width=2)

    # Quote marks
    f_quote = _get_font("BebasNeue-Regular", 120)
    draw.text((100, 310), "\"",
              font=f_quote, fill=(0,128,128,100))

    f_review = _get_font("Montserrat-Bold", 30)
    # Word wrap review text
    words = review_text.split()
    lines_r = []
    current = ""
    for word in words:
        if len(current + word) < 32:
            current += word + " "
        else:
            lines_r.append(current.strip())
            current = word + " "
    if current:
        lines_r.append(current.strip())

    for li, line in enumerate(lines_r[:5]):
        draw.text((W//2, 380 + li*52), line,
                  font=f_review, fill=(220,220,220,255), anchor="mm")

    # Customer info
    f_cust = _get_font("Montserrat-Bold", 22)
    draw.text((W//2, 570), "— Verified Customer, Mumbai",
              font=f_cust, fill=(0,160,160,200), anchor="mm")

    # Product
    bg = _place_product(bg, product_path, scale=0.42, position="right")
    draw = ImageDraw.Draw(bg)

    # Trust badges
    badges = ["12,100+ Customers", "Heat Sealed", "Factory Direct"]
    f_badge = _get_font("Montserrat-Bold", 22)
    for bi, badge in enumerate(badges):
        x = 120 + bi * 300
        draw.rounded_rectangle([x-90, 640, x+90, 680],
                                radius=10, fill=(0,80,80,255))
        draw.text((x, 660), badge,
                  font=f_badge, fill=(255,255,255,255), anchor="mm")

    # CTA
    draw.rectangle([0, H-80, W, H], fill=(0,80,80,255))
    f_cta = _get_font("Montserrat-Bold", 26)
    draw.text((W//2, H-40), "relaxfashionwear.in  ·  Flat Rs89 OFF Prepaid",
              font=f_cta, fill=(255,255,255,255), anchor="mm")

    return _save(bg, "social_proof")


# ── ROUTER ───────────────────────────────────────────────
def apply_template(image_path, template_name, brief):
    if not image_path or not os.path.exists(image_path):
        return _create_no_image_fallback(brief, template_name)

    name     = brief.get("product_name", "RF Product")
    price    = brief.get("price", "")
    features = brief.get("features", [
        "Heat Sealed Seams",
        "3000mm Waterproof",
        "Anti-Sweat Design",
        "Reflective Strips",
        "Factory Direct"
    ])
    hook     = brief.get("hook_idea", "")
    offer    = config.BRAND.get("offer", "Flat Rs89 OFF")

    try:
        if template_name == "dark_cinematic":
            return dark_cinematic(image_path, name, price, hook[:50] if hook else "")
        elif template_name == "premium_minimal":
            return premium_minimal(image_path, features, price)
        elif template_name == "urgency_offer":
            return urgency_offer(image_path, price, offer)
        elif template_name == "feature_breakdown":
            return feature_breakdown(image_path, features)
        elif template_name == "lifestyle_emotion":
            return lifestyle_emotion(image_path, hook)
        elif template_name == "social_proof":
            return social_proof(image_path,
                "Baarish mein bhi ek baar bhi nahi bheega! Best purchase this monsoon.", 5)
        else:
            return dark_cinematic(image_path, name, price, "")
    except Exception as e:
        print(f"Template error {template_name}: {e}")
        return _create_no_image_fallback(brief, template_name)


def _create_no_image_fallback(brief, template_name):
    W, H = 1080, 1080
    bg   = Image.new("RGB", (W, H), (0, 80, 80))
    draw = ImageDraw.Draw(bg)

    _draw_gradient_rect(draw, 0, 0, W, H,
                        (0, 95, 95), (0, 40, 50))

    f_big   = _get_font("BebasNeue-Regular", 100)
    f_med   = _get_font("BebasNeue-Regular", 60)
    f_small = _get_font("Montserrat-Bold", 30)

    draw.text((W//2, 200),  "RELAX FASHIONWEAR",
              font=f_big, fill=(255,255,255), anchor="mm")
    draw.text((W//2, 400),
              brief.get("product_name","RF PRODUCT").upper(),
              font=f_med, fill=(255,255,0), anchor="mm")
    if brief.get("price"):
        draw.text((W//2, 520), f"Rs. {brief['price']}",
                  font=f_med, fill=(255,255,255), anchor="mm")
    draw.rectangle([0, 650, W, 720], fill=(0,50,50))
    draw.text((W//2, 685), "Flat Rs89 OFF on Prepaid Orders",
              font=f_small, fill=(255,255,255), anchor="mm")
    draw.text((W//2, 820), "relaxfashionwear.in",
              font=f_small, fill=(200,255,255), anchor="mm")
    draw.text((W//2, 900), "+91 93213 84257",
              font=f_small, fill=(200,255,255), anchor="mm")

    path = config.GENERATED_DIR / f"fallback_{int(time.time())}.jpg"
    os.makedirs(config.GENERATED_DIR, exist_ok=True)
    bg.save(str(path), quality=95)
    return str(path)


def generate_all_ratios(image_path):
    if not image_path or not os.path.exists(image_path):
        return {}
    ratios = {}
    try:
        base = Image.open(image_path).convert("RGB")
        for ratio_name, (W, H) in SIZES.items():
            bw, bh = base.size
            scale  = max(W/bw, H/bh)
            nw     = int(bw * scale)
            nh     = int(bh * scale)
            scaled = base.resize((nw, nh), Image.Resampling.LANCZOS)
            canvas = Image.new("RGB", (W, H), (0,0,0))
            x      = (W - nw) // 2
            y      = (H - nh) // 2
            canvas.paste(scaled, (x, y))
            out = config.GENERATED_DIR / f"ratio_{ratio_name}_{int(time.time())}.jpg"
            canvas.save(str(out), quality=95)
            ratios[ratio_name] = str(out)
    except Exception as e:
        print(f"Ratio generation error: {e}")
    return ratios