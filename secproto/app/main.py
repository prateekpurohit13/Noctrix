import os, json, time, base64, sqlite3, io, secrets
from typing import Optional, List
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Response, Header, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from passlib.hash import bcrypt
import jwt

from security.crypto import encrypt_at_rest, decrypt_at_rest
from security.kms import get_dek
from security.rbac import allowed
from security.audit import append_audit
from security.privacy import verify_anonymization

load_dotenv()
DB_PATH = os.getenv("SQLITE_PATH", "./data/app.db")
TENANT_ID = os.getenv("TENANT_ID", "demo")
JWT_ISSUER = os.getenv("JWT_ISSUER", "secproto")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "secproto-users")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "0") == "1"
JWT_ALG = "HS256"
JWT_SECRET = base64.b64decode(os.getenv("KEK_BASE64"))  # reuse KEK to sign dev JWTs

app = FastAPI(title="SecProto – Secure File Pipeline")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost:8443","http://localhost:8000","http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _conn():
    return sqlite3.connect(DB_PATH)

def _user_from_db(username: str):
    conn = _conn()
    c = conn.cursor()
    c.execute("SELECT id, username, password_hash, role FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "username": row[1], "password_hash": row[2], "role": row[3]}
    return None

def _get_request_ip(req: Request)->str:
    xff = req.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return req.client.host if req.client else "-"

def issue_tokens(user_id:int, username:str, role:str):
    now = int(time.time())
    csrf = base64.b64encode(os.urandom(16)).decode()
    payload = {
        "sub": str(user_id),
        "usr": username,
        "role": role,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": now,
        "exp": now + JWT_EXPIRE_MINUTES*60,
        "csrf": csrf
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)
    return token, csrf

def require_auth(req: Request, session: Optional[str]=Header(default=None, alias="Cookie"), x_csrf_token: Optional[str]=Header(default=None, alias="x-csrf-token")):
    # Extract "session" cookie manually
    token = None
    if req.cookies.get("session"):
        token = req.cookies.get("session")
    else:
        # fallback: allow Authorization: Bearer for tooling
        auth = req.headers.get("authorization")
        if auth and auth.lower().startswith("bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, JWT_SECRET, audience=JWT_AUDIENCE, algorithms=[JWT_ALG])
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    # CSRF for state-changing: if method is not GET/HEAD/OPTIONS
    if req.method not in ("GET","HEAD","OPTIONS"):
        csrf_claim = payload.get("csrf")
        hdr = req.headers.get("x-csrf-token")
        if not csrf_claim or not hdr or hdr != csrf_claim:
            raise HTTPException(status_code=403, detail="CSRF token missing or invalid")
    return payload

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/auth/login")
def login(req: Request, username: str, password: str):
    u = _user_from_db(username)
    if not u or not bcrypt.verify(password, u["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token, csrf = issue_tokens(u["id"], u["username"], u["role"])
    resp = JSONResponse({"ok": True, "role": u["role"], "csrf": csrf})
    resp.set_cookie("session", token, httponly=True, secure=COOKIE_SECURE, samesite="lax", max_age=JWT_EXPIRE_MINUTES*60)
    # Also expose csrf in a cookie for easy frontend access (non-HttpOnly)
    resp.set_cookie("csrf", csrf, httponly=False, secure=COOKIE_SECURE, samesite="lax", max_age=JWT_EXPIRE_MINUTES*60)
    append_audit(u["id"], u["role"], "auth:login", None, _get_request_ip(req), req.headers.get("user-agent","-"), True, "")
    return resp

@app.post("/auth/logout")
def logout(req: Request, user=Depends(require_auth)):
    resp = JSONResponse({"ok": True})
    resp.delete_cookie("session")
    resp.delete_cookie("csrf")
    append_audit(int(user["sub"]), user["role"], "auth:logout", None, _get_request_ip(req), req.headers.get("user-agent","-"), True, "")
    return resp

@app.post("/upload")
async def upload_file(req: Request, file: UploadFile = File(...), user=Depends(require_auth)):
    role = user.get("role")
    if not allowed(role, "upload:create"):
        raise HTTPException(status_code=403, detail="insufficient permissions")
    content = await file.read()
    dek = get_dek(TENANT_ID, "uploads")
    blob = encrypt_at_rest(content, dek)
    row = {
        "tenant_id": TENANT_ID,
        "purpose": "raw",
        "filename": file.filename,
        "blob_json": json.dumps(blob),
        "created_at": int(time.time()),
    }
    # minimization: store only fields we allow
    # (in this MVP we trust row keys)
    conn = _conn()
    c = conn.cursor()
    c.execute("INSERT INTO assets(tenant_id,purpose,filename,blob_json,created_at) VALUES(?,?,?,?,?)",
              (row["tenant_id"], row["purpose"], row["filename"], row["blob_json"], row["created_at"]))
    asset_id = c.lastrowid
    conn.commit()
    conn.close()
    append_audit(int(user["sub"]), role, "upload:create", asset_id, _get_request_ip(req), req.headers.get("user-agent","-"), True, file.filename)
    return {"ok": True, "asset_id": asset_id}

@app.get("/asset/{asset_id}")
def get_asset(req: Request, asset_id: int, user=Depends(require_auth)):
    role = user.get("role")
    if not allowed(role, "asset:read"):
        raise HTTPException(status_code=403, detail="insufficient permissions")
    conn = _conn()
    c = conn.cursor()
    c.execute("SELECT tenant_id, purpose, filename, blob_json FROM assets WHERE id=?", (asset_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="asset not found")
    tenant_id, purpose, filename, blob_json = row
    blob = json.loads(blob_json)
    dek = get_dek(tenant_id, "uploads")
    content = decrypt_at_rest(blob, dek)
    append_audit(int(user["sub"]), role, "asset:read", asset_id, _get_request_ip(req), req.headers.get("user-agent","-"), True, filename or "")
    # For demo: return first 128 bytes length so we don't dump file
    head = content[:128]
    return {"filename": filename, "size_bytes": len(content), "head_sample_base64": base64.b64encode(head).decode()}

@app.post("/privacy/verify")
def privacy_verify(req: Request, cleansed_text: str, known_pii: Optional[List[str]] = None, user=Depends(require_auth)):
    result = verify_anonymization(cleansed_text, known_pii or [])
    append_audit(int(user["sub"]), user["role"], "privacy:verify", None, _get_request_ip(req), req.headers.get("user-agent","-"), result["ok"], "")
    return result
