"""
app.py — Main Flask application for the On Ice skating blog.
Entry point: python app.py
"""

import math
import os
from datetime import date

from flask import (
    Flask,
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
from models import (
    close_db,
    count_posts,
    fmt_date,
    get_db,
    get_posts,
    get_settings,
    ensure_runtime_schema,
)

csrf = CSRFProtect()
talisman = Talisman()

# Rate limiter for default limits (app-wide)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per minute"],
    storage_uri="memory://",
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
            "script-src": "'self' 'unsafe-inline' https://cdn.jsdelivr.net https://checkout.razorpay.com https://accounts.google.com https://challenges.cloudflare.com",
            "style-src": "'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src": "'self' https://fonts.gstatic.com",
            "img-src": "'self' data: https:",
            "connect-src": "'self' https://api.razorpay.com",
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
    app.register_blueprint(admin_bp)

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
            app.view_functions[endpoint] = limiter.limit(limit)(app.view_functions[endpoint])

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

    # ── Public routes ─────────────────────────────────────────────

    @app.route("/")
    def home():
        """Home page with blog feed, search, and pagination."""
        db = get_db()
        get_settings()
        per_page = app.config["PER_PAGE"]
        page_num = max(1, int(request.args.get("page", 1)))
        q = (request.args.get("q") or "").strip()
        offset = (page_num - 1) * per_page
        published_only = not is_admin()

        if q:
            posts = get_posts(
                published_only=published_only, search=q, limit=per_page, offset=offset
            )
            total_filtered = count_posts(published_only=published_only, search=q)
        else:
            posts = get_posts(
                published_only=published_only, limit=per_page, offset=offset
            )
            total_filtered = count_posts(published_only=published_only)

        total_published = db.execute(
            "SELECT COUNT(*) FROM posts WHERE status='published'"
        ).fetchone()[0]
        total_all = db.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
        total_pages = math.ceil(total_filtered / per_page) if per_page else 1
        tech_count = db.execute("SELECT COUNT(*) FROM techniques").fetchone()[0]

        return render_template(
            "index.html",
            posts=posts,
            q=q,
            page_num=page_num,
            total=total_published,
            total_all=total_all,
            total_filtered=total_filtered,
            total_pages=total_pages,
            tech_count=tech_count,
            per_page=per_page,
        )

    @app.route("/post/<post_id>")
    def post_detail(post_id):
        """Single post view."""
        db = get_db()
        post = db.execute(
            "SELECT * FROM posts WHERE id = ? LIMIT 1", (post_id,)
        ).fetchone()

        # Non-admins can't see drafts
        if post and post["status"] == "draft" and not is_admin():
            return redirect(url_for("home"))

        # Related posts
        related = []
        if post:
            status_clause = "" if is_admin() else "AND status='published'"
            related = db.execute(
                f"SELECT id, title, post_date, read_time FROM posts WHERE id != ? {status_clause} ORDER BY post_date DESC LIMIT 3",
                (post_id,),
            ).fetchall()

        return render_template("post.html", post=post, related=related)

    @app.route("/gallery")
    def gallery():
        """Gallery page with filtering and lightbox."""
        db = get_db()
        try:
            rows = db.execute(
                "SELECT * FROM gallery_items ORDER BY sort_order ASC"
            ).fetchall()
            items = [dict(row) for row in rows]
        except Exception:
            items = []

        tags = sorted({item["tag"] for item in items})
        return render_template("gallery.html", gallery_items=items, tags=tags)

    @app.route("/techniques")
    def techniques():
        """Technique guides page."""
        db = get_db()
        techs = db.execute(
            "SELECT * FROM techniques ORDER BY sort_order ASC"
        ).fetchall()
        return render_template("techniques.html", techs=techs)

    @app.route("/contact")
    def contact():
        """Contact form page."""
        return render_template("contact.html")

    @app.route("/about")
    def about():
        """About page."""
        return render_template("about.html")

    @app.route("/profile")
    def profile():
        """User profile page."""
        return render_template("profile.html")

    @app.route("/shop")
    def shop():
        """Dedicated shop page for coach's skates."""
        db = get_db()
        products = db.execute(
            "SELECT * FROM products ORDER BY created_at DESC"
        ).fetchall()
        prod_data = []
        for p in products:
            img = db.execute(
                "SELECT image_url FROM product_images WHERE product_id=? ORDER BY sort_order ASC LIMIT 1",
                (p["id"],),
            ).fetchone()
            p_dict = dict(p)
            p_dict["image"] = (
                img["image_url"]
                if img
                else url_for("static", filename="images/pro_ice.png")
            )
            prod_data.append(p_dict)
        return render_template("shop.html", products=prod_data)

    @app.route("/shop/<product_id>")
    def product(product_id):
        """Single product details with variants."""
        db = get_db()
        product = db.execute(
            "SELECT * FROM products WHERE id=?", (product_id,)
        ).fetchone()
        if not product:
            return redirect(url_for("shop"))
        variants = db.execute(
            "SELECT * FROM product_variants WHERE product_id=?", (product_id,)
        ).fetchall()
        images = db.execute(
            "SELECT * FROM product_images WHERE product_id=? ORDER BY sort_order",
            (product_id,),
        ).fetchall()
        variants_list = [dict(v) for v in variants]
        return render_template(
            "product.html", product=product, variants=variants_list, images=images
        )

    @app.route("/checkout")
    def checkout():
        """Simulated payment gateway."""
        return render_template("checkout.html")

    @app.route("/order-success", methods=["GET", "POST"])
    def order_success():
        """Order confirmation page."""
        return render_template("success.html")

    @app.route("/rules")
    def rules():
        """ISU Rules & Testing Center."""
        return render_template("isu_rules.html")

    @app.route("/page/<page_id>")
    def custom_page(page_id):
        """Custom page view."""
        db = get_db()
        pg = db.execute(
            "SELECT * FROM custom_pages WHERE id = ? LIMIT 1", (page_id,)
        ).fetchone()
        return render_template("page.html", pg=pg)

    # ── Custom pages for nav (context processor) ──────────────────
    @app.context_processor
    def inject_nav_pages():
        """Make custom pages available to nav template."""
        db = get_db()
        try:
            nav_pages = db.execute(
                "SELECT id, name, slug FROM custom_pages ORDER BY created_at ASC LIMIT 5"
            ).fetchall()
        except Exception:
            nav_pages = []
        return {"nav_pages": nav_pages}

    # ── Error handlers ────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return (
            render_template(
                "index.html",
                posts=[],
                q="",
                page_num=1,
                total=0,
                total_all=0,
                total_filtered=0,
                total_pages=0,
                tech_count=0,
                per_page=9,
            ),
            404,
        )

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


# ── Entry point ──────────────────────────────────────────────────

app = create_app()

if __name__ == "__main__":
    import socket

    # Discover LAN IP so mobile devices know the address to use
    try:
        lan_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        lan_ip = "(could not detect)"
    print("\n  ⛸  On Ice — Aurora Frost Edition")
    print("  ─────────────────────────────────")
    print("  Local  : http://localhost:5000")
    print(f"  Network: http://{lan_ip}:5000  ← open this on your phone")
    print("  (phone must be on the same WiFi)\n")
    app.run(debug=os.getenv("FLASK_ENV") != "production", host="0.0.0.0", port=5000)
