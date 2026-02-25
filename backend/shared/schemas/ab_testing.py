import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ABVariantCreate(BaseModel):
    model_version: str
    weight: int = Field(ge=0, le=100)
    is_control: bool = False


class ABExperimentCreate(BaseModel):
    name: str = Field(max_length=100)
    model_type: str
    variants: list[ABVariantCreate] = Field(min_length=2)


class ABExperimentUpdate(BaseModel):
    is_active: bool | None = None


class ABVariantResponse(BaseModel):
    id: uuid.UUID
    model_version: str
    weight: int
    is_control: bool

    model_config = {"from_attributes": True}


class ABExperimentResponse(BaseModel):
    id: uuid.UUID
    name: str
    model_type: str
    is_active: bool
    start_date: datetime | None
    end_date: datetime | None
    variants: list[ABVariantResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ABVariantStats(BaseModel):
    variant_id: uuid.UUID
    model_version: str
    sample_count: int
    avg_confidence: float | None
    avg_processing_time_ms: float | None
