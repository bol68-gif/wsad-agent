from ai_team.base_agent import BaseAgent 
import os 
 
class Designer(BaseAgent): 
    def __init__(self): 
        super().__init__( 
            name        = "Designer", 
            role        = "Senior Brand Designer", 
            personality = """ 
You are RF Senior Brand Designer. 
Teal aesthetic specialist. 
Every pixel either builds trust or destroys it. 
You never let a distorted product pass. 
            """ 
        ) 
 
    def create_post_assets(self, brief, caption): 
        self.log_and_broadcast( 
            f"Building visual assets for {brief.get('product_name')}...", 
            "WORKING" 
        ) 
        assets = { 
            "final_image": "", 
            "story_image": "", 
            "ratios":      {} 
        } 
        try: 
            product_image = self.get_product_image(brief.get("product_name", "")) 
            if product_image: 
                from visual.enhancer      import enhance_product 
                from visual.brand_overlay import apply_overlay 
                from visual.color_grader  import apply_teal_grade 
                from visual.rain_effects  import apply_rain 
                from visual.templates     import apply_template, generate_all_ratios 
 
                enhanced  = enhance_product(product_image) 
                overlaid  = apply_overlay(enhanced, brief) 
                templated = apply_template(overlaid, brief.get("template","dark_cinematic"), brief) 
                graded    = apply_teal_grade(templated) 
                final     = apply_rain(graded) 
                ratios    = generate_all_ratios(final) 
 
                assets["final_image"] = final 
                assets["ratios"]      = ratios 
                self.log_and_broadcast( 
                    f"Visual pipeline complete — {len(ratios)} ratios generated", 
                    "VISUAL READY" 
                ) 
            else: 
                self.log_and_broadcast( 
                    "No product image found — skipping visual pipeline", 
                    "WARNING" 
                ) 
        except Exception as e: 
            self.log_and_broadcast(f"Visual pipeline error: {str(e)[:100]}", "ERROR") 
 
        return assets 
 
    def get_product_image(self, product_name): 
        try: 
            products_dir = os.path.join("assets", "products") 
            if not os.path.exists(products_dir): 
                return None 
            for folder in os.listdir(products_dir): 
                if product_name.lower().replace(" ","") in folder.lower().replace(" ",""): 
                    folder_path = os.path.join(products_dir, folder) 
                    if os.path.isdir(folder_path): 
                         images = [f for f in os.listdir(folder_path) 
                                   if f.lower().endswith(('.jpg','.jpeg','.png','.webp'))] 
                         if images: 
                             return os.path.join(folder_path, images[0]) 
            return None 
        except: 
            return None 
 
    def select_template(self, brief): 
        category = brief.get("category", "").lower() 
        post_type = brief.get("post_type", "static") 
        if "biker" in category:    return "dark_cinematic" 
        if "women" in category:    return "premium_minimal" 
        if post_type == "offer":   return "urgency_offer" 
        if post_type == "carousel":return "feature_breakdown" 
        if post_type == "lifestyle":return "lifestyle_emotion" 
        return "dark_cinematic" 
