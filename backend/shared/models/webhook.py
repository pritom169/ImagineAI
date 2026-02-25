import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import Base, TimestampMixin, UUIDMixin


class WebhookEndpoint(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "webhook_endpoints"
    __table_args__ = (
        UniqueConstraint("organization_id", "url", name="uq_org_webhook_url"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    secret: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    events: Mapped[list] = mapped_column(JSONB, default=list)
    description: Mapped[str | None] = mapped_column(String(500))
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    deliveries = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<WebhookEndpoint {self.url}>"


class WebhookDelivery(UUIDMixin, Base):
    __tablename__ = "webhook_deliveries"

    webhook_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("webhook_endpoints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    response_status: Mapped[int | None] = mapped_column(Integer)
    response_body: Mapped[str | None] = mapped_column(Text)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    attempt: Mapped[int] = mapped_column(Integer, default=1)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    webhook = relationship("WebhookEndpoint", back_populates="deliveries")

    def __repr__(self) -> str:
        return f"<WebhookDelivery {self.event_type} success={self.success}>"
