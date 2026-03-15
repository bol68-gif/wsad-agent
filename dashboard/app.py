from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os

db        = SQLAlchemy()
login_mgr = LoginManager()
socketio  = SocketIO()
limiter   = Limiter(key_func=get_remote_address)

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    app.config["SECRET_KEY"]          = os.getenv("SECRET_KEY", "dev_secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///../data/rf_agent.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_mgr.init_app(app)
    socketio.init_app(app, async_mode="eventlet", cors_allowed_origins="*")
    limiter.init_app(app)

    login_mgr.login_view = "auth.login_page"

    from dashboard.auth   import auth_bp
    from dashboard.routes import routes_bp
    from dashboard.api    import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(routes_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    with app.app_context():
        db.create_all()

    return app
