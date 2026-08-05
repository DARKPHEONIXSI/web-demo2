"""
api.py — AJAX data mutation endpoints for the On Ice skating blog.
Handles all CRUD operations for posts, techniques, gallery, pages, settings, users, messages.
"""

import hashlib
import hmac
import io
import json
import mimetypes
import os
import urllib.parse
import urllib.request
from operator import attrgetter

try:
    import magic
except ImportError:  # Windows/local installs often lack libmagic bindings.
    magic = None

import paytmchecksum
import razorpay
from flask import Blueprint, current_app, jsonify, request
from razorpay.errors import SignatureVerificationError
from werkzeug.utils import secure_filename

try:
    from PIL import Image, ImageOps
except ImportError:
    Image = None
    ImageOps = None

from auth import admin_required, current_user, jwt_required
from models import gen_id, get_db, log_audit, save_setting, unique_slug
from purify_html import purify_html

api_bp = Blueprint("api", __name__)


def ok(msg: str = "OK", **extra):
    """Return a standard successful JSON response."""
    payload = {"ok": True, "msg": msg}
    payload.update(extra)
    return jsonify(payload)


def err(msg: str, status: int = 400, **extra):
    """Return a standard error JSON response."""
    payload = {"ok": False, "msg": msg}
    payload.update(extra)
    return jsonify(payload), status


def parse_int_form(name: str, default: int = 0) -> tuple[int | None, str | None]:
    raw = request.form.get(name)
    if raw in (None, ""):
        return default, None
    try:
        return int(raw), None
    except ValueError:
        return None, f"Invalid {name.replace('_', ' ')} value."


