FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements/base.txt backend/requirements/django.txt backend/requirements/
RUN pip install --no-cache-dir -r backend/requirements/django.txt

# Copy application code
COPY backend/shared/ backend/shared/
COPY backend/django_app/ backend/django_app/

ENV PYTHONPATH=/app/backend
WORKDIR /app/backend/django_app

EXPOSE 8001

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8001", "--workers", "2"]
