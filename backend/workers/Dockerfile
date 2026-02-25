FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies (includes ML libs for inference)
COPY backend/requirements/base.txt backend/requirements/ml.txt backend/requirements/
RUN pip install --no-cache-dir -r backend/requirements/base.txt -r backend/requirements/ml.txt

# Copy application code
COPY backend/shared/ backend/shared/
COPY backend/ml/ backend/ml/
COPY backend/workers/ backend/workers/

ENV PYTHONPATH=/app/backend

CMD ["celery", "-A", "workers.celery_app:celery_app", "worker", \
     "--loglevel=info", "--concurrency=4", \
     "--queues=image_processing,description_generation,notifications"]
