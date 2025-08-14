# src/models/user_tracking.py
from .base import Base
from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    ForeignKey,
    func,
)
from sqlalchemy.orm import relationship

class UserTracking(Base):
    __tablename__ = "user_tracking"
    __table_args__ = {"schema": "ariadne"}

    user_id = Column(Integer, ForeignKey("ariadne.users.user_id", ondelete="CASCADE"), primary_key=True)
    login_count = Column(Integer, nullable=False, default=0)
    viewed_posts_count = Column(Integer, nullable=False, default=0)
    bought_posts_count = Column(Integer, nullable=False, default=0)
    profile_view_count = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship to User table
    user = relationship("User", back_populates="user_tracking")
