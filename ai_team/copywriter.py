from ai_team.base_agent import BaseAgent
import json

class Copywriter(BaseAgent):
    def __init__(self):
        personality = """
        YOUR SPECIFIC IDENTITY:
        You are the copywriter whose hooks have stopped 50 million Indian thumbs mid-scroll.
        You wrote campaigns for boAt, Meesho, Nykaa, Mamaearth.
        You dream in Hinglish.
        You know the exact word that makes a Mumbai biker feel understood.
        You have never written a generic caption in 50 years.
        Every word you choose has a reason.
        Your CTAs have generated crores in revenue.
        
        8 psychology triggers in every caption:
        Pain, Identity, Authority, Scarcity, Social Proof, Value, Made in India, Urgency.
        """
        super().__init__(name="Copywriter", role="Senior Copywriter", personality=personality)

    def write_caption(self, brief):
        self.log(f"Writing caption for {brief['product_name']}...", "info")
        
        # Layer 1: Hook
        hooks = self.write_hook(brief)
        selected_hook = hooks.split('\n')[0] 
        
        # Layer 2: Full Caption
        full_caption = self.write_full_caption(selected_hook, brief)
        
        # Layer 3: Strategy Check
        is_valid = self.strategy_check(full_caption, brief)
        
        if "REJECTED" in is_valid:
            self.log("Strategy check failed. Regenerating...", "warning")
            full_caption = self.write_full_caption(selected_hook, brief)
            
        hashtags = self.generate_hashtags(brief)
        final_caption = f"{full_caption}\n\n{hashtags}"
        
        self.log("Final caption completed.", "success")
        return final_caption

    def write_hook(self, brief):
        prompt = f"""
        Generate 3 strong Hinglish hooks for: {brief['product_name']}.
        Creative Angle: {brief['creative_angle']}
        Tone: {brief['caption_tone']}
        Psychological Trigger: {brief['psychological_trigger']}
        
        Focus on the first line that stops a Mumbai delivery partner mid-scroll.
        Return 3 hooks, one per line.
        """
        return self.call_gemini(prompt)

    def write_full_caption(self, hook, brief):
        prompt = f"""
        Write a complete Instagram caption starting with this hook: "{hook}"
        
        BRIEF DETAILS:
        - Product: {brief['product_name']}
        - Creative Angle: {brief['creative_angle']}
        - Persona: {brief['primary_persona']}
        
        STRUCTURE:
        1. Hook (Already provided)
        2. Pain: Describe the monsoon struggle
        3. Solution: How RF {brief['product_name']} saves the day
        4. Features: Mention 2 key features naturally
        5. Social Proof: Hint at thousands of happy customers
        6. Urgency CTA: Specific call to action (Not 'Buy Now')
        7. Website: relaxfashionwear.in | WhatsApp: +91 93213 84257
        
        RULES:
        - 60% Hindi (written in English script), 40% English.
        - Tone: {brief['caption_tone']}
        - No generic corporate talk.
        """
        return self.call_gemini(prompt)

    def generate_hashtags(self, brief):
        prompt = f"""
        Generate exactly 15 hashtags for: {brief['product_name']} in {brief['category']}.
        Mix: 3 Broad, 3 Niche, 3 Location (Mumbai/Pune), 3 Seasonal, 3 Brand.
        Return ONLY the hashtags separated by spaces.
        """
        return self.call_gemini(prompt)

    def strategy_check(self, caption, brief):
        prompt = f"""
        Review this caption for Relax Fashionwear strategy alignment:
        
        CAPTION:
        {caption}
        
        BRIEF:
        {json.dumps(brief)}
        
        CRITERIA:
        - Is it Hinglish?
        - Does it use the psychological trigger: {brief['psychological_trigger']}?
        - Is the CTA specific?
        
        If it passes, return "PASSED". If not, return "REJECTED: [reason]".
        """
        return self.call_gemini(prompt)
