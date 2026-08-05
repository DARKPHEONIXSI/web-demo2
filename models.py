"""
models.py — Database helpers for the On Ice skating blog.
Uses SQLite locally or Postgres via DATABASE_URL.
"""

import json
import os
import re
import secrets
import sqlite3
from datetime import date, datetime, timedelta, timezone
from operator import attrgetter

import jwt
from flask import current_app, g

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:
    psycopg = None
    dict_row = None

sqlite3.register_adapter(datetime, lambda value: value.isoformat(" "))
sqlite3.register_converter(
    "timestamp", lambda value: datetime.fromisoformat(value.decode("utf-8"))
)

# ── Connection management ────────────────────────────────────


class PgRow(dict):
    """Dictionary row that also supports integer indexes like sqlite3.Row."""

    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


class PgCursor:
    def __init__(self, cursor):
        self.cursor = cursor
        self.rowcount = -1

    def execute(self, query, params=()):
        query = self._translate_query(query)
        self.cursor.execute(query, params or ())
        self.rowcount = self.cursor.rowcount
        return self

    def fetchone(self):
        row = self.cursor.fetchone()
        return PgRow(row) if row is not None else None

    def fetchall(self):
        return [PgRow(row) for row in self.cursor.fetchall()]

    @staticmethod
    def _translate_query(query: str) -> str:
        return (
            query.replace('datetime("now")', "CURRENT_TIMESTAMP")
            .replace("datetime('now')", "CURRENT_TIMESTAMP")
            .replace("?", "%s")
        )


class PgConnection:
    def __init__(self, conn):
        self.conn = conn

    def execute(self, query, params=()):
        return PgCursor(self.conn.cursor()).execute(query, params)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()


def using_postgres() -> bool:
    return bool(current_app.config.get("DATABASE_URL"))


def get_db():
    """Get (or create) a database connection for the current request."""
    if "db" not in g:
        database_url = current_app.config.get("DATABASE_URL")
        if database_url:
            if psycopg is None:
                raise RuntimeError("psycopg is required for Postgres DATABASE_URL")
            connect = attrgetter("connect")(psycopg)
            conn = connect(database_url, row_factory=dict_row)
            g.db = PgConnection(conn)
        else:
            conn = sqlite3.connect(
                current_app.config["DATABASE_PATH"],
                detect_types=sqlite3.PARSE_DECLTYPES,
            )
            conn.row_factory = sqlite3.Row
            g.db = conn
    return g.db


