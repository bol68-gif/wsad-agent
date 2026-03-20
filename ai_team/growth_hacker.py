from ai_team.base_agent import BaseAgent 
import json 
 
class GrowthHacker(BaseAgent): 
    def __init__(self): 
        super().__init__( 
            name        = "Growth Hacker", 
            role        = "Senior Growth Marketer", 
            personality = """ 
You are RF Senior Growth Hacker with 50 years experience. 
You grew boAt, Mamaearth, Wakefit from zero. 
You see gaps competitors miss completely. 
You are aggressive, specific, and data-driven. 
You never give generic advice. 
Every insight must be actionable and specific. 
            """ 
        ) 
 
    def find_gaps(self): 
        # First call — research competitors 
        competitor_research = self._research_competitors() 
        # Second call — find gaps based on research 
        gaps = self._analyze_gaps(competitor_research) 
        # Third call — create specific content ideas 
        ideas = self._generate_ideas(gaps) 
        return { 
            "competitor_research": competitor_research, 
            "gaps": gaps, 
            "post_ideas": ideas 
        } 
 
    def _research_competitors(self): 
        task = """ 
You are researching Indian rainwear brands on Instagram for competitive analysis. 
 
Research these specific brands and what they post: 
 - Wildcraft India (@wildcraftindia) 
 - Decathlon India (@decathlonin) 
 - Columbia India 
 - Rexine India 
 - Any other Indian rainwear brand you know 
 
 For each brand analyse: 
 1. What content do they post most? 
 2. What audience do they target? 
 3. What languages do they use? 
 4. What segments do they completely ignore? 
 5. What emotional angles do they never use? 
 6. What product categories do they never show? 
 
 Be extremely specific. Use your training knowledge about these brands. 
 Do not make up information — only state what you actually know. 
 
 Return your research as detailed text analysis — not JSON yet. 
 Just write your analysis clearly. 
         """ 
        self.log_and_broadcast( 
            "Researching competitor Instagram strategies...", 
            "RESEARCHING" 
        ) 
        return self.call_gemini(task) 
 
    def _analyze_gaps(self, competitor_research): 
        task = f""" 
 Based on this competitor research: 
 {competitor_research[:2000]} 
 
 And knowing Relax Fashionwear: 
 - Makes raincoats in Pelhar Factory, Bhiwandi 
 - Has heat sealed seams technology (competitors use stitching) 
 - Sells to bikers, delivery partners, women, kids, safety workers 
 - Price range Rs599 to Rs1599 
 - Strong Indian monsoon expertise 
 
 Find 6 VERY SPECIFIC content gaps. 
 Each gap must be: 
 - A specific audience segment nobody targets 
 - Or a specific content format nobody creates 
 - Or a specific emotional angle nobody addresses 
 - Backed by your competitor research above 
 
 Return ONLY valid JSON: 
 {{ 
     "gaps": [ 
         {{ 
             "gap": "very specific description", 
             "why_nobody_does_it": "specific reason based on research", 
             "rf_advantage": "why RF specifically can own this" 
         }} 
     ] 
 }} 
         """ 
        self.log_and_broadcast( 
            "Analysing gaps from competitor research...", 
            "ANALYSING" 
        ) 
        result = self.call_gemini(task) 
        try: 
            clean = result.strip() 
            start = clean.find('{') 
            end   = clean.rfind('}') 
            if start != -1 and end != -1: 
                return json.loads(clean[start:end+1]) 
        except: 
            pass 
        return {"gaps": []} 
 
    def _generate_ideas(self, gaps): 
        gaps_text = json.dumps(gaps, indent=2) if isinstance(gaps, dict) else str(gaps) 
        task = f""" 
 Based on these content gaps for Relax Fashionwear: 
 {gaps_text[:1500]} 
 
 Create 5 VERY SPECIFIC Instagram post ideas. 
 Each idea must: 
 - Target a specific person in a specific situation 
 - Use a specific content format 
 - Have a specific Hindi/Hinglish hook line 
 - Explain exactly why it will perform well 
 
 Return ONLY valid JSON: 
 {{ 
     "ideas": [ 
         {{ 
             "title": "specific post title", 
             "format": "reel/carousel/static", 
             "target_person": "very specific person description", 
             "hook_line": "exact first line in Hinglish", 
             "why_it_works": "specific reason" 
         }} 
     ] 
 }} 
         """ 
        self.log_and_broadcast( 
            "Generating specific content ideas from gaps...", 
            "IDEATING" 
        ) 
        result = self.call_gemini(task) 
        try: 
            clean = result.strip() 
            start = clean.find('{') 
            end   = clean.rfind('}') 
            if start != -1 and end != -1: 
                return json.loads(clean[start:end+1]) 
        except: 
            pass 
        return {"ideas": []} 
 
    def scan_trending_hashtags(self): 
        task = """ 
 You are finding Instagram hashtags for Relax Fashionwear — Indian raincoat brand. 
 
 Think about: 
 1. What hashtags do Indian bikers use on Instagram? 
 2. What hashtags do Indian delivery partners use? 
 3. What hashtags trend during Indian monsoon season? 
 4. What hashtags do Indian moms use when buying for kids? 
 5. What niche hashtags have 10K-500K posts — big enough to get seen, small enough to rank? 
 
 Research this properly using your knowledge of Indian Instagram culture. 
 Find hashtags that are specific to RF's audience — not too generic. 
 
 Return ONLY valid JSON: 
 { 
     "hashtags": ["#tag1", "#tag2"], 
     "trending_topics": ["specific topic"], 
     "reasoning": "why these hashtags specifically" 
 } 
         """ 
        self.log_and_broadcast("Scanning trending hashtags for RF audience...", "WORKING") 
        result = self.call_gemini(task) 
        try: 
            clean = result.strip() 
            start = clean.find('{') 
            end   = clean.rfind('}') 
            if start != -1 and end != -1: 
                return json.loads(clean[start:end+1]) 
        except: 
            return {"hashtags": [], "trending_topics": [], "reasoning": "Parse failed"} 
