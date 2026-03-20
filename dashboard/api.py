from flask import Blueprint, jsonify, request 
from flask_login import login_required 
from data.database import db, Post, Log, Analytics, WeatherAlert, Notification, OwnerInput, Settings 
from datetime import datetime 
import config 
import os 

api_bp = Blueprint("api", __name__) 

# ── STATUS ──────────────────────────────────────────── 
@api_bp.route("/status") 
@login_required 
def status(): 
    setting = Settings.query.filter_by(key="agent_status").first() 
    agent_status = setting.value if setting else "running" 
    return jsonify({ 
        "status": agent_status, 
        "version": "1.0", 
        "last_action": "System startup", 
        "next_job": "Weather check at 09:00", 
        "gemini_calls_today": 0 
    }) 
 
# ── TEST ROUTES ─────────────────────────────────────── 
@api_bp.route("/test/models") 
@login_required 
def list_models(): 
    from groq import Groq 
    import config 
    client = Groq(api_key=config.GROQ_API_KEY) 
    models = [m.id for m in client.models.list()] 
    return jsonify({"models": models}) 
 
# ── LOGS ────────────────────────────────────────────── 
@api_bp.route("/logs") 
@login_required 
def get_logs(): 
    logs = Log.query.order_by(Log.timestamp.desc()).limit(50).all() 
    return jsonify([log.to_dict() for log in logs]) 

# ── POSTS ───────────────────────────────────────────── 
@api_bp.route("/posts/pending") 
@login_required 
def pending_posts(): 
    posts = Post.query.filter(Post.status == "pending").all() 
    return jsonify([p.to_dict() for p in posts]) 

@api_bp.route("/posts/posted") 
@login_required 
def posted_posts(): 
    posts = Post.query.filter(Post.status == "posted").all() 
    return jsonify([p.to_dict() for p in posts]) 

@api_bp.route("/posts/<int:post_id>/approve", methods=["POST"]) 
@login_required 
def approve_post(post_id): 
    post = Post.query.get(post_id) 
    if not post: 
        return jsonify({"success": False, "message": "Post not found"}), 404 
    post.status       = "approved" 
    post.owner_approved = True 
    post.approved_at  = datetime.utcnow() 
    db.session.commit() 
    return jsonify({"success": True, "message": f"Post approved and scheduled"}) 

@api_bp.route("/posts/<int:post_id>/skip", methods=["POST"]) 
@login_required 
def skip_post(post_id): 
    post = Post.query.get(post_id) 
    if not post: 
        return jsonify({"success": False, "message": "Post not found"}), 404 
    post.status = "skipped" 
    db.session.commit() 
    return jsonify({"success": True, "message": "Post skipped"}) 

@api_bp.route("/posts/<int:post_id>/regenerate", methods=["POST"]) 
@login_required 
def regenerate_post(post_id): 
    post = Post.query.get(post_id) 
    if not post: 
        return jsonify({"success": False, "message": "Post not found"}), 404 
    post.status = "regenerating" 
    db.session.commit() 
    return jsonify({"success": True, "message": "Regeneration queued — check logs"}) 

# ── CALENDAR ────────────────────────────────────────── 
@api_bp.route("/calendar/<int:year>/<int:month>") 
@login_required 
def calendar_data(year, month): 
    posts = Post.query.filter( 
        db.extract('year',  Post.date) == year, 
        db.extract('month', Post.date) == month 
    ).all() 
    return jsonify([p.to_dict() for p in posts]) 

# ── ANALYTICS ───────────────────────────────────────── 
@api_bp.route("/analytics/summary") 
@login_required 
def analytics_summary(): 
    from data.database import Analytics, Post 
    analytics = Analytics.query.order_by( 
        Analytics.date.desc()).limit(7).all() 
    total_reach    = sum(a.reach    or 0 for a in analytics) 
    total_likes    = sum(a.likes    or 0 for a in analytics) 
    total_saves    = sum(a.saves    or 0 for a in analytics) 
    total_comments = sum(a.comments or 0 for a in analytics) 
    best = Post.query.order_by(Post.ig_likes.desc()).first() 
    return jsonify({ 
        "week_reach":    total_reach, 
        "week_likes":    total_likes, 
        "week_saves":    total_saves, 
        "week_comments": total_comments, 
        "best_post":     best.product_name if best else "No posts yet", 
        "followers":     12100, 
        "daily_data":    [a.to_dict() for a in reversed(analytics)] 
    }) 
 
