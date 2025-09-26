from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, text
from sqlalchemy.orm import Session, selectinload
from datetime import datetime, timedelta
from typing import Literal
from ..db import SessionLocal
from ..models import User, Audit, Job
from ..schemas import UserCreate, UserOut, AnalyticsSummary, UsageSeries, UsagePoint, RecentEventsPage, RecentEvent
from ..security import admin_required, hash_password, TokenUser

router = APIRouter(prefix="/admin", tags=["Admin"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/users", response_model=UserOut)
def add_user(payload: UserCreate, admin: TokenUser = Depends(admin_required), db: Session = Depends(get_db)):
    exists = db.scalar(select(func.count()).select_from(User).where(User.username == payload.username))
    if exists:
        raise HTTPException(status_code=409, detail="Username already exists")
    u = User(username=payload.username, password_hash=hash_password(payload.password), role=payload.role)
    db.add(u); db.flush()
    db.add(Audit(event_type="admin:user_created", actor_user_id=admin.sub, metadata_hash=None, success=True))
    db.commit(); db.refresh(u)
    return u

@router.delete("/users/{user_id}", status_code=204)
def remove_user(user_id: int, admin: TokenUser = Depends(admin_required), db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(u)
    db.add(Audit(event_type="admin:user_deleted", actor_user_id=admin.sub, metadata_hash=None, success=True))
    db.commit()
    return

@router.get("/users", response_model=list[UserOut])
def list_users(admin: TokenUser = Depends(admin_required), db: Session = Depends(get_db)):
    users = db.execute(select(User)).scalars().all()
    return users

@router.get("/analytics/summary", response_model=AnalyticsSummary)
def analytics_summary(admin: TokenUser = Depends(admin_required), db: Session = Depends(get_db)):
    total_users = db.scalar(select(func.count()).select_from(User)) or 0
    since = datetime.utcnow() - timedelta(days=7)
    files_processed_last_7d = db.scalar(
        select(func.count()).select_from(Job).where(Job.created_at >= since, Job.status == "completed")
    ) or 0
    login_success = db.scalar(
        select(func.count()).select_from(Audit).where(Audit.event_type == "auth:login_success")
    ) or 0
    login_failed = db.scalar(
        select(func.count()).select_from(Audit).where(Audit.event_type == "auth:login_failed")
    ) or 0
    return {
        "total_users": total_users,
        "files_processed_last_7d": files_processed_last_7d,
        "login_success": login_success,
        "login_failed": login_failed,
    }

@router.get("/analytics/usage_over_time", response_model=UsageSeries)
def usage_over_time(
    granularity: Literal["day","week","month"] = "day",
    days: int = 30,
    admin: TokenUser = Depends(admin_required),
    db: Session = Depends(get_db)
):
    since = datetime.utcnow() - timedelta(days=days)
    fmt = "%Y-%m-%d" if granularity in ("day","week") else "%Y-%m"
    jobs_rows = db.execute(text(f"""
        SELECT strftime('{fmt}', created_at) AS bucket, COUNT(*) as c
        FROM jobs
        WHERE datetime(created_at) >= datetime(:since)
        GROUP BY 1 ORDER BY 1
    """), {"since": since}).all()
    logins_rows = db.execute(text(f"""
        SELECT strftime('{fmt}', created_at) AS bucket, COUNT(*) as c
        FROM audit
        WHERE datetime(created_at) >= datetime(:since) AND event_type = 'auth:login_success'
        GROUP BY 1 ORDER BY 1
    """), {"since": since}).all()
    jobs_map = {r.bucket: r.c for r in jobs_rows}
    logins_map = {r.bucket: r.c for r in logins_rows}
    buckets = sorted(set(jobs_map) | set(logins_map))
    points = [UsagePoint(bucket=b, jobs_count=jobs_map.get(b,0), logins_count=logins_map.get(b,0)) for b in buckets]
    return {"granularity": granularity, "points": points}

@router.get("/analytics/recent_activity", response_model=RecentEventsPage)
def recent_activity(limit: int = 25, offset: int = 0, admin: TokenUser = Depends(admin_required), db: Session = Depends(get_db)):
    stmt = select(Audit).options(selectinload(Audit.actor)).order_by(Audit.created_at.desc()).limit(limit).offset(offset)
    rows = db.execute(stmt).scalars().all()
    items = [RecentEvent(
        id=a.id,
        event_type=a.event_type,
        actor_username=(a.actor.username if a.actor else None),
        success=a.success,
        created_at=a.created_at
    ) for a in rows]
    next_offset = offset + limit if len(items) == limit else None
    return {"items": items, "next_offset": next_offset}
