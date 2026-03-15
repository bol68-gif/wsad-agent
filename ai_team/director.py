from ai_team.base_agent import BaseAgent
import json
import config

class Director(BaseAgent):
    def __init__(self):
        personality = """
        YOUR SPECIFIC IDENTITY:
        You are the Creative Director who built RF's visual identity from scratch.
        You have approved campaigns for 50+ Indian fashion brands.
        You have rejected 10,000+ pieces of content in your career.
        You know instantly within 3 seconds if content will perform.
        Weak content physically pains you.
        Your approval means the content is truly exceptional.
        Your rejection always comes with the exact fix needed.
        """
        super().__init__(name="Director", role="Creative Director", personality=personality)

    def review_content(self, caption, visual_desc, brief):
        self.log("Reviewing content for quality and brand alignment...", "info")
        
        task_prompt = f"""
        Review the following social media content:
        
        CAPTION:
        {caption}
        
        VISUAL DESCRIPTION:
        {visual_desc}
        
        STRATEGY BRIEF:
        {json.dumps(brief)}
        
        INSTRUCTIONS:
        Analyze this content against Relax Fashionwear's high standards. 
        Calculate scores for hook, visual, caption, strategy, brand, and conversion.
        Determine if it's approved (score >= 8.5).
        If not approved, provide a specific list of fixes_needed.
        
        Return ONLY this exact JSON format:
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
        
        response_text = self.call_gemini(task_prompt)
        
        try:
            # Clean response text if Gemini adds markdown code blocks
            clean_json = response_text.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:-3].strip()
            elif clean_json.startswith("```"):
                clean_json = clean_json[3:-3].strip()
                
            review = json.loads(clean_json)
            
            # Recalculate overall based on specific weights
            review['overall'] = self.calculate_overall_score(review)
            
            self.log(f"Director Review: {review['overall']}/10 - {'APPROVED' if review['overall'] >= 8.5 else 'REJECTED'}", "DIRECTOR REVIEW")
            return review
        except Exception as e:
            self.log(f"Director JSON Parse Error: {str(e)}", "error")
            # Default scores on failure
            return {
                "hook_score": 5.0, "visual_score": 5.0, "caption_score": 5.0,
                "strategy_score": 5.0, "brand_score": 5.0, "conversion_score": 5.0,
                "overall": 5.0, "approved": False, "fixes_needed": ["System error during review. Manual check required."],
                "director_note": "Fallback review due to system error.", "ad_ready": False, "ad_budget_suggestion": ""
            }

    def approve_or_reject(self, review_json):
        score = review_json.get('overall', 0.0)
        
        if score >= 8.5:
            self.log("DIRECTOR APPROVED: Content is magnum opus material.", "success")
            self.broadcast("DIRECTOR APPROVED: Content is magnum opus material.", "success")
            return True
        elif score >= 7.0:
            fixes = ", ".join(review_json.get('fixes_needed', []))
            self.log(f"MINOR FIXES NEEDED: {fixes}", "warning")
            self.broadcast(f"MINOR FIXES NEEDED: {fixes}", "warning")
            return False
        else:
            self.log(f"FULL REJECTION: Content is mediocre. Score: {score}", "error")
            self.broadcast(f"FULL REJECTION: Content is mediocre. Score: {score}", "error")
            # Logic for stuck protocol would go here in the main workflow
            return False

    def calculate_overall_score(self, review_json):
        # Hook 20% + Visual 20% + Caption 15% + Strategy 15% + Brand 15% + Conversion 15%
        score = (
            review_json.get('hook_score', 0) * 0.20 +
            review_json.get('visual_score', 0) * 0.20 +
            review_json.get('caption_score', 0) * 0.15 +
            review_json.get('strategy_score', 0) * 0.15 +
            review_json.get('brand_score', 0) * 0.15 +
            review_json.get('conversion_score', 0) * 0.15
        )
        return round(score, 1)

    def stuck_protocol(self):
        self.log("STUCK PROTOCOL TRIGGERED: 3 failed revision attempts.", "error")
        # In a real scenario, this would send a Telegram alert
        # from distribution.telegram_bot import send_alert
        # send_alert("STUCK PROTOCOL: Director has rejected content 3 times. Manual intervention needed.")
        return "FALLBACK: Using best proven template due to revision loop."

    def get_fix_instructions(self, review_json):
        fixes = review_json.get('fixes_needed', [])
        return "Fixes required: " + "; ".join(fixes)
