# app/services/cv_service.py
from fastapi import HTTPException
from typing import Dict, Any, List
from sqlalchemy.orm import Session
import logging
from ..models.database import CV, Section
from datetime import datetime

logger = logging.getLogger(__name__)

class CVService:
    def __init__(self, db: Session):
        self.db = db

    async def create_cv(self, user_id: str, template_id: str) -> CV:
        """Create a new CV"""
        try:
            logger.debug(f"Creating new CV for user {user_id} with template {template_id}")
            cv = CV(
                user_id=user_id,
                template_id=template_id,
                cv_data={}  # Initialize empty
            )
            self.db.add(cv)
            self.db.commit()
            self.db.refresh(cv)
            logger.info(f"Successfully created CV with ID: {cv.id}")
            return cv
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create CV: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    async def get_cv(self, cv_id: str, user_id: str) -> CV:
        """Get CV by ID"""
        cv = self.db.query(CV).filter(
            CV.user_id == user_id,
            CV.id == cv_id
        ).first()
        if not cv:
            raise HTTPException(status_code=404, detail="CV not found")
        return cv

    async def get_user_cvs(self, user_id: str) -> List[CV]:
        """Get all CVs for a user"""
        return self.db.query(CV).filter(CV.user_id == user_id).all()

    async def update_cv(self, cv_id: str, user_id: str, cv_data: Dict[Any, Any]) -> CV:
        """Update CV data"""
        try:
            # Get the CV
            cv = self.db.query(CV).filter(CV.id == cv_id, CV.user_id == user_id).first()
            if not cv:
                raise HTTPException(status_code=404, detail="CV not found")

            # Update CV fields
            cv.template_id = cv_data.get("template_id")
            cv.status = cv_data.get("status")
            cv.updated_at = datetime.utcnow()

            # Delete existing sections
            self.db.query(Section).filter(Section.cv_id == cv_id).delete()

            # Add new sections
            for section_data in cv_data.get("sections", []):
                section = Section(
                    cv_id=cv_id,
                    type=section_data["type"],
                    title=section_data["title"],
                    content=section_data["content"],
                    order_index=section_data["order_index"]
                )
                self.db.add(section)

            self.db.commit()
            self.db.refresh(cv)
            return cv
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    async def delete_cv(self, cv_id: str, user_id: str) -> bool:
        """Delete CV"""
        try:
            cv = await self.get_cv(cv_id, user_id)
            self.db.delete(cv)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))