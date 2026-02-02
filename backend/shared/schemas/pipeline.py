import uuid
from datetime import datetime

from pydantic import BaseModel


class JobStepResponse(BaseModel):
    id: uuid.UUID
    step_name: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    duration_ms: int | None
    error_message: str | None
    result_data: dict

    model_config = {"from_attributes": True}


class ProcessingJobResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    job_type: str
    status: str
    total_images: int
    processed_images: int
    failed_images: int
    celery_task_id: str | None
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    steps: list[JobStepResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProcessingJobListResponse(BaseModel):
    items: list[ProcessingJobResponse]
    total: int


class ProcessingUpdate(BaseModel):
    """WebSocket message format for real-time processing updates."""

    type: str  # "step_update", "job_complete", "job_failed"
    job_id: str
    image_id: str | None = None
    step: str | None = None
    status: str
    progress: dict | None = None  # {"completed": 3, "total": 5}
    data: dict | None = None
    timestamp: datetime


class BatchCreateRequest(BaseModel):
    product_id: uuid.UUID
    image_ids: list[uuid.UUID]
