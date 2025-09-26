from pydantic import BaseModel, Field
from typing import Literal, List, Optional
from datetime import datetime

Role = Literal["Admin","Analyst","Viewer"]

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=1, max_length=2048)  # long allowed, safely sliced for bcrypt
    role: Role

class UserOut(BaseModel):
    id: int
    username: str
    role: Role
    created_at: datetime
    class Config:
        from_attributes = True

class LoginIn(BaseModel):
    username: str
    password: str

class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class AnalyticsSummary(BaseModel):
    total_users: int
    files_processed_last_7d: int
    login_success: int
    login_failed: int

class UsagePoint(BaseModel):
    bucket: str
    jobs_count: int
    logins_count: int

class UsageSeries(BaseModel):
    granularity: Literal["day","week","month"]
    points: List[UsagePoint]

class RecentEvent(BaseModel):
    id: int
    event_type: str
    actor_username: Optional[str]
    success: Optional[bool]
    created_at: datetime

class RecentEventsPage(BaseModel):
    items: List[RecentEvent]
    next_offset: Optional[int] = None
