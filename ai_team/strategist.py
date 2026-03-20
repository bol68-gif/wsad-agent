from ai_team.base_agent import BaseAgent 
import json 
from datetime import datetime 
 
class Strategist(BaseAgent): 
    def __init__(self): 
        super().__init__( 
            name        = "Strategist", 
            role        = "Senior Brand Strategist", 
            personality = """ 
 You are RF Senior Brand Strategist with 50 years experience. 
 You built campaigns for Woodland, Red Chief, Wildcraft. 
 You understand Indian consumer psychology at a deep level. 
 You never repeat the same creative approach twice. 
 Every brief must be unique, specific, and executable. 
             """ 
        ) 
 
    def morning_brief(self): 
        context     = self.get_performance_context() 
        day_of_week = datetime.now().strftime("%A") 
        date_str    = datetime.now().strftime("%d %B %Y") 
 
        self.log_and_broadcast( 
            f"Starting morning brief for {day_of_week} {date_str}", 
            "MORNING BRIEF" 
        ) 
 
        # Step 1 — Understand today's opportunity 
        opportunity = self._find_todays_opportunity(day_of_week, context) 
 
        # Step 2 — Pick the best product and angle 
        brief = self._create_brief(day_of_week, opportunity, context) 
 
        return brief 
 
    def _find_todays_opportunity(self, day, context): 
        task = f""" 
 Today is {day}. You are planning Instagram content for Relax Fashionwear. 
 
 PERFORMANCE CONTEXT: 
 Total posts made: {context.get('total_posts', 0)} 
 This week reach: {context.get('week_reach', 0)} 
 This week likes: {context.get('week_likes', 0)} 
 Best performing post: {context.get('best_post', 'None yet')} 
 
 CONTENT RHYTHM (follow this strictly): 
 Monday    = Factory/Manufacturing trust content 
 Tuesday   = Product desire — one product hero 
 Wednesday = Educational carousel — teach something valuable 
 Thursday  = Problem vs Solution — pain then RF as answer 
 Friday    = Offer/Urgency — price, scarcity, FOMO 
 Saturday  = Lifestyle/Emotion — aspirational, cinematic 
 Sunday    = Social Proof — reviews, customer stories, trust 
 
 TODAY IS: {day.upper()} 
 
 RELAX FASHIONWEAR PRODUCTS: 
 Biker segment: EliteShield Rs1599, Pro Biker Rain Set Rs1599 
 Men segment: Urban Rain Suit Rs1450, Classic Rain Set Rs1399 
 Women segment: Women Long Rain Coat Rs1399 
 Kids segment: Kids Cartoon Rs899, Kids Solid Rs899, Kids Rain Suit Rs999 
 Unisex: Poncho Rs599, Windcheater Rs799, Reversible Jacket Rs1599 
 Safety: Hi-Vis Orange Rs1199, Hi-Vis Green Rs1199 
 
 BRAND STRENGTHS: 
 - Heat sealed seams (competitors use stitching — this leaks) 
 - Factory direct from Pelhar Bhiwandi (no middleman) 
 - 3000mm waterproof rating 
 - Anti-sweat breathable design 
 - Reflective strips for night safety 
 
 Based on today being {day} and the content rhythm: 
 1. What is the biggest opportunity today? 
 2. Which specific customer is most likely to buy today? 
 3. What emotional state are they in today specifically? 
 4. What has NOT been done in recent posts? 
 
 Answer these 4 questions in detail. Be very specific. 
 Think like a CMO planning a campaign, not a social media manager posting randomly. 
         """ 
        self.log_and_broadcast( 
            f"Analysing {day}'s content opportunity...", 
            "WORKING" 
        ) 
        return self.call_gemini(task, context) 
 
    def _create_brief(self, day, opportunity, context): 
        task = f""" 
 Based on this opportunity analysis: 
 {opportunity[:2000]} 
 
 Create a SPECIFIC, DETAILED content brief for Relax Fashionwear Instagram. 
 
 The brief must be completely unique — imagine you have never made this type of post before. 
 Think of ONE specific person, ONE specific moment, ONE specific emotion. 
 
 Return ONLY valid JSON — no markdown, no extra text: 
 {{ 
     "product_name": "exact product name", 
     "category": "Biker/Men/Women/Kids/Unisex/Safety", 
     "price": 0, 
     "template": "dark_cinematic/premium_minimal/urgency_offer/feature_breakdown/lifestyle_emotion/social_proof", 
     "primary_persona": "extremely specific person — their job, city, exact situation right now", 
     "psychological_trigger": "Pain/Identity/Authority/Scarcity/Social Proof/Value/Urgency", 
     "creative_angle": "unique specific angle — one sentence, very concrete, tells a story", 
     "hook_idea": "exact first line in Hinglish that stops scroll", 
     "caption_tone": "Bold Urgent/Emotional Relatable/Educational Trust/FOMO", 
     "post_type": "static/reel/carousel", 
     "ad_potential": true, 
     "day_theme": "why this fits {day}'s content rhythm", 
     "reasoning": "specific reasons why this product and angle will work today" 
 }} 
         """ 
        self.log_and_broadcast( 
            "Creating detailed content brief...", 
            "WORKING" 
        ) 
        result = self.call_gemini(task, context) 
 
        try: 
            clean = result.strip() 
            if "```" in clean: 
                parts = clean.split("```") 
                for part in parts: 
                    part = part.strip() 
                    if part.startswith("json"): 
                        part = part[4:].strip() 
                    try: 
                        return json.loads(part) 
                    except: 
                        continue 
            start = clean.find('{') 
            end   = clean.rfind('}') 
            if start != -1 and end != -1: 
                return json.loads(clean[start:end+1]) 
            return json.loads(clean) 
        except Exception as e: 
            self.log_and_broadcast( 
                f"Brief JSON parse failed — retrying with simpler prompt: {str(e)[:50]}", 
                "WARNING" 
            ) 
            return self._retry_brief(day) 
 
    def _retry_brief(self, day): 
        task = f""" 
 Create a content brief for Relax Fashionwear for {day}. 
 Give me ONLY a JSON object with these exact keys: 
 product_name, category, price, template, primary_persona, 
 psychological_trigger, creative_angle, hook_idea, caption_tone, 
 post_type, ad_potential, day_theme, reasoning 
 
 Make it specific and unique. Today is {day}. 
 Return ONLY the JSON object. Nothing else. 
         """ 
        self.log_and_broadcast("Retrying brief generation...", "RETRY") 
        result = self.call_gemini(task) 
        try: 
            clean = result.strip() 
            start = clean.find('{') 
            end   = clean.rfind('}') 
            if start != -1 and end != -1: 
                return json.loads(clean[start:end+1]) 
        except: 
            pass 
        # Last resort — minimal valid brief 
        return { 
            "product_name":         "EliteShield Rain Set", 
            "category":             "Biker", 
            "price":                1599, 
            "template":             "dark_cinematic", 
            "primary_persona":      "Delivery partner riding in Mumbai monsoon", 
            "psychological_trigger":"Pain + Identity", 
            "creative_angle":       "Heat sealed seams vs stitched seams — which keeps you dry", 
            "hook_idea":            "Baarish mein bheeg gaye? Galat raincoat ki wajah se.", 
            "caption_tone":         "Bold Urgent", 
            "post_type":            "static", 
            "ad_potential":         True, 
            "day_theme":            f"{day} content", 
            "reasoning":            "Auto-generated after parse failure" 
        } 
