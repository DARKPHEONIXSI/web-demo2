import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Flask application configuration."""

    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", os.getenv("SECRET_KEY"))
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "simar.db")
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
    UPLOAD_URL = "/uploads/"
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}

    # ── Admin credentials ────────────────────────────────────
    # ADMIN_PASS_HASH must be set in .env (generated via werkzeug.security.generate_password_hash)
    ADMIN_USER = os.getenv("ADMIN_USER", "sir")
    ADMIN_PASS_HASH = os.getenv("ADMIN_PASS_HASH")
    if not ADMIN_PASS_HASH:
        raise RuntimeError("ADMIN_PASS_HASH must be set in .env")

    # ── CSRF (Flask-WTF) ─────────────────────────────────────
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 1800  # tokens expire after 30 min
    WTF_CSRF_HEADERS = ["X-CSRFToken"]  # accept token from this header (AJAX)

    # Posts per page
    PER_PAGE = 9

    # ── Security: HTTPS, Secure Cookies ──────────────────────
    SESSION_COOKIE_SECURE = os.getenv("FLASK_ENV") == "production"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 1800  # 30 min

    # ── Payment Gateways ─────────────────────────────────────
    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
    RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
    PAYTM_MERCHANT_ID = os.getenv("PAYTM_MERCHANT_ID")
    PAYTM_MERCHANT_KEY = os.getenv("PAYTM_MERCHANT_KEY")

    # ── Notifications ────────────────────────────────────────
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
    SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "coach@onice.com")
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")

    # ── Rate Limiting ────────────────────────────────────────
    RATELIMIT_DEFAULT = "200 per minute"
    RATELIMIT_STORAGE_URL = "memory://"

    # ── JWT Configuration ──────────────────────────────────────
    JWT_ALGORITHM = "HS256"
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES = 604800  # 7 days
    JWT_COOKIE_SECURE = os.getenv("FLASK_ENV") == "production"
    JWT_COOKIE_HTTPONLY = True
    JWT_COOKIE_SAMESITE = "Lax"