def allowed_file(filename: str) -> bool:
    """Check uploaded image extension against the configured allow-list."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_EXTENSIONS"]
    )


def detect_mime(file) -> str:
    """Detect upload MIME type, preferring libmagic when available."""
    if magic is not None:
        file.seek(0)
        mime_type = magic.from_buffer(file.read(2048), mime=True)
        file.seek(0)
        return mime_type
    mime_type, _ = mimetypes.guess_type(file.filename or "")
    return mime_type or ""


def sanitized_image_bytes(file, ext: str) -> tuple[bytes | None, str | None]:
    """Re-encode uploaded images to strip metadata and enforce dimensions."""
    if Image is None or ImageOps is None:
        return None, "Image processing dependency is not installed."

    try:
        file.seek(0)
        with Image.open(file) as img:
            img.load()
            if img.width * img.height > current_app.config["MAX_IMAGE_PIXELS"]:
                return None, "Image dimensions are too large."
            img = ImageOps.exif_transpose(img)
            save_ext = "JPEG" if ext in {"jpg", "jpeg"} else ext.upper()
            if save_ext == "JPG":
                save_ext = "JPEG"
            if save_ext not in {"JPEG", "PNG", "WEBP", "GIF"}:
                return None, "Unsupported image format."
            if save_ext == "JPEG" and img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            elif save_ext in {"PNG", "WEBP", "GIF"} and img.mode not in (
                "RGB",
                "RGBA",
                "P",
                "L",
            ):
                img = img.convert("RGBA")
            output = io.BytesIO()
            img.save(output, format=save_ext, optimize=True)
        file.seek(0)
        return output.getvalue(), None
    except Exception:
        current_app.logger.exception("image re-encoding failed")
        return None, "Invalid image file."


def save_sanitized_image(file, filepath: str, ext: str):
    image_bytes, error = sanitized_image_bytes(file, ext)
    if error:
        return error
    with open(filepath, "wb") as f:
        f.write(image_bytes or b"")
    return None


def storage_public_url(object_name: str) -> str:
    return current_app.config["UPLOAD_URL"] + object_name


def is_safe_public_asset_path(value: str) -> bool:
    if not value:
        return True
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme or parsed.netloc or "\\" in value:
        return False
    return value.startswith(("/uploads/", "/static/images/")) and ".." not in parsed.path


def has_mp4_signature(data: bytes) -> bool:
    return len(data) >= 12 and data[4:8] == b"ftyp"


def save_storage_object(object_name: str, data: bytes, content_type: str) -> str:
    """Save bytes to local uploads and return public URL."""
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    with open(os.path.join(upload_dir, object_name), "wb") as f:
        f.write(data)
    return storage_public_url(object_name)


def delete_storage_object(url_or_path: str):
    """Delete a stored object where possible. Best-effort only."""
    object_name = os.path.basename(url_or_path or "")
    if not object_name:
        return
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], object_name)
    if os.path.exists(filepath):
        try:
            os.unlink(filepath)
        except OSError:
            pass


def verify_turnstile() -> str | None:
    """Verify Cloudflare Turnstile when configured; return error message if invalid."""
    secret = current_app.config.get("TURNSTILE_SECRET_KEY")
    if not secret:
        return None
    token = request.form.get("cf-turnstile-response") or ""
    if not token:
        return "Human verification is required."
    data = urllib.parse.urlencode(
        {"secret": secret, "response": token, "remoteip": request.remote_addr or ""}
    ).encode("utf-8")
    try:
        req = urllib.request.Request(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify", data=data
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except Exception:
        current_app.logger.warning("Turnstile verification request failed")
        return "Human verification failed."
    return None if result.get("success") else "Human verification failed."


def calculate_cart_total(cart_json: str) -> tuple[float, list[dict], str | None]:
    """Calculate cart total from trusted database prices, not browser prices."""
    try:
        cart = json.loads(cart_json or "[]")
    except json.JSONDecodeError:
        return 0.0, [], "Invalid cart data."

    if not isinstance(cart, list) or not cart:
        return 0.0, [], "Cart is empty."

    db = get_db()
    total = 0.0
    items = []
    for raw_item in cart:
        if not isinstance(raw_item, dict):
            return 0.0, [], "Invalid cart item."

        product_id = str(raw_item.get("product_id") or "").strip()
        variant_id = str(raw_item.get("variant_id") or "").strip()
        try:
            quantity = int(raw_item.get("quantity") or 1)
        except (TypeError, ValueError):
            return 0.0, [], "Invalid cart quantity."

        if not product_id or quantity < 1 or quantity > 20:
            return 0.0, [], "Invalid cart item."

        product = db.execute(
            "SELECT id, name, base_price, sale_price, stock_quantity, status FROM products WHERE id=? LIMIT 1",
            (product_id,),
        ).fetchone()
        if not product:
            return 0.0, [], "Product no longer exists."
        if product["status"] != "active":
            return 0.0, [], "Product is not available."
        if not variant_id and int(product["stock_quantity"] or 0) < quantity:
            return 0.0, [], f"Not enough stock for {product['name']}."

        unit_price = float(
            product["sale_price"]
            if product["sale_price"] is not None
            else product["base_price"] or 0
        )
        item_name = product["name"]
        if variant_id:
            variant = db.execute(
                "SELECT id, color, size, stock_quantity, price_override FROM product_variants WHERE id=? AND product_id=? LIMIT 1",
                (variant_id, product_id),
            ).fetchone()
            if not variant:
                return 0.0, [], "Product variant no longer exists."
            if int(variant["stock_quantity"] or 0) < quantity:
                return 0.0, [], f"Not enough stock for {product['name']}."
            if variant["price_override"] is not None:
                unit_price = float(variant["price_override"])
            labels = [v for v in (variant["color"], variant["size"]) if v]
            if labels:
                item_name += " - " + " / ".join(labels)

        line_total = round(unit_price * quantity, 2)
        total += line_total
        items.append(
            {
                "product_id": product_id,
                "variant_id": variant_id or None,
                "name": item_name,
                "quantity": quantity,
                "unit_price": unit_price,
                "line_total": line_total,
            }
        )

    return round(total, 2), items, None


def cart_hash(items: list[dict]) -> str:
    """Create a stable hash for the server-priced cart contents."""
    normalized = [
        {
            "product_id": item["product_id"],
            "variant_id": item["variant_id"] or "",
            "quantity": item["quantity"],
            "unit_price": item["unit_price"],
        }
        for item in items
    ]
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def coupon_discount(subtotal: float, code: str = "") -> tuple[float, str | None]:
    """Return discount for an active coupon code."""
    code = (code or "").strip().upper()
    if not code:
        return 0.0, None
    coupon = (
        get_db()
        .execute("SELECT * FROM coupons WHERE code=? AND active=1 LIMIT 1", (code,))
        .fetchone()
    )
    if not coupon:
        return 0.0, "Coupon is invalid or inactive."
    value = float(coupon["discount_value"] or 0)
    if coupon["discount_type"] == "fixed":
        return min(subtotal, value), None
    return round(subtotal * min(value, 100) / 100, 2), None


def order_totals(subtotal: float, coupon_code: str = "") -> dict:
    """Calculate transparent order totals from the trusted cart subtotal."""
    discount, coupon_error = coupon_discount(subtotal, coupon_code)
    if coupon_error:
        discount = 0.0
    shipping = 0.0 if subtotal >= 5000 else 199.0
    taxable = max(0.0, subtotal - discount)
    tax = round(taxable * 0.18, 2)
    total = round(taxable + shipping + tax, 2)
    return {
        "subtotal": round(subtotal, 2),
        "discount": discount,
        "shipping": shipping,
        "tax": tax,
        "total": total,
        "coupon_error": coupon_error,
    }


# Allowed MIME types for uploads
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "video/mp4",
}

ALLOWED_MEDIA_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "mp4"}


# ── Contact form (public) ────────────────────────────────────


@api_bp.route("/api/contact", methods=["POST"])
def contact():
    """Public contact form submission."""
    turnstile_error = verify_turnstile()
    if turnstile_error:
        log_audit("contact.turnstile_failed", ip_address=request.remote_addr)
        return err(turnstile_error)

    name = (request.form.get("name") or "").strip()
    email = (request.form.get("email") or "").strip()
    subject = (request.form.get("subject") or "").strip()
    message = (request.form.get("message") or "").strip()

    if not name or len(name) > 100:
        return err("Name is required and must be under 100 characters.")

    import re

    email_regex = re.compile(r"^[\w\.\+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-\.]+$")
    if not email or not email_regex.match(email) or len(email) > 150:
        return err("A valid email address is required.")

    if len(subject) > 200:
        return err("Subject must be under 200 characters.")

    if not message or len(message) > 5000:
        return err("Message is required and must be under 5000 characters.")

    db = get_db()
    db.execute(
        "INSERT INTO contact_messages (name, email, subject, message) VALUES (?, ?, ?, ?)",
        (name, email, subject, message),
    )
    db.commit()
    return ok("Message sent! The coach will be in touch soon.")


# ── Get posts (public) ───────────────────────────────────────


@api_bp.route("/api/get_posts")
def get_posts_api():
    """Return published posts as JSON."""
    db = get_db()
    rows = db.execute(
        """SELECT id, title, excerpt, body, cover_image, category, tags, slug, seo_title, seo_description, post_date, read_time, pinned
           FROM posts WHERE status='published'
           ORDER BY pinned DESC, post_date DESC"""
    ).fetchall()
    return jsonify({"ok": True, "posts": [dict(r) for r in rows]})


@api_bp.route("/api/get_products")
def get_products_api():
    """Return active products with their primary images."""
    rows = get_db().execute(
        """SELECT p.*,
                  (SELECT pi.image_url FROM product_images pi
                   WHERE pi.product_id=p.id ORDER BY pi.sort_order ASC LIMIT 1) AS image
           FROM products p WHERE p.status='active' ORDER BY p.created_at DESC"""
    ).fetchall()
    return ok(products=[dict(row) for row in rows])


@api_bp.route("/api/get_product")
def get_product_api():
    """Return one active product with variants, images, and approved reviews."""
    product_id = (request.args.get("id") or "").strip()
    db = get_db()
    product = db.execute(
        "SELECT * FROM products WHERE id=? AND status='active' LIMIT 1",
        (product_id,),
    ).fetchone()
    if not product:
        return err("Product not found.", 404)
    variants = db.execute(
        """SELECT id, product_id, color, size, stock_quantity, price_override
           FROM product_variants WHERE product_id=? ORDER BY color, size""",
        (product_id,),
    ).fetchall()
    images = db.execute(
        """SELECT id, product_id, color_match, image_url, sort_order
           FROM product_images WHERE product_id=? ORDER BY sort_order ASC""",
        (product_id,),
    ).fetchall()
    reviews = db.execute(
        """SELECT id, product_id, name, rating, body, created_at
           FROM product_reviews
           WHERE product_id=? AND status='approved' ORDER BY created_at DESC""",
        (product_id,),
    ).fetchall()
    return ok(
        product=dict(product),
        variants=[dict(row) for row in variants],
        images=[dict(row) for row in images],
        reviews=[dict(row) for row in reviews],
    )


@api_bp.route("/api/get_gallery")
def get_gallery_api():
    """Return gallery items in display order."""
    rows = get_db().execute(
        "SELECT * FROM gallery_items ORDER BY sort_order ASC"
    ).fetchall()
    return ok(gallery=[dict(row) for row in rows])


@api_bp.route("/api/get_techniques")
def get_techniques_api():
    """Return technique guides in display order."""
    rows = get_db().execute(
        "SELECT * FROM techniques ORDER BY sort_order ASC"
    ).fetchall()
    return ok(techniques=[dict(row) for row in rows])


@api_bp.route("/api/get_pages")
def get_pages_api():
    """Return custom pages."""
    rows = get_db().execute(
        "SELECT * FROM custom_pages ORDER BY created_at ASC"
    ).fetchall()
    return ok(pages=[dict(row) for row in rows])


@api_bp.route("/api/get_page")
def get_page_api():
    """Return one custom page by ID."""
    page_id = (request.args.get("id") or "").strip()
    page = get_db().execute(
        "SELECT * FROM custom_pages WHERE id=? LIMIT 1", (page_id,)
    ).fetchone()
    if not page:
        return err("Page not found.", 404)
    return ok(page=dict(page))


@api_bp.route("/api/profile/orders")
@jwt_required
def get_profile_orders_api():
    """Return recent orders owned by the authenticated user."""
    rows = get_db().execute(
        "SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC LIMIT 20",
        (current_user()["id"],),
    ).fetchall()
    return ok(orders=[dict(row) for row in rows])


def order_for_current_user(token: str):
    """Resolve an order token and enforce the SSR owner-or-admin policy."""
    order = get_db().execute(
        "SELECT * FROM orders WHERE order_token=? LIMIT 1", (token,)
    ).fetchone()
    if not order:
        return None, err("Order not found.", 404)
    user = current_user()
    if user.get("role") != "admin" and user.get("id") != order["user_id"]:
        return None, err("Order access forbidden.", 403)
    return order, None


@api_bp.route("/api/order/detail")
@jwt_required
def get_order_detail_api():
    """Return an order and tracking item details to its owner or an admin."""
    order, access_error = order_for_current_user(
        (request.args.get("token") or "").strip()
    )
    if access_error:
        return access_error
    assert order is not None
    items = get_db().execute(
        """SELECT oi.*, p.name AS product_name, pv.color, pv.size
           FROM order_items oi
           LEFT JOIN products p ON p.id=oi.product_id
           LEFT JOIN product_variants pv ON pv.id=oi.product_variant_id
           WHERE oi.order_id=?""",
        (order["id"],),
    ).fetchall()
    return ok(order=dict(order), items=[dict(row) for row in items])


@api_bp.route("/api/invoice/detail")
@jwt_required
def get_invoice_detail_api():
    """Return invoice data to the order owner or an admin."""
    order, access_error = order_for_current_user(
        (request.args.get("token") or "").strip()
    )
    if access_error:
        return access_error
    assert order is not None
    items = get_db().execute(
        """SELECT oi.*, p.name AS product_name
           FROM order_items oi LEFT JOIN products p ON p.id=oi.product_id
           WHERE oi.order_id=?""",
        (order["id"],),
    ).fetchall()
    return ok(invoice=dict(order), order=dict(order), items=[dict(row) for row in items])


@api_bp.route("/api/admin/dashboard")
@admin_required
def get_admin_dashboard_api():
    """Return aggregate dashboard metrics and low-stock products."""
    db = get_db()
    summary = db.execute(
        """SELECT
             (SELECT COUNT(*) FROM posts) AS post_count,
             (SELECT COUNT(*) FROM techniques) AS technique_count,
             (SELECT COUNT(*) FROM users) AS user_count,
             (SELECT COUNT(*) FROM custom_pages) AS page_count,
             (SELECT COUNT(*) FROM gallery_items) AS gallery_count,
             (SELECT COUNT(*) FROM products) AS product_count,
             (SELECT COUNT(*) FROM orders) AS order_count,
             (SELECT COUNT(*) FROM contact_messages WHERE is_read=0) AS unread_count,
             (SELECT COALESCE(SUM(total_amount), 0) FROM orders
              WHERE status='completed') AS revenue"""
    ).fetchone()
    assert summary is not None
    low_stock = db.execute(
        """SELECT id, name, stock_quantity FROM products
           WHERE status='active' AND stock_quantity <= 5
           ORDER BY stock_quantity ASC LIMIT 10"""
    ).fetchall()
    dashboard = {
        "post_count": summary["post_count"],
        "technique_count": summary["technique_count"],
        "user_count": summary["user_count"],
        "page_count": summary["page_count"],
        "gallery_count": summary["gallery_count"],
        "product_count": summary["product_count"],
        "order_count": summary["order_count"],
        "unread_count": summary["unread_count"],
        "revenue": summary["revenue"],
        "low_stock": [dict(row) for row in low_stock],
    }
    return ok(dashboard=dashboard)


@api_bp.route("/api/admin/orders")
@admin_required
def get_admin_orders_api():
    """Return recent orders for administration."""
    rows = get_db().execute(
        "SELECT * FROM orders ORDER BY created_at DESC LIMIT 100"
    ).fetchall()
    return ok(orders=[dict(row) for row in rows])


@api_bp.route("/api/admin/products")
@admin_required
def get_admin_products_api():
    """Return all products with primary images for administration."""
    rows = get_db().execute(
        """SELECT p.*,
                  (SELECT pi.image_url FROM product_images pi
                   WHERE pi.product_id=p.id ORDER BY pi.sort_order ASC LIMIT 1) AS image
           FROM products p ORDER BY p.created_at DESC"""
    ).fetchall()
    return ok(products=[dict(row) for row in rows])


@api_bp.route("/api/admin/posts")
@admin_required
def get_admin_posts_api():
    """Return all posts for administration."""
    rows = get_db().execute(
        "SELECT * FROM posts ORDER BY post_date DESC"
    ).fetchall()
    return ok(posts=[dict(row) for row in rows])


@api_bp.route("/api/admin/messages")
@admin_required
def get_admin_messages_api():
    """Return recent contact messages for administration."""
    rows = get_db().execute(
        "SELECT * FROM contact_messages ORDER BY created_at DESC LIMIT 50"
    ).fetchall()
    return ok(messages=[dict(row) for row in rows])


@api_bp.route("/api/admin/users")
@admin_required
def get_admin_users_api():
    """Return non-secret user account fields for administration."""
    rows = get_db().execute(
        """SELECT id, username, google_email, is_google, role, created_at
           FROM users ORDER BY created_at DESC"""
    ).fetchall()
    return ok(users=[dict(row) for row in rows])


@api_bp.route("/api/admin/media")
@admin_required
def get_admin_media_api():
    """Return media library records for administration."""
    rows = get_db().execute(
        "SELECT * FROM media_library ORDER BY uploaded_at DESC"
    ).fetchall()
    return ok(media=[dict(row) for row in rows])


@api_bp.route("/api/cart/quote", methods=["POST"])
def cart_quote():
    """Return a server-confirmed quote for the cart."""
    total_amount, items, cart_error = calculate_cart_total(
        request.form.get("cart") or "[]"
    )
    if cart_error:
        log_audit(
            "cart.quote_failed", ip_address=request.remote_addr, reason=cart_error
        )
        return err(cart_error)
    totals = order_totals(total_amount, request.form.get("coupon") or "")
    if totals["coupon_error"]:
        return err(totals["coupon_error"])
    return jsonify(
        {
            "ok": True,
            "subtotal_amount": totals["subtotal"],
            "discount_amount": totals["discount"],
            "shipping_amount": totals["shipping"],
            "tax_amount": totals["tax"],
            "total_amount": totals["total"],
            "items": items,
        }
    )


@api_bp.route("/api/comment", methods=["POST"])
def save_comment():
    post_id = (request.form.get("post_id") or "").strip()
    name = (request.form.get("name") or "").strip()[:100]
    body = (request.form.get("body") or "").strip()[:1000]
    if not post_id or not name or not body:
        return err("Name and comment are required.")
    db = get_db()
    post = db.execute(
        "SELECT id FROM posts WHERE id=? AND status='published'", (post_id,)
    ).fetchone()
    if not post:
        return err("Post not found.", 404)
    db.execute(
        "INSERT INTO post_comments (post_id, name, body) VALUES (?, ?, ?)",
        (post_id, name, body),
    )
    db.commit()
    return ok("Comment added.")


@api_bp.route("/api/review", methods=["POST"])
@jwt_required
def save_review():
    product_id = (request.form.get("product_id") or "").strip()
    body = (request.form.get("body") or "").strip()[:1000]
    try:
        rating = max(1, min(5, int(request.form.get("rating") or 5)))
    except ValueError:
        rating = 5
    if not product_id:
        return err("Product is required.")
    db = get_db()
    product = db.execute(
        "SELECT id FROM products WHERE id=? AND status='active'", (product_id,)
    ).fetchone()
    if not product:
        return err("Product not found.", 404)
    user = db.execute(
        "SELECT username FROM users WHERE id=?", (current_user()["id"],)
    ).fetchone()
    name = user["username"] if user else "Member"
    db.execute(
        "INSERT INTO product_reviews (product_id, user_id, name, rating, body) VALUES (?, ?, ?, ?, ?)",
        (product_id, current_user()["id"], name, rating, body),
    )
    db.commit()
    return ok("Review added.")


@api_bp.route("/api/wishlist/toggle", methods=["POST"])
@jwt_required
def toggle_wishlist():
    product_id = (request.form.get("product_id") or "").strip()
    db = get_db()
    product = db.execute(
        "SELECT id FROM products WHERE id=? AND status='active'", (product_id,)
    ).fetchone()
    if not product:
        return err("Product not found.", 404)
    existing = db.execute(
        "SELECT 1 FROM wishlist_items WHERE user_id=? AND product_id=?",
        (current_user()["id"], product_id),
    ).fetchone()
    if existing:
        db.execute(
            "DELETE FROM wishlist_items WHERE user_id=? AND product_id=?",
            (current_user()["id"], product_id),
        )
        wished = False
    else:
        db.execute(
            "INSERT OR IGNORE INTO wishlist_items (user_id, product_id) VALUES (?, ?)",
            (current_user()["id"], product_id),
        )
        wished = True
    db.commit()
    return ok("Wishlist updated.", wished=wished)


@api_bp.route("/api/cart/save", methods=["POST"])
@jwt_required
def save_server_cart():
    total, items, cart_error = calculate_cart_total(request.form.get("cart") or "[]")
    if cart_error:
        return err(cart_error)
    db = get_db()
    db.execute("DELETE FROM cart_items WHERE user_id=?", (current_user()["id"],))
    for item in items:
        db.execute(
            "INSERT INTO cart_items (user_id, product_id, variant_id, quantity) VALUES (?, ?, ?, ?)",
            (
                current_user()["id"],
                item["product_id"],
                item["variant_id"] or "",
                item["quantity"],
            ),
        )
    db.commit()
    return ok("Cart saved.")


@api_bp.route("/api/cart/load")
@jwt_required
def load_server_cart():
    rows = (
        get_db()
        .execute("SELECT * FROM cart_items WHERE user_id=?", (current_user()["id"],))
        .fetchall()
    )
    return jsonify({"ok": True, "cart": [dict(r) for r in rows]})


# ── Image upload ──────────────────────────────────────────────


@api_bp.route("/api/upload_image", methods=["POST"])
@admin_required
def upload_image():
    """Upload an image file. Admin only."""
    if "image" not in request.files:
        return err("No file received.")

    file = request.files["image"]
    filename = file.filename or ""
    if filename == "":
        return err("No file selected.")

    if not allowed_file(filename):
        return err("Only JPEG, PNG, GIF and WebP images are allowed.")

    # MIME type validation
    mime_type = detect_mime(file)
    if mime_type not in ALLOWED_MIME_TYPES or not mime_type.startswith("image/"):
        return err(
            "Invalid file type. Only JPEG, PNG, GIF and WebP images are allowed."
        )

    ext = filename.rsplit(".", 1)[1].lower()
    filename = gen_id() + "." + ext
    image_bytes, image_error = sanitized_image_bytes(file, ext)
    if image_error:
        log_audit(
            "upload.image_rejected",
            actor_id=current_user().get("id"),
            ip_address=request.remote_addr,
            reason=image_error,
        )
        return err(image_error)
    try:
        url = save_storage_object(filename, image_bytes or b"", mime_type)
    except RuntimeError as e:
        return err(str(e), 502)
    current_app.logger.info(
        "uploaded image %s by user %s", filename, current_user().get("id")
    )
    log_audit(
        "upload.image",
        actor_id=current_user().get("id"),
        ip_address=request.remote_addr,
        filename=filename,
    )

    return ok("Uploaded.", path=url, filename=filename)


# ── POSTS ─────────────────────────────────────────────────────


@api_bp.route("/api/save_post", methods=["POST"])
@admin_required
def save_post():
    """Create or update a post. Admin only."""
    post_id = (request.form.get("id") or "").strip()
    title = (request.form.get("title") or "").strip()
    excerpt = (request.form.get("excerpt") or "").strip()
    body = purify_html((request.form.get("body") or "").strip())
    cover_image = (request.form.get("cover_image") or "").strip()
    category = (request.form.get("category") or "").strip()
    tags = (request.form.get("tags") or "").strip()
    slug = (request.form.get("slug") or "").strip()
    seo_title = (request.form.get("seo_title") or "").strip()
    seo_description = (request.form.get("seo_description") or "").strip()
    author = (request.form.get("author") or "The Coach").strip()
    read_time, read_time_error = parse_int_form("read_time", 4)
    if read_time_error:
        return err(read_time_error)
    read_time = max(1, read_time or 4)
    pinned = 1 if request.form.get("pinned") in ("1", "true", "on") else 0
    status = "draft" if request.form.get("status") == "draft" else "published"
    post_date = (request.form.get("post_date") or "").strip()

    if not title or len(title) > 200:
        return err("Title is required and must be under 200 characters.")
    if not body:
        return err("Body is required.")
    if len(seo_title) > 200 or len(seo_description) > 300:
        return err("SEO title/description are too long.")
    if not is_safe_public_asset_path(cover_image):
        return err("Image path must be a local uploaded or static image.")

    author_id = (
        current_user().get("id") if current_user().get("id") != "admin" else None
    )

    db = get_db()
    slug = unique_slug("posts", slug or title, post_id)
    if post_id:
        db.execute(
            """UPDATE posts SET title=?, excerpt=?, body=?, cover_image=?, category=?, tags=?, slug=?,
               seo_title=?, seo_description=?, author=?, author_id=?, read_time=?, pinned=?, status=?, post_date=?, updated_at=datetime('now')
               WHERE id=?""",
            (
                title,
                excerpt,
                body,
                cover_image,
                category,
                tags,
                slug,
                seo_title,
                seo_description,
                author,
                author_id,
                read_time,
                pinned,
                status,
                post_date,
                post_id,
            ),
        )
    else:
        post_id = gen_id()
        db.execute(
            """INSERT INTO posts (id, title, excerpt, body, cover_image, category, tags, slug, seo_title, seo_description, author, author_id, read_time, pinned, status, post_date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                post_id,
                title,
                excerpt,
                body,
                cover_image,
                category,
                tags,
                slug,
                seo_title,
                seo_description,
                author,
                author_id,
                read_time,
                pinned,
                status,
                post_date,
            ),
        )
    db.commit()
    return ok("Post saved.", id=post_id, slug=slug)


