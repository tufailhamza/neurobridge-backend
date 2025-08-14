# src/models/collections.py
from .base import Base
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
    func,
)
from sqlalchemy.orm import relationship

class Collection(Base):
    __tablename__ = "collections"
    __table_args__ = {"schema": "ariadne"}

    collection_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("ariadne.users.user_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to User
    user = relationship("User", back_populates="collections")
