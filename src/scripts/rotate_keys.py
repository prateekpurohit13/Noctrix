import os, base64, time
import psycopg2
from dotenv import load_dotenv
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

load_dotenv()
POSTGRES_DSN = f"dbname='{os.getenv('POSTGRES_DB')}' user='{os.getenv('POSTGRES_USER')}' password='{os.getenv('POSTGRES_PASSWORD')}' host='{os.getenv('POSTGRES_HOST')}' port='{os.getenv('POSTGRES_PORT')}'"
new_kek_b64 = os.getenv("NEW_KEK_BASE64")
if not new_kek_b64:
    raise SystemExit("Set NEW_KEK_BASE64 (base64 32 bytes) in env before running rotation.")

new_kek = base64.b64decode(new_kek_b64)
old_kek = base64.b64decode(os.getenv("KEK_BASE64"))

conn = psycopg2.connect(POSTGRES_DSN)
c = conn.cursor()

c.execute("SELECT tenant_id, purpose, alg, dek_ct, dek_nonce FROM keys")
rows = c.fetchall()

for tenant_id, purpose, alg, dek_ct, dek_nonce in rows:
    if alg != "AES-256-GCM":
        print(f"[skip] Unsupported alg for {tenant_id}/{purpose}: {alg}")
        continue
    # unwrap using old KEK
    aes_old = AESGCM(old_kek)
    dek = aes_old.decrypt(dek_nonce.tobytes() if hasattr(dek_nonce, 'tobytes') else dek_nonce, 
                          dek_ct.tobytes() if hasattr(dek_ct, 'tobytes') else dek_ct, None)
    # rewrap using new KEK
    aes_new = AESGCM(new_kek)
    nonce = os.urandom(12)
    ct = aes_new.encrypt(nonce, dek, None)
    c.execute("UPDATE keys SET dek_ct=%s, dek_nonce=%s WHERE tenant_id=%s AND purpose=%s",
              (psycopg2.Binary(ct), psycopg2.Binary(nonce), tenant_id, purpose))
    print(f"[rotate] Rewrapped DEK for {tenant_id}/{purpose}")

conn.commit()
conn.close()
print("[rotate] Done. Remember to update KEK_BASE64 in .env to NEW_KEK_BASE64.")