"""
analytics_engine.py — Relax Fashionwear
Collects Instagram performance data, calculates engagement rates,
tracks growth, generates AI insights via Groq.
"""

from datetime import datetime, timedelta
import json


def get_app():
    from dashboard.app import get_app as _get_app
    return _get_app()


# ── CORE COLLECTION ─────────────────────────────────────────────────────────

def collect_instagram_stats():
    """
    Collect real Instagram stats via Graph API.
    Falls back to estimated data if API not connected yet.
    Returns dict with all platform metrics.
    """
    import config
    from dashboard.socketio_events import broadcast_log

    broadcast_log("Analyst", "WORKING", "📊 Collecting Instagram stats via Graph API...")

    # Try real Instagram API first
    if config.INSTAGRAM_TOKEN and config.INSTAGRAM_BUSINESS_ID:
        try:
            import requests
            url = f"https://graph.facebook.com/v18.0/{config.INSTAGRAM_BUSINESS_ID}/insights"
            params = {
                "metric": "reach,impressions,profile_views,follower_count",
                "period": "day",
                "access_token": config.INSTAGRAM_TOKEN
            }
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()

            if "data" in data:
                metrics = {item["name"]: item["values"][-1]["value"] for item in data["data"]}
                broadcast_log("Analyst", "DATA", f"✅ Live Instagram data — Reach: {metrics.get('reach', 0)} | Impressions: {metrics.get('impressions', 0)}")
                return {
                    "source":       "instagram_api",
                    "reach":        metrics.get("reach", 0),
                    "impressions":  metrics.get("impressions", 0),
                    "profile_views":metrics.get("profile_views", 0),
                    "followers":    metrics.get("follower_count", 12100),
                    "likes":        0,
                    "comments":     0,
                    "saves":        0,
                    "clicks":       0,
                }
        except Exception as e:
            broadcast_log("Analyst", "WARNING", f"⚠️ Instagram API error: {str(e)[:100]} — using estimated data")

    # Fallback — calculate from posted posts in DB
    broadcast_log("Analyst", "WORKING", "📊 Instagram API not connected — calculating from post database...")
    return _calculate_from_db()


def _calculate_from_db():
    """Calculate analytics from posts stored in database."""
    app = get_app()
    with app.app_context():
        try:
            from data.database import Post, Analytics

            posts = Post.query.filter_by(status="posted").all()
            today_posts = [p for p in posts if p.posted_at and p.posted_at.date() == datetime.utcnow().date()]

            total_likes    = sum(p.ig_likes    or 0 for p in posts)
            total_comments = sum(p.ig_comments or 0 for p in posts)
            total_saves    = sum(p.ig_saves    or 0 for p in posts)
            total_reach    = sum(p.ig_reach    or 0 for p in posts)

            # Get last known follower count
            last_analytics = Analytics.query.order_by(Analytics.date.desc()).first()
            followers = last_analytics.followers if last_analytics else 12100

            return {
                "source":       "database",
                "reach":        total_reach,
                "impressions":  total_reach * 2,
                "profile_views":total_reach // 4,
                "followers":    followers,
                "likes":        total_likes,
                "comments":     total_comments,
                "saves":        total_saves,
                "clicks":       total_likes // 3,
            }
        except Exception as e:
            return {
                "source":       "fallback",
                "reach":        0, "impressions": 0, "profile_views": 0,
                "followers":    12100, "likes": 0, "comments": 0,
                "saves":        0, "clicks": 0,
            }


# ── SAVE TO DATABASE ─────────────────────────────────────────────────────────

