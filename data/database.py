from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Product(db.Model): 
    __tablename__    = "products" 
    id               = db.Column(db.Integer, primary_key=True) 
    name             = db.Column(db.String(200), nullable=False) 
    category         = db.Column(db.String(100)) 
    price            = db.Column(db.Integer, default=0) 
    stock            = db.Column(db.Integer, default=0) 
    description      = db.Column(db.Text) 
    features         = db.Column(db.Text) 
    target_persona   = db.Column(db.String(300)) 
    pain_points      = db.Column(db.Text) 
    website_url      = db.Column(db.String(500)) 
    priority         = db.Column(db.String(50), default="medium") 
    active           = db.Column(db.Boolean, default=True) 
    primary_image    = db.Column(db.String(500)) 
    all_images       = db.Column(db.Text) 
    post_count       = db.Column(db.Integer, default=0) 
    avg_engagement   = db.Column(db.Float, default=0.0) 
    created_at       = db.Column(db.DateTime, default=datetime.utcnow) 
    scraped_at       = db.Column(db.DateTime) 

    def to_dict(self): 
        return { 
            "id":            self.id, 
            "name":          self.name, 
            "category":      self.category, 
            "price":         self.price, 
            "stock":         self.stock, 
            "description":   self.description, 
            "features":      self.features, 
            "target_persona":self.target_persona, 
            "website_url":   self.website_url, 
            "priority":      self.priority, 
            "active":        self.active, 
            "primary_image": self.primary_image, 
            "all_images":    self.all_images, 
            "post_count":    self.post_count, 
            "avg_engagement":self.avg_engagement, 
        } 

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    product_name = db.Column(db.String(100))
    category = db.Column(db.String(50))
    caption = db.Column(db.Text)
    image_path = db.Column(db.String(255))
    reel_path = db.Column(db.String(255))
    story_path = db.Column(db.String(255))
    template_used = db.Column(db.String(50))
    director_score = db.Column(db.Float)
    hook_score = db.Column(db.Float)
    visual_score = db.Column(db.Float)
    caption_score = db.Column(db.Float)
    strategy_score = db.Column(db.Float)
    brand_score = db.Column(db.Float)
    conversion_score = db.Column(db.Float)
    director_note = db.Column(db.Text)
    owner_approved = db.Column(db.Boolean, default=False)
    approved_at = db.Column(db.DateTime)
    ig_post_id = db.Column(db.String(100))
    ig_reach = db.Column(db.Integer, default=0)
    ig_likes = db.Column(db.Integer, default=0)
    ig_comments = db.Column(db.Integer, default=0)
    ig_saves = db.Column(db.Integer, default=0)
    ig_clicks = db.Column(db.Integer, default=0)
    posted_at = db.Column(db.DateTime)
    ad_ready = db.Column(db.Boolean, default=False)
    ad_budget = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default="pending") # pending, approved, posted, skipped
    post_type = db.Column(db.String(20)) # image, reel, story
    scheduled_time = db.Column(db.DateTime)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Settings(db.Model): 
    __tablename__ = "settings" 
    id         = db.Column(db.Integer, primary_key=True) 
    key        = db.Column(db.String(200), unique=True, nullable=False) 
    value      = db.Column(db.Text) 
    updated_at = db.Column(db.DateTime, default=datetime.utcnow) 

    def to_dict(self): 
        return { 
            "key":   self.key, 
            "value": self.value 
        }

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    agent_name = db.Column(db.String(50))
    log_type = db.Column(db.String(20)) # info, warning, error, success
    content = db.Column(db.Text)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Analytics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=datetime.utcnow().date())
    platform = db.Column(db.String(20)) # instagram, facebook, combined
    reach = db.Column(db.Integer, default=0)
    likes = db.Column(db.Integer, default=0)
    comments = db.Column(db.Integer, default=0)
    saves = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    followers = db.Column(db.Integer, default=0)
    best_post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Competitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    instagram_handle = db.Column(db.String(100))
    brand_name = db.Column(db.String(100))
    followers = db.Column(db.Integer, default=0)
    avg_engagement = db.Column(db.Float, default=0.0)
    content_gaps = db.Column(db.Text)
    last_checked = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class WeatherAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    city = db.Column(db.String(50))
    rain_mm = db.Column(db.Float)
    intensity = db.Column(db.String(20)) # light, moderate, heavy
    post_triggered = db.Column(db.Boolean, default=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    type = db.Column(db.String(20)) # approval, performance, error, weather
    title = db.Column(db.String(100))
    message = db.Column(db.Text)
    page_link = db.Column(db.String(100))
    read = db.Column(db.Boolean, default=False, index=True)
    urgent = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class OwnerInput(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    channel = db.Column(db.String(20)) # telegram, dashboard
    message = db.Column(db.Text)
    action_taken = db.Column(db.String(100))
    result = db.Column(db.Text)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class AdCampaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    platform = db.Column(db.String(20))
    objective = db.Column(db.String(50))
    budget_daily = db.Column(db.Float)
    total_spent = db.Column(db.Float, default=0.0)
    reach = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    ctr = db.Column(db.Float, default=0.0)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default="active") # active, completed, paused

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
