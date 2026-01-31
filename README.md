# ImagineAI

**AI-Powered E-Commerce Image Intelligence Platform**

ImagineAI is a full-stack platform that automates product image analysis for
e-commerce. Upload product photos and the system automatically classifies them,
extracts attributes (color, material, condition), detects defects, and generates
natural-language product descriptions using an ML pipeline backed by AWS Bedrock.

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

---

## License

This project is licensed under the [MIT License](LICENSE).
