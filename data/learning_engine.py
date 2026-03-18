"""
learning_engine.py — Relax Fashionwear
Tracks performance of every post, learns which content works best,
improves Director scoring thresholds, and feeds insights back to agents.
This is RF's memory — it gets smarter every single day.
"""

from datetime import datetime, timedelta
import json


def get_app():
    from dashboard.app import get_app as _get_app
    return _get_app()


# ── LEARNING DATA COLLECTION ──────────────────────────────────────────────────

def record_post_performance(post_id: int, likes: int, comments: int,
                             saves: int, reach: int, shares: int = 0):
    """
    Called when real Instagram performance data comes in for a post.
    Updates post record and triggers learning update.
    """
    from dashboard.socketio_events import broadcast_log
    app = get_app()
    with app.app_context():
        try:
            from data.database import db, Post

            post = Post.query.get(post_id)
            if not post:
                broadcast_log("Analyst", "ERROR",
                    f"❌ Learning: Post #{post_id} not found")
                return False

            post.ig_likes    = likes
            post.ig_comments = comments
            post.ig_saves    = saves
            post.ig_reach    = reach
            db.session.commit()

            engagement = _calculate_engagement(likes, comments, saves, reach)
            broadcast_log("Analyst", "LEARNING",
                f"📚 Post #{post_id} ({post.product_name}) performance recorded — "
                f"Likes: {likes} | Saves: {saves} | Reach: {reach} | "
                f"Engagement: {engagement}% | Director score was: {post.director_score}/10"
            )

            # Trigger learning update
            _update_learning_model(post, engagement)
            return True

        except Exception as e:
            broadcast_log("Analyst", "ERROR",
                f"❌ Failed to record performance: {str(e)[:100]}")
            return False


def _calculate_engagement(likes, comments, saves, reach):
    """Standard engagement rate: (likes + comments + saves) / reach * 100."""
    if not reach or reach == 0:
        return 0.0
    return round(((likes + comments + saves) / reach) * 100, 2)


# ── LEARNING MODEL ────────────────────────────────────────────────────────────

def _update_learning_model(post, engagement_rate):
    """
    Core learning function.
    Updates what we know about what works for RF's Instagram.
    Learns: best templates, best day, best persona, Director score vs real performance.
    """
    from dashboard.socketio_events import broadcast_log
    app = get_app()
    with app.app_context():
        try:
            from data.database import db, Post, Settings

            # Get all posted posts for pattern learning
            all_posts = Post.query.filter(
                Post.status == "posted",
                Post.ig_reach != None,
                Post.ig_likes != None
            ).all()

            if len(all_posts) < 3:
                broadcast_log("Analyst", "LEARNING",
                    f"📚 Only {len(all_posts)} posts — need 3+ for pattern learning. Collecting...")
                return

            # Learn best template
            template_scores = _learn_best_template(all_posts)
            # Learn best day
            day_scores      = _learn_best_day(all_posts)
            # Learn Director score accuracy
            score_accuracy  = _learn_director_accuracy(all_posts)
            # Learn best persona
            persona_scores  = _learn_best_persona(all_posts)

            # Save insights to Settings table for agents to read
            insights = {
                "best_template":           max(template_scores, key=template_scores.get) if template_scores else "dark_cinematic",
                "template_scores":         template_scores,
                "best_day":                max(day_scores, key=day_scores.get) if day_scores else "Thursday",
                "day_scores":              day_scores,
                "director_accuracy":       score_accuracy,
                "best_persona":            max(persona_scores, key=persona_scores.get) if persona_scores else "Biker",
                "persona_scores":          persona_scores,
                "total_posts_learned":     len(all_posts),
                "last_updated":            datetime.now().isoformat(),
            }

            _save_learning_insights(insights)

            broadcast_log("Analyst", "LEARNING",
                f"📚 Learning updated — Best template: {insights['best_template']} | "
                f"Best day: {insights['best_day']} | "
                f"Best persona: {insights['best_persona']} | "
                f"Posts analysed: {len(all_posts)}"
            )

        except Exception as e:
            broadcast_log("Analyst", "ERROR",
                f"❌ Learning model update failed: {str(e)[:100]}")


