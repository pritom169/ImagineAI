import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from fastapi_app.api.deps import CurrentUser, DBSession
from shared.exceptions import NotFoundError
from shared.models.ab_testing import ABExperiment, ABVariant, UserCohortAssignment
from shared.models.analysis import AnalysisResult
from shared.schemas.ab_testing import (
    ABExperimentCreate,
    ABExperimentResponse,
    ABExperimentUpdate,
    ABVariantStats,
)

router = APIRouter()


@router.post("/experiments", response_model=ABExperimentResponse, status_code=status.HTTP_201_CREATED)
async def create_experiment(
    data: ABExperimentCreate,
    db: DBSession,
    current_user: CurrentUser,
):
    experiment = ABExperiment(
        name=data.name,
        model_type=data.model_type,
        start_date=datetime.now(UTC),
    )
    db.add(experiment)
    await db.flush()

    for variant_data in data.variants:
        variant = ABVariant(
            experiment_id=experiment.id,
            model_version=variant_data.model_version,
            weight=variant_data.weight,
            is_control=variant_data.is_control,
        )
        db.add(variant)
    await db.flush()

    await db.refresh(experiment, attribute_names=["variants"])
    return experiment


@router.get("/experiments", response_model=list[ABExperimentResponse])
async def list_experiments(
    db: DBSession,
    current_user: CurrentUser,
):
    result = await db.execute(
        select(ABExperiment)
        .options(selectinload(ABExperiment.variants))
        .order_by(ABExperiment.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/experiments/{experiment_id}", response_model=ABExperimentResponse)
async def get_experiment(
    experiment_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
):
    result = await db.execute(
        select(ABExperiment)
        .options(selectinload(ABExperiment.variants))
        .where(ABExperiment.id == experiment_id)
    )
    experiment = result.scalar_one_or_none()
    if not experiment:
        raise NotFoundError("Experiment", str(experiment_id))
    return experiment


@router.patch("/experiments/{experiment_id}", response_model=ABExperimentResponse)
async def update_experiment(
    experiment_id: uuid.UUID,
    data: ABExperimentUpdate,
    db: DBSession,
    current_user: CurrentUser,
):
    result = await db.execute(
        select(ABExperiment)
        .options(selectinload(ABExperiment.variants))
        .where(ABExperiment.id == experiment_id)
    )
    experiment = result.scalar_one_or_none()
    if not experiment:
        raise NotFoundError("Experiment", str(experiment_id))

    if data.is_active is not None:
        experiment.is_active = data.is_active
        if not data.is_active:
            experiment.end_date = datetime.now(UTC)

    await db.flush()
    await db.refresh(experiment, attribute_names=["variants"])
    return experiment


@router.delete("/experiments/{experiment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_experiment(
    experiment_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
):
    result = await db.execute(
        select(ABExperiment).where(ABExperiment.id == experiment_id)
    )
    experiment = result.scalar_one_or_none()
    if not experiment:
        raise NotFoundError("Experiment", str(experiment_id))
    await db.delete(experiment)
    await db.flush()


@router.get("/experiments/{experiment_id}/results", response_model=list[ABVariantStats])
async def get_experiment_results(
    experiment_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
):
    result = await db.execute(
        select(ABExperiment)
        .options(selectinload(ABExperiment.variants))
        .where(ABExperiment.id == experiment_id)
    )
    experiment = result.scalar_one_or_none()
    if not experiment:
        raise NotFoundError("Experiment", str(experiment_id))

    stats = []
    for variant in experiment.variants:
        # Count assignments
        count_result = await db.execute(
            select(func.count(UserCohortAssignment.id)).where(
                UserCohortAssignment.variant_id == variant.id
            )
        )
        sample_count = count_result.scalar() or 0

        # Get average confidence and processing time from analysis results
        metrics_result = await db.execute(
            select(
                func.avg(AnalysisResult.classification_confidence),
                func.avg(AnalysisResult.processing_time_ms),
            ).where(AnalysisResult.variant_id == variant.id)
        )
        row = metrics_result.one()
        avg_confidence = round(float(row[0]), 4) if row[0] else None
        avg_processing_time = round(float(row[1]), 2) if row[1] else None

        stats.append(ABVariantStats(
            variant_id=variant.id,
            model_version=variant.model_version,
            sample_count=sample_count,
            avg_confidence=avg_confidence,
            avg_processing_time_ms=avg_processing_time,
        ))

    return stats
