import os
import psycopg2
from dotenv import load_dotenv
from passlib.hash import bcrypt

load_dotenv()
try:
    conn = psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT")
    )
    c = conn.cursor()
    print("[init] Connected to PostgreSQL successfully.")
except Exception as e:
    print(f"[init] ERROR: Could not connect to PostgreSQL. Please check your .env file. Error: {e}")
    exit(1)

# Users table with refresh token columns
c.execute("""CREATE TABLE IF NOT EXISTS users(
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    refresh_token_hash TEXT,
    refresh_token_expires_at TIMESTAMP WITH TIME ZONE
)""")

# Keys table
c.execute("""CREATE TABLE IF NOT EXISTS keys(
    tenant_id TEXT NOT NULL,
    purpose TEXT NOT NULL,
    alg TEXT NOT NULL,
    dek_ct BYTEA NOT NULL,
    dek_nonce BYTEA NOT NULL,
    created_at BIGINT NOT NULL,
    PRIMARY KEY(tenant_id, purpose)
)""")

# Assets table
c.execute("""CREATE TABLE IF NOT EXISTS assets(
    id SERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    purpose TEXT NOT NULL,
    filename TEXT,
    blob_json TEXT NOT NULL,
    created_at BIGINT NOT NULL
)""")

# Audit table
c.execute("""CREATE TABLE IF NOT EXISTS audit(
    id SERIAL PRIMARY KEY,
    ts BIGINT NOT NULL,
    user_id INTEGER,
    role TEXT,
    action TEXT NOT NULL,
    object_id TEXT,
    ip TEXT,
    user_agent TEXT,
    success BOOLEAN NOT NULL,
    details_hash TEXT
)""")

# --- Seed Users ---
c.execute("SELECT COUNT(*) FROM users")
if c.fetchone()[0] == 0:
    admin_user = os.getenv("ADMIN_USERNAME", "admin")
    admin_pass = os.getenv("ADMIN_PASSWORD", "Admin@12345")
    analyst_user = os.getenv("ANALYST_USERNAME", "analyst")
    analyst_pass = os.getenv("ANALYST_PASSWORD", "Analyst@12345")
    
    c.execute("INSERT INTO users(username,password_hash,role) VALUES(%s,%s,%s)",
              (admin_user, bcrypt.hash(admin_pass), "Admin"))
    c.execute("INSERT INTO users(username,password_hash,role) VALUES(%s,%s,%s)",
              (analyst_user, bcrypt.hash(analyst_pass), "Analyst"))
    print(f"[init] Seeded users: {admin_user}/Admin, {analyst_user}/Analyst")
else:
    print("[init] Users already present.")

conn.commit()
c.close()
conn.close()
print(f"[init] PostgreSQL DB is ready.")