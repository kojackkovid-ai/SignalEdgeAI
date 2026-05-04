# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.12.10
FROM python:${PYTHON_VERSION}-slim AS base

# Prevent Python from writing .pyc files and buffer logs.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# Install system dependencies required for PostgreSQL and ML.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    postgresql-client \
    libpq-dev \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create non-privileged app user.
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# Install Python dependencies.
COPY backend/requirements.txt /app/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install -r /app/requirements.txt

# Copy startup script and make it executable.
COPY backend/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Copy backend source code.
COPY backend/app /app/app
COPY backend/check_startup.py /app/check_startup.py

# Copy frontend build output from repository root to /app/static.
COPY frontend/dist /app/static

# Ensure the ml-models directory exists.
RUN mkdir -p /app/ml-models/trained

USER appuser

EXPOSE 8000
WORKDIR /app/backend
CMD ["/app/start.sh"]
