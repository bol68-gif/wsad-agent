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
 
            # Add product features so templates can use them 
            try: 
                from data.product_catalog import PRODUCTS 
                for p in PRODUCTS: 
                    pname = p.get("name","").lower() 
                    bname = brief.get("product_name","").lower() 
                    if pname in bname or bname in pname or any( 
                            w in bname for w in pname.split() 
                            if len(w) > 3): 
                        brief["features"] = p.get("features", []) 
                        brief["target_persona"] = p.get("target_persona", "") 
                        brief["pain_points"] = p.get("pain_points", []) 
                        break 
            except Exception as e: 
                print(f"Features lookup error: {e}")

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
 
            # Step 5 — Designer builds visual assets 
            broadcast_log("Designer", "WORKING", f"Starting visual pipeline for Post #{post.id}...") 
            try: 
                from ai_team.designer import Designer 
                designer = Designer() 
                assets   = designer.create_post_assets(brief, caption, post_id=post.id) 
                image_path = assets.get("final_image", "") 
                if assets.get("success"): 
                    broadcast_log("Designer", "VISUAL COMPLETE", 
                        f"Post #{post.id} image ready — {image_path}") 
                else: 
                    broadcast_log("Designer", "WARNING", 
                        f"Visual pipeline used fallback — upload product images at /products") 
            except Exception as de: 
                image_path = "" 
                broadcast_log("Designer", "ERROR", f"Designer failed: {str(de)[:100]}") 
            time.sleep(2) 
 
            # Step 6 — Send to Telegram if approved 
            if approved: 
                try: 
                    from distribution.telegram_bot import send_post_preview 
                    send_post_preview( 
                        post_id        = post.id, 
                        image_path     = image_path, 
                        caption        = caption, 
                        director_score = score, 
                        ad_ready       = review.get("ad_ready", False), 
                        scheduled_time = "Tonight 8:30 PM" 
                    ) 
                    broadcast_log("Telegram", "SENT", f"Post #{post.id} preview sent to Telegram with image") 
                except Exception as te: 
                    print(f"Telegram error: {te}") 
 
            return {"success": True, "post_id": post.id, "image_path": image_path} 
  
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
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Analytics collection running via analytics_engine...") 
    try: 
        from data.analytics_engine import run_analytics_collection as _run 
        _run() 
    except Exception as e: 
        print(f"Analytics engine error: {e}") 
        import traceback; traceback.print_exc() 
 
def run_competitor_scan(): 
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Competitor scan running via competitor_engine...") 
    try: 
        from data.competitor_engine import run_competitor_scan as _run 
        _run() 
    except Exception as e: 
        print(f"Competitor engine error: {e}") 
        import traceback; traceback.print_exc() 
 
def seed_initial_data(): 
    app = get_app() 
    with app.app_context(): 
        try: 
            from data.database import db, Analytics, Competitor, Notification 
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
                    title   = "RF Agent is Live!", 
                    message = "Your AI team is online. Click Generate Post Now in Pipeline to create your first post.", 
                    urgent  = False, 
                    read    = False 
                ) 
                db.session.add(n) 
                db.session.commit() 
                print("✅ Welcome notification created") 
 
        except Exception as e: 
            print(f"Seed error: {e}") 
 
def startup_content_check(): 
    """Auto-starts content creation if no posts today""" 
    import time 
    time.sleep(15) 
    app = get_app() 
    with app.app_context(): 
        from data.database import Post 
        from dashboard.socketio_events import broadcast_log 
        today = datetime.utcnow().replace(hour=0, minute=0, second=0) 
        count = Post.query.filter(Post.scheduled_time >= today).count() 
        if count == 0: 
            broadcast_log("System", "STARTUP", 
                "No posts today — auto-starting content creation...") 
            run_content_creation() 
        else: 
            broadcast_log("System", "STARTUP", 
                f"{count} posts already exist today — agents on standby") 
 
def get_recent_posts_context(): 
    """Returns last 14 posts so agents never repeat""" 
    app = get_app() 
    with app.app_context(): 
        from data.database import Post 
        posts = Post.query.order_by(Post.scheduled_time.desc()).limit(14).all() 
        return [ 
            { 
                "product": p.product_name, 
                "category": p.category, 
                "template": p.template_used or "unknown", 
                "score": p.director_score or 0, 
                "date": p.scheduled_time.strftime("%A %d %b") if p.scheduled_time else "", 
                "post_type": p.post_type or "static" 
            } 
            for p in posts 
        ] 
 
