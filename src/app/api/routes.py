from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Header
from typing import Optional
from app.api.schemas import *
from app.services.document_processor import DocumentProcessor
from app.services.resume_parser import ResumeParser
from app.services.job_matcher import JobMatcher
from app.database.models import Resume, session_scope
from app.config import settings
from app.utils.validators import validate_file
import uuid
from datetime import datetime
import os

router = APIRouter()

# Simple API Key authentication
async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key

@router.post("/resumes/upload", response_model=UploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    """Upload and parse a resume"""
    try:
        # Validate file
        validate_file(file)
        
        # Generate unique ID
        resume_id = str(uuid.uuid4())
        
        # Save file
        file_path = os.path.join(settings.UPLOAD_DIR, f"{resume_id}_{file.filename}")
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Process document
        processor = DocumentProcessor()
        text = processor.extract_text(file_path, file.filename)
        
        # Parse resume
        parser = ResumeParser()
        parsed_data = await parser.parse(text, file.filename)
        
        # Save to database
        with session_scope() as session:
            resume = Resume(
                id=resume_id,
                file_name=file.filename,
                file_path=file_path,
                raw_text=text,
                parsed_data=parsed_data,
                processed_at=datetime.utcnow()
            )
            session.add(resume)
            session.commit()
        
        return UploadResponse(
            id=resume_id,
            status="success",
            message="Resume processed successfully",
            file_name=file.filename
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/resumes/{resume_id}", response_model=ParsedResumeResponse)
async def get_resume(
    resume_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get parsed resume data"""
    try:
        with session_scope() as session:
            resume = session.query(Resume).filter(Resume.id == resume_id).first()
            
            if not resume:
                raise HTTPException(status_code=404, detail="Resume not found")
            
            return ParsedResumeResponse(
                id=resume.id,
                file_name=resume.file_name,
                personal_info=PersonalInfo(**resume.parsed_data.get("personal_info", {})),
                summary=resume.parsed_data.get("summary"),
                experience=[WorkExperience(**exp) for exp in resume.parsed_data.get("experience", [])],
                education=[Education(**edu) for edu in resume.parsed_data.get("education", [])],
                skills=Skills(**resume.parsed_data.get("skills", {})),
                certifications=[Certification(**cert) for cert in resume.parsed_data.get("certifications", [])],
                raw_text=resume.raw_text,
                processed_at=resume.processed_at
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import uuid
import logging

logger = logging.getLogger(__name__)

@router.post("/resumes/{resume_id}/match", response_model=MatchingResult)
async def match_resume(
    resume_id: str,
    job_description: JobDescription,
    api_key: str = Depends(verify_api_key)
):
    """Match resume with job description"""
    try:
        with session_scope() as session:
            resume = session.query(Resume).filter(Resume.id == resume_id).first()
            
            if not resume:
                raise HTTPException(status_code=404, detail="Resume not found")
            
            matcher = JobMatcher()
            result = await matcher.match(resume.parsed_data, job_description.dict())

            # Remove keys from result that we set explicitly to avoid duplicate kwargs
            result.pop("match_id", None)
            result.pop("resume_id", None)
            result.pop("job_title", None)

            return MatchingResult(
                match_id=str(uuid.uuid4()),
                resume_id=resume_id,
                job_title=job_description.title,
                **result
            )
    except HTTPException:
        raise
    except Exception as e:
        # log full exception for debugging
        logger.exception("Error matching resume %s: %s", resume_id, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/resumes/{resume_id}")
async def delete_resume(
    resume_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Delete a resume"""
    try:
        with session_scope() as session:
            resume = session.query(Resume).filter(Resume.id == resume_id).first()
            
            if not resume:
                raise HTTPException(status_code=404, detail="Resume not found")
            
            # Delete file
            if os.path.exists(resume.file_path):
                os.remove(resume.file_path)
            
            session.delete(resume)
            session.commit()
            
            return {"message": "Resume deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))