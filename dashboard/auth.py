import bcrypt 
from flask import Blueprint, render_template, redirect, url_for, request, flash 
from flask_login import UserMixin, login_user, logout_user, login_required, current_user 
from dashboard.app import login_mgr, limiter 
import config 

auth_bp = Blueprint("auth", __name__) 

class User(UserMixin): 
    def __init__(self, id): 
        self.id = id 

@login_mgr.user_loader 
def load_user(user_id): 
    if user_id == config.DASHBOARD_USERNAME: 
        return User(user_id) 
    return None 

@auth_bp.route("/login", methods=["GET", "POST"]) 
@limiter.limit("5 per 10 minutes") 
def login_page(): 
    if current_user.is_authenticated: 
        return redirect(url_for("routes.home")) 

    if request.method == "POST": 
        username = request.form.get("username", "").strip() 
        password = request.form.get("password", "").strip() 

        username_match = username == config.DASHBOARD_USERNAME 
        password_match = password == config.DASHBOARD_PASSWORD 

        if username_match and password_match: 
            user = User(username) 
            login_user(user, remember=True) 
            # Send Telegram login alert 
            try: 
                from distribution.telegram_bot import send_message 
                ip = request.remote_addr 
                send_message(f"🔐 Dashboard login detected\nIP: {ip}\nTime: {__import__('datetime').datetime.now().strftime('%H:%M %d %b')}") 
            except Exception: 
                pass 
            return redirect(url_for("routes.home")) 
        else: 
            flash("Wrong username or password. Try again.", "error") 

    return render_template("login.html") 

@auth_bp.route("/logout") 
@login_required 
def logout(): 
    logout_user() 
    return redirect(url_for("auth.login_page"))
