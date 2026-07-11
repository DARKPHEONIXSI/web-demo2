import io
import json
import sys
from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app
from config import Config
from models import get_db, init_db
import auth as auth_module


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
    r = client.post("/auth/register", data={"username": "alice", "password": "secret1", "password2": "secret1"})
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
        return {"aud": client_id, "email": "g@example.com", "email_verified": True, "name": "Google User"}

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
        product_cols = [r[1] for r in db.execute("PRAGMA table_info(products)").fetchall()]
        order_cols = [r[1] for r in db.execute("PRAGMA table_info(orders)").fetchall()]
        for col in ["cover_image", "category", "tags", "slug", "seo_title", "seo_description"]:
            assert col in post_cols
        for col in ["category", "badge", "sku", "status", "stock_quantity", "sale_price", "seo_title", "seo_description"]:
            assert col in product_cols
        for col in ["user_id", "shipping_amount", "tax_amount", "tracking_number", "fulfillment_status"]:
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
    client.post("/auth/register", data={"username": "buyer", "password": "secret1", "password2": "secret1"})
    with app.app_context():
        db = get_db()
        user = db.execute("SELECT id FROM users WHERE username=?", ("buyer",)).fetchone()
        db.execute(
            """INSERT INTO orders (id, user_id, name, address, total_amount, shipping_amount, tax_amount,
               payment_method, status, fulfillment_status, tracking_number, order_token)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            ("ord_test", user["id"], "Buyer", "Address", 100.0, 0.0, 0.0, "razorpay", "completed", "shipped", "TRK123", "tok_test"),
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
    for path in ["/sitemap.xml", "/robots.txt", "/feed.xml", "/privacy", "/terms", "/shipping-returns", "/refund-policy", "/payment-failed"]:
        r = client.get(path)
        assert r.status_code == 200
    assert b"sitemap" in client.get("/robots.txt").data.lower()
    assert b"<rss" in client.get("/feed.xml").data


def test_blog_archive_comment_and_slug(client, app):
    with app.app_context():
        post = get_db().execute("SELECT id, slug FROM posts WHERE category <> '' LIMIT 1").fetchone()
    assert client.get(f"/post/{post['slug']}").status_code == 200
    assert client.get("/category/Training").status_code == 200
    assert client.get("/tag/practice").status_code == 200
    r = client.post("/api/comment", data={"post_id": post["id"], "name": "Reader", "body": "Great post"})
    assert r.status_code == 200
    assert r.json["ok"] is True


def test_coupon_and_out_of_stock(client, app):
    with app.app_context():
        db = get_db()
        db.execute("INSERT INTO coupons (code, discount_type, discount_value) VALUES (?, ?, ?)", ("SAVE10", "percent", 10))
        db.execute("INSERT INTO products (id, name, description, base_price, stock_quantity) VALUES (?, ?, ?, ?, ?)", ("sold_out", "Sold Out", "", 100.0, 0))
        db.commit()
    cart = json.dumps([{"product_id": "prod_test", "quantity": 1}])
    quote = client.post("/api/cart/quote", data={"cart": cart, "coupon": "SAVE10"})
    assert quote.status_code == 200
    assert quote.json["discount_amount"] == 123.4
    sold_out = client.post("/api/cart/quote", data={"cart": json.dumps([{"product_id": "sold_out", "quantity": 1}])})
    assert sold_out.status_code == 400


def test_review_wishlist_and_server_cart(client):
    client.post("/auth/register", data={"username": "shopper", "password": "secret1", "password2": "secret1"})
    review = client.post("/api/review", data={"product_id": "prod_test", "rating": "5", "body": "Excellent"})
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


def test_admin_order_update_export_and_refund(client, app):
    client.post("/auth/login", data={"username": "sir", "password": "adminpass"})
    with app.app_context():
        db = get_db()
        db.execute(
            """INSERT INTO orders (id, name, address, total_amount, payment_method, status, fulfillment_status, order_token)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("ord_admin", "Buyer", "Address", 100.0, "razorpay", "completed", "pending", "tok_admin"),
        )
        db.commit()
    update = client.post("/api/update_order_status", data={"id": "ord_admin", "status": "completed", "fulfillment_status": "shipped", "tracking_number": "TRACK"})
    assert update.status_code == 200
    export = client.get("/admin/orders/export.csv")
    assert export.status_code == 200
    assert b"ord_admin" in export.data
    refund = client.post("/api/refund_order", data={"id": "ord_admin"})
    assert refund.status_code == 200


def test_mocked_razorpay_checkout_success(client, app, monkeypatch):
    import api as api_module

    client.post("/auth/register", data={"username": "paybuyer", "password": "secret1", "password2": "secret1"})
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
            return {"id": payment_id, "order_id": "rzp_order", "amount": expected_amount, "currency": "INR", "status": "captured"}

    class FakeOrder:
        def create(self, data):
            return {"id": "rzp_order", **data}
        def fetch(self, order_id):
            return {"id": order_id, "amount": expected_amount, "notes": {"cart_hash": expected_hash}}

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


def test_upload_rejects_non_image(client):
    client.post("/auth/login", data={"username": "sir", "password": "adminpass"})
    r = client.post(
        "/api/upload_image",
        data={"image": (io.BytesIO(b"not an image"), "bad.png")},
        content_type="multipart/form-data",
    )
    assert r.status_code == 400
    assert r.json["ok"] is False


def test_xss_sanitizer_removes_dangerous_markup():
    from purify_html import purify_html

    cleaned = purify_html('<p style="color:red">Hi</p><script>alert(1)</script><img src="javascript:alert(2)">')
    assert "script" not in cleaned.lower()
    assert "javascript:" not in cleaned.lower()
    assert "style=" not in cleaned.lower()
