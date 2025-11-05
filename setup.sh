#!/usr/bin/env bash
set -euo pipefail

# --- Colors ---
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting setup for AI Resume Parser...${NC}"

# Find the directory where this script lives (works when executed or sourced)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Walk up the directory tree from the script directory to locate the `docker/docker-compose.yml`
PROJECT_ROOT=""
CUR_DIR="$SCRIPT_DIR"
while [ "$CUR_DIR" != "/" ]; do
  if [ -f "$CUR_DIR/docker/docker-compose.yml" ]; then
    PROJECT_ROOT="$CUR_DIR"
    break
  fi
  CUR_DIR="$(dirname "$CUR_DIR")"
done

# If not found, also try current working directory (in case script was executed from elsewhere)
if [ -z "${PROJECT_ROOT}" ] && [ -f "$(pwd)/docker/docker-compose.yml" ]; then
  PROJECT_ROOT="$(pwd)"
fi

if [ -z "${PROJECT_ROOT}" ]; then
  echo -e "${RED}❌ Could not find docker/docker-compose.yml in this folder or any parent folders.${NC}"
  echo -e "${YELLOW}⚠️  Make sure you run this script from inside the project, or place this script inside the project directory.${NC}"
  exit 1
fi

echo -e "${GREEN}📁 Found project root at: ${PROJECT_ROOT}${NC}"
cd "${PROJECT_ROOT}"

# --- Step 1: Check if Docker is installed ---
if ! command -v docker >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker not found! Please install Docker first.${NC}"
    exit 1
fi

# --- Step 2: Check if Docker daemon is running ---
if ! docker stats --no-stream >/dev/null 2>&1; then
    echo -e "${YELLOW}🐳 Docker daemon appears not to be running. Attempting to start (Linux only)...${NC}"
    if [[ "${OSTYPE:-}" == "linux-gnu"* ]]; then
        if command -v systemctl >/dev/null 2>&1; then
            sudo systemctl start docker || true
            sleep 2
        fi
    fi
    # re-check
    if ! docker stats --no-stream >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Docker still not running. Please start Docker Desktop / daemon and re-run this script.${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Docker is running.${NC}"

# --- Step 3: Check if docker compose is available ---
if ! docker compose version >/dev/null 2>&1; then
    echo -e "${RED}❌ docker compose plugin not found! Please install Docker Compose plugin (or upgrade Docker).${NC}"
    exit 1
fi

# --- Step 4: Build and start containers (from project root) ---
echo -e "${GREEN}🧩 Building and starting containers using: docker compose -f docker/docker-compose.yml up --build${NC}"

# Run without -d so logs appear if the user double-clicks; if you prefer detached, change to append -d
docker compose -f docker/docker-compose.yml up --build

# If the command returns, we assume compose finished/stopped
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
  echo -e "${GREEN}🎉 docker compose finished successfully.${NC}"
else
  echo -e "${RED}❌ docker compose exited with code ${EXIT_CODE}.${NC}"
fi

# --- Optional: open API docs (only when containers are started in background) ---
# If you want the script to open http://localhost:8000/docs#/ automatically, run the compose command with -d
# Example: docker compose -f docker/docker-compose.yml up --build -d

exit $EXIT_CODE
