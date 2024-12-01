# app/api/sections.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from uuid import UUID
from ..models.section import (
    Section,
    SectionCreate,
    SectionUpdate,
    SectionOrder
)
from ..models.responses import ResponseModel
from ..models.user import UserProfile
from ..middleware.auth import get_current_user
from ..services.section_service import SectionService

router = APIRouter(prefix="/sections", tags=["Sections"])

@router.post("/{cv_id}", response_model=ResponseModel)
async def create_section(
    cv_id: UUID,
    section: SectionCreate,
    current_user: UserProfile = Depends(get_current_user)
):
    """Create a new section in a CV"""
    # Verify CV ownership
    if not await SectionService.verify_cv_ownership(cv_id, current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to modify this CV")
    
    section.cv_id = cv_id
    result = await SectionService.create_section(section)
    return ResponseModel(
        success=True,
        message="Section created successfully",
        data=result
    )

@router.put("/{section_id}", response_model=ResponseModel)
async def update_section(
    section_id: UUID,
    section: SectionUpdate,
    current_user: UserProfile = Depends(get_current_user)
):
    """Update a section's content"""
    # Verify section ownership
    if not await SectionService.verify_section_ownership(section_id, current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to modify this section")
    
    result = await SectionService.update_section(section_id, section)
    return ResponseModel(
        success=True,
        message="Section updated successfully",
        data=result
    )

@router.delete("/{section_id}", response_model=ResponseModel)
async def delete_section(
    section_id: UUID,
    current_user: UserProfile = Depends(get_current_user)
):
    """Delete a section"""
    if not await SectionService.verify_section_ownership(section_id, current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to delete this section")
    
    await SectionService.delete_section(section_id)
    return ResponseModel(
        success=True,
        message="Section deleted successfully"
    )

@router.post("/{cv_id}/reorder", response_model=ResponseModel)
async def reorder_sections(
    cv_id: UUID,
    section_orders: List[SectionOrder],
    current_user: UserProfile = Depends(get_current_user)
):
    """Update the order of sections in a CV"""
    if not await SectionService.verify_cv_ownership(cv_id, current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to modify this CV")
    
    await SectionService.reorder_sections(cv_id, section_orders)
    return ResponseModel(
        success=True,
        message="Sections reordered successfully"
    )

@router.get("/{cv_id}", response_model=ResponseModel)
async def get_cv_sections(
    cv_id: UUID,
    current_user: UserProfile = Depends(get_current_user)
):
    """Get all sections for a CV"""
    if not await SectionService.verify_cv_ownership(cv_id, current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to view this CV")
    
    sections = await SectionService.get_cv_sections(cv_id)
    return ResponseModel(
        success=True,
        message="Sections retrieved successfully",
        data=sections
    )

@router.post("/{cv_id}/bulk-update", response_model=ResponseModel)
async def bulk_update_sections(
    cv_id: UUID,
    sections: List[SectionUpdate],
    current_user: UserProfile = Depends(get_current_user)
):
    """Update multiple sections at once"""
    if not await SectionService.verify_cv_ownership(cv_id, current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to modify this CV")
    
    result = await SectionService.bulk_update_sections(cv_id, sections)
    return ResponseModel(
        success=True,
        message="Sections updated successfully",
        data=result
    )