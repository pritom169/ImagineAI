# ImagineAI -- Deployment Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Infrastructure Provisioning (Terraform)](#infrastructure-provisioning-terraform)
4. [Kubernetes Deployment (Helm)](#kubernetes-deployment-helm)
5. [CI/CD Pipeline](#cicd-pipeline)
6. [Environment Configuration](#environment-configuration)
7. [Monitoring and Alerting](#monitoring-and-alerting)
8. [Troubleshooting](#troubleshooting)
9. [Rollback Procedures](#rollback-procedures)

---

## Prerequisites

Ensure the following tools are installed before proceeding:

| Tool | Minimum Version | Purpose |
|---|---|---|
| Docker | 24.0+ | Container runtime |
| Docker Compose | 2.20+ | Local orchestration |
| AWS CLI | 2.x | AWS resource management |
| Terraform | 1.5+ | Infrastructure as code |
| kubectl | 1.28+ | Kubernetes cluster management |
| Helm | 3.12+ | Kubernetes package manager |
| Node.js | 18 LTS+ | Frontend build toolchain |
| Python | 3.12+ | Backend development |

Optional but recommended:

| Tool | Purpose |
|---|---|
| `k9s` | Terminal-based Kubernetes UI |
| `jq` | JSON processing from the command line |
| `aws-vault` | Secure AWS credential management |
| ArgoCD CLI | GitOps deployment management |

---

## Local Development Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-org/ImagineAI.git
cd ImagineAI
```

### 2. Create a `.env` file

Copy the example and adjust values as needed. The defaults work with the
Docker Compose stack out of the box.

```bash
cp .env.example .env
```

Key variables (defaults are set in `shared/config.py`):

```dotenv
APP_ENV=development
DEBUG=true
SECRET_KEY=change-me
JWT_SECRET_KEY=change-me-jwt
POSTGRES_HOST=postgres
POSTGRES_DB=imagineai
POSTGRES_USER=imagineai
POSTGRES_PASSWORD=imagineai_dev_password
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
S3_ENDPOINT_URL=http://localstack:4566
```

### 3. Start all services

```bash
docker compose up -d
```

This starts:

| Service | Port | Description |
|---|---|---|
| `postgres` | 5432 | PostgreSQL 16 |
| `redis` | 6379 | Redis 7 |
| `rabbitmq` | 5672 / 15672 | RabbitMQ (AMQP + Management UI) |
| `localstack` | 4566 | LocalStack (S3 emulation) |
| `fastapi` | 8000 | FastAPI REST API |
| `django-admin` | 8001 | Django Admin Panel |
| `celery-worker` | -- | Celery task worker |
| `celery-beat` | -- | Celery periodic scheduler |
| `frontend` | 4200 | Angular development server |

### 4. Run database migrations

```bash
make migrate
```

### 5. Seed demo data

```bash
make seed
```

This creates demo users, products, images, and analysis results. See
`scripts/seed_data.py` for details and credentials.

### 6. Verify the stack

```bash
# Health check
curl http://localhost:8000/health

# Readiness check (database + Redis)
curl http://localhost:8000/ready

# API docs
open http://localhost:8000/docs

# Django Admin
open http://localhost:8001/admin

# RabbitMQ Management
open http://localhost:15672   # guest / guest

# Frontend
open http://localhost:4200
```

### Common development commands

```bash
make help              # Show all available commands
make logs              # Tail all service logs
make logs-api          # Tail FastAPI logs only
make logs-worker       # Tail Celery worker logs only
make test              # Run backend tests
make test-cov          # Run tests with coverage report
make lint              # Run ruff linter
make lint-fix          # Auto-fix linting issues
make shell-api         # Shell into the FastAPI container
make shell-worker      # Shell into the Celery worker container
make down              # Stop all services
make clean             # Remove containers, volumes, and images
```

---

## Infrastructure Provisioning (Terraform)

The production infrastructure runs on AWS and is defined in
`infrastructure/terraform/`.

### Directory structure

```
infrastructure/terraform/
  main.tf              -- Root module composing all sub-modules
  variables.tf         -- Input variables
  outputs.tf           -- Output values (endpoints, ARNs)
  providers.tf         -- AWS provider configuration
  modules/
    vpc/               -- VPC, subnets, NAT gateway, security groups
    eks/               -- EKS cluster, managed node groups, OIDC
    rds/               -- RDS PostgreSQL 16, parameter groups
    elasticache/       -- Redis 7 cluster, subnet groups
    mq/                -- Amazon MQ (RabbitMQ) broker
    s3/                -- Image bucket, lifecycle policies, CORS
    ecr/               -- Container image repositories
    iam/               -- IRSA roles and policies
  environments/
    dev/               -- Development tfvars
    staging/           -- Staging tfvars
    prod/              -- Production tfvars
```

### Step-by-step provisioning

#### 1. Configure AWS credentials

```bash
export AWS_PROFILE=imagineai-prod
aws sts get-caller-identity    # verify access
```

#### 2. Initialize Terraform

```bash
cd infrastructure/terraform
terraform init
```

#### 3. Select the target environment

```bash
terraform workspace select prod
# or: terraform workspace new prod
```

#### 4. Review the plan

```bash
terraform plan -var-file=environments/prod/terraform.tfvars
```

#### 5. Apply

```bash
terraform apply -var-file=environments/prod/terraform.tfvars
```

This provisions, in order:

1. **VPC** with public and private subnets across 3 AZs
2. **EKS cluster** with managed node groups (GPU nodes for ML inference)
3. **RDS PostgreSQL** in private subnets with Multi-AZ
4. **ElastiCache Redis** cluster in private subnets
5. **Amazon MQ** broker in private subnets
6. **S3 bucket** for product images with encryption and lifecycle rules
7. **ECR repositories** for each service container image
8. **IAM IRSA roles** for pod-level AWS access

#### 6. Update kubeconfig

```bash
aws eks update-kubeconfig --name imagineai-prod --region us-east-1
kubectl get nodes    # verify connectivity
```

#### 7. Record Terraform outputs

```bash
terraform output -json > /tmp/tf-outputs.json
```

Key outputs include: RDS endpoint, Redis endpoint, MQ endpoint, S3 bucket
name, ECR repository URIs, and EKS cluster endpoint.

---

## Kubernetes Deployment (Helm)

### Build and push container images

```bash
# Authenticate to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# Build and push each service
for svc in fastapi django-admin celery-worker frontend; do
  docker build -t imagineai-${svc}:latest -f backend/${svc}/Dockerfile .
  docker tag imagineai-${svc}:latest <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/imagineai-${svc}:latest
  docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/imagineai-${svc}:latest
done
```

### Deploy with Helm

```bash
cd infrastructure/helm

helm upgrade --install imagineai ./imagineai \
  --namespace imagineai \
  --create-namespace \
  --values ./imagineai/values-prod.yaml \
  --set image.tag=$(git rev-parse --short HEAD) \
  --set database.host=$(terraform output -raw rds_endpoint) \
  --set redis.host=$(terraform output -raw redis_endpoint) \
  --set rabbitmq.host=$(terraform output -raw mq_endpoint) \
  --set s3.bucket=$(terraform output -raw s3_bucket_name)
```

### Verify the deployment

```bash
kubectl -n imagineai get pods
kubectl -n imagineai get svc
kubectl -n imagineai logs -f deployment/fastapi
```

### Run migrations in the cluster

```bash
kubectl -n imagineai exec -it deployment/fastapi -- alembic upgrade head
```

### Seed data (optional for staging)

```bash
kubectl -n imagineai exec -it deployment/fastapi -- python scripts/seed_data.py
```

---

## CI/CD Pipeline

The CI/CD pipeline is managed via GitHub Actions (or your preferred CI system)
and ArgoCD for GitOps-based continuous delivery.

### Pipeline stages

```
Push to main
     |
     v
[Lint & Test]  -- ruff check, pytest, Angular tests
     |
     v
[Build Images] -- Docker build for each service
     |
     v
[Push to ECR]  -- Tag with git SHA, push to ECR
     |
     v
[Update Helm]  -- Update image tags in values file
     |
     v
[ArgoCD Sync]  -- ArgoCD detects drift and syncs to cluster
     |
     v
[Smoke Tests]  -- Hit /health and /ready endpoints
     |
     v
[Notify]       -- Slack / email notification
```

### Branch strategy

| Branch | Deploys to | Trigger |
|---|---|---|
| `feature/*` | -- | PR checks only (lint, test) |
| `develop` | `dev` | Auto-deploy on merge |
| `release/*` | `staging` | Auto-deploy on merge |
| `main` | `prod` | Manual approval required |

### ArgoCD application

ArgoCD manifests are in `infrastructure/argocd/`. ArgoCD watches the Helm
chart values in the repository and reconciles the cluster state automatically.

---

## Environment Configuration

### Required environment variables

| Variable | Description | Example |
|---|---|---|
| `APP_ENV` | Environment name | `production` |
| `DEBUG` | Enable debug mode | `false` |
| `SECRET_KEY` | Application secret | (generate a random 64-char string) |
| `JWT_SECRET_KEY` | JWT signing secret | (generate a random 64-char string) |
| `POSTGRES_HOST` | Database hostname | `imagineai-prod.abc123.us-east-1.rds.amazonaws.com` |
| `POSTGRES_PORT` | Database port | `5432` |
| `POSTGRES_DB` | Database name | `imagineai` |
| `POSTGRES_USER` | Database user | `imagineai` |
| `POSTGRES_PASSWORD` | Database password | (from Secrets Manager) |
| `REDIS_URL` | Redis connection URL | `redis://redis.abc123.cache.amazonaws.com:6379/0` |
| `CELERY_BROKER_URL` | RabbitMQ AMQP URL | `amqps://user:pass@mq.abc123.mq.us-east-1.amazonaws.com:5671` |
| `CELERY_RESULT_BACKEND` | Celery result store | `redis://redis.abc123.cache.amazonaws.com:6379/1` |
| `AWS_REGION` | AWS region | `us-east-1` |
| `S3_BUCKET_NAME` | Image bucket name | `imagineai-prod-images` |
| `S3_ENDPOINT_URL` | S3 endpoint (leave empty for real AWS) | `` |
| `BEDROCK_MODEL_ID` | Bedrock model identifier | `anthropic.claude-3-5-sonnet-20241022-v2:0` |
| `BEDROCK_REGION` | Bedrock region | `us-east-1` |

### Kubernetes secrets

Sensitive values should be stored in Kubernetes secrets (or an external secret
manager like AWS Secrets Manager + External Secrets Operator):

```bash
kubectl -n imagineai create secret generic imagineai-secrets \
  --from-literal=SECRET_KEY="$(openssl rand -hex 32)" \
  --from-literal=JWT_SECRET_KEY="$(openssl rand -hex 32)" \
  --from-literal=POSTGRES_PASSWORD="<password>"
```

---

## Monitoring and Alerting

### Stack

| Component | Tool | Purpose |
|---|---|---|
| Metrics | Prometheus | Scrape application and infrastructure metrics |
| Dashboards | Grafana | Visualize metrics and create dashboards |
| Alerting | Alertmanager | Route alerts to Slack, PagerDuty, email |
| Logging | CloudWatch / Loki | Centralized log aggregation |
| Tracing | X-Ray / Jaeger | Distributed request tracing |

### Grafana dashboards

Pre-built dashboards are in `monitoring/grafana/`:

- **API Overview**: Request rate, latency percentiles, error rate
- **Celery Workers**: Task throughput, queue depth, failure rate
- **ML Pipeline**: Inference latency, model confidence distributions
- **Database**: Connection pool, query latency, replication lag
- **Infrastructure**: Pod CPU/memory, node utilization

### Alert rules

Alert rules are defined in `monitoring/alerts/`:

| Alert | Condition | Severity |
|---|---|---|
| High API error rate | > 5% 5xx responses over 5 min | Critical |
| Celery queue backlog | > 100 pending tasks for 10 min | Warning |
| Database connection exhaustion | Pool > 80% utilized | Warning |
| ML inference latency | p99 > 5s over 5 min | Warning |
| Pod crash loop | > 3 restarts in 10 min | Critical |
| Disk usage | > 85% on any PV | Warning |

### Health check endpoints

- `GET /health` -- Liveness probe (always returns 200 if the process is up)
- `GET /ready` -- Readiness probe (checks database and Redis connectivity)

These are configured as Kubernetes probes on the FastAPI deployment.

---

## Troubleshooting

### Container will not start

```bash
# Check pod events
kubectl -n imagineai describe pod <pod-name>

# Check logs
kubectl -n imagineai logs <pod-name> --previous

# Common causes:
# - Missing environment variable  -> check configmap and secrets
# - Database unreachable          -> check security groups and RDS status
# - Image pull error              -> check ECR credentials and image tag
```

### Database migration fails

```bash
# Check current migration state
kubectl -n imagineai exec -it deployment/fastapi -- alembic current

# View migration history
kubectl -n imagineai exec -it deployment/fastapi -- alembic history

# Downgrade one step if needed
kubectl -n imagineai exec -it deployment/fastapi -- alembic downgrade -1
```

### Celery tasks stuck in queue

```bash
# Check RabbitMQ management UI
open http://localhost:15672

# Inspect Celery worker status
kubectl -n imagineai exec -it deployment/celery-worker -- celery -A workers.celery_app inspect active

# Purge a specific queue (use with caution)
kubectl -n imagineai exec -it deployment/celery-worker -- celery -A workers.celery_app purge
```

### S3 upload errors

```bash
# Verify IRSA annotation on service account
kubectl -n imagineai get sa fastapi -o yaml

# Test S3 access from inside the pod
kubectl -n imagineai exec -it deployment/fastapi -- \
  python -c "import boto3; s3 = boto3.client('s3'); print(s3.list_buckets())"
```

### WebSocket connection refused

```bash
# Verify Redis is reachable
kubectl -n imagineai exec -it deployment/fastapi -- \
  python -c "import redis; r = redis.from_url('redis://redis:6379/0'); print(r.ping())"

# Check that the ALB/Ingress supports WebSocket upgrade
kubectl -n imagineai get ingress -o yaml
```

---

## Rollback Procedures

### Helm rollback

```bash
# List release history
helm -n imagineai history imagineai

# Rollback to previous revision
helm -n imagineai rollback imagineai <revision-number>

# Verify pods are running the previous image
kubectl -n imagineai get pods -o jsonpath='{.items[*].spec.containers[*].image}'
```

### Database migration rollback

```bash
# Downgrade one migration
kubectl -n imagineai exec -it deployment/fastapi -- alembic downgrade -1

# Downgrade to a specific revision
kubectl -n imagineai exec -it deployment/fastapi -- alembic downgrade <revision>
```

### ArgoCD rollback

```bash
# List application history
argocd app history imagineai

# Rollback to a specific revision
argocd app rollback imagineai <history-id>
```

### Emergency procedures

1. **Immediate traffic halt**: Scale FastAPI deployment to 0 replicas.
   ```bash
   kubectl -n imagineai scale deployment/fastapi --replicas=0
   ```
2. **Stop all processing**: Scale Celery worker to 0.
   ```bash
   kubectl -n imagineai scale deployment/celery-worker --replicas=0
   ```
3. **Investigate**: Check logs, metrics, and alerts.
4. **Fix forward or rollback**: Apply the fix or roll back Helm + migrations.
5. **Restore traffic**: Scale deployments back up.
   ```bash
   kubectl -n imagineai scale deployment/fastapi --replicas=3
   kubectl -n imagineai scale deployment/celery-worker --replicas=2
   ```
