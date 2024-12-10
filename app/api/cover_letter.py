from app.models.database import CoverLetter
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..services.ai_service import CoverLetterService
from ..services.cv_service import CVService
from ..models.ai_models import (
    CoverLetterRequest,
    CoverLetterResponse,
    WriteStyle
)
from ..models.user import User
from ..database import get_db
from ..middleware.auth import get_current_user
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from typing import List
import logging
from fastapi.responses import StreamingResponse
from ..services.cover_letter_export_service import CoverLetterExportService
from io import BytesIO
from typing import Literal

class SaveCoverLetterRequest(BaseModel):
    content: str
    cv_id: Optional[str] = None
    job_id: Optional[str] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    matching_score: Optional[float] = None

class CoverLetterResponse(BaseModel):
    id: str
    content: str
    job_title: Optional[str]
    company_name: Optional[str]
    matching_score: Optional[float]
    created_at: datetime
    cv_id: Optional[str]
    
    
router = APIRouter(prefix="/api/ai", tags=["Cover Letter"])
logger = logging.getLogger(__name__)

@router.post("", response_model=CoverLetterResponse)
async def generate_cover_letter(
    request: CoverLetterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a personalized cover letter"""
    try:
        # Check if user has enough credits
        if current_user.ai_credits <= 0:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Insufficient credits for AI generation"
            )
            
        # Initialize services
        ai_service = CoverLetterService()
        cv_service = CVService(db)
        
        # Get CV content if cv_id is provided
        if request.cv_id:
            cv = await cv_service.get_cv(request.cv_id, current_user.id)
            if not cv:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="CV not found"
                )
            request.cv_content = cv.sections
        elif not request.cv_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either cv_id or cv_content must be provided"
            )
            
        # Generate cover letter
        try:
            result = await ai_service.generate_cover_letter(request)
            
            # Deduct credits
            current_user.ai_credits -= result.credits_used
            db.commit()
            
            return result
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cover letter generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate cover letter"
        )

@router.get("/credits")
async def get_credits(current_user: User = Depends(get_current_user)):
    """Get user's remaining AI credits"""
    return {"credits": current_user.ai_credits}


@router.post("/save", response_model=CoverLetterResponse)
async def save_cover_letter(
    request: SaveCoverLetterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Save generated cover letter"""
    try:
        cover_letter = CoverLetter(
            user_id=current_user.id,
            cv_id=request.cv_id,
            job_id=request.job_id,
            content=request.content,
            job_title=request.job_title,
            company_name=request.company_name,
            matching_score=request.matching_score
        )
        
        db.add(cover_letter)
        db.commit()
        db.refresh(cover_letter)
        
        return CoverLetterResponse(
            id=str(cover_letter.id),
            content=cover_letter.content,
            job_title=cover_letter.job_title,
            company_name=cover_letter.company_name,
            matching_score=cover_letter.matching_score,
            created_at=cover_letter.created_at,
            cv_id=str(cover_letter.cv_id) if cover_letter.cv_id else None
        )
        
    except Exception as e:
        logger.error(f"Failed to save cover letter: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save cover letter"
        )

@router.get("/letters", response_model=List[CoverLetterResponse])
async def get_cover_letters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 10
):
    """Get user's cover letters with pagination"""
    try:
        cover_letters = db.query(CoverLetter)\
            .filter(CoverLetter.user_id == current_user.id)\
            .order_by(CoverLetter.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
            
        return [
            CoverLetterResponse(
                id=str(letter.id),
                content=letter.content,
                job_title=letter.job_title,
                company_name=letter.company_name,
                matching_score=letter.matching_score,
                created_at=letter.created_at,
                cv_id=str(letter.cv_id) if letter.cv_id else None
            )
            for letter in cover_letters
        ]
        
    except Exception as e:
        logger.error(f"Failed to fetch cover letters: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch cover letters"
        )

@router.get("/letters/{letter_id}", response_model=CoverLetterResponse)
async def get_cover_letter(
    letter_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific cover letter by ID"""
    try:
        cover_letter = db.query(CoverLetter)\
            .filter(
                CoverLetter.id == letter_id,
                CoverLetter.user_id == current_user.id
            )\
            .first()
            
        if not cover_letter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cover letter not found"
            )
            
        return CoverLetterResponse(
            id=str(cover_letter.id),
            content=cover_letter.content,
            job_title=cover_letter.job_title,
            company_name=cover_letter.company_name,
            matching_score=cover_letter.matching_score,
            created_at=cover_letter.created_at,
            cv_id=str(cover_letter.cv_id) if cover_letter.cv_id else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch cover letter: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch cover letter"
        )
        
@router.get("/letters/{letter_id}/export/{format}")
async def export_cover_letter(
    letter_id: str,
    format: Literal["pdf", "docx"],
    template: Optional[str] = "basic.html",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export cover letter in PDF or DOCX format"""
    try:
        letter = db.query(CoverLetter)\
            .filter(
                CoverLetter.id == letter_id,
                CoverLetter.user_id == current_user.id
            ).first()
            
        if not letter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cover letter not found"
            )

        export_service = CoverLetterExportService()
        
        export_args = {
            "content": letter.content,
            "company_name": letter.company_name,
            "job_title": letter.job_title,
            "author": current_user.full_name
        }
        
        if format == "pdf":
            content = await export_service.to_pdf(
                template_name=template,
                **export_args
            )
            media_type = "application/pdf"
            filename = "cover_letter.pdf"
        else:
            content = await export_service.to_docx(**export_args)
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = "cover_letter.docx"

        return StreamingResponse(
            BytesIO(content),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export cover letter"
        )