# app/models/cv.py
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ..database import Base

class CV(Base):
    __tablename__ = "cvs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    cv_data = Column(JSON)
    template_id = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="cvs")
    sections = relationship("Section", back_populates="cv", cascade="all, delete-orphan")
# Pydantic models for request validation
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any
from uuid import UUID

class CVCreate(BaseModel):
    cv_data: Dict[str, Any]
    template_id: str

class CVResponse(BaseModel):
    id: UUID
    user_id: UUID
    cv_data: Dict[str, Any]
    template_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True