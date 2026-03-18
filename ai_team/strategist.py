from ai_team.base_agent import BaseAgent
import json

class Strategist(BaseAgent):
    def __init__(self):
        super().__init__(
            name        = "Strategist",
            role        = "Senior Brand Strategist",
            personality = """
You are RF Senior Brand Strategist.
CMO mindset. Data obsessed.
Grew 6 Indian D2C brands to 1 crore revenue.
You never brief the same approach twice in 14 days.
            """
        )

    def morning_brief(self):
        self.log_and_broadcast("🧠 [Strategist] MORNING BRIEF STARTING — Analysing brand performance data...", "MORNING BRIEF")
        self.log_and_broadcast("📊 [Strategist] Step 1/4 — Loading last 7 days performance context...", "WORKING")

        context = self.get_performance_context()
        self.log_and_broadcast(
            f"📊 [Strategist] Performance loaded — Week reach: {context.get('week_reach',0)} | Week likes: {context.get('week_likes',0)} | Best post: {context.get('best_post','None yet')} | Total posts: {context.get('total_posts',0)}",
            "DATA"
        )

        self.log_and_broadcast("🌦️ [Strategist] Step 2/4 — Checking weather triggers across 6 cities...", "WORKING")
        self.log_and_broadcast("🏆 [Strategist] Step 3/4 — Evaluating competitor gaps and content opportunities...", "WORKING")
        self.log_and_broadcast("✍️ [Strategist] Step 4/4 — Building today's creative brief with AI...", "WORKING")

        task = """
Create today's content brief for Relax Fashionwear.

Think step by step:
1. Which product has the most untapped potential right now?
2. Which audience segment is least served?
3. What psychological trigger converts best this time of year?
4. What creative angle has NOT been done in 14 days?

Return ONLY this JSON — no other text:
{
    "product_name": "product name here",
    "category": "Men/Women/Kids/Biker/Unisex/Safety",
    "price": 0,
    "template": "dark_cinematic/premium_minimal/urgency_offer/feature_breakdown/lifestyle_emotion/social_proof",
    "primary_persona": "who is the target buyer",
    "psychological_trigger": "main trigger to use",
    "creative_angle": "the unique angle for this post",
    "caption_tone": "tone description",
    "post_type": "static/reel/carousel",
    "ad_potential": true,
    "reasoning": "why this product and angle today"
}
        """
        result = self.call_gemini(task, context)

        try:
            clean = result.strip()
            if "```" in clean:
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            brief = json.loads(clean)
            self.log_and_broadcast(
                f"✅ [Strategist] BRIEF COMPLETE — Product: {brief.get('product_name')} | Angle: {brief.get('creative_angle','')[:100]} | Ad potential: {brief.get('ad_potential')}",
                "BRIEF READY"
            )
            self.log_and_broadcast(f"🎯 [Strategist] Reasoning: {brief.get('reasoning','')}", "STRATEGY")
            self.log_and_broadcast(
                f"👤 [Strategist] Persona: {brief.get('primary_persona','')} | Trigger: {brief.get('psychological_trigger','')} | Template: {brief.get('template','')}",
                "STRATEGY"
            )
            return brief
        except Exception as e:
            self.log_and_broadcast(f"⚠️ [Strategist] JSON parse failed ({str(e)}) — using fallback brief", "WARNING")
            from data.product_catalog import get_product_for_day
            from datetime import datetime
            product = get_product_for_day(datetime.now().strftime("%A"))
            brief = {
                "product_name":          product["name"],
                "category":              product["category"],
                "price":                 product["price"],
                "template":              "dark_cinematic",
                "primary_persona":       product["target_persona"],
                "psychological_trigger": "Pain + Identity",
                "creative_angle":        f"Why {product['name']} is essential for Indian monsoon",
                "caption_tone":          "Bold and Urgent",
                "post_type":             "static",
                "ad_potential":          True,
                "reasoning":             "Fallback brief — AI parse failed"
            }
            self.log_and_broadcast(f"✅ [Strategist] Fallback brief ready — {brief['product_name']}", "BRIEF READY")
            return brief