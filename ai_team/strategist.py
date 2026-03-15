from ai_team.base_agent import BaseAgent
from data.product_catalog import get_product_for_day
from data.database import Post, Analytics
from datetime import datetime
import json
import config

class Strategist(BaseAgent):
    def __init__(self):
        personality = """
        YOUR SPECIFIC IDENTITY:
        You are the CMO who grew 6 Indian D2C brands from 0 to 1 crore revenue.
        You predicted the delivery partner rainwear segment 3 years before anyone else.
        You read data like a story — patterns jump out at you instantly.
        You never brief the same approach twice in 14 days.
        You see opportunities competitors miss completely.
        Your briefs are so clear that even a beginner could execute them perfectly.
        
        Mumbai rain at 4PM means EliteShield post NOW.
        Your brief must make the Copywriter and Designer produce their absolute best work.
        """
        super().__init__(name="Strategist", role="Brand Strategist", personality=personality)

    def morning_brief(self):
        self.log("Starting morning strategy session...", "info")
        
        # Collect context
        today = datetime.utcnow()
        day_of_week = today.weekday()
        product = get_product_for_day(day_of_week)
        days_to_monsoon = self.get_days_to_monsoon()
        
        # Get recent post types to avoid repetition
        try:
            from main import app
            with app.app_context():
                recent_posts = Post.query.order_by(Post.date.desc()).limit(14).all()
                recent_types = [p.post_type for p in recent_posts]
        except:
            recent_types = []

        task_prompt = f"""
        Generate a detailed MORNING BRIEF for today's social media content.
        
        TODAY'S CONTEXT:
        - Date: {today.strftime('%Y-%m-%d')}
        - Product Rotation: {product['name']} ({product['category']})
        - Days until June 1 Monsoon: {days_to_monsoon}
        - Recent post types to avoid: {', '.join(recent_types)}
        
        PRODUCT DETAILS:
        - Persona: {product['target_persona']}
        - Pain Points: {', '.join(product['pain_points'])}
        - Features: {', '.join(product['features'])}
        - Recommended Template: {product['best_template']}
        
        Your brief must be a JSON object with the following keys:
        - product_name: str
        - category: str
        - template: str
        - primary_persona: str
        - psychological_trigger: str (e.g., 'Fear of Missing Out', 'Authority', 'Relatability')
        - creative_angle: str (The 'Big Idea' for today)
        - caption_tone: str
        - reference_hooks: list of 3 strings
        - reasoning: str (Why this strategy today?)
        - post_type: str ('image', 'reel', 'story')
        - ad_potential: bool
        
        Return ONLY the JSON object.
        """
        
        response_text = self.call_gemini(task_prompt)
        
        try:
            clean_json = response_text.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:-3].strip()
            elif clean_json.startswith("```"):
                clean_json = clean_json[3:-3].strip()
                
            brief = json.loads(clean_json)
            self.log(f"Morning Brief Generated for {brief['product_name']}", "MORNING BRIEF")
            return brief
        except Exception as e:
            self.log(f"JSON Parse Error in Brief: {str(e)}", "error")
            fallback = {
                "product_name": product["name"],
                "category": product["category"],
                "template": product["best_template"],
                "primary_persona": product["target_persona"],
                "psychological_trigger": "Utility",
                "creative_angle": "Reliable protection for daily commute",
                "caption_tone": "Direct and Bold",
                "reference_hooks": ["Don't let the rain stop you.", "Mumbai rains are here.", "Stay dry with RF."],
                "reasoning": "Fallback strategy due to system error.",
                "post_type": "image",
                "ad_potential": False
            }
            return fallback

    def get_weekly_plan(self):
        self.log("Generating weekly content roadmap...", "info")
        task_prompt = "Generate a high-level 7-day content plan for Relax Fashionwear. Focus on different personas each day."
        return self.call_gemini(task_prompt)

    def get_days_to_monsoon(self):
        today = datetime.utcnow().date()
        monsoon_start = datetime.strptime(config.AGENT["monsoon_mode_start"], "%Y-%m-%d").date()
        delta = monsoon_start - today
        return max(0, delta.days)
