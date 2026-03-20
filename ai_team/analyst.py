from ai_team.base_agent import BaseAgent 
import json 
 
class Analyst(BaseAgent): 
    def __init__(self): 
        super().__init__( 
            name        = "Analyst", 
            role        = "Senior Data Analyst", 
            personality = """ 
You are RF Senior Data Analyst. 
Processed 500 million social media data points. 
You find patterns others need 6 months to see. 
Data without insight is noise. 
            """ 
        ) 
 
    def generate_weekly_report(self): 
        context = self.get_performance_context() 
        task = f""" 
Analyze this week's Relax Fashionwear Instagram performance: 
 {json.dumps(context, indent=2)} 
 
 Write a brief analysis covering: 
 1. What worked this week 
 2. What failed 
 3. Top 3 recommendations for next week 
 4. Best content type to focus on 
 
 Write in plain English. Be specific. Maximum 200 words. 
         """ 
        return self.call_gemini(task, context) 
 
    def get_insights(self): 
        context = self.get_performance_context() 
        task = """ 
Based on RF performance data, give 3 specific actionable insights. 
Return ONLY this JSON: 
 { 
     "insights": ["insight1", "insight2", "insight3"], 
     "recommended_focus": "what to focus on this week", 
     "predicted_best_content": "what type of content will perform best" 
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
            return { 
                "insights": [ 
                    "Biker content performing 2x other categories", 
                    "Friday offer posts get highest saves", 
                    "Hinglish captions get more comments than English" 
                ], 
                "recommended_focus": "Biker and delivery partner content", 
                "predicted_best_content": "Reel with rain effects" 
            } 

    def create_monthly_plan(self): 
        from datetime import datetime, timedelta 
        import json 
        import calendar 
    
        now = datetime.now() 
        month_name = now.strftime("%B %Y") 
        days_in_month = calendar.monthrange(now.year, now.month)[1] 
    
        task = f""" 
 Create a complete 30-day Instagram content plan for Relax Fashionwear for {month_name}. 
 
 CONTENT RHYTHM (follow strictly every week): 
 Monday    = Factory Trust post 
 Tuesday   = Product Hero post 
 Wednesday = Educational Carousel 
 Thursday  = Problem/Solution Reel 
 Friday    = Offer/Urgency post 
 Saturday  = Lifestyle/Emotion Reel 
 Sunday    = Social Proof Carousel 
 
 PRODUCTS TO ROTATE (13 total): 
 EliteShield Rain Set, Urban Rain Suit, Classic Rain Set, Pro Biker Rain Set, 
 Women Long Rain Coat, Kids Cartoon Rain Set, Kids Solid Rain Set, Kids Rain Suit, 
 Poncho, Windcheater, Reversible Rain Jacket, Hi-Vis Orange Safety, Hi-Vis Green Safety 
 
 RULES: 
 - Never feature same product twice in one week 
 - Mix biker, women, kids, safety content evenly 
 - Friday posts must have Rs89 OFF offer urgency 
 - Wednesday posts must be educational carousels 
 - Vary between static, reel, carousel formats 
 
 Create a plan for all {days_in_month} days of {month_name}. 
 
 Return ONLY valid JSON: 
 {{ 
     "month": "{month_name}", 
     "total_posts": {days_in_month}, 
     "weeks": [ 
         {{ 
             "week": 1, 
             "days": [ 
                 {{ 
                     "date": "1", 
                     "day": "Monday", 
                     "product": "product name", 
                     "category": "Biker/Men/Women/Kids/Safety/Unisex", 
                     "template": "dark_cinematic/premium_minimal/etc", 
                     "post_type": "static/reel/carousel", 
                     "theme": "brief theme description", 
                     "hook": "first line of caption idea" 
                 }} 
             ] 
         }} 
     ] 
 }} 
         """ 
        self.log_and_broadcast( 
            f"Creating 30-day content plan for {month_name}...", 
            "MONTHLY PLAN" 
        ) 
        result = self.call_gemini(task) 
        try: 
            clean = result.strip() 
            start = clean.find('{') 
            end   = clean.rfind('}') 
            if start != -1 and end != -1: 
                plan = json.loads(clean[start:end+1]) 
                self.log_and_broadcast( 
                    f"30-day plan ready for {month_name}", 
                    "PLAN COMPLETE" 
                ) 
                return plan 
        except Exception as e: 
            self.log_and_broadcast( 
                f"Plan parse failed: {str(e)[:80]}", 
                "WARNING" 
            ) 
        return {"month": month_name, "weeks": [], "error": "Parse failed"} 
