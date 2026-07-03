"""
admin.py — Admin dashboard blueprint for the On Ice skating blog.
All routes require admin authentication.
"""

import json

# pyrefly: ignore [missing-import]
from flask import Blueprint, current_app, redirect, render_template, request, url_for

# pyrefly: ignore [missing-import]
from werkzeug.security import check_password_hash

from auth import get_sess, is_admin, set_sess
from models import fmt_date, get_db, get_settings

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
        media_items = db.execute(
            "SELECT * FROM media_library ORDER BY uploaded_at DESC"
        ).fetchall()
        social_tokens = db.execute("SELECT * FROM social_tokens").fetchall()
    except Exception:
        products = []
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
                set_sess({"role": "admin", "username": "Admin", "id": "admin"})
                return redirect(url_for("admin.admin_index"))

        # Check DB admins
        db = get_db()
        user = db.execute(
            'SELECT * FROM users WHERE username=? AND role="admin" AND is_google=0 LIMIT 1',
            (username,),
        ).fetchone()
        if user and check_password_hash(user["password"], password):
            set_sess({"role": "admin", "username": user["username"], "id": user["id"]})
            return redirect(url_for("admin.admin_index"))

        login_err = "Incorrect credentials."

    return render_template("admin/login.html", settings=s, login_err=login_err)


@admin_bp.route("/marketplace")
def admin_marketplace():
    """Demo marketplace for Sir's Skates. Admin only."""
    if not is_admin():
        return redirect(url_for("admin.admin_login"))

    s = get_settings()
    return render_template("admin/marketplace.html", settings=s)
