"""Migrate all data from SQLite to PostgreSQL."""
import sqlite3
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["DATABASE_URL"] = "postgresql://onice_user:onice_pass_2026@localhost:5432/onice"

from app import create_app
from config import Config
from models import get_db, init_db

# Read from SQLite
src = sqlite3.connect("simar.db")
src.row_factory = sqlite3.Row

app = create_app()
with app.app_context():
    # Ensure PostgreSQL tables exist
    init_db()
    pg = get_db()

    def copy_table(table, cols):
        print(f"Copying {table}...")
        placeholders = ", ".join(["%s"] * len(cols))
        col_names = ", ".join(cols)
        for row in src.execute(f"SELECT {col_names} FROM {table}").fetchall():
            values = tuple(row[c] for c in cols)
            try:
                pg.execute(
                    f"INSERT INTO {table} ({col_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING",
                    values,
                )
                pg.commit()
            except Exception as e:
                pg.rollback()
                print(f"  Error on {table}: {e}")

    # Settings
    copy_table("settings", ["setting_key", "setting_val"])

    # Users
    copy_table("users", ["id", "username", "password", "is_google", "role",
                         "jwt_token", "jwt_expires_at", "refresh_token",
                         "refresh_expires_at", "created_at"])

    # Posts
    copy_table("posts", ["id", "title", "excerpt", "body", "author", "author_id",
                         "read_time", "pinned", "status", "post_date",
                         "created_at", "updated_at"])

    # Techniques
    copy_table("techniques", ["id", "title", "icon", "excerpt", "body", "sort_order", "created_at"])

    # Custom pages
    copy_table("custom_pages", ["id", "name", "slug", "body", "created_at", "updated_at"])

    # Gallery items
    copy_table("gallery_items", ["id", "emoji", "title", "description", "tag", "image_path", "sort_order", "created_at"])

    # Contact messages
    copy_table("contact_messages", ["name", "email", "subject", "message", "is_read", "created_at"])

    # Products
    copy_table("products", ["id", "name", "description", "base_price", "created_at", "updated_at"])

    # Product variants
    copy_table("product_variants", ["id", "product_id", "color", "size", "stock_quantity", "price_override"])

    # Product images
    copy_table("product_images", ["id", "product_id", "color_match", "image_url", "sort_order"])

    # Orders
    copy_table("orders", ["id", "name", "address", "total_amount", "payment_method",
                          "status", "order_token", "razorpay_payment_id",
                          "razorpay_order_id", "customer_email",
                          "customer_phone", "created_at"])

    # Audits
    copy_table("audit_logs", ["id", "event_type", "actor_id", "ip_address", "detail", "created_at"])

    # Order items
    copy_table("order_items", ["id", "order_id", "product_id", "product_variant_id",
                                "quantity", "price_at_time"])

print("Migration complete!")
src.close()
