# test_db.py
import os
from sqlalchemy import create_engine

url = os.getenv("DATABASE_URL")
print("PYTHON sees DATABASE_URL:", repr(url))
if not url:
    raise SystemExit("DATABASE_URL is not set for Python -- fix your shell env or .env loader.")
engine = create_engine(url, pool_pre_ping=True)
with engine.connect() as conn:
    print(conn.exec_driver_sql("SELECT version();").all())
