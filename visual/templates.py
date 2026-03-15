import os
import time
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import cv2
import numpy as np
import config

def apply_template(image_path, template_name, brief):
    """
    Routes to the correct template function based on template_name.
    """
    if not image_path or not os.path.exists(image_path):
        return image_path
        
    try:
        if template_name == 'dark_cinematic':
            return dark_cinematic(image_path, brief.get('product_name', ''), brief.get('price', ''))
        elif template_name == 'premium_minimal':
            return premium_minimal(image_path, brief.get('features', []), brief.get('price', ''))
        elif template_name == 'urgency_offer':
            return urgency_offer(image_path, brief.get('price', ''), config.BRAND['offer'])
        elif template_name == 'feature_breakdown':
            return feature_breakdown(image_path, brief.get('features', []))
        elif template_name == 'lifestyle_emotion':
            return lifestyle_emotion(image_path, brief.get('creative_angle', ''))
        elif template_name == 'social_proof':
            return social_proof(image_path, "Amazing quality!", 5)
        else:
            return image_path
    except Exception as e:
        print(f"Template Error: {str(e)}")
        return image_path

def dark_cinematic(product_path, name, price):
    with Image.open(product_path).convert("RGBA") as product:
        # Create dark background
        bg = Image.new("RGBA", (1080, 1080), (10, 10, 10, 255))
        
        # Center product
        product.thumbnail((800, 800))
        pos = ((bg.width - product.width) // 2, (bg.height - product.height) // 2)
        bg.paste(product, pos, product)
        
        draw = ImageDraw.Draw(bg)
        try:
            font_bebas = ImageFont.truetype(str(config.ASSETS_DIR / "fonts" / "BebasNeue-Regular.ttf"), 120)
            font_mont = ImageFont.truetype(str(config.ASSETS_DIR / "fonts" / "Montserrat-Bold.ttf"), 40)
        except:
            font_bebas = font_mont = ImageFont.load_default()
            
        # Text
        draw.text((bg.width//2, 100), name.upper(), font=font_bebas, fill=(255, 255, 255), anchor="mt")
        if price:
            draw.text((bg.width - 100, bg.height - 100), f"Rs.{price}", font=font_mont, fill=(0, 128, 128), anchor="rb")
            
        timestamp = int(time.time())
        output_path = config.GENERATED_DIR / f"template_dark_{timestamp}.png"
        bg.convert("RGB").save(output_path)
        return str(output_path)

def premium_minimal(product_path, features, price):
    with Image.open(product_path).convert("RGBA") as product:
        bg = Image.new("RGBA", (1080, 1080), (255, 255, 255, 255))
        
        # Teal accent bar
        draw = ImageDraw.Draw(bg)
        draw.rectangle([0, 0, 40, 1080], fill=(0, 128, 128))
        
        # Product on right
        product.thumbnail((700, 700))
        bg.paste(product, (400, 200), product)
        
        try:
            font = ImageFont.truetype(str(config.ASSETS_DIR / "fonts" / "Montserrat-Bold.ttf"), 30)
        except:
            font = ImageFont.load_default()
            
        # Features on left
        for i, feat in enumerate(features[:4]):
            draw.ellipse([80, 300 + i*80, 100, 320 + i*80], fill=(0, 128, 128))
            draw.text((120, 300 + i*80), feat, font=font, fill=(50, 50, 50))
            
        timestamp = int(time.time())
        output_path = config.GENERATED_DIR / f"template_minimal_{timestamp}.png"
        bg.convert("RGB").save(output_path)
        return str(output_path)

def urgency_offer(product_path, price, offer):
    bg = Image.new("RGB", (1080, 1080), (0, 128, 128)) # Simple solid for now
    draw = ImageDraw.Draw(bg)
    try:
        font_bebas = ImageFont.truetype(str(config.ASSETS_DIR / "fonts" / "BebasNeue-Regular.ttf"), 150)
    except:
        font_bebas = ImageFont.load_default()
        
    draw.text((540, 400), offer.upper(), font=font_bebas, fill=(255, 255, 255), anchor="mm")
    draw.rectangle([0, 900, 1080, 1080], fill=(200, 0, 0)) # Red strip
    draw.text((540, 990), "LIMITED TIME ONLY", font=ImageFont.load_default(), fill=(255, 255, 255), anchor="mm")
    
    timestamp = int(time.time())
    output_path = config.GENERATED_DIR / f"template_offer_{timestamp}.png"
    bg.save(output_path)
    return str(output_path)

def feature_breakdown(product_path, features):
    return dark_cinematic(product_path, "Features", "") # Placeholder

def lifestyle_emotion(product_path, hook_text):
    with Image.open(product_path).convert("RGBA") as product:
        bg = Image.new("RGBA", (1080, 1080), (20, 20, 20, 255))
        product.thumbnail((900, 900))
        bg.paste(product, (90, 90), product)
        bg = bg.filter(ImageFilter.GaussianBlur(5)) # Blur background a bit
        
        # Overlay original product sharp
        with Image.open(product_path).convert("RGBA") as sharp:
            sharp.thumbnail((800, 800))
            pos = ((bg.width - sharp.width) // 2, (bg.height - sharp.height) // 2)
            bg.paste(sharp, pos, sharp)
            
        draw = ImageDraw.Draw(bg)
        draw.text((540, 100), hook_text, font=ImageFont.load_default(), fill=(255, 255, 255), anchor="mt")
        
        timestamp = int(time.time())
        output_path = config.GENERATED_DIR / f"template_lifestyle_{timestamp}.png"
        bg.convert("RGB").save(output_path)
        return str(output_path)

def social_proof(product_path, review, rating):
    return dark_cinematic(product_path, "Happy Customer", "") # Placeholder

def generate_all_ratios(image_path):
    """
    Generates 5 standard social media aspect ratios.
    """
    ratios = {
        "1_1": (1080, 1080),
        "4_5": (1080, 1350),
        "9_16": (1080, 1920),
        "16_9": (1920, 1080),
        "1_91_1": (1200, 628)
    }
    
    results = {}
    try:
        with Image.open(image_path) as img:
            base_name = os.path.basename(image_path).split('.')[0]
            for name, size in ratios.items():
                # Create a canvas of target size with background color
                canvas = Image.new("RGB", size, (10, 10, 10))
                
                # Resize original to fit canvas while maintaining aspect ratio
                temp_img = img.copy()
                temp_img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Paste in center
                pos = ((size[0] - temp_img.width) // 2, (size[1] - temp_img.height) // 2)
                canvas.paste(temp_img, pos)
                
                out_path = config.GENERATED_DIR / f"{base_name}_{name}.jpg"
                canvas.save(out_path, quality=90)
                results[name] = str(out_path)
                
        return results
    except Exception as e:
        print(f"Ratio Generation Error: {str(e)}")
        return {"original": image_path}
