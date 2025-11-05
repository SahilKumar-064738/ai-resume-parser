
set -e

# --- Colors ---
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting setup for AI Resume Parser...${NC}"

# --- Step 1: Check if Docker is installed ---
if ! command -v docker &> /dev/null
then
    echo -e "${RED}❌ Docker not found! Please install Docker first.${NC}"
    exit 1
fi

# --- Step 2: Check if Docker is running ---
if (! docker stats --no-stream &> /dev/null); then
    echo -e "${YELLOW}🐳 Docker daemon is not running. Trying to start it...${NC}"
    # macOS & Windows use GUI; Linux can start via systemctl
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo systemctl start docker
    else
        echo -e "${YELLOW}⚠️  Please start Docker Desktop manually and rerun this script.${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Docker is running.${NC}"

# --- Step 3: Check if docker-compose is available ---
if ! command -v docker compose &> /dev/null
then
    echo -e "${RED}❌ docker compose not found! Please install Docker Compose plugin.${NC}"
    exit 1
fi

# --- Step 4: Build and start containers ---
echo -e "${GREEN}🧩 Building and starting containers...${NC}"
docker compose -f docker/docker-compose.yml up --build -d

# --- Step 5: Wait for FastAPI service to become ready ---
echo -e "${YELLOW}⏳ Waiting for FastAPI to start on port 8000...${NC}"

RETRIES=30
until curl -s http://localhost:8000/docs > /dev/null; do
    ((RETRIES--))
    if [ $RETRIES -le 0 ]; then
        echo -e "${RED}❌ FastAPI service did not start in time.${NC}"
        docker compose logs app
        exit 1
    fi
    sleep 2
done

echo -e "${GREEN}✅ FastAPI is up and running!${NC}"

# --- Step 6: Open API docs in browser ---
echo -e "${GREEN}🌐 Opening http://localhost:8000/docs#/ in your default browser...${NC}"

# Open URL in default browser based on OS
if which xdg-open > /dev/null; then
    xdg-open "http://localhost:8000/docs#/"
elif which open > /dev/null; then
    open "http://localhost:8000/docs#/"
elif which start > /dev/null; then
    start "http://localhost:8000/docs#/"
else
    echo -e "${YELLOW}⚠️  Could not detect browser opener. Please visit manually: http://localhost:8000/docs#/${NC}"
fi

echo -e "${GREEN}🎉 Setup complete! You can now explore the API docs at: http://localhost:8000/docs#/${NC}"
