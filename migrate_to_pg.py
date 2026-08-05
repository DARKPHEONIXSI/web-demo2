import os
import sqlite3
from urllib.parse import quote

from app import create_app
from config import Config
from models import get_db, init_db

MIGRATION_TABLES = (
    "settings",
    "users",
    "posts",
    "techniques",
    "custom_pages",
    "gallery_items",
    "contact_messages",
    "products",
    "product_variants",
    "product_images",
    "media_library",
    "social_tokens",
    "orders",
    "audit_logs",
    "order_items",
    "post_comments",
    "product_reviews",
    "wishlist_items",
    "coupons",
    "return_requests",
    "cart_items",
    "analytics_events",
)


def postgres_url_from_env() -> str:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    required_pg_vars = ("PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD")
    missing_pg_vars = [name for name in required_pg_vars if not os.getenv(name)]
    if missing_pg_vars:
        missing = ", ".join(missing_pg_vars)
        raise RuntimeError(
            "Set DATABASE_URL or explicit PostgreSQL environment variables "
            f"(missing: {missing})."
        )
    return (
        f"postgresql://{quote(os.environ['PGUSER'], safe='')}:"
        f"{quote(os.environ['PGPASSWORD'], safe='')}@"
        f"{os.environ['PGHOST']}:{os.environ['PGPORT']}/"
        f"{quote(os.environ['PGDATABASE'], safe='')}"
    )


def sqlite_table_exists(src: sqlite3.Connection, table: str) -> bool:
    return (
        src.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        is not None
    )


def sqlite_columns(src: sqlite3.Connection, table: str) -> list[str]:
    return [row[1] for row in src.execute(f"PRAGMA table_info({table})").fetchall()]


def postgres_columns(pg, table: str) -> list[str]:
    rows = pg.execute(
        """SELECT column_name FROM information_schema.columns
           WHERE table_schema = 'public' AND table_name = ?
           ORDER BY ordinal_position""",
        (table,),
    ).fetchall()
    return [row[0] for row in rows]


def copy_table(src: sqlite3.Connection, pg, table: str) -> None:
    if not sqlite_table_exists(src, table):
        print(f"Skipping {table}: not present in SQLite source.")
        return
    src_cols = sqlite_columns(src, table)
    pg_cols = postgres_columns(pg, table)
    cols = [col for col in src_cols if col in pg_cols]
    if not cols:
        print(f"Skipping {table}: no common columns.")
        return

    print(f"Copying {table}...")
    placeholders = ", ".join(["%s"] * len(cols))
    col_names = ", ".join(cols)
    for row in src.execute(f"SELECT {col_names} FROM {table}").fetchall():
        values = tuple(row[col] for col in cols)
        try:
            pg.execute(
                f"INSERT INTO {table} ({col_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING",
                values,
            )
            pg.commit()
        except Exception as e:
            pg.rollback()
            print(f"  Error on {table}: {e}")


def main() -> None:
    Config.DATABASE_URL = postgres_url_from_env()
    src = sqlite3.connect("simar.db")
    src.row_factory = sqlite3.Row
    app = create_app()
    try:
        with app.app_context():
            init_db()
            pg = get_db()
            for table in MIGRATION_TABLES:
                copy_table(src, pg, table)
    finally:
        src.close()
    print("Migration complete!")


if __name__ == "__main__":
    main()
