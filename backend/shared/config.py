from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    app_name: str = "ImagineAI"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-me"

    # Database
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "imagineai"
    postgres_user: str = "imagineai"
    postgres_password: str = "imagineai_dev_password"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_url: str = "redis://localhost:6379/0"

    # RabbitMQ
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672//"

    # AWS / S3
    aws_region: str = "us-east-1"
    aws_access_key_id: str = "test"
    aws_secret_access_key: str = "test"
    s3_bucket_name: str = "imagineai-images"
    s3_endpoint_url: str | None = "http://localstack:4566"

    # AWS Bedrock
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    bedrock_region: str = "us-east-1"

    # JWT
    jwt_secret_key: str = "change-me-jwt"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # FastAPI
    fastapi_host: str = "0.0.0.0"
    fastapi_port: int = 8000

    # Celery
    celery_broker_url: str = "amqp://guest:guest@localhost:5672//"
    celery_result_backend: str = "redis://localhost:6379/1"

    # ML
    ml_model_dir: str = "./backend/ml/weights"
    ml_classification_threshold: float = 0.5
    ml_defect_threshold: float = 0.3
    ml_ab_test_percentage: int = 10

    # Rate Limiting
    rate_limit_default_per_minute: int = 60
    rate_limit_default_per_hour: int = 1000

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
