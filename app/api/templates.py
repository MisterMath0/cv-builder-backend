# app/api/templates.py
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from uuid import UUID
from ..models.template import Template, TemplateCreate, TemplateUpdate
from ..models.responses import ResponseModel
from ..models.user import UserProfile
from ..middleware.auth import get_current_user
from ..services.template_service import TemplateService

router = APIRouter(prefix="/templates", tags=["Templates"])

@router.post("/", response_model=ResponseModel)
async def create_template(
    template: TemplateCreate,
    current_user: UserProfile = Depends(get_current_user)
):
    """Create a new template (admin only)"""
    # TODO: Add admin check
    template.created_by = current_user.id
    result = await TemplateService.create_template(template)
    return ResponseModel(
        success=True,
        message="Template created successfully",
        data=result
    )

@router.get("/", response_model=ResponseModel)
async def list_templates(
    category: Optional[str] = None,
    is_public: bool = True,
    current_user: Optional[UserProfile] = Depends(get_current_user)
):
    """Get all available templates"""
    templates = await TemplateService.list_templates(category, is_public)
    return ResponseModel(
        success=True,
        message="Templates retrieved successfully",
        data=templates
    )

@router.get("/{template_id}", response_model=ResponseModel)
async def get_template(
    template_id: UUID,
    current_user: Optional[UserProfile] = Depends(get_current_user)
):
    """Get a specific template"""
    template = await TemplateService.get_template(template_id)
    return ResponseModel(
        success=True,
        message="Template retrieved successfully",
        data=template
    )

@router.post("/{template_id}/apply/{cv_id}", response_model=ResponseModel)
async def apply_template(
    template_id: UUID,
    cv_id: UUID,
    current_user: UserProfile = Depends(get_current_user)
):
    """Apply a template to a CV"""
    result = await TemplateService.apply_template_to_cv(
        cv_id,
        template_id,
        current_user.id
    )
    return ResponseModel(
        success=True,
        message="Template applied successfully",
        data=result
    )

# More routes can be added for template management