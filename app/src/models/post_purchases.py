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

class PostPurchase(Base):
    __tablename__ = "post_purchases"
    __table_args__ = {"schema": "ariadne"}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("ariadne.users.user_id"), nullable=False)
    post_id = Column(String(255), ForeignKey("ariadne.posts.id"), nullable=False)
    purchase_id = Column(Integer, ForeignKey("ariadne.purchases.id"), nullable=True)  # Link to original purchase
    amount = Column(Integer, nullable=False)
    currency = Column(String(3), nullable=False, default='usd')
    purchased_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="post_purchases")
    post = relationship("Post", back_populates="purchases")
    purchase = relationship("Purchase", back_populates="post_purchase")
