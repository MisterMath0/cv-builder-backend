# app/api/preview.py
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
from uuid import UUID
from ..models.responses import ResponseModel
from ..models.user import UserProfile
from ..middleware.auth import get_current_user
from ..services.preview_service import PreviewService
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/preview", tags=["Preview"])

@router.get("/cv/{cv_id}/template/{template_id}", response_model=ResponseModel)
async def preview_cv_with_template(
    cv_id: UUID,
    template_id: UUID,
    current_user: UserProfile = Depends(get_current_user)
):
    """Get preview data for CV with specific template"""
    try:
        preview_data = await PreviewService.generate_preview_data(
            cv_id=cv_id,
            template_id=template_id
        )
        return ResponseModel(
            success=True,
            message="Preview data generated successfully",
            data=preview_data
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/cv/{cv_id}/template/{template_id}/html", response_class=HTMLResponse)
async def preview_cv_html(
    cv_id: UUID,
    template_id: UUID,
    current_user: UserProfile = Depends(get_current_user)
):
    """Get HTML preview for CV with specific template"""
    try:
        preview_data = await PreviewService.generate_preview_data(
            cv_id=cv_id,
            template_id=template_id
        )
        html = await PreviewService.generate_html_preview(preview_data)
        return HTMLResponse(content=html)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/template/{template_id}", response_model=ResponseModel)
async def preview_template_with_data(
    template_id: UUID,
    cv_data: Dict[str, Any],
    current_user: UserProfile = Depends(get_current_user)
):
    """Preview template with provided CV data"""
    try:
        preview_data = await PreviewService.generate_preview_data(
            template_id=template_id,
            cv_data=cv_data
        )
        return ResponseModel(
            success=True,
            message="Preview data generated successfully",
            data=preview_data
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/template/{template_id}/html", response_class=HTMLResponse)
async def preview_template_html(
    template_id: UUID,
    cv_data: Dict[str, Any],
    current_user: UserProfile = Depends(get_current_user)
):
    """Get HTML preview for template with provided CV data"""
    try:
        preview_data = await PreviewService.generate_preview_data(
            template_id=template_id,
            cv_data=cv_data
        )
        html = await PreviewService.generate_html_preview(preview_data)
        return HTMLResponse(content=html)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))