def close_db(e=None):
    """Close the database connection at end of request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def ensure_runtime_schema():
    """Apply small additive runtime migrations."""
    db = get_db()
    post_columns = {
        "cover_image": "TEXT NOT NULL DEFAULT ''",
        "category": "TEXT NOT NULL DEFAULT ''",
        "tags": "TEXT NOT NULL DEFAULT ''",
        "slug": "TEXT NOT NULL DEFAULT ''",
        "seo_title": "TEXT NOT NULL DEFAULT ''",
        "seo_description": "TEXT NOT NULL DEFAULT ''",
    }
    product_columns = {
        "category": "TEXT NOT NULL DEFAULT ''",
        "badge": "TEXT NOT NULL DEFAULT ''",
        "sku": "TEXT NOT NULL DEFAULT ''",
        "status": "TEXT NOT NULL DEFAULT 'active'",
        "stock_quantity": "INTEGER NOT NULL DEFAULT 0",
        "sale_price": "REAL DEFAULT NULL",
        "seo_title": "TEXT NOT NULL DEFAULT ''",
        "seo_description": "TEXT NOT NULL DEFAULT ''",
    }
    order_columns = {
        "user_id": "TEXT DEFAULT NULL",
        "shipping_amount": "REAL NOT NULL DEFAULT 0",
        "tax_amount": "REAL NOT NULL DEFAULT 0",
        "discount_amount": "REAL NOT NULL DEFAULT 0",
        "tracking_number": "TEXT NOT NULL DEFAULT ''",
        "fulfillment_status": "TEXT NOT NULL DEFAULT 'pending'",
    }
    custom_page_columns = {
        "seo_title": "TEXT NOT NULL DEFAULT ''",
        "seo_description": "TEXT NOT NULL DEFAULT ''",
    }
    if using_postgres():
        try:
            db.execute(
                "ALTER TABLE order_items ADD COLUMN IF NOT EXISTS product_id TEXT NOT NULL DEFAULT ''"
            )
            for name, definition in post_columns.items():
                db.execute(
                    f"ALTER TABLE posts ADD COLUMN IF NOT EXISTS {name} {definition}"
                )
            for name, definition in product_columns.items():
                pg_definition = definition.replace("REAL", "NUMERIC(12,2)")
                db.execute(
                    f"ALTER TABLE products ADD COLUMN IF NOT EXISTS {name} {pg_definition}"
                )
            for name, definition in order_columns.items():
                pg_definition = definition.replace("REAL", "NUMERIC(12,2)")
                db.execute(
                    f"ALTER TABLE orders ADD COLUMN IF NOT EXISTS {name} {pg_definition}"
                )
            for name, definition in custom_page_columns.items():
                db.execute(
                    f"ALTER TABLE custom_pages ADD COLUMN IF NOT EXISTS {name} {definition}"
                )
            create_feature_tables(db, postgres=True)
            for row in db.execute(
                "SELECT id, title FROM posts WHERE slug='' OR slug IS NULL"
            ).fetchall():
                db.execute(
                    "UPDATE posts SET slug=? WHERE id=?",
                    (unique_slug("posts", row["title"], row["id"]), row["id"]),
                )
            db.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_posts_slug ON posts(slug)"
            )
            db.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_products_sku ON products(sku) WHERE sku <> ''"
            )
            db.commit()
        except Exception:
            db.rollback()
    else:

        def table_exists(table: str) -> bool:
            return (
                db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
                    (table,),
                ).fetchone()
                is not None
            )

        def add_missing_columns(table: str, columns: dict[str, str]):
            if not table_exists(table):
                return
            existing = [
                r[1] for r in db.execute(f"PRAGMA table_info({table})").fetchall()
            ]
            if not existing:
                return
            for name, definition in columns.items():
                if name not in existing:
                    db.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")

        if table_exists("order_items"):
            order_item_cols = [
                r[1] for r in db.execute("PRAGMA table_info(order_items)").fetchall()
            ]
            if order_item_cols and "product_id" not in order_item_cols:
                db.execute(
                    "ALTER TABLE order_items ADD COLUMN product_id TEXT NOT NULL DEFAULT ''"
                )
        add_missing_columns("posts", post_columns)
        add_missing_columns("products", product_columns)
        add_missing_columns("orders", order_columns)
        add_missing_columns("custom_pages", custom_page_columns)
        create_feature_tables(db, postgres=False)
        if table_exists("posts"):
            for row in db.execute(
                "SELECT id, title FROM posts WHERE slug='' OR slug IS NULL"
            ).fetchall():
                db.execute(
                    "UPDATE posts SET slug=? WHERE id=?",
                    (unique_slug("posts", row["title"], row["id"]), row["id"]),
                )
            db.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_posts_slug ON posts(slug)"
            )
        if table_exists("products"):
            db.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_products_sku ON products(sku) WHERE sku <> ''"
            )

    db.execute("""CREATE TABLE IF NOT EXISTS audit_logs (
             id TEXT NOT NULL PRIMARY KEY,
             event_type TEXT NOT NULL,
             actor_id TEXT DEFAULT NULL,
             ip_address TEXT DEFAULT NULL,
             detail TEXT NOT NULL DEFAULT '',
             created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
           )""")
    db.commit()


def create_feature_tables(db, postgres: bool = False):
    """Create optional feature tables used by blog/shop production features."""
    id_type = (
        "BIGSERIAL PRIMARY KEY" if postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
    )
    money = "NUMERIC(12,2)" if postgres else "REAL"
    db.execute(f"""CREATE TABLE IF NOT EXISTS post_comments (
             id {id_type},
             post_id TEXT NOT NULL,
             user_id TEXT DEFAULT NULL,
             name TEXT NOT NULL,
             body TEXT NOT NULL,
             status TEXT NOT NULL DEFAULT 'approved',
             created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
           )""")
    db.execute(f"""CREATE TABLE IF NOT EXISTS product_reviews (
             id {id_type},
             product_id TEXT NOT NULL,
             user_id TEXT DEFAULT NULL,
             name TEXT NOT NULL,
             rating INTEGER NOT NULL DEFAULT 5,
             body TEXT NOT NULL DEFAULT '',
             status TEXT NOT NULL DEFAULT 'approved',
             created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
           )""")
    db.execute("""CREATE TABLE IF NOT EXISTS wishlist_items (
             user_id TEXT NOT NULL,
             product_id TEXT NOT NULL,
             created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
             PRIMARY KEY (user_id, product_id)
           )""")
    db.execute(f"""CREATE TABLE IF NOT EXISTS coupons (
             code TEXT NOT NULL PRIMARY KEY,
             discount_type TEXT NOT NULL DEFAULT 'percent',
             discount_value {money} NOT NULL DEFAULT 0,
             active INTEGER NOT NULL DEFAULT 1,
             expires_at TEXT DEFAULT NULL,
             created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
           )""")
    db.execute("""CREATE TABLE IF NOT EXISTS return_requests (
             id TEXT NOT NULL PRIMARY KEY,
             order_id TEXT NOT NULL,
             user_id TEXT DEFAULT NULL,
             reason TEXT NOT NULL,
             status TEXT NOT NULL DEFAULT 'requested',
             created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
           )""")
    db.execute("""CREATE TABLE IF NOT EXISTS cart_items (
             user_id TEXT NOT NULL,
             product_id TEXT NOT NULL,
             variant_id TEXT NOT NULL DEFAULT '',
             quantity INTEGER NOT NULL DEFAULT 1,
             updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
             PRIMARY KEY (user_id, product_id, variant_id)
           )""")
    db.execute(f"""CREATE TABLE IF NOT EXISTS analytics_events (
             id {id_type},
             event_type TEXT NOT NULL,
             object_id TEXT NOT NULL DEFAULT '',
             user_id TEXT DEFAULT NULL,
             created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
           )""")
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_post_comments_post_id ON post_comments(post_id)"
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_product_reviews_product_id ON product_reviews(product_id)"
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_return_requests_order_id ON return_requests(order_id)"
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_analytics_events_type ON analytics_events(event_type, created_at)"
    )


def slugify(value: str) -> str:
    """Convert a title/name into a URL-safe slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")
    return slug or gen_id()


