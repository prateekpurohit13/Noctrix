import os, time
import psycopg2
from dotenv import load_dotenv

load_dotenv()
POSTGRES_DSN = f"dbname='{os.getenv('POSTGRES_DB')}' user='{os.getenv('POSTGRES_USER')}' password='{os.getenv('POSTGRES_PASSWORD')}' host='{os.getenv('POSTGRES_HOST')}' port='{os.getenv('POSTGRES_PORT')}'"
conn = psycopg2.connect(POSTGRES_DSN)
c = conn.cursor()

now = int(time.time())
def days(name, default):
    try:
        return int(os.getenv(name, str(default)))
    except:
        return default

ret_raw = days("RETENTION_RAW_UPLOAD", 7)
ret_clean = days("RETENTION_CLEANSED_ASSET", 90)
ret_audit = days("RETENTION_AUDIT", 365)

# Purge assets by purpose
def purge_assets(purpose, retention_days):
    cutoff = now - retention_days*86400
    c.execute("DELETE FROM assets WHERE purpose=%s AND created_at < %s", (purpose, cutoff))
    print(f"[purge] assets purpose={purpose} older than {retention_days}d removed: {c.rowcount}")

purge_assets("raw", ret_raw)
purge_assets("cleansed", ret_clean)

# Purge audit
cutoff_audit = now - ret_audit*86400
c.execute("DELETE FROM audit WHERE ts < %s", (cutoff_audit,))
print(f"[purge] audit older than {ret_audit}d removed: {c.rowcount}")

conn.commit()
conn.close()