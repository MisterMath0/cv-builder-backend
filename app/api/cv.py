# app/api/cv.py
import uuid
from app.middleware.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List,Optional
from ..services.cv_service import CVService
from ..database import get_db
from ..services.preview_service import PreviewService
from ..services.export_service import ExportService
from fastapi.responses import StreamingResponse
from io import BytesIO
from pydantic import BaseModel
from ..models.database import CV, Section, CVStatus  # Import SQLAlchemy models
from sqlalchemy.sql import func


router = APIRouter(prefix="/api/cv", tags=["CV"])

# Pydantic models for API
class SectionRequest(BaseModel):
    type: str
    title: str
    content: Any
    order_index: int

class SectionResponse(BaseModel):
    type: str
    title: str
    content: Any
    order_index: int

class CVCreateRequest(BaseModel):
    template_id: str
    sections: List[SectionRequest]
    status: Optional[CVStatus] = CVStatus.DRAFT  # Add this line



class CVPreviewRequest(BaseModel):
    cv_data: Dict[str, Any]
    template_id: str
    
class CVExportRequest(BaseModel):
    cv_data: Dict[str, Any]
    template_id: str

class CVDataModel(BaseModel):
    sections: List[SectionResponse]
    
class PreviewRequest(BaseModel):
    cv_data: CVDataModel
    template_id: str

@router.post("")
async def create_cv(
    request: CVCreateRequest,
    db: Session = Depends(get_db)
):
    """Create new CV with sections"""
    try:
        # Create CV record
        cv = CV(
            template_id=request.template_id,
            title="Untitled CV",
            status=CVStatus.DRAFT
        )
        db.add(cv)
        db.flush()

        # Create sections with current timestamp
        current_time = func.now()
        for section_data in request.sections:
            section = Section(
                cv_id=cv.id,
                type=section_data.type,
                title=section_data.title,
                content=section_data.content,
                order_index=section_data.order_index,
                updated_at=current_time  
            )
            db.add(section)

        db.commit()
        db.refresh(cv)
        
        return {
            "success": True,
            "id": str(cv.id),
            "message": "CV created successfully"
        }
    except Exception as e:
        db.rollback()
        print(f"Error creating CV: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
# Rest of your routes remain the same
@router.get("/{cv_id}")
async def get_cv(
    cv_id: str,
    db: Session = Depends(get_db)
):
    """Get CV by ID"""
    cv_service = CVService(db)
    return await cv_service.get_cv(cv_id)

@router.put("/{cv_id}")
async def update_cv(
    cv_id: str,
    request: CVCreateRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),  # Assuming you have user authentication

):
    """Update CV data"""
    try:
        print(f"Received update request for CV {cv_id}")
        print(f"Request data: {request}")
        
        cv_service = CVService(db)
        result = await cv_service.update_cv(cv_id, user_id.id, request.dict())
        
        return {
            "success": True,
            "message": "CV updated successfully"
        }
    except Exception as e:
        print(f"Error updating CV: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/preview")
async def preview_cv(request: PreviewRequest):
    try:
        preview_service = PreviewService()
        preview_html = await preview_service.generate_preview(
            request.cv_data.dict(),
            request.template_id
        )
        return {"html": preview_html}
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.post("/export/{format}")
async def export_cv(
    format: str,
    request: CVExportRequest
):
    """Export CV in specified format"""
    export_service = ExportService()
    preview_service = PreviewService()
    
    if format == "pdf":
        preview_html = await preview_service.generate_preview(request.cv_data, request.template_id)
        pdf_bytes = await export_service.to_pdf(preview_html)
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=cv.pdf"}
        )
    elif format == "docx":
        docx_bytes = await export_service.to_docx(request.cv_data)
        return StreamingResponse(
            BytesIO(docx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": "attachment; filename=cv.docx"}
        )
    
    raise HTTPException(status_code=400, detail="Unsupported format")