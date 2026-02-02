import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import Base, TimestampMixin, UUIDMixin


class RateLimitConfig(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "rate_limit_configs"
    __table_args__ = (
        UniqueConstraint("organization_id", "endpoint_pattern", name="uq_org_endpoint_limit"),
    )

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    endpoint_pattern: Mapped[str] = mapped_column(String(200), default="*")
    requests_per_minute: Mapped[int] = mapped_column(Integer, default=60)
    requests_per_hour: Mapped[int] = mapped_column(Integer, default=1000)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<RateLimitConfig {self.endpoint_pattern} {self.requests_per_minute}/min>"
