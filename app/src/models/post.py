# src/models/post.py
from .base import Base
from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    Boolean,
    Float,
    DateTime,
    func,
    ForeignKey
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
import enum

class TierEnum(enum.Enum):
    free = "free"
    premium = "premium"
    exclusive = "exclusive"

class Post(Base):
    __tablename__ = "posts"
    __table_args__ = {"schema": "ariadne"}

    id = Column(String, primary_key=True, index=True)
    image_url = Column(String, nullable=False)
    title = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("ariadne.users.user_id"), nullable=True)
    date = Column(String, nullable=True)
    read_time = Column(String, nullable=True)
    tags = Column(ARRAY(String), nullable=True)
    price = Column(Float, nullable=True)
    html_content = Column(Text, nullable=False)
    allow_comments = Column(Boolean, nullable=True)
    tier = Column(String, nullable=False)  # Using String instead of Enum for flexibility
    collection = Column(String, nullable=True)
    attachments = Column(ARRAY(String), nullable=True)
    date_published = Column(DateTime, nullable=True)
    user_name = Column(String(255), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    stripe_price_id = Column(String(255), nullable=True)
    stripe_product_id = Column(String(255), nullable=True)
    scheduled_time = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationship to User
    user = relationship("User", back_populates="posts")
    
    # Relationship to purchases
    purchases = relationship("PostPurchase", back_populates="post")
