# Fly.io Production Dockerfile
ARG PYTHON_VERSION=3.12.10
FROM python:${PYTHON_VERSION}-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    postgresql-client \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-privileged user
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# Copy and install requirements
COPY backend/requirements.txt .
RUN python -m pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code - copy entire backend as app/ for proper imports
COPY backend/ /app/backend/
COPY ml-models/ /app/ml-models/ 2>/dev/null || true

# Create necessary directories
RUN mkdir -p /app/logs && chown -R appuser:appuser /app

# Set correct Python path for backend
ENV PYTHONPATH=/app/backend

# Switch to non-privileged user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Change to backend directory and run uvicorn without reload, with multiple workers
WORKDIR /app/backend
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
