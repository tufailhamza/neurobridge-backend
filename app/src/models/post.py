from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    Float,
    Enum,
    ForeignKey,
    Text,
    ARRAY,
)
from sqlalchemy.orm import declarative_base, relationship
import enum
from datetime import datetime
from .base import Base

class TierEnum(enum.Enum):
    public = "public"
    paid = "paid"

class Post(Base):
    __tablename__ = "posts"
    __table_args__ = {"schema": "ariadne"}

    id = Column(String, primary_key=True, index=True)
    image_url = Column(String, nullable=False)
    title = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("ariadne.users.user_id"))
    user = relationship("User")  # Assuming User model is imported or defined
    date = Column(String, nullable=True)  # or DateTime if you prefer
    read_time = Column(String, nullable=True)
    tags = Column(ARRAY(String), nullable=True)
    price = Column(Float, nullable=True, default=0)
    html_content = Column(Text, nullable=False)
    allow_comments = Column(Boolean, default=True)
    tier = Column(Enum(TierEnum), nullable=False, default=TierEnum.public)
    collection = Column(String, nullable=True)
    attachments = Column(ARRAY(String), nullable=True)  # URLs as array
    date_published = Column(DateTime, default=datetime.utcnow)
