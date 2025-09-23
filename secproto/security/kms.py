import os, sqlite3, time, base64
from dotenv import load_dotenv
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from .crypto import generate_dek, ALG

load_dotenv()
DB_PATH = os.getenv("SQLITE_PATH", "./data/app.db")
KEK = base64.b64decode(os.getenv("KEK_BASE64", "")) if os.getenv("KEK_BASE64") else None
if not KEK:
    raise RuntimeError("KEK_BASE64 not set in environment. Set a base64-encoded 32-byte key.")

def _conn():
    return sqlite3.connect(DB_PATH)

def get_dek(tenant_id: str, purpose: str) -> bytes:
    conn = _conn()
    c = conn.cursor()
    c.execute("SELECT alg, dek_ct, dek_nonce FROM keys WHERE tenant_id=? AND purpose=?",
              (tenant_id, purpose))
    row = c.fetchone()
    if row:
        alg, dek_ct, dek_nonce = row
        if alg != ALG:
            raise RuntimeError(f"Unsupported alg {alg}")
        aes = AESGCM(KEK)
        dek = aes.decrypt(dek_nonce, dek_ct, None)
        conn.close()
        return dek
    # create new DEK
    dek = generate_dek()
    aes = AESGCM(KEK)
    import os as _os
    nonce = _os.urandom(12)
    ct = aes.encrypt(nonce, dek, None)
    c.execute("INSERT INTO keys(tenant_id,purpose,alg,dek_ct,dek_nonce,created_at) VALUES(?,?,?,?,?,?)",
              (tenant_id, purpose, ALG, ct, nonce, int(time.time())))
    conn.commit()
    conn.close()
    return dek
