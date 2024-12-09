from datetime import datetime
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain.chains import SequentialChain, LLMChain
from langchain.output_parsers import PydanticOutputParser
from langchain.pydantic_v1 import BaseModel, Field, validator
from typing import Dict, Optional, List
from datetime import datetime
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
            model_name="gpt-4o-mini",
            temperature=0.2,
            api_key=settings.OPENAI_API_KEY
        )
        self.llm_writer = ChatOpenAI(
            model_name="gpt-4o",
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
            
            return CoverLetterResponse(
                draft=CoverLetterDraft(
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
                ),
                job_analysis=job_analysis["analysis"],
                cv_analysis=cv_analysis["analysis"],
                status="completed",
                credits_used=total_tokens_used
            )
            
        except Exception as e:
            logger.error(f"Cover letter generation failed: {str(e)}")
            raise

    async def _analyze_job_posting(self, job_description: str) -> Dict:
        """Analyze job posting for key details"""
        try:
            parser = PydanticOutputParser(pydantic_object=JobAnalysis)
            prompt = PromptTemplate(
                template="""Analyze this job posting comprehensively:
                {job_description}
                
                Extract the following with high precision:
                1. Company name and any background information
                2. Exact position title and level
                3. All stated and implied requirements
                4. Technical and soft skills needed
                5. Company culture indicators and values
                6. Department and reporting structure
                7. Contact details if available
                8. Location and work arrangement details
                
                Provide structured analysis following this format:
                {format_instructions}
                """,
                input_variables=["job_description"],
                partial_variables={"format_instructions": parser.get_format_instructions()}
            )

            chain = LLMChain(llm=self.llm_analyzer, prompt=prompt)
            response = await chain.arun(job_description=job_description)
            
            return {
                "analysis": parser.parse(response),
                "tokens_used": len(response.split()) * 1.3  # Approximate token count
            }
            
        except Exception as e:
            logger.error(f"Job analysis failed: {str(e)}")
            raise

    async def _analyze_cv(self, cv_content: Dict, job_analysis: JobAnalysis) -> Dict:
        """Analyze CV in context of job requirements"""
        try:
            parser = PydanticOutputParser(pydantic_object=CVAnalysis)
            prompt = PromptTemplate(
                template="""Analyze this CV for job matching:
                
                CV Content: {cv_content}
                
                Job Requirements:
                Position: {position}
                Required Skills: {required_skills}
                Key Requirements: {key_requirements}
                
                Provide detailed analysis:
                1. Most relevant experiences for this role
                2. Skills that directly match requirements
                3. Quantifiable achievements
                4. Unique selling points for this position
                5. Any gaps or areas needing emphasis
                
                Format requirements:
                {format_instructions}
                """,
                input_variables=["cv_content", "position", "required_skills", "key_requirements"],
                partial_variables={"format_instructions": parser.get_format_instructions()}
            )

            chain = LLMChain(llm=self.llm_analyzer, prompt=prompt)
            response = await chain.arun(
                cv_content=cv_content,
                position=job_analysis.position,
                required_skills=job_analysis.required_skills,
                key_requirements=job_analysis.key_requirements
            )
            
            return {
                "analysis": parser.parse(response),
                "tokens_used": len(response.split()) * 1.3
            }
        except Exception as e:
            logger.error(f"CV analysis failed: {str(e)}")
            raise ValueError(f"Failed to analyze CV: {str(e)}")

    async def _generate_draft(
        self, 
        cv_analysis: CVAnalysis,
        job_analysis: JobAnalysis,
        request: CoverLetterRequest
    ) -> Dict:
        """Generate initial cover letter draft"""
        try:
            style_prompts = {
                WriteStyle.PROFESSIONAL: "formal and polished",
                WriteStyle.CREATIVE: "innovative and engaging",
                WriteStyle.ACADEMIC: "scholarly and detailed",
                WriteStyle.MODERN: "dynamic and contemporary",
                WriteStyle.TRADITIONAL: "classic and conventional"
            }

            # Calculate matching scores first
            matching_result = self._calculate_matching_score(cv_analysis, job_analysis)
            match_level = self._get_match_details(matching_result['total_score'])

            prompt = ChatPromptTemplate.from_template(
                """Write a compelling cover letter with these specifications:
                
                Company Details:
                Company: {company}
                Position: {position}
                Department: {department}
                
                Candidate Qualifications:
                Key Experiences: {experiences}
                Matching Skills: {skills}
                Notable Achievements: {achievements}
                Value Proposition: {value_prop}
                
                Style Guide:
                Tone: {style_guide}
                Additional Preferences: {tone_preferences}
                
                Writing Instructions:
                1. Begin with a powerful opening showing company research
                2. Draw clear parallels between experiences and job requirements
                3. Demonstrate cultural alignment with company values
                4. Include specific achievements with metrics
                5. Address any potential concerns proactively
                6. End with confident call to action
                7. Keep length between 250-400 words
                
                Company Values to Emphasize: {company_values}
                """
            )

            chain = LLMChain(llm=self.llm_writer, prompt=prompt)
            response = await chain.arun(
                company=job_analysis.company_name,
                position=job_analysis.position,
                department=job_analysis.department,
                experiences=cv_analysis.key_experiences,
                skills=cv_analysis.highlighted_skills,
                achievements=cv_analysis.achievements,
                value_prop=cv_analysis.value_proposition,
                style_guide=style_prompts[request.style],
                tone_preferences=request.tone_preferences,
                company_values=job_analysis.company_values
            )
            
            return {
                "content": response,
                "tokens_used": len(response.split()) * 1.3,
                "matching_score": matching_result['total_score'],
                "match_level": match_level,
                "matching_details": {
                    "skills_match": matching_result['skills_score'],
                    "experience_match": matching_result['experience_score'],
                    "education_match": matching_result['education_score'],
                    "achievement_match": matching_result['achievement_score']
                },
                "points_covered": self._identify_covered_points(response, job_analysis),
                "improvement_suggestions": await self._generate_suggestions(response, job_analysis)
            }
            
        except Exception as e:
            logger.error(f"Draft generation failed: {str(e)}")
            raise ValueError(f"Failed to generate draft: {str(e)}")

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