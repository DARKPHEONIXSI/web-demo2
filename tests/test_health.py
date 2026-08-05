from __future__ import annotations

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
    test_app.config.update(TESTING=True, WTF_CSRF_ENABLED=False, RATELIMIT_ENABLED=False)
    with test_app.app_context():
        init_db()
    return test_app


@pytest.fixture()
def client(app):
    return app.test_client()


def _sqlite_schema_snapshot() -> tuple[tuple[str, tuple[str, ...]], ...]:
    db = get_db()
    tables = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    return tuple(
        (
            table[0],
            tuple(
                column[1]
                for column in db.execute(f"PRAGMA table_info({table[0]})").fetchall()
            ),
        )
        for table in tables
    )


def test_health_get_returns_json_without_schema_changes(client, app):
    with app.app_context():
        before = _sqlite_schema_snapshot()

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == {"service": "on-ice-api", "status": "ok"}

    with app.app_context():
        after = _sqlite_schema_snapshot()

    assert after == before
