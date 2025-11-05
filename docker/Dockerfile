FROM python:3.11-slim

# set working dir to app root
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for better layer caching (context must include project root)
COPY src/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source into image
# We copy only the src folder into /app/src to avoid noise from other files
COPY src/ /app/src/

# Create uploads directory inside container
RUN mkdir -p /app/uploads

EXPOSE 8000

# Run the app from the installed source location
CMD ["python", "src/run.py"]
