# ImagineAI -- Architecture

## System Overview

```
                            +------------------+
                            |   Angular SPA    |
                            |  (Frontend :4200)|
                            +--------+---------+
                                     |
                              HTTPS / WSS
                                     |
                    +----------------+----------------+
                    |                                  |
           +-------v--------+              +----------v---------+
           | FastAPI (REST)  |              |   Django Admin      |
           |  API  :8000     |              |   Panel  :8001      |
           +--+---------+---+              +----------+----------+
              |         |                              |
              |    +----v-----------+                   |
              |    | WebSocket /ws  |                   |
              |    +----+-----------+                   |
              |         |                              |
   +----------v---+  +--v---------+           +--------v---------+
   | PostgreSQL   |  |   Redis    |           |   PostgreSQL     |
   | (Primary DB) |  | (Cache /   |           |  (Shared DB)     |
   |    :5432     |  |  Pub/Sub)  |           +------------------+
   +--------------+  |   :6379    |
                     +--+---------+
                        |
              +---------v----------+
              |    RabbitMQ        |
              | (Message Broker)   |
              |    :5672           |
              +----+--------+------+
                   |        |
          +--------v--+ +---v-----------+
          |  Celery   | |  Celery Beat  |
          |  Worker   | |  (Scheduler)  |
          +-----+-----+ +---------------+
                |
       +--------v---------+
       |   ML Pipeline     |
       |  - Classification |
       |  - Feature Extr.  |
       |  - Defect Det.    |
       |  - Bedrock LLM    |
       +--------+----------+
                |
         +------v------+
         |  AWS S3      |
         | (Images)     |
         +-------------+
```

## Component Descriptions

### FastAPI (REST API Server)

The primary API server handling all client requests. Built with FastAPI for high
performance async I/O and automatic OpenAPI documentation.

- **Location**: `backend/fastapi_app/`
- **Port**: 8000
- **Responsibilities**:
  - JWT-based authentication (register, login, refresh)
  - Product CRUD operations
  - Presigned URL generation for S3 uploads
  - Direct file upload endpoint
  - Analysis result retrieval
  - Batch processing job creation
  - Dashboard statistics
  - WebSocket connections for real-time processing updates
- **Key middleware**: CORS, Request ID injection

### Django Admin Panel

An administrative interface for internal teams to manage data, monitor system
health, and perform manual operations.

- **Location**: `backend/django_app/`
- **Port**: 8001
- **Responsibilities**:
  - User management (view / deactivate accounts)
  - Product and image browsing
  - Analysis result inspection
  - Processing job monitoring
- **Shares** the same PostgreSQL database as FastAPI via Django ORM proxy models

### Celery Workers

Distributed task workers that process images through the ML pipeline. They
consume jobs from RabbitMQ and store results back in PostgreSQL.

- **Location**: `backend/workers/`
- **Tasks**:
  - `image_processing.process_image` -- Single image pipeline orchestrator
  - `batch_processing.process_batch` -- Batch job orchestrator
  - `classification.classify_image` -- Product category classification
  - `feature_extraction.extract_features` -- Attribute extraction (color, material, etc.)
  - `defect_detection.detect_defects` -- Defect identification and localization
  - `description_gen.generate_description` -- AI-generated product descriptions
  - `notifications.send_processing_update` -- Redis pub/sub push to WebSocket clients

### Celery Beat (Scheduler)

Periodic task scheduler for maintenance and recurring operations.

- Runs alongside workers using the same codebase
- Triggers scheduled clean-up, retry of failed jobs, and health pings

### ML Pipeline

Machine learning models for image analysis, hosted in-process within Celery
workers and augmented by AWS Bedrock for LLM capabilities.

- **Location**: `backend/ml/`
- **Models**:
  - `classifier.py` -- Product classification (ResNet / EfficientNet based)
  - `feature_extractor.py` -- Attribute extraction (color, material, condition)
  - `defect_detector.py` -- Defect detection with bounding boxes
  - `model_registry.py` -- Version management and A/B test routing
