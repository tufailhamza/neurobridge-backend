from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Text,
    ARRAY,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from .base import Base

class Caregiver(Base):
    __tablename__ = "caregivers"
    __table_args__ = {"schema": "ariadne"}

    user_id = Column(Integer, ForeignKey("ariadne.users.user_id"), primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    username = Column(String, nullable=False, unique=True)
    country = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    zip_code = Column(String, nullable=False)
    caregiver_role = Column(String, nullable=False)
    childs_age = Column(Integer, nullable=False)
    diagnosis = Column(String, nullable=False)
    years_of_diagnosis = Column(Integer, nullable=False)
    make_name_public = Column(Boolean, nullable=False, default=False)
    make_personal_details_public = Column(Boolean, nullable=False, default=False)
    profile_image = Column(String, nullable=True)
    cover_image = Column(String, nullable=True)
    content_preferences_tags = Column(ARRAY(Text), nullable=False, default=[])
    bio = Column(Text, nullable=False)
    subscribed_clinicians_ids = Column(ARRAY(Text), nullable=False, default=[])
    purchased_feed_content_ids = Column(ARRAY(Text), nullable=False, default=[])
    
    # Relationship to User table
    user = relationship("User", back_populates="caregiver")
