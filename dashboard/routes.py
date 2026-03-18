from flask import Blueprint, render_template
# DEV MODE — login_required disabled for testing
# from flask_login import login_required
from data.database import Post, Log, Analytics, Competitor, WeatherAlert, Notification, AdCampaign
import config

routes_bp = Blueprint("routes", __name__)

@routes_bp.route("/")
@routes_bp.route("/dashboard")
# @login_required  # DEV MODE — disabled
def home():
    posts_today = Post.query.filter(Post.status == 'posted').count()
    pending_approvals = Post.query.filter(Post.status == 'pending').count()
    return render_template("home.html", posts_today=posts_today, pending_approvals=pending_approvals)

@routes_bp.route("/logs")
# @login_required  # DEV MODE
def logs():
    all_logs = Log.query.order_by(Log.timestamp.desc()).limit(100).all()
    return render_template("logs.html", logs=all_logs)

@routes_bp.route("/calendar")
# @login_required  # DEV MODE
def calendar():
    return render_template("calendar.html")

@routes_bp.route("/pipeline")
# @login_required  # DEV MODE
def pipeline():
    pending_posts = Post.query.filter(Post.status == 'pending').all()
    approved_posts = Post.query.filter(Post.status == 'approved').all()
    posted_posts = Post.query.filter(Post.status == 'posted').all()
    return render_template("pipeline.html", pending=pending_posts, approved=approved_posts, posted=posted_posts)

@routes_bp.route("/products")
# @login_required  # DEV MODE
def products():
    from data.database import Product
    products_list = Product.query.filter_by(active=True).all()
    if not products_list:
        from data.product_catalog import PRODUCTS
        products_list = []
        for i, p in enumerate(PRODUCTS):
            p_copy = p.copy()
            p_copy['id'] = i + 1000
            p_copy['post_count'] = 0
            p_copy['avg_engagement'] = 0.0
            p_copy['primary_image'] = None
            products_list.append(p_copy)
    return render_template("products.html", products=products_list)

@routes_bp.route("/analytics")
# @login_required  # DEV MODE
def analytics():
    summary = Analytics.query.order_by(Analytics.date.desc()).limit(30).all()
    return render_template("analytics.html", summary=summary)

@routes_bp.route("/ads")
# @login_required  # DEV MODE
def ads():
    active_campaigns = AdCampaign.query.filter(AdCampaign.status == 'active').all()
    return render_template("ads.html", campaigns=active_campaigns)

@routes_bp.route("/weather")
# @login_required  # DEV MODE
def weather():
    alerts = WeatherAlert.query.order_by(WeatherAlert.timestamp.desc()).limit(10).all()
    return render_template("weather.html", alerts=alerts, cities=config.BRAND["cities"])

@routes_bp.route("/competitors")
# @login_required  # DEV MODE
def competitors():
    competitors_list = Competitor.query.all()
    return render_template("competitors.html", competitors=competitors_list)

@routes_bp.route("/notifications")
# @login_required  # DEV MODE
def notifications():
    # Limit to last 50 notifications for performance
    all_notifications = Notification.query.order_by(Notification.timestamp.desc()).limit(50).all()
    return render_template("notifications.html", notifications=all_notifications)

@routes_bp.route("/brand")
# @login_required  # DEV MODE
def brand():
    return render_template("brand.html", brand=config.BRAND)

@routes_bp.route("/editor")
# @login_required  # DEV MODE
def editor():
    return render_template("editor.html")

@routes_bp.route("/settings")
# @login_required  # DEV MODE
def settings():
    return render_template("settings.html", agent=config.AGENT)