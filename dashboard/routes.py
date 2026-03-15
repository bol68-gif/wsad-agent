from flask import Blueprint
routes_bp = Blueprint("routes", __name__)

@routes_bp.route("/")
@routes_bp.route("/dashboard")
def home():
    return "Home dashboard — coming Night 1 coding"

@routes_bp.route("/logs")
def logs():
    return "Logs room — coming Night 1 coding"

@routes_bp.route("/calendar")
def calendar():
    return "Calendar — coming Night 1 coding"

@routes_bp.route("/pipeline")
def pipeline():
    return "Pipeline — coming Night 1 coding"

@routes_bp.route("/products")
def products():
    return "Products — coming Night 1 coding"

@routes_bp.route("/analytics")
def analytics():
    return "Analytics — coming Night 1 coding"

@routes_bp.route("/ads")
def ads():
    return "Ads — coming Night 1 coding"

@routes_bp.route("/weather")
def weather():
    return "Weather — coming Night 1 coding"

@routes_bp.route("/competitors")
def competitors():
    return "Competitors — coming Night 1 coding"

@routes_bp.route("/notifications")
def notifications():
    return "Notifications — coming Night 1 coding"

@routes_bp.route("/brand")
def brand():
    return "Brand settings — coming Night 1 coding"

@routes_bp.route("/settings")
def settings():
    return "Agent settings — coming Night 1 coding"
