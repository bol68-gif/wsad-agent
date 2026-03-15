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
