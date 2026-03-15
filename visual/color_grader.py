import cv2
import numpy as np
import os
import time
import config

def apply_teal_grade(image_path):
    """
    Applies cinematic teal color grading using OpenCV.
    """
    if not image_path or not os.path.exists(image_path):
        return image_path
        
    try:
        img = cv2.imread(image_path)
        if img is None: return image_path
        
        # 1. Boost Contrast
        img = boost_contrast(img, 1.2)
        
        # 2. Color Wash (Teal Shadows)
        img = apply_color_wash(img, strength=0.2)
        
        # 3. Add Rim Light (Edge Glow)
        img = add_rim_light(img)
        
        timestamp = int(time.time())
        output_path = config.GENERATED_DIR / f"graded_{timestamp}.png"
        cv2.imwrite(str(output_path), img)
        
        return str(output_path)
    except Exception as e:
        print(f"Color Grading Warning: {str(e)}")
        return image_path

def add_rim_light(image, color=(128, 128, 0)): # BGR Teal
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        
        # Dilate edges to create glow area
        kernel = np.ones((5,5), np.uint8)
        glow_mask = cv2.dilate(edges, kernel, iterations=1)
        glow_mask = cv2.GaussianBlur(glow_mask, (15, 15), 0)
        
        # Create teal glow
        glow = np.zeros_like(image)
        glow[:] = color
        
        # Blend glow with original based on mask
        mask_3d = cv2.merge([glow_mask, glow_mask, glow_mask]) / 255.0
        result = image * (1 - mask_3d * 0.5) + glow * (mask_3d * 0.5)
        return result.astype(np.uint8)
    except:
        return image

def apply_color_wash(image, strength=0.2):
    try:
        teal_overlay = np.full(image.shape, (128, 128, 0), dtype=np.uint8) # BGR
        return cv2.addWeighted(image, 1.0 - strength, teal_overlay, strength, 0)
    except:
        return image

def boost_contrast(image, factor=1.2):
    try:
        return cv2.convertScaleAbs(image, alpha=factor, beta=0)
    except:
        return image
