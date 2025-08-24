from .base import Base
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    func,
    ForeignKey
)
from sqlalchemy.orm import relationship

class Purchase(Base):
    __tablename__ = "purchases"
    __table_args__ = {"schema": "ariadne"}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False)
    content_id = Column(String(255), nullable=False)
    stripe_session_id = Column(String(255), unique=True, nullable=True)
    stripe_payment_intent_id = Column(String(255), nullable=True)
    amount = Column(Integer, nullable=False)
    currency = Column(String(3), nullable=False, default='usd')
    status = Column(String(50), nullable=False, default='pending')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships - commented out due to type mismatch between String and Integer
    # user = relationship("User", foreign_keys=[user_id], primaryjoin="Purchase.user_id == User.user_id")
    # content = relationship("Post", foreign_keys=[content_id], primaryjoin="Purchase.content_id == Post.id")