@api_bp.route("/api/delete_post", methods=["POST"])
@admin_required
def delete_post():
    """Delete a post. Admin only."""
    post_id = (request.form.get("id") or "").strip()
    if not post_id:
        return err("No ID.")

    db = get_db()
    db.execute("DELETE FROM posts WHERE id=?", (post_id,))
    db.commit()
    return ok("Post deleted.")


@api_bp.route("/api/toggle_pin", methods=["POST"])
@admin_required
def toggle_pin():
    """Toggle pin status on a post. Admin only."""
    post_id = (request.form.get("id") or "").strip()
    db = get_db()
    db.execute("UPDATE posts SET pinned = 1 - pinned WHERE id=?", (post_id,))
    db.commit()
    return ok("Toggled.")


# ── TECHNIQUES ────────────────────────────────────────────────


@api_bp.route("/api/save_technique", methods=["POST"])
@admin_required
def save_technique():
    """Create or update a technique. Admin only."""
    tech_id = (request.form.get("id") or "").strip()
    title = (request.form.get("title") or "").strip()
    icon = (request.form.get("icon") or "⛸").strip()
    excerpt = (request.form.get("excerpt") or "").strip()
    body = purify_html((request.form.get("body") or "").strip())
    sort_order, sort_order_error = parse_int_form("sort_order")
    if sort_order_error:
        return err(sort_order_error)

    if not title or len(title) > 100:
        return err("Title is required and must be under 100 characters.")
    if len(icon) > 10:
        return err("Icon is too long.")

    db = get_db()
    if tech_id:
        db.execute(
            "UPDATE techniques SET title=?, icon=?, excerpt=?, body=?, sort_order=? WHERE id=?",
            (title, icon, excerpt, body, sort_order, tech_id),
        )
    else:
        tech_id = gen_id()
        db.execute(
            "INSERT INTO techniques (id, title, icon, excerpt, body, sort_order) VALUES (?, ?, ?, ?, ?, ?)",
            (tech_id, title, icon, excerpt, body, sort_order),
        )
    db.commit()
    return ok("Technique saved.", id=tech_id)


