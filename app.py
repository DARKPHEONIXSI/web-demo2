"""
app.py — Main Flask application for the On Ice skating blog.
Entry point: python app.py
"""

import math
import os
from datetime import date
from xml.sax.saxutils import escape as xml_escape

from flask import (
    abort,
    Flask,
    Response,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect

from admin_bp import admin_bp
from api import api_bp
from auth import auth_bp, get_sess, is_admin
from config import Config, validate_config
from health_api import health_bp
from models import (
    close_db,
    count_posts,
    ensure_runtime_schema,
    fmt_date,
    get_db,
    get_posts,
    get_settings,
)


def log_analytics(event_type: str, object_id: str = "", user_id: str = ""):
    """Best-effort analytics logging for views/conversions."""
    try:
        db = get_db()
        db.execute(
            "INSERT INTO analytics_events (event_type, object_id, user_id) VALUES (?, ?, ?)",
            (event_type, object_id or "", user_id or None),
        )
        db.commit()
    except Exception:
        pass


csrf = CSRFProtect()
talisman = Talisman()

# Rate limiter for default limits (app-wide)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per minute"],
    storage_uri=Config.RATELIMIT_STORAGE_URL,
)


def create_app():
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(Config)
    validate_config(app.config)

    # ── Security: HTTPS, HSTS, CSP, Secure Cookies ───────────────
    talisman.init_app(
        app,
        force_https=app.config.get("FLASK_ENV") == "production",
        strict_transport_security=True,
        strict_transport_security_max_age=31536000,
        strict_transport_security_include_subdomains=True,
        content_security_policy={
            "default-src": "'self'",
            "script-src": "'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://checkout.razorpay.com https://accounts.google.com https://challenges.cloudflare.com",
            "style-src": "'self' 'unsafe-inline' https://fonts.googleapis.com https://accounts.google.com",
            "font-src": "'self' https://fonts.gstatic.com",
            "img-src": "'self' data: https:",
            "connect-src": "'self' https://api.razorpay.com https://accounts.google.com",
            "frame-src": "https://checkout.razorpay.com https://accounts.google.com https://challenges.cloudflare.com",
        },
        session_cookie_secure=app.config.get("FLASK_ENV") == "production",
        session_cookie_http_only=True,
        session_cookie_samesite="Lax",
    )

    # ── Rate Limiting ─────────────────────────────────────────────
    limiter.init_app(app)

    with app.app_context():
        ensure_runtime_schema()

    # ── CSRF protection ───────────────────────────────────────────
    csrf.init_app(app)

    # ── Register blueprints ───────────────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(admin_bp)

    if "api.razorpay_webhook" in app.view_functions:
        csrf.exempt(app.view_functions["api.razorpay_webhook"])

    # ── Strict limits for abuse-prone endpoints ───────────────────
    endpoint_limits = {
        "auth.login": "5 per minute",
        "auth.register": "5 per minute",
        "auth.google_login": "5 per minute",
        "api.contact": "5 per minute",
        "api.create_razorpay_order": "10 per minute",
        "api.verify_razorpay": "10 per minute",
        "api.create_paytm_order": "10 per minute",
        "api.verify_paytm": "10 per minute",
    }
    for endpoint, limit in endpoint_limits.items():
        if endpoint in app.view_functions:
            limited_view = app.ensure_sync(
                limiter.limit(limit)(app.view_functions[endpoint])
            )
            app.view_functions[endpoint] = limited_view

    # ── Database lifecycle ────────────────────────────────────────
    app.teardown_appcontext(close_db)

    # ── Template globals & filters ────────────────────────────────
    @app.context_processor
    def inject_globals():
        """Make common data available to all templates."""
        return {
            "get_sess": get_sess,
            "is_admin": is_admin,
            "settings": get_settings(),
            "current_year": date.today().year,
            "fmt_date": fmt_date,
        }

    @app.template_filter("fmt_date")
    def fmt_date_filter(d):
        return fmt_date(d)

    # ── Uploaded files ────────────────────────────────────────────
    @app.route("/uploads/<filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    @app.route("/favicon.ico")
    def favicon():
        """Serve a lightweight site icon to avoid browser favicon 404s."""
        return send_from_directory(
            os.path.join(app.root_path, "static", "images"),
            "pro_ice.png",
            mimetype="image/png",
        )

# ── SPA catch-all: serve simar-website index.html for all non-API routes ──
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def spa_catch_all(path):
        """Serve the SPA index.html for all non-API routes.
        This allows the frontend router to handle client-side navigation.
        """
        # Skip API routes - they should be handled by blueprints
        if path.startswith("api/"):
            abort(404)
        # Skip static files
        if path.startswith("static/"):
            abort(404)
        # Skip uploads
        if path.startswith("uploads/"):
            abort(404)
        # Skip favicon
        if path == "favicon.ico":
            abort(404)
        # Skip health check
        if path.startswith("health"):
            abort(404)
        # Skip admin (has its own blueprint)
        if path.startswith("admin"):
            abort(404)
        # Skip auth (has its own blueprint)
        if path.startswith("auth"):
            abort(404)
        
        # Serve the simar-website index.html
        return send_from_directory(
            os.path.join(app.root_path, "static"),
            "index.html"
        )

    # ── Original Flask routes DISABLED — SPA handles all frontend routing ──
    # @app.route("/")
    # def home(): ...
    # @app.route("/post/<post_id>")
    # def post_detail(post_id): ...
    # @app.route("/category/<category>")
    # def category_archive(category): ...
    # @app.route("/tag/<tag>")
    # def tag_archive(tag): ...
    # @app.route("/gallery")
    # def gallery(): ...
    # @app.route("/techniques")
    # def techniques(): ...
    # @app.route("/contact")
    # def contact(): ...
    # @app.route("/about")
    # def about(): ...
    # @app.route("/profile")
    # def profile(): ...
    # @app.route("/shop")
    # def shop(): ...
    # @app.route("/shop/category/<category>")
    # def shop_category(category): ...
    # @app.route("/shop/<product_id>")
    # def product(product_id): ...
    # @app.route("/checkout")
    # def checkout(): ...
    # @app.route("/order-success", methods=["GET", "POST"])
    # def order_success(): ...
    # @app.route("/order/<order_token>")
    # def order_tracking(order_token): ...
    # @app.route("/invoice/<order_token>")
    # def invoice(order_token): ...
    # @app.route("/returns/<order_token>")
    # def returns(order_token): ...
    # @app.route("/payment-failed")
    # def payment_failed(): ...
    # @app.route("/privacy")
    # def privacy(): ...
    # @app.route("/terms")
    # def terms(): ...
    # @app.route("/shipping-returns")
    # def shipping_returns(): ...
    # @app.route("/refund-policy")
    # def refund_policy(): ...
    # @app.route("/robots.txt")
    # def robots(): ...
    # @app.route("/sitemap.xml")
    # def sitemap(): ...
    # @app.route("/feed.xml")
    # def rss_feed(): ...
    # @app.route("/rules")
    # def rules(): ...
    # @app.route("/page/<page_id>")
    # def custom_page(page_id): ...
    #
    # All frontend routes now served by SPA catch-all above
    # Data accessed via /api/* endpoints

    # ── Error handlers ────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith("/api/"):
            return jsonify({"ok": False, "msg": "API endpoint not found", "code": "NOT_FOUND"}), 404
        return send_from_directory(os.path.join(app.root_path, "static"), "index.html"), 404

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return (
            jsonify(
                {
                    "ok": False,
                    "msg": "Rate limit exceeded. Please slow down.",
                    "code": "RATE_LIMITED",
                }
            ),
            429,
        )

    return app


if __name__ == "__main__":
    local_app = create_app()
    local_app.run(
        debug=os.getenv("FLASK_DEBUG") == "1",
        host=os.getenv("FLASK_RUN_HOST", "127.0.0.1"),
        port=5000,
    )
