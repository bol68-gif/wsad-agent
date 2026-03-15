import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from data.database import db
import config

login_mgr = LoginManager()
socketio = SocketIO()
limiter = Limiter(key_func=get_remote_address)

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # App Config
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + str(config.DATABASE_PATH)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize Extensions
    db.init_app(app)
    login_mgr.init_app(app)
    socketio.init_app(app, async_mode="eventlet", cors_allowed_origins="*")
    limiter.init_app(app)

    login_mgr.login_view = "auth.login_page"

    # Register Blueprints
    from dashboard.auth import auth_bp
    from dashboard.routes import routes_bp
    from dashboard.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(routes_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # Create Database Tables
    with app.app_context():
        db.create_all()

    return app
