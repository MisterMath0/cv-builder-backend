from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, JSON, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from ..database import Base
import enum
from pydantic import BaseModel, UUID4  # Make sure to use UUID4 from Pydantic
from typing import List, Optional, Dict, Any
from datetime import datetime

class CVStatus(enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class CV(Base):
    __tablename__ = "cvs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False, default="Untitled CV")
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    template_id = Column(String, nullable=False)
    status = Column(Enum(CVStatus), default=CVStatus.DRAFT)  # Add this line
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
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())  # Changed this line

    cv = relationship("CV", back_populates="sections")

# Pydantic models for API validation
class SectionCreate(BaseModel):
    id: UUID4  # Use UUID4 here
    type: str
    title: str
    content: Dict[str, Any]
    order_index: int

class CVCreate(BaseModel):
    title: Optional[str] = "Untitled CV"
    template_id: str
    sections: List[SectionCreate]

class SectionUpdate(SectionCreate):
    id: UUID4  # Use UUID4 here

class CVUpdate(BaseModel):
    title: Optional[str]
    template_id: Optional[str]
    sections: Optional[List[SectionUpdate]]
    status: Optional[CVStatus]
