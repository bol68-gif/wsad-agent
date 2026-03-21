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
socketio  = SocketIO() 
limiter   = Limiter(key_func=get_remote_address) 

def create_app(): 
    global _app_instance
    app = Flask(__name__, template_folder="templates", static_folder="static") 
    _app_instance = app

    app.config["SECRET_KEY"]                     = config.SECRET_KEY 
    app.config["SQLALCHEMY_DATABASE_URI"]        = "sqlite:///" + str(config.DATABASE_PATH) 
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False 

    db.init_app(app) 
    login_mgr.init_app(app) 
    socketio.init_app( 
        app, 
        async_mode          = "threading", 
        cors_allowed_origins= "*", 
        logger              = False, 
        engineio_logger     = False,
        allow_upgrades      = False,
        ping_timeout        = 60,
        ping_interval       = 25
    ) 
    limiter.init_app(app) 

    login_mgr.login_view = "auth.login_page" 

    from dashboard.auth   import auth_bp 
    from dashboard.routes import routes_bp 
    from dashboard.api    import api_bp 

    app.register_blueprint(auth_bp) 
    app.register_blueprint(routes_bp) 
    app.register_blueprint(api_bp, url_prefix="/api") 

    from flask import send_from_directory 
 
    # Auto-create placeholder on startup 
    placeholder_dir = os.path.join(app.root_path, "static", "img") 
    placeholder_path = os.path.join(placeholder_dir, "placeholder.png") 
    if not os.path.exists(placeholder_path): 
        os.makedirs(placeholder_dir, exist_ok=True) 
        try: 
            from PIL import Image, ImageDraw 
            img  = Image.new("RGB", (400, 400), (20, 20, 20)) 
            draw = ImageDraw.Draw(img) 
            draw.text((200, 200), "NO IMAGE", fill=(80,80,80), anchor="mm") 
            img.save(placeholder_path) 
        except Exception as e: 
            print(f"Error creating placeholder: {e}")

    @app.route('/static/products/<path:filename>') 
    def serve_product_image(filename): 
        # Handle both absolute paths and relative paths 
        if os.path.isabs(filename): 
            return send_from_directory( 
                os.path.dirname(filename), 
                os.path.basename(filename)) 
        # Remove any accidental "assets/products/" prefix 
        clean = filename.replace('assets/products/', '').replace('assets\\products\\', '') 
        return send_from_directory( 
            os.path.join(os.getcwd(), 'assets', 'products'), clean) 

    @app.route('/generated/<path:filename>') 
    def serve_generated(filename): 
        import os 
        return send_from_directory( 
            os.path.join(os.getcwd(), 'assets', 'generated'), 
            filename 
        ) 

    with app.app_context(): 
        from data.database import (Post, Log, Analytics, Competitor, 
                                   WeatherAlert, Notification, 
                                   OwnerInput, AdCampaign, Settings) 
        db.create_all() 

    return app

# Global app instance for agents to use 
_app_instance = None 

def get_app(): 
    global _app_instance 
    if _app_instance is None: 
        _app_instance = create_app() 
    return _app_instance
