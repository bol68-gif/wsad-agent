from apscheduler.schedulers.background import BackgroundScheduler 
from apscheduler.triggers.cron import CronTrigger 
from datetime import datetime 
import threading 
import config 
import time
 
scheduler = BackgroundScheduler(timezone="Asia/Kolkata") 
_app = None 
 
def get_app(): 
    global _app 
    if _app is None: 
        from dashboard.app import create_app 
        _app = create_app() 
    return _app 
 
def run_morning_brief(): 
    print(f"\n{'='*50}") 
    print(f"[{datetime.now().strftime('%H:%M:%S')}] MORNING BRIEF STARTING") 
    print(f"{'='*50}") 
    app = get_app() 
    with app.app_context(): 
        try: 
            from ai_team.strategist import Strategist 
            from dashboard.socketio_events import broadcast_log 
            broadcast_log("Strategist", "MORNING BRIEF", "Starting morning brief — analysing performance data...") 
            s = Strategist() 
            brief = s.morning_brief() 
            broadcast_log("Strategist", "MORNING BRIEF DONE", f"Brief ready — Product: {brief.get('product_name','RF Product')}") 
            print(f"Brief: {brief}") 
            return brief 
        except Exception as e: 
            print(f"Morning brief error: {e}") 
            broadcast_log("System", "ERROR", f"Morning brief failed: {str(e)}") 
            return get_fallback_brief() 
 
def get_fallback_brief(): 
    from data.product_catalog import get_product_for_day 
    from datetime import datetime 
    day = datetime.now().strftime("%A") 
    product = get_product_for_day(day) 
    return { 
        "product_name": product["name"], 
        "category": product["category"], 
        "price": product["price"], 
        "template": "dark_cinematic", 
        "primary_persona": product["target_persona"], 
        "psychological_trigger": "Pain + Identity", 
        "creative_angle": f"Why {product['name']} is the best choice for Indian monsoon", 
        "caption_tone": "Bold and Urgent", 
        "post_type": "static", 
        "ad_potential": True, 
        "reasoning": "Fallback brief — using product catalog data" 
    } 
 
