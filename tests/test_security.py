import hashlib
import hmac
import io
import json
import re
import html
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash

import auth as auth_module
from app import create_app
from config import Config
from models import get_db, init_db


@pytest.fixture()
def app(tmp_path, monkeypatch):
    admin_hash = generate_password_hash("adminpass")
    monkeypatch.setenv("ADMIN_PASS_HASH", generate_password_hash("adminpass"))
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-that-is-long-enough")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-key-that-is-long-enough")
    Config.DATABASE_PATH = str(tmp_path / "test.db")
    Config.DATABASE_URL = ""
    Config.ADMIN_PASS_HASH = admin_hash
    Config.SECRET_KEY = "test-secret-key-that-is-long-enough"
    Config.JWT_SECRET_KEY = "test-jwt-secret-key-that-is-long-enough"
    test_app = create_app()
    test_app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        GOOGLE_CLIENT_ID="client-id.apps.googleusercontent.com",
        RATELIMIT_ENABLED=False,
        DATABASE_URL="",
    )
    with test_app.app_context():
        init_db()
        db = get_db()
        db.execute(
            "INSERT INTO products (id, name, description, base_price, stock_quantity) VALUES (?, ?, ?, ?, ?)",
            ("prod_test", "Test Skates", "", 1234.0, 10),
        )
        db.commit()
    return test_app


@pytest.fixture()
def client(app):
    return app.test_client()


def test_register_login_logout(client):
    r = client.post(
        "/auth/register",
        data={"username": "alice", "password": "secret1", "password2": "secret1"},
    )
    assert r.status_code == 200
    assert r.json["ok"] is True

    r = client.post("/auth/logout")
    assert r.status_code == 200
    assert r.json["ok"] is True

    r = client.post("/auth/login", data={"username": "alice", "password": "secret1"})
    assert r.status_code == 200
    assert r.json["ok"] is True


def test_google_bad_token_rejected(client):
    r = client.post("/auth/google", data={"credential": "bad-token"})
    assert r.status_code == 401
    assert r.json["ok"] is False


def test_google_success_mock(client, monkeypatch):
    def fake_verify(token, request, client_id):
        return {
            "aud": client_id,
            "email": "g@example.com",
            "email_verified": True,
            "name": "Google User",
        }

    monkeypatch.setattr(auth_module.google_id_token, "verify_oauth2_token", fake_verify)
    r = client.post("/auth/google", data={"credential": "valid-token"})
    assert r.status_code == 200
    assert r.json["ok"] is True


def test_csrf_blocks_admin_api_when_enabled(app):
    app.config["WTF_CSRF_ENABLED"] = True
    client = app.test_client()
    client.post("/auth/login", data={"username": "sir", "password": "adminpass"})
    r = client.post("/api/delete_post", data={"id": "p1"})
    assert r.status_code == 400


def test_checkout_pricing_tamper_protection(app):
    with app.app_context():
        from api import calculate_cart_total

        db = get_db()
        product = db.execute("SELECT id, base_price FROM products LIMIT 1").fetchone()
        assert product is not None
        cart = json.dumps([{"product_id": product["id"], "price": 1, "quantity": 2}])
        total, items, error = calculate_cart_total(cart)
        assert error is None
        assert total == float(product["base_price"]) * 2
        assert items[0]["unit_price"] == float(product["base_price"])


def test_order_item_persistence_schema(app):
    with app.app_context():
        db = get_db()
        cols = [r[1] for r in db.execute("PRAGMA table_info(order_items)").fetchall()]
        assert "product_id" in cols
        assert "product_variant_id" in cols


