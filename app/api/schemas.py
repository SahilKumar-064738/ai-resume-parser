from pydantic import BaseModel, EmailStr, Field, HttpUrl
from typing import Optional, List, Dict
from datetime import datetime, date

class PersonalInfo(BaseModel):
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    linkedin: Optional[str] = None
    website: Optional[str] = None

class WorkExperience(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    current: bool = False
    description: Optional[str] = None
    achievements: List[str] = []
    technologies: List[str] = []

class Education(BaseModel):
    degree: Optional[str] = None
    field: Optional[str] = None
    institution: Optional[str] = None
    location: Optional[str] = None
    graduation_date: Optional[str] = None
    gpa: Optional[float] = None

class Skills(BaseModel):
    technical: List[str] = []
    soft: List[str] = []
    languages: List[Dict[str, str]] = []

class Certification(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None

class ParsedResumeResponse(BaseModel):
    id: str
    file_name: str
    personal_info: PersonalInfo
    summary: Optional[str] = None
    experience: List[WorkExperience] = []
    education: List[Education] = []
    skills: Skills
    certifications: List[Certification] = []
    raw_text: Optional[str] = None
    processed_at: datetime

class UploadResponse(BaseModel):
    id: str = "uuid"
    status: str = "processing"
    message: str = "Resume uploaded successfully"
    estimatedProcessingTime: int = 30
    webhookUrl: Optional[str] = "optional callback URL"

class JobDescription(BaseModel):
    title: str
    company: Optional[str] = None
    description: str
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    experience_required: Optional[str] = None

class MatchingScore(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    skills_match: int = Field(ge=0, le=100)
    experience_match: int = Field(ge=0, le=100)
    education_match: int = Field(ge=0, le=100)

class MatchingResult(BaseModel):
    match_id: str
    resume_id: str
    job_title: str
    scores: MatchingScore
    matched_skills: List[str]
    missing_skills: List[str]
    strengths: List[str]
    gaps: List[str]
    recommendation: str
    explanation: str