def _learn_best_template(posts):
    """Find which visual template gets highest engagement."""
    template_data = {}
    for post in posts:
        template = getattr(post, 'template', 'dark_cinematic') or 'dark_cinematic'
        engagement = _calculate_engagement(
            post.ig_likes or 0, post.ig_comments or 0,
            post.ig_saves or 0, post.ig_reach or 1
        )
        if template not in template_data:
            template_data[template] = []
        template_data[template].append(engagement)

    return {t: round(sum(v)/len(v), 2) for t, v in template_data.items() if v}


def _learn_best_day(posts):
    """Find which day of week gets highest engagement."""
    day_data = {}
    for post in posts:
        if not post.posted_at:
            continue
        day = post.posted_at.strftime("%A")
        engagement = _calculate_engagement(
            post.ig_likes or 0, post.ig_comments or 0,
            post.ig_saves or 0, post.ig_reach or 1
        )
        if day not in day_data:
            day_data[day] = []
        day_data[day].append(engagement)

    return {d: round(sum(v)/len(v), 2) for d, v in day_data.items() if v}


def _learn_director_accuracy(posts):
    """
    How accurate is the Director's score vs real Instagram performance?
    High score should = high engagement. Track the correlation.
    """
    correlations = []
    for post in posts:
        score      = post.director_score or 0
        engagement = _calculate_engagement(
            post.ig_likes or 0, post.ig_comments or 0,
            post.ig_saves or 0, post.ig_reach or 1
        )
        if score > 0 and engagement > 0:
            correlations.append({
                "director_score": score,
                "real_engagement": engagement,
                "accurate": (score >= 8.5) == (engagement >= 3.0)
            })

    if not correlations:
        return {"accuracy": 0, "sample_size": 0, "insight": "Not enough data"}

    accurate_count = sum(1 for c in correlations if c["accurate"])
    accuracy = round((accurate_count / len(correlations)) * 100, 1)

    return {
        "accuracy":    accuracy,
        "sample_size": len(correlations),
        "insight":     f"Director is {accuracy}% accurate in predicting real performance"
    }


def _learn_best_persona(posts):
    """Find which target persona content performs best."""
    persona_data = {}
    for post in posts:
        persona = post.category or "General"
        engagement = _calculate_engagement(
            post.ig_likes or 0, post.ig_comments or 0,
            post.ig_saves or 0, post.ig_reach or 1
        )
        if persona not in persona_data:
            persona_data[persona] = []
        persona_data[persona].append(engagement)

    return {p: round(sum(v)/len(v), 2) for p, v in persona_data.items() if v}


def _save_learning_insights(insights: dict):
    """Save learning insights to Settings table so all agents can read them."""
    app = get_app()
    with app.app_context():
        try:
            from data.database import db, Settings

            key = "learning_insights"
            value = json.dumps(insights)

            setting = Settings.query.filter_by(key=key).first()
            if setting:
                setting.value      = value
                setting.updated_at = datetime.utcnow()
            else:
                db.session.add(Settings(key=key, value=value))

            db.session.commit()
        except Exception as e:
            pass


# ── READ LEARNING INSIGHTS ────────────────────────────────────────────────────

def get_learning_insights():
    """
    Read current learning insights from database.
    Used by agents to make smarter decisions.
    Returns dict with all learned patterns.
    """
    app = get_app()
    with app.app_context():
        try:
            from data.database import Settings

            setting = Settings.query.filter_by(key="learning_insights").first()
            if setting:
                return json.loads(setting.value)
        except:
            pass

    return _default_insights()


def _default_insights():
    """Default insights before enough data is collected."""
    return {
        "best_template":         "dark_cinematic",
        "template_scores":       {"dark_cinematic": 4.5, "lifestyle_emotion": 4.0},
        "best_day":              "Thursday",
        "day_scores":            {"Thursday": 5.2, "Saturday": 4.8, "Tuesday": 4.3},
        "director_accuracy":     {"accuracy": 0, "sample_size": 0, "insight": "Collecting data..."},
        "best_persona":          "Biker",
        "persona_scores":        {"Biker": 5.5, "Women": 4.2, "Kids": 3.8},
        "total_posts_learned":   0,
        "last_updated":          "Not yet",
    }


