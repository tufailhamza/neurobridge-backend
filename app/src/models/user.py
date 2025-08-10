# src/models/user.py
from .base import Base
from sqlalchemy import (
    Column,
    String,
    Integer,
    Enum,
    DateTime,
    Boolean,
    func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
import enum

class UserRole(enum.Enum):
    clinician = "clinician"
    caretaker = "caretaker"
    admin = "admin"

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "ariadne"}

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True)
    role = Column(Enum(UserRole), nullable=False)

    child_diagnosis = Column(String, nullable=True)
    location = Column(String, nullable=True)

    account_create_date = Column(DateTime(timezone=True), server_default=func.now())
    content_preferences = Column(JSONB, nullable=True)
    messaging_enabled = Column(Boolean, default=True)

    last_active_at = Column(DateTime(timezone=True), nullable=True)
    last_engagement_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
