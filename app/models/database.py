# app/models/database.py
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, JSON, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from ..database import Base
import enum

class CVStatus(enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    cvs = relationship("CV", back_populates="user")
    profile_photo = Column(String, nullable=True)

class CV(Base):
    __tablename__ = "cvs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False, default="Untitled CV")
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    template_id = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="cvs")
    sections = relationship("Section", back_populates="cv", cascade="all, delete-orphan")
    
class Section(Base):
    __tablename__ = "sections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cv_id = Column(UUID(as_uuid=True), ForeignKey("cvs.id", ondelete="CASCADE"))
    type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    content = Column(JSON, nullable=False)
    order_index = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    cv = relationship("CV", back_populates="sections")

# Pydantic models for API validation
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

class SectionCreate(BaseModel):
    type: str
    title: str
    content: Dict[str, Any]
    order_index: int

class CVCreate(BaseModel):
    title: Optional[str] = "Untitled CV"
    template_id: str
    sections: List[SectionCreate]

class SectionUpdate(SectionCreate):
    id: UUID

class CVUpdate(BaseModel):
    title: Optional[str]
    template_id: Optional[str]
    sections: Optional[List[SectionUpdate]]
    status: Optional[CVStatus]