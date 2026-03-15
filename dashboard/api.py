from flask import Blueprint, jsonify, request
from flask_login import login_required
from data.database import db, Post, Log, Analytics, WeatherAlert, Notification, OwnerInput
from datetime import datetime
import config

api_bp = Blueprint("api", __name__)

@api_bp.route("/status")
@login_required
def status():
    return jsonify({
        "status": "RF Agent running",
        "version": "1.0",
        "last_action": "System startup",
        "next_job": "Weather check at 09:00",
        "gemini_calls_today": 0
    })

@api_bp.route("/logs")
@login_required
def get_logs():
    logs = Log.query.order_by(Log.timestamp.desc()).limit(50).all()
    return jsonify([log.to_dict() for log in logs])

@api_bp.route("/posts/pending")
@login_required
def pending_posts():
    posts = Post.query.filter(Post.status == "pending").all()
    return jsonify([post.to_dict() for post in posts])

@api_bp.route("/posts/posted")
@login_required
def posted_posts():
    posts = Post.query.filter(Post.status == "posted").all()
    return jsonify([post.to_dict() for post in posts])

@api_bp.route("/calendar/<int:year>/<int:month>")
@login_required
def calendar_data(year, month):
    # Basic filtering by year and month
    posts = Post.query.filter(db.extract('year', Post.date) == year, db.extract('month', Post.date) == month).all()
    return jsonify([post.to_dict() for post in posts])

@api_bp.route("/posts/<int:post_id>/approve", methods=["POST"])
@login_required
def approve_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.status = "approved"
    post.owner_approved = True
    post.approved_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"status": "success", "message": f"Post {post_id} approved"})

@api_bp.route("/posts/<int:post_id>/skip", methods=["POST"])
@login_required
def skip_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.status = "skipped"
    db.session.commit()
    return jsonify({"status": "success", "message": f"Post {post_id} skipped"})

@api_bp.route("/analytics/summary")
@login_required
def analytics_summary():
    # Return mock summary for now
    return jsonify({
        "week_reach": 15200,
        "week_likes": 840,
        "week_saves": 120,
        "best_post": "Monsoon Pro Biker"
    })

@api_bp.route("/weather")
@login_required
def latest_weather():
    alerts = WeatherAlert.query.order_by(WeatherAlert.timestamp.desc()).limit(5).all()
    return jsonify([alert.to_dict() for alert in alerts])

@api_bp.route("/notifications")
@login_required
def get_notifications():
    notifications = Notification.query.filter(Notification.read == False).all()
    return jsonify([n.to_dict() for n in notifications])

@api_bp.route("/owner/input", methods=["POST"])
@login_required
def owner_input():
    data = request.json
    new_input = OwnerInput(
        channel="dashboard",
        message=data.get("message"),
        timestamp=datetime.utcnow()
    )
    db.session.add(new_input)
    db.session.commit()
    return jsonify({"status": "success", "message": "Input received and logged"})

@api_bp.route("/test/strategist")
@login_required
def test_strategist():
    from ai_team.strategist import Strategist
    s = Strategist()
    brief = s.morning_brief()
    return jsonify(brief)

@api_bp.route("/test/copywriter")
@login_required
def test_copywriter():
    from ai_team.copywriter import Copywriter
    from ai_team.strategist import Strategist
    s = Strategist()
    brief = s.morning_brief()
    c = Copywriter()
    caption = c.write_caption(brief)
    return jsonify({"caption": caption})
