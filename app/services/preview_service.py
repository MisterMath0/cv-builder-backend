# app/services/preview_service.py
from fastapi import HTTPException
import jinja2
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PreviewService:
    def __init__(self):
        try:
            self.template_loader = jinja2.FileSystemLoader('app/templates/cv')
            self.template_env = jinja2.Environment(loader=self.template_loader)
            logger.debug("Template environment initialized")
        except Exception as e:
            logger.error(f"Template environment initialization failed: {str(e)}")
            raise

    async def generate_preview(self, cv_data: Dict[Any, Any], template_id: str) -> str:
        """Generate HTML preview using selected template"""
        try:
            logger.debug(f"Generating preview for template: {template_id}")
            template = self.template_env.get_template(f'{template_id}.html')
            html = template.render(**cv_data)
            logger.debug("Preview generated successfully")
            return html
        except jinja2.TemplateNotFound:
            logger.error(f"Template {template_id} not found")
            raise HTTPException(
                status_code=404, 
                detail=f"Template {template_id} not found"
            )
        except Exception as e:
            logger.error(f"Preview generation failed: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to generate preview: {str(e)}"
            )