def test_blog_and_product_schema_fields(app):
    with app.app_context():
        db = get_db()
        post_cols = [r[1] for r in db.execute("PRAGMA table_info(posts)").fetchall()]
        product_cols = [
            r[1] for r in db.execute("PRAGMA table_info(products)").fetchall()
        ]
        order_cols = [r[1] for r in db.execute("PRAGMA table_info(orders)").fetchall()]
        for col in [
            "cover_image",
            "category",
            "tags",
            "slug",
            "seo_title",
            "seo_description",
        ]:
            assert col in post_cols
        for col in [
            "category",
            "badge",
            "sku",
            "status",
            "stock_quantity",
            "sale_price",
            "seo_title",
            "seo_description",
        ]:
            assert col in product_cols
        for col in [
            "user_id",
            "shipping_amount",
            "tax_amount",
            "tracking_number",
            "fulfillment_status",
        ]:
            assert col in order_cols


def test_shop_checkout_and_quote(client):
    assert client.get("/shop").status_code == 200
    checkout = client.get("/checkout")
    assert checkout.status_code == 200
    assert b"Sign in to checkout" in checkout.data

    cart = json.dumps([{"product_id": "prod_test", "price": 1, "quantity": 2}])
    quote = client.post("/api/cart/quote", data={"cart": cart})
    assert quote.status_code == 200
    assert quote.json["ok"] is True
    assert quote.json["subtotal_amount"] == 2468.0
    assert quote.json["shipping_amount"] == 199.0
    assert quote.json["tax_amount"] == 444.24
    assert quote.json["total_amount"] == 3111.24


def test_admin_product_save_fields(client):
    client.post("/auth/login", data={"username": "sir", "password": "adminpass"})
    r = client.post(
        "/api/save_product",
        data={
            "name": "Elite Boot",
            "description": "<p>Fast</p>",
            "category": "Skates",
            "badge": "New",
            "sku": "ELITE-001",
            "status": "active",
            "stock_quantity": "5",
            "base_price": "1000",
            "sale_price": "900",
            "seo_title": "Elite Boot SEO",
            "seo_description": "SEO description",
        },
    )
    assert r.status_code == 200
    assert r.json["ok"] is True


