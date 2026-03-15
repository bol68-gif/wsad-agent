import os
import time
from PIL import Image
from rembg import remove
import config

def enhance_product(input_path):
    """
    Orchestrates background removal and upscaling.
    """
    if not input_path or not os.path.exists(input_path):
        return input_path
        
    try:
        # Step 1: Remove Background
        no_bg_path = remove_background(input_path)
        
        # Step 2: Upscale
        final_path = upscale_image(no_bg_path)
        
        return final_path
    except Exception as e:
        print(f"Enhancement Warning: {str(e)}")
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
