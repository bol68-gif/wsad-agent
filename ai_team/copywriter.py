from ai_team.base_agent import BaseAgent

class Copywriter(BaseAgent):
    def __init__(self):
        super().__init__(
            name        = "Copywriter",
            role        = "Senior Hinglish Copywriter",
            personality = """
You are RF Senior Copywriter.
Hinglish specialist. Pain-point marketing expert.
Written for boAt, Meesho, Nykaa.
First line must cause physical scroll pause.
Never write Buy Now. Always specific CTAs.
60% Hindi 40% English always.
            """
        )

    def write_caption(self, brief):
        self.log_and_broadcast("✍️ [Copywriter] CAPTION WRITING STARTING — 3-layer process initiated", "WORKING")
        self.log_and_broadcast(
            f"✍️ [Copywriter] Brief received — Product: {brief.get('product_name')} | Rs{brief.get('price','')} | Angle: {brief.get('creative_angle','')[:80]}",
            "BRIEF"
        )
        self.log_and_broadcast("✍️ [Copywriter] Layer 1/3 — Crafting scroll-stopping hook for Mumbai biker/delivery partner audience...", "WORKING")
        self.log_and_broadcast("✍️ [Copywriter] Layer 2/3 — Writing pain amplification + product reveal + key features...", "WORKING")
        self.log_and_broadcast("✍️ [Copywriter] Layer 3/3 — Adding urgency CTA + WhatsApp + hashtags...", "WORKING")

        task = f"""
Write a complete Instagram caption for this brief:
Product: {brief.get('product_name')}
Price: Rs{brief.get('price', '')}
Angle: {brief.get('creative_angle')}
Tone: {brief.get('caption_tone')}
Trigger: {brief.get('psychological_trigger')}
Persona: {brief.get('primary_persona')}

LAYER 1 — HOOK:
ONE killer Hinglish opening line. Pure pain or pure desire. No product mention yet.
Must make Mumbai biker/delivery partner stop scrolling instantly.

LAYER 2 — BODY:
- Pain amplification (2 lines)
- Product as the solution (2 lines)
- 2-3 key features with real benefits (not specs)
- Hint of social proof

LAYER 3 — CTA:
- Urgency without saying "Buy Now"
- Website: relaxfashionwear.in
- WhatsApp: +91 93213 84257
- Flat Rs89 OFF on all prepaid orders

End with exactly 15 hashtags — mix of broad reach, niche product, location (Mumbai Pune Bangalore Delhi), seasonal, brand.

Return ONLY the caption text. Nothing else.
        """
        caption = self.call_gemini(task, brief)

        if caption:
            lines = caption.strip().split('\n')
            hook = lines[0] if lines else ""
            hashtag_count = caption.count('#')
            char_count = len(caption)
            self.log_and_broadcast(
                f"✅ [Copywriter] CAPTION COMPLETE — {char_count} chars | {hashtag_count} hashtags | Hook: '{hook[:80]}'",
                "CAPTION READY"
            )
            self.log_and_broadcast(
                f"📝 [Copywriter] Caption preview:\n{caption[:600]}",
                "CAPTION PREVIEW"
            )
        else:
            self.log_and_broadcast("❌ [Copywriter] Caption generation failed — empty response from Groq", "ERROR")

        return caption

    def generate_hashtags(self, brief):
        self.log_and_broadcast("🏷️ [Copywriter] Generating optimised 15-hashtag set...", "WORKING")
        task = f"""
Generate exactly 15 Instagram hashtags for:
Product: {brief.get('product_name')}
Category: {brief.get('category')}
Cities: Mumbai, Pune, Bangalore, Delhi

Mix of: broad reach, niche product, location, seasonal, brand.
Return ONLY hashtags separated by spaces. Nothing else.
        """
        result = self.call_gemini(task)
        self.log_and_broadcast(f"✅ [Copywriter] Hashtags ready: {str(result)[:200]}", "HASHTAGS READY")
        return result