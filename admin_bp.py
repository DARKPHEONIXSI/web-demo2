"""
admin.py — Admin dashboard blueprint for the On Ice skating blog.
All routes require admin authentication.
"""

import json
import csv
import io

# pyrefly: ignore [missing-import]
from flask import Blueprint, Response, current_app, make_response, redirect, render_template, request, url_for

# pyrefly: ignore [missing-import]
from werkzeug.security import check_password_hash

from auth import get_sess, is_admin, set_auth_cookies, set_sess
from models import (
    create_access_token,
    create_refresh_token,
    ensure_builtin_admin_user,
    fmt_date,
    get_db,
    get_settings,
    store_tokens,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
def admin_index():
    """Admin dashboard entry point."""
    if not is_admin():
        return redirect(url_for("admin.admin_login"))

    db = get_db()
    sec = request.args.get("sec", "dashboard")
    edit_id = request.args.get("edit", "")
    edit_pg = request.args.get("editpage", "")

    if edit_id:
        sec = "edit_post"
    if edit_pg:
        sec = "edit_page"

    # Load data
    s = get_settings()
    posts = db.execute(
        "SELECT id, title, post_date, pinned, read_time, status FROM posts ORDER BY post_date DESC"
    ).fetchall()
    techs = db.execute(
        "SELECT id, title, icon, sort_order FROM techniques ORDER BY sort_order"
    ).fetchall()
    users = db.execute(
        "SELECT id, username, role, is_google, created_at FROM users ORDER BY created_at DESC"
    ).fetchall()
    pages = db.execute(
        "SELECT id, name, slug FROM custom_pages ORDER BY created_at DESC"
    ).fetchall()

    try:
        gallery = db.execute(
            "SELECT id, emoji, title, description, tag, image_path, sort_order FROM gallery_items ORDER BY sort_order"
        ).fetchall()
    except Exception:
        gallery = []

    try:
        products = db.execute(
            "SELECT * FROM products ORDER BY created_at DESC"
        ).fetchall()
        low_stock = db.execute(
            "SELECT id, name, stock_quantity FROM products WHERE status='active' AND stock_quantity <= 5 ORDER BY stock_quantity ASC LIMIT 10"
        ).fetchall()
        revenue = db.execute(
            "SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE status='completed'"
        ).fetchone()[0]
        media_items = db.execute(
            "SELECT * FROM media_library ORDER BY uploaded_at DESC"
        ).fetchall()
        social_tokens = db.execute("SELECT * FROM social_tokens").fetchall()
    except Exception:
        products = []
        low_stock = []
        revenue = 0
        media_items = []
        social_tokens = []

    try:
        messages = db.execute(
            "SELECT * FROM contact_messages ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
        unread_count = db.execute(
            "SELECT COUNT(*) FROM contact_messages WHERE is_read=0"
        ).fetchone()[0]
    except Exception:
        messages = []
        unread_count = 0

    # Edit targets
    edit_post = None
    edit_page = None
    edit_product = None
    product_variants = []
    product_images = []
    if edit_id:
        edit_post = db.execute(
            "SELECT * FROM posts WHERE id=? LIMIT 1", (edit_id,)
        ).fetchone()
    if edit_pg:
        edit_page = db.execute(
            "SELECT * FROM custom_pages WHERE id=? LIMIT 1", (edit_pg,)
        ).fetchone()
    edit_prod_id = request.args.get("editproduct")
    if edit_prod_id:
        sec = "new_product"
        edit_product = db.execute(
            "SELECT * FROM products WHERE id=? LIMIT 1", (edit_prod_id,)
        ).fetchone()
        product_variants = db.execute(
            "SELECT * FROM product_variants WHERE product_id=? ORDER BY color, size",
            (edit_prod_id,),
        ).fetchall()
        product_images = db.execute(
            "SELECT * FROM product_images WHERE product_id=? ORDER BY sort_order",
            (edit_prod_id,),
        ).fetchall()

    # Full technique data for JS editing
    techs_full = db.execute("SELECT * FROM techniques ORDER BY sort_order").fetchall()
    techs_json = {t["id"]: dict(t) for t in techs_full}

    # Gallery data for JS editing
    gallery_json = {g["id"]: dict(g) for g in gallery}

    return render_template(
        "admin/dashboard.html",
        settings=s,
        sess=get_sess(),
        sec=sec,
        posts=posts,
        techs=techs,
        users=users,
        pages=pages,
        gallery=gallery,
        messages=messages,
        products=products,
        media_items=media_items,
        social_tokens=social_tokens,
        unread_count=unread_count,
        edit_post=edit_post,
        edit_page=edit_page,
        edit_product=edit_product,
        product_variants=product_variants,
        product_images=product_images,
        techs_json=json.dumps(techs_json),
        gallery_json=json.dumps(gallery_json),
        post_count=len(posts),
        tech_count=len(techs),
        user_count=len(users),
        page_count=len(pages),
        gallery_count=len(gallery),
        product_count=len(products),
        revenue=revenue,
        low_stock=low_stock,
        fmt_date=fmt_date,
    )


@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():
    """Admin login page."""
    s = get_settings()
    login_err = ""

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        # Check hardcoded admin via secure hash comparison
        if username == current_app.config["ADMIN_USER"]:
            if check_password_hash(current_app.config["ADMIN_PASS_HASH"], password):
                ensure_builtin_admin_user()
                access_token, access_expires = create_access_token("admin", "admin")
                refresh_token, refresh_expires = create_refresh_token("admin")
                store_tokens(
                    "admin", access_token, access_expires, refresh_token, refresh_expires
                )
                set_sess({"role": "admin", "username": "Admin", "id": "admin"})
                response = make_response(redirect(url_for("admin.admin_index")))
                set_auth_cookies(response, access_token, refresh_token)
                return response

        # Check DB admins
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username=? AND role='admin' AND is_google=0 LIMIT 1",
            (username,),
        ).fetchone()
        if user and check_password_hash(user["password"], password):
            access_token, access_expires = create_access_token(user["id"], user["role"])
            refresh_token, refresh_expires = create_refresh_token(user["id"])
            store_tokens(
                user["id"], access_token, access_expires, refresh_token, refresh_expires
            )
            set_sess({"role": "admin", "username": user["username"], "id": user["id"]})
            response = make_response(redirect(url_for("admin.admin_index")))
            set_auth_cookies(response, access_token, refresh_token)
            return response

        current_app.logger.warning(
            "failed admin login for username %r from %s", username, request.remote_addr
        )
        login_err = "Incorrect credentials."

    return render_template("admin/login.html", settings=s, login_err=login_err)


@admin_bp.route("/marketplace")
def admin_marketplace():
    """Demo marketplace for Sir's Skates. Admin only."""
    if not is_admin():
        return redirect(url_for("admin.admin_login"))

    s = get_settings()
    return render_template("admin/marketplace.html", settings=s)


@admin_bp.route("/orders")
def admin_orders():
    """Order management dashboard. Admin only."""
    if not is_admin():
        return redirect(url_for("admin.admin_login"))

    db = get_db()
    orders = db.execute(
        "SELECT * FROM orders ORDER BY created_at DESC LIMIT 100"
    ).fetchall()
    order_items = {}
    for order in orders:
        order_items[order["id"]] = db.execute(
            """SELECT oi.*, p.name AS product_name, pv.color, pv.size
               FROM order_items oi
               LEFT JOIN products p ON p.id = oi.product_id
               LEFT JOIN product_variants pv ON pv.id = oi.product_variant_id
               WHERE oi.order_id=?""",
            (order["id"],),
        ).fetchall()
    audit_logs = db.execute(
        "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 50"
    ).fetchall()
    return render_template(
        "admin/orders.html",
        settings=get_settings(),
        orders=orders,
        order_items=order_items,
        audit_logs=audit_logs,
    )


@admin_bp.route("/orders/export.csv")
def export_orders_csv():
    """Export orders as CSV. Admin only."""
    if not is_admin():
        return redirect(url_for("admin.admin_login"))
    db = get_db()
    rows = db.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "created_at", "name", "email", "phone", "total", "payment_status", "fulfillment", "tracking"])
    for r in rows:
        writer.writerow([r["id"], r["created_at"], r["name"], r["customer_email"], r["customer_phone"], r["total_amount"], r["status"], r["fulfillment_status"], r["tracking_number"]])
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=orders.csv"})
