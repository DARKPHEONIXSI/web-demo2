import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from config import Config
from models import get_db, init_db


@pytest.fixture()
def app(tmp_path, monkeypatch):
    admin_hash = generate_password_hash("adminpass")
    monkeypatch.setenv("ADMIN_PASS_HASH", admin_hash)
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
        RATELIMIT_ENABLED=False,
        DATABASE_URL="",
    )
    with test_app.app_context():
        init_db()
        db = get_db()
        db.execute(
            """INSERT INTO products
               (id, name, description, category, sku, status, stock_quantity, base_price)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("prod_active", "Active Skates", "Ready", "Skates", "ACTIVE-1", "active", 4, 1200.0),
        )
        db.execute(
            """INSERT INTO products
               (id, name, description, status, stock_quantity, base_price)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("prod_draft", "Draft Skates", "Hidden", "draft", 2, 800.0),
        )
        db.execute(
            """INSERT INTO product_images (id, product_id, image_url, color_match, sort_order)
               VALUES (?, ?, ?, ?, ?)""",
            ("img_active", "prod_active", "/uploads/skates.png", "blue", 1),
        )
        db.execute(
            """INSERT INTO product_variants
               (id, product_id, color, size, stock_quantity, price_override)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("var_active", "prod_active", "blue", "8", 2, 1100.0),
        )
        db.execute(
            """INSERT INTO product_reviews (product_id, name, rating, body, status)
               VALUES (?, ?, ?, ?, ?)""",
            ("prod_active", "Reader", 5, "Approved", "approved"),
        )
        db.execute(
            """INSERT INTO product_reviews (product_id, name, rating, body, status)
               VALUES (?, ?, ?, ?, ?)""",
            ("prod_active", "Reader", 1, "Pending", "pending"),
        )
        db.execute(
            """INSERT INTO custom_pages (id, name, slug, body)
               VALUES (?, ?, ?, ?)""",
            ("page_api", "API Page", "api-page", "<p>Page body</p>"),
        )
        db.execute(
            """INSERT INTO contact_messages (name, email, subject, message)
               VALUES (?, ?, ?, ?)""",
            ("Visitor", "visitor@example.com", "Hello", "Message"),
        )
        db.execute(
            """INSERT INTO media_library (id, media_type, url, alt_text)
               VALUES (?, ?, ?, ?)""",
            ("media_api", "image", "/uploads/media.png", "Media"),
        )
        db.execute(
            """INSERT INTO social_tokens (id, platform, access_token)
               VALUES (?, ?, ?)""",
            ("social_api", "facebook", "NEVER_EXPOSE_THIS_TOKEN"),
        )
        db.commit()
    return test_app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def owner_client(app):
    owner = app.test_client()
    registered = owner.post(
        "/auth/register",
        data={"username": "owner", "password": "secret1", "password2": "secret1"},
    )
    assert registered.status_code == 200
    with app.app_context():
        db = get_db()
        user = db.execute("SELECT id FROM users WHERE username=?", ("owner",)).fetchone()
        assert user is not None
        db.execute(
            """INSERT INTO orders
               (id, user_id, name, address, total_amount, shipping_amount, tax_amount,
                discount_amount, payment_method, status, fulfillment_status,
                tracking_number, order_token, customer_email, customer_phone)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "order_api", user["id"], "Owner", "Address", 1300.0, 100.0, 100.0,
                0.0, "razorpay", "completed", "shipped", "TRACK-API", "token_api",
                "owner@example.com", "9999999999",
            ),
        )
        db.execute(
            """INSERT INTO order_items
               (id, order_id, product_id, product_variant_id, quantity, price_at_time)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("item_api", "order_api", "prod_active", "var_active", 1, 1100.0),
        )
        db.commit()
    return owner


def test_public_read_endpoints_return_schema_backed_data(client):
    # Given seeded public products, content, and product relations
    # When each public read endpoint is requested
    products = client.get("/api/get_products")
    product = client.get("/api/get_product?id=prod_active")
    gallery = client.get("/api/get_gallery")
    techniques = client.get("/api/get_techniques")
    pages = client.get("/api/get_pages")
    page = client.get("/api/get_page?id=page_api")

    # Then only active products are exposed and related records use real schema fields
    assert products.status_code == 200
    assert [item["id"] for item in products.json["products"]] == ["prod_active"]
    assert products.json["products"][0]["image"] == "/uploads/skates.png"
    assert product.status_code == 200
    assert product.json["product"]["id"] == "prod_active"
    assert product.json["variants"][0]["id"] == "var_active"
    assert product.json["images"][0]["id"] == "img_active"
    assert [review["body"] for review in product.json["reviews"]] == ["Approved"]
    assert gallery.status_code == 200 and gallery.json["gallery"]
    assert techniques.status_code == 200 and techniques.json["techniques"]
    assert pages.status_code == 200 and pages.json["pages"][0]["id"] == "page_api"
    assert page.status_code == 200 and page.json["page"]["body"] == "<p>Page body</p>"


@pytest.mark.parametrize(
    "path",
    [
        "/api/profile/orders",
        "/api/order/detail?token=token_api",
        "/api/invoice/detail?token=token_api",
        "/api/admin/dashboard",
        "/api/admin/orders",
        "/api/admin/products",
        "/api/admin/posts",
        "/api/admin/messages",
        "/api/admin/users",
        "/api/admin/media",
    ],
)
def test_protected_read_endpoints_reject_anonymous_requests(client, path):
    # Given no authentication cookie
    # When a protected read endpoint is requested
    response = client.get(path)

    # Then the shared JWT decorators return the standard authentication error
    assert response.status_code == 401
    assert response.json["ok"] is False
    assert response.json["code"] == "AUTH_REQUIRED"


def test_owner_can_read_profile_order_and_invoice(owner_client):
    # Given an authenticated user who owns a seeded order
    # When their order read endpoints are requested
    profile = owner_client.get("/api/profile/orders")
    detail = owner_client.get("/api/order/detail?token=token_api")
    invoice = owner_client.get("/api/invoice/detail?token=token_api")

    # Then the order and its items are returned
    assert profile.status_code == 200
    assert profile.json["orders"][0]["id"] == "order_api"
    assert detail.status_code == 200
    assert detail.json["order"]["tracking_number"] == "TRACK-API"
    assert detail.json["items"][0]["product_name"] == "Active Skates"
    assert invoice.status_code == 200
    assert invoice.json["items"][0]["price_at_time"] == 1100.0


def test_order_reads_enforce_owner_and_missing_token_semantics(app, owner_client):
    # Given a second authenticated user who does not own the seeded order
    intruder = app.test_client()
    intruder.post(
        "/auth/register",
        data={"username": "intruder", "password": "secret1", "password2": "secret1"},
    )

    # When the wrong owner and the real owner request forbidden or absent tokens
    wrong_detail = intruder.get("/api/order/detail?token=token_api")
    wrong_invoice = intruder.get("/api/invoice/detail?token=token_api")
    absent_detail = owner_client.get("/api/order/detail?token=missing")
    absent_invoice = owner_client.get("/api/invoice/detail?token=missing")

    # Then ownership failures are 403 and absent orders are 404
    assert wrong_detail.status_code == 403
    assert wrong_invoice.status_code == 403
    assert absent_detail.status_code == 404
    assert absent_invoice.status_code == 404


def test_admin_read_endpoints_require_admin_and_return_safe_data(app, owner_client):
    paths_and_keys = {
        "/api/admin/dashboard": "dashboard",
        "/api/admin/orders": "orders",
        "/api/admin/products": "products",
        "/api/admin/posts": "posts",
        "/api/admin/messages": "messages",
        "/api/admin/users": "users",
        "/api/admin/media": "media",
    }

    # Given a regular authenticated user and an authenticated admin
    admin = app.test_client()
    logged_in = admin.post("/auth/login", data={"username": "sir", "password": "adminpass"})
    assert logged_in.status_code == 200

    # When both roles request every admin read endpoint
    regular_responses = [owner_client.get(path) for path in paths_and_keys]
    admin_responses = {path: admin.get(path) for path in paths_and_keys}
    admin_order = admin.get("/api/order/detail?token=token_api")
    admin_invoice = admin.get("/api/invoice/detail?token=token_api")

    # Then regular users are forbidden and admins receive safe JSON without social secrets
    assert all(response.status_code == 403 for response in regular_responses)
    assert all(response.status_code == 200 for response in admin_responses.values())
    assert admin_order.status_code == 200
    assert admin_invoice.status_code == 200
    for path, key in paths_and_keys.items():
        assert key in admin_responses[path].json
        assert "NEVER_EXPOSE_THIS_TOKEN" not in admin_responses[path].get_data(as_text=True)
    assert "jwt_token" not in admin_responses["/api/admin/users"].json["users"][0]
