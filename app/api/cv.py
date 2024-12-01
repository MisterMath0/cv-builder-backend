# app/api/cv.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from ..services.cv_service import CVService
from ..database import get_db
from ..middleware.auth import get_current_user
from ..models.user import User
from ..services.preview_service import PreviewService
from ..services.export_service import ExportService
from fastapi.responses import StreamingResponse
from io import BytesIO

router = APIRouter(prefix="/api/cv", tags=["CV"])

@router.post("")
async def create_cv(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new CV"""
    cv_service = CVService(db)
    return await cv_service.create_cv(str(current_user.id), template_id)

@router.get("/{cv_id}")
async def get_cv(
    cv_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get CV by ID"""
    cv_service = CVService(db)
    return await cv_service.get_cv(cv_id, str(current_user.id))

@router.get("")
async def get_user_cvs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all user's CVs"""
    cv_service = CVService(db)
    return await cv_service.get_user_cvs(str(current_user.id))

@router.put("/{cv_id}")
async def update_cv(
    cv_id: str,
    cv_data: Dict[Any, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update CV data"""
    cv_service = CVService(db)
    return await cv_service.update_cv(cv_id, str(current_user.id), cv_data)

@router.delete("/{cv_id}")
async def delete_cv(
    cv_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete CV"""
    cv_service = CVService(db)
    return await cv_service.delete_cv(cv_id, str(current_user.id))

@router.post("/preview")
async def preview_cv(
    cv_data: Dict[Any, Any],
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate HTML preview of CV"""
    preview_service = PreviewService()
    preview_html = await preview_service.generate_preview(cv_data, template_id)
    return {"html": preview_html}

@router.post("/export/{format}")
async def export_cv(
    format: str,
    cv_data: Dict[Any, Any],
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export CV in specified format"""
    export_service = ExportService()
    preview_service = PreviewService()
    
    if format == "pdf":
        # Generate HTML first, then convert to PDF
        preview_html = await preview_service.generate_preview(cv_data, template_id)
        pdf_bytes = await export_service.to_pdf(preview_html)
        
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={current_user.full_name}_cv.pdf"}
        )
        
    elif format == "docx":
        docx_bytes = await export_service.to_docx(cv_data)
        
        return StreamingResponse(
            BytesIO(docx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={current_user.full_name}_cv.docx"}
        )
        
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")