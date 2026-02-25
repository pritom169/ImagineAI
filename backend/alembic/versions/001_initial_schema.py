"""Initial schema with all tables

Revision ID: 001
Revises:
Create Date: 2026-02-20

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("is_superuser", sa.Boolean, default=False),
        sa.Column("is_staff", sa.Boolean, default=False),
        sa.Column("last_login", sa.DateTime(timezone=True)),
        sa.Column("date_joined", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_users_email", "users", ["email"])

    # Products
    op.create_table(
        "products",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500)),
        sa.Column("description", sa.Text),
        sa.Column("category", sa.String(100)),
        sa.Column("subcategory", sa.String(100)),
        sa.Column("ai_description", sa.Text),
        sa.Column("status", sa.String(20), default="draft"),
        sa.Column("metadata", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_products_user", "products", ["user_id"])
    op.create_index("idx_products_category", "products", ["category"])
    op.create_index("idx_products_status", "products", ["status"])
    op.create_index("idx_products_created", "products", ["created_at"])

    # Product Images
    op.create_table(
        "product_images",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("product_id", UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("s3_key", sa.String(1024), nullable=False),
        sa.Column("s3_bucket", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(500)),
        sa.Column("content_type", sa.String(100)),
        sa.Column("file_size_bytes", sa.BigInteger),
        sa.Column("width", sa.Integer),
        sa.Column("height", sa.Integer),
        sa.Column("is_primary", sa.Boolean, default=False),
        sa.Column("upload_status", sa.String(20), default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_product_images_product", "product_images", ["product_id"])

    # Analysis Results
    op.create_table(
        "analysis_results",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("product_image_id", UUID(as_uuid=True), sa.ForeignKey("product_images.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("model_version", sa.String(50), nullable=False),
        sa.Column("classification_label", sa.String(100)),
        sa.Column("classification_confidence", sa.Float),
        sa.Column("classification_scores", JSONB, server_default="{}"),
        sa.Column("description_text", sa.Text),
        sa.Column("description_model", sa.String(100)),
        sa.Column("processing_time_ms", sa.Integer),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("error_message", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_analysis_image", "analysis_results", ["product_image_id"])
    op.create_index("idx_analysis_status", "analysis_results", ["status"])

    # Extracted Attributes
    op.create_table(
        "extracted_attributes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("analysis_result_id", UUID(as_uuid=True), sa.ForeignKey("analysis_results.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attribute_name", sa.String(100), nullable=False),
        sa.Column("attribute_value", sa.String(500), nullable=False),
        sa.Column("confidence", sa.Float),
        sa.Column("metadata", JSONB, server_default="{}"),
    )
    op.create_index("idx_attributes_analysis", "extracted_attributes", ["analysis_result_id"])
    op.create_index("idx_attributes_name", "extracted_attributes", ["attribute_name"])

    # Detected Defects
    op.create_table(
        "detected_defects",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("analysis_result_id", UUID(as_uuid=True), sa.ForeignKey("analysis_results.id", ondelete="CASCADE"), nullable=False),
        sa.Column("defect_type", sa.String(100), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("confidence", sa.Float),
        sa.Column("bounding_box", JSONB),
        sa.Column("description", sa.Text),
    )
    op.create_index("idx_defects_analysis", "detected_defects", ["analysis_result_id"])
    op.create_index("idx_defects_type", "detected_defects", ["defect_type"])

    # Processing Jobs
    op.create_table(
        "processing_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), default="queued"),
        sa.Column("total_images", sa.Integer, default=0),
        sa.Column("processed_images", sa.Integer, default=0),
        sa.Column("failed_images", sa.Integer, default=0),
        sa.Column("celery_task_id", sa.String(255)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("error_message", sa.Text),
        sa.Column("metadata", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_jobs_user", "processing_jobs", ["user_id"])
    op.create_index("idx_jobs_status", "processing_jobs", ["status"])
    op.create_index("idx_jobs_celery", "processing_jobs", ["celery_task_id"])

    # Job Steps
    op.create_table(
        "job_steps",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("job_id", UUID(as_uuid=True), sa.ForeignKey("processing_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_image_id", UUID(as_uuid=True), sa.ForeignKey("product_images.id")),
        sa.Column("step_name", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("duration_ms", sa.Integer),
        sa.Column("error_message", sa.Text),
        sa.Column("result_data", JSONB, server_default="{}"),
    )
    op.create_index("idx_job_steps_job", "job_steps", ["job_id"])
    op.create_index("idx_job_steps_status", "job_steps", ["status"])


def downgrade() -> None:
    op.drop_table("job_steps")
    op.drop_table("processing_jobs")
    op.drop_table("detected_defects")
    op.drop_table("extracted_attributes")
    op.drop_table("analysis_results")
    op.drop_table("product_images")
    op.drop_table("products")
    op.drop_table("users")