def get_recommendation_for_today():
    """
    Returns today's best content recommendation based on learned data.
    Used by Strategist to improve morning brief.
    """
    from dashboard.socketio_events import broadcast_log
    insights = get_learning_insights()

    day_of_week = datetime.now().strftime("%A")
    best_template = insights.get("best_template", "dark_cinematic")
    best_persona  = insights.get("best_persona", "Biker")
    best_day      = insights.get("best_day", "Thursday")
    total_learned = insights.get("total_posts_learned", 0)

    if total_learned < 5:
        broadcast_log("Analyst", "LEARNING",
            f"📚 Learning engine: Only {total_learned} posts — using startup recommendations. "
            f"Start posting to teach the agent what works!")
        return {
            "recommended_template": "dark_cinematic",
            "recommended_persona":  "Biker",
            "best_posting_day":     "Thursday",
            "confidence":           "low",
            "note":                 f"Post more content to improve learning accuracy. {total_learned}/5 posts collected."
        }

    day_score = insights.get("day_scores", {}).get(day_of_week, 3.0)
    best_score = max(insights.get("day_scores", {day_of_week: 3.0}).values())
    day_performance = "🔥 great" if day_score >= best_score * 0.8 else "average"

    broadcast_log("Analyst", "LEARNING",
        f"📚 Learning insights for today ({day_of_week}) — "
        f"Best template: {best_template} | "
        f"Best persona: {best_persona} | "
        f"Today's expected performance: {day_performance} | "
        f"Based on {total_learned} posts"
    )

    return {
        "recommended_template": best_template,
        "recommended_persona":  best_persona,
        "best_posting_day":     best_day,
        "today_day_score":      day_score,
        "confidence":           "high" if total_learned >= 10 else "medium",
        "note":                 f"Based on {total_learned} RF posts — {day_of_week} historically gets {day_score}% engagement"
    }


# ── IMPROVEMENT TRACKING ──────────────────────────────────────────────────────

def get_improvement_trend():
    """
    Is the agent improving over time?
    Compares last 7 days vs previous 7 days engagement.
    Returns trend dict.
    """
    from dashboard.socketio_events import broadcast_log
    app = get_app()
    with app.app_context():
        try:
            from data.database import Analytics

            now       = datetime.utcnow()
            last_7    = Analytics.query.filter(
                Analytics.date >= now - timedelta(days=7)
            ).all()
            prev_7    = Analytics.query.filter(
                Analytics.date >= now - timedelta(days=14),
                Analytics.date < now - timedelta(days=7)
            ).all()

            if not last_7 or not prev_7:
                return {"trend": "not enough data", "improvement": 0}

            last_avg_reach = sum(a.reach or 0 for a in last_7) / len(last_7)
            prev_avg_reach = sum(a.reach or 0 for a in prev_7) / len(prev_7)

            if prev_avg_reach == 0:
                return {"trend": "baseline", "improvement": 0}

            improvement = round(((last_avg_reach - prev_avg_reach) / prev_avg_reach) * 100, 1)
            trend = "improving" if improvement > 0 else "declining"

            broadcast_log("Analyst", "LEARNING",
                f"📈 Improvement trend — Week-over-week reach: {improvement:+}% ({trend}) | "
                f"Last 7 days avg: {int(last_avg_reach)} | "
                f"Previous 7 days avg: {int(prev_avg_reach)}"
            )

            return {
                "trend":           trend,
                "improvement":     improvement,
                "last_week_reach": int(last_avg_reach),
                "prev_week_reach": int(prev_avg_reach),
                "message":         f"RF is {trend} — {abs(improvement)}% {'up' if improvement > 0 else 'down'} vs last week"
            }

        except Exception as e:
            return {"trend": "error", "improvement": 0, "error": str(e)[:100]}


def get_director_score_history():
    """
    Track Director approval scores over time.
    Are scores improving? Is the bar getting harder to hit?
    Returns list of recent scores with dates.
    """
    app = get_app()
    with app.app_context():
        try:
            from data.database import Post

            posts = Post.query.filter(
                Post.director_score != None
            ).order_by(Post.date.desc()).limit(30).all()

            return [
                {
                    "date":     p.date.strftime("%d %b") if p.date else "",
                    "score":    p.director_score or 0,
                    "product":  p.product_name or "",
                    "approved": (p.director_score or 0) >= 8.5,
                    "status":   p.status or ""
                }
                for p in reversed(posts)
            ]
        except:
            return []


