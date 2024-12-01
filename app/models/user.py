# app/models/user.py
from sqlalchemy import Boolean, Column, String, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ..database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_locked = Column(Boolean, default=False)  # Track account lock status
    failed_login_attempts = Column(Integer, default=0)  # Track failed login attempts
    last_login = Column(DateTime(timezone=True), nullable=True)  # Track last successful login
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    cvs = relationship("CV", back_populates="user", cascade="all, delete-orphan")
