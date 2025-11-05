from app.services.llm_service import LLMService

class JobMatcher:
    """Match resumes with job descriptions"""
    
    def __init__(self):
        self.llm = LLMService()
    
    async def match(self, resume_data: dict, job_data: dict) -> dict:
        """Match resume with job description"""
        
        # Use LLM for intelligent matching
        result = await self.llm.analyze_match(resume_data, job_data)
        
        # Ensure scores structure
        if "scores" not in result:
            result["scores"] = {
                "overall_score": result.get("overall_score", 0),
                "skills_match": result.get("skills_match", 0),
                "experience_match": result.get("experience_match", 0),
                "education_match": result.get("education_match", 0)
            }
        
        return result