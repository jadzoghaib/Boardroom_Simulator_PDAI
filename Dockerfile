# ── Boardroom Simulator — Dockerfile ──────────────────────────────
# BRANCH: aws-deployment
# Packages the FastAPI backend + HTML/JS/CSS frontend into a single
# container ready for deployment on AWS ECS, AppRunner, or EC2.

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for chromadb and pdfplumber
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Expose the FastAPI port
EXPOSE 8002

# Environment variables — override at runtime via ECS task definition
# or docker run -e flags. Never hardcode secrets here.
ENV AWS_REGION=us-east-1
ENV SAGEMAKER_ENDPOINT=boardroom-mistral-endpoint

# Start the FastAPI server
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8002"]
