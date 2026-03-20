import os
import time
from PIL import Image
from rembg import remove
import config

def enhance_product(input_path): 
    """Handles both local files and URLs""" 
    import tempfile 
    import requests

    if not input_path: 
        return input_path 
 
    # Download if URL 
    if input_path.startswith("http"): 
        try: 
            headers = {"User-Agent": "Mozilla/5.0"} 
            resp    = requests.get(input_path, timeout=15, headers=headers) 
            if resp.status_code == 200: 
                ext = ".jpg" if "jpg" in input_path else ( 
                      ".png" if "png" in input_path else ".webp") 
                os.makedirs(str(config.GENERATED_DIR), exist_ok=True) 
                tmp = tempfile.NamedTemporaryFile( 
                    delete=False, suffix=ext, 
                    dir=str(config.GENERATED_DIR)) 
                tmp.write(resp.content) 
                tmp.close() 
                input_path = tmp.name 
            else: 
                return input_path 
        except: 
            return input_path 
 
    if not os.path.exists(input_path): 
        return input_path 
 
    try: 
        no_bg = remove_background(input_path) 
        final = upscale_image(no_bg, scale=2) 
        return final 
    except Exception as e: 
        print(f"Enhancement error: {e}") 
        return input_path 

def remove_background(input_path):
    """
    Uses rembg to remove background.
    """
    try:
        with open(input_path, 'rb') as i:
            input_data = i.read()
            output_data = remove(input_data)
            
        timestamp = int(time.time())
        output_path = config.GENERATED_DIR / f"enhanced_{timestamp}.png"
        
        with open(output_path, 'wb') as o:
            o.write(output_data)
            
        return str(output_path)
    except Exception as e:
        raise Exception(f"Rembg failure: {str(e)}")

def upscale_image(input_path, scale=2):
    """
    Uses Pillow LANCZOS for high-quality upscaling.
    """
    try:
        with Image.open(input_path) as img:
            width, height = img.size
            new_size = (width * scale, height * scale)
            upscaled_img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Update path slightly
            output_path = input_path.replace(".png", "_upscaled.png")
            upscaled_img.save(output_path)
            
        return output_path
    except Exception as e:
        raise Exception(f"Upscale failure: {str(e)}")
