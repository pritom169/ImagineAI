import uuid

from fastapi import APIRouter, Query
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from fastapi_app.api.deps import CurrentUser, DBSession
from shared.exceptions import NotFoundError
from shared.models.pipeline import ProcessingJob
from shared.schemas.pipeline import ProcessingJobListResponse, ProcessingJobResponse

router = APIRouter()


@router.get("", response_model=ProcessingJobListResponse)
async def list_jobs(
    db: DBSession,
    current_user: CurrentUser,
    status: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    query = select(ProcessingJob).where(ProcessingJob.user_id == current_user.id)
    count_query = select(func.count(ProcessingJob.id)).where(
        ProcessingJob.user_id == current_user.id
    )

    if status:
        query = query.where(ProcessingJob.status == status)
        count_query = count_query.where(ProcessingJob.status == status)

    total = (await db.execute(count_query)).scalar() or 0

    query = (
        query.options(selectinload(ProcessingJob.steps))
        .order_by(ProcessingJob.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    items = list(result.scalars().all())

    return {"items": items, "total": total}


@router.get("/{job_id}", response_model=ProcessingJobResponse)
async def get_job_detail(
    job_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
):
    result = await db.execute(
        select(ProcessingJob)
        .options(selectinload(ProcessingJob.steps))
        .where(
            ProcessingJob.id == job_id,
            ProcessingJob.user_id == current_user.id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundError("Processing job", str(job_id))
    return job
