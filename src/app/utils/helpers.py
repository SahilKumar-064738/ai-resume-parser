import re
from typing import Optional

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters
    text = re.sub(r'[^\w\s@.,\-()]', '', text)
    return text.strip()

def extract_email(text: str) -> Optional[str]:
    """Extract email from text"""
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(pattern, text)
    return match.group(0) if match else None

def extract_phone(text: str) -> Optional[str]:
    """Extract phone number from text"""
    pattern = r'\+?[\d\s\-\(\)]{10,}'
    match = re.search(pattern, text)
    return match.group(0) if match else None
