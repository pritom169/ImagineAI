import uuid
from datetime import datetime

from pydantic import BaseModel


class ExtractedAttributeResponse(BaseModel):
    id: uuid.UUID
    attribute_name: str
    attribute_value: str
    confidence: float | None

    model_config = {"from_attributes": True}


class DetectedDefectResponse(BaseModel):
    id: uuid.UUID
    defect_type: str
    severity: str
    confidence: float | None
    bounding_box: dict | None
    description: str | None

    model_config = {"from_attributes": True}


class AnalysisResultResponse(BaseModel):
    id: uuid.UUID
    product_image_id: uuid.UUID
    model_version: str
    classification_label: str | None
    classification_confidence: float | None
    classification_scores: dict
    description_text: str | None
    description_model: str | None
    processing_time_ms: int | None
    status: str
    error_message: str | None
    experiment_id: uuid.UUID | None = None
    variant_id: uuid.UUID | None = None
    extracted_attributes: list[ExtractedAttributeResponse] = []
    detected_defects: list[DetectedDefectResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