- **Services**:
  - `preprocessing.py` -- Image normalization, resizing
  - `inference.py` -- Unified inference orchestrator
  - `bedrock_client.py` -- AWS Bedrock API client for Claude-based descriptions
  - `description_generator.py` -- Natural language product description generation
- **Configuration**: Thresholds and model paths are in `ml/config.py` and `shared/config.py`

### Frontend (Angular SPA)

Single-page application providing the user interface.

- **Location**: `frontend/`
- **Port**: 4200
- **Tech**: Angular 17+, Angular Material, RxJS
- **Features**: Product management, image upload, analysis dashboard, real-time
  processing status via WebSocket

---

## Data Flow

### Image Upload and Processing Pipeline

```
User uploads image
        |
        v
+-------------------+     presigned URL     +----------+
|  Angular Frontend  | ------------------->  |  FastAPI  |
+-------------------+                       +-----+----+
        |                                         |
        |  PUT (binary)                    generate S3 key
        v                                         |
+-------------------+                       +-----v----+
|     AWS S3        | <--- direct upload -- | Response  |
+-------------------+                       +----------+
        |
        |  confirm upload
        v
+-------------------+     enqueue job       +------------+
|     FastAPI       | --------------------> |  RabbitMQ   |
+-------------------+                       +------+-----+
                                                   |
                                            +------v------+
                                            | Celery Worker|
                                            +------+------+
                                                   |
                            +----------------------+----------------------+
                            |                      |                      |
                     +------v------+       +-------v------+      +-------v-------+
                     | Preprocess  |       |   Classify   |      | Extract Attrs |
                     | (resize,    |       | (category    |      | (color,       |
                     |  normalize) |       |  prediction) |      |  material)    |
                     +------+------+       +-------+------+      +-------+-------+
                            |                      |                      |
                            +----------+-----------+----------------------+
                                       |
                                +------v--------+
                                | Detect Defects|
                                | (bounding box |
                                |  annotations) |
                                +------+--------+
                                       |
                                +------v-----------+
                                | Generate Desc.   |
                                | (Bedrock / Claude)|
                                +------+-----------+
                                       |
                          +------------v-----------+
                          |  Write results to DB   |
                          |  (analysis_results,    |
                          |   extracted_attributes,|
                          |   detected_defects)    |
                          +------------+-----------+
                                       |
                              +--------v--------+
                              | Publish update  |
                              | via Redis PubSub|
                              +--------+--------+
                                       |
                              +--------v--------+
                              | WebSocket push  |
                              | to Frontend     |
                              +----------------+
```

### Request Authentication Flow

1. Client sends `POST /api/v1/auth/login` with email + password.
2. FastAPI verifies credentials against bcrypt hash in PostgreSQL.
3. On success, returns a JWT `access_token` (30 min) and `refresh_token` (7 days).
4. Client includes `Authorization: Bearer <access_token>` on subsequent requests.
5. WebSocket connections pass the token as a query parameter (`?token=...`).
6. Tokens are refreshed via `POST /api/v1/auth/refresh`.

---

## Database Schema Overview

```
users
  |-- id (UUID, PK)
  |-- email (unique, indexed)
  |-- hashed_password
  |-- full_name
  |-- is_active, is_superuser, is_staff
  |-- last_login, date_joined
  |-- created_at, updated_at
  |
  +--< products
  |      |-- id (UUID, PK)
  |      |-- user_id (FK -> users.id)
  |      |-- title, description, category, subcategory
  |      |-- ai_description, status, metadata (JSONB)
  |      |-- created_at, updated_at
  |      |
  |      +--< product_images
  |             |-- id (UUID, PK)
  |             |-- product_id (FK -> products.id)
  |             |-- s3_key, s3_bucket, original_filename
  |             |-- content_type, file_size_bytes, width, height
  |             |-- is_primary, upload_status
  |             |-- created_at
  |             |
  |             +--< analysis_results (1:1)
  |                    |-- id (UUID, PK)
  |                    |-- product_image_id (FK, unique)
  |                    |-- model_version, status
  |                    |-- classification_label, classification_confidence
  |                    |-- classification_scores (JSONB)
  |                    |-- description_text, description_model
  |                    |-- processing_time_ms, error_message
  |                    |-- created_at, updated_at
  |                    |
  |                    +--< extracted_attributes
  |                    |      |-- attribute_name, attribute_value
  |                    |      |-- confidence, metadata (JSONB)
  |                    |
  |                    +--< detected_defects
  |                           |-- defect_type, severity
  |                           |-- confidence, bounding_box (JSONB)
  |                           |-- description
  |
  +--< processing_jobs
         |-- id (UUID, PK)
         |-- user_id (FK -> users.id)
         |-- job_type (single / batch), status
         |-- total_images, processed_images, failed_images
         |-- celery_task_id, started_at, completed_at
         |-- error_message, metadata (JSONB)
         |-- created_at, updated_at
         |
         +--< job_steps
                |-- step_name, status
                |-- product_image_id (FK)
                |-- started_at, completed_at, duration_ms
                |-- error_message, result_data (JSONB)
```

