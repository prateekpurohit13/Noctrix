import os, time, base64
import psycopg2
from dotenv import load_dotenv
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from .crypto import generate_dek, ALG

load_dotenv()
POSTGRES_DSN = f"dbname='{os.getenv('POSTGRES_DB')}' user='{os.getenv('POSTGRES_USER')}' password='{os.getenv('POSTGRES_PASSWORD')}' host='{os.getenv('POSTGRES_HOST')}' port='{os.getenv('POSTGRES_PORT')}'"
KEK = base64.b64decode(os.getenv("KEK_BASE64", "")) if os.getenv("KEK_BASE64") else None
if not KEK:
    raise RuntimeError("KEK_BASE64 not set in environment. Set a base64-encoded 32-byte key.")

def _conn():
    return psycopg2.connect(POSTGRES_DSN)

def get_dek(tenant_id: str, purpose: str) -> bytes:
    conn = _conn()
    c = conn.cursor()
    c.execute("SELECT alg, dek_ct, dek_nonce FROM keys WHERE tenant_id=%s AND purpose=%s",
              (tenant_id, purpose))
    row = c.fetchone()
    if row:
        alg, dek_ct, dek_nonce = row
        if alg != ALG:
            raise RuntimeError(f"Unsupported alg {alg}")
        aes = AESGCM(KEK)
        dek = aes.decrypt(dek_nonce.tobytes() if hasattr(dek_nonce, 'tobytes') else dek_nonce, 
                          dek_ct.tobytes() if hasattr(dek_ct, 'tobytes') else dek_ct, None)
        conn.close()
        return dek
    # create new DEK
    dek = generate_dek()
    aes = AESGCM(KEK)
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, dek, None)
    c.execute("INSERT INTO keys(tenant_id,purpose,alg,dek_ct,dek_nonce,created_at) VALUES(%s,%s,%s,%s,%s,%s)",
              (tenant_id, purpose, ALG, psycopg2.Binary(ct), psycopg2.Binary(nonce), int(time.time())))
    conn.commit()
    conn.close()
    return dek