@api_bp.route("/api/delete_technique", methods=["POST"])
@admin_required
def delete_technique():
    """Delete a technique. Admin only."""
    tech_id = (request.form.get("id") or "").strip()
    if not tech_id:
        return err("No ID.")

    db = get_db()
    db.execute("DELETE FROM techniques WHERE id=?", (tech_id,))
    db.commit()
    return ok("Technique deleted.")


# ── CUSTOM PAGES ──────────────────────────────────────────────


@api_bp.route("/api/save_page", methods=["POST"])
@admin_required
def save_page():
    """Create or update a custom page. Admin only."""
    import re

    page_id = (request.form.get("id") or "").strip()
    name = (request.form.get("name") or "").strip()
    body = purify_html((request.form.get("body") or "").strip())
    seo_title = (request.form.get("seo_title") or "").strip()
    seo_description = (request.form.get("seo_description") or "").strip()
    slug = re.sub(r"[^a-z0-9-]", "", name.lower().replace(" ", "-"))

    if not name:
        return err("Page name is required.")

    db = get_db()
    if page_id:
        db.execute(
            "UPDATE custom_pages SET name=?, slug=?, body=?, seo_title=?, seo_description=?, updated_at=datetime('now') WHERE id=?",
            (name, slug, body, seo_title, seo_description, page_id),
        )
    else:
        page_id = gen_id()
        db.execute(
            "INSERT INTO custom_pages (id, name, slug, body, seo_title, seo_description) VALUES (?, ?, ?, ?, ?, ?)",
            (page_id, name, slug, body, seo_title, seo_description),
        )
    db.commit()
    return ok("Page saved.", id=page_id)


