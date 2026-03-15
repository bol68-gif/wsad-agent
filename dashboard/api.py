from flask import Blueprint, jsonify, request 
from flask_login import login_required 
from data.database import db, Post, Log, Analytics, WeatherAlert, Notification, OwnerInput, Settings 
from datetime import datetime 
import config 

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
        Notification.timestamp.desc()).limit(50).all() 
    return jsonify([n.to_dict() for n in notifications]) 

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
    product.primary_image = save_path 
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
@api_bp.route("/competitors/all") 
@login_required 
def get_competitors(): 
    from data.database import Competitor 
    competitors = Competitor.query.filter_by(active=True).all() 
    if not competitors: 
        # Auto-seed if empty 
        from scheduler import run_competitor_scan 
        import threading 
        threading.Thread(target=run_competitor_scan, daemon=True).start() 
        return jsonify([]) 
    return jsonify([c.to_dict() for c in competitors]) 

@api_bp.route("/competitors/scan", methods=["POST"]) 
@login_required 
def scan_competitors(): 
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