def unique_slug(table: str, base_value: str, current_id: str = "") -> str:
    """Build a unique slug for posts or products."""
    base = slugify(base_value)
    slug = base
    suffix = 2
    db = get_db()
    while True:
        row = db.execute(
            f"SELECT id FROM {table} WHERE slug=? AND id != ? LIMIT 1",
            (slug, current_id or ""),
        ).fetchone()
        if not row:
            return slug
        slug = f"{base}-{suffix}"
        suffix += 1


def init_db():
    """Initialize the database if tables don't exist."""
    db = get_db()
    schema_name = "schema_postgres.sql" if using_postgres() else "schema.sql"
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), schema_name)
    with open(schema_path, encoding="utf-8") as f:
        sql = f.read()
    if using_postgres():
        for statement in sql.split(";"):
            statement = statement.strip()
            if statement:
                db.execute(statement)
    else:
        if not isinstance(db, sqlite3.Connection):
            raise RuntimeError("SQLite schema initialization requires SQLite")
        db.executescript(sql)
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
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expires = now + timedelta(seconds=current_app.config["JWT_ACCESS_TOKEN_EXPIRES"])
    payload = {
        "sub": user_id,
        "role": role,
        "exp": expires,
        "type": "access",
        "iat": now,
    }
    token = jwt.encode(
        payload,
        current_app.config["JWT_SECRET_KEY"],
        algorithm=current_app.config["JWT_ALGORITHM"],
    )
    return token, expires


def create_refresh_token(user_id: str) -> tuple[str, datetime]:
    """Create a JWT refresh token. Returns (token, expires_at)."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expires = now + timedelta(seconds=current_app.config["JWT_REFRESH_TOKEN_EXPIRES"])
    payload = {
        "sub": user_id,
        "exp": expires,
        "type": "refresh",
        "iat": now,
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


def ensure_builtin_admin_user():
    """Ensure the configured built-in admin can participate in JWT auth."""
    db = get_db()
    db.execute(
        """INSERT INTO users (id, username, password, role, is_google)
           VALUES ('admin', ?, ?, 'admin', 0)
           ON CONFLICT(id) DO UPDATE SET
             username = EXCLUDED.username,
             password = EXCLUDED.password,
             role = 'admin',
             is_google = 0""",
        (current_app.config["ADMIN_USER"], current_app.config["ADMIN_PASS_HASH"]),
    )
    db.commit()


def log_audit(
    event_type: str,
    actor_id: str | None = None,
    ip_address: str | None = None,
    **detail,
):
    """Persist a structured audit event without interrupting the request."""
    try:
        db = get_db()
        db.execute(
            "INSERT INTO audit_logs (id, event_type, actor_id, ip_address, detail) VALUES (?, ?, ?, ?, ?)",
            (
                gen_id(),
                event_type,
                actor_id,
                ip_address,
                json.dumps(detail, sort_keys=True),
            ),
        )
        db.commit()
    except Exception:
        current_app.logger.exception("failed to write audit log for %s", event_type)


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
        count_row = db.execute(query, (like, like)).fetchone()
        return count_row[0] if count_row else 0

    # No search
    if published_only:
        count_row = db.execute(
            "SELECT COUNT(*) FROM posts WHERE status='published'"
        ).fetchone()
        return count_row[0] if count_row else 0
    count_row = db.execute("SELECT COUNT(*) FROM posts").fetchone()
    return count_row[0] if count_row else 0
