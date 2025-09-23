# SecProto – Starter (Data Security & Privacy Layer)

This is a minimal FastAPI starter that demonstrates:
- **At-Rest Encryption (AES‑256‑GCM)** with per-tenant DEKs and a KEK.
- **TLS-ready** via a local Caddy reverse proxy (TLS 1.3).
- **RBAC (least privilege)** checks per action.
- **Audit Logging** for auth, uploads, reads, and privacy checks.
- **Session Management** using HttpOnly JWT cookie + CSRF token.
- **Retention Jobs** via a simple purge script.
- **Anonymization Verification** utility endpoint.

## Quickstart

1. **Install Python 3.10+**, then:
   ```bash
   cd secproto
   python -m venv .venv
   . .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Create `.env`** from example and set KEK:
   ```bash
   cp .env.example .env
   # Generate a base64 32-byte key:
   python - << 'PY'
import os, base64
print(base64.b64encode(os.urandom(32)).decode())
PY
   # paste into KEK_BASE64=...
   ```

3. **Init DB** and seed demo users:
   ```bash
   python scripts/init_db.py
   ```

4. **Run API**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

5. **(Recommended) Enable local TLS 1.3** with Caddy:
   - Install Caddy (https://caddyserver.com/docs/install)
   - Run:
     ```bash
     cd caddy
     caddy run --config Caddyfile
     ```
   - Set `COOKIE_SECURE=1` in `.env` and restart the API.
   - Use **https://localhost:8443**

## Try it

- **Login** (Admin or Analyst):
  ```bash
  curl -i -X POST http://127.0.0.1:8000/auth/login -d "username=analyst" -d "password=Analyst@12345"
  ```
  Copy the `set-cookie: session=...` and `csrf` cookie value.

- **Upload** a file (needs CSRF header + cookie):
  ```bash
  curl -b "session=<paste>" -b "csrf=<csrfcookie>" -H "x-csrf-token: <csrfcookie>" \
       -F "file=@README.md" http://127.0.0.1:8000/upload
  ```

- **Read** the asset:
  ```bash
  curl -b "session=<paste>" http://127.0.0.1:8000/asset/1
  ```

- **Privacy Verify**:
  ```bash
  curl -b "session=<paste>" -H "x-csrf-token: <csrfcookie>" \
       -X POST "http://127.0.0.1:8000/privacy/verify" \
       -d "cleansed_text=hello user@example.com" -d "known_pii=user@example.com"
  ```

## Rotation & Retention

- **Rotate KEK (rewrap DEKs)**:
  ```bash
  export NEW_KEK_BASE64=$(python - << 'PY'
import os, base64; print(base64.b64encode(os.urandom(32)).decode())
PY
  )
  NEW_KEK_BASE64=$NEW_KEK_BASE64 KEK_BASE64=$(grep KEK_BASE64 .env | cut -d= -f2) python scripts/rotate_keys.py
  # Then update KEK_BASE64 in .env to NEW_KEK_BASE64
  ```

- **Retention purge** (delete old assets/audit by policy):
  ```bash
  python scripts/purge.py
  ```

## Notes

- This is a teaching/prototype scaffold. For production, integrate a cloud KMS, structured audit export to SIEM, and real user management (DB + password policy + lockouts + MFA).
