# app/services/template_service.py
from fastapi import HTTPException
from typing import List, Optional
from uuid import UUID
from ..database import supabase
from ..models.template import Template, TemplateCreate, TemplateUpdate

class TemplateService:
    @staticmethod
    async def create_template(template: TemplateCreate) -> dict:
        """Create a new CV template"""
        try:
            result = supabase.table('templates').insert(template.model_dump()).execute()
            return result.data[0]
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    async def get_template(template_id: UUID) -> dict:
        """Get template by ID"""
        try:
            result = supabase.table('templates')\
                .select("*")\
                .eq('id', str(template_id))\
                .single()\
                .execute()
                
            if not result.data:
                raise HTTPException(status_code=404, detail="Template not found")
            return result.data
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    async def list_templates(
        category: Optional[str] = None,
        is_public: bool = True
    ) -> List[dict]:
        """Get list of templates with optional filtering"""
        try:
            query = supabase.table('templates')\
                .select("*")\
                .eq('is_public', is_public)
                
            if category:
                query = query.eq('category', category)
                
            result = query.execute()
            return result.data
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    async def apply_template_to_cv(
        cv_id: UUID,
        template_id: UUID,
        user_id: UUID
    ) -> dict:
        """Apply a template to an existing CV"""
        try:
            # Get template
            template = await TemplateService.get_template(template_id)
            
            # Update CV with template settings
            cv_update = {
                'template_id': str(template_id),
                'style_config': template['style_config']
            }
            
            cv_result = supabase.table('cvs')\
                .update(cv_update)\
                .eq('id', str(cv_id))\
                .eq('user_id', str(user_id))\
                .single()\
                .execute()
                
            if not cv_result.data:
                raise HTTPException(status_code=404, detail="CV not found")
                
            # Update sections based on template
            sections_result = supabase.table('sections')\
                .select("*")\
                .eq('cv_id', str(cv_id))\
                .execute()
                
            # Map existing sections to template sections
            for template_section in template['sections']:
                matching_section = next(
                    (s for s in sections_result.data if s['type'] == template_section['type']),
                    None
                )
                
                if matching_section:
                    # Update existing section with template settings
                    supabase.table('sections')\
                        .update({
                            'title': template_section['title'],
                            'order_index': template_section['order_index'],
                            'style_config': template_section['style_config']
                        })\
                        .eq('id', matching_section['id'])\
                        .execute()
                else:
                    # Create new section from template
                    supabase.table('sections')\
                        .insert({
                            'cv_id': str(cv_id),
                            'type': template_section['type'],
                            'title': template_section['title'],
                            'order_index': template_section['order_index'],
                            'content': template_section['default_content'],
                            'style_config': template_section['style_config']
                        })\
                        .execute()

            # Increment template usage count
            supabase.table('templates')\
                .update({ 'usage_count': template['usage_count'] + 1 })\
                .eq('id', str(template_id))\
                .execute()
                
            return await TemplateService.get_template(template_id)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))