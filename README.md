# ImagineAI

**AI-Powered E-Commerce Image Intelligence Platform**

ImagineAI is a full-stack platform that automates product image analysis for
e-commerce. Upload product photos and the system automatically classifies them,
extracts attributes (color, material, condition), detects defects, and generates
natural-language product descriptions using an ML pipeline backed by AWS Bedrock.

The platform supports multi-tenancy, batch processing, webhook integrations,
data exports, A/B testing for ML models, and real-time processing updates via
WebSockets.

---

## Architecture

```
 Angular SPA (:4200)
      |
   HTTPS / WSS
      |
 FastAPI API (:8000)  +  Django Admin (:8001)
      |                        |
      +------ PostgreSQL ------+
      |            |
      |       Rate Limiter
      |
 RabbitMQ (:5672)
      |
 Celery Workers + Celery Beat
      |
      +-- ML Pipeline -----> AWS Bedrock (Claude)
      +-- Webhooks ---------> External Services
      +-- Notifications ----> Users
      +-- Exports ----------> S3
      |
 AWS S3 (Images)
      |
 Redis (:6379)
   - Result backend
   - Pub/Sub (WebSocket)
   - Cache
```

Real-time processing updates are pushed to the frontend via WebSocket
connections backed by Redis pub/sub.

---

## Key Features

- **Image Classification** -- Automatic product categorization using PyTorch models
- **Feature Extraction** -- Color, material, condition, and attribute detection
- **Defect Detection** -- Visual defect identification with bounding box overlays
- **Description Generation** -- Natural-language product descriptions via AWS Bedrock (Claude 3.5 Sonnet)
- **Batch Processing** -- Upload and process multiple images in a single job
- **Multi-Tenancy** -- Organization-based data isolation and management
- **Webhook Integrations** -- HTTP callbacks for pipeline events to external services
- **Data Exports** -- Export analysis results in bulk
- **A/B Testing** -- Compare ML model variants with admin controls
- **Rate Limiting** -- Per-user and per-organization request throttling
- **Real-Time Updates** -- WebSocket-driven processing status in the UI
- **Dashboard & Analytics** -- Metrics and insights on processing activity

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Angular 17, Angular Material 17, RxJS 7.8, Chart.js 4.4 |
| **API** | FastAPI (Python 3.12), async SQLAlchemy, Pydantic v2 |
| **Admin** | Django 5, Django Admin |
| **Task Queue** | Celery + Celery Beat + RabbitMQ (broker) + Redis (result backend) |
| **ML** | PyTorch, AWS Bedrock (Claude 3.5 Sonnet) |
| **Database** | PostgreSQL 16 |
| **Cache / PubSub** | Redis 7 |
| **Storage** | AWS S3 (LocalStack for local dev) |
| **Infrastructure** | Terraform, Kubernetes (EKS), Helm, ArgoCD |
| **Monitoring** | Prometheus, Grafana, Alertmanager |
| **CI/CD** | GitLab CI/CD, ArgoCD |
| **Security** | Trivy (container scanning), Safety (dependency check) |

---

## Quick Start

### Prerequisites

- Docker 24.0+
- Docker Compose 2.20+
- Make

### Setup

```bash
# Clone the repository
git clone https://github.com/your-org/ImagineAI.git
cd ImagineAI

# Copy environment file
cp .env.example .env

# Start all services
docker compose up -d

# Run database migrations
make migrate

# Seed demo data
make seed
```

### Access the application

| Service | URL |
|---|---|
| Frontend | http://localhost:4200 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |
| Django Admin | http://localhost:8001/admin |
| RabbitMQ Management | http://localhost:15672 |

### Demo credentials

| User | Email | Password |
|---|---|---|
| Admin | admin@imagineai.com | admin123456 |
| Demo | demo@imagineai.com | demo12345678 |
| Test | test@imagineai.com | test12345678 |

---

## Development Commands

