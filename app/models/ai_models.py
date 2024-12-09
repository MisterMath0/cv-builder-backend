from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum

class WriteStyle(str, Enum):
    PROFESSIONAL = "professional"
    CREATIVE = "creative"
    ACADEMIC = "academic"
    MODERN = "modern"
    TRADITIONAL = "traditional"

class JobAnalysis(BaseModel):
    company_name: str = Field(description="Company name extracted from job posting")
    position: str = Field(description="Job position/title")
    key_requirements: List[str] = Field(description="Key job requirements")
    required_skills: List[str] = Field(description="Required technical/soft skills")
    company_values: List[str] = Field(description="Company culture and values")
    contact_info: Optional[Dict] = Field(description="Contact information if available")
    department: Optional[str] = Field(description="Department or team")
    location: Optional[str] = Field(description="Job location")
    employment_type: Optional[str] = Field(description="Type of employment (full-time, contract, etc)")

class CVAnalysis(BaseModel):
    key_experiences: List[str] = Field(description="Relevant professional experiences")
    highlighted_skills: List[str] = Field(description="Skills matching job requirements")
    achievements: List[str] = Field(description="Notable achievements")
    value_proposition: str = Field(description="Unique value proposition")
    education_match: Optional[bool] = Field(description="If education matches requirements")
    experience_level_match: Optional[bool] = Field(description="If experience level matches")
    skill_match_score: Optional[float] = Field(None, description="Individual skill match score")
    experience_match_score: Optional[float] = Field(None, description="Experience match score")
    overall_match_score: Optional[float] = Field(None, description="Overall match score")
    match_level: Optional[str] = Field(None, description="Match level description")

class CoverLetterRequest(BaseModel):
    cv_id: Optional[str] = Field(None, description="ID of saved CV")
    cv_content: Optional[Dict] = Field(None, description="CV content if not using saved CV")
    job_description: str = Field(..., description="Job posting content or URL")
    company_website: Optional[str] = Field(None, description="Company website URL")
    additional_context: Optional[Dict] = Field(
        default_factory=dict,
        description="Additional context or preferences for the letter"
    )
    style: WriteStyle = Field(
        default=WriteStyle.PROFESSIONAL,
        description="Desired writing style"
    )
    tone_preferences: Optional[List[str]] = Field(
        default_factory=list,
        description="Specific tone preferences"
    )

class CoverLetterDraft(BaseModel):
    content: str = Field(..., description="Cover letter content")
    analysis: Dict = Field(..., description="Analysis used to generate the letter")
    metadata: Dict = Field(
        default_factory=dict,
        description="Additional metadata about the generation"
    )
    suggestions: Optional[List[str]] = Field(
        default_factory=list,
        description="Improvement suggestions"
    )

class CoverLetterResponse(BaseModel):
    draft: CoverLetterDraft
    job_analysis: JobAnalysis
    cv_analysis: CVAnalysis
    status: str = Field(..., description="Generation status")
    credits_used: int = Field(..., description="AI credits used for generation")