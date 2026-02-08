import logging
import time
from datetime import UTC, datetime

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.orm import Session

from shared.config import get_settings
from shared.constants import AnalysisStatus, JobStatus, StepName, StepStatus
from shared.models.analysis import AnalysisResult
from shared.models.pipeline import JobStep, ProcessingJob
from shared.models.product import Product, ProductImage
from workers.celery_app import get_sync_session
from workers.tasks.notifications import (
    publish_job_complete,
    publish_job_failed,
    publish_step_update,
)

logger = logging.getLogger(__name__)
settings = get_settings()


def update_step_status(
    session: Session,
    job_id: str,
    image_id: str,
    step_name: str,
    status: str,
    duration_ms: int | None = None,
    result_data: dict | None = None,
    error_message: str | None = None,
):
    """Update a job step status in the database."""
    step = session.execute(
        select(JobStep).where(
            JobStep.job_id == job_id,
            JobStep.product_image_id == image_id,
            JobStep.step_name == step_name,
        )
    ).scalar_one_or_none()

    if step:
        step.status = status
        if status == StepStatus.RUNNING.value:
            step.started_at = datetime.now(UTC)
        if status in (StepStatus.COMPLETED.value, StepStatus.FAILED.value):
            step.completed_at = datetime.now(UTC)
        if duration_ms is not None:
            step.duration_ms = duration_ms
        if result_data:
            step.result_data = result_data
        if error_message:
            step.error_message = error_message
        session.commit()


