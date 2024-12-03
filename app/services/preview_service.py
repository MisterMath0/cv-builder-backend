# app/services/preview_service.py
from fastapi import HTTPException
import jinja2
import logging
from typing import Dict, Any
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class PreviewService:
    def __init__(self):
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            template_dir = os.path.join(base_dir, 'templates', 'cv')
            
            self.template_loader = jinja2.FileSystemLoader(template_dir)
            self.template_env = jinja2.Environment(
                loader=self.template_loader,
                autoescape=True
            )
            
        except Exception as e:
            logger.error(f"Template environment initialization failed: {str(e)}")
            raise

    def parse_date(self, date_string: str) -> datetime:
        """Parse date string handling various formats"""
        if not date_string:
            return None
            
        try:
            # Remove timezone info
            date_string = date_string.split('T')[0]
            return datetime.strptime(date_string, '%Y-%m-%d')
        except Exception as e:
            logger.error(f"Date parsing failed for {date_string}: {str(e)}")
            return None

    async def generate_preview(self, cv_data: Dict[str, Any], template_id: str) -> str:
        try:
            template = self.template_env.get_template(f'{template_id}.html')
            
            # Process dates for proper formatting
            if 'sections' in cv_data:
                for section in cv_data['sections']:
                    if section['type'] in ['experience', 'education']:
                        for item in section.get('content', []):
                            if isinstance(item, dict):  # Make sure item is a dictionary
                                item['startDate'] = self.parse_date(item.get('startDate'))
                                item['endDate'] = self.parse_date(item.get('endDate'))
            
            html = template.render(cv=cv_data)
            return html
            
        except Exception as e:
            logger.error(f"Preview generation failed: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Template rendering failed: {str(e)}"
            )