@api_bp.route("/api/delete_page", methods=["POST"])
@admin_required
def delete_page():
    """Delete a custom page. Admin only."""
    page_id = (request.form.get("id") or "").strip()
    if not page_id:
        return err("No ID.")

    db = get_db()
    db.execute("DELETE FROM custom_pages WHERE id=?", (page_id,))
    db.commit()
    return ok("Page deleted.")


# ── SETTINGS ──────────────────────────────────────────────────


@api_bp.route("/api/save_settings", methods=["POST"])
@admin_required
def save_settings():
    """Save site settings. Admin only."""
    keys = [
        "blog_name",
        "tagline",
        "hero_quote",
        "coach_title",
        "whatsapp_link",
        "contact_email",
    ]
    for k in keys:
        val = request.form.get(k)
        if val is not None:
            save_setting(k, val.strip())

    db = get_db()
    fb_token = (request.form.get("fb_token") or "").strip()
    if fb_token:
        db.execute("DELETE FROM social_tokens WHERE platform='facebook'")
        db.execute(
            "INSERT INTO social_tokens (id, platform, access_token) VALUES (?, 'facebook', ?)",
            (gen_id(), fb_token),
        )

    ig_token = (request.form.get("ig_token") or "").strip()
    if ig_token:
        db.execute("DELETE FROM social_tokens WHERE platform='instagram'")
        db.execute(
            "INSERT INTO social_tokens (id, platform, access_token) VALUES (?, 'instagram', ?)",
            (gen_id(), ig_token),
        )
    db.commit()

    return ok("Settings saved.")


# ── GALLERY ───────────────────────────────────────────────────


@api_bp.route("/api/save_gallery_item", methods=["POST"])
@admin_required
def save_gallery_item():
    """Create or update a gallery item. Admin only."""
    item_id = (request.form.get("id") or "").strip()
    emoji = (request.form.get("emoji") or "⛸").strip()
    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip()
    tag = (request.form.get("tag") or "Training").strip()
    image_path = (request.form.get("image_path") or "").strip()
    sort_order, sort_order_error = parse_int_form("sort_order")
    if sort_order_error:
        return err(sort_order_error)

    if not title:
        return err("Title is required.")
    if not is_safe_public_asset_path(image_path):
        return err("Image path must be a local uploaded or static image.")

    db = get_db()
    if item_id:
        db.execute(
            """UPDATE gallery_items SET emoji=?, title=?, description=?,
               tag=?, image_path=?, sort_order=? WHERE id=?""",
            (emoji, title, description, tag, image_path, sort_order, item_id),
        )
    else:
        item_id = gen_id()
        db.execute(
            """INSERT INTO gallery_items (id, emoji, title, description, tag, image_path, sort_order)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (item_id, emoji, title, description, tag, image_path, sort_order),
        )
    db.commit()
    return ok("Gallery item saved.", id=item_id)


@api_bp.route("/api/delete_gallery_item", methods=["POST"])
@admin_required
def delete_gallery_item():
    """Delete a gallery item. Admin only."""
    item_id = (request.form.get("id") or "").strip()
    if not item_id:
        return err("No ID.")

    db = get_db()
    # Delete uploaded file if exists
    row = db.execute(
        "SELECT image_path FROM gallery_items WHERE id=? LIMIT 1", (item_id,)
    ).fetchone()
    if row and row["image_path"]:
        delete_storage_object(row["image_path"])

    db.execute("DELETE FROM gallery_items WHERE id=?", (item_id,))
    db.commit()
    return ok("Gallery item deleted.")


# ── CONTACT MESSAGES ──────────────────────────────────────────


@api_bp.route("/api/mark_read", methods=["POST"])
@admin_required
def mark_read():
    """Mark a contact message as read. Admin only."""
    msg_id, msg_id_error = parse_int_form("id")
    if msg_id_error:
        return err(msg_id_error)
    db = get_db()
    db.execute("UPDATE contact_messages SET is_read=1 WHERE id=?", (msg_id,))
    db.commit()
    return ok("Marked read.")


@api_bp.route("/api/delete_message", methods=["POST"])
@admin_required
def delete_message():
    """Delete a contact message. Admin only."""
    msg_id, msg_id_error = parse_int_form("id")
    if msg_id_error:
        return err(msg_id_error)
    db = get_db()
    db.execute("DELETE FROM contact_messages WHERE id=?", (msg_id,))
    db.commit()
    return ok("Deleted.")


# ── USERS ─────────────────────────────────────────────────────


@api_bp.route("/api/delete_user", methods=["POST"])
@admin_required
def delete_user():
    """Delete a user. Admin only."""
    user_id = (request.form.get("id") or "").strip()
    if not user_id:
        return err("No ID.")

    db = get_db()
    if user_id == current_user().get("id"):
        return err("You cannot delete your own account.")
    target = db.execute("SELECT role FROM users WHERE id=?", (user_id,)).fetchone()
    if target and target["role"] == "admin":
        admin_count_row = db.execute(
            "SELECT COUNT(*) FROM users WHERE role='admin'"
        ).fetchone()
        admin_count = admin_count_row[0] if admin_count_row else 0
        if admin_count <= 1:
            return err("Cannot delete the only admin account.")
    db.execute("DELETE FROM users WHERE id=?", (user_id,))
    db.commit()
    return ok("User deleted.")


# ── CMS ENDPOINTS ─────────────────────────────────────────────


@api_bp.route("/api/upload_media", methods=["POST"])
@admin_required
def upload_media():
    """Upload media (image or MP4 video) to the library. Admin only."""
    if "media" not in request.files:
        return err("No file received.")
    file = request.files["media"]
    filename = file.filename or ""
    if filename == "":
        return err("No file selected.")

    # Strict extension whitelist
    safe_name = secure_filename(filename)
    if "." not in safe_name:
        return err("Invalid file: no extension detected.")
    ext = safe_name.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_MEDIA_EXTENSIONS:
        return err("Only images (JPEG, PNG, GIF, WebP) and MP4 video are allowed.")

    # MIME type validation
    mime_type = detect_mime(file)
    if mime_type not in ALLOWED_MIME_TYPES:
        return err(
            "Invalid file type. Only JPEG, PNG, GIF, WebP images and MP4 video are allowed."
        )

    filename = gen_id() + "." + ext
    media_type = "video" if ext == "mp4" else "image"
    if media_type == "image":
        data, image_error = sanitized_image_bytes(file, ext)
        if image_error:
            log_audit(
                "upload.media_rejected",
                actor_id=current_user().get("id"),
                ip_address=request.remote_addr,
                reason=image_error,
            )
            return err(image_error)
    else:
        file.seek(0)
        data = file.read()
        if not has_mp4_signature(data):
            return err("Invalid MP4 file.")

    try:
        url = save_storage_object(filename, data or b"", mime_type)
    except RuntimeError as e:
        return err(str(e), 502)
    media_id = gen_id()
    db = get_db()
    db.execute(
        "INSERT INTO media_library (id, media_type, url) VALUES (?, ?, ?)",
        (media_id, media_type, url),
    )
    db.commit()
    current_app.logger.info(
        "uploaded media %s by user %s", filename, current_user().get("id")
    )
    log_audit(
        "upload.media",
        actor_id=current_user().get("id"),
        ip_address=request.remote_addr,
        filename=filename,
        media_type=media_type,
    )
    return ok("Media uploaded.", url=url)


@api_bp.route("/api/delete_media", methods=["POST"])
@admin_required
def delete_media():
    media_id = request.form.get("id")
    db = get_db()
    row = db.execute(
        "SELECT url FROM media_library WHERE id=? LIMIT 1", (media_id,)
    ).fetchone()
    if row and row["url"]:
        delete_storage_object(row["url"])
    db.execute("DELETE FROM media_library WHERE id=?", (media_id,))
    db.commit()
    return ok("Deleted.")


@api_bp.route("/api/save_product", methods=["POST"])
@admin_required
def save_product():
    """Create or update a product. Admin only."""
    pid = (request.form.get("id") or "").strip()
    name = (request.form.get("name") or "").strip()
    if not name:
        return err("Product name is required.")

    desc = purify_html((request.form.get("description") or "").strip())
    category = (request.form.get("category") or "").strip()
    badge = (request.form.get("badge") or "").strip()
    sku = (request.form.get("sku") or "").strip()
    status = (
        request.form.get("status")
        if request.form.get("status") in {"active", "draft", "archived"}
        else "active"
    )
    seo_title = (request.form.get("seo_title") or "").strip()
    seo_description = (request.form.get("seo_description") or "").strip()

    try:
        price = float(request.form.get("base_price") or 0)
        if price < 0:
            return err("Price cannot be negative.")
    except (ValueError, TypeError):
        return err("Invalid price value.")
    try:
        stock_quantity = int(request.form.get("stock_quantity") or 0)
        if stock_quantity < 0:
            return err("Stock cannot be negative.")
    except (ValueError, TypeError):
        return err("Invalid stock value.")
    sale_price_raw = (request.form.get("sale_price") or "").strip()
    sale_price = None
    if sale_price_raw:
        try:
            sale_price = float(sale_price_raw)
            if sale_price < 0:
                return err("Sale price cannot be negative.")
        except (ValueError, TypeError):
            return err("Invalid sale price value.")

    db = get_db()
    if sku:
        existing = db.execute(
            "SELECT id FROM products WHERE sku=? AND id != ? LIMIT 1", (sku, pid or "")
        ).fetchone()
        if existing:
            return err("SKU already exists.")
    if pid:
        db.execute(
            """UPDATE products SET name=?, description=?, category=?, badge=?, sku=?, status=?,
               stock_quantity=?, base_price=?, sale_price=?, seo_title=?, seo_description=?, updated_at=datetime('now')
               WHERE id=?""",
            (
                name,
                desc,
                category,
                badge,
                sku,
                status,
                stock_quantity,
                price,
                sale_price,
                seo_title,
                seo_description,
                pid,
            ),
        )
    else:
        pid = gen_id()
        db.execute(
            """INSERT INTO products (id, name, description, category, badge, sku, status,
               stock_quantity, base_price, sale_price, seo_title, seo_description)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                pid,
                name,
                desc,
                category,
                badge,
                sku,
                status,
                stock_quantity,
                price,
                sale_price,
                seo_title,
                seo_description,
            ),
        )
    db.commit()
    return ok("Product saved.", id=pid)


