import os, sqlite3, time
from dotenv import load_dotenv
from passlib.hash import bcrypt

load_dotenv()
db_path = os.getenv("SQLITE_PATH", "./data/app.db")
os.makedirs(os.path.dirname(db_path), exist_ok=True)
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Users table
c.execute("""CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL
)""")

# Keys table (stores DEKs wrapped by KEK)
c.execute("""CREATE TABLE IF NOT EXISTS keys(
    tenant_id TEXT NOT NULL,
    purpose TEXT NOT NULL,
    alg TEXT NOT NULL,
    dek_ct BLOB NOT NULL,
    dek_nonce BLOB NOT NULL,
    created_at INTEGER NOT NULL,
    PRIMARY KEY(tenant_id, purpose)
)""")

# Assets table (encrypted blobs at-rest)
c.execute("""CREATE TABLE IF NOT EXISTS assets(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,
    purpose TEXT NOT NULL,
    filename TEXT,
    blob_json TEXT NOT NULL,
    created_at INTEGER NOT NULL
)""")

# Audit table (append-only)
c.execute("""CREATE TABLE IF NOT EXISTS audit(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER NOT NULL,
    user_id INTEGER,
    role TEXT,
    action TEXT NOT NULL,
    object_id TEXT,
    ip TEXT,
    user_agent TEXT,
    success INTEGER NOT NULL,
    details_hash TEXT
)""")

# Seed users if empty
c.execute("SELECT COUNT(*) FROM users")
if c.fetchone()[0] == 0:
    admin_user = os.getenv("ADMIN_USERNAME", "admin")
    admin_pass = os.getenv("ADMIN_PASSWORD", "Admin@12345")
    analyst_user = os.getenv("ANALYST_USERNAME", "analyst")
    analyst_pass = os.getenv("ANALYST_PASSWORD", "Analyst@12345")
    c.execute("INSERT INTO users(username,password_hash,role) VALUES(?,?,?)",
              (admin_user, bcrypt.hash(admin_pass), "Admin"))
    c.execute("INSERT INTO users(username,password_hash,role) VALUES(?,?,?)",
              (analyst_user, bcrypt.hash(analyst_pass), "Analyst"))
    print(f"[init] Seeded users: {admin_user}/Admin, {analyst_user}/Analyst")
else:
    print("[init] Users already present.")

conn.commit()
conn.close()
print(f"[init] DB ready at {db_path}")
