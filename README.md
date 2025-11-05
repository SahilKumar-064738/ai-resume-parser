# AI Resume Parser

Intelligent resume parsing system using OpenAI GPT-4 and FastAPI.

## Features

- Multi-format support (PDF, DOCX, TXT, Images with OCR)
- AI-powered extraction using OpenAI GPT-4
- Resume-Job matching with detailed scoring
- RESTful API with OpenAPI documentation
- PostgreSQL database storage

## Quick Start

### 1. Setup Environment

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Run with Docker

```bash
docker compose -f docker/docker-compose.yml up --build
```

### 3. Run Locally

```bash
pip install -r requirements.txt
python src/run.py
```

## API Endpoints

- `POST /api/v1/resumes/upload` - Upload and parse resume
- `GET /api/v1/resumes/{id}` - Get parsed resume data
- `POST /api/v1/resumes/{id}/match` - Match resume with job
- `DELETE /api/v1/resumes/{id}` - Delete resume

## API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## Authentication

Include API key in header:

```
X-API-Key: your-api-key-here
```

## Example Usage

```python
import requests

# Upload resume
files = {'file': open('resume.pdf', 'rb')}
headers = {'X-API-Key': 'your-api-key'}
response = requests.post(
    'http://localhost:8000/api/v1/resumes/upload',
    files=files,
    headers=headers
)
resume_id = response.json()['id']

# Get parsed data
response = requests.get(
    f'http://localhost:8000/api/v1/resumes/{resume_id}',
    headers=headers
)
print(response.json())
```

## License

MIT