def save_daily_analytics(stats: dict):
    """Save today's analytics snapshot to database."""
    from dashboard.socketio_events import broadcast_log
    app = get_app()
    with app.app_context():
        try:
            from data.database import db, Analytics

            today = datetime.utcnow().date()
            existing = Analytics.query.filter(
                db.func.date(Analytics.date) == today,
                Analytics.platform == "instagram"
            ).first()

            if existing:
                # Update today's record
                existing.reach     = stats.get("reach", 0)
                existing.likes     = stats.get("likes", 0)
                existing.comments  = stats.get("comments", 0)
                existing.saves     = stats.get("saves", 0)
                existing.clicks    = stats.get("clicks", 0)
                existing.followers = stats.get("followers", 12100)
                existing.impressions = stats.get("impressions", 0)
                broadcast_log("Analyst", "DATA", f"📊 Today's analytics updated — Reach: {stats.get('reach',0)} | Likes: {stats.get('likes',0)} | Followers: {stats.get('followers',12100)}")
            else:
                # Create new record
                record = Analytics(
                    date      = datetime.utcnow(),
                    platform  = "instagram",
                    reach     = stats.get("reach", 0),
                    likes     = stats.get("likes", 0),
                    comments  = stats.get("comments", 0),
                    saves     = stats.get("saves", 0),
                    clicks    = stats.get("clicks", 0),
                    followers = stats.get("followers", 12100),
                )
                db.session.add(record)
                broadcast_log("Analyst", "DATA", f"📊 New analytics record created — {today}")

            db.session.commit()
            broadcast_log("Analyst", "SUCCESS", f"✅ Analytics saved — Source: {stats.get('source','unknown')}")
            return True

        except Exception as e:
            broadcast_log("Analyst", "ERROR", f"❌ Failed to save analytics: {str(e)[:150]}")
            return False


# ── PERFORMANCE CALCULATIONS ─────────────────────────────────────────────────

def calculate_engagement_rate(likes, comments, saves, reach):
    """Standard Instagram engagement rate formula."""
    if not reach or reach == 0:
        return 0.0
    total_interactions = likes + comments + saves
    return round((total_interactions / reach) * 100, 2)


def get_week_summary():
    """
    Get last 7 days performance summary.
    Returns dict with totals, averages, best/worst day.
    """
    app = get_app()
    with app.app_context():
        try:
            from data.database import Analytics, Post

            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            analytics = Analytics.query.filter(
                Analytics.date >= seven_days_ago,
                Analytics.platform == "instagram"
            ).order_by(Analytics.date.asc()).all()

            if not analytics:
                return _empty_week_summary()

            total_reach    = sum(a.reach    or 0 for a in analytics)
            total_likes    = sum(a.likes    or 0 for a in analytics)
            total_comments = sum(a.comments or 0 for a in analytics)
            total_saves    = sum(a.saves    or 0 for a in analytics)
            total_clicks   = sum(a.clicks   or 0 for a in analytics)
            days           = len(analytics)

            # Follower growth
            first_followers = analytics[0].followers  or 12100
            last_followers  = analytics[-1].followers or 12100
            follower_growth = last_followers - first_followers

            # Best performing day
            best_day = max(analytics, key=lambda a: (a.likes or 0) + (a.saves or 0))

            # Engagement rate
            avg_engagement = calculate_engagement_rate(
                total_likes / days if days else 0,
                total_comments / days if days else 0,
                total_saves / days if days else 0,
                total_reach / days if days else 1
            )

            # Best post this week
            best_post = Post.query.filter(
                Post.posted_at >= seven_days_ago,
                Post.status == "posted"
            ).order_by(Post.ig_likes.desc()).first()

            return {
                "days":             days,
                "total_reach":      total_reach,
                "total_likes":      total_likes,
                "total_comments":   total_comments,
                "total_saves":      total_saves,
                "total_clicks":     total_clicks,
                "avg_reach_per_day":round(total_reach / days if days else 0),
                "avg_likes_per_day":round(total_likes / days if days else 0),
                "avg_engagement":   avg_engagement,
                "follower_growth":  follower_growth,
                "current_followers":last_followers,
                "best_day":         best_day.date.strftime("%A %d %b") if best_day.date else "N/A",
                "best_post":        best_post.product_name if best_post else "No posts yet",
                "best_post_likes":  best_post.ig_likes if best_post else 0,
                "daily_data": [
                    {
                        "date":     a.date.strftime("%d %b") if a.date else "",
                        "reach":    a.reach    or 0,
                        "likes":    a.likes    or 0,
                        "comments": a.comments or 0,
                        "saves":    a.saves    or 0,
                    }
                    for a in analytics
                ]
            }

        except Exception as e:
            return _empty_week_summary()