@api_bp.route("/analytics/chart_data") 
@login_required 
def chart_data(): 
    from data.database import Analytics 
    data = Analytics.query.order_by( 
        Analytics.date.desc()).limit(30).all() 
    return jsonify({ 
        "labels": [a.date.strftime("%d %b") if a.date else "" for a in reversed(data)], 
        "reach":  [a.reach  or 0 for a in reversed(data)], 
        "likes":  [a.likes  or 0 for a in reversed(data)], 
        "saves":  [a.saves  or 0 for a in reversed(data)], 
    }) 

# ── WEATHER ─────────────────────────────────────────── 
@api_bp.route("/scheduler/status") 
@login_required 
def scheduler_status(): 
    try: 
        from scheduler import get_scheduler_status 
        jobs = get_scheduler_status() 
        return jsonify({"success": True, "jobs": jobs}) 
    except Exception as e: 
        return jsonify({"success": False, "message": str(e)}) 
 
@api_bp.route("/scheduler/run_now/<job_name>", methods=["POST"]) 
@login_required 
def run_job_now(job_name): 
    try: 
        import threading 
        jobs = { 
            "morning_brief":    "run_morning_brief", 
            "content_creation": "run_content_creation", 
            "weather_check":    "run_weather_check", 
            "auto_post":        "run_auto_post_job", 
            "analytics":        "run_analytics_collection", 
            "competitor_scan":  "run_competitor_scan", 
            "make_plan":        "run_planning_cycle",
        } 
        if job_name not in jobs: 
            return jsonify({"success": False, 
                            "message": f"Unknown job: {job_name}"}) 
 
        import scheduler as sched 
        func = getattr(sched, jobs[job_name]) 
        threading.Thread(target=func, daemon=True).start() 
 
        return jsonify({ 
            "success": True, 
            "message": f"{job_name} started — watch logs page for live updates" 
        }) 
    except Exception as e: 
        return jsonify({"success": False, "message": str(e)}) 