def test_order_tracking_and_profile_history(client, app):
    client.post(
        "/auth/register",
        data={"username": "buyer", "password": "secret1", "password2": "secret1"},
    )
    with app.app_context():
        db = get_db()
        user = db.execute(
            "SELECT id FROM users WHERE username=?", ("buyer",)
        ).fetchone()
        assert user is not None
        db.execute(
            """INSERT INTO orders (id, user_id, name, address, total_amount, shipping_amount, tax_amount,
               payment_method, status, fulfillment_status, tracking_number, order_token)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "ord_test",
                user["id"],
                "Buyer",
                "Address",
                100.0,
                0.0,
                0.0,
                "razorpay",
                "completed",
                "shipped",
                "TRK123",
                "tok_test",
            ),
        )
        db.execute(
            "INSERT INTO order_items (id, order_id, product_id, quantity, price_at_time) VALUES (?, ?, ?, ?, ?)",
            ("oi_test", "ord_test", "prod_test", 1, 100.0),
        )
        db.commit()
    tracking = client.get("/order/tok_test")
    assert tracking.status_code == 200
    assert b"TRK123" in tracking.data
    profile = client.get("/profile")
    assert profile.status_code == 200
    assert b"Order History" in profile.data


def test_seo_legal_and_feeds(client):
    for path in [
        "/sitemap.xml",
        "/robots.txt",
        "/feed.xml",
        "/privacy",
        "/terms",
        "/shipping-returns",
        "/refund-policy",
        "/payment-failed",
    ]:
        r = client.get(path)
        assert r.status_code == 200
    assert b"sitemap" in client.get("/robots.txt").data.lower()
    assert b"<rss" in client.get("/feed.xml").data


def test_feed_escapes_xml_content(client, app):
    with app.app_context():
        db = get_db()
        db.execute(
            """INSERT INTO posts (id, title, excerpt, body, status, slug, post_date)
               VALUES (?, ?, ?, ?, ?, ?, date('now'))""",
            (
                "post_xml",
                "Bad <title> & data",
                "Excerpt <bad> & data",
                "<p>Body</p>",
                "published",
                "bad-xml",
            ),
        )
        db.commit()

    response = client.get("/feed.xml")

    assert response.status_code == 200
    ET.fromstring(response.data)


def test_home_rejects_invalid_page_query(client):
    response = client.get("/?page=abc")

    assert response.status_code == 400


def test_blog_archive_comment_and_slug(client, app):
    with app.app_context():
        post = (
            get_db()
            .execute("SELECT id, slug FROM posts WHERE category <> '' LIMIT 1")
            .fetchone()
        )
    assert post is not None
    assert client.get(f"/post/{post['slug']}").status_code == 200
    assert client.get("/category/Training").status_code == 200
    assert client.get("/tag/practice").status_code == 200
    r = client.post(
        "/api/comment",
        data={"post_id": post["id"], "name": "Reader", "body": "Great post"},
    )
    assert r.status_code == 200
    assert r.json["ok"] is True


def test_coupon_and_out_of_stock(client, app):
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO coupons (code, discount_type, discount_value) VALUES (?, ?, ?)",
            ("SAVE10", "percent", 10),
        )
        db.execute(
            "INSERT INTO products (id, name, description, base_price, stock_quantity) VALUES (?, ?, ?, ?, ?)",
            ("sold_out", "Sold Out", "", 100.0, 0),
        )
        db.commit()
    cart = json.dumps([{"product_id": "prod_test", "quantity": 1}])
    quote = client.post("/api/cart/quote", data={"cart": cart, "coupon": "SAVE10"})
    assert quote.status_code == 200
    assert quote.json["discount_amount"] == 123.4
    sold_out = client.post(
        "/api/cart/quote",
        data={"cart": json.dumps([{"product_id": "sold_out", "quantity": 1}])},
    )
    assert sold_out.status_code == 400


def test_review_wishlist_and_server_cart(client):
    client.post(
        "/auth/register",
        data={"username": "shopper", "password": "secret1", "password2": "secret1"},
    )
    review = client.post(
        "/api/review",
        data={"product_id": "prod_test", "rating": "5", "body": "Excellent"},
    )
    assert review.status_code == 200
    wish = client.post("/api/wishlist/toggle", data={"product_id": "prod_test"})
    assert wish.status_code == 200
    assert wish.json["wished"] is True
    cart = json.dumps([{"product_id": "prod_test", "quantity": 1}])
    saved = client.post("/api/cart/save", data={"cart": cart})
    assert saved.status_code == 200
    loaded = client.get("/api/cart/load")
    assert loaded.status_code == 200
    assert loaded.json["cart"][0]["product_id"] == "prod_test"


def test_ugc_endpoints_reject_missing_parent_rows(client, app):
    client.post(
        "/auth/register",
        data={"username": "orphan-check", "password": "secret1", "password2": "secret1"},
    )

    comment = client.post(
        "/api/comment",
        data={"post_id": "missing_post", "name": "Reader", "body": "orphan"},
    )
    review = client.post(
        "/api/review",
        data={"product_id": "missing_prod", "rating": "5", "body": "orphan"},
    )
    wishlist = client.post("/api/wishlist/toggle", data={"product_id": "missing_prod"})

    assert comment.status_code == 404
    assert review.status_code == 404
    assert wishlist.status_code == 404
    with app.app_context():
        db = get_db()
        comment_count = db.execute(
            "SELECT COUNT(*) FROM post_comments WHERE post_id='missing_post'"
        ).fetchone()
        review_count = db.execute(
            "SELECT COUNT(*) FROM product_reviews WHERE product_id='missing_prod'"
        ).fetchone()
        wishlist_count = db.execute(
            "SELECT COUNT(*) FROM wishlist_items WHERE product_id='missing_prod'"
        ).fetchone()
        assert comment_count is not None
        assert review_count is not None
        assert wishlist_count is not None
        assert comment_count[0] == 0
        assert review_count[0] == 0
        assert wishlist_count[0] == 0


def test_product_variant_values_do_not_break_inline_javascript(client, app):
    with app.app_context():
        db = get_db()
        db.execute(
            """INSERT INTO product_variants (id, product_id, color, size, stock_quantity)
               VALUES (?, ?, ?, ?, ?)""",
            ("var_xss", "prod_test", "x');alert(1)//", "L');alert(2)//", 5),
        )
        db.commit()

    response = client.get("/shop/prod_test")
    decoded = html.unescape(response.get_data(as_text=True))

    assert response.status_code == 200
    assert "selectColor('x');alert(1)//')" not in decoded
    assert "selectSize('L');alert(2)//')" not in decoded


def test_shop_category_filter_does_not_break_inline_javascript(client, app):
    with app.app_context():
        db = get_db()
        db.execute(
            """INSERT INTO products (id, name, description, category, base_price, stock_quantity, status)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            ("prod_cat_xss", "Category Probe", "", "x');alert(2);//", 100.0, 5, "active"),
        )
        db.commit()

    decoded = html.unescape(client.get("/shop").get_data(as_text=True))

    assert "filterProducts('x');alert(2);//'" not in decoded
    assert "data-category-choice" in decoded


