import csv
import io
import uuid
from datetime import datetime, UTC

from celery import shared_task

from shared.config import get_settings
from workers.celery_app import get_sync_session

settings = get_settings()


@shared_task(bind=True, time_limit=600, soft_time_limit=570)
def generate_export(self, export_job_id: str):
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from shared.models.analysis import AnalysisResult
    from shared.models.export import ExportJob
    from shared.models.product import Product, ProductImage

    with get_sync_session() as session:
        export_job = session.get(ExportJob, uuid.UUID(export_job_id))
        if not export_job:
            return

        export_job.status = "processing"
        session.commit()

        try:
            org_id = export_job.organization_id

            if export_job.export_type in ("analysis_csv", "analysis_pdf"):
                results = session.execute(
                    select(AnalysisResult)
                    .join(ProductImage, AnalysisResult.product_image_id == ProductImage.id)
                    .join(Product, ProductImage.product_id == Product.id)
                    .options(
                        selectinload(AnalysisResult.extracted_attributes),
                        selectinload(AnalysisResult.detected_defects),
                    )
                    .where(Product.organization_id == org_id)
                    .order_by(AnalysisResult.created_at.desc())
                ).scalars().all()

                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow([
                    "Image ID", "Classification", "Confidence", "Model Version",
                    "Attributes", "Defect Count", "Processing Time (ms)",
                    "Status", "Created At",
                ])

                for r in results:
                    attrs = "; ".join(
                        f"{a.attribute_name}={a.attribute_value}" for a in r.extracted_attributes
                    )
                    writer.writerow([
                        str(r.product_image_id),
                        r.classification_label or "",
                        f"{r.classification_confidence:.4f}" if r.classification_confidence else "",
                        r.model_version,
                        attrs,
                        len(r.detected_defects),
                        r.processing_time_ms or "",
                        r.status,
                        r.created_at.isoformat() if r.created_at else "",
                    ])

                row_count = len(results)
                content = output.getvalue().encode("utf-8")

            elif export_job.export_type == "products_csv":
                products = session.execute(
                    select(Product)
                    .options(selectinload(Product.images))
                    .where(Product.organization_id == org_id)
                    .order_by(Product.created_at.desc())
                ).scalars().all()

                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow([
                    "Product ID", "Title", "Category", "Status",
                    "Image Count", "AI Description", "Created At",
                ])

                for p in products:
                    writer.writerow([
                        str(p.id),
                        p.title or "",
                        p.category or "",
                        p.status,
                        len(p.images),
                        (p.ai_description or "")[:200],
                        p.created_at.isoformat() if p.created_at else "",
                    ])

                row_count = len(products)
                content = output.getvalue().encode("utf-8")
            else:
                raise ValueError(f"Unknown export type: {export_job.export_type}")

            # Upload to S3
            import boto3
            from botocore.config import Config as BotoConfig

            s3_kwargs = {
                "service_name": "s3",
                "region_name": settings.aws_region,
                "aws_access_key_id": settings.aws_access_key_id,
                "aws_secret_access_key": settings.aws_secret_access_key,
                "config": BotoConfig(signature_version="s3v4"),
            }
            if settings.s3_endpoint_url:
                s3_kwargs["endpoint_url"] = settings.s3_endpoint_url

            s3 = boto3.client(**s3_kwargs)
            s3_key = f"exports/{org_id}/{export_job.id}.csv"

            s3.put_object(
                Bucket=settings.s3_bucket_name,
                Key=s3_key,
                Body=content,
                ContentType="text/csv",
            )

            export_job.status = "completed"
            export_job.s3_key = s3_key
            export_job.s3_bucket = settings.s3_bucket_name
            export_job.file_size_bytes = len(content)
            export_job.row_count = row_count
            session.commit()

        except Exception as exc:
            export_job.status = "failed"
            export_job.error_message = str(exc)[:500]
            session.commit()
            raise


@shared_task
def cleanup_expired_exports():
    from sqlalchemy import select

    from shared.models.export import ExportJob

    with get_sync_session() as session:
        result = session.execute(
            select(ExportJob).where(
                ExportJob.expires_at < datetime.now(UTC),
                ExportJob.status == "completed",
            )
        )
        expired = result.scalars().all()

        for job in expired:
            if job.s3_key:
                try:
                    import boto3
                    from botocore.config import Config as BotoConfig

                    s3_kwargs = {
                        "service_name": "s3",
                        "region_name": settings.aws_region,
                        "aws_access_key_id": settings.aws_access_key_id,
                        "aws_secret_access_key": settings.aws_secret_access_key,
                        "config": BotoConfig(signature_version="s3v4"),
                    }
                    if settings.s3_endpoint_url:
                        s3_kwargs["endpoint_url"] = settings.s3_endpoint_url

                    s3 = boto3.client(**s3_kwargs)
                    s3.delete_object(
                        Bucket=job.s3_bucket or settings.s3_bucket_name,
                        Key=job.s3_key,
                    )
                except Exception:
                    pass

            job.status = "expired"
        session.commit()
