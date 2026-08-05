"""Initialize or update the local database schema.

This project uses additive runtime migrations in models.ensure_runtime_schema()
plus schema.sql for fresh SQLite databases.
"""

from app import create_app
from models import ensure_runtime_schema, init_db

app = create_app()
with app.app_context():
    init_db()
    ensure_runtime_schema()
    print("Database schema is up to date.")