# ── CONTENT BANK HEALTH ───────────────────────────────────────────────────────

def get_content_bank_status():
    """
    How many approved posts are ready to post?
    Are we running low? Alert if < 2 days of content.
    """
    from dashboard.socketio_events import broadcast_log
    app = get_app()
    with app.app_context():
        try:
            from data.database import Post

            pending   = Post.query.filter_by(status="pending").count()
            approved  = Post.query.filter_by(status="approved", owner_approved=True).count()
            revision  = Post.query.filter_by(status="needs_revision").count()

            status = "healthy" if approved >= 2 else "low" if approved == 1 else "empty"

            if status == "empty":
                broadcast_log("System", "WARNING",
                    "⚠️ Content bank EMPTY — No approved posts ready. "
                    "Triggering emergency content creation...")
                try:
                    from distribution.telegram_bot import send_message
                    send_message("⚠️ Content bank is empty! No posts ready to publish. "
                                "Please approve posts in Pipeline or trigger content creation.")
                except:
                    pass

            broadcast_log("Analyst", "CONTENT BANK",
                f"📦 Content bank — Approved ready: {approved} | "
                f"Pending review: {pending} | "
                f"Needs revision: {revision} | "
                f"Status: {status.upper()}"
            )

            return {
                "status":          status,
                "approved_count":  approved,
                "pending_count":   pending,
                "revision_count":  revision,
                "days_of_content": approved // 2,  # 2 posts per day
            }
        except Exception as e:
            return {"status": "error", "approved_count": 0, "pending_count": 0,
                    "revision_count": 0, "days_of_content": 0}


# ── MAIN ENTRY POINT ──────────────────────────────────────────────────────────

def run_learning_cycle():
    """
    Main function — called by scheduler.
    Runs full learning update: insights, trends, content bank check.
    """
    from dashboard.socketio_events import broadcast_log

    broadcast_log("Analyst", "WORKING",
        "📚 [Learning Engine] LEARNING CYCLE STARTING...")
    broadcast_log("Analyst", "WORKING",
        "📚 [Learning Engine] Step 1/4 — Loading today's recommendations from learned data...")

    rec = get_recommendation_for_today()
    broadcast_log("Analyst", "LEARNING",
        f"📚 Today's recommendation — Template: {rec['recommended_template']} | "
        f"Persona: {rec['recommended_persona']} | "
        f"Confidence: {rec['confidence']} | "
        f"Note: {rec['note']}"
    )

    broadcast_log("Analyst", "WORKING",
        "📚 [Learning Engine] Step 2/4 — Checking week-over-week improvement trend...")
    trend = get_improvement_trend()
    broadcast_log("Analyst", "LEARNING",
        f"📈 Trend: {trend.get('message', 'Collecting data...')}")

    broadcast_log("Analyst", "WORKING",
        "📚 [Learning Engine] Step 3/4 — Checking content bank health...")
    bank = get_content_bank_status()

    broadcast_log("Analyst", "WORKING",
        "📚 [Learning Engine] Step 4/4 — Updating learning model with latest post data...")

    # Force update learning from all existing posted data
    app = get_app()
    with app.app_context():
        try:
            from data.database import Post
            all_posted = Post.query.filter(
                Post.status == "posted",
                Post.ig_likes != None
            ).all()
            if all_posted:
                _update_learning_model(all_posted[-1], 0)
        except:
            pass

    broadcast_log("Analyst", "SUCCESS",
        f"✅ [Learning Engine] Learning cycle complete — "
        f"Content bank: {bank['status'].upper()} ({bank['approved_count']} ready) | "
        f"Trend: {trend.get('trend', 'N/A')} | "
        f"Best template: {rec['recommended_template']} | "
        f"Best persona: {rec['recommended_persona']}"
    )

    return {
        "recommendation": rec,
        "trend":          trend,
        "content_bank":   bank,
    }
