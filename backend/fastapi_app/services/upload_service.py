import uuid
from datetime import datetime, UTC

import boto3
from botocore.config import Config as BotoConfig
from sqlalchemy.ext.asyncio import AsyncSession

from shared.config import get_settings
from shared.constants import AnalysisStatus, JobStatus, JobType, StepName, StepStatus
from shared.exceptions import NotFoundError, StorageError, ValidationError
from shared.models.analysis import AnalysisResult
from shared.models.pipeline import JobStep, ProcessingJob
from shared.models.product import Product, ProductImage

settings = get_settings()

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def get_s3_client():
    kwargs = {
        "service_name": "s3",
        "region_name": settings.aws_region,
        "aws_access_key_id": settings.aws_access_key_id,
        "aws_secret_access_key": settings.aws_secret_access_key,
        "config": BotoConfig(signature_version="s3v4"),
    }
    if settings.s3_endpoint_url:
        kwargs["endpoint_url"] = settings.s3_endpoint_url
    return boto3.client(**kwargs)


def generate_s3_key(user_id: uuid.UUID, product_id: uuid.UUID, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1] if "." in filename else "jpg"
    unique_id = uuid.uuid4().hex[:12]
    return f"uploads/{user_id}/{product_id}/{unique_id}.{ext}"


async def create_presigned_upload(
    db: AsyncSession,
    user_id: uuid.UUID,
    product_id: uuid.UUID,
    filename: str,
    content_type: str,
    file_size_bytes: int,
    org_id: uuid.UUID | None = None,
) -> dict:
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValidationError(f"Content type '{content_type}' not allowed. Use: {ALLOWED_CONTENT_TYPES}")

    from sqlalchemy import select

    query = select(Product).where(Product.id == product_id)
    if org_id:
        query = query.where(Product.organization_id == org_id)
    else:
        query = query.where(Product.user_id == user_id)

    result = await db.execute(query)
    if not result.scalar_one_or_none():
        raise NotFoundError("Product", str(product_id))

    s3_key = generate_s3_key(user_id, product_id, filename)

    # Create ProductImage record
    image = ProductImage(
        product_id=product_id,
        s3_key=s3_key,
        s3_bucket=settings.s3_bucket_name,
        original_filename=filename,
        content_type=content_type,
        file_size_bytes=file_size_bytes,
        upload_status="pending",
    )
    db.add(image)
    await db.flush()
    await db.refresh(image)

    # Generate presigned URL
    try:
        s3 = get_s3_client()
        presigned_url = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": settings.s3_bucket_name,
                "Key": s3_key,
                "ContentType": content_type,
            },
            ExpiresIn=3600,
        )
    except Exception as e:
        raise StorageError(f"Failed to generate presigned URL: {e}")

    return {
        "upload_url": presigned_url,
        "image_id": image.id,
        "s3_key": s3_key,
        "expires_in": 3600,
    }


async def confirm_upload(
    db: AsyncSession,
    user_id: uuid.UUID,
    image_id: uuid.UUID,
) -> dict:
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    # Get image with product
    result = await db.execute(
        select(ProductImage)
        .options(selectinload(ProductImage.product))
        .where(ProductImage.id == image_id)
    )
    image = result.scalar_one_or_none()
    if not image or image.product.user_id != user_id:
        raise NotFoundError("Image", str(image_id))

    # Verify the object exists in S3
    try:
        s3 = get_s3_client()
        s3.head_object(Bucket=image.s3_bucket, Key=image.s3_key)
    except Exception:
        raise StorageError("Image not found in storage. Please upload first.")

    # Update image status
    image.upload_status = "uploaded"

    # Update product status
    image.product.status = "processing"

    # Create analysis result placeholder
    analysis = AnalysisResult(
        product_image_id=image.id,
        model_version="pending",
        status=AnalysisStatus.PENDING.value,
    )
    db.add(analysis)

    # Create processing job
    job = ProcessingJob(
        user_id=user_id,
        job_type=JobType.SINGLE.value,
        status=JobStatus.QUEUED.value,
        total_images=1,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)

    # Create job steps
    for step_name in StepName:
        step = JobStep(
            job_id=job.id,
            product_image_id=image.id,
            step_name=step_name.value,
            status=StepStatus.PENDING.value,
        )
        db.add(step)

    await db.flush()

    # Dispatch Celery task
    from workers.tasks.image_processing import process_image

    task = process_image.delay(str(image.id), str(job.id))
    job.celery_task_id = task.id
    job.started_at = datetime.now(UTC)
    await db.flush()

    return {
        "image_id": image.id,
        "job_id": job.id,
        "status": "queued",
        "message": "Image processing started",
    }