def _empty_week_summary():
    return {
        "days": 0, "total_reach": 0, "total_likes": 0,
        "total_comments": 0, "total_saves": 0, "total_clicks": 0,
        "avg_reach_per_day": 0, "avg_likes_per_day": 0,
        "avg_engagement": 0.0, "follower_growth": 0,
        "current_followers": 12100, "best_day": "N/A",
        "best_post": "No data yet", "best_post_likes": 0,
        "daily_data": []
    }


def get_best_performing_content_type():
    """
    Analyse which content type (static/reel/carousel) gets best engagement.
    Returns string with recommendation.
    """
    app = get_app()
    with app.app_context():
        try:
            from data.database import Post

            types = ["static", "reel", "carousel"]
            results = {}
            for t in types:
                posts = Post.query.filter_by(
                    post_type=t, status="posted"
                ).all()
                if posts:
                    avg_likes = sum(p.ig_likes or 0 for p in posts) / len(posts)
                    avg_saves = sum(p.ig_saves or 0 for p in posts) / len(posts)
                    results[t] = avg_likes + avg_saves
                else:
                    results[t] = 0

            if results:
                best = max(results, key=results.get)
                return best
            return "reel"  # default recommendation
        except:
            return "reel"


def get_best_posting_time():
    """
    Find what time of day gets highest engagement from posted posts.
    Returns recommended time as string.
    """
    app = get_app()
    with app.app_context():
        try:
            from data.database import Post

            posts = Post.query.filter(
                Post.status == "posted",
                Post.posted_at != None,
                Post.ig_likes != None
            ).all()

            if not posts:
                return "8:30 PM"

            hour_performance = {}
            for post in posts:
                hour = post.posted_at.hour
                engagement = (post.ig_likes or 0) + (post.ig_saves or 0)
                if hour not in hour_performance:
                    hour_performance[hour] = []
                hour_performance[hour].append(engagement)

            # Average engagement per hour
            hour_avg = {h: sum(v)/len(v) for h, v in hour_performance.items()}
            best_hour = max(hour_avg, key=hour_avg.get)

            period = "AM" if best_hour < 12 else "PM"
            display_hour = best_hour if best_hour <= 12 else best_hour - 12
            return f"{display_hour}:30 {period}"
        except:
            return "8:30 PM"


# ── AI REPORT GENERATION ─────────────────────────────────────────────────────

def generate_ai_weekly_report():
    """
    Uses Groq via Analyst agent to generate a human-readable
    weekly performance report with specific recommendations.
    """
    from dashboard.socketio_events import broadcast_log
    broadcast_log("Analyst", "WORKING", "🤖 Generating AI weekly performance report via Groq...")

    summary = get_week_summary()
    best_type = get_best_performing_content_type()
    best_time = get_best_posting_time()

    broadcast_log("Analyst", "DATA",
        f"📊 Week data loaded — Reach: {summary['total_reach']} | "
        f"Likes: {summary['total_likes']} | "
        f"Engagement: {summary['avg_engagement']}% | "
        f"Follower growth: +{summary['follower_growth']}"
    )

    try:
        from ai_team.analyst import Analyst
        analyst = Analyst()
        report  = analyst.generate_weekly_report()
        broadcast_log("Analyst", "REPORT READY", f"✅ Weekly AI report generated — {len(report)} chars")

        # Save report to database as a notification
        _save_report_notification(report)
        return report

    except Exception as e:
        broadcast_log("Analyst", "ERROR", f"❌ AI report generation failed: {str(e)[:100]}")
        return _fallback_text_report(summary, best_type, best_time)


