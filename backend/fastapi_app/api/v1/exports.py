import uuid
from datetime import datetime, UTC, timedelta

from fastapi import APIRouter, Query, status
from sqlalchemy import select

from fastapi_app.api.deps import CurrentOrg, CurrentUser, DBSession
from shared.exceptions import NotFoundError
from shared.models.export import ExportJob
from shared.schemas.export import ExportJobResponse, ExportRequest

router = APIRouter()


@router.post("/", response_model=ExportJobResponse, status_code=status.HTTP_201_CREATED)
async def create_export(
    data: ExportRequest,
    db: DBSession,
    current_user: CurrentUser,
    current_org: CurrentOrg,
):
    export_job = ExportJob(
        organization_id=current_org.id,
        user_id=current_user.id,
        export_type=data.export_type,
        filters=data.filters.model_dump(mode="json"),
        expires_at=datetime.now(UTC) + timedelta(hours=24),
    )
    db.add(export_job)
    await db.flush()
    await db.refresh(export_job)

    from workers.tasks.export_tasks import generate_export

    generate_export.delay(str(export_job.id))

    return export_job


@router.get("/", response_model=list[ExportJobResponse])
async def list_exports(
    db: DBSession,
    current_user: CurrentUser,
    current_org: CurrentOrg,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    result = await db.execute(
        select(ExportJob)
        .where(
            ExportJob.organization_id == current_org.id,
            ExportJob.user_id == current_user.id,
        )
        .order_by(ExportJob.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all())


@router.get("/{export_id}", response_model=ExportJobResponse)
async def get_export(
    export_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
    current_org: CurrentOrg,
):
    result = await db.execute(
        select(ExportJob).where(
            ExportJob.id == export_id,
            ExportJob.organization_id == current_org.id,
        )
    )
    export_job = result.scalar_one_or_none()
    if not export_job:
        raise NotFoundError("Export job", str(export_id))

    if export_job.status == "completed" and export_job.s3_key:
        from fastapi_app.services.upload_service import get_s3_client
        from shared.config import get_settings

        settings = get_settings()
        try:
            s3 = get_s3_client()
            download_url = s3.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": export_job.s3_bucket or settings.s3_bucket_name,
                    "Key": export_job.s3_key,
                },
                ExpiresIn=3600,
            )
            export_job_dict = ExportJobResponse.model_validate(export_job).model_dump()
            export_job_dict["download_url"] = download_url
            return ExportJobResponse(**export_job_dict)
        except Exception:
            pass

    return export_job


@router.delete("/{export_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_export(
    export_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
    current_org: CurrentOrg,
):
    result = await db.execute(
        select(ExportJob).where(
            ExportJob.id == export_id,
            ExportJob.organization_id == current_org.id,
        )
    )
    export_job = result.scalar_one_or_none()
    if not export_job:
        raise NotFoundError("Export job", str(export_id))

    # Delete S3 file if exists
    if export_job.s3_key:
        try:
            from fastapi_app.services.upload_service import get_s3_client
            from shared.config import get_settings

            settings = get_settings()
            s3 = get_s3_client()
            s3.delete_object(
                Bucket=export_job.s3_bucket or settings.s3_bucket_name,
                Key=export_job.s3_key,
            )
        except Exception:
            pass

    await db.delete(export_job)
    await db.flush()
