import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import Base, TimestampMixin, UUIDMixin


class AnalysisResult(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "analysis_results"

    product_image_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_images.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    classification_label: Mapped[str | None] = mapped_column(String(100))
    classification_confidence: Mapped[float | None] = mapped_column(Float)
    classification_scores: Mapped[dict] = mapped_column(JSONB, default=dict)
    description_text: Mapped[str | None] = mapped_column(Text)
    description_model: Mapped[str | None] = mapped_column(String(100))
    processing_time_ms: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    error_message: Mapped[str | None] = mapped_column(Text)

    # A/B experiment tracking
    experiment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ab_experiments.id", ondelete="SET NULL"),
        nullable=True,
    )
    variant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ab_variants.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    product_image = relationship("ProductImage", back_populates="analysis_result")
    extracted_attributes = relationship(
        "ExtractedAttribute", back_populates="analysis_result", cascade="all, delete-orphan"
    )
    detected_defects = relationship(
        "DetectedDefect", back_populates="analysis_result", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<AnalysisResult {self.classification_label} ({self.status})>"


class ExtractedAttribute(UUIDMixin, Base):
    __tablename__ = "extracted_attributes"

    analysis_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attribute_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    attribute_value: Mapped[str] = mapped_column(String(500), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)

    # Relationships
    analysis_result = relationship("AnalysisResult", back_populates="extracted_attributes")

    def __repr__(self) -> str:
        return f"<ExtractedAttribute {self.attribute_name}={self.attribute_value}>"


class DetectedDefect(UUIDMixin, Base):
    __tablename__ = "detected_defects"

    analysis_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    defect_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)
    bounding_box: Mapped[dict | None] = mapped_column(JSONB)
    description: Mapped[str | None] = mapped_column(Text)

    # Relationships
    analysis_result = relationship("AnalysisResult", back_populates="detected_defects")

    def __repr__(self) -> str:
        return f"<DetectedDefect {self.defect_type} ({self.severity})>"