def _fallback_text_report(summary, best_type, best_time):
    """Generate a basic text report without AI."""
    return f"""
RF WEEKLY PERFORMANCE REPORT
Week of {datetime.now().strftime('%d %b %Y')}

REACH: {summary['total_reach']:,} total | {summary['avg_reach_per_day']:,}/day avg
LIKES: {summary['total_likes']:,} total
ENGAGEMENT RATE: {summary['avg_engagement']}%
FOLLOWER GROWTH: +{summary['follower_growth']} this week ({summary['current_followers']:,} total)

BEST CONTENT TYPE: {best_type.upper()}
BEST POSTING TIME: {best_time}
BEST POST: {summary['best_post']} ({summary['best_post_likes']} likes)

RECOMMENDATION: Focus on {best_type} content posted at {best_time} for maximum reach.
    """.strip()


def _save_report_notification(report_text):
    """Save weekly report as a notification in the dashboard."""
    app = get_app()
    with app.app_context():
        try:
            from data.database import db, Notification
            n = Notification(
                type    = "report",
                title   = f"📊 Weekly AI Report — {datetime.now().strftime('%d %b %Y')}",
                message = report_text[:500] + "..." if len(report_text) > 500 else report_text,
                urgent  = False,
                read    = False
            )
            db.session.add(n)
            db.session.commit()
        except Exception as e:
            pass


# ── MAIN ENTRY POINT ─────────────────────────────────────────────────────────

def run_analytics_collection():
    """
    Main function called by scheduler every 2 hours.
    Collects stats, saves to DB, checks for viral posts.
    """
    from dashboard.socketio_events import broadcast_log

    broadcast_log("Analyst", "WORKING", "📊 [Analyst] ANALYTICS COLLECTION STARTING...")
    broadcast_log("Analyst", "WORKING", "📊 [Analyst] Step 1/4 — Fetching Instagram performance data...")

    stats = collect_instagram_stats()

    broadcast_log("Analyst", "WORKING", "📊 [Analyst] Step 2/4 — Saving data to database...")
    save_daily_analytics(stats)

    broadcast_log("Analyst", "WORKING", "📊 [Analyst] Step 3/4 — Calculating engagement rates and trends...")
    summary = get_week_summary()

    broadcast_log("Analyst", "WORKING", "📊 [Analyst] Step 4/4 — Checking for viral posts (2x avg engagement)...")
    check_viral_posts(summary)

    broadcast_log("Analyst", "SUCCESS",
        f"✅ [Analyst] Analytics complete — "
        f"7-day reach: {summary['total_reach']:,} | "
        f"Likes: {summary['total_likes']:,} | "
        f"Engagement: {summary['avg_engagement']}% | "
        f"Followers: {summary['current_followers']:,} (+{summary['follower_growth']})"
    )

    return summary


def check_viral_posts(summary):
    """Alert Krishna via Telegram if any post hits 2x average engagement."""
    from dashboard.socketio_events import broadcast_log
    app = get_app()
    with app.app_context():
        try:
            from data.database import Post

            avg_likes = summary.get("avg_likes_per_day", 0)
            if avg_likes == 0:
                return

            threshold = avg_likes * 2
            recent_posts = Post.query.filter(
                Post.status == "posted",
                Post.ig_likes >= threshold
            ).all()

            for post in recent_posts:
                broadcast_log("Analyst", "VIRAL ALERT",
                    f"🚀 VIRAL POST DETECTED — '{post.product_name}' got {post.ig_likes} likes "
                    f"(2x avg of {int(avg_likes)}) — Consider boosting as ad!"
                )
                try:
                    from distribution.telegram_bot import send_message
                    send_message(
                        f"🚀 VIRAL POST ALERT!\n"
                        f"Post: {post.product_name}\n"
                        f"Likes: {post.ig_likes} (2x average!)\n"
                        f"Consider boosting this as an ad! 💰"
                    )
                except:
                    pass
        except Exception as e:
            broadcast_log("Analyst", "ERROR", f"❌ Viral check failed: {str(e)[:100]}")