def test_gallery_uses_schema_field_names(client, app):
    with app.app_context():
        db = get_db()
        db.execute(
            """INSERT INTO gallery_items (id, title, tag, image_path, sort_order)
               VALUES (?, ?, ?, ?, ?)""",
            ("gal_probe", "Probe Image", "Training", "/static/images/pro_ice.png", 0),
        )
        db.commit()

    html_text = client.get("/gallery").get_data(as_text=True)

    assert 'data-category="Training"' in html_text
    assert 'src="/static/images/pro_ice.png"' in html_text


def test_gallery_tag_filter_does_not_break_inline_javascript(client, app):
    with app.app_context():
        db = get_db()
        db.execute(
            """INSERT INTO gallery_items (id, title, tag, image_path, sort_order)
               VALUES (?, ?, ?, ?, ?)""",
            ("gal_tag_xss", "Probe Image", "x');alert(3);//", "/static/images/pro_ice.png", 0),
        )
        db.commit()

    decoded = html.unescape(client.get("/gallery").get_data(as_text=True))

    assert "filterGallery('x');alert(3);//'" not in decoded
    assert "data-gallery-filter" in decoded


def test_profile_logout_uses_post(client):
    client.post(
        "/auth/register",
        data={"username": "profile-user", "password": "secret1", "password2": "secret1"},
    )

    html_text = client.get("/profile").get_data(as_text=True)

    assert "fetch('/auth/logout', { method: 'POST' })" in html_text


def test_password_change_revokes_existing_tokens(client):
    client.post(
        "/auth/register",
        data={"username": "pw-user", "password": "secret1", "password2": "secret1"},
    )
    old_access = client.get_cookie("access_token")
    assert old_access is not None

    changed = client.post(
        "/auth/change_password",
        data={"current": "secret1", "new": "secret2", "new2": "secret2"},
    )
    client.set_cookie("access_token", old_access.value)
    current_user_response = client.get("/auth/me")
    profile_response = client.get("/profile")

    assert changed.status_code == 200
    assert current_user_response.status_code == 401
    assert b"Your Profile" not in profile_response.data


def test_checkout_template_does_not_render_quote_names_with_inner_html(client):
    checkout_html = client.get("/checkout").get_data(as_text=True)

    assert "+ (item.name || 'Item') +" not in checkout_html
    assert "textContent = item.name || 'Item'" in checkout_html


def test_media_url_fields_reject_external_and_data_urls(client):
    client.post("/auth/login", data={"username": "sir", "password": "adminpass"})

    post = client.post(
        "/api/save_post",
        data={
            "title": "URL Probe",
            "body": "<p>Body</p>",
            "cover_image": "http://127.0.0.1:65535/track.png",
        },
    )
    gallery = client.post(
        "/api/save_gallery_item",
        data={
            "title": "Gallery URL Probe",
            "image_path": "data:image/svg+xml,<svg onload=alert(1)></svg>",
        },
    )
    product_image = client.post(
        "/api/save_prod_image",
        data={"product_id": "prod_test", "image_url": "http://127.0.0.1:65535/x.png"},
    )

    assert post.status_code == 400
    assert gallery.status_code == 400
    assert product_image.status_code == 400


