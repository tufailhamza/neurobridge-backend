# src/models/user.py
from .base import Base
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    func,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "ariadne"}

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    role = Column(ENUM('clinician', 'caregiver', 'admin', name='userrole', schema='ariadne'), nullable=False)
    account_create_date = Column(DateTime(timezone=True), server_default=func.now())
    last_active_at = Column(DateTime(timezone=True), nullable=True)
    last_engagement_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    password = Column(String, nullable=False)
    stripe_customer_id = Column(String, nullable=True, unique=True)
    
    # Relationships to Clinician and Caregiver tables
    clinician = relationship("src.models.clinician.Clinician", back_populates="user", uselist=False, lazy="select")
    caregiver = relationship("src.models.caregivers.Caregiver", back_populates="user", uselist=False, lazy="select")
    
    # Relationship to posts
    posts = relationship("Post", back_populates="user")
    
    # Relationship to collections
    collections = relationship("Collection", back_populates="user")
    
    # Relationship to user tracking
    user_tracking = relationship("UserTracking", back_populates="user", uselist=False, lazy="select")
