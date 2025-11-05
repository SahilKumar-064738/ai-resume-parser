# 🤖 AI Resume Parser

> Intelligent resume parsing system powered by OpenAI GPT-4 and FastAPI

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)

---

## ✨ Features

- 📄 **Multi-format Support** — PDF, DOCX, TXT, and Images (with OCR)
- 🧠 **AI-Powered Extraction** — Leverages OpenAI GPT-4 for intelligent parsing
- 🎯 **Resume-Job Matching** — Detailed scoring and compatibility analysis
- 🚀 **RESTful API** — Complete OpenAPI documentation
- 💾 **PostgreSQL Storage** — Reliable database backend
- 🔐 **Secure Authentication** — API key-based access control

---

## 🚀 Quick Start

---

## ⚠️ DISCLAIMER

**If the application throws any errors during startup or execution:**

Clean up Docker resources and restart from scratch:

```bash
# Clean Docker system
docker system prune -a

# Clean Docker images
docker image prune -a

# Clean Docker volumes
docker volume prune -a
```

> ⚡ **Warning:** These commands will remove **all** unused Docker resources. Make sure you don't have other important containers running.

After cleanup, **re-execute from Step 1**:

```bash
./setup.sh
```

---

### Automated Setup

Start the project with a single command:

```bash
./setup.sh
```

**What `setup.sh` does:**

1. ✅ Copies `.env.example` → `.env` (if not present)
2. 🔑 Prompts for required environment variables (including `OPENAI_API_KEY`)
3. 🐳 Verifies Docker and Docker Compose installation
4. 🏗️ Builds and starts the application
5. 🌐 Opens API documentation in your browser

> **Note:** Ensure the script is executable: `chmod +x setup.sh`

---

## 🛠️ Manual Setup

<details>
<summary><b>Expand for manual installation steps</b></summary>

### 1️⃣ Environment Configuration

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY and other required variables
```

### 2️⃣ Docker Deployment

```bash
docker compose -f docker/docker-compose.yml up --build
```

### 3️⃣ Local Development

```bash
pip install -r requirements.txt
python src/run.py
```

</details>

---

## 📚 API Documentation

Once the server is running, access the interactive API documentation:

🔗 **[http://localhost:8000/docs#/](http://localhost:8000/docs#/)**

---

## 🔌 API Endpoints

| Method   | Endpoint                     | Description                       |
| -------- | ---------------------------- | --------------------------------- |
| `POST`   | `/api/v1/resumes/upload`     | Upload and parse resume           |
| `GET`    | `/api/v1/resumes/{id}`       | Retrieve parsed resume data       |
| `POST`   | `/api/v1/resumes/{id}/match` | Match resume with job description |
| `DELETE` | `/api/v1/resumes/{id}`       | Delete resume                     |

---

## 🔐 Authentication

Include your API key in the request header:

```http
X-API-Key: your-api-key-here
```

---

## 💻 Example Usage

### Python

```python
import requests

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"X-API-Key": "your-api-key"}

# Upload resume
with open("resume.pdf", "rb") as file:
    response = requests.post(
        f"{BASE_URL}/resumes/upload",
        files={"file": file},
        headers=HEADERS
    )

resume_id = response.json()["id"]
print(f"✅ Resume uploaded: {resume_id}")

# Get parsed data
response = requests.get(
    f"{BASE_URL}/resumes/{resume_id}",
    headers=HEADERS
)

data = response.json()
print(f"📄 Resume Data: {data}")
```

### cURL

```bash
# Upload resume
curl -X POST "http://localhost:8000/api/v1/resumes/upload" \
  -H "X-API-Key: your-api-key" \
  -F "file=@resume.pdf"

# Get parsed data
curl -X GET "http://localhost:8000/api/v1/resumes/{id}" \
  -H "X-API-Key: your-api-key"
```

---

## 🏗️ Tech Stack

- **Framework:** FastAPI
- **AI Engine:** OpenAI GPT-4
- **Database:** PostgreSQL
- **Containerization:** Docker & Docker Compose
- **Document Processing:** PyPDF2, python-docx, Pillow (OCR)

---

## 📋 Requirements

- 🐍 Python 3.9+
- 🐳 Docker & Docker Compose
- 🔑 OpenAI API Key

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 📞 Support

For issues and questions:

- 📖 Check the [Documentation](http://localhost:8000/docs)
- 🐛 Report bugs via [GitHub Issues](https://github.com/yourusername/ai-resume-parser/issues)

---

<div align="center">

**Made with ❤️ using FastAPI and OpenAI**

⭐ Star this repo if you find it helpful!

</div>
