# app/api/cv.py
import uuid
from app.models.cv import CV
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from ..services.cv_service import CVService
from ..database import get_db
from ..services.preview_service import PreviewService
from ..services.export_service import ExportService
from fastapi.responses import StreamingResponse
from io import BytesIO
from pydantic import BaseModel
from typing import Dict, Any, List

router = APIRouter(prefix="/api/cv", tags=["CV"])

class CVCreateRequest(BaseModel):
    template_id: str
    sections: List[Dict[str, Any]]

class CVPreviewRequest(BaseModel):
    cv_data: Dict[str, Any]
    template_id: str
    
class CVExportRequest(BaseModel):
    cv_data: Dict[str, Any]
    template_id: str

class Section(BaseModel):
    type: str
    title: str
    content: Any
    order_index: int
    
class CVData(BaseModel):
    sections: List[Section]
    
class PreviewRequest(BaseModel):
    cv_data: CVData
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
            id=uuid.uuid4(),
            template_id=request.template_id,
            title="Untitled CV"
        )
        db.add(cv)
        db.flush()  # Get CV ID before adding sections

        # Create sections
        if request.sections:
            for section_data in request.sections:
                section = Section(
                    id=uuid.uuid4(),
                    cv_id=cv.id,
                    type=section_data.get('type'),
                    title=section_data.get('title'),
                    content=section_data.get('content'),
                    order_index=section_data.get('order_index', 0)
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
        print(f"Error creating CV: {str(e)}")  # For debugging
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/{cv_id}")
async def get_cv(
    cv_id: str,
    db: Session = Depends(get_db)
):
    """Get CV with its sections"""
    try:
        cv = db.query(CV).filter(CV.id == cv_id).first()
        if not cv:
            raise HTTPException(status_code=404, detail="CV not found")

        sections = db.query(Section).filter(Section.cv_id == cv_id).order_by(Section.order_index).all()
        
        return {
            "success": True,
            "data": {
                "id": str(cv.id),
                "template_id": cv.template_id,
                "title": cv.title,
                "sections": [
                    {
                        "type": section.type,
                        "title": section.title,
                        "content": section.content,
                        "order_index": section.order_index
                    } for section in sections
                ]
            }
        }
    except Exception as e:
        print(f"Error getting CV: {str(e)}")  # For debugging
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{cv_id}")
async def update_cv(
    cv_id: str,
    request: CVCreateRequest,
    db: Session = Depends(get_db)
):
    """Update CV and its sections"""
    try:
        # Get existing CV
        cv = db.query(CV).filter(CV.id == cv_id).first()
        if not cv:
            raise HTTPException(status_code=404, detail="CV not found")

        # Update CV template
        cv.template_id = request.template_id
        
        # Delete existing sections
        db.query(Section).filter(Section.cv_id == cv_id).delete()
        
        # Create new sections
        for section_data in request.sections:
            section = Section(
                id=uuid.uuid4(),
                cv_id=cv_id,
                type=section_data.get('type'),
                title=section_data.get('title'),
                content=section_data.get('content'),
                order_index=section_data.get('order_index', 0)
            )
            db.add(section)

        db.commit()
        return {
            "success": True,
            "message": "CV updated successfully"
        }
    except Exception as e:
        db.rollback()
        print(f"Error updating CV: {str(e)}")  # For debugging
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