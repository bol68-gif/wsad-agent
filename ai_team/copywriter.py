from ai_team.base_agent import BaseAgent 
 
class Copywriter(BaseAgent): 
    def __init__(self): 
        super().__init__( 
            name        = "Copywriter", 
            role        = "Senior Hinglish Copywriter", 
            personality = """ 
You are RF Senior Copywriter. 
Hinglish specialist. Pain-point marketing expert. 
Written for boAt, Meesho, Nykaa. 
First line must cause physical scroll pause. 
Never write Buy Now. Always specific CTAs. 
60% Hindi 40% English always. 
            """ 
        ) 
 
    def write_caption(self, brief): 
        task = f""" 
Write a complete Instagram caption for this brief: 
 Product: {brief.get('product_name')} 
 Price: Rs{brief.get('price', '')} 
 Angle: {brief.get('creative_angle')} 
 Tone: {brief.get('caption_tone')} 
 Trigger: {brief.get('psychological_trigger')} 
 
 Caption must have: 
 - Hook line that stops Mumbai biker mid-scroll 
 - Pain amplification 
 - Product as solution 
 - 2-3 key features 
 - Urgency CTA with website relaxfashionwear.in 
 - WhatsApp +91 93213 84257 
 - Exactly 15 hashtags at end 
 
 Return ONLY the caption text. Nothing else. 
         """ 
        return self.call_gemini(task, brief) 
 
    def generate_hashtags(self, brief): 
        task = f""" 
Generate exactly 15 Instagram hashtags for: 
 Product: {brief.get('product_name')} 
 Category: {brief.get('category')} 
 Cities: Mumbai, Pune, Bangalore, Delhi 
 
 Mix of: broad reach, niche product, location, seasonal, brand 
 Return ONLY hashtags separated by spaces. Nothing else. 
         """ 
        return self.call_gemini(task) 