@api_bp.route("/api/delete_product", methods=["POST"])
@admin_required
def delete_product():
    pid = request.form.get("id")
    db = get_db()
    db.execute("DELETE FROM product_variants WHERE product_id=?", (pid,))
    db.execute("DELETE FROM product_images WHERE product_id=?", (pid,))
    db.execute("DELETE FROM products WHERE id=?", (pid,))
    db.commit()
    return ok("Deleted.")


@api_bp.route("/api/save_variant", methods=["POST"])
@admin_required
def save_variant():
    pid = request.form.get("product_id")
    color = request.form.get("color", "")
    size = request.form.get("size", "")
    try:
        stock = int(request.form.get("stock_quantity") or 0)
    except ValueError:
        stock = 0
    price_raw = (request.form.get("price_override") or "").strip()
    price_override = None
    if price_raw:
        try:
            price_override = float(price_raw)
        except ValueError:
            return err("Invalid variant price.")
    db = get_db()
    db.execute(
        "INSERT INTO product_variants (id, product_id, color, size, stock_quantity, price_override) VALUES (?, ?, ?, ?, ?, ?)",
        (gen_id(), pid, color, size, stock, price_override),
    )
    db.commit()
    return ok("Saved.")


@api_bp.route("/api/delete_variant", methods=["POST"])
@admin_required
def delete_variant():
    vid = request.form.get("id")
    db = get_db()
    db.execute("DELETE FROM product_variants WHERE id=?", (vid,))
    db.commit()
    return ok("Deleted.")


@api_bp.route("/api/save_prod_image", methods=["POST"])
@admin_required
def save_prod_image():
    pid = request.form.get("product_id")
    url = (request.form.get("image_url") or "").strip()
    color = request.form.get("color_match", "")
    if not is_safe_public_asset_path(url):
        return err("Image path must be a local uploaded or static image.")
    db = get_db()
    db.execute(
        "INSERT INTO product_images (id, product_id, image_url, color_match) VALUES (?, ?, ?, ?)",
        (gen_id(), pid, url, color),
    )
    db.commit()
    return ok("Saved.")


@api_bp.route("/api/delete_prod_image", methods=["POST"])
@admin_required
def delete_prod_image():
    iid = request.form.get("id")
    db = get_db()
    db.execute("DELETE FROM product_images WHERE id=?", (iid,))
    db.commit()
    return ok("Deleted.")


@api_bp.route("/api/update_order_status", methods=["POST"])
@admin_required
def update_order_status():
    """Update order payment, fulfillment, and tracking state. Admin only."""
    order_id = (request.form.get("id") or "").strip()
    status = request.form.get("status") or "completed"
    fulfillment_status = request.form.get("fulfillment_status") or "pending"
    tracking_number = (request.form.get("tracking_number") or "").strip()
    if status not in {
        "pending",
        "completed",
        "payment_failed",
        "cancelled",
        "refunded",
    }:
        return err("Invalid payment status.")
    if fulfillment_status not in {
        "pending",
        "packed",
        "shipped",
        "delivered",
        "cancelled",
        "returned",
    }:
        return err("Invalid fulfillment status.")
    db = get_db()
    db.execute(
        "UPDATE orders SET status=?, fulfillment_status=?, tracking_number=? WHERE id=?",
        (status, fulfillment_status, tracking_number, order_id),
    )
    db.commit()
    log_audit(
        "order.status_updated",
        actor_id=current_user().get("id"),
        ip_address=request.remote_addr,
        order_id=order_id,
        status=status,
        fulfillment_status=fulfillment_status,
    )
    return ok("Order updated.")


# ── Razorpay Endpoints ────────────────────────────────────────


