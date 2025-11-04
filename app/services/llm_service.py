from openai import OpenAI
from app.config import settings
import json

class LLMService:
    """OpenAI integration for intelligent parsing"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
    
    async def extract_structured_data(self, text: str, prompt: str) -> dict:
        """Extract structured data using LLM"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert resume parser. Extract information accurately and return valid JSON."},
                    {"role": "user", "content": f"{prompt}\n\nResume Text:\n{text}"}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content
            return json.loads(result)
        
        except Exception as e:
            print(f"LLM Error: {e}")
            return {}
    
    async def analyze_match(self, resume_data: dict, job_data: dict) -> dict:
        """Analyze resume-job match using LLM"""
        prompt = f"""
        Analyze how well this resume matches the job description.
        
        Resume Data: {json.dumps(resume_data, indent=2)}
        
        Job Description: {json.dumps(job_data, indent=2)}
        
        Provide a detailed matching analysis with:
        1. Overall match score (0-100)
        2. Skills match score (0-100)
        3. Experience match score (0-100)
        4. Education match score (0-100)
        5. List of matched skills
        6. List of missing skills
        7. Strengths (list)
        8. Gaps (list)
        9. Recommendation (Strong Match/Good Match/Partial Match/Poor Match)
        10. Detailed explanation
        
        Return as JSON with keys: overall_score, skills_match, experience_match, education_match, 
        matched_skills, missing_skills, strengths, gaps, recommendation, explanation
        """
        
        return await self.extract_structured_data("", prompt)