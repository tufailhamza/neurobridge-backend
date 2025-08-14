# # src/models/channels.py
# from .base import Base
# from sqlalchemy import (
#     Column,
#     String,
#     Integer,
#     Text,
#     ForeignKey,
#     PrimaryKeyConstraint,
# )
# from sqlalchemy.orm import relationship

# class Channel(Base):
#     __tablename__ = "channels"
#     __table_args__ = (
#         PrimaryKeyConstraint('user_id', 'channel_name', name='channels_pkey'),
#         {"schema": "ariadne"}
#     )

#     user_id = Column(Integer, ForeignKey("ariadne.users.user_id"), nullable=False)
#     channel_name = Column(Text, nullable=False)
    
#     # Relationship to User table
#     user = relationship("User", back_populates="channels")
