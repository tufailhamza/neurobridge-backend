from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from .base import Base


class Clinician(Base):
    __tablename__ = "clinicians"
    __table_args__ = {"schema": "ariadne"}

    user_id = Column(Integer, ForeignKey("ariadne.users.user_id"), primary_key=True, index=True)
    specialty = Column(String, nullable=False)
    profile_image = Column(String, nullable=True)
    is_subscribed = Column(Boolean, default=False)
    prefix = Column(String, nullable=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    zip_code = Column(String, nullable=False)
    clinician_type = Column(String, nullable=False)
    license_number = Column(String, nullable=False)
    area_of_expertise = Column(String, nullable=False)
    content_preferences_tags = Column(ARRAY(Text), nullable=True)
    
    # Relationship to User table
    user = relationship("User", back_populates="clinician")

