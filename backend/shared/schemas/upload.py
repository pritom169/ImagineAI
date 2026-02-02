import uuid

from pydantic import BaseModel, Field


class PresignedURLRequest(BaseModel):
    product_id: uuid.UUID
    filename: str = Field(max_length=500)
    content_type: str = Field(max_length=100)
    file_size_bytes: int = Field(gt=0, le=50_000_000)  # Max 50MB


class PresignedURLResponse(BaseModel):
    upload_url: str
    image_id: uuid.UUID
    s3_key: str
    expires_in: int  # seconds


class UploadConfirmRequest(BaseModel):
    image_id: uuid.UUID


class UploadConfirmResponse(BaseModel):
    image_id: uuid.UUID
    job_id: uuid.UUID
    status: str = "queued"
    message: str = "Image processing started"


class DirectUploadResponse(BaseModel):
    image_id: uuid.UUID
    job_id: uuid.UUID
    status: str = "queued"
    message: str = "Image uploaded and processing started"
