FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements/base.txt backend/requirements/fastapi.txt backend/requirements/
RUN pip install --no-cache-dir -r backend/requirements/fastapi.txt

# Copy application code
COPY backend/shared/ backend/shared/
COPY backend/fastapi_app/ backend/fastapi_app/
COPY backend/ml/ backend/ml/
COPY backend/workers/ backend/workers/
COPY backend/alembic/ backend/alembic/
COPY backend/alembic/alembic.ini .

ENV PYTHONPATH=/app/backend

# Production stage
FROM base AS production
EXPOSE 8000
CMD ["uvicorn", "fastapi_app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Development stage
FROM base AS development
RUN pip install --no-cache-dir watchfiles
CMD ["uvicorn", "fastapi_app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
