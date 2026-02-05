import uuid
from datetime import datetime, UTC

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from fastapi_app.api.deps import CurrentOrg, CurrentUser, DBSession
from shared.constants import (
    AnalysisStatus,
    JobStatus,
    JobType,
    StepName,
    StepStatus,
)
from shared.exceptions import NotFoundError, ValidationError
from shared.models.analysis import AnalysisResult
from shared.models.pipeline import JobStep, ProcessingJob
from shared.models.product import Product, ProductImage
from shared.schemas.pipeline import BatchCreateRequest, ProcessingJobResponse

router = APIRouter()


@router.post("", response_model=ProcessingJobResponse, status_code=201)
async def create_batch_job(
    data: BatchCreateRequest,
    db: DBSession,
    current_user: CurrentUser,
    current_org: CurrentOrg,
):
    result = await db.execute(
        select(Product).where(
            Product.id == data.product_id, Product.organization_id == current_org.id
        )
    )
    if not result.scalar_one_or_none():
        raise NotFoundError("Product", str(data.product_id))

    result = await db.execute(
        select(ProductImage).where(
            ProductImage.id.in_(data.image_ids),
            ProductImage.product_id == data.product_id,
        )
    )
    images = list(result.scalars().all())
    if len(images) != len(data.image_ids):
        raise ValidationError("Some image IDs are invalid or don't belong to this product")

    job = ProcessingJob(
        user_id=current_user.id,
        job_type=JobType.BATCH.value,
        status=JobStatus.QUEUED.value,
        total_images=len(images),
        started_at=datetime.now(UTC),
    )
    db.add(job)
    await db.flush()

    for image in images:
        existing = await db.execute(
            select(AnalysisResult).where(AnalysisResult.product_image_id == image.id)
        )
        if not existing.scalar_one_or_none():
            db.add(AnalysisResult(
                product_image_id=image.id,
                model_version="pending",
                status=AnalysisStatus.PENDING.value,
            ))

        for step_name in StepName:
            db.add(JobStep(
                job_id=job.id,
                product_image_id=image.id,
                step_name=step_name.value,
                status=StepStatus.PENDING.value,
            ))

    await db.flush()

    from workers.tasks.batch_processing import process_batch

    task = process_batch.delay(str(job.id), [str(img.id) for img in images])
    job.celery_task_id = task.id
    await db.flush()
    await db.refresh(job, attribute_names=["steps"])

    return job


@router.get("/{job_id}", response_model=ProcessingJobResponse)
async def get_batch_status(
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
        raise NotFoundError("Batch job", str(job_id))
    return job


@router.delete("/{job_id}", status_code=204)
async def cancel_batch_job(
    job_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
):
    result = await db.execute(
        select(ProcessingJob).where(
            ProcessingJob.id == job_id,
            ProcessingJob.user_id == current_user.id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundError("Batch job", str(job_id))

    if job.celery_task_id:
        from workers.celery_app import celery_app
        celery_app.control.revoke(job.celery_task_id, terminate=True)

    job.status = JobStatus.CANCELLED.value
    job.completed_at = datetime.now(UTC)
    await db.flush()