def run_content_creation(): 
    print(f"\n{'='*50}") 
    print(f"[{datetime.now().strftime('%H:%M:%S')}] CONTENT CREATION STARTING") 
    print(f"{'='*50}") 
    app = get_app() 
    with app.app_context(): 
        try: 
            from ai_team.strategist import Strategist 
            from ai_team.copywriter import Copywriter 
            from ai_team.director import Director 
            from data.database import db, Post 
            from dashboard.socketio_events import broadcast_log 
 
            # Step 1 — Get brief 
            broadcast_log("Strategist", "WORKING", "Generating morning brief...") 
            s = Strategist() 
            brief = s.morning_brief() 
            broadcast_log("Strategist", "BRIEF READY", f"Brief: {brief.get('product_name')} — {brief.get('creative_angle','')[:80]}") 
            time.sleep(3) # Rate limit protection
 
            # Step 2 — Write caption 
            broadcast_log("Copywriter", "WORKING", "Writing Hinglish caption — 3 layer process starting...") 
            c = Copywriter() 
            caption = c.write_caption(brief) 
            broadcast_log("Copywriter", "CAPTION READY", f"Caption written: {caption[:100]}...") 
            time.sleep(3) # Rate limit protection
 
            # Step 3 — Director review 
            broadcast_log("Director", "REVIEWING", "Reviewing content — checking all 6 criteria...") 
            d = Director() 
            review = d.review_content(caption, brief.get("template", "dark_cinematic"), brief) 
            approved = d.approve_or_reject(review) 
            score = review.get("overall", 0) 
            broadcast_log("Director", "APPROVED" if approved else "REJECTED", 
                         f"Score: {score}/10 — {'APPROVED ✅' if approved else 'NEEDS REVISION ❌'}") 
            time.sleep(3) # Rate limit protection
 
            # Step 4 — Save post to database 
            post = Post( 
                product_name     = brief.get("product_name", "RF Product"), 
                category         = brief.get("category", ""), 
                caption          = caption, 
                image_path       = "", 
                director_score   = review.get("overall", 0), 
                hook_score       = review.get("hook_score", 0), 
                visual_score     = review.get("visual_score", 0), 
                caption_score    = review.get("caption_score", 0), 
                strategy_score   = review.get("strategy_score", 0), 
                brand_score      = review.get("brand_score", 0), 
                conversion_score = review.get("conversion_score", 0), 
                director_note    = review.get("director_note", ""), 
                ad_ready         = review.get("ad_ready", False), 
                ad_budget        = review.get("ad_budget_suggestion", ""), 
                status           = "pending" if approved else "needs_revision", 
                post_type        = brief.get("post_type", "static"), 
                scheduled_time   = datetime.utcnow(), 
            ) 
            db.session.add(post) 
            db.session.commit() 
            broadcast_log("System", "POST SAVED", f"Post #{post.id} ready — Score: {review.get('overall',0)}/10") 
 
            # Step 5 — Send to Telegram if approved 
            if approved: 
                try: 
                    from distribution.telegram_bot import send_post_preview 
                    send_post_preview( 
                        post_id        = post.id, 
                        image_path     = None, 
                        caption        = caption, 
                        director_score = score, 
                        ad_ready       = review.get("ad_ready", False), 
                        scheduled_time = "Tonight 8:30 PM" 
                    ) 
                    broadcast_log("Telegram", "SENT", f"Post #{post.id} preview sent to your Telegram") 
                except Exception as te: 
                    print(f"Telegram error: {te}") 
 
            return {"success": True, "post_id": post.id} 
 
        except Exception as e: 
            print(f"Content creation error: {e}") 
            import traceback 
            traceback.print_exc() 
            broadcast_log("System", "ERROR", f"Content creation failed: {str(e)}") 
            return {"success": False, "error": str(e)} 
 
def run_weather_check(): 
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Weather check running...") 
    app = get_app() 
    with app.app_context(): 
        try: 
            from data.weather_engine import check_rain_triggers, get_all_cities_weather 
            from data.database import db, WeatherAlert 
            from dashboard.socketio_events import broadcast_log 
 
            weather_data = get_all_cities_weather() 
            broadcast_log("System", "WEATHER CHECK", f"Checked {len(weather_data)} cities") 
 
            triggers = [w for w in weather_data if w.get("trigger")] 
            for city_data in triggers: 
                alert = WeatherAlert( 
                    city           = city_data["city"], 
                    rain_mm        = city_data["rain_mm"], 
                    intensity      = city_data["intensity"], 
                    post_triggered = False 
                ) 
                db.session.add(alert) 
                db.session.commit() 
 
                from distribution.telegram_bot import send_rain_alert 
                send_rain_alert(city_data["city"], city_data["rain_mm"], city_data["intensity"]) 
                broadcast_log("System", "RAIN ALERT", f"Rain detected in {city_data['city']} — {city_data['rain_mm']}mm") 
 
        except Exception as e: 
            print(f"Weather check error: {e}") 
 
def run_analytics_collection(): 
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Analytics collection running...") 
    app = get_app() 
    with app.app_context(): 
        try: 
            from data.database import db, Post, Analytics 
            from dashboard.socketio_events import broadcast_log 
 
            posts = Post.query.filter_by(status="posted").all() 
            total_reach    = sum(p.ig_reach    or 0 for p in posts) 
            total_likes    = sum(p.ig_likes    or 0 for p in posts) 
            total_comments = sum(p.ig_comments or 0 for p in posts) 
            total_saves    = sum(p.ig_saves    or 0 for p in posts) 
 
            analytics = Analytics( 
                platform  = "instagram", 
                reach     = total_reach, 
                likes     = total_likes, 
                comments  = total_comments, 
                saves     = total_saves, 
                followers = 12100 
            ) 
            db.session.add(analytics) 
            db.session.commit() 
            broadcast_log("Analyst", "ANALYTICS", f"Collected — Reach: {total_reach} Likes: {total_likes}") 
 
        except Exception as e: 
            print(f"Analytics error: {e}") 
 
