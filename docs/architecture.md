# Architecture — AI Resume Parser

## High-level overview

The AI Resume Parser is a modular microservice-style application designed to ingest resumes (PDF, DOCX, TXT, images), extract text using format-specific processors and OCR, normalize the extracted text, call a Large Language Model (Google Gemini in the reference implementation) to convert unstructured text to structured JSON, and persist both raw files and structured data for retrieval and further processing (job matching).

### Primary components

- **API Gateway / FastAPI App** — Serves HTTP endpoints (`/api/v1/*`), performs API key authentication, input validation, and coordinates processing workflows.

- **Document Processor** — Handles format-specific extraction:
- PDF: `pdfplumber` / `PyPDF2`
- DOCX: `python-docx`
- Images: `Pillow` + `pytesseract` (Tesseract OCR)
- TXT: direct read

- **Resume Parser (LLM Service)** — Sends text payloads to an LLM (Gemini) to produce structured JSON. Includes request templating, retry/backoff, prompt engineering, and JSON schema validation.

- **Job Matcher** — Uses the LLM or local scoring logic (embedding + cosine similarity) to compare resume contents to job descriptions and return a ranked match with field-level explainability.

- **Data Layer** — PostgreSQL with SQLAlchemy ORM. `Resume` model stores metadata and a `parsed_data` JSONB column. Raw files are stored in `UPLOAD_DIR` (local filesystem or object storage like S3).

- **Optional Worker / Background Queue** — For long-running tasks (LLM calls, OCR), a background worker (Celery/RQ or FastAPI background tasks) processes jobs from a queue so the API can return quickly.

- **Vector Store (optional)** — Use `pgvector` or a dedicated vector DB to store embeddings for fast similarity search for job matching and semantic retrieval.

- **Monitoring & Logging** — Centralized logging (stdout -> log aggregator), metrics (Prometheus) and dashboards (Grafana), health checks and readiness probes.

## Data Flow

1. Client calls `POST /api/v1/resumes/upload` with multipart file and API key.
2. API validates file type/size and writes raw file to `UPLOAD_DIR`.
3. API enqueues a processing job (or runs sync for small files): Document Processor extracts raw text.
4. Extracted text is passed to Resume Parser which calls the LLM service to transform into structured JSON.
5. Structured JSON is validated, normalized and stored in PostgreSQL (`parsed_data` JSONB), and resume metadata is inserted into `resumes` table.
6. API responds with created resource information and ID. Client may poll or call `GET /api/v1/resumes/{id}` for final parsed result.

## Security & Config

- API Key authentication via `X-API-KEY`. For production consider OAuth or mTLS for partner integrations.
- Sensitive configuration in environment variables. Use HashiCorp Vault or cloud secrets manager for production.
- Validate and sanitize all inputs. Use safe file name generation (UUIDs) and enforce hard limits on upload size.

## Scalability

- Scale FastAPI workers behind a load balancer.
- Deploy background workers separately and scale independently (horizontal autoscaling).
- Move file storage to S3/Cloud Storage to enable stateless API nodes.
- Use a managed PostgreSQL cluster and `pgvector` for semantic search.

## Resilience

- Retries with exponential backoff for transient LLM/API errors.
- Circuit breaker around external LLM calls.
- Database backups and file storage lifecycle management.

## Technologies (reference)

- Python 3.11, FastAPI, Uvicorn
- SQLAlchemy, Alembic
- PostgreSQL (+ pgvector)
- pdfplumber, python-docx, Pillow, pytesseract
- Google Gemini (LLM) via Google Cloud APIs
- Docker, Docker Compose