@shared_task(
    bind=True,
    max_retries=3,
    acks_late=True,
    reject_on_worker_lost=True,
    time_limit=300,
    soft_time_limit=270,
)
def process_image(self, image_id: str, job_id: str, user_id: str | None = None):
    """Main image processing pipeline task."""
    logger.info(f"Starting processing for image={image_id}, job={job_id}")
    pipeline_start = time.time()

    with get_sync_session() as session:
        try:
            # Update job status
            job = session.execute(
                select(ProcessingJob).where(ProcessingJob.id == job_id)
            ).scalar_one()
            job.status = JobStatus.PROCESSING.value
            session.commit()

            # Get the image
            image = session.execute(
                select(ProductImage).where(ProductImage.id == image_id)
            ).scalar_one()

            analysis = session.execute(
                select(AnalysisResult).where(
                    AnalysisResult.product_image_id == image_id
                )
            ).scalar_one()

            analysis.status = AnalysisStatus.PROCESSING.value
            session.commit()

            # ---- Step 1: Preprocess ----
            step_start = time.time()
            update_step_status(
                session, job_id, image_id, StepName.PREPROCESS.value, StepStatus.RUNNING.value
            )
            publish_step_update(job_id, image_id, "preprocess", "running")

            from ml.services.preprocessing import download_and_preprocess

            image_tensor = download_and_preprocess(image.s3_bucket, image.s3_key)

            step_ms = int((time.time() - step_start) * 1000)
            update_step_status(
                session, job_id, image_id, StepName.PREPROCESS.value,
                StepStatus.COMPLETED.value, duration_ms=step_ms,
            )
            publish_step_update(
                job_id, image_id, "preprocess", "completed",
                progress={"completed": 1, "total": 5},
            )

            # ---- Resolve A/B test model versions ----
            experiment_id = None
            variant_id = None
            if user_id:
                from ml.models.model_registry import registry

                clf_version, experiment_id, variant_id = registry.get_model_version_for_user(
                    "classifier", user_id, session
                )
                fe_version, _, _ = registry.get_model_version_for_user(
                    "feature_extractor", user_id, session
                )
                dd_version, _, _ = registry.get_model_version_for_user(
                    "defect_detector", user_id, session
                )
            else:
                clf_version = fe_version = dd_version = "v1"

            # ---- Step 2: Classification ----
            step_start = time.time()
            update_step_status(
                session, job_id, image_id, StepName.CLASSIFY.value, StepStatus.RUNNING.value
            )
            publish_step_update(job_id, image_id, "classify", "running")

            from ml.services.inference import run_classification

            classification = run_classification(image_tensor, version=clf_version)

            analysis.classification_label = classification["label"]
            analysis.classification_confidence = classification["confidence"]
            analysis.classification_scores = classification["scores"]
            session.commit()

            step_ms = int((time.time() - step_start) * 1000)
            update_step_status(
                session, job_id, image_id, StepName.CLASSIFY.value,
                StepStatus.COMPLETED.value, duration_ms=step_ms,
                result_data={"label": classification["label"], "confidence": classification["confidence"]},
            )
            publish_step_update(
                job_id, image_id, "classify", "completed",
                progress={"completed": 2, "total": 5},
                data={"label": classification["label"], "confidence": classification["confidence"]},
            )

            # ---- Step 3: Attribute Extraction ----
            step_start = time.time()
            update_step_status(
                session, job_id, image_id, StepName.EXTRACT_ATTRIBUTES.value,
                StepStatus.RUNNING.value,
            )
            publish_step_update(job_id, image_id, "extract_attributes", "running")

            from ml.services.inference import run_attribute_extraction
            from shared.models.analysis import ExtractedAttribute

            attributes = run_attribute_extraction(image_tensor, version=fe_version)
            for attr in attributes:
                session.add(ExtractedAttribute(
                    analysis_result_id=analysis.id,
                    attribute_name=attr["name"],
                    attribute_value=attr["value"],
                    confidence=attr["confidence"],
                ))
            session.commit()

            step_ms = int((time.time() - step_start) * 1000)
            update_step_status(
                session, job_id, image_id, StepName.EXTRACT_ATTRIBUTES.value,
                StepStatus.COMPLETED.value, duration_ms=step_ms,
                result_data={"attributes_count": len(attributes)},
            )
            publish_step_update(
                job_id, image_id, "extract_attributes", "completed",
                progress={"completed": 3, "total": 5},
                data={"attributes": attributes},
            )

            # ---- Step 4: Defect Detection ----
            step_start = time.time()
            update_step_status(
                session, job_id, image_id, StepName.DETECT_DEFECTS.value,
                StepStatus.RUNNING.value,
            )
            publish_step_update(job_id, image_id, "detect_defects", "running")

            from ml.services.inference import run_defect_detection
            from shared.models.analysis import DetectedDefect

            defects = run_defect_detection(image_tensor, version=dd_version)
            for defect in defects:
                session.add(DetectedDefect(
                    analysis_result_id=analysis.id,
                    defect_type=defect["type"],
                    severity=defect["severity"],
                    confidence=defect["confidence"],
                    bounding_box=defect.get("bounding_box"),
                    description=defect.get("description"),
                ))
            session.commit()

            step_ms = int((time.time() - step_start) * 1000)
            update_step_status(
                session, job_id, image_id, StepName.DETECT_DEFECTS.value,
                StepStatus.COMPLETED.value, duration_ms=step_ms,
                result_data={"defects_count": len(defects)},
            )
            publish_step_update(
                job_id, image_id, "detect_defects", "completed",
                progress={"completed": 4, "total": 5},
                data={"defects_count": len(defects)},
            )

            # ---- Step 5: Description Generation ----
            step_start = time.time()
            update_step_status(
                session, job_id, image_id, StepName.GENERATE_DESCRIPTION.value,
                StepStatus.RUNNING.value,
            )
            publish_step_update(job_id, image_id, "generate_description", "running")

            from ml.services.description_generator import generate_description

            description_result = generate_description(
                category=classification["label"],
                attributes=attributes,
                defects=defects,
                s3_bucket=image.s3_bucket,
                s3_key=image.s3_key,
            )

            analysis.description_text = description_result["description"]
            analysis.description_model = description_result["model"]
            session.commit()

            # Update product with AI data
            product = session.execute(
                select(Product).where(Product.id == image.product_id)
            ).scalar_one()
            product.category = classification["label"]
            product.ai_description = description_result["description"]
            product.status = "active"
            session.commit()

            step_ms = int((time.time() - step_start) * 1000)
            update_step_status(
                session, job_id, image_id, StepName.GENERATE_DESCRIPTION.value,
                StepStatus.COMPLETED.value, duration_ms=step_ms,
            )
            publish_step_update(
                job_id, image_id, "generate_description", "completed",
                progress={"completed": 5, "total": 5},
            )

            # ---- Finalize ----
            total_ms = int((time.time() - pipeline_start) * 1000)
            analysis.processing_time_ms = total_ms
            analysis.status = AnalysisStatus.COMPLETED.value
            analysis.model_version = classification.get("model_version", "efficientnet-b4-v1")
            if experiment_id:
                analysis.experiment_id = experiment_id
            if variant_id:
                analysis.variant_id = variant_id

            job.status = JobStatus.COMPLETED.value
            job.processed_images = job.processed_images + 1
            job.completed_at = datetime.now(UTC)
            session.commit()

            publish_job_complete(
                job_id,
                progress={"completed": job.processed_images, "total": job.total_images},
            )

            logger.info(
                f"Completed processing for image={image_id} in {total_ms}ms"
            )

        except Exception as exc:
            logger.exception(f"Failed processing image={image_id}: {exc}")
            session.rollback()

            # Mark as failed
            try:
                analysis = session.execute(
                    select(AnalysisResult).where(
                        AnalysisResult.product_image_id == image_id
                    )
                ).scalar_one_or_none()
                if analysis:
                    analysis.status = AnalysisStatus.FAILED.value
                    analysis.error_message = str(exc)

                job = session.execute(
                    select(ProcessingJob).where(ProcessingJob.id == job_id)
                ).scalar_one_or_none()
                if job:
                    job.failed_images = job.failed_images + 1
                    # Only mark job as failed if all images have been processed
                    if job.processed_images + job.failed_images >= job.total_images:
                        job.status = JobStatus.FAILED.value
                        job.completed_at = datetime.now(UTC)
                        job.error_message = str(exc)
                session.commit()
            except Exception:
                session.rollback()

            publish_job_failed(job_id, str(exc))

            # Retry with exponential backoff for transient errors
            backoff = 2 ** self.request.retries * 30
            raise self.retry(exc=exc, countdown=backoff)
