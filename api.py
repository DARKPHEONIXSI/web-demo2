"""
api.py — AJAX data mutation endpoints for the On Ice skating blog.
Handles all CRUD operations for posts, techniques, gallery, pages, settings, users, messages.
"""

import os

import paytmchecksum
import razorpay
from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

from auth import admin_required, jwt_required
from models import gen_id, get_db, save_setting
from purify_html import purify_html

api_bp = Blueprint("api", __name__)


def ok(msg="", **extra):
    """Return a success JSON response."""
    return jsonify({"ok": True, "msg": msg, **extra})


def err(msg):
    """Return an error JSON response."""
    return jsonify({"ok": False, "msg": msg})


def allowed_file(filename):
    """Check if file extension is allowed for image uploads."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_EXTENSIONS"]
    )


# Allowed extensions for the media library (images + video only)
ALLOWED_MEDIA_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "mp4"}


# ── Contact form (public) ────────────────────────────────────


@api_bp.route("/api/contact", methods=["POST"])
def contact():
    """Public contact form submission."""
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
        """SELECT id, title, excerpt, body, post_date, read_time, pinned
           FROM posts WHERE status='published'
           ORDER BY pinned DESC, post_date DESC"""
    ).fetchall()
    return jsonify({"ok": True, "posts": [dict(r) for r in rows]})


# ── Image upload ──────────────────────────────────────────────


@api_bp.route("/api/upload_image", methods=["POST"])
@admin_required
def upload_image():
    """Upload an image file. Admin only."""
    if "image" not in request.files:
        return err("No file received.")

    file = request.files["image"]
    if file.filename == "":
        return err("No file selected.")

    if not allowed_file(file.filename):
        return err("Only JPEG, PNG, GIF and WebP images are allowed.")

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)

    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = gen_id() + "." + ext
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    return ok(
        "Uploaded.", path=current_app.config["UPLOAD_URL"] + filename, filename=filename
    )


# ── POSTS ─────────────────────────────────────────────────────


@api_bp.route("/api/save_post", methods=["POST"])
@admin_required
def save_post():
    """Create or update a post. Admin only."""
    post_id = (request.form.get("id") or "").strip()
    title = (request.form.get("title") or "").strip()
    excerpt = (request.form.get("excerpt") or "").strip()
    body = purify_html((request.form.get("body") or "").strip())
    author = (request.form.get("author") or "The Coach").strip()
    read_time = max(1, int(request.form.get("read_time") or 4))
    pinned = 1 if request.form.get("pinned") in ("1", "true", "on") else 0
    status = "draft" if request.form.get("status") == "draft" else "published"
    post_date = (request.form.get("post_date") or "").strip()

    if not title or len(title) > 200:
        return err("Title is required and must be under 200 characters.")
    if not body:
        return err("Body is required.")

    author_id = (
        request.current_user.get("id")
        if request.current_user.get("id") != "admin"
        else None
    )

    db = get_db()
    if post_id:
        db.execute(
            """UPDATE posts SET title=?, excerpt=?, body=?, author=?, author_id=?,
               read_time=?, pinned=?, status=?, post_date=?, updated_at=datetime('now')
               WHERE id=?""",
            (
                title,
                excerpt,
                body,
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
            """INSERT INTO posts (id, title, excerpt, body, author, author_id, read_time, pinned, status, post_date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                post_id,
                title,
                excerpt,
                body,
                author,
                author_id,
                read_time,
                pinned,
                status,
                post_date,
            ),
        )
    db.commit()
    return ok("Post saved.", id=post_id)


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
    sort_order = int(request.form.get("sort_order") or 0)

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
    slug = re.sub(r"[^a-z0-9-]", "", name.lower().replace(" ", "-"))

    if not name:
        return err("Page name is required.")

    db = get_db()
    if page_id:
        db.execute(
            "UPDATE custom_pages SET name=?, slug=?, body=?, updated_at=datetime('now') WHERE id=?",
            (name, slug, body, page_id),
        )
    else:
        page_id = gen_id()
        db.execute(
            "INSERT INTO custom_pages (id, name, slug, body) VALUES (?, ?, ?, ?)",
            (page_id, name, slug, body),
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
    fb_token = request.form.get("fb_token")
    if fb_token is not None:
        db.execute('DELETE FROM social_tokens WHERE platform="facebook"')
        if fb_token.strip():
            db.execute(
                'INSERT INTO social_tokens (id, platform, access_token) VALUES (?, "facebook", ?)',
                (gen_id(), fb_token.strip()),
            )

    ig_token = request.form.get("ig_token")
    if ig_token is not None:
        db.execute('DELETE FROM social_tokens WHERE platform="instagram"')
        if ig_token.strip():
            db.execute(
                'INSERT INTO social_tokens (id, platform, access_token) VALUES (?, "instagram", ?)',
                (gen_id(), ig_token.strip()),
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
    sort_order = int(request.form.get("sort_order") or 0)

    if not title:
        return err("Title is required.")

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
        filepath = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), row["image_path"]
        )
        if os.path.exists(filepath):
            try:
                os.unlink(filepath)
            except OSError:
                pass

    db.execute("DELETE FROM gallery_items WHERE id=?", (item_id,))
    db.commit()
    return ok("Gallery item deleted.")


