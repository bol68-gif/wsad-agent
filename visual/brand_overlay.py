import os
import time
from PIL import Image, ImageDraw, ImageFont
import config

def apply_overlay(image_path, brief):
    """
    Applies brand overlays: logo, website, price, and watermark.
    """
    if not image_path or not os.path.exists(image_path):
        return image_path
        
    try:
        with Image.open(image_path).convert("RGBA") as img:
            # 1. Add Watermark
            img = add_watermark(img, "RELAX FASHIONWEAR")
            
            # 2. Add Logo
            logo_path = config.ASSETS_DIR / "logo" / "rf_logo.png"
            if logo_path.exists():
                img = add_logo(img, str(logo_path))
            
            # 3. Add Website URL
            img = add_text_overlay(img, config.BRAND["website"], (40, img.height - 60), size=24)
            
            # 4. Add Price if present
            if 'price' in brief:
                price_text = f"Rs.{brief['price']}"
                img = add_text_overlay(img, price_text, (img.width - 200, 60), size=40, color=(255, 255, 255))
            
            # Save final
            timestamp = int(time.time())
            output_path = config.GENERATED_DIR / f"overlaid_{timestamp}.png"
            img.convert("RGB").save(output_path)
            
        return str(output_path)
    except Exception as e:
        print(f"Overlay Warning: {str(e)}")
        return image_path

def add_logo(image, logo_path, height=80):
    try:
        with Image.open(logo_path).convert("RGBA") as logo:
            # Resize logo maintaining aspect ratio
            aspect = logo.width / logo.height
            logo = logo.resize((int(height * aspect), height), Image.Resampling.LANCZOS)
            
            # Position: bottom-right
            pos = (image.width - logo.width - 40, image.height - logo.height - 40)
            
            # Apply 70% opacity to logo
            logo_data = logo.getdata()
            new_logo_data = []
            for item in logo_data:
                new_logo_data.append((item[0], item[1], item[2], int(item[3] * 0.7)))
            logo.putdata(new_logo_data)
            
            image.paste(logo, pos, logo)
        return image
    except:
        return image

def add_text_overlay(image, text, position, size=24, color=(255, 255, 255)):
    draw = ImageDraw.Draw(image)
    try:
        # Try to load custom font
        font_path = config.ASSETS_DIR / "fonts" / "Montserrat-Bold.ttf"
        font = ImageFont.truetype(str(font_path), size)
    except:
        font = ImageFont.load_default()
        
    draw.text(position, text, font=font, fill=color)
    return image

def add_watermark(image, text):
    watermark = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(watermark)
    try:
        font_path = config.ASSETS_DIR / "fonts" / "BebasNeue-Regular.ttf"
        font = ImageFont.truetype(str(font_path), 80)
    except:
        font = ImageFont.load_default()
        
    # Position in center
    draw.text((image.width//4, image.height//2), text, font=font, fill=(255, 255, 255, 25)) # 10% opacity approx
    return Image.alpha_composite(image, watermark)
