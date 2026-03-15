from ai_team.base_agent import BaseAgent 
import json 
 
class Strategist(BaseAgent): 
    def __init__(self): 
        super().__init__( 
            name        = "Strategist", 
            role        = "Senior Brand Strategist", 
            personality = """ 
You are RF Senior Brand Strategist. 
CMO mindset. Data obsessed. 
Grew 6 Indian D2C brands to 1 crore revenue. 
You never brief the same approach twice in 14 days. 
            """ 
        ) 
 
    def morning_brief(self): 
        context = self.get_performance_context() 
        task = """ 
Create today's content brief for Relax Fashionwear. 
 
Return ONLY this JSON — no other text: 
 { 
     "product_name": "product name here", 
     "category": "Men/Women/Kids/Biker/Unisex/Safety", 
     "price": 0, 
     "template": "dark_cinematic/premium_minimal/urgency_offer/feature_breakdown/lifestyle_emotion/social_proof", 
     "primary_persona": "who is the target buyer", 
     "psychological_trigger": "main trigger to use", 
     "creative_angle": "the unique angle for this post", 
     "caption_tone": "tone description", 
     "post_type": "static/reel/carousel", 
     "ad_potential": true, 
     "reasoning": "why this product and angle today" 
 } 
         """ 
        result = self.call_gemini(task, context) 
        try: 
            clean = result.strip() 
            if "```" in clean: 
                clean = clean.split("```")[1] 
                if clean.startswith("json"): 
                    clean = clean[4:] 
            return json.loads(clean) 
        except: 
            from data.product_catalog import get_product_for_day 
            from datetime import datetime 
            product = get_product_for_day(datetime.now().strftime("%A")) 
            return { 
                "product_name":         product["name"], 
                "category":             product["category"], 
                "price":                product["price"], 
                "template":             "dark_cinematic", 
                "primary_persona":      product["target_persona"], 
                "psychological_trigger":"Pain + Identity", 
                "creative_angle":       f"Why {product['name']} is essential for Indian monsoon", 
                "caption_tone":         "Bold and Urgent", 
                "post_type":            "static", 
                "ad_potential":         True, 
                "reasoning":            "Fallback brief" 
            } 
