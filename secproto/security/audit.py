import os, sqlite3, time, hashlib
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("SQLITE_PATH", "./data/app.db")

def _conn():
    return sqlite3.connect(DB_PATH)

def append_audit(user_id, role, action, object_id, ip, user_agent, success=True, details: str = ""):
    conn = _conn()
    c = conn.cursor()
    dh = hashlib.sha256(details.encode("utf-8")).hexdigest() if details else None
    c.execute("""INSERT INTO audit(ts,user_id,role,action,object_id,ip,user_agent,success,details_hash)
                 VALUES(?,?,?,?,?,?,?,?,?)""",
              (int(time.time()), user_id, role, action, str(object_id) if object_id is not None else None,
               ip, user_agent, 1 if success else 0, dh))
    conn.commit()
    conn.close()
