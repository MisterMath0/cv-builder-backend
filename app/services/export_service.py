# app/services/export_service.py
from fastapi import HTTPException
from weasyprint import HTML
from docx import Document
from docx.shared import Pt, Inches
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ExportService:
    async def to_pdf(self, html_content: str) -> bytes:
        """Convert HTML to PDF"""
        try:
            logger.debug("Converting HTML to PDF")
            pdf = HTML(string=html_content).write_pdf()
            logger.debug("PDF generated successfully")
            return pdf
        except Exception as e:
            logger.error(f"PDF generation failed: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to generate PDF: {str(e)}"
            )

    async def to_docx(self, cv_data: Dict[Any, Any]) -> bytes:
        """Convert CV data to DOCX"""
        try:
            logger.debug("Generating DOCX document")
            doc = Document()
            
            # Document styling
            self._setup_document_style(doc)
            
            # Add sections in order
            self._add_contact_section(doc, cv_data.get('contact', {}))
            
            if profile := cv_data.get('profile'):
                self._add_section(doc, 'Profile', profile)
            
            if experiences := cv_data.get('experience', []):
                self._add_experience_section(doc, experiences)
            
            if education := cv_data.get('education', []):
                self._add_education_section(doc, education)
            
            if skills := cv_data.get('skills'):
                self._add_section(doc, 'Skills', skills)
            
            if languages := cv_data.get('languages', []):
                self._add_languages_section(doc, languages)
            
            if hobbies := cv_data.get('hobbies'):
                self._add_section(doc, 'Interests & Hobbies', hobbies)

            # Save to bytes
            doc_bytes = bytes()
            doc.save(doc_bytes)
            logger.debug("DOCX generated successfully")
            return doc_bytes
            
        except Exception as e:
            logger.error(f"DOCX generation failed: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to generate DOCX: {str(e)}"
            )

    def _setup_document_style(self, doc: Document):
        """Setup document styling"""
        # Default font style
        style = doc.styles['Normal']
        style.font.name = 'Calibri'
        style.font.size = Pt(11)
        
        # Heading styles
        for i in range(1, 4):
            style = doc.styles[f'Heading {i}']
            style.font.name = 'Calibri'
            style.font.size = Pt(14 - i)
            style.font.bold = True

    def _add_contact_section(self, doc: Document, contact_data: Dict):
        """Add contact information section"""
        logger.debug("Adding contact section")
        name = contact_data.get('name', '')
        email = contact_data.get('email', '')
        phone = contact_data.get('phone', '')
        location = contact_data.get('location', '')
        
        # Add name as main heading
        if name:
            heading = doc.add_heading(name, 0)
            heading.alignment = 1  # Center alignment
        
        # Add contact details
        contact_para = doc.add_paragraph()
        contact_para.alignment = 1
        contact_para.add_run(f"{email} | {phone}\n{location}")
        
        doc.add_paragraph()  # Add spacing

    def _add_section(self, doc: Document, title: str, content: str):
        """Add a generic section"""
        logger.debug(f"Adding section: {title}")
        doc.add_heading(title, 1)
        doc.add_paragraph(content)
        doc.add_paragraph()  # Add spacing

    def _add_experience_section(self, doc: Document, experiences: list):
        """Add experience section"""
        logger.debug("Adding experience section")
        doc.add_heading('Professional Experience', 1)
        
        for exp in experiences:
            # Company and position
            p = doc.add_paragraph()
            p.add_run(f"{exp['position']}\n").bold = True
            p.add_run(f"{exp['company']}\n").italic = True
            
            # Date range
            date_range = f"{exp['startDate']} - "
            date_range += "Present" if exp.get('current') else exp.get('endDate', '')
            p.add_run(date_range).italic = True
            
            # Description
            if description := exp.get('description'):
                doc.add_paragraph(description)
            
            doc.add_paragraph()  # Add spacing

    def _add_education_section(self, doc: Document, education: list):
        """Add education section"""
        logger.debug("Adding education section")
        doc.add_heading('Education', 1)
        
        for edu in education:
            # Institution and degree
            p = doc.add_paragraph()
            p.add_run(f"{edu['degree']}\n").bold = True
            p.add_run(f"{edu['institution']}\n").italic = True
            
            # Date range
            date_range = f"{edu['startDate']} - "
            date_range += "Present" if edu.get('current') else edu.get('endDate', '')
            p.add_run(date_range).italic = True
            
            # Description
            if description := edu.get('description'):
                doc.add_paragraph(description)
            
            doc.add_paragraph()  # Add spacing

    def _add_languages_section(self, doc: Document, languages: list):
        """Add languages section"""
        logger.debug("Adding languages section")
        doc.add_heading('Languages', 1)
        
        for lang in languages:
            doc.add_paragraph(
                f"{lang['name']} - {lang['level']}", 
                style='List Bullet'
            )
        
        doc.add_paragraph()  # Add spacing