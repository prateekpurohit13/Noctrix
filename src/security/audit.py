import os, time, hashlib
import psycopg2
from dotenv import load_dotenv

load_dotenv()
POSTGRES_DSN = f"dbname='{os.getenv('POSTGRES_DB')}' user='{os.getenv('POSTGRES_USER')}' password='{os.getenv('POSTGRES_PASSWORD')}' host='{os.getenv('POSTGRES_HOST')}' port='{os.getenv('POSTGRES_PORT')}'"

def append_audit(user_id, role, action, object_id, ip, user_agent, success=True, details: str = ""):
    conn = psycopg2.connect(POSTGRES_DSN)
    c = conn.cursor()
    dh = hashlib.sha256(details.encode("utf-8")).hexdigest() if details else None
    c.execute("""INSERT INTO audit(ts,user_id,role,action,object_id,ip,user_agent,success,details_hash)
                 VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
              (int(time.time()), user_id, role, action, str(object_id) if object_id is not None else None,
               ip, user_agent, bool(success), dh))
    conn.commit()
    conn.close()