@api_bp.route("/api/create_razorpay_order", methods=["POST"])
@jwt_required
def create_razorpay_order():
    """Create a Razorpay order. Returns order_id and amount in paise."""
    subtotal_amount, items, cart_error = calculate_cart_total(
        request.form.get("cart") or "[]"
    )
    if cart_error:
        current_app.logger.warning(
            "cart validation failed during Razorpay create: %s", cart_error
        )
        return err(cart_error)
    totals = order_totals(subtotal_amount, request.form.get("coupon") or "")
    if totals["coupon_error"]:
        return err(totals["coupon_error"])
    if totals["total"] <= 0:
        return err("Amount must be greater than zero.")

    # Amount in paise
    amount_paise = int(totals["total"] * 100)

    client = razorpay.Client(
        auth=(
            current_app.config["RAZORPAY_KEY_ID"],
            current_app.config["RAZORPAY_KEY_SECRET"],
        )
    )

    try:
        order_data = {
            "amount": amount_paise,
            "currency": "INR",
            "payment_capture": "1",
            "notes": {
                "user_id": current_user().get("id", "guest"),
                "item_count": str(sum(item["quantity"] for item in items)),
                "cart_hash": cart_hash(items),
            },
        }
        order = attrgetter("order")(client).create(data=order_data)
        current_app.logger.info(
            "created Razorpay order %s for user %s amount %s",
            order["id"],
            current_user().get("id", "guest"),
            amount_paise,
        )
        return jsonify(
            {
                "ok": True,
                "order_id": order["id"],
                "amount": amount_paise,
                "subtotal_amount": totals["subtotal"],
                "shipping_amount": totals["shipping"],
                "tax_amount": totals["tax"],
                "total_amount": totals["total"],
            }
        )
    except Exception as e:
        current_app.logger.warning("Razorpay order creation failed: %s", e)
        return err(f"Razorpay error: {str(e)}")


@api_bp.route("/api/verify_razorpay", methods=["POST"])
@jwt_required
def verify_razorpay():
    """Verify Razorpay payment signature and create order with idempotency check."""
    name = (request.form.get("name") or "").strip()
    address = (request.form.get("address") or "").strip()
    email = (request.form.get("email") or "").strip()
    phone = (request.form.get("phone") or "").strip()

    subtotal_amount, items, cart_error = calculate_cart_total(
        request.form.get("cart") or "[]"
    )
    if cart_error:
        current_app.logger.warning(
            "cart validation failed during Razorpay verify: %s", cart_error
        )
        return err(cart_error)
    totals = order_totals(subtotal_amount, request.form.get("coupon") or "")
    if totals["coupon_error"]:
        return err(totals["coupon_error"])

    razorpay_payment_id = request.form.get("razorpay_payment_id")
    razorpay_order_id = request.form.get("razorpay_order_id")
    razorpay_signature = request.form.get("razorpay_signature")

    if not razorpay_payment_id or not razorpay_order_id or not razorpay_signature:
        return err("Missing payment details.")

    # Verify signature
    client = razorpay.Client(
        auth=(
            current_app.config["RAZORPAY_KEY_ID"],
            current_app.config["RAZORPAY_KEY_SECRET"],
        )
    )

    try:
        attrgetter("utility")(client).verify_payment_signature(
            {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            }
        )
    except SignatureVerificationError:
        current_app.logger.warning(
            "invalid Razorpay signature for payment %s", razorpay_payment_id
        )
        return err("Invalid payment signature")

    amount_paise = int(totals["total"] * 100)
    try:
        payment = attrgetter("payment")(client).fetch(razorpay_payment_id)
        provider_order = attrgetter("order")(client).fetch(razorpay_order_id)
    except Exception as e:
        current_app.logger.warning("Razorpay provider verification failed: %s", e)
        return err("Could not verify payment with Razorpay.")

    if payment.get("order_id") != razorpay_order_id:
        current_app.logger.warning(
            "Razorpay order mismatch for payment %s", razorpay_payment_id
        )
        return err("Payment order mismatch.")
    if (
        int(payment.get("amount") or 0) != amount_paise
        or payment.get("currency") != "INR"
    ):
        current_app.logger.warning(
            "Razorpay amount mismatch for payment %s", razorpay_payment_id
        )
        return err("Payment amount mismatch.")
    if payment.get("status") != "captured":
        current_app.logger.warning(
            "Razorpay payment not completed: %s", payment.get("status")
        )
        log_audit(
            "payment.razorpay_not_captured",
            actor_id=current_user().get("id"),
            ip_address=request.remote_addr,
            status=payment.get("status"),
        )
        return err("Payment is not completed.")
    if int(provider_order.get("amount") or 0) != amount_paise:
        current_app.logger.warning(
            "Razorpay order amount mismatch for order %s", razorpay_order_id
        )
        return err("Order amount mismatch.")
    provider_notes = provider_order.get("notes") or {}
    if provider_notes.get("user_id") and provider_notes.get("user_id") != current_user().get("id"):
        current_app.logger.warning(
            "Razorpay user mismatch for order %s", razorpay_order_id
        )
        return err("Payment user mismatch.")
    if provider_notes.get("cart_hash") != cart_hash(items):
        current_app.logger.warning(
            "Razorpay cart hash mismatch for order %s", razorpay_order_id
        )
        return err("Cart changed after payment order creation.")

    # Idempotency check - prevent duplicate orders for same payment
    db = get_db()
    existing = db.execute(
        "SELECT id FROM orders WHERE razorpay_payment_id = ?", (razorpay_payment_id,)
    ).fetchone()

    if existing:
        return ok("Order already processed.", order_id=existing["id"])

    # Generate order token (UUIDv4)
    import uuid

    order_token = str(uuid.uuid4())
    order_id = gen_id()

    try:
        db.execute(
            """INSERT INTO orders (id, user_id, name, address, total_amount, shipping_amount, tax_amount, discount_amount, payment_method,
                                  razorpay_payment_id, razorpay_order_id, order_token,
                                  customer_email, customer_phone, status, fulfillment_status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                order_id,
                current_user().get("id"),
                name,
                address,
                totals["total"],
                totals["shipping"],
                totals["tax"],
                totals["discount"],
                "razorpay",
                razorpay_payment_id,
                razorpay_order_id,
                order_token,
                email,
                phone,
                "completed",
                "pending",
            ),
        )

        for item in items:
            db.execute(
                """INSERT INTO order_items
                   (id, order_id, product_id, product_variant_id, quantity, price_at_time)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    gen_id(),
                    order_id,
                    item["product_id"],
                    item["variant_id"],
                    item["quantity"],
                    item["unit_price"],
                ),
            )
            if item["variant_id"]:
                cur = db.execute(
                    "UPDATE product_variants SET stock_quantity = stock_quantity - ? WHERE id=? AND stock_quantity >= ?",
                    (item["quantity"], item["variant_id"], item["quantity"]),
                )
                if cur.rowcount != 1:
                    raise ValueError(f"Not enough stock for {item['name']}.")
            else:
                cur = db.execute(
                    "UPDATE products SET stock_quantity = stock_quantity - ? WHERE id=? AND stock_quantity >= ?",
                    (item["quantity"], item["product_id"], item["quantity"]),
                )
                if cur.rowcount != 1:
                    raise ValueError(f"Not enough stock for {item['name']}.")
        db.commit()
    except Exception as e:
        db.rollback()
        current_app.logger.warning("local order creation failed: %s", e)
        return err("Could not create local order. Please contact support.")

    current_app.logger.info(
        "completed order %s for payment %s", order_id, razorpay_payment_id
    )
    log_audit(
        "payment.razorpay_completed",
        actor_id=current_user().get("id"),
        ip_address=request.remote_addr,
        order_id=order_id,
        payment_id=razorpay_payment_id,
    )

    # Trigger notifications (async in production)
    try:
        send_order_notifications(order_id, name, email, phone, totals["total"])
    except Exception:
        pass  # Log error in production

    return ok(
        "Order completed successfully.", order_id=order_id, order_token=order_token
    )


@api_bp.route("/api/order/cancel", methods=["POST"])
@jwt_required
def cancel_order():
    token = (request.form.get("order_token") or "").strip()
    db = get_db()
    order = db.execute(
        "SELECT * FROM orders WHERE order_token=? AND user_id=?",
        (token, current_user()["id"]),
    ).fetchone()
    if not order:
        return err("Order not found.", 404)
    if order["fulfillment_status"] not in {"pending", "packed"}:
        return err("This order can no longer be cancelled.")
    db.execute(
        "UPDATE orders SET status='cancelled', fulfillment_status='cancelled' WHERE id=?",
        (order["id"],),
    )
    db.commit()
    return ok("Cancellation requested.")


