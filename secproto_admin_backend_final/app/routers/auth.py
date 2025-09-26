from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..db import SessionLocal, Base, engine
from ..models import User, Audit
from ..schemas import LoginIn, LoginOut
from ..security import verify_password, create_token

router = APIRouter(prefix="/auth", tags=["Auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

Base.metadata.create_all(bind=engine)

@router.post("/login", response_model=LoginOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.username == payload.username)).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        db.add(Audit(event_type="auth:login_failed", actor_user_id=(user.id if user else None), metadata_hash=None, success=False))
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user.id, user.username, user.role)
    db.add(Audit(event_type="auth:login_success", actor_user_id=user.id, metadata_hash=None, success=True))
    db.commit()
    return {"access_token": token, "token_type": "bearer"}
