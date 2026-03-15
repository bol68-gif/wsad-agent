from groq import Groq 
from datetime import datetime 
import config 
import time 
import json 
 
client = Groq(api_key=config.GROQ_API_KEY) 
 
class BaseAgent: 
    def __init__(self, name, role, personality): 
        self.name        = name 
        self.role        = role 
        self.personality = personality 
        self.model       = "llama-3.3-70b-versatile" 
 
    def _build_prompt(self, task_prompt, context={}): 
        brand    = config.BRAND 
        yesterday_score = self.get_yesterday_score() 
 
        return f""" 
 MASTER IDENTITY — READ THIS FIRST: 
 
 You are not an AI assistant. You ARE Relax Fashionwear. 
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
 
 YOUR STANDARD: 
 - Mediocre output is personal failure 
 - Easy path is never an option 
 - Every output must be your magnum opus 
 - You improve every single day without exception 
 - Yesterday score was {yesterday_score} — beat it today 
 - Your creativity has no ceiling 
 
 THIS IS YOUR BRAND. PROTECT IT. GROW IT. OWN IT. 
 
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 
 YOUR SPECIFIC ROLE: {self.role} 
 YOUR IDENTITY: {self.personality} 
 
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 
 BRAND DNA: 
 Name: {brand['name']} 
 Website: {brand['website']} 
 WhatsApp: {brand['whatsapp']} 
 Offer: {brand['offer']} 
 Voice: {brand['voice']} 
 Cities: {', '.join(brand['cities'])} 
 USPs: {', '.join(brand['usps'])} 
 
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 
 CONTEXT: 
 {json.dumps(context, indent=2) if context else 'No additional context'} 
 
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 
 YOUR TASK: 
 {task_prompt} 
 """ 
 
    def call_gemini(self, task_prompt, context={}): 
        """Main method — named call_gemini for compatibility but uses Groq""" 
        max_retries = 3 
        for attempt in range(max_retries): 
            try: 
                full_prompt = self._build_prompt(task_prompt, context) 
                result = self._call_groq(full_prompt) 
                if result is not None: 
                    return result 
            except Exception as e: 
                error = str(e) 
                if "429" in error or "rate" in error.lower(): 
                     wait = 30 * (attempt + 1) 
                     self.log_and_broadcast( 
                         f"Rate limit — waiting {wait}s — attempt {attempt+1}/{max_retries}", 
                         "WARNING" 
                     ) 
                     time.sleep(wait) 
                else: 
                     self.log_and_broadcast(f"Error: {error[:150]}", "ERROR") 
                     if attempt == max_retries - 1: 
                         return "" 
                     time.sleep(5) 
        return "" 

    def _call_groq(self, prompt): 
        import time 
        for attempt in range(3): 
            try: 
                if not config.GROQ_API_KEY: 
                    return None 
                from groq import Groq 
                client = Groq(api_key=config.GROQ_API_KEY) 
                self.broadcast(f"{self.name} thinking... attempt {attempt+1}", "WORKING") 
                response = client.chat.completions.create( 
                    model       = self.model, 
                    messages    = [{"role": "user", "content": prompt}], 
                    max_tokens  = 1500, 
                    temperature = 0.8 
                ) 
                result = response.choices[0].message.content 
                self.log_and_broadcast(result[:400], f"{self.name.upper()} OUTPUT") 
                return result 
            except Exception as e: 
                err = str(e) 
                self.log_and_broadcast(f"Groq error attempt {attempt+1}: {err[:80]}", "ERROR") 
                if attempt < 2: 
                    time.sleep(10 * (attempt + 1)) 
                else: 
                    return None 
        return None 
 
    def log(self, content, log_type="INFO"): 
        try: 
            from dashboard.app import get_app 
            app = get_app() 
            with app.app_context(): 
                from data.database import db, Log 
                entry = Log( 
                    agent_name = self.name, 
                    log_type   = log_type, 
                    content    = str(content)[:2000] 
                ) 
                db.session.add(entry) 
                db.session.commit() 
        except Exception as e: 
            print(f"[LOG ERROR] [{self.name}][{log_type}] {str(e)[:100]}") 
            print(f"[{self.name}][{log_type}] {str(content)[:200]}") 
 
    def broadcast(self, content, log_type="INFO"): 
        try: 
            from dashboard.socketio_events import broadcast_log 
            broadcast_log(self.name, log_type, str(content)[:500]) 
        except Exception as e: 
            pass 
 
    def log_and_broadcast(self, content, log_type="INFO"): 
        print(f"[{datetime.now().strftime('%H:%M:%S')}][{self.name}][{log_type}] {str(content)[:150]}") 
        self.log(content, log_type) 
        self.broadcast(content, log_type) 
 
    def get_yesterday_score(self): 
        try: 
            from dashboard.app import get_app 
            app = get_app() 
            with app.app_context(): 
                from data.database import Post 
                last = Post.query.order_by(Post.date.desc()).first() 
                return last.director_score if last else 7.0 
        except: 
            return 7.0 
 
    def get_performance_context(self): 
        try: 
            from dashboard.app import get_app 
            app = get_app() 
            with app.app_context(): 
                from data.database import Analytics, Post 
                analytics = Analytics.query.order_by( 
                    Analytics.date.desc()).limit(7).all() 
                best = Post.query.order_by(Post.ig_likes.desc()).first() 
                return { 
                    "week_reach":  sum(a.reach or 0 for a in analytics), 
                    "week_likes":  sum(a.likes or 0 for a in analytics), 
                    "best_post":   best.product_name if best else "None yet", 
                    "total_posts": Post.query.count() 
                } 
        except: 
            return {} 