All primary keys are UUIDs (v4). Timestamps use `timezone=True`. Soft cascading
deletes are configured on all foreign key relationships.

---

## Infrastructure Overview

### AWS Services

| Service | Purpose |
|---|---|
| **EKS** | Kubernetes cluster hosting all application workloads |
| **RDS (PostgreSQL 16)** | Managed relational database |
| **ElastiCache (Redis 7)** | Caching, session store, and pub/sub for WebSocket |
| **Amazon MQ (RabbitMQ)** | Managed message broker for Celery task queue |
| **S3** | Product image storage |
| **ECR** | Container image registry |
| **Bedrock** | Managed LLM inference (Claude 3.5 Sonnet) |
| **VPC** | Network isolation with public/private subnets |
| **IAM / IRSA** | Pod-level AWS permissions via service account annotations |

### Terraform Modules

Infrastructure is provisioned via Terraform with environment-specific variable
files (`dev`, `staging`, `prod`).

```
infrastructure/terraform/
  modules/
    vpc/           -- VPC, subnets, NAT gateway, security groups
    eks/           -- EKS cluster, node groups, OIDC provider
    rds/           -- RDS PostgreSQL instance, parameter groups
    elasticache/   -- Redis cluster, subnet groups
    mq/            -- Amazon MQ broker
    s3/            -- Image bucket, lifecycle policies, CORS
    ecr/           -- Container image repositories
    iam/           -- IRSA roles, policies for pod-level access
```

### Kubernetes Architecture

```
infrastructure/k8s/
  base/
    namespace.yaml
    configmap.yaml
    fastapi/          -- Deployment, Service, HPA
    celery-worker/    -- Deployment
    celery-beat/      -- Deployment
    django-admin/     -- Deployment, Service
    frontend/         -- Deployment, Service
  overlays/
    dev/              -- Development overrides
    staging/          -- Staging overrides
    prod/             -- Production overrides (replicas, resources, etc.)
```

Helm charts are available in `infrastructure/helm/imagineai/` for templated
deployments. ArgoCD application manifests live in `infrastructure/argocd/`.

---

## Security

### Authentication and Authorization

- **JWT tokens** with HS256 signing. Access tokens expire in 30 minutes; refresh
  tokens in 7 days.
- **Password hashing** via bcrypt (passlib).
- All product and job queries are scoped to the authenticated user's ID,
  preventing cross-tenant data access.

### AWS Security

- **IRSA (IAM Roles for Service Accounts)**: Pods assume fine-grained IAM roles
  instead of using static AWS credentials.
- **Network policies**: Celery workers and databases reside in private subnets
  with no direct internet access.
- **Encryption at rest**: RDS and S3 use AES-256 encryption. ElastiCache
  uses at-rest and in-transit encryption.
- **Encryption in transit**: All inter-service communication uses TLS. The
  ALB terminates external HTTPS.

### Application Security

- CORS restricted to the frontend origin.
- Request ID middleware for end-to-end tracing.
- Input validation via Pydantic schemas on every endpoint.
- File upload validation (content type allowlist, 50 MB size limit).
- Presigned S3 URLs with short expiration for secure client-side uploads.
