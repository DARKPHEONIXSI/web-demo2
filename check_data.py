import sqlite3, os
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
os.environ['PGPASSWORD'] = 'onice_pass_2026'
os.system('"C:\\Program Files\\PostgreSQL\\16\\bin\\psql.exe" -U onice_user -d onice -c "SELECT count(*) as products FROM products; SELECT count(*) as posts FROM posts; SELECT count(*) as gallery FROM gallery_items; SELECT count(*) as users FROM users;"')