```bash
make help                  # Show all available commands

# Docker
make build                 # Build all Docker images
make up                    # Start all services
make down                  # Stop all services
make restart               # Restart all services
make logs                  # Tail logs for all services
make logs-api              # Tail FastAPI logs
make logs-worker           # Tail Celery worker logs

# Database
make migrate               # Run Alembic migrations
make migrate-create msg="description"   # Create a new migration
make migrate-downgrade     # Downgrade one migration

# Testing
make test                  # Run all backend tests
make test-cov              # Run tests with coverage
make test-ml               # Run ML tests only

# Linting
make lint                  # Run linters
make lint-fix              # Fix linting issues

# Seed Data
make seed                  # Seed the database with demo data

# Django Admin
make django-shell          # Open Django shell
make django-createsuperuser  # Create Django superuser

# Utilities
make shell-api             # Shell into FastAPI container
make shell-worker          # Shell into Celery worker container
make clean                 # Remove all containers, volumes, and images
```

---

## Project Structure

```
ImagineAI/
  backend/
    shared/                 # Shared code (models, schemas, config, database)
      models/               # SQLAlchemy async models
        user.py             #   User accounts
        product.py          #   Products
        pipeline.py         #   Pipeline jobs
        analysis.py         #   Analysis results
        organization.py     #   Multi-tenant organizations
        webhook.py          #   Webhook endpoints
        export.py           #   Export jobs
        rate_limit.py       #   Rate limiting rules
        ab_testing.py       #   A/B test configurations
      schemas/              # Pydantic request/response schemas
      config.py             # Application settings (pydantic-settings)
      database.py           # Async engine and session factory
      constants.py          # Enums (statuses, categories, step names)
      exceptions.py         # Custom exception hierarchy
    fastapi_app/            # FastAPI application
      api/
        v1/                 # Versioned API routes
          auth.py           #   Authentication (JWT)
          products.py       #   Product CRUD
          uploads.py        #   File uploads (S3)
          jobs.py           #   Pipeline job status
          analysis.py       #   Analysis results retrieval
          batch.py          #   Batch processing
          dashboard.py      #   Dashboard metrics
          organizations.py  #   Organization management
          exports.py        #   Data exports
          webhooks.py       #   Webhook management
          health.py         #   Health checks
          admin/            #   Admin-only endpoints
            rate_limits.py  #     Rate limit configuration
            ab_testing.py   #     A/B testing management
        deps.py             # Dependency injection
        websocket.py        # WebSocket handler
      services/             # Business logic
        auth_service.py     #   JWT, password hashing
        product_service.py  #   Product operations
        upload_service.py   #   S3 upload handling
        organization_service.py  # Tenant management
        webhook_service.py  #   Webhook delivery
      middleware/            # HTTP middleware
        request_id.py       #   Request ID tracking
        rate_limiter.py     #   Rate limiting
      main.py               # Application factory and lifespan
    django_app/             # Django admin application
      apps/                 # Django apps (accounts, products, analysis, pipeline)
      config/               # Django settings and URL configuration
    workers/                # Celery task workers
      tasks/                # Task modules
        image_processing.py #   Image preprocessing
        classification.py   #   Image classification
        feature_extraction.py  # Feature extraction
        defect_detection.py #   Defect detection
        description_gen.py  #   LLM description generation
        batch_processing.py #   Batch job orchestration
        export_tasks.py     #   Data export jobs
        notifications.py    #   User notifications
        webhook_delivery.py #   Webhook HTTP delivery
      celery_app.py         # Celery application configuration
    ml/                     # Machine learning pipeline
      models/               # ML model implementations
        classifier.py       #   Image classification
        feature_extractor.py  # Feature extraction
        defect_detector.py  #   Defect detection
        model_registry.py   #   Model loading and registry
      services/             # ML inference services
        preprocessing.py    #   Image preprocessing
        inference.py        #   Model inference
        bedrock_client.py   #   AWS Bedrock client
        description_generator.py  # LLM-based descriptions
      weights/              # Model weights storage
      config.py             # ML-specific configuration
    alembic/                # Database migrations
    tests/                  # Test suite
      test_api/             #   API endpoint tests
      test_ml/              #   ML pipeline tests
      test_workers/         #   Worker task tests
      factories.py          #   Test data factories
    requirements/           # Pip dependency files
      base.txt              #   Core dependencies
      fastapi.txt           #   FastAPI-specific
      django.txt            #   Django-specific
      ml.txt                #   ML libraries
      dev.txt               #   Dev/test tools
  frontend/                 # Angular single-page application
    src/app/
      core/                 # Singleton services and state
        guards/             #   Route guards (auth)
        interceptors/       #   HTTP interceptors (auth, error, rate-limit)
        models/             #   TypeScript interfaces
        services/           #   API, auth, notification, organization, WebSocket
        store/              #   State management
      features/             # Feature modules
        auth/               #   Login, registration
        dashboard/          #   Dashboard with widgets
        upload/             #   Single and batch image upload
        products/           #   Product list, detail, form
        analysis/           #   Analysis viewer, defect overlay, description panel
        exports/            #   Data export management
        settings/           #   Organization settings, webhook configuration
        admin/              #   A/B testing management
        layout/             #   App shell (header, sidebar)
      shared/               # Shared components, directives, pipes
        components/         #   image-upload, image-annotator, processing-status, confirm-dialog
  infrastructure/
    terraform/              # AWS infrastructure as code
      modules/              #   VPC, EKS, RDS, ElastiCache, S3, ECR, IAM, MQ
      environments/         #   Per-environment variable files (dev, staging, prod)
    k8s/                    # Kubernetes manifests (Kustomize)
      base/                 #   Base manifests (fastapi, django, celery-worker, frontend)
      overlays/             #   Environment-specific overrides (dev, staging, prod)
    helm/                   # Helm chart for templated deployments
    argocd/                 # ArgoCD application manifests (Application, ApplicationSet, Project)
  monitoring/               # Observability stack
    prometheus/             #   Prometheus config and alert rules
      rules/                #     application.yml, infrastructure.yml
    grafana/                #   Grafana dashboards and provisioning
      dashboards/           #     application-overview, celery-workers, ml-pipeline
    alerts/                 #   Alertmanager configuration
  scripts/
    localstack-init.sh      # LocalStack S3 bucket initialization
    seed_data.py            # Database seed script
  docs/
    architecture.md         # System architecture documentation
    api.md                  # API reference
    deployment.md           # Deployment guide
  .gitlab-ci.yml            # CI/CD pipeline (lint, test, build, security, deploy)
  docker-compose.yml        # Local development orchestration
  Makefile                  # Development command shortcuts
  pyproject.toml            # Python project metadata and tool configuration
  .env.example              # Environment variable template
```

