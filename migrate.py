import sqlite3

db = sqlite3.connect("simar.db")
cursor = db.cursor()

# ─── Add JWT columns to users ────────────────────────────────
try:
    cursor.execute("ALTER TABLE users ADD COLUMN jwt_token TEXT DEFAULT NULL")
    print("Added jwt_token to users")
except sqlite3.OperationalError as e:
    if "duplicate column" not in str(e).lower():
        raise

try:
    cursor.execute("ALTER TABLE users ADD COLUMN jwt_expires_at TIMESTAMP DEFAULT NULL")
    print("Added jwt_expires_at to users")
except sqlite3.OperationalError as e:
    if "duplicate column" not in str(e).lower():
        raise

# ─── Add order_token and Razorpay columns to orders ──────────
# Need to add without UNIQUE first, then populate, then create unique index

# order_token
try:
    cursor.execute("ALTER TABLE orders ADD COLUMN order_token TEXT DEFAULT NULL")
    print("Added order_token to orders")
except sqlite3.OperationalError as e:
    if "duplicate column" not in str(e).lower():
        raise

# Populate order_token for existing rows
cursor.execute(
    """
    UPDATE orders
    SET order_token = hex(randomblob(16))
    WHERE order_token IS NULL
"""
)
print(f"Populated order_token for {cursor.rowcount} existing orders")

# Now add unique index
try:
    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_orders_order_token ON orders(order_token)"
    )
    print("Created unique index idx_orders_order_token")
except sqlite3.OperationalError as e:
    if "already exists" not in str(e).lower():
        raise

# razorpay_payment_id
try:
    cursor.execute(
        "ALTER TABLE orders ADD COLUMN razorpay_payment_id TEXT DEFAULT NULL"
    )
    print("Added razorpay_payment_id to orders")
except sqlite3.OperationalError as e:
    if "duplicate column" not in str(e).lower():
        raise

try:
    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_orders_razorpay_payment ON orders(razorpay_payment_id)"
    )
    print("Created unique index idx_orders_razorpay_payment")
except sqlite3.OperationalError as e:
    if "already exists" not in str(e).lower():
        raise

# razorpay_order_id
try:
    cursor.execute("ALTER TABLE orders ADD COLUMN razorpay_order_id TEXT DEFAULT NULL")
    print("Added razorpay_order_id to orders")
except sqlite3.OperationalError as e:
    if "duplicate column" not in str(e).lower():
        raise

# paytm_txn_id
try:
    cursor.execute("ALTER TABLE orders ADD COLUMN paytm_txn_id TEXT DEFAULT NULL")
    print("Added paytm_txn_id to orders")
except sqlite3.OperationalError as e:
    if "duplicate column" not in str(e).lower():
        raise

try:
    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_orders_paytm_txn ON orders(paytm_txn_id)"
    )
    print("Created unique index idx_orders_paytm_txn")
except sqlite3.OperationalError as e:
    if "already exists" not in str(e).lower():
        raise

# customer_email
try:
    cursor.execute("ALTER TABLE orders ADD COLUMN customer_email TEXT DEFAULT NULL")
    print("Added customer_email to orders")
except sqlite3.OperationalError as e:
    if "duplicate column" not in str(e).lower():
        raise

# customer_phone
try:
    cursor.execute("ALTER TABLE orders ADD COLUMN customer_phone TEXT DEFAULT NULL")
    print("Added customer_phone to orders")
except sqlite3.OperationalError as e:
    if "duplicate column" not in str(e).lower():
        raise

# status
try:
    cursor.execute(
        'ALTER TABLE orders ADD COLUMN status TEXT NOT NULL DEFAULT "completed"'
    )
    print("Added status to orders")
except sqlite3.OperationalError as e:
    if "duplicate column" not in str(e).lower():
        raise

# Add CHECK constraint via trigger (SQLite doesn't support ALTER TABLE ADD CHECK)
try:
    cursor.execute(
        """
        CREATE TRIGGER IF NOT EXISTS check_orders_status
        BEFORE INSERT ON orders
        FOR EACH ROW
        BEGIN
            SELECT CASE
                WHEN NEW.status NOT IN ('pending','completed','failed','refunded')
                THEN RAISE(ABORT, 'Invalid order status')
            END;
        END
    """
    )
    print("Created trigger check_orders_status for INSERT")
except sqlite3.OperationalError as e:
    if "already exists" not in str(e).lower():
        raise

try:
    cursor.execute(
        """
        CREATE TRIGGER IF NOT EXISTS check_orders_status_update
        BEFORE UPDATE ON orders
        FOR EACH ROW
        BEGIN
            SELECT CASE
                WHEN NEW.status NOT IN ('pending','completed','failed','refunded')
                THEN RAISE(ABORT, 'Invalid order status')
            END;
        END
    """
    )
    print("Created trigger check_orders_status_update for UPDATE")
except sqlite3.OperationalError as e:
    if "already exists" not in str(e).lower():
        raise

# ─── Create index for faster JWT lookups ─────────────────────
try:
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_jwt_token ON users(jwt_token)")
    print("Created index idx_users_jwt_token")
except sqlite3.OperationalError as e:
    if "already exists" not in str(e).lower():
        raise

db.commit()
db.close()
print("Migration completed successfully.")
