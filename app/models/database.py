# app/models/database.py
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, JSON, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from ..database import Base

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

class CV(Base):
    __tablename__ = "cvs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    is_template = Column(Boolean, default=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("cvs.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    active = Column(Boolean, default=True)

    user = relationship("User", back_populates="cvs")
    sections = relationship("Section", back_populates="cv", cascade="all, delete-orphan")

class Section(Base):
    __tablename__ = "sections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cv_id = Column(UUID(as_uuid=True), ForeignKey("cvs.id"))
    type = Column(String)  # contact, text, experience, education, skills, languages
    title = Column(String)
    content = Column(JSON)
    order_index = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    cv = relationship("CV", back_populates="sections")