import psycopg2

try:
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/resume_parser")
    print("✅ DB connection OK")
    conn.close()
except Exception as e:
    print("❌ DB connection failed:", e)
