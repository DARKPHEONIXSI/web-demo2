import os
import sqlite3
import subprocess

database_url = os.getenv("DATABASE_URL")
required_pg_vars = ("PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD")
missing_pg_vars = [name for name in required_pg_vars if not os.getenv(name)]
if not database_url and missing_pg_vars:
    missing = ", ".join(missing_pg_vars)
    raise RuntimeError(
        "Set DATABASE_URL or explicit PostgreSQL environment variables "
        f"(missing: {missing})."
    )

db = sqlite3.connect("simar.db")
db.row_factory = sqlite3.Row

print("=== Products ===")
for r in db.execute("SELECT id, name, base_price FROM products").fetchall():
    print(f"  {r['id']}: {r['name']} - ${r['base_price']}")

print("\n=== Gallery Items ===")
for r in db.execute("SELECT id, title, tag, image_path FROM gallery_items").fetchall():
    print(f"  {r['id']}: {r['title']} - {r['tag']} - {r['image_path']}")

print("\n=== Posts ===")
for r in db.execute("SELECT id, title, status FROM posts").fetchall():
    print(f"  {r['id']}: {r['title']} - {r['status']}")

print("\n=== Users ===")
for r in db.execute("SELECT id, username, role FROM users").fetchall():
    print(f"  {r['id']}: {r['username']} - {r['role']}")

print(f"\nOrders: {db.execute('SELECT COUNT(*) as c FROM orders').fetchone()['c']}")
db.close()

# Check PostgreSQL
psql_command = [os.getenv("PSQL_PATH", "psql")]
if database_url:
    psql_command.extend(["--dbname", database_url])
psql_command.extend(
    [
        "--command",
        "SELECT count(*) AS products FROM products; "
        "SELECT count(*) AS posts FROM posts; "
        "SELECT count(*) AS gallery FROM gallery_items; "
        "SELECT count(*) AS users FROM users;",
    ]
)
try:
    subprocess.run(psql_command, check=True)
except subprocess.CalledProcessError:
    raise RuntimeError("PostgreSQL data check failed.") from None
