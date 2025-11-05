from app.services.llm_service import LLMService
import re

class ResumeParser:
    """Parse resume text into structured data"""
    
    def __init__(self):
        self.llm = LLMService()
    
    async def parse(self, text: str, filename: str) -> dict:
        """Parse resume text"""
        
        prompt = """
        Extract the following information from the resume and return as JSON:
        
        {
            "personal_info": {
                "full_name": "string",
                "first_name": "string",
                "last_name": "string",
                "email": "string",
                "phone": "string",
                "address": "string",
                "linkedin": "string",
                "website": "string"
            },
            "summary": "Professional summary text",
            "experience": [
                {
                    "title": "Job title",
                    "company": "Company name",
                    "location": "Location",
                    "start_date": "YYYY-MM",
                    "end_date": "YYYY-MM or Present",
                    "current": true/false,
                    "description": "Job description",
                    "achievements": ["achievement1", "achievement2"],
                    "technologies": ["tech1", "tech2"]
                }
            ],
            "education": [
                {
                    "degree": "Degree type",
                    "field": "Field of study",
                    "institution": "University name",
                    "location": "Location",
                    "graduation_date": "YYYY-MM",
                    "gpa": 3.5
                }
            ],
            "skills": {
                "technical": ["skill1", "skill2"],
                "soft": ["skill1", "skill2"],
                "languages": [{"language": "English", "proficiency": "Native"}]
            },
            "certifications": [
                {
                    "name": "Certification name",
                    "issuer": "Issuing organization",
                    "issue_date": "YYYY-MM",
                    "expiry_date": "YYYY-MM"
                }
            ]
        }
        
        If any field is not found, use null. Extract as much information as possible.
        """
        
        # Use LLM to extract structured data
        parsed_data = await self.llm.extract_structured_data(text, prompt)
        
        # Ensure all required keys exist
        default_structure = {
            "personal_info": {},
            "summary": None,
            "experience": [],
            "education": [],
            "skills": {"technical": [], "soft": [], "languages": []},
            "certifications": []
        }
        
        for key, value in default_structure.items():
            if key not in parsed_data:
                parsed_data[key] = value
        
        return parsed_data