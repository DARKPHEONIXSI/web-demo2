import sqlite3

db_path = "simar.db"
schema_path = "schema.sql"


def migrate():
    print("Starting migration...")
    conn = sqlite3.connect(db_path)
    # Enable foreign keys just in case
    conn.execute("PRAGMA foreign_keys=OFF")

    with open(schema_path, encoding="utf-8") as f:
        schema = f.read()

    # We will rename the old tables, create the new ones from schema, copy data, and drop old.
    tables_to_migrate = ["posts", "product_variants", "users"]

    for table in tables_to_migrate:
        print(f"Migrating {table}...")
        try:
            # Check if old table exists
            conn.execute(f"ALTER TABLE {table} RENAME TO {table}_old")
        except sqlite3.OperationalError as e:
            print(f"  {table} already renamed or doesn't exist: {e}")
            continue

    # Execute new schema to create all new tables (including new constraints and order_items)
    print("Running new schema...")
    conn.executescript(schema)

    # Copy data back
    print("Copying data for posts...")
    try:
        # Delete seed data to avoid UNIQUE constraint on existing IDs
        conn.execute("DELETE FROM posts")
        # author_id will be NULL for existing since it's a new column, which is fine
        conn.execute(
            """
            INSERT INTO posts (id, title, excerpt, body, author, read_time, pinned, status, post_date, created_at, updated_at)
            SELECT id, title, excerpt, body, author, read_time, pinned, status, post_date, created_at, updated_at
            FROM posts_old
        """
        )
        conn.execute("DROP TABLE posts_old")
    except Exception as e:
        print("  Error migrating posts:", e)

    print("Copying data for product_variants...")
    try:
        conn.execute("DELETE FROM product_variants")
        conn.execute(
            """
            INSERT INTO product_variants (id, product_id, color, size, stock_quantity, price_override)
            SELECT id, product_id, color, size, stock_quantity, price_override
            FROM product_variants_old
        """
        )
        conn.execute("DROP TABLE product_variants_old")
    except Exception as e:
        print("  Error migrating product_variants:", e)

    print("Copying data for users...")
    try:
        # Keep existing users, just copy over the fields that exist
        conn.execute("DELETE FROM users")
        conn.execute(
            """
            INSERT INTO users (id, username, password, google_email, is_google, role, jwt_token, jwt_expires_at, created_at)
            SELECT id, username, password, google_email, is_google, role, jwt_token, jwt_expires_at, created_at
            FROM users_old
        """
        )
        conn.execute("DROP TABLE users_old")
    except Exception as e:
        print("  Error migrating users:", e)

    conn.execute("PRAGMA foreign_keys=ON")
    conn.commit()
    conn.close()
    print("Migration complete!")


if __name__ == "__main__":
    migrate()
