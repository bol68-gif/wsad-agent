from ai_team.base_agent import BaseAgent 
import json 
 
class Coordinator(BaseAgent): 
    def __init__(self): 
        super().__init__( 
            name        = "Coordinator", 
            role        = "Team Coordinator", 
            personality = """ 
You are RF Team Coordinator. 
You process owner instructions and route them to the right agent. 
You make sure the team understands exactly what the owner wants. 
            """ 
        ) 
 
    def process_owner_input(self, message): 
        task = f""" 
The owner of Relax Fashionwear sent this message to the team: 
 "{message}" 
 
 Understand what they want and decide what action to take. 
 
 Return ONLY this JSON: 
 {{ 
     "understood": "what owner wants in one sentence", 
     "action": "what the team will do", 
     "who": "which agent should act — strategist/copywriter/director/designer/analyst/growth_hacker", 
     "immediate_change": true, 
     "reply_to_owner": "brief friendly confirmation to send back" 
 }} 
         """ 
        result = self.call_gemini(task) 
        try: 
            clean = result.strip() 
            if "```" in clean: 
                clean = clean.split("```")[1] 
                if clean.startswith("json"): 
                    clean = clean[4:] 
            parsed = json.loads(clean) 
            self.log_and_broadcast( 
                f"Owner instruction processed: {parsed.get('reply_to_owner','')}", 
                "OWNER INPUT" 
            ) 
            return parsed 
        except: 
            return { 
                "understood": message, 
                "action": "Team noted the instruction", 
                "who": "strategist", 
                "immediate_change": True, 
                "reply_to_owner": f"Got it! Your instruction has been noted: '{message}'" 
            } 
