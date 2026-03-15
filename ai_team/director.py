from ai_team.base_agent import BaseAgent 
import json 
 
class Director(BaseAgent): 
    def __init__(self): 
        super().__init__( 
            name        = "Director", 
            role        = "Senior Creative Director", 
            personality = """ 
You are RF Creative Director. 
15 years building premium Indian brand campaigns. 
Weak content physically pains you. 
You have rejected 10000+ pieces of content in your career. 
Your approval means the content is truly exceptional. 
            """ 
        ) 
        self.revision_count = 0 
 
    def review_content(self, caption, visual_desc, brief): 
        task = f""" 
Review this content for Relax Fashionwear Instagram post. 
 
 CAPTION: 
 {caption} 
 
 VISUAL: {visual_desc} 
 PRODUCT: {brief.get('product_name')} 
 STRATEGY: {brief.get('creative_angle')} 
 
 Score each criteria 1-10. Be brutally honest. 
 
 Return ONLY this JSON — no other text: 
 {{ 
     "hook_score": 0, 
     "visual_score": 0, 
     "caption_score": 0, 
     "strategy_score": 0, 
     "brand_score": 0, 
     "conversion_score": 0, 
     "overall": 0.0, 
     "approved": false, 
     "fixes_needed": [], 
     "director_note": "", 
     "ad_ready": false, 
     "ad_budget_suggestion": "" 
 }} 
         """ 
        result = self.call_gemini(task, brief) 
        try: 
            clean = result.strip() 
            if "```" in clean: 
                clean = clean.split("```")[1] 
                if clean.startswith("json"): 
                    clean = clean[4:] 
            return json.loads(clean) 
        except: 
            return { 
                "hook_score": 7.5, 
                "visual_score": 7.5, 
                "caption_score": 7.5, 
                "strategy_score": 7.5, 
                "brand_score": 7.5, 
                "conversion_score": 7.5, 
                "overall": 7.5, 
                "approved": False, 
                "fixes_needed": ["Could not parse review — using fallback scores"], 
                "director_note": "Review parsing failed — content needs manual check", 
                "ad_ready": False, 
                "ad_budget_suggestion": "" 
            } 
 
    def approve_or_reject(self, review): 
        score = review.get("overall", 0) 
        if score >= 8.5: 
            self.log_and_broadcast( 
                f"APPROVED ✅ Score: {score}/10 — {review.get('director_note','')}", 
                "APPROVED" 
            ) 
            self.revision_count = 0 
            return True 
        elif score >= 7.0: 
            self.log_and_broadcast( 
                f"MINOR FIXES — Score: {score}/10 — Fixes: {', '.join(review.get('fixes_needed',[])[:2])}", 
                "MINOR FIXES" 
            ) 
            self.revision_count += 1 
            return False 
        else: 
            self.log_and_broadcast( 
                f"REJECTED ❌ Score: {score}/10 — Full restart needed", 
                "REJECTED" 
            ) 
            self.revision_count += 1 
            if self.revision_count >= 3: 
                self.stuck_protocol() 
            return False 
 
    def stuck_protocol(self): 
        self.log_and_broadcast( 
            "Stuck protocol triggered — resetting to proven template", 
            "STUCK PROTOCOL" 
        ) 
        self.revision_count = 0 
        try: 
            from distribution.telegram_bot import send_message 
            send_message("⚠️ Director stuck after 3 attempts — resetting to proven template") 
        except: 
            pass 
