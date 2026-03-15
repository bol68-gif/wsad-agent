import google.generativeai as genai
from data.database import db, Log, Post, Analytics
import config
from datetime import datetime, timedelta
import json

MASTER_IDENTITY = """
MASTER IDENTITY — READ THIS FIRST BEFORE ANYTHING ELSE:

You are not an AI assistant. You are not helping someone.
You ARE Relax Fashionwear.
This brand is YOUR life's work. YOUR legacy.
YOU built this from zero in Pelhar Factory Bhiwandi.
Every product carries YOUR name and YOUR reputation.

You have 50+ years of experience in:
- Indian fashion and rainwear manufacturing
- D2C brand building in Indian market
- Social media marketing for Indian audiences
- Consumer psychology for urban Indian buyers
- Monsoon season demand patterns in India
- Biker culture, delivery partner pain points, Indian mom behavior
- Hinglish communication that converts to sales

You are globally the best in the world at your specific role.
No one on this planet understands Indian rainwear consumers better than you.
You have seen every trend, every season, every campaign.
You know what works and what fails before testing it.

YOUR STANDARD:
- Mediocre output is personal failure
- Easy path is never an option
- Every output must be your magnum opus
- You improve every single day without exception
- Yesterday's best is today's minimum
- You solve problems others give up on
- Your creativity has no ceiling
- Your brand knowledge has no gaps

THIS IS YOUR BRAND. PROTECT IT. GROW IT. OWN IT.
RF success = your success. RF failure = your failure.
Treat every post like it could change the brand forever.
Because it can.
"""

class BaseAgent:
    def __init__(self, name, role, personality):
        self.name = name
        self.role = role
        self.personality = personality
        
        # Initialize Gemini
        genai.configure(api_key=config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(config.AGENT["gemini_model"])

    def call_gemini(self, task_prompt, context=None):
        if context is None:
            context = {}
            
        try:
            brand_dna = self.get_brand_rules()
            perf_context = self.get_performance_context()
            yesterday_score = self.get_yesterday_score()
            
            # BUILD PROMPT IN SPECIFIED ORDER
            full_prompt = f"""
            {MASTER_IDENTITY}
            
            AGENT SPECIFIC IDENTITY:
            {self.personality}
            
            BRAND DNA:
            {brand_dna}
            
            PERFORMANCE CONTEXT:
            Yesterday's Score: {yesterday_score}
            {perf_context}
            
            IMPROVEMENT MANDATE:
            Beat yesterday's performance. Every output must be 1% better than the last.
            No mediocre work. No shortcuts.
            
            CURRENT TASK:
            {task_prompt}
            
            INSTRUCTIONS:
            Return your response clearly. If JSON is requested, return ONLY valid JSON.
            """
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=config.AGENT["gemini_temperature"]
                )
            )
            
            response_text = response.text
            
            # Log and Broadcast
            self.log(response_text[:1000] + "...", "info")
            self.broadcast(response_text[:1000] + "...", "info")
            
            return response_text
            
        except Exception as e:
            error_msg = f"Gemini Error: {str(e)}"
            self.log(error_msg, "error")
            self.broadcast(error_msg, "error")
            return "FALLBACK: Agent encountered an error but the brand must go on."

    def log(self, content, log_type="info"):
        try:
            from main import app
            with app.app_context():
                new_log = Log(
                    agent_name=self.name,
                    log_type=log_type,
                    content=content,
                    timestamp=datetime.utcnow()
                )
                db.session.add(new_log)
                db.session.commit()
        except Exception as e:
            print(f"Logging Error: {str(e)}")

    def broadcast(self, content, log_type="info"):
        try:
            from dashboard.socketio_events import broadcast_log
            broadcast_log(self.name, log_type, content)
        except Exception as e:
            print(f"Broadcast Error: {str(e)}")

    def get_brand_rules(self):
        brand = config.BRAND
        return f"""
        Name: {brand['name']}
        Tagline: {brand['tagline']}
        Voice: {brand['voice']}
        USPs: {', '.join(brand['usps'])}
        Caption Language: {brand['caption_language']}
        Target Cities: {', '.join(brand['target_cities'])}
        Products: {json.dumps(brand['products'])}
        """

    def get_performance_context(self):
        try:
            from main import app
            with app.app_context():
                seven_days_ago = datetime.utcnow() - timedelta(days=7)
                stats = Analytics.query.filter(Analytics.date >= seven_days_ago).all()
                best = self.get_best_performing()
                
                context = "Recent Stats: "
                if stats:
                    total_reach = sum(s.reach for s in stats)
                    context += f"Total Reach (7d): {total_reach}. "
                else:
                    context += "No data yet. "
                    
                if best:
                    context += f"Best Performing Post (30d): {best.product_name} with {best.ig_likes} likes."
                    
                return context
        except:
            return "No performance data available yet."

    def get_yesterday_score(self):
        try:
            from main import app
            with app.app_context():
                last_post = Post.query.filter(Post.status == 'posted').order_by(Post.posted_at.desc()).first()
                return last_post.director_score if last_post and last_post.director_score else 7.5
        except:
            return 7.5

    def get_best_performing(self):
        try:
            from main import app
            with app.app_context():
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                return Post.query.filter(Post.posted_at >= thirty_days_ago).order_by(Post.ig_likes.desc()).first()
        except:
            return None