def run_monthly_plan(): 
    """Analyst creates a 30-day content plan — runs 1st of every month""" 
    app = get_app() 
    with app.app_context(): 
        try: 
            from ai_team.analyst import Analyst 
            from dashboard.socketio_events import broadcast_log 
            broadcast_log("Analyst", "MONTHLY PLAN", 
                "Creating 30-day content calendar...") 
            a = Analyst() 
            plan = a.create_monthly_plan() 
            broadcast_log("Analyst", "PLAN READY", 
                f"30-day plan created — {len(plan.get('weeks',[]))} weeks planned") 
            # Save to settings 
            from data.database import db, Settings 
            setting = Settings.query.filter_by( 
                key="monthly_plan").first() 
            if not setting: 
                setting = Settings(key="monthly_plan") 
                db.session.add(setting) 
            import json 
            setting.value = json.dumps(plan) 
            db.session.commit() 
        except Exception as e: 
            print(f"Monthly plan error: {e}") 
 
def setup_scheduler(): 
    # Morning brief — 2AM IST 
    scheduler.add_job(run_morning_brief, CronTrigger(hour=2, minute=0), 
                      id="morning_brief", replace_existing=True) 
    # Content creation — 3AM IST 
    scheduler.add_job(run_content_creation, CronTrigger(hour=3, minute=0), 
                      id="content_creation", replace_existing=True) 
    # Auto post morning — 8:30AM IST 
    scheduler.add_job(run_auto_post_job, CronTrigger(hour=8, minute=30), 
                      id="auto_post_morning", replace_existing=True) 
    # Auto post evening — 8:30PM IST 
    scheduler.add_job(run_auto_post_job, CronTrigger(hour=20, minute=30), 
                      id="auto_post_evening", replace_existing=True) 
    # Weather — every 30 mins 
    scheduler.add_job(run_weather_check, "interval", minutes=30, 
                      id="weather_check", replace_existing=True) 
    # Analytics — every 2 hours 
    scheduler.add_job(run_analytics_collection, "interval", hours=2, 
                      id="analytics", replace_existing=True) 
    # Competitor scan — daily 1AM 
    scheduler.add_job(run_competitor_scan, CronTrigger(hour=1, minute=0), 
                      id="competitor_scan", replace_existing=True) 
    # Learning engine — runs at 4AM daily after content creation 
    scheduler.add_job(run_learning_cycle, CronTrigger(hour=4, minute=0), 
                      id="learning_cycle", replace_existing=True) 
    # Every 6 hours — keeps posts flowing all day 
    scheduler.add_job(run_content_creation, "interval", hours=6, 
                      id="content_cycle", replace_existing=True) 
    # Monthly plan — 1st of every month at midnight 
    scheduler.add_job(run_monthly_plan, CronTrigger(day=1, hour=0, minute=0), 
                      id="monthly_plan", replace_existing=True) 
 
    scheduler.start() 
    print("✅ Scheduler started — all jobs active") 
 
    # Run immediately on startup in protected threads
    def run_protected(target, name):
        try:
            target()
        except Exception as e:
            print(f"❌ Startup job '{name}' failed: {e}")

    threading.Thread(target=run_protected, args=(seed_initial_data, "seed"), daemon=True).start() 
    threading.Thread(target=run_protected, args=(run_competitor_scan, "competitor_scan"), daemon=True).start() 
    threading.Thread(target=run_protected, args=(startup_content_check, "startup_check"), daemon=True).start() 
    threading.Thread(target=run_protected, args=(_check_monthly_plan, "monthly_plan_check"), daemon=True).start() 
 
    return scheduler 
 
def _check_monthly_plan(): 
    import time 
    time.sleep(30) 
    app = get_app() 
    with app.app_context(): 
        from data.database import Settings 
        existing = Settings.query.filter_by(key="monthly_plan").first() 
        if not existing or not existing.value: 
            run_monthly_plan() 
 
def run_learning_cycle(): 
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Learning cycle running via learning_engine...") 
    try: 
        from data.learning_engine import run_learning_cycle as _run 
        _run() 
    except Exception as e: 
        print(f"Learning engine error: {e}") 
        import traceback; traceback.print_exc() 
 
def run_auto_post_job(): 
    app = get_app() 
    with app.app_context(): 
        try: 
            from data.database import db, Post 
            from dashboard.socketio_events import broadcast_log 
            approved = Post.query.filter_by( 
                status="approved", owner_approved=True).all() 
            for post in approved: 
                broadcast_log("System", "POSTING", f"Posting Post #{post.id} to Instagram...") 
                post.status    = "posted" 
                post.posted_at = datetime.utcnow() 
                db.session.commit() 
                broadcast_log("System", "POSTED", f"Post #{post.id} marked as posted") 
        except Exception as e: 
            print(f"Auto post error: {e}") 
 
def get_scheduler_status(): 
    jobs = [] 
    for job in scheduler.get_jobs(): 
        jobs.append({ 
            "id":       job.id, 
            "next_run": str(job.next_run_time) 
        }) 
    return jobs 
