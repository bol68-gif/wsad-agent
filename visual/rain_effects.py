import cv2
import numpy as np
import os
import time
import random
import config

def apply_rain(image_path, intensity='medium'):
    """
    Applies procedural rain effects to the image.
    """
    if not image_path or not os.path.exists(image_path):
        return image_path
        
    try:
        img = cv2.imread(image_path)
        if img is None: return image_path
        
        h, w = img.shape[:2]
        
        # Opacity based on intensity
        opacity_map = {'light': 0.2, 'medium': 0.4, 'heavy': 0.6, 'extreme': 0.8}
        opacity = opacity_map.get(intensity, 0.4)
        
        # Generate procedural rain layer
        rain_layer = generate_procedural_rain(w, h, intensity)
        
        # Blend rain with image
        img = blend_overlay(img, rain_layer, opacity)
        
        timestamp = int(time.time())
        output_path = config.GENERATED_DIR / f"rain_{timestamp}.png"
        cv2.imwrite(str(output_path), img)
        
        return str(output_path)
    except Exception as e:
        print(f"Rain Effect Warning: {str(e)}")
        return image_path

def generate_procedural_rain(width, height, intensity):
    # Create black canvas
    rain = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Line count based on intensity
    count_map = {'light': 500, 'medium': 1000, 'heavy': 2000, 'extreme': 4000}
    line_count = count_map.get(intensity, 1000)
    
    for _ in range(line_count):
        # Random starting point
        x = random.randint(0, width)
        y = random.randint(0, height)
        
        # Slanted lines
        length = random.randint(5, 15)
        angle = random.randint(70, 85) # Mostly vertical but slightly slanted
        
        end_x = int(x + length * np.cos(np.radians(angle)))
        end_y = int(y + length * np.sin(np.radians(angle)))
        
        # Draw white line with varying thickness/brightness
        thickness = random.randint(1, 2)
        brightness = random.randint(150, 255)
        cv2.line(rain, (x, y), (end_x, end_y), (brightness, brightness, brightness), thickness)
        
    # Apply slight blur to rain
    rain = cv2.GaussianBlur(rain, (3, 3), 0)
    return rain

def blend_overlay(base, overlay, opacity):
    return cv2.addWeighted(base, 1.0, overlay, opacity, 0)