@api_bp.route("/api/returns/request", methods=["POST"])
@jwt_required
def request_return():
    token = (request.form.get("order_token") or "").strip()
    reason = (request.form.get("reason") or "").strip()[:1000]
    if not reason:
        return err("Return reason is required.")
    db = get_db()
    order = db.execute(
        "SELECT * FROM orders WHERE order_token=? AND user_id=?",
        (token, current_user()["id"]),
    ).fetchone()
    if not order:
        return err("Order not found.", 404)
    db.execute(
        "INSERT INTO return_requests (id, order_id, user_id, reason) VALUES (?, ?, ?, ?)",
        (gen_id(), order["id"], current_user()["id"], reason),
    )
    db.commit()
    return ok("Return request submitted.")


@api_bp.route("/api/refund_order", methods=["POST"])
@admin_required
def refund_order():
    order_id = (request.form.get("id") or "").strip()
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    if not order:
        return err("Order not found.", 404)
    # Razorpay refund API can be connected here when live credentials are ready.
    db.execute(
        "UPDATE orders SET status='refunded', fulfillment_status='returned' WHERE id=?",
        (order_id,),
    )
    db.commit()
    log_audit(
        "order.refunded",
        actor_id=current_user().get("id"),
        ip_address=request.remote_addr,
        order_id=order_id,
    )
    return ok("Order marked refunded.")


@api_bp.route("/api/razorpay/webhook", methods=["POST"])
def razorpay_webhook():
    """Verify Razorpay webhooks and update known order state."""
    secret = current_app.config.get("RAZORPAY_WEBHOOK_SECRET")
    if not secret:
        return err("Razorpay webhook is not configured.", 501)

    signature = request.headers.get("X-Razorpay-Signature", "")
    body = request.get_data() or b""
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        log_audit("payment.webhook_invalid_signature", ip_address=request.remote_addr)
        return err("Invalid webhook signature.", 401)

    payload = request.get_json(silent=True) or {}
    event = payload.get("event", "")
    payment = ((payload.get("payload") or {}).get("payment") or {}).get("entity") or {}
    payment_id = payment.get("id")
    if payment_id and event in {"payment.captured", "payment.failed"}:
        status = "completed" if event == "payment.captured" else "payment_failed"
        db = get_db()
        db.execute(
            "UPDATE orders SET status=? WHERE razorpay_payment_id=?",
            (status, payment_id),
        )
        db.commit()
    log_audit(
        "payment.razorpay_webhook",
        ip_address=request.remote_addr,
        event=event,
        payment_id=payment_id,
    )
    return ok("Webhook received.")


# ── Paytm Endpoints (Full verification) ───────────────────────


@api_bp.route("/api/create_paytm_order", methods=["POST"])
@jwt_required
def create_paytm_order():
    """Create a Paytm order. Returns order_id and txnToken."""
    return err(
        "Paytm checkout requires merchant credentials and frontend activation.", 501
    )

    try:
        total_amount = float(request.form.get("total_amount") or 0)
    except ValueError:
        return err("Invalid amount.")

    order_id = gen_id()

    # In production, call Paytm's Initiate Transaction API here
    # For now, return a mock token that the frontend can use
    # The real implementation would:
    # 1. Generate checksum with merchant key
    # 2. Call Paytm API to get txnToken
    # 3. Return txnToken to frontend

    txn_token = "paytm_txn_token_" + order_id

    return jsonify(
        {
            "ok": True,
            "order_id": order_id,
            "txnToken": txn_token,
            "amount": total_amount,
            "mid": current_app.config["PAYTM_MERCHANT_ID"],
        }
    )


@api_bp.route("/api/verify_paytm", methods=["POST"])
@jwt_required
def verify_paytm():
    """Verify Paytm payment with checksum validation and create order."""
    return err(
        "Paytm checkout requires merchant credentials and frontend activation.", 501
    )

    name = (request.form.get("name") or "").strip()
    address = (request.form.get("address") or "").strip()
    email = (request.form.get("email") or "").strip()
    phone = (request.form.get("phone") or "").strip()

    try:
        total_amount = float(request.form.get("total_amount") or 0)
    except ValueError:
        total_amount = 0.0

    order_id = request.form.get("order_id")
    paytm_txn_id = request.form.get("txnId")  # Paytm transaction ID
    paytm_checksum = request.form.get("checksumhash")

    if not order_id:
        return err("Missing order ID.")

    # Verify Paytm checksum
    # In production, use paytmchecksum.verifySignature() with all response params
    # For now, we'll validate if checksum is provided
    if paytm_checksum:
        # Reconstruct params for verification
        params = {
            "ORDERID": order_id,
            "TXNAMOUNT": str(total_amount),
            "TXNID": paytm_txn_id or "",
            "STATUS": "TXN_SUCCESS",
            # Add other required params
        }
        try:
            # Verify signature
            is_valid = paytmchecksum.verifySignature(
                params, current_app.config["PAYTM_MERCHANT_KEY"], paytm_checksum
            )
            if not is_valid:
                return err("Invalid Paytm checksum")
        except Exception:
            return err("Paytm verification failed")

    # Idempotency check
    db = get_db()
    if paytm_txn_id:
        existing = db.execute(
            "SELECT id FROM orders WHERE paytm_txn_id = ?", (paytm_txn_id,)
        ).fetchone()
        if existing:
            return ok("Order already processed.", order_id=existing["id"])

    import uuid

    order_token = str(uuid.uuid4())
    new_order_id = gen_id()

    db.execute(
        """INSERT INTO orders (id, name, address, total_amount, payment_method,
                              paytm_txn_id, order_token, customer_email, customer_phone, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            new_order_id,
            name,
            address,
            total_amount,
            "paytm",
            paytm_txn_id,
            order_token,
            email,
            phone,
            "completed",
        ),
    )
    db.commit()

    try:
        send_order_notifications(new_order_id, name, email, phone, total_amount)
    except Exception:
        pass

    return ok("Order completed.", order_id=new_order_id, order_token=order_token)


# ── Notification Helpers ──────────────────────────────────────


def send_order_notifications(
    order_id: str, name: str, email: str, phone: str, total: float
):
    """Send order confirmation via email and/or SMS."""
    # Email via SendGrid
    if current_app.config.get("SENDGRID_API_KEY") and email:
        try:
            import sendgrid
            from sendgrid.helpers.mail import Content, Email, Mail, To

            sg = sendgrid.SendGridAPIClient(
                api_key=current_app.config["SENDGRID_API_KEY"]
            )
            from_email = Email(current_app.config["SENDGRID_FROM_EMAIL"])
            to_email = To(email)
            subject = f"Order Confirmation - #{order_id[:8]}"
            content = Content(
                "text/html",
                f"""
                <h2>Thank you for your order, {name}!</h2>
                <p>Your order <strong>#{order_id[:8]}</strong> has been confirmed.</p>
                <p>Total: ₹{total:.2f}</p>
                <p>We'll notify you when your order ships.</p>
            """,
            )
            mail = Mail(from_email, to_email, subject, content)
            attrgetter("mail.send.post")(sg.client)(request_body=mail.get())
        except Exception:
            pass  # Log in production

    # SMS via Twilio
    if current_app.config.get("TWILIO_ACCOUNT_SID") and phone:
        try:
            from twilio.rest import Client

            client = Client(
                current_app.config["TWILIO_ACCOUNT_SID"],
                current_app.config["TWILIO_AUTH_TOKEN"],
            )
            client.messages.create(
                body=f"Order #{order_id[:8]} confirmed. Total: ₹{total:.2f}. Thank you!",
                from_=current_app.config["TWILIO_FROM_NUMBER"],
                to=phone,
            )
        except Exception:
            pass  # Log in production
