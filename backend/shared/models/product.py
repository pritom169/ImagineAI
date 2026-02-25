import uuid

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import Base, TimestampMixin, UUIDMixin


class Product(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "products"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(100), index=True)
    subcategory: Mapped[str | None] = mapped_column(String(100))
    ai_description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)

    # Relationships
    user = relationship("User", back_populates="products")
    organization = relationship("Organization", back_populates="products")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Product {self.title}>"


class ProductImage(UUIDMixin, Base):
    __tablename__ = "product_images"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    s3_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    s3_bucket: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(500))
    content_type: Mapped[str | None] = mapped_column(String(100))
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    upload_status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at = TimestampMixin.created_at

    # Relationships
    product = relationship("Product", back_populates="images")
    analysis_result = relationship(
        "AnalysisResult", back_populates="product_image", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ProductImage {self.original_filename}>"
