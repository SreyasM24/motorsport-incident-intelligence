# Production Dockerfile for Motorsport Incident Intelligence Backend
FROM python:3.13-slim as base

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install runtime system dependencies (curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root user
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -m -s /bin/bash appuser

WORKDIR /app

# Copy dependency specification and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code, migrations, and scripts
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY scripts/ ./scripts/

# Create data cache directories with proper permissions
RUN mkdir -p /app/data/cache/fastf1 && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

EXPOSE 8000

# Healthcheck targeting liveness endpoint
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/live || exit 1

# Production command executing migrations before launching uvicorn with worker pool
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2"]
