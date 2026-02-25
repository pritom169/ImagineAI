import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import Base, TimestampMixin, UUIDMixin


class ProcessingJob(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "processing_jobs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    total_images: Mapped[int] = mapped_column(Integer, default=0)
    processed_images: Mapped[int] = mapped_column(Integer, default=0)
    failed_images: Mapped[int] = mapped_column(Integer, default=0)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)

    # Relationships
    user = relationship("User", back_populates="processing_jobs")
    steps = relationship("JobStep", back_populates="job", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ProcessingJob {self.id} ({self.status})>"


class JobStep(UUIDMixin, Base):
    __tablename__ = "job_steps"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("processing_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_image_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_images.id"),
    )
    step_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    result_data: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Relationships
    job = relationship("ProcessingJob", back_populates="steps")

    def __repr__(self) -> str:
        return f"<JobStep {self.step_name} ({self.status})>"
