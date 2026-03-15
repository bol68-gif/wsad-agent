import os
from dotenv import load_dotenv

load_dotenv()

# ── BRAND DNA ─────────────────────────────────────────
BRAND = {
    "name": "Relax Fashionwear",
    "tagline": "Engineered for Indian Monsoon",
    "website": "relaxfashionwear.in",
    "whatsapp": "+91 93213 84257",
    "offer": "Flat Rs89 OFF all prepaid orders",
    "instagram": "@relaxrainwear",
    "location": "Pelhar Factory, Bhiwandi, Mumbai",
    "colors": {
        "primary_teal": "#008080",
        "dark_teal": "#005F5F",
    },
    "fonts": {
        "headline": "Bebas Neue",
        "body": "Montserrat",
    },
    "target_cities": ["Mumbai", "Pune", "Bangalore", "Delhi", "Chennai", "Hyderabad"],
    "voice": "Bold, direct, Hinglish, never corporate, never generic",
    "usps": [
        "Heat sealed seams — zero needle holes",
        "Factory direct — no middleman",
        "3000mm waterproof rating",
        "Anti-sweat breathable design",
        "Reflective strips for night safety",
        "Made in India — Pelhar Factory Bhiwandi",
    ],
    "caption_language": "Hinglish — 60 percent Hindi 40 percent English",
    "caption_tone": "Bold, Urgent, Direct, Indian, Never Corporate",
}

# ── API KEYS ──────────────────────────────────────────
GEMINI_API_KEY        = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN    = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID      = os.getenv("TELEGRAM_CHAT_ID")
INSTAGRAM_TOKEN       = os.getenv("INSTAGRAM_ACCESS_TOKEN")
INSTAGRAM_BUSINESS_ID = os.getenv("INSTAGRAM_BUSINESS_ID")
FACEBOOK_TOKEN        = os.getenv("FACEBOOK_PAGE_TOKEN")
FACEBOOK_PAGE_ID      = os.getenv("FACEBOOK_PAGE_ID")
WEATHER_API_KEY       = os.getenv("WEATHER_API_KEY")
REPLICATE_TOKEN       = os.getenv("REPLICATE_API_TOKEN")
IDEOGRAM_KEY          = os.getenv("IDEOGRAM_API_KEY")
PIXABAY_KEY           = os.getenv("PIXABAY_API_KEY")

# ── DASHBOARD ─────────────────────────────────────────
SECRET_KEY           = os.getenv("SECRET_KEY", "dev_secret_change_this")
DASHBOARD_USERNAME   = os.getenv("DASHBOARD_USERNAME", "admin")
DASHBOARD_PASSWORD   = os.getenv("DASHBOARD_PASSWORD", "changethis123")

# ── AGENT SETTINGS ────────────────────────────────────
AGENT_SETTINGS = {
    "director_min_score":      8.5,
    "max_revision_attempts":   3,
    "max_gemini_calls_per_day":20,
    "gemini_model":            "gemini-1.5-pro",
    "gemini_temperature":      0.8,
    "morning_post_time":       "08:30",
    "evening_post_time":       "20:30",
    "story_time":              "09:00",
    "rain_threshold_mm":       50,
    "auto_post_on_rain":       False,
    "content_bank_days":       3,
    "monsoon_mode_start":      "2025-06-01",
    "improvement_mode":        True,
}

# ── PATHS ─────────────────────────────────────────────
import pathlib
BASE_DIR       = pathlib.Path(__file__).parent
ASSETS_DIR     = BASE_DIR / "assets"
GENERATED_DIR  = ASSETS_DIR / "generated"
PRODUCTS_DIR   = ASSETS_DIR / "products"
DATABASE_PATH  = BASE_DIR / "data" / "rf_agent.db"