def test_admin_order_update_export_and_refund(client, app):
    client.post("/auth/login", data={"username": "sir", "password": "adminpass"})
    with app.app_context():
        db = get_db()
        db.execute(
            """INSERT INTO orders (id, name, address, total_amount, payment_method, status, fulfillment_status, order_token)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "ord_admin",
                "Buyer",
                "Address",
                100.0,
                "razorpay",
                "completed",
                "pending",
                "tok_admin",
            ),
        )
        db.commit()
    update = client.post(
        "/api/update_order_status",
        data={
            "id": "ord_admin",
            "status": "completed",
            "fulfillment_status": "shipped",
            "tracking_number": "TRACK",
        },
    )
    assert update.status_code == 200
    export = client.get("/admin/orders/export.csv")
    assert export.status_code == 200
    assert b"ord_admin" in export.data
    refund = client.post("/api/refund_order", data={"id": "ord_admin"})
    assert refund.status_code == 200


def test_mocked_razorpay_checkout_success(client, app, monkeypatch):
    import api as api_module

    client.post(
        "/auth/register",
        data={"username": "paybuyer", "password": "secret1", "password2": "secret1"},
    )
    cart = json.dumps([{"product_id": "prod_test", "quantity": 1}])
    with app.app_context():
        subtotal, items, error = api_module.calculate_cart_total(cart)
        assert error is None
        totals = api_module.order_totals(subtotal)
        expected_amount = int(totals["total"] * 100)
        expected_hash = api_module.cart_hash(items)
        user = get_db().execute(
            "SELECT id FROM users WHERE username=?", ("paybuyer",)
        ).fetchone()
        assert user is not None

    class FakeUtility:
        def verify_payment_signature(self, payload):
            return True

    class FakePayment:
        def fetch(self, payment_id):
            return {
                "id": payment_id,
                "order_id": "rzp_order",
                "amount": expected_amount,
                "currency": "INR",
                "status": "captured",
            }

    class FakeOrder:
        def create(self, data):
            return {"id": "rzp_order", **data}

        def fetch(self, order_id):
            return {
                "id": order_id,
                "amount": expected_amount,
                "notes": {"cart_hash": expected_hash, "user_id": user["id"]},
            }

    class FakeClient:
        def __init__(self, auth):
            self.utility = FakeUtility()
            self.payment = FakePayment()
            self.order = FakeOrder()

    monkeypatch.setattr(api_module.razorpay, "Client", FakeClient)
    created = client.post("/api/create_razorpay_order", data={"cart": cart})
    assert created.status_code == 200
    verified = client.post(
        "/api/verify_razorpay",
        data={
            "cart": cart,
            "name": "Pay Buyer",
            "address": "Address",
            "email": "buyer@example.com",
            "phone": "9999999999",
            "razorpay_payment_id": "pay_1",
            "razorpay_order_id": "rzp_order",
            "razorpay_signature": "sig",
        },
    )
    assert verified.status_code == 200
    assert verified.json["ok"] is True


def test_razorpay_verify_rejects_provider_order_user_mismatch(client, app, monkeypatch):
    import api as api_module

    client.post(
        "/auth/register",
        data={"username": "pay-mismatch", "password": "secret1", "password2": "secret1"},
    )
    cart = json.dumps([{"product_id": "prod_test", "quantity": 1}])
    with app.app_context():
        subtotal, items, error = api_module.calculate_cart_total(cart)
        assert error is None
        totals = api_module.order_totals(subtotal)
        expected_amount = int(totals["total"] * 100)
        expected_hash = api_module.cart_hash(items)

    class FakeUtility:
        def verify_payment_signature(self, payload):
            return True

    class FakePayment:
        def fetch(self, payment_id):
            return {
                "id": payment_id,
                "order_id": "rzp_order_mismatch",
                "amount": expected_amount,
                "currency": "INR",
                "status": "captured",
            }

    class FakeOrder:
        def fetch(self, order_id):
            return {
                "id": order_id,
                "amount": expected_amount,
                "notes": {"cart_hash": expected_hash, "user_id": "different-user"},
            }

    class FakeClient:
        def __init__(self, auth):
            self.utility = FakeUtility()
            self.payment = FakePayment()
            self.order = FakeOrder()

    monkeypatch.setattr(api_module.razorpay, "Client", FakeClient)
    response = client.post(
        "/api/verify_razorpay",
        data={
            "cart": cart,
            "name": "Pay Buyer",
            "address": "Address",
            "email": "buyer@example.com",
            "phone": "9999999999",
            "razorpay_payment_id": "pay_mismatch",
            "razorpay_order_id": "rzp_order_mismatch",
            "razorpay_signature": "sig",
        },
    )

    assert response.status_code == 400


def test_upload_rejects_non_image(client):
    client.post("/auth/login", data={"username": "sir", "password": "adminpass"})
    r = client.post(
        "/api/upload_image",
        data={"image": (io.BytesIO(b"not an image"), "bad.png")},
        content_type="multipart/form-data",
    )
    assert r.status_code == 400
    assert r.json["ok"] is False


def test_upload_media_rejects_fake_mp4_without_magic(client, monkeypatch):
    import api as api_module

    client.post("/auth/login", data={"username": "sir", "password": "adminpass"})
    monkeypatch.setattr(api_module, "magic", None)

    response = client.post(
        "/api/upload_media",
        data={"media": (io.BytesIO(b"not really an mp4"), "probe.mp4")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400


def test_xss_sanitizer_removes_dangerous_markup():
    from purify_html import purify_html

    cleaned = purify_html(
        '<p style="color:red">Hi</p><script>alert(1)</script><img src="javascript:alert(2)">'
    )
    assert "script" not in cleaned.lower()
    assert "javascript:" not in cleaned.lower()
    assert "style=" not in cleaned.lower()


def test_production_config_exposes_environment(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    assert hasattr(Config, "FLASK_ENV")


def test_production_config_rejects_env_example_placeholders(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    config = {
        "SECRET_KEY": "x" * 32,
        "JWT_SECRET_KEY": "y" * 32,
        "ADMIN_PASS_HASH": "hash",
        "SESSION_COOKIE_SECURE": True,
        "JWT_COOKIE_SECURE": True,
        "DATABASE_URL": "postgresql://replace-user:replace-password@replace-host:5432/replace-database",
    }
    with pytest.raises(RuntimeError, match="Replace placeholder production config"):
        from config import validate_config

        validate_config(config)


def test_production_config_requires_shared_rate_limit_store(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    config = {
        "SECRET_KEY": "x" * 32,
        "JWT_SECRET_KEY": "y" * 32,
        "ADMIN_PASS_HASH": "hash",
        "SESSION_COOKIE_SECURE": True,
        "JWT_COOKIE_SECURE": True,
        "DATABASE_URL": "postgresql://user:pass@db.example:5432/onice",
        "RATELIMIT_STORAGE_URL": "memory://",
    }
    with pytest.raises(RuntimeError, match="shared rate-limit store"):
        from config import validate_config

        validate_config(config)


def test_admin_settings_masks_social_tokens(client, app):
    client.post("/auth/login", data={"username": "sir", "password": "adminpass"})
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO social_tokens (id, platform, access_token) VALUES (?, ?, ?)",
            ("tok_fb", "facebook", "FACEBOOK_SECRET_TOKEN"),
        )
        db.commit()

    html_text = client.get("/admin/?sec=settings").get_data(as_text=True)
    saved = client.post(
        "/api/save_settings",
        data={"blog_name": "On Ice", "fb_token": "", "ig_token": ""},
    )

    assert "FACEBOOK_SECRET_TOKEN" not in html_text
    assert "Token saved" in html_text
    assert saved.status_code == 200
    with app.app_context():
        token = get_db().execute(
            "SELECT access_token FROM social_tokens WHERE platform='facebook'"
        ).fetchone()
        assert token is not None
        assert token["access_token"] == "FACEBOOK_SECRET_TOKEN"


def test_admin_json_data_islands_escape_closing_script(client, app):
    client.post("/auth/login", data={"username": "sir", "password": "adminpass"})
    with app.app_context():
        db = get_db()
        db.execute(
            """INSERT INTO techniques (id, title, icon, excerpt, body, sort_order)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                "tech_xss",
                "Safe title",
                "x",
                "</script><script>alert(1)</script>",
                "<p>Body</p>",
                0,
            ),
        )
        db.commit()

    html_text = client.get("/admin/?sec=techniques").get_data(as_text=True)

    assert "</script><script>alert(1)</script>" not in html_text