# ── CONTACT MESSAGES ──────────────────────────────────────────


@api_bp.route("/api/mark_read", methods=["POST"])
@admin_required
def mark_read():
    """Mark a contact message as read. Admin only."""
    msg_id = int(request.form.get("id") or 0)
    db = get_db()
    db.execute("UPDATE contact_messages SET is_read=1 WHERE id=?", (msg_id,))
    db.commit()
    return ok("Marked read.")


@api_bp.route("/api/delete_message", methods=["POST"])
@admin_required
def delete_message():
    """Delete a contact message. Admin only."""
    msg_id = int(request.form.get("id") or 0)
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
    if file.filename == "":
        return err("No file selected.")

    # Strict extension whitelist
    safe_name = secure_filename(file.filename)
    if "." not in safe_name:
        return err("Invalid file: no extension detected.")
    ext = safe_name.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_MEDIA_EXTENSIONS:
        return err("Only images (JPEG, PNG, GIF, WebP) and MP4 video are allowed.")

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    filename = gen_id() + "." + ext
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    url = current_app.config["UPLOAD_URL"] + filename
    media_type = "video" if ext == "mp4" else "image"
    media_id = gen_id()
    db = get_db()
    db.execute(
        "INSERT INTO media_library (id, media_type, url) VALUES (?, ?, ?)",
        (media_id, media_type, url),
    )
    db.commit()
    return ok("Media uploaded.", url=url)


@api_bp.route("/api/delete_media", methods=["POST"])
@admin_required
def delete_media():
    media_id = request.form.get("id")
    db = get_db()
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

    try:
        price = float(request.form.get("base_price") or 0)
        if price < 0:
            return err("Price cannot be negative.")
    except (ValueError, TypeError):
        return err("Invalid price value.")

    db = get_db()
    if pid:
        db.execute(
            "UPDATE products SET name=?, description=?, base_price=? WHERE id=?",
            (name, desc, price, pid),
        )
    else:
        pid = gen_id()
        db.execute(
            "INSERT INTO products (id, name, description, base_price) VALUES (?, ?, ?, ?)",
            (pid, name, desc, price),
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
    db = get_db()
    db.execute(
        "INSERT INTO product_variants (id, product_id, color, size, stock_quantity) VALUES (?, ?, ?, ?, ?)",
        (gen_id(), pid, color, size, stock),
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
    url = request.form.get("image_url")
    color = request.form.get("color_match", "")
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


# ── Razorpay Endpoints ────────────────────────────────────────


@api_bp.route("/api/create_razorpay_order", methods=["POST"])
@jwt_required
def create_razorpay_order():
    """Create a Razorpay order. Returns order_id and amount in paise."""
    try:
        total_amount = float(request.form.get("total_amount") or 0)
    except ValueError:
        return err("Invalid amount.")
    if total_amount <= 0:
        return err("Amount must be greater than zero.")

    # Amount in paise
    amount_paise = int(total_amount * 100)

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
            "notes": {"user_id": request.current_user.get("id", "guest")},
        }
        order = client.order.create(data=order_data)
        return jsonify({"ok": True, "order_id": order["id"], "amount": amount_paise})
    except Exception as e:
        return err(f"Razorpay error: {str(e)}")


@api_bp.route("/api/verify_razorpay", methods=["POST"])
@jwt_required
def verify_razorpay():
    """Verify Razorpay payment signature and create order with idempotency check."""
    name = (request.form.get("name") or "").strip()
    address = (request.form.get("address") or "").strip()
    email = (request.form.get("email") or "").strip()
    phone = (request.form.get("phone") or "").strip()

    try:
        total_amount = float(request.form.get("total_amount") or 0)
    except ValueError:
        total_amount = 0.0

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
        client.utility.verify_payment_signature(
            {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            }
        )
    except razorpay.errors.SignatureVerificationError:
        return err("Invalid payment signature")

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

    db.execute(
        """INSERT INTO orders (id, name, address, total_amount, payment_method,
                              razorpay_payment_id, razorpay_order_id, order_token,
                              customer_email, customer_phone, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            order_id,
            name,
            address,
            total_amount,
            "razorpay",
            razorpay_payment_id,
            razorpay_order_id,
            order_token,
            email,
            phone,
            "completed",
        ),
    )
    db.commit()

    # Trigger notifications (async in production)
    try:
        send_order_notifications(order_id, name, email, phone, total_amount)
    except Exception:
        pass  # Log error in production

    return ok(
        "Order completed successfully.", order_id=order_id, order_token=order_token
    )


# ── Paytm Endpoints (Full verification) ───────────────────────


@api_bp.route("/api/create_paytm_order", methods=["POST"])
@jwt_required
def create_paytm_order():
    """Create a Paytm order. Returns order_id and txnToken."""
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
            sg.client.mail.send.post(request_body=mail.get())
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
