# ApexAurum Cloud - Production Dockerfile for Railway
# Note: Railway uses rootDirectory=backend, so paths are relative to backend/
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (relative to backend/)
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Force rebuild v9
RUN echo "Build: v9-noauth-$(date +%s)" > /tmp/build-info.txt

# Copy application code (relative to backend/)
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini

# Create non-root user
RUN useradd -m -u 1000 apex && chown -R apex:apex /app
USER apex

# Railway uses PORT env variable
ENV PORT=8080
EXPOSE $PORT

# Start command
CMD ["sh", "-c", "echo 'Starting uvicorn v9...' && python -u -m uvicorn app.main:app --host 0.0.0.0 --port $PORT --log-level info"]
