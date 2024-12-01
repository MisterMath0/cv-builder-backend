# app/services/section_service.py
from typing import List
from uuid import UUID
from fastapi import HTTPException
from ..database import supabase
from ..models import Section, SectionCreate, SectionUpdate

class SectionService:
    @staticmethod
    async def create_section(section_data: SectionCreate) -> dict:
        """Create a new section"""
        try:
            result = supabase.table('sections').insert(section_data.model_dump()).execute()
            return result.data[0]
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    async def update_section(section_id: UUID, section_data: SectionUpdate) -> dict:
        """Update a section"""
        try:
            result = supabase.table('sections')\
                .update(section_data.model_dump(exclude_unset=True))\
                .eq('id', str(section_id))\
                .execute()
            return result.data[0]
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    async def reorder_sections(cv_id: UUID, section_orders: List[dict]) -> bool:
        """Update the order of sections"""
        try:
            for order in section_orders:
                supabase.table('sections')\
                    .update({"order_index": order["order"]})\
                    .eq('id', order["id"])\
                    .eq('cv_id', str(cv_id))\
                    .execute()
            return True
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    async def verify_section_ownership(section_id: UUID, user_id: UUID) -> bool:
        """Verify if a section belongs to a user's CV"""
        try:
            result = supabase.table('sections')\
                .select("cv_id")\
                .eq('id', str(section_id))\
                .single()\
                .execute()
                
            if not result.data:
                return False
                
            cv_result = supabase.table('cvs')\
                .select("user_id")\
                .eq('id', result.data['cv_id'])\
                .single()\
                .execute()
                
            return cv_result.data and cv_result.data['user_id'] == str(user_id)
        except Exception:
            return False