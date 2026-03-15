from ai_team.base_agent import BaseAgent 
import json 
 
class GrowthHacker(BaseAgent): 
    def __init__(self): 
        super().__init__( 
            name        = "Growth Hacker", 
            role        = "Senior Growth Marketer", 
            personality = """ 
You are RF Senior Growth Marketer. 
Found the delivery partner segment before any competitor. 
You see gaps like a hawk sees prey from 1000 feet. 
Every competitor weakness is RF opportunity. 
            """ 
        ) 
 
    def find_gaps(self): 
        task = """ 
Analyze these Indian rainwear competitors: 
Wildcraft, Decathlon India, Columbia India, RAINS India, Quechua India 
 
What content are they NOT creating that RF can dominate? 
 
Return ONLY this JSON — no other text: 
 { 
     "gaps": ["gap1", "gap2", "gap3", "gap4"], 
     "opportunities": ["opp1", "opp2", "opp3"], 
     "recommended_content": ["content1", "content2", "content3"] 
 } 
         """ 
        result = self.call_gemini(task) 
        try: 
            clean = result.strip() 
            if "```" in clean: 
                clean = clean.split("```")[1] 
                if clean.startswith("json"): 
                    clean = clean[4:] 
            return json.loads(clean) 
        except: 
            return { 
                "gaps": [ 
                    "No biker delivery partner content", 
                    "No Hinglish captions", 
                    "No factory trust content", 
                    "No monsoon urgency posts" 
                ], 
                "opportunities": [ 
                    "Own delivery partner segment", 
                    "Dominate Hinglish rainwear content" 
                ], 
                "recommended_content": [ 
                    "Biker rain protection reel", 
                    "Factory quality trust post" 
                ] 
            } 
 
    def scan_trending_hashtags(self): 
        task = """ 
Top 15 trending Instagram hashtags in India for 
rainwear, monsoon, bikers, outdoor fashion right now. 
 
Return ONLY this JSON: 
 { 
     "hashtags": ["#tag1", "#tag2"], 
     "trending_topics": ["topic1", "topic2"] 
 } 
         """ 
        result = self.call_gemini(task) 
        try: 
            clean = result.strip() 
            if "```" in clean: 
                clean = clean.split("```")[1] 
                if clean.startswith("json"): 
                    clean = clean[4:] 
            return json.loads(clean) 
        except: 
            return { 
                "hashtags": [ 
                    "#MonsoonIndia", "#BikerLife", "#RainwearIndia", 
                    "#MumbaiRains", "#DeliveryPartner", "#RaincoatIndia", 
                    "#MonsoonReady", "#IndianMonsoon", "#BikerRaincoat", 
                    "#RelaxFashionwear", "#MonsoonFashion", "#RainProtection", 
                    "#HeatSealedSeams", "#FactoryDirect", "#MadeInIndia" 
                ], 
                "trending_topics": ["monsoon prep", "biker safety"] 
            } 
