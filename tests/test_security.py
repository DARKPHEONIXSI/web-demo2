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
    Config.ADMIN_PASS_HASH = admin_hash
    Config.SECRET_KEY = "test-secret-key-that-is-long-enough"
    Config.JWT_SECRET_KEY = "test-jwt-secret-key-that-is-long-enough"
    test_app = create_app()
    test_app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        GOOGLE_CLIENT_ID="client-id.apps.googleusercontent.com",
        RATELIMIT_ENABLED=False,
    )
    with test_app.app_context():
        init_db()
        db = get_db()
        db.execute(
            "INSERT INTO products (id, name, description, base_price) VALUES (?, ?, ?, ?)",
            ("prod_test", "Test Skates", "", 1234.0),
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
