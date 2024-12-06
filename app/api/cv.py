import uuid
from app.middleware.auth import get_current_user
from app.models.user import User
from app.config import settings
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from ..services.cv_service import CVService
from ..database import get_db
from ..services.preview_service import PreviewService
from ..services.export_service import ExportService
from fastapi.responses import StreamingResponse
from io import BytesIO
from pydantic import BaseModel
from ..models.database import CV, Section, CVStatus  # Import SQLAlchemy models
from sqlalchemy.sql import func
from fastapi import Depends, HTTPException
from jose import JWTError, jwt
from typing import Optional
from fastapi.security import OAuth2PasswordBearer
from fastapi import UploadFile


router = APIRouter(prefix="/api/cv", tags=["CV"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="access_token")  # This URL is where the client gets the token from

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


from datetime import datetime

@router.post("")
async def create_cv(
    request: CVCreateRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Create new CV with sections"""
    try:
        if not request.template_id or not request.sections:
            raise HTTPException(status_code=400, detail="Template ID and sections are required.")
        
        # Delete existing drafts for this user
        existing_drafts = db.query(CV).filter(
            CV.user_id == current_user.id,
            CV.status == CVStatus.DRAFT
        ).all()
        
        for draft in existing_drafts:
            db.delete(draft)
        
        # Generate title and create new CV
        current_time = datetime.utcnow()
        title = f"CV_{current_time.strftime('%Y-%m-%d_%H-%M-%S')}"
        
        cv = CV(
            template_id=request.template_id,
            title=title,
            status=CVStatus.DRAFT,
            user_id=current_user.id
        )
        db.add(cv)
        db.flush()

        # Create sections
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



@router.get("/{cv_id}")
async def get_cv(
    cv_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)  # Ensure the user is authenticated
):
    """Get CV by ID"""
    cv_service = CVService(db)
    cv = await cv_service.get_cv(cv_id, current_user.id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found.")
    return cv

@router.get("")  # Changed from "/cvs"
async def get_user_cvs(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get all CVs for the authenticated user"""
    try:
        cv_service = CVService(db)
        user_cvs = await cv_service.get_user_cvs(current_user.id)
        if not user_cvs:
            return []  # Return empty list instead of 404
        return user_cvs
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{cv_id}")
async def update_cv(
    cv_id: str,
    request: CVCreateRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Update CV data"""
    try:
        print(f"Received update request for CV {cv_id}")
        
        # If updating to draft status, delete other drafts first
        if request.status == CVStatus.DRAFT:
            existing_drafts = db.query(CV).filter(
                CV.user_id == current_user.id,
                CV.status == CVStatus.DRAFT,
                CV.id != cv_id  # Don't delete the current CV
            ).all()
            
            for draft in existing_drafts:
                db.delete(draft)
        
        cv_service = CVService(db)
        result = await cv_service.update_cv(
            cv_id=cv_id, 
            user_id=current_user.id,
            cv_data={
                "template_id": request.template_id,
                "sections": [section.dict() for section in request.sections],
                "status": request.status
            }
        )
        
        return {
            "success": True,
            "message": "CV updated successfully"
        }
    except Exception as e:
        db.rollback()
        print(f"Error updating CV: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    

@router.delete("/{cv_id}")
async def delete_cv(
    cv_id: str,
    db: Session = Depends(get_db)
):
    """Delete a CV"""
    try:
        # Check if CV exists
        cv = db.query(CV).filter(CV.id == cv_id).first()
        if not cv:
            raise HTTPException(status_code=404, detail="CV not found")

        # Delete CV (this will cascade to sections due to relationship setting)
        db.delete(cv)
        db.commit()

        return {
            "success": True,
            "message": "CV deleted successfully"
        }
    except Exception as e:
        db.rollback()
        print(f"Error deleting CV: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/preview")
async def preview_cv(request: PreviewRequest, current_user: str = Depends(get_current_user)):  # Ensure the user is authenticated
    try:
        # Validate input
        if not request.template_id or not request.cv_data:
            raise HTTPException(status_code=400, detail="Invalid data for preview.")
        
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
    request: CVExportRequest,
    current_user: str = Depends(get_current_user)  # Ensure the user is authenticated
):
    """Export CV in specified format"""
    # Validate format
    if format not in ["pdf", "docx"]:
        raise HTTPException(status_code=400, detail="Unsupported format.")
    
    export_service = ExportService()
    preview_service = PreviewService()

    try:
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
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/upload-image")
async def upload_image(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Upload profile image"""
    try:
        cv_service = CVService(db)
        image_url = await cv_service.upload_profile_image(
            current_user.id,
            file  # Pass the UploadFile directly
        )
        return {"image_url": image_url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))