def run_competitor_scan(): 
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Competitor scan running...") 
    app = get_app() 
    with app.app_context(): 
        try: 
            from data.database import db, Competitor 
            from dashboard.socketio_events import broadcast_log 
 
            # Seed known competitors if none exist 
            if Competitor.query.count() == 0: 
                known = [ 
                    {"instagram_handle": "@wildcraft", "brand_name": "Wildcraft India", "followers": 89400}, 
                    {"instagram_handle": "@decathlonin", "brand_name": "Decathlon India", "followers": 245000}, 
                    {"instagram_handle": "@columbiaindiaofficial", "brand_name": "Columbia India", "followers": 34000}, 
                    {"instagram_handle": "@rainsindia", "brand_name": "RAINS India", "followers": 12000}, 
                    {"instagram_handle": "@quechuaindia", "brand_name": "Quechua India", "followers": 28000}, 
                ] 
                for comp in known: 
                    c = Competitor( 
                        instagram_handle = comp["instagram_handle"], 
                        brand_name       = comp["brand_name"], 
                        followers        = comp["followers"], 
                        avg_engagement   = 2.4, 
                        content_gaps     = "No biker content, no delivery partner angle, no Hinglish captions", 
                        active           = True 
                    ) 
                    db.session.add(c) 
                db.session.commit() 
                broadcast_log("Growth Hacker", "COMPETITORS FOUND", f"Seeded {len(known)} Indian rainwear competitors") 
 
            from ai_team.growth_hacker import GrowthHacker 
            g = GrowthHacker() 
            gaps = g.find_gaps() 
            broadcast_log("Growth Hacker", "GAP ANALYSIS", f"Gaps found: {str(gaps)[:200]}") 
 
        except Exception as e: 
            print(f"Competitor scan error: {e}") 
 
def seed_initial_data(): 
    app = get_app() 
    with app.app_context(): 
        try: 
            from data.database import db, Analytics, Notification 
            from datetime import timedelta 
 
            if Analytics.query.count() == 0: 
                for i in range(7): 
                    a = Analytics( 
                        date      = datetime.utcnow() - timedelta(days=i), 
                        platform  = "instagram", 
                        reach     = 1200 + (i * 150), 
                        likes     = 120  + (i * 15), 
                        comments  = 12   + i, 
                        saves     = 45   + (i * 5), 
                        clicks    = 34   + (i * 4), 
                        followers = 12100 
                    ) 
                    db.session.add(a) 
                db.session.commit() 
                print("✅ Analytics seeded") 
 
            if Notification.query.count() == 0: 
                n = Notification( 
                    type    = "info", 
                    title   = "RF Agent Started", 
                    message = "Your AI team is online and working automatically.", 
                    urgent  = False, 
                    read    = False 
                ) 
                db.session.add(n) 
                db.session.commit() 
                print("✅ Welcome notification created") 
 
        except Exception as e: 
            print(f"Seed error: {e}") 
 
def run_full_agent_cycle(): 
    """Runs every 6 hours — full pipeline: brief + caption + review""" 
    print(f"\n[{datetime.now().strftime('%H:%M')}] 🔄 Running scheduled agent cycle...") 
    run_content_creation() 
 
