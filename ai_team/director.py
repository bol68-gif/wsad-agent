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
        self.log_and_broadcast("🎬 [Director] CONTENT REVIEW STARTING — Checking all 6 criteria...", "REVIEWING")
        self.log_and_broadcast(f"🎬 [Director] Content to review: {brief.get('product_name')} | Template: {visual_desc}", "REVIEWING")
        self.log_and_broadcast("🎬 [Director] Criteria 1/6 — HOOK strength — scroll-stop power...", "WORKING")
        self.log_and_broadcast("🎬 [Director] Criteria 2/6 — VISUAL concept quality...", "WORKING")
        self.log_and_broadcast("🎬 [Director] Criteria 3/6 — CAPTION flow and Hinglish authenticity...", "WORKING")
        self.log_and_broadcast("🎬 [Director] Criteria 4/6 — STRATEGY alignment with brief...", "WORKING")
        self.log_and_broadcast("🎬 [Director] Criteria 5/6 — BRAND voice consistency...", "WORKING")
        self.log_and_broadcast("🎬 [Director] Criteria 6/6 — CONVERSION potential and CTA strength...", "WORKING")
        self.log_and_broadcast("🎬 [Director] Calculating scores — minimum 8.5/10 required for approval...", "WORKING")

        task = f"""
Review this content for Relax Fashionwear Instagram post.

CAPTION:
{caption}

VISUAL: {visual_desc}
PRODUCT: {brief.get('product_name')}
STRATEGY: {brief.get('creative_angle')}
TARGET: {brief.get('primary_persona')}
TRIGGER: {brief.get('psychological_trigger')}

Score each criteria 1-10. Be brutally honest.
Minimum 8.5 overall to approve. If below, list SPECIFIC actionable fixes.

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
            review = json.loads(clean)
            score = review.get('overall', 0)
            self.log_and_broadcast(
                f"🎬 [Director] SCORES — Hook:{review.get('hook_score')}/10 | Visual:{review.get('visual_score')}/10 | Caption:{review.get('caption_score')}/10 | Strategy:{review.get('strategy_score')}/10 | Brand:{review.get('brand_score')}/10 | Conversion:{review.get('conversion_score')}/10",
                "SCORES"
            )
            self.log_and_broadcast(
                f"🎬 [Director] OVERALL: {score}/10 | Ad ready: {review.get('ad_ready')} | {review.get('director_note','')}",
                "OVERALL SCORE"
            )
            if review.get('fixes_needed'):
                self.log_and_broadcast(
                    f"🎬 [Director] Fixes needed: {' | '.join(review.get('fixes_needed',[]))}",
                    "FIXES"
                )
            return review
        except Exception as e:
            self.log_and_broadcast(f"⚠️ [Director] JSON parse failed ({str(e)}) — using fallback scores", "WARNING")
            return {
                "hook_score": 7.5, "visual_score": 7.5, "caption_score": 7.5,
                "strategy_score": 7.5, "brand_score": 7.5, "conversion_score": 7.5,
                "overall": 7.5, "approved": False,
                "fixes_needed": ["Parse failed — manual check needed"],
                "director_note": "Review parse failed",
                "ad_ready": False, "ad_budget_suggestion": ""
            }

    def approve_or_reject(self, review):
        score = review.get("overall", 0)
        if score >= 8.5:
            self.log_and_broadcast(
                f"✅ [Director] APPROVED — {score}/10 — Content meets RF standards. {review.get('director_note','')}",
                "APPROVED"
            )
            self.revision_count = 0
            return True
        elif score >= 7.0:
            self.log_and_broadcast(
                f"🔄 [Director] MINOR FIXES — {score}/10 — Sending back to Copywriter. Fixes: {' | '.join(review.get('fixes_needed',[])[:3])}",
                "MINOR FIXES"
            )
            self.revision_count += 1
            return False
        else:
            self.log_and_broadcast(
                f"❌ [Director] REJECTED — {score}/10 — Does not meet RF standards. Full restart.",
                "REJECTED"
            )
            self.revision_count += 1
            if self.revision_count >= 3:
                self.stuck_protocol()
            return False

    def stuck_protocol(self):
        self.log_and_broadcast(
            "🚨 [Director] STUCK PROTOCOL — 3 attempts failed. Resetting to proven template. Alerting Krishna via Telegram.",
            "STUCK PROTOCOL"
        )
        self.revision_count = 0
        try:
            from distribution.telegram_bot import send_message
            send_message("⚠️ Director stuck after 3 attempts — resetting to proven template. Check logs.")
        except:
            pass

## FILE 7 of 7 — `dashboard/templates/logs.html`
# In your project folder run:
# Just replace the file from the fixed version I already built above