import os, sqlite3, base64, time, json
from dotenv import load_dotenv
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

load_dotenv()
db_path = os.getenv("SQLITE_PATH", "./data/app.db")
new_kek_b64 = os.getenv("NEW_KEK_BASE64")
if not new_kek_b64:
    raise SystemExit("Set NEW_KEK_BASE64 (base64 32 bytes) in env before running rotation.")

new_kek = base64.b64decode(new_kek_b64)
old_kek = base64.b64decode(os.getenv("KEK_BASE64"))

conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT tenant_id, purpose, alg, dek_ct, dek_nonce FROM keys")
rows = c.fetchall()

for tenant_id, purpose, alg, dek_ct, dek_nonce in rows:
    if alg != "AES-256-GCM":
        print(f"[skip] Unsupported alg for {tenant_id}/{purpose}: {alg}")
        continue
    # unwrap using old KEK
    aes_old = AESGCM(old_kek)
    dek = aes_old.decrypt(dek_nonce, dek_ct, None)
    # rewrap using new KEK
    aes_new = AESGCM(new_kek)
    import os as _os
    nonce = _os.urandom(12)
    ct = aes_new.encrypt(nonce, dek, None)
    c.execute("UPDATE keys SET dek_ct=?, dek_nonce=? WHERE tenant_id=? AND purpose=?",
              (ct, nonce, tenant_id, purpose))
    print(f"[rotate] Rewrapped DEK for {tenant_id}/{purpose}")

conn.commit()
conn.close()
print("[rotate] Done. Remember to update KEK_BASE64 in .env to NEW_KEK_BASE64.")
