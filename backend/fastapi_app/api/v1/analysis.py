import uuid

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from fastapi_app.api.deps import CurrentOrg, CurrentUser, DBSession
from shared.exceptions import NotFoundError
from shared.models.analysis import AnalysisResult
from shared.models.product import Product, ProductImage
from shared.schemas.analysis import AnalysisResultResponse

router = APIRouter()


@router.get("/{image_id}", response_model=AnalysisResultResponse)
async def get_analysis_result(
    image_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
    current_org: CurrentOrg,
):
    result = await db.execute(
        select(AnalysisResult)
        .join(ProductImage, AnalysisResult.product_image_id == ProductImage.id)
        .join(Product, ProductImage.product_id == Product.id)
        .options(
            selectinload(AnalysisResult.extracted_attributes),
            selectinload(AnalysisResult.detected_defects),
        )
        .where(
            AnalysisResult.product_image_id == image_id,
            Product.organization_id == current_org.id,
        )
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise NotFoundError("Analysis result", str(image_id))
    return analysis


@router.post("/{image_id}/retry", response_model=dict)
async def retry_analysis(
    image_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
    current_org: CurrentOrg,
):
    from datetime import datetime, UTC
    from shared.constants import AnalysisStatus, JobStatus, JobType, StepName, StepStatus
    from shared.models.pipeline import ProcessingJob, JobStep

    result = await db.execute(
        select(AnalysisResult)
        .join(ProductImage, AnalysisResult.product_image_id == ProductImage.id)
        .join(Product, ProductImage.product_id == Product.id)
        .where(
            AnalysisResult.product_image_id == image_id,
            Product.organization_id == current_org.id,
        )
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise NotFoundError("Analysis result", str(image_id))

    # Reset analysis
    analysis.status = AnalysisStatus.PENDING.value
    analysis.error_message = None

    # Create new processing job
    job = ProcessingJob(
        user_id=current_user.id,
        job_type=JobType.SINGLE.value,
        status=JobStatus.QUEUED.value,
        total_images=1,
        started_at=datetime.now(UTC),
    )
    db.add(job)
    await db.flush()

    for step_name in StepName:
        db.add(JobStep(
            job_id=job.id,
            product_image_id=image_id,
            step_name=step_name.value,
            status=StepStatus.PENDING.value,
        ))
    await db.flush()

    from workers.tasks.image_processing import process_image

    task = process_image.delay(str(image_id), str(job.id))
    job.celery_task_id = task.id
    await db.flush()

    return {"job_id": str(job.id), "status": "queued", "message": "Analysis retry started"}
