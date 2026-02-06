from fastapi import APIRouter
from sqlalchemy import func, select

from fastapi_app.api.deps import CurrentOrg, CurrentUser, DBSession
from shared.models.analysis import AnalysisResult, DetectedDefect
from shared.models.pipeline import ProcessingJob
from shared.models.product import Product, ProductImage

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(
    db: DBSession, current_user: CurrentUser, current_org: CurrentOrg
):
    total_products = (
        await db.execute(
            select(func.count(Product.id)).where(Product.organization_id == current_org.id)
        )
    ).scalar() or 0

    total_images = (
        await db.execute(
            select(func.count(ProductImage.id))
            .join(Product, ProductImage.product_id == Product.id)
            .where(Product.organization_id == current_org.id)
        )
    ).scalar() or 0

    completed_analyses = (
        await db.execute(
            select(func.count(AnalysisResult.id))
            .join(ProductImage, AnalysisResult.product_image_id == ProductImage.id)
            .join(Product, ProductImage.product_id == Product.id)
            .where(Product.organization_id == current_org.id, AnalysisResult.status == "completed")
        )
    ).scalar() or 0

    total_defects = (
        await db.execute(
            select(func.count(DetectedDefect.id))
            .join(AnalysisResult, DetectedDefect.analysis_result_id == AnalysisResult.id)
            .join(ProductImage, AnalysisResult.product_image_id == ProductImage.id)
            .join(Product, ProductImage.product_id == Product.id)
            .where(Product.organization_id == current_org.id)
        )
    ).scalar() or 0

    active_jobs = (
        await db.execute(
            select(func.count(ProcessingJob.id)).where(
                ProcessingJob.user_id == current_user.id,
                ProcessingJob.status.in_(["queued", "processing"]),
            )
        )
    ).scalar() or 0

    avg_processing_time = (
        await db.execute(
            select(func.avg(AnalysisResult.processing_time_ms))
            .join(ProductImage, AnalysisResult.product_image_id == ProductImage.id)
            .join(Product, ProductImage.product_id == Product.id)
            .where(
                Product.organization_id == current_org.id,
                AnalysisResult.status == "completed",
                AnalysisResult.processing_time_ms.isnot(None),
            )
        )
    ).scalar()

    return {
        "total_products": total_products,
        "total_images": total_images,
        "completed_analyses": completed_analyses,
        "total_defects": total_defects,
        "active_jobs": active_jobs,
        "avg_processing_time_ms": round(avg_processing_time) if avg_processing_time else None,
    }


@router.get("/recent")
async def get_recent_activity(db: DBSession, current_user: CurrentUser):
    result = await db.execute(
        select(ProcessingJob)
        .where(ProcessingJob.user_id == current_user.id)
        .order_by(ProcessingJob.created_at.desc())
        .limit(10)
    )
    jobs = result.scalars().all()

    return [
        {
            "id": str(job.id),
            "job_type": job.job_type,
            "status": job.status,
            "total_images": job.total_images,
            "processed_images": job.processed_images,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        }
        for job in jobs
    ]


@router.get("/category-distribution")
async def get_category_distribution(
    db: DBSession, current_user: CurrentUser, current_org: CurrentOrg
):
    result = await db.execute(
        select(Product.category, func.count(Product.id))
        .where(
            Product.organization_id == current_org.id,
            Product.category.isnot(None),
        )
        .group_by(Product.category)
        .order_by(func.count(Product.id).desc())
    )
    rows = result.all()
    return [{"category": row[0], "count": row[1]} for row in rows]
