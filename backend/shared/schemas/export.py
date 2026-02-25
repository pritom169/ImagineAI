import uuid
from datetime import datetime

from pydantic import BaseModel


class ExportFilter(BaseModel):
    date_from: datetime | None = None
    date_to: datetime | None = None
    category: str | None = None
    status: str | None = None
    product_ids: list[uuid.UUID] | None = None


class ExportRequest(BaseModel):
    export_type: str
    filters: ExportFilter = ExportFilter()


class ExportJobResponse(BaseModel):
    id: uuid.UUID
    export_type: str
    status: str
    row_count: int | None
    file_size_bytes: int | None
    download_url: str | None = None
    created_at: datetime
    expires_at: datetime | None

    model_config = {"from_attributes": True}