def run_planning_cycle(timeframe="week"):
    """Runs a planning cycle for the strategist"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Planning cycle started for {timeframe}")
    app = get_app()
    with app.app_context():
        try:
            from ai_team.strategist import Strategist
            s = Strategist()
            s.make_plan(timeframe)
        except Exception as e:
            print(f"Planning error: {e}")
 
def startup_sequence(): 
    """Runs immediately when server starts — seeds data and begins agent work""" 
    import time 
    time.sleep(5)  # Wait for Flask to fully start 
 
    print("\n" + "="*50) 
    print("🚀 STARTUP SEQUENCE BEGINNING") 
    print("="*50) 
 
    # Step 1 — Seed initial data 
    seed_initial_data() 
    print("✅ Data seeded") 
 
    # Step 2 — Competitor scan 
    run_competitor_scan() 
    print("✅ Competitors loaded") 
 
    # Step 3 — Check if we need a post today 
    app = get_app() 
    with app.app_context(): 
        from data.database import Post 
        from datetime import date 
        today_posts = Post.query.filter( 
            Post.date >= datetime.utcnow().replace( 
                hour=0, minute=0, second=0) 
        ).count() 
 
        if today_posts == 0: 
            print("📝 No posts today — starting content creation...") 
            run_content_creation() 
        else: 
            print(f"✅ {today_posts} posts already created today") 
 
    print("="*50) 
    print("🎯 Startup sequence complete — agents running") 
    print("="*50 + "\n") 
 
def setup_scheduler(): 
    # ── DAILY SCHEDULED JOBS ────────────────────── 
    scheduler.add_job(run_morning_brief, 
        CronTrigger(hour=2, minute=0), 
        id="morning_brief", replace_existing=True) 
 
    scheduler.add_job(run_content_creation, 
        CronTrigger(hour=3, minute=0), 
        id="content_creation", replace_existing=True) 
 
    scheduler.add_job(run_auto_post_job, 
        CronTrigger(hour=8, minute=30), 
        id="auto_post_morning", replace_existing=True) 
 
    scheduler.add_job(run_auto_post_job, 
        CronTrigger(hour=20, minute=30), 
        id="auto_post_evening", replace_existing=True) 
 
    scheduler.add_job(run_weather_check, 
        "interval", minutes=30, 
        id="weather_check", replace_existing=True) 
 
    scheduler.add_job(run_analytics_collection, 
        "interval", hours=2, 
        id="analytics", replace_existing=True) 
 
    scheduler.add_job(run_competitor_scan, 
        CronTrigger(hour=1, minute=0), 
        id="competitor_scan", replace_existing=True) 
 
    # ── CONTINUOUS IMPROVEMENT LOOP ─────────────── 
    # Runs every 6 hours — keeps agents working around the clock 
    scheduler.add_job(run_full_agent_cycle, 
        "interval", hours=6, 
        id="full_cycle", replace_existing=True) 
 
    scheduler.start() 
    print("✅ Scheduler started — all jobs active") 
 
    # ── RUN IMMEDIATELY ON STARTUP ───────────────── 
    # These run as soon as server starts — no waiting 
    threading.Thread(target=startup_sequence, daemon=True).start() 
 
    return scheduler 
 
def run_auto_post_job(): 
    app = get_app() 
    with app.app_context(): 
        try: 
            from data.database import db, Post 
            from dashboard.socketio_events import broadcast_log 
            approved_posts = Post.query.filter_by( 
                status="approved", owner_approved=True).all() 
            if not approved_posts:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Auto-post: No approved posts to publish.")
                return

            for post in approved_posts: 
                broadcast_log("System", "POSTING", f"Posting Post #{post.id} to Instagram...") 
                post.status    = "posted" 
                post.posted_at = datetime.utcnow() 
                db.session.commit() 
                broadcast_log("System", "POSTED", f"Post #{post.id} marked as posted") 
        except Exception as e: 
            print(f"Auto post error: {e}") 
            broadcast_log("System", "ERROR", f"Auto-post failed: {str(e)}") 
 
def get_scheduler_status(): 
    jobs = [] 
    for job in scheduler.get_jobs(): 
        jobs.append({ 
            "id":       job.id, 
            "next_run": str(job.next_run_time) 
        }) 
    return jobs 