def test_invoice_and_return_pages_require_order_owner(client, app):
    client.post(
        "/auth/register",
        data={"username": "owner", "password": "secret1", "password2": "secret1"},
    )
    with app.app_context():
        db = get_db()
        user = db.execute("SELECT id FROM users WHERE username=?", ("owner",)).fetchone()
        assert user is not None
        db.execute(
            """INSERT INTO orders (id, user_id, name, address, total_amount, payment_method, status,
               fulfillment_status, order_token) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "ord_owner",
                user["id"],
                "Owner",
                "Address",
                100.0,
                "razorpay",
                "completed",
                "pending",
                "tok_owner",
            ),
        )
        db.commit()

    owner_invoice = client.get("/invoice/tok_owner")
    owner_returns = client.get("/returns/tok_owner")
    client.post("/auth/logout")
    anon_invoice = client.get("/invoice/tok_owner")
    anon_returns = client.get("/returns/tok_owner")

    assert owner_invoice.status_code == 200
    assert owner_returns.status_code == 200
    assert anon_invoice.status_code == 403
    assert anon_returns.status_code == 403


def test_order_success_requires_order_owner(client, app):
    client.post(
        "/auth/register",
        data={"username": "success-owner", "password": "secret1", "password2": "secret1"},
    )
    with app.app_context():
        db = get_db()
        user = db.execute(
            "SELECT id FROM users WHERE username=?", ("success-owner",)
        ).fetchone()
        assert user is not None
        db.execute(
            """INSERT INTO orders (id, user_id, name, address, total_amount, payment_method, status,
               fulfillment_status, order_token) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "ord_success",
                user["id"],
                "Owner",
                "Address",
                100.0,
                "razorpay",
                "completed",
                "pending",
                "tok_success",
            ),
        )
        db.commit()

    owner_response = client.get("/order-success?token=tok_success")
    client.post("/auth/logout")
    anonymous_response = client.get("/order-success?token=tok_success")

    assert owner_response.status_code == 200
    assert anonymous_response.status_code == 403


def test_razorpay_webhook_bypasses_csrf_but_keeps_signature(app):
    app.config["WTF_CSRF_ENABLED"] = True
    app.config["RAZORPAY_WEBHOOK_SECRET"] = "webhook-secret"
    client = app.test_client()
    body = b'{"event":"payment.captured","payload":{"payment":{"entity":{"id":"pay_x"}}}}'
    signature = hmac.new(b"webhook-secret", body, hashlib.sha256).hexdigest()

    response = client.post(
        "/api/razorpay/webhook",
        data=body,
        content_type="application/json",
        headers={"X-Razorpay-Signature": signature},
    )

    assert response.status_code == 200


def test_postgres_migration_covers_schema_tables():
    root = Path(__file__).resolve().parents[1]
    schema = (root / "schema_postgres.sql").read_text(encoding="utf-8")
    migration = (root / "migrate_to_pg.py").read_text(encoding="utf-8")
    tables = set(
        re.findall(r"CREATE TABLE IF NOT EXISTS ([a-z_]+)", schema, flags=re.I)
    )
    copied = set(re.findall(r'"([a-z_]+)"', migration))
    assert tables <= copied