---

## CI/CD Pipeline

The `.gitlab-ci.yml` defines a multi-stage pipeline:

| Stage | Jobs |
|---|---|
| **Lint** | Python (Ruff), Frontend (ESLint), Terraform (fmt/validate), Helm (lint), K8s (kubeval) |
| **Test** | Backend (pytest with coverage), Frontend (ng test) |
| **Build** | Docker images for FastAPI, Django, Celery Worker, Frontend → pushed to ECR |
| **Security** | Trivy (container image scanning), Safety (Python dependency audit) |
| **Deploy** | Dev → Staging → Prod via ArgoCD sync to Kubernetes (EKS) |

---

## Documentation

- [Architecture](docs/architecture.md) -- System overview, component descriptions, data flow, database schema, infrastructure, and security.
- [API Reference](docs/api.md) -- Complete REST API documentation with request/response examples, WebSocket events, and error codes.
- [Deployment Guide](docs/deployment.md) -- Local development setup, Terraform provisioning, Kubernetes deployment, CI/CD, monitoring, troubleshooting, and rollback procedures.

---

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/my-feature`).
3. Write tests for new functionality.
4. Ensure all tests pass (`make test`).
5. Ensure linting passes (`make lint`).
6. Commit your changes with a descriptive message.
7. Push to your fork and open a Pull Request.

Please follow existing code conventions:

- Python: Ruff for linting and formatting, type hints on all function signatures.
- Commit messages: imperative mood, concise summary line.
- Tests: pytest with async support, use factories from `tests/factories.py`.

---

## License

This project is licensed under the [MIT License](LICENSE).
