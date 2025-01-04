from datetime import datetime
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain.chains import SequentialChain, LLMChain
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field, validator
from typing import Dict, Optional, List, cast
from datetime import datetime
from langchain_openai import ChatOpenAI  # Updated import
from ..config import settings
from ..models.ai_models import (
    JobAnalysis,
    CVAnalysis,
    CoverLetterDraft,
    CoverLetterRequest,
    CoverLetterResponse,
    WriteStyle
)
import logging

logger = logging.getLogger(__name__)

class CoverLetterService:
    def __init__(self):
        self.llm_analyzer = ChatOpenAI(
            model_name="gpt-4o-mini",  # Make sure this matches available models
            temperature=0.2,
            api_key=settings.OPENAI_API_KEY
        )
        self.llm_writer = ChatOpenAI(
            model_name="gpt-4o-mini",
            temperature=0.7,
            api_key=settings.OPENAI_API_KEY
        )
        
    async def generate_cover_letter(
        self,
        request: CoverLetterRequest
    ) -> CoverLetterResponse:
        """Main method to handle cover letter generation process"""
        try:
            # Track token usage
            total_tokens_used = 0
            
            # Analyze job posting
            job_analysis = await self._analyze_job_posting(request.job_description)
            total_tokens_used += job_analysis.get("tokens_used", 0)
            
            # Analyze CV
            cv_analysis = await self._analyze_cv(
                request.cv_content,
                job_analysis["analysis"]
            )
            total_tokens_used += cv_analysis.get("tokens_used", 0)
            
            # Generate initial draft
            draft = await self._generate_draft(
                cv_analysis["analysis"],
                job_analysis["analysis"],
                request
            )
            total_tokens_used += draft.get("tokens_used", 0)
            
            # Refine the draft
            final_draft = await self._refine_draft(
                draft["content"],
                request.style,
                request.tone_preferences
            )
            total_tokens_used += final_draft.get("tokens_used", 0)
            total_tokens_used = int(round(total_tokens_used))

            draft_obj = CoverLetterDraft(
                content=final_draft["content"],
                analysis={
                    "job_matching_score": draft.get("matching_score", 0),
                    "key_points_covered": draft.get("points_covered", [])
                },
                metadata={
                    "style": request.style,
                    "tone": request.tone_preferences,
                    "generation_timestamp": str(datetime.utcnow())
                },
                suggestions=draft.get("improvement_suggestions", [])
            )
            
            return CoverLetterResponse(
                draft=draft_obj,
                job_analysis=job_analysis["analysis"],
                cv_analysis=cv_analysis["analysis"],
                status="completed",
                credits_used=total_tokens_used,
                content=final_draft["content"],
                job_title=job_analysis["analysis"].position,
                company_name=job_analysis["analysis"].company_name,
                matching_score=float(draft.get("matching_score", 0)),
                cv_id=request.cv_id
            )
            
        except Exception as e:
            logger.error(f"Cover letter generation failed: {str(e)}")
            raise

    async def _analyze_job_posting(self, job_description: str) -> Dict:
        try:
            parser = PydanticOutputParser(pydantic_object=JobAnalysis)
            
            # Updated prompt creation syntax
            prompt = ChatPromptTemplate.from_messages([
                ("system", """Analyze the following job posting and extract key information:
                    {format_instructions}
                """),
                ("user", "{job_description}")
            ])

            # Create the chain
            chain = prompt | self.llm_analyzer | parser

            # Execute the chain
            response = await chain.ainvoke({
                "job_description": job_description,
                "format_instructions": parser.get_format_instructions()
            })

            return {
                "analysis": response,
                "tokens_used": int(len(str(response).split()) * 1.3)
            }
                
        except Exception as e:
            logger.error(f"Job analysis failed: {str(e)}")
            raise

    async def _analyze_cv(self, cv_content: dict, job_analysis: JobAnalysis) -> Dict:
        """Analyze CV in context of job requirements"""
        try:
            # Extract sections from dictionary
            experiences = []
            skills = []
            education = []

            # Access dictionary content directly
            if 'experience' in cv_content:
                for exp in cv_content['experience']:
                    experience_text = (
                        f"Position: {exp.get('position', '')}\n"
                        f"Company: {exp.get('company', '')}\n"
                        f"Description: {exp.get('description', '')}"
                    )
                    experiences.append(experience_text)

            if 'skills' in cv_content:
                skills_content = cv_content['skills']
                if isinstance(skills_content, str):
                    skills.append(skills_content)
                elif isinstance(skills_content, list):
                    for skill in skills_content:
                        if isinstance(skill, dict):
                            skills.append(skill.get('name', ''))
                        else:
                            skills.append(str(skill))

            if 'education' in cv_content:
                for edu in cv_content['education']:
                    education_text = (
                        f"Degree: {edu.get('degree', '')}\n"
                        f"Institution: {edu.get('institution', '')}\n"
                        f"Description: {edu.get('description', '')}"
                    )
                    education.append(education_text)

            parser = PydanticOutputParser(pydantic_object=CVAnalysis)
            format_instructions = parser.get_format_instructions()

            prompt = ChatPromptTemplate.from_messages([
                ("system", """You must output a JSON object with:
                    - key_experiences: list of relevant experiences
                    - highlighted_skills: list of matching skills
                    - achievements: list of achievements
                    - value_proposition: summary string
                    - education_match: boolean
                    - experience_level_match: boolean
                    - skill_match_score: float between 0 and 1
                    - experience_match_score: float between 0 and 1
                    - overall_match_score: float between 0 and 1
                    - match_level: string describing match quality"""),
                ("user", """Analyze this CV content for job matching:
                    CV Content:
                    Experiences: {experiences}
                    Skills: {skills}
                    Education: {education}
                    
                    Job Requirements:
                    Position: {position}
                    Required Skills: {required_skills}
                    Key Requirements: {key_requirements}""")
            ])

            chain = prompt | self.llm_analyzer
            response = await chain.ainvoke({
                "experiences": "\n\n".join(experiences),
                "skills": ", ".join(skills),
                "education": "\n\n".join(education),
                "position": job_analysis.position,
                "required_skills": ", ".join(job_analysis.required_skills),
                "key_requirements": ", ".join(job_analysis.key_requirements)
            })

            response_content = response.content if hasattr(response, 'content') else str(response)
            
            return {
                "analysis": parser.parse(response_content),
                "tokens_used": len(str(response_content).split()) * 1.3
            }

        except Exception as e:
            logger.error(f"CV analysis failed: {str(e)}")
            raise ValueError(f"Failed to analyze CV: {str(e)}")

    async def _generate_draft(
        self, 
        cv_data: dict,  # Complete CV data
        job_data: dict,  # Complete job data
        request: CoverLetterRequest
    ) -> Dict:
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a professional cover letter writer. Generate a complete, formatted cover letter 
                using the candidate's CV data and job details. Use actual data, no placeholders."""),
                ("user", """
                CV Data:
                {cv_data}
                
                Job Details:
                {job_data}
                
                Style: {style}
                
                Generate a properly formatted cover letter with:
                - Complete header (date, contact info)
                - Professional greeting
                - 3-4 well-structured paragraphs
                - Professional closing
                
                Use \n for line breaks to ensure proper formatting.
                """)
            ])

            chain = prompt | self.llm_writer
            response = await chain.ainvoke({
                "cv_data": cv_data,
                "job_data": job_data,
                "style": request.style
            })

            return {
                "content": response.content,
                "tokens_used": len(response.content.split()) * 1.3
            }
        except Exception as e:
            logger.error(f"Draft generation failed: {str(e)}")
            raise ValueError(f"Failed to generate draft: {str(e)}")

    def _extract_contact_info(self, cv_content: dict) -> dict:
        """Extract contact information from CV content"""
        contact_info = {
            'name': '',
            'address': '',
            'email': '',
            'phone': ''
        }
        
        try:
            for section in cv_content:
                if section['type'] == 'contact':
                    content = section['content']
                    contact_info['name'] = content.get('name', '')
                    contact_info['address'] = content.get('location', '')
                    contact_info['email'] = content.get('email', '')
                    contact_info['phone'] = content.get('phone', '')
                    break
        except Exception as e:
            logger.error(f"Error extracting contact info: {str(e)}")
        
        return contact_info
        

    def _get_style_guide(self, style: WriteStyle) -> str:
        """Convert style enum to detailed guidelines"""
        style_guides = {
            WriteStyle.PROFESSIONAL: "formal, polished, business-appropriate language",
            WriteStyle.CREATIVE: "engaging, unique voice while maintaining professionalism",
            WriteStyle.ACADEMIC: "scholarly tone with emphasis on research and methodologies",
            WriteStyle.MODERN: "contemporary, direct language with clear value propositions",
            WriteStyle.TRADITIONAL: "classic business format with conventional structure"
        }
        return style_guides.get(style, style_guides[WriteStyle.PROFESSIONAL])

    async def _refine_draft(
        self,
        draft: str,
        style: WriteStyle,
        tone_preferences: Optional[List[str]]
    ) -> Dict:
        """Polish and enhance the draft"""
        try:
            prompt = ChatPromptTemplate.from_template(
                """Enhance this cover letter draft:
                {draft}
                
                Desired Style: {style}
                Tone Preferences: {tone_preferences}
                
                Improve:
                1. Strengthen language and impact
                2. Ensure natural flow and transitions
                3. Perfect grammar and tone consistency
                4. Remove clichés and generic phrases
                5. Enhance persuasiveness
                
                Return the polished version maintaining exact same facts but with enhanced expression.
                """
            )

            chain = LLMChain(llm=self.llm_writer, prompt=prompt)
            response = await chain.arun(
                draft=draft,
                style=style,
                tone_preferences=tone_preferences
            )
            
            return {
                "content": response,
                "tokens_used": len(response.split()) * 1.3
            }
        except Exception as e:
            logger.error(f"Refine draft failed: {str(e)}")
            raise ValueError(f"Failed to generate: {str(e)}")

    def _calculate_matching_score(self, cv_analysis: CVAnalysis, job_analysis: JobAnalysis) -> Dict:
        """
        Calculate job matching score based on various factors.
        Returns a dict with total score and individual component scores
        """
        try:
            weights = {
                'skills': 0.35,
                'experience': 0.30,
                'education': 0.15,
                'achievements': 0.20
            }
            
            # Skills matching
            skills_score = 0
            required_skills = set(s.lower() for s in job_analysis.required_skills)
            candidate_skills = set(s.lower() for s in cv_analysis.highlighted_skills)
            if required_skills:
                skills_score = len(required_skills.intersection(candidate_skills)) / len(required_skills)
            
            # Experience matching
            experience_score = 0
            key_requirements = set(req.lower() for req in job_analysis.key_requirements)
            experiences = set(exp.lower() for exp in cv_analysis.key_experiences)
            if key_requirements:
                experience_score = len(key_requirements.intersection(experiences)) / len(key_requirements)
            
            # Education match
            education_score = 1.0 if cv_analysis.education_match else 0.5
            
            # Achievement relevance score
            achievement_score = 0
            if cv_analysis.achievements:
                relevant_achievements = sum(
                    1 for achievement in cv_analysis.achievements
                    if any(req.lower() in achievement.lower() for req in job_analysis.key_requirements)
                )
                achievement_score = min(relevant_achievements / 3, 1.0)
            
            # Calculate weighted total score
            total_score = round(
                skills_score * weights['skills'] +
                experience_score * weights['experience'] +
                education_score * weights['education'] +
                achievement_score * weights['achievements'],
                2
            )
            
            return {
                'total_score': total_score,
                'skills_score': round(skills_score, 2),
                'experience_score': round(experience_score, 2),
                'education_score': round(education_score, 2),
                'achievement_score': round(achievement_score, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating matching score: {str(e)}")
            return {
                'total_score': 0.0,
                'skills_score': 0.0,
                'experience_score': 0.0,
                'education_score': 0.0,
                'achievement_score': 0.0
            }

    def _get_match_details(self, score: float) -> str:
        """Get matching level description based on score"""
        if score >= 0.85:
            return "Excellent Match"
        elif score >= 0.70:
            return "Strong Match"
        elif score >= 0.50:
            return "Good Match"
        elif score >= 0.30:
            return "Fair Match"
        else:
            return "Limited Match"

    def _identify_covered_points(self, content: str, job_analysis: JobAnalysis) -> Dict:
        """
        Identify which key job requirements are covered in the letter
        Returns dict with covered points, missing points, and coverage percentage
        """
        try:
            covered_points = []
            
            # Clean and lowercase the content for comparison
            clean_content = content.lower()
            
            # Dictionary to track requirement coverage with context
            coverage = {}
            
            # Check key requirements coverage
            for requirement in job_analysis.key_requirements:
                req_lower = requirement.lower()
                # Check if requirement or related keywords are mentioned
                if req_lower in clean_content:
                    # Get the surrounding context
                    start_idx = clean_content.find(req_lower)
                    # Get surrounding context (50 chars before and after)
                    context_start = max(0, start_idx - 50)
                    context_end = min(len(clean_content), start_idx + len(req_lower) + 50)
                    context = content[context_start:context_end].strip()
                    
                    coverage[requirement] = {
                        'covered': True,
                        'context': context
                    }
                else:
                    coverage[requirement] = {
                        'covered': False,
                        'context': None
                    }
            
            # Check skills coverage
            for skill in job_analysis.required_skills:
                skill_lower = skill.lower()
                if skill_lower in clean_content:
                    start_idx = clean_content.find(skill_lower)
                    context_start = max(0, start_idx - 50)
                    context_end = min(len(clean_content), start_idx + len(skill_lower) + 50)
                    context = content[context_start:context_end].strip()
                    
                    coverage[f"Skill: {skill}"] = {
                        'covered': True,
                        'context': context
                    }
                else:
                    coverage[f"Skill: {skill}"] = {
                        'covered': False,
                        'context': None
                    }

            # Format covered points with context
            for point, details in coverage.items():
                if details['covered']:
                    covered_points.append({
                        'requirement': point,
                        'context': details['context']
                    })
                
            # Add missing points
            missing_points = [
                point for point, details in coverage.items() 
                if not details['covered']
            ]
            
            return {
                'covered': covered_points,
                'missing': missing_points,
                'coverage_percentage': round(len(covered_points) / len(coverage) * 100, 1)
            }
            
        except Exception as e:
            logger.error(f"Error identifying covered points: {str(e)}")
            return {
                'covered': [],
                'missing': [],
                'coverage_percentage': 0.0
            }

    async def _generate_suggestions(self, content: str, job_analysis: JobAnalysis) -> List[str]:
        """Generate improvement suggestions for future iterations"""
        try:
            prompt = PromptTemplate(
                template="""Analyze this cover letter and provide improvement suggestions:
                {content}
                
                Job Requirements:
                {requirements}
                
                Suggest 3-5 specific improvements focusing on:
                1. Content strengthening
                2. Skills emphasis
                3. Persuasiveness
                """
            )
            
            chain = LLMChain(llm=self.llm_analyzer, prompt=prompt)
            response = await chain.arun(
                content=content,
                requirements=job_analysis.key_requirements
            )
            
            return response.split("\n")
        except Exception:
            return []