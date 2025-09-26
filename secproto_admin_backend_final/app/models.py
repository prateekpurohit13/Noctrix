from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # 'Admin','Analyst','Viewer'
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class Audit(Base):
    __tablename__ = "audit"
    id = Column(Integer, primary_key=True)
    event_type = Column(String, nullable=False)
    actor_user_id = Column(Integer, ForeignKey("users.id"))
    metadata_hash = Column(Text)
    success = Column(Boolean)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    actor = relationship("User", backref="audit_events", lazy="joined")

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, nullable=False)  # e.g., 'completed','failed'
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
