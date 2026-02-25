"""Add multi-tenancy, rate limiting, A/B testing, webhooks, and exports

Revision ID: 002
Revises: 001
Create Date: 2026-02-22

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---- Phase 1: Multi-tenancy ----

    # Organizations
    op.create_table(
        "organizations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("plan", sa.String(50), server_default="'free'"),
        sa.Column("settings", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_organizations_slug", "organizations", ["slug"])

    # Organization Members
    op.create_table(
        "organization_members",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), server_default="'member'"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_org_user"),
    )
    op.create_index("idx_org_members_org", "organization_members", ["organization_id"])
    op.create_index("idx_org_members_user", "organization_members", ["user_id"])

    # Add organization_id to products (nullable initially for backfill)
    op.add_column(
        "products",
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True),
    )
    op.create_index("idx_products_organization", "products", ["organization_id"])

    # Backfill: create a default org for each user and assign products
    op.execute("""
        INSERT INTO organizations (id, name, slug, is_active, plan)
        SELECT
            gen_random_uuid(),
            COALESCE(u.full_name, u.email) || '''s Organization',
            REPLACE(LOWER(u.email), '@', '-at-') || '-org',
            true,
            'free'
        FROM users u
        WHERE NOT EXISTS (
            SELECT 1 FROM organization_members om WHERE om.user_id = u.id
        )
    """)

    op.execute("""
        INSERT INTO organization_members (id, organization_id, user_id, role)
        SELECT gen_random_uuid(), o.id, u.id, 'owner'
        FROM users u
        JOIN organizations o ON o.slug = REPLACE(LOWER(u.email), '@', '-at-') || '-org'
        WHERE NOT EXISTS (
            SELECT 1 FROM organization_members om WHERE om.user_id = u.id
        )
    """)

    op.execute("""
        UPDATE products p
        SET organization_id = (
            SELECT om.organization_id
            FROM organization_members om
            WHERE om.user_id = p.user_id
            LIMIT 1
        )
        WHERE p.organization_id IS NULL
    """)

    # Make organization_id NOT NULL after backfill
    op.alter_column("products", "organization_id", nullable=False)

    # ---- Phase 2: Rate Limiting ----

    op.create_table(
        "rate_limit_configs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("endpoint_pattern", sa.String(200), server_default="'*'"),
        sa.Column("requests_per_minute", sa.Integer, server_default="60"),
        sa.Column("requests_per_hour", sa.Integer, server_default="1000"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("organization_id", "endpoint_pattern", name="uq_org_endpoint_limit"),
    )
    op.create_index("idx_rate_limit_org", "rate_limit_configs", ["organization_id"])
    op.create_index("idx_rate_limit_user", "rate_limit_configs", ["user_id"])

    # ---- Phase 3: A/B Testing ----

    op.create_table(
        "ab_experiments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("model_type", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("start_date", sa.DateTime(timezone=True)),
        sa.Column("end_date", sa.DateTime(timezone=True)),
        sa.Column("metadata", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "ab_variants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("experiment_id", UUID(as_uuid=True), sa.ForeignKey("ab_experiments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model_version", sa.String(50), nullable=False),
        sa.Column("weight", sa.Integer, server_default="0"),
        sa.Column("is_control", sa.Boolean, server_default="false"),
        sa.UniqueConstraint("experiment_id", "model_version", name="uq_experiment_version"),
    )
    op.create_index("idx_ab_variants_experiment", "ab_variants", ["experiment_id"])

    op.create_table(
        "user_cohort_assignments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("experiment_id", UUID(as_uuid=True), sa.ForeignKey("ab_experiments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("variant_id", UUID(as_uuid=True), sa.ForeignKey("ab_variants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "experiment_id", name="uq_user_experiment"),
    )
    op.create_index("idx_cohort_user", "user_cohort_assignments", ["user_id"])
    op.create_index("idx_cohort_experiment", "user_cohort_assignments", ["experiment_id"])

    # Add experiment tracking columns to analysis_results
    op.add_column(
        "analysis_results",
        sa.Column("experiment_id", UUID(as_uuid=True), sa.ForeignKey("ab_experiments.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column(
        "analysis_results",
        sa.Column("variant_id", UUID(as_uuid=True), sa.ForeignKey("ab_variants.id", ondelete="SET NULL"), nullable=True),
    )

    # Seed default classifier experiment (90/10 split)
    op.execute("""
        INSERT INTO ab_experiments (id, name, model_type, is_active, start_date)
        VALUES (
            gen_random_uuid(),
            'classifier-v1-vs-v2',
            'classifier',
            true,
            NOW()
        )
    """)
    op.execute("""
        INSERT INTO ab_variants (id, experiment_id, model_version, weight, is_control)
        SELECT gen_random_uuid(), e.id, 'v1', 90, true
        FROM ab_experiments e WHERE e.name = 'classifier-v1-vs-v2'
    """)
    op.execute("""
        INSERT INTO ab_variants (id, experiment_id, model_version, weight, is_control)
        SELECT gen_random_uuid(), e.id, 'v2', 10, false
        FROM ab_experiments e WHERE e.name = 'classifier-v1-vs-v2'
    """)

    # ---- Phase 4: Webhooks ----

    op.create_table(
        "webhook_endpoints",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("secret", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("events", JSONB, server_default="'[]'::jsonb"),
        sa.Column("description", sa.String(500)),
        sa.Column("failure_count", sa.Integer, server_default="0"),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("organization_id", "url", name="uq_org_webhook_url"),
    )
    op.create_index("idx_webhooks_org", "webhook_endpoints", ["organization_id"])

    op.create_table(
        "webhook_deliveries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("webhook_id", UUID(as_uuid=True), sa.ForeignKey("webhook_endpoints.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("response_status", sa.Integer),
        sa.Column("response_body", sa.Text),
        sa.Column("delivered_at", sa.DateTime(timezone=True)),
        sa.Column("success", sa.Boolean, server_default="false"),
        sa.Column("attempt", sa.Integer, server_default="1"),
        sa.Column("error_message", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_webhook_deliveries_webhook", "webhook_deliveries", ["webhook_id"])

    # ---- Phase 5: Exports ----

    op.create_table(
        "export_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("export_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), server_default="'pending'"),
        sa.Column("filters", JSONB, server_default="{}"),
        sa.Column("s3_key", sa.String(1024)),
        sa.Column("s3_bucket", sa.String(255)),
        sa.Column("file_size_bytes", sa.BigInteger),
        sa.Column("row_count", sa.Integer),
        sa.Column("error_message", sa.Text),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_export_jobs_org", "export_jobs", ["organization_id"])


def downgrade() -> None:
    # Phase 5
    op.drop_table("export_jobs")

    # Phase 4
    op.drop_table("webhook_deliveries")
    op.drop_table("webhook_endpoints")

    # Phase 3
    op.drop_column("analysis_results", "variant_id")
    op.drop_column("analysis_results", "experiment_id")
    op.drop_table("user_cohort_assignments")
    op.drop_table("ab_variants")
    op.drop_table("ab_experiments")

    # Phase 2
    op.drop_table("rate_limit_configs")

    # Phase 1
    op.drop_column("products", "organization_id")
    op.drop_table("organization_members")
    op.drop_table("organizations")
