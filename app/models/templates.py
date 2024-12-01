# app/models/template.py
from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional, Dict, Any
from datetime import datetime

class TemplateStyleConfig(BaseModel):
    """Styling configuration for templates"""
    font_family: str
    colors: Dict[str, str]
    spacing: Dict[str, str]
    layout: str
    custom_css: Optional[str] = None

class TemplateSection(BaseModel):
    """Template section configuration"""
    type: str
    title: str
    required: bool = False
    order_index: int
    default_content: Optional[Dict[str, Any]] = None
    style_config: Optional[Dict[str, Any]] = None

class TemplateBase(BaseModel):
    """Base template model"""
    name: str
    description: str
    thumbnail_url: Optional[str] = None
    style_config: TemplateStyleConfig
    sections: List[TemplateSection]
    is_public: bool = True
    category: str  # e.g., 'Professional', 'Creative', 'Academic'

class TemplateCreate(TemplateBase):
    created_by: UUID

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    style_config: Optional[TemplateStyleConfig] = None
    sections: Optional[List[TemplateSection]] = None
    is_public: Optional[bool] = None
    category: Optional[str] = None

class Template(TemplateBase):
    id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    usage_count: int = 0

    class Config:
        from_attributes = True