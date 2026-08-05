import os

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:
    """Flask application configuration."""

    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", os.getenv("SECRET_KEY"))
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DATABASE_PATH = os.path.join(BASE_DIR, "simar.db")
    DATABASE_URL = os.getenv("DATABASE_URL")
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    UPLOAD_URL = "/uploads/"
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
    MAX_IMAGE_PIXELS = 12_000_000
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
    SESSION_COOKIE_SECURE = FLASK_ENV == "production"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 1800  # 30 min

    # ── Payment Gateways ─────────────────────────────────────
    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
    RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
    RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")
    PAYTM_MERCHANT_ID = os.getenv("PAYTM_MERCHANT_ID")
    PAYTM_MERCHANT_KEY = os.getenv("PAYTM_MERCHANT_KEY")

    # ── Notifications ────────────────────────────────────────
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
    SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "coach@onice.com")
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")

    # ── Google Sign-In ───────────────────────────────────────
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

    # ── Abuse protection ─────────────────────────────────────
    TURNSTILE_SITE_KEY = os.getenv("TURNSTILE_SITE_KEY")
    TURNSTILE_SECRET_KEY = os.getenv("TURNSTILE_SECRET_KEY")

    # ── File Storage ─────────────────────────────────────────
    STORAGE_BACKEND = "local"

    # ── Rate Limiting ────────────────────────────────────────
    RATELIMIT_DEFAULT = "200 per minute"
    RATELIMIT_STORAGE_URL = os.getenv("REDIS_URL", "memory://")

    # ── JWT Configuration ──────────────────────────────────────
    JWT_ALGORITHM = "HS256"
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES = 604800  # 7 days
    JWT_COOKIE_SECURE = FLASK_ENV == "production"
    JWT_COOKIE_HTTPONLY = True
    JWT_COOKIE_SAMESITE = "Lax"

    # Development-only auth shortcut. Never enable in production.
    ALLOW_SIMULATED_GOOGLE_AUTH = (
        os.getenv("ALLOW_SIMULATED_GOOGLE_AUTH") == "1" and FLASK_ENV != "production"
    )


def validate_config(config):
    """Fail fast on unsafe production configuration."""
    if os.getenv("FLASK_ENV") != "production":
        return

    required = ["SECRET_KEY", "JWT_SECRET_KEY", "ADMIN_PASS_HASH"]
    missing = [key for key in required if not config.get(key)]
    if missing:
        raise RuntimeError("Missing production config: " + ", ".join(missing))

    for key in ("SECRET_KEY", "JWT_SECRET_KEY"):
        if len(config[key]) < 32:
            raise RuntimeError(f"{key} must be at least 32 characters in production")

    placeholders = {
        "RAZORPAY_KEY_ID": "rzp_test_YourNewKeyId",
        "RAZORPAY_KEY_SECRET": "YourNewRazorpaySecret",
        "PAYTM_MERCHANT_ID": "YourNewPaytmMerchantId",
        "PAYTM_MERCHANT_KEY": "YourNewPaytmMerchantKey",
        "SENDGRID_API_KEY": "your_sendgrid_key",
        "TWILIO_ACCOUNT_SID": "your_twilio_sid",
        "TWILIO_AUTH_TOKEN": "your_twilio_token",
    }
    unsafe = [key for key, value in placeholders.items() if config.get(key) == value]
    placeholder_markers = ("replace-with-", "replace_", "replace-", "your_")
    unsafe.extend(
        key
        for key, value in config.items()
        if isinstance(value, str)
        and any(marker in value for marker in placeholder_markers)
    )
    unsafe = sorted(set(unsafe))
    if unsafe:
        raise RuntimeError(
            "Replace placeholder production config: " + ", ".join(unsafe)
        )

    if not config.get("SESSION_COOKIE_SECURE") or not config.get("JWT_COOKIE_SECURE"):
        raise RuntimeError("Secure cookies must be enabled in production")

    if not config.get("DATABASE_URL") and os.getenv("ALLOW_SQLITE_PRODUCTION") != "1":
        raise RuntimeError(
            "SQLite production use is blocked. Migrate the database layer before production, "
            "or explicitly set ALLOW_SQLITE_PRODUCTION=1."
        )

    if config.get("RATELIMIT_STORAGE_URL") == "memory://":
        raise RuntimeError("Production requires a shared rate-limit store such as Redis.")

    sensitive_paths = [
        os.path.join(BASE_DIR, ".env"),
        os.path.join(BASE_DIR, "simar.db"),
        os.path.join(BASE_DIR, "database_backup.db"),
        os.path.join(BASE_DIR, "simar_backup2.db"),
    ]
    exposed_paths = [path for path in sensitive_paths if os.path.exists(path)]
    if exposed_paths and os.getenv("ALLOW_APP_ROOT_SECRETS_PRODUCTION") != "1":
        raise RuntimeError(
            "Move secrets and database files outside the production app root: "
            + ", ".join(os.path.basename(path) for path in exposed_paths)
        )
