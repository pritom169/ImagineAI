import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import Base, TimestampMixin, UUIDMixin


class ABExperiment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "ab_experiments"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)

    variants = relationship("ABVariant", back_populates="experiment", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ABExperiment {self.name} ({self.model_type})>"


class ABVariant(UUIDMixin, Base):
    __tablename__ = "ab_variants"
    __table_args__ = (
        UniqueConstraint("experiment_id", "model_version", name="uq_experiment_version"),
    )

    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ab_experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    weight: Mapped[int] = mapped_column(Integer, default=0)
    is_control: Mapped[bool] = mapped_column(Boolean, default=False)

    experiment = relationship("ABExperiment", back_populates="variants")

    def __repr__(self) -> str:
        return f"<ABVariant {self.model_version} weight={self.weight}>"


class UserCohortAssignment(UUIDMixin, Base):
    __tablename__ = "user_cohort_assignments"
    __table_args__ = (
        UniqueConstraint("user_id", "experiment_id", name="uq_user_experiment"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ab_experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    variant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ab_variants.id", ondelete="CASCADE"),
        nullable=False,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<UserCohortAssignment user={self.user_id} variant={self.variant_id}>"
