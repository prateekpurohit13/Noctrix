import bcrypt
from fastapi import HTTPException, Depends
from jose import jwt, JWTError
from pydantic import BaseModel
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os, time

oauth2_scheme = HTTPBearer()

JWT_SECRET = os.getenv("JWT_SECRET", "change_me")
JWT_ALG = "HS256"
JWT_TTL_SECONDS = int(os.getenv("JWT_TTL_SECONDS", "86400"))

def _slice72(password: str) -> bytes:
    return password.encode("utf-8")[:72]

def hash_password(password: str) -> str:
    return bcrypt.hashpw(_slice72(password), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(_slice72(password), hashed.encode())

class TokenUser(BaseModel):
    sub: int
    username: str
    role: str

def create_token(sub: int, username: str, role: str) -> str:
    now = int(time.time())
    payload = {"sub": str(sub), "username": username, "role": role, "iat": now, "exp": now + JWT_TTL_SECONDS}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def get_current_user(token: HTTPAuthorizationCredentials = Depends(oauth2_scheme)) -> TokenUser:
    try:
        payload = jwt.decode(token.credentials, JWT_SECRET, algorithms=[JWT_ALG])
        return TokenUser(sub=int(payload["sub"]), username=payload["username"], role=payload["role"])

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def admin_required(user: TokenUser = Depends(get_current_user)) -> TokenUser:
    if user.role != "Admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user
