from fastapi import APIRouter, UploadFile

from fastapi_app.api.deps import CurrentUser, DBSession
from fastapi_app.services.upload_service import confirm_upload, create_presigned_upload
from shared.schemas.upload import (
    DirectUploadResponse,
    PresignedURLRequest,
    PresignedURLResponse,
    UploadConfirmRequest,
    UploadConfirmResponse,
)

router = APIRouter()


@router.post("/presigned-url", response_model=PresignedURLResponse)
async def get_presigned_url(
    data: PresignedURLRequest,
    db: DBSession,
    current_user: CurrentUser,
):
    result = await create_presigned_upload(
        db,
        user_id=current_user.id,
        product_id=data.product_id,
        filename=data.filename,
        content_type=data.content_type,
        file_size_bytes=data.file_size_bytes,
    )
    return result


@router.post("/confirm", response_model=UploadConfirmResponse)
async def confirm_image_upload(
    data: UploadConfirmRequest,
    db: DBSession,
    current_user: CurrentUser,
):
    return await confirm_upload(db, current_user.id, data.image_id)


@router.post("/direct", response_model=DirectUploadResponse)
async def direct_upload(
    product_id: str,
    file: UploadFile,
    db: DBSession,
    current_user: CurrentUser,
):
    import uuid

    from fastapi_app.services.upload_service import get_s3_client, generate_s3_key
    from shared.config import get_settings
    from shared.constants import AnalysisStatus, JobStatus, JobType, StepName, StepStatus
    from shared.models.analysis import AnalysisResult
    from shared.models.pipeline import JobStep, ProcessingJob
    from shared.models.product import ProductImage
    from shared.exceptions import ValidationError, StorageError
    from datetime import datetime, UTC

    settings = get_settings()
    pid = uuid.UUID(product_id)

    content_type = file.content_type or "image/jpeg"
    allowed = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if content_type not in allowed:
        raise ValidationError(f"Content type '{content_type}' not allowed")

    contents = await file.read()
    if len(contents) > 50_000_000:
        raise ValidationError("File too large. Maximum 50MB.")

    s3_key = generate_s3_key(current_user.id, pid, file.filename or "upload.jpg")

    # Upload to S3
    try:
        s3 = get_s3_client()
        s3.put_object(
            Bucket=settings.s3_bucket_name,
            Key=s3_key,
            Body=contents,
            ContentType=content_type,
        )
    except Exception as e:
        raise StorageError(f"Upload failed: {e}")

    # Create records
    image = ProductImage(
        product_id=pid,
        s3_key=s3_key,
        s3_bucket=settings.s3_bucket_name,
        original_filename=file.filename,
        content_type=content_type,
        file_size_bytes=len(contents),
        upload_status="uploaded",
    )
    db.add(image)
    await db.flush()

    analysis = AnalysisResult(
        product_image_id=image.id,
        model_version="pending",
        status=AnalysisStatus.PENDING.value,
    )
    db.add(analysis)

    job = ProcessingJob(
        user_id=current_user.id,
        job_type=JobType.SINGLE.value,
        status=JobStatus.QUEUED.value,
        total_images=1,
        started_at=datetime.now(UTC),
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)

    for step_name in StepName:
        db.add(JobStep(
            job_id=job.id,
            product_image_id=image.id,
            step_name=step_name.value,
            status=StepStatus.PENDING.value,
        ))
    await db.flush()

    from workers.tasks.image_processing import process_image

    task = process_image.delay(str(image.id), str(job.id))
    job.celery_task_id = task.id
    await db.flush()

    return DirectUploadResponse(image_id=image.id, job_id=job.id)
