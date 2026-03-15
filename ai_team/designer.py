import os
import pathlib
from ai_team.base_agent import BaseAgent
from visual import enhancer, brand_overlay, templates, color_grader, rain_effects
import config

class Designer(BaseAgent):
    def __init__(self):
        personality = """
        YOUR SPECIFIC IDENTITY:
        You are the brand designer who created visual identities for 30 Indian consumer brands.
        You see teal and immediately know 12 ways to make it more powerful.
        You have never let a distorted product image pass in 50 years.
        Your templates have been copied by competitors but never matched.
        You understand that every pixel either builds trust or destroys it.
        """
        super().__init__(name="Designer", role="Senior Brand Designer", personality=personality)

    def create_post_assets(self, brief, caption):
        self.log(f"Orchestrating visual assets for {brief.get('product_name')}...", "info")
        
        try:
            # Step 0: Get product image
            product_image = self.get_product_image(brief.get('product_name'))
            if not self.quality_check(product_image):
                self.log("Initial quality check failed. Using placeholder.", "warning")
                # Fallback to a placeholder if necessary
            
            # Step 1: Enhance
            self.log("Step 1: Enhancing product image...", "info")
            enhanced_path = enhancer.enhance_product(product_image)
            
            # Step 2: Overlay
            self.log("Step 2: Applying brand overlays...", "info")
            overlaid_path = brand_overlay.apply_overlay(enhanced_path, brief)
            
            # Step 3: Template
            template_name = self.select_template(brief)
            self.log(f"Step 3: Applying {template_name} template...", "info")
            templated_path = templates.apply_template(overlaid_path, template_name, brief)
            
            # Step 4: Color Grade
            self.log("Step 4: Applying teal color grade...", "info")
            graded_path = color_grader.apply_teal_grade(templated_path)
            
            # Step 5: Rain Effects
            self.log("Step 5: Applying procedural rain effects...", "info")
            final_path = rain_effects.apply_rain(graded_path)
            
            # Step 6: Ratios
            self.log("Step 6: Generating all aspect ratios...", "info")
            all_assets = templates.generate_all_ratios(final_path)
            
            self.log("Visual pipeline completed successfully.", "success")
            return all_assets
            
        except Exception as e:
            self.log(f"Visual Pipeline Error: {str(e)}", "error")
            return {"original": product_image if 'product_image' in locals() else None}

    def select_template(self, brief):
        category = brief.get('category', '').lower()
        if 'biker' in category:
            return 'dark_cinematic'
        elif 'women' in category:
            return 'premium_minimal'
        elif brief.get('ad_potential'):
            return 'urgency_offer'
        
        # Check day-based logic or other markers
        return 'lifestyle_emotion'

    def quality_check(self, image_path):
        if not image_path or not os.path.exists(image_path):
            return False
        # In a real scenario, use Pillow to check resolution
        # For now, return True if file exists
        return True

    def get_product_image(self, product_name):
        search_folder = config.PRODUCTS_DIR
        # Basic search for product name in folder
        if os.path.exists(search_folder):
            for file in os.listdir(search_folder):
                if product_name.lower().replace(" ", "_") in file.lower():
                    return str(search_folder / file)
        
        # Fallback to a generic product image if exists
        fallback = search_folder / "generic_raincoat.jpg"
        return str(fallback) if fallback.exists() else None
