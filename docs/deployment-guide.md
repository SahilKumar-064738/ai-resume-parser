# Deployment Guide — AI Resume Parser

This guide covers deploying the AI Resume Parser from development to production (containerized). It assumes the reference codebase (FastAPI, SQLAlchemy, Google Gemini integration) is present.

## Prerequisites

- Docker & Docker Compose (for simple deployments)
- Python 3.11 local environment for development
- PostgreSQL (managed or self-hosted)
- Tesseract OCR installed on worker nodes if image OCR is required
- Google Cloud credentials and `GOOGLE_API_KEY` or service account with Model access
- An object storage bucket (S3/MinIO/GCS) recommended for production

## Environment variables (example)

```
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
DATABASE_URL=postgresql+psycopg2://postgres:password@db:5432/resume_parser
API_KEY=supersecretapikey
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE=10485760
GOOGLE_API_KEY=ya29.example
GEMINI_MODEL=gemini-2.5-flash
```

Store secrets in a secrets manager or Docker secrets in production.

## Docker Compose (example)

```yaml
version: "3.8"
services:
  app:
    build: ./src
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - API_KEY=${API_KEY}
      - UPLOAD_DIR=/app/uploads
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    volumes:
      - ./uploads:/app/uploads
    depends_on:
      - db
  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=resume_parser
    ports:
      - "5433:5432"
    volumes:
      - db_data:/var/lib/postgresql/data
volumes:
  db_data:
```

### Build & Run (development)

1. Copy or create `.env` from `.env.example` with appropriate values.
2. Build and start containers:
   ```bash
   docker compose up -d --build
   ```
3. Apply DB migrations (inside app container or locally using alembic):
   ```bash
   docker compose exec app alembic upgrade head
   ```
4. Initialize uploads dir permissions if needed:
   ```bash
   mkdir -p uploads && chmod 775 uploads
   ```

## Production considerations

- Use a production-ready ASGI server (Uvicorn + Gunicorn or Uvicorn with multiple workers behind a process manager).
- Serve behind an HTTPS load balancer (NGINX/Traefik) with TLS certs (Let's Encrypt or managed certs).
- Replace local `UPLOAD_DIR` with cloud object storage and update file access code.
- Use managed database (Amazon RDS, Cloud SQL) with automated backups.
- Store API keys and Google credentials in a secrets manager (AWS Secrets Manager / GCP Secret Manager / HashiCorp Vault).

## Kubernetes (optional)

Provide a reference for critical k8s objects:

- Deployment for `app` with 2+ replicas, resource requests/limits, and liveness/readiness probes.
- StatefulSet or Deployment for `db` (prefer using managed DB instead).
- Secret & ConfigMap for env variables.
- PersistentVolumeClaim for uploads only if using PV; prefer S3.

### Example liveness/readiness

```yaml
livenessProbe:
  httpGet:
    path: /api/v1/health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
readinessProbe:
  httpGet:
    path: /api/v1/health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
```

## Logging, monitoring & alerting

- Expose `/metrics` for Prometheus scraping (use `prometheus_client` in Python).
- Forward logs to centralized system (ELK, Cloud Logging).
- Create alerts for LLM error rates, high queue lengths, DB connection errors, and disk usage on uploads.

## Backups & Recovery

- Enable periodic DB backups and test restores.
- Snapshot or lifecycle policy for object storage.
- Keep a retention policy for raw uploads and parsed results per compliance needs.

## Troubleshooting

- **Missing env vars**: Ensure `.env` loaded and all required variables present. Look at startup logs.
- **LLM auth errors**: Validate `GOOGLE_API_KEY`, scopes, and billing/quota.
- **OCR not working**: Confirm Tesseract is installed and accessible in the container PATH.
- **File upload 413/timeout**: Increase `MAX_FILE_SIZE` and request timeouts or switch to asynchronous background processing.

---

If you'd like, I can:

- Generate Kubernetes manifests (Deployment, Service, Secret) for production.
- Create a GitHub Actions pipeline to build and push Docker images.
- Split this into a downloadable `deployment-guide.md` and commit it to your repo (if you give repo access).