@api_bp.route("/planner/generate", methods=["POST"])
@login_required
def generate_plan():
    data = request.get_json()
    timeframe = data.get("timeframe", "week")
    try:
        from ai_team.strategist import Strategist
        s = Strategist()
        plan = s.make_plan(timeframe)
        if plan:
            return jsonify({"success": True, "plan": plan})
        return jsonify({"success": False, "message": "Failed to generate plan"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@api_bp.route("/agents/status") 
@login_required 
def agents_status(): 
    from data.database import Log 
    from datetime import timedelta 
 
    # Get last action per agent in last 24 hours 
    agents = ["Strategist","Copywriter","Designer", 
              "Director","Analyst","Growth Hacker"] 
    result = {} 
    for agent in agents: 
        last_log = Log.query.filter( 
            Log.agent_name == agent, 
            Log.timestamp >= datetime.utcnow() - timedelta(hours=24) 
        ).order_by(Log.timestamp.desc()).first() 
 
        result[agent.lower().replace(" ","_")] = { 
            "name":        agent, 
            "last_action": last_log.log_type if last_log else "Never", 
            "last_time":   last_log.timestamp.strftime("%H:%M") if last_log else "—", 
            "content":     last_log.content[:80] if last_log else "Waiting...", 
            "status":      "active" if last_log else "idle" 
        } 
 
    # Get scheduler jobs 
    try: 
        from scheduler import get_scheduler_status 
        jobs = get_scheduler_status() 
    except: 
        jobs = [] 
 
    return jsonify({ 
        "agents": result, 
        "scheduler_jobs": jobs, 
        "total_logs_today": Log.query.filter( 
            Log.timestamp >= datetime.utcnow().replace( 
                hour=0, minute=0, second=0) 
        ).count() 
    }) 
 
@api_bp.route("/weather")
@login_required
def get_weather_alerts():
    from data.database import WeatherAlert
    alerts = WeatherAlert.query.order_by(WeatherAlert.timestamp.desc()).limit(20).all()
    return jsonify([a.to_dict() for a in alerts])

@api_bp.route("/weather/current") 
@login_required 
def current_weather(): 
    try: 
        from data.weather_engine import get_all_cities_weather 
        data = get_all_cities_weather() 
        return jsonify({"success": True, "data": data}) 
    except Exception as e: 
        cities = config.BRAND.get("cities", ["Mumbai","Pune","Bangalore","Delhi","Chennai","Hyderabad"]) 
        data   = [{"city": c, "condition": "Unknown", 
                   "rain_mm": 0, "intensity": "none"} for c in cities] 
        return jsonify({"success": True, "data": data}) 
 
# ── NOTIFICATIONS ───────────────────────────────────── 
@api_bp.route("/notifications") 
@login_required 
def get_notifications(): 
    notifications = Notification.query.order_by( 
        Notification.timestamp.desc()).limit(20).all() 
    return jsonify([n.to_dict() for n in notifications]) 

# ── MONTHLY PLAN ────────────────────────────────────── 
@api_bp.route("/monthly_plan") 
@login_required 
def get_monthly_plan(): 
    from data.database import Settings 
    import json 
    setting = Settings.query.filter_by(key="monthly_plan").first() 
    if setting and setting.value: 
        try: 
            return jsonify(json.loads(setting.value)) 
        except: 
            pass 
    return jsonify({"weeks": [], "message": "No plan yet — generating..."}) 
 
@api_bp.route("/monthly_plan/generate", methods=["POST"]) 
@login_required 
def generate_monthly_plan(): 
    import threading 
    from scheduler import run_monthly_plan 
    threading.Thread(target=run_monthly_plan, daemon=True).start() 
    return jsonify({"success": True, "message": "Monthly plan generating — check logs"}) 

@api_bp.route("/notifications/unread_count") 
@login_required 
def unread_count(): 
    count = Notification.query.filter_by(read=False).count() 
    return jsonify({"count": count}) 

@api_bp.route("/notifications/mark_read/<int:notif_id>", methods=["POST"]) 
@login_required 
def mark_read(notif_id): 
    n = Notification.query.get(notif_id) 
    if n: 
        n.read = True 
        db.session.commit() 
    return jsonify({"success": True, "message": "Marked as read"}) 

@api_bp.route("/notifications/mark_all_read", methods=["POST"]) 
@login_required 
def mark_all_read(): 
    Notification.query.update({"read": True}) 
    db.session.commit() 
    return jsonify({"success": True, "message": "All notifications marked as read"}) 

@api_bp.route("/notifications/create_test", methods=["POST"]) 
@login_required 
def create_test_notification(): 
    n = Notification( 
        type="test", 
        title="Test Alert from RF Agent", 
        message="This is a test notification. System is working correctly.", 
        urgent=False, 
        read=False 
    ) 
    db.session.add(n) 
    db.session.commit() 
    return jsonify({"success": True, "message": "Test notification created"}) 

# ── SETTINGS ────────────────────────────────────────── 
@api_bp.route("/settings/all") 
@login_required 
def get_settings(): 
    settings = Settings.query.all() 
    return jsonify({s.key: s.value for s in settings}) 

@api_bp.route("/settings/update", methods=["POST"]) 
@login_required 
def update_settings(): 
    data = request.get_json() 
    for key, value in data.items(): 
        setting = Settings.query.filter_by(key=key).first() 
        if setting: 
            setting.value      = str(value) 
            setting.updated_at = datetime.utcnow() 
        else: 
            db.session.add(Settings(key=key, value=str(value))) 
    db.session.commit() 
    return jsonify({"success": True, "message": "Settings saved successfully"}) 

@api_bp.route("/settings/add_city", methods=["POST"]) 
@login_required 
def add_city(): 
    data = request.get_json() 
    city = data.get("city", "").strip() 
    if not city: 
        return jsonify({"success": False, "message": "City name is required"}) 
    setting = Settings.query.filter_by(key="target_cities").first() 
    if not setting: 
        setting = Settings(key="target_cities", 
                           value="Mumbai,Pune,Bangalore,Delhi,Chennai,Hyderabad") 
        db.session.add(setting) 
    cities = [c.strip() for c in setting.value.split(",") if c.strip()] 
    if city not in cities: 
        cities.append(city) 
        setting.value      = ",".join(cities) 
        setting.updated_at = datetime.utcnow() 
        db.session.commit() 
        return jsonify({"success": True, "message": f"{city} added", "cities": cities}) 
    return jsonify({"success": False, "message": f"{city} already exists", "cities": cities}) 

@api_bp.route("/settings/remove_city", methods=["POST"]) 
@login_required 
def remove_city(): 
    data = request.get_json() 
    city = data.get("city", "").strip() 
    setting = Settings.query.filter_by(key="target_cities").first() 
    if setting: 
        cities = [c.strip() for c in setting.value.split(",") if c.strip() and c.strip() != city] 
        setting.value      = ",".join(cities) 
        setting.updated_at = datetime.utcnow() 
        db.session.commit() 
        return jsonify({"success": True, "message": f"{city} removed", "cities": cities}) 
    return jsonify({"success": False, "message": "No cities found"}) 

@api_bp.route("/settings/pause_agent", methods=["POST"]) 
@login_required 
def pause_agent(): 
    setting = Settings.query.filter_by(key="agent_status").first() 
    if not setting: 
        db.session.add(Settings(key="agent_status", value="paused")) 
    else: 
        setting.value = "paused" 
    db.session.commit() 
    return jsonify({"success": True, "message": "Agent paused successfully"}) 

@api_bp.route("/settings/resume_agent", methods=["POST"]) 
@login_required 
def resume_agent(): 
    setting = Settings.query.filter_by(key="agent_status").first() 
    if not setting: 
        db.session.add(Settings(key="agent_status", value="running")) 
    else: 
        setting.value = "running" 
    db.session.commit() 
    return jsonify({"success": True, "message": "Agent resumed successfully"}) 

@api_bp.route("/products/scrape", methods=["POST"]) 
@login_required 
def scrape_website_products(): 
    try: 
        from data.product_scraper import scrape_products 
        products = scrape_products() 
        return jsonify({ 
            "success": True, 
            "message": f"Scraped {len(products)} products from relaxfashionwear.in", 
            "products": products 
        }) 
    except Exception as e: 
        return jsonify({"success": False, "message": str(e)}) 

# ── PRODUCTS ────────────────────────────────────────── 
from werkzeug.utils import secure_filename 
 
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'} 
 
def allowed_file(filename): 
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS 
 
@api_bp.route("/products/<int:product_id>/upload_image", methods=["POST"]) 
@login_required 
def upload_product_image(product_id): 
    from data.database import Product 
    product = Product.query.get(product_id) 
    if not product: 
        return jsonify({"success": False, "message": "Product not found"}) 
    if 'image' not in request.files: 
        return jsonify({"success": False, "message": "No image file provided"}) 
    file = request.files['image'] 
    if file.filename == '': 
        return jsonify({"success": False, "message": "No file selected"}) 
    if not allowed_file(file.filename): 
        return jsonify({"success": False, "message": "Only JPG, PNG, WEBP allowed"}) 
    filename  = secure_filename(f"product_{product_id}_{file.filename}") 
    save_dir  = os.path.join("assets", "products", str(product_id)) 
    os.makedirs(save_dir, exist_ok=True) 
    save_path = os.path.join(save_dir, filename) 
    file.save(save_path) 
    # Normalize path to forward slashes for cross-platform compatibility
    product.primary_image = save_path.replace("\\", "/") 
    db.session.commit() 
    return jsonify({ 
        "success":   True, 
        "message":   "Image uploaded successfully", 
        "image_url": f"/static/products/{product_id}/{filename}" 
    }) 
 
@api_bp.route("/products/add", methods=["POST"]) 
@login_required 
def add_product(): 
    from data.database import Product 
    data    = request.get_json() 
    name    = data.get("name", "").strip() 
    if not name: 
        return jsonify({"success": False, "message": "Product name required"}) 
    product = Product( 
        name           = name, 
        category       = data.get("category", ""), 
        price          = int(data.get("price", 0)), 
        stock          = int(data.get("stock", 0)), 
        description    = data.get("description", ""), 
        features       = data.get("features", ""), 
        target_persona = data.get("target_persona", ""), 
        website_url    = data.get("website_url", ""), 
        priority       = data.get("priority", "medium"), 
    ) 
    db.session.add(product) 
    db.session.commit() 
    return jsonify({"success": True, "message": f"{name} added successfully", "id": product.id}) 
 
@api_bp.route("/products/all") 
@login_required 
def get_products(): 
    from data.database import Product 
    products = Product.query.filter_by(active=True).all() 
    if not products: 
        from data.product_catalog import PRODUCTS 
        results = []
        for i, p in enumerate(PRODUCTS):
            p_copy = p.copy()
            p_copy['id'] = i + 1000
            p_copy['post_count'] = 0
            p_copy['avg_engagement'] = 0.0
            p_copy['primary_image'] = None
            results.append(p_copy)
        return jsonify(results) 
    return jsonify([p.to_dict() for p in products]) 

# ── COMPETITORS ─────────────────────────────────────── 
@api_bp.route("/competitors/gap_analysis")
@login_required
def get_gap_analysis():
    from data.competitor_engine import run_gap_analysis
    # In a real app, you'd fetch the latest saved analysis. 
    # For now, let's run it or return fallback.
    analysis = run_gap_analysis()
    return jsonify(analysis)

@api_bp.route("/competitors/all") 
@login_required 
def get_competitors(): 
    from data.competitor_engine import get_competitor_summary, run_competitor_scan 
    competitors = get_competitor_summary() 
    if not competitors: 
        import threading 
        threading.Thread(target=run_competitor_scan, daemon=True).start() 
        return jsonify([]) 
    return jsonify(competitors) 

@api_bp.route("/competitors/scan", methods=["POST"]) 
@login_required 
def scan_competitors(): 
    from data.competitor_engine import run_competitor_scan 
    import threading 
    threading.Thread(target=run_competitor_scan, daemon=True).start() 
    return jsonify({"success": True, 
                    "message": "Competitor scan started — check logs page for updates"}) 

# ── OWNER INPUT ─────────────────────────────────────── 
@api_bp.route("/owner/input", methods=["POST"]) 
@login_required 
def owner_input(): 
    from data.database import OwnerInput 
    from dashboard.socketio_events import broadcast_log 
    data    = request.get_json() 
    message = data.get("message", "").strip() 
    if not message: 
        return jsonify({"success": False, "message": "Message required"}) 
 
    # Save to database 
    inp = OwnerInput( 
        channel      = "dashboard", 
        message      = message, 
        action_taken = "Processing..." 
    ) 
    db.session.add(inp) 
    db.session.commit() 
 
    # Broadcast to logs immediately 
    broadcast_log("System", "OWNER INPUT", 
                   f"Owner instruction received: '{message}'") 
 
    # Process in background thread 
    import threading 
    def process_instruction(): 
        try: 
            broadcast_log("Coordinator", "WORKING", 
                         f"Processing owner instruction: '{message}'") 
            from ai_team.coordinator import Coordinator 
            coord  = Coordinator() 
            result = coord.process_owner_input(message) 
            reply  = result.get("reply_to_owner", "Got it!") if isinstance(result, dict) else "Instruction noted" 
            broadcast_log("Coordinator", "OWNER INPUT PROCESSED", 
                         f"✅ {reply}") 
 
            # Update owner input record 
            from dashboard.app import create_app 
            app = create_app() 
            with app.app_context(): 
                from data.database import db, OwnerInput 
                record = OwnerInput.query.order_by( 
                    OwnerInput.id.desc()).first() 
                if record: 
                    record.action_taken = reply 
                    db.session.commit() 
 
            # Send Telegram confirmation 
            try: 
                from distribution.telegram_bot import send_message 
                send_message(f"✅ Instruction received:\n'{message}'\n\nTeam action: {reply}") 
            except: 
                pass 
 
        except Exception as e: 
            broadcast_log("System", "ERROR", 
                         f"Failed to process instruction: {str(e)[:100]}") 
 
    threading.Thread(target=process_instruction, daemon=True).start() 
 
    return jsonify({ 
        "success": True, 
        "message": "Instruction received — your AI team is processing it" 
    }) 

@api_bp.route("/test/telegram", methods=["POST"]) 
@login_required 
def test_telegram(): 
    try: 
        from distribution.telegram_bot import send_message 
        send_message( 
            "🧪 <b>Test Message from RF Agent Dashboard</b>\n" 
            "If you see this — Telegram is working perfectly! ✅" 
        ) 
        return jsonify({"success": True, 
                        "message": "Test message sent to your Telegram"}) 
    except Exception as e: 
        return jsonify({"success": False, "message": str(e)}) 
 
@api_bp.route("/test/post_preview", methods=["POST"]) 
@login_required 
def test_post_preview(): 
    try: 
        from distribution.telegram_bot import send_post_preview 
        send_post_preview( 
            post_id        = 999, 
            image_path     = None, 
            caption        = "Test caption — Baarish mein bhi delivery dete ho? 🏍️ EliteShield Rain Set protects you completely. Order karo abhi! relaxfashionwear.in", 
            director_score = 9.2, 
            ad_ready       = True, 
            scheduled_time = "Tonight 8:30 PM" 
        ) 
        return jsonify({"success": True, 
                        "message": "Post preview sent to your Telegram — check your phone!"}) 
    except Exception as e: 
        return jsonify({"success": False, "message": str(e)}) 

# ── TEST ROUTES ─────────────────────────────────────── 
@api_bp.route("/test/strategist") 
@login_required 
def test_strategist(): 
    from ai_team.strategist import Strategist 
    s     = Strategist() 
    brief = s.morning_brief() 
    return jsonify(brief) 

@api_bp.route("/test/copywriter") 
@login_required 
def test_copywriter(): 
    from ai_team.strategist import Strategist 
    from ai_team.copywriter import Copywriter 
    s       = Strategist() 
    brief   = s.morning_brief() 
    c       = Copywriter() 
    caption = c.write_caption(brief) 
    return jsonify({"caption": caption}) 

@api_bp.route("/test/full_pipeline") 
@login_required 
def test_full_pipeline(): 
    from ai_team.strategist import Strategist 
    from ai_team.copywriter import Copywriter 
    from ai_team.director   import Director 
    s       = Strategist() 
    brief   = s.morning_brief() 
    c       = Copywriter() 
    caption = c.write_caption(brief) 
    d       = Director() 
    review  = d.review_content(caption, "dark cinematic template", brief) 
    approved = d.approve_or_reject(review) 
    return jsonify({ 
        "brief":    brief, 
        "caption":  caption, 
        "review":   review, 
        "approved": approved 
    }) 

@api_bp.route("/test/socket", methods=["POST"]) 
@login_required 
def test_socket(): 
    from dashboard.socketio_events import broadcast_log, broadcast_agent_status 
    broadcast_log("System", "SOCKET TEST", "Socket is working! This message was sent via SocketIO") 
    broadcast_log("Strategist", "WORKING", "Strategist is alive and thinking...") 
    broadcast_log("Copywriter", "WORKING", "Copywriter is writing your caption...") 
    broadcast_log("Director", "REVIEWING", "Director is reviewing content...") 
    broadcast_agent_status("Strategist", "working", "Testing socket connection") 
    broadcast_agent_status("Copywriter", "working", "Testing socket connection") 
    broadcast_agent_status("Director",   "working", "Testing socket connection") 
    return jsonify({"success": True, "message": "Test logs sent — check logs page!"}) 

# ── EDITOR API ENDPOINTS ──────────────────────────────────────────── 
 
@api_bp.route("/editor/save_post", methods=["POST"]) 
def editor_save_post(): 
    """ 
    Saves an image from the editor directly into the Post pipeline. 
    Receives: multipart form with image blob + post metadata. 
    """ 
    try: 
        from data.database import db, Post 
        from datetime import datetime 
        import config 
 
        # Get image file 
        if 'image' not in request.files: 
            return jsonify({"success": False, "message": "No image provided"}) 
 
        image_file = request.files['image'] 
        product    = request.form.get('product', 'RF Product') 
        price      = request.form.get('price', '') 
        template   = request.form.get('template', 'dark_cinematic') 
        caption    = request.form.get('caption', '') 
 
        # Save image to generated folder 
        os.makedirs(config.GENERATED_DIR, exist_ok=True) 
        timestamp  = int(__import__('time').time()) 
        filename   = f"editor_post_{timestamp}.png" 
        image_path = os.path.join(config.GENERATED_DIR, filename) 
        image_file.save(image_path) 
 
        # Create Post record 
        post = Post( 
            product_name   = product, 
            category       = "Editor", 
            caption        = caption, 
            image_path     = image_path, 
            director_score = 0.0, 
            hook_score     = 0.0, 
            visual_score   = 0.0, 
            caption_score  = 0.0, 
            strategy_score = 0.0, 
            brand_score    = 0.0, 
            conversion_score = 0.0, 
            director_note  = "Created in Post Editor — awaiting Director review", 
            ad_ready       = False, 
            ad_budget      = "", 
            status         = "pending", 
            post_type      = "static", 
            scheduled_time = datetime.utcnow(), 
        ) 
        db.session.add(post) 
        db.session.commit() 
 
        # Broadcast to logs 
        from dashboard.socketio_events import broadcast_log 
        broadcast_log("Designer", "EDITOR POST SAVED", 
            f"📸 Post #{post.id} created in editor — Product: {product} | " 
            f"Go to Pipeline to review and approve" 
        ) 
 
        # Run Director review in background 
        import threading 
        def run_director_review(): 
            try: 
                from ai_team.director import Director 
                from ai_team.strategist import Strategist 
                from dashboard.app import get_app 
                app = get_app() 
                with app.app_context(): 
                    brief = { 
                        "product_name":    product, 
                        "price":           price, 
                        "template":        template, 
                        "creative_angle":  caption[:100] if caption else "Editor post", 
                        "primary_persona": "Urban Indian buyer", 
                        "psychological_trigger": "Quality + Trust", 
                    } 
                    d      = Director() 
                    review = d.review_content(caption or "No caption yet", template, brief) 
                    approved = d.approve_or_reject(review) 
 
                    from data.database import db, Post 
                    p = Post.query.get(post.id) 
                    if p: 
                        p.director_score   = review.get("overall", 0) 
                        p.hook_score       = review.get("hook_score", 0) 
                        p.visual_score     = review.get("visual_score", 0) 
                        p.caption_score    = review.get("caption_score", 0) 
                        p.strategy_score   = review.get("strategy_score", 0) 
                        p.brand_score      = review.get("brand_score", 0) 
                        p.conversion_score = review.get("conversion_score", 0) 
                        p.director_note    = review.get("director_note", "") 
                        p.ad_ready         = review.get("ad_ready", False) 
                        p.status           = "pending" 
                        db.session.commit() 
 
                    broadcast_log("Director", "REVIEWED", 
                        f"Editor Post #{post.id} reviewed — Score: {review.get('overall',0)}/10" 
                    ) 
            except Exception as e: 
                broadcast_log("Director", "ERROR", 
                    f"Director review failed for editor post: {str(e)[:100]}") 
 
        threading.Thread(target=run_director_review, daemon=True).start() 
 
        return jsonify({ 
            "success": True, 
            "post_id": post.id, 
            "message": f"Post saved to pipeline — Director reviewing now" 
        }) 
 
    except Exception as e: 
        return jsonify({"success": False, "message": str(e)[:200]}) 
 
 
@api_bp.route("/editor/generate_caption", methods=["POST"]) 
def editor_generate_caption(): 
    """ 
    Calls Groq via Copywriter agent to generate a caption for editor post. 
    """ 
    try: 
        data     = request.get_json() 
        product  = data.get('product', 'RF Product') 
        price    = data.get('price', '') 
        template = data.get('template', 'dark_cinematic') 
 
        brief = { 
            "product_name":          product, 
            "price":                 price, 
            "template":              template, 
            "creative_angle":        f"Why {product} is essential for Indian monsoon", 
            "caption_tone":          "Bold, urgent, Hinglish", 
            "psychological_trigger": "Pain + Identity", 
            "primary_persona":       "Urban Indian — biker, delivery partner, professional", 
        } 
 
        from ai_team.copywriter import Copywriter 
        import threading 
 
        caption_holder = {"caption": ""} 
 
        def generate(): 
            c = Copywriter() 
            caption_holder["caption"] = c.write_caption(brief) or "" 
 
        t = threading.Thread(target=generate) 
        t.start() 
        t.join(timeout=30)  # 30 second timeout 
 
        if caption_holder["caption"]: 
            return jsonify({"success": True, "caption": caption_holder["caption"]}) 
        else: 
            return jsonify({"success": False, "message": "Caption generation timed out"}) 
 
    except Exception as e: 
        return jsonify({"success": False, "message": str(e)[:200]})