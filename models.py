"""
models.py — Database helpers for the On Ice skating blog.
Uses local SQLite database.
"""

import os
import secrets
import sqlite3
from datetime import date, datetime, timedelta

import jwt
from flask import current_app, g

# ── Connection management ────────────────────────────────────


def get_db():
    """Get (or create) a database connection for the current request."""
    if "db" not in g:
        # Connect to SQLite
        conn = sqlite3.connect(
            current_app.config["DATABASE_PATH"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db


def close_db(e=None):
    """Close the database connection at end of request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Initialize the database from schema.sql if tables don't exist."""
    db = get_db()
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
    with open(schema_path, encoding="utf-8") as f:
        db.executescript(f.read())
    db.commit()


# ── ID generator ─────────────────────────────────────────────


def gen_id() -> str:
    """Generate a 26-character hex ID (similar to ULID)."""
    return secrets.token_hex(13)


# ── Settings helpers ─────────────────────────────────────────


def get_settings() -> dict:
    """Load all settings as a {key: value} dict."""
    db = get_db()
    rows = db.execute("SELECT setting_key, setting_val FROM settings").fetchall()
    return {r["setting_key"]: r["setting_val"] for r in rows}


def save_setting(key: str, val: str):
    """Upsert a single setting."""
    db = get_db()
    db.execute(
        """INSERT INTO settings (setting_key, setting_val)
           VALUES (?, ?)
           ON CONFLICT(setting_key) DO UPDATE SET
             setting_val = EXCLUDED.setting_val,
             updated_at = CURRENT_TIMESTAMP""",
        (key, val),
    )
    db.commit()


# ── Date formatting ──────────────────────────────────────────


def fmt_date(d) -> str:
    """Format a date string or date object to 'Mon D, YYYY'."""
    if not d:
        return ""
    if isinstance(d, str):
        try:
            dt = datetime.strptime(d, "%Y-%m-%d")
        except ValueError:
            try:
                dt = datetime.strptime(d, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    dt = datetime.strptime(d.split(".")[0], "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    return d
    elif isinstance(d, (datetime, date)):
        dt = d
    else:
        return str(d)
    return dt.strftime("%b %-d, %Y") if os.name != "nt" else dt.strftime("%b %#d, %Y")


# ── JWT Token helpers ────────────────────────────────────────


def create_access_token(user_id: str, role: str) -> tuple[str, datetime]:
    """Create a JWT access token. Returns (token, expires_at)."""
    expires = datetime.utcnow() + timedelta(
        seconds=current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]
    )
    payload = {
        "sub": user_id,
        "role": role,
        "exp": expires,
        "type": "access",
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(
        payload,
        current_app.config["JWT_SECRET_KEY"],
        algorithm=current_app.config["JWT_ALGORITHM"],
    )
    return token, expires


def create_refresh_token(user_id: str) -> tuple[str, datetime]:
    """Create a JWT refresh token. Returns (token, expires_at)."""
    expires = datetime.utcnow() + timedelta(
        seconds=current_app.config["JWT_REFRESH_TOKEN_EXPIRES"]
    )
    payload = {
        "sub": user_id,
        "exp": expires,
        "type": "refresh",
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(
        payload,
        current_app.config["JWT_SECRET_KEY"],
        algorithm=current_app.config["JWT_ALGORITHM"],
    )
    return token, expires


def decode_token(token: str) -> dict | None:
    """Decode and validate a JWT token. Returns payload dict or None."""
    try:
        return jwt.decode(
            token,
            current_app.config["JWT_SECRET_KEY"],
            algorithms=[current_app.config["JWT_ALGORITHM"]],
        )
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def verify_refresh_token(refresh_token: str) -> dict | None:
    """Verify a refresh token against the database. Returns user dict or None."""
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        return None
    db = get_db()
    user = db.execute(
        'SELECT id, role FROM users WHERE refresh_token = ? AND refresh_expires_at > datetime("now")',
        (refresh_token,),
    ).fetchone()
    return dict(user) if user else None


def store_tokens(
    user_id: str,
    access_token: str,
    access_expires: datetime,
    refresh_token: str,
    refresh_expires: datetime,
):
    """Store tokens in database."""
    db = get_db()
    db.execute(
        """UPDATE users SET
            jwt_token = ?, jwt_expires_at = ?,
            refresh_token = ?, refresh_expires_at = ?
           WHERE id = ?""",
        (access_token, access_expires, refresh_token, refresh_expires, user_id),
    )
    db.commit()


def clear_tokens(user_id: str):
    """Clear tokens from database (logout)."""
    db = get_db()
    db.execute(
        "UPDATE users SET jwt_token = NULL, jwt_expires_at = NULL, "
        "refresh_token = NULL, refresh_expires_at = NULL WHERE id = ?",
        (user_id,),
    )
    db.commit()


def get_user_by_access_token(access_token: str) -> dict | None:
    """Get user by valid access token from database."""
    payload = decode_token(access_token)
    if not payload or payload.get("type") != "access":
        return None
    db = get_db()
    user = db.execute(
        'SELECT id, role FROM users WHERE jwt_token = ? AND jwt_expires_at > datetime("now")',
        (access_token,),
    ).fetchone()
    return dict(user) if user else None


# ── Query helpers ────────────────────────────────────────────


def get_posts(
    published_only: bool = True, search: str = "", limit: int = 9, offset: int = 0
):
    """Fetch posts with optional status filter and search."""
    db = get_db()

    if search:
        like = f"%{search}%"
        if published_only:
            query = (
                "SELECT * FROM posts "
                "WHERE (title LIKE ? OR excerpt LIKE ?) AND status='published' "
                "ORDER BY post_date DESC LIMIT ? OFFSET ?"
            )
        else:
            query = (
                "SELECT * FROM posts "
                "WHERE (title LIKE ? OR excerpt LIKE ?) "
                "ORDER BY post_date DESC LIMIT ? OFFSET ?"
            )
        return db.execute(query, (like, like, limit, offset)).fetchall()

    # No search
    if published_only:
        query = (
            "SELECT * FROM posts WHERE status='published' "
            "ORDER BY pinned DESC, post_date DESC LIMIT ? OFFSET ?"
        )
    else:
        query = (
            "SELECT * FROM posts ORDER BY pinned DESC, post_date DESC LIMIT ? OFFSET ?"
        )
    return db.execute(query, (limit, offset)).fetchall()


def count_posts(published_only: bool = True, search: str = "") -> int:
    """Count posts matching the same filter as get_posts()."""
    db = get_db()

    if search:
        like = f"%{search}%"
        if published_only:
            query = (
                "SELECT COUNT(*) FROM posts "
                "WHERE (title LIKE ? OR excerpt LIKE ?) AND status='published'"
            )
        else:
            query = (
                "SELECT COUNT(*) FROM posts " "WHERE (title LIKE ? OR excerpt LIKE ?)"
            )
        return db.execute(query, (like, like)).fetchone()[0]

    # No search
    if published_only:
        return db.execute(
            "SELECT COUNT(*) FROM posts WHERE status='published'"
        ).fetchone()[0]
    return db.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
