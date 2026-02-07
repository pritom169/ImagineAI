import logging
import random
import uuid

from ml.config import AB_TEST_PERCENTAGE

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Registry for ML model versioning and A/B test routing.

    Supports DB-backed experiments via ABExperiment/ABVariant models,
    with fallback to in-memory config for standalone usage.
    """

    def __init__(self):
        self._versions: dict[str, dict] = {
            "classifier": {
                "v1": {"name": "efficientnet-b4-v1", "weight": 100 - AB_TEST_PERCENTAGE},
                "v2": {"name": "efficientnet-b4-v2", "weight": AB_TEST_PERCENTAGE},
            },
            "feature_extractor": {
                "v1": {"name": "feature-extractor-v1", "weight": 100},
            },
            "defect_detector": {
                "v1": {"name": "defect-detector-v1", "weight": 100},
            },
        }

    def get_version(self, model_type: str) -> str:
        """Get the model version to use, factoring in A/B test weights."""
        versions = self._versions.get(model_type, {})
        if not versions:
            return "v1"

        choices = list(versions.keys())
        weights = [versions[v]["weight"] for v in choices]
        total = sum(weights)
        if total == 0:
            return choices[0]

        rand = random.uniform(0, total)
        cumulative = 0
        for choice, weight in zip(choices, weights):
            cumulative += weight
            if rand <= cumulative:
                return choice
        return choices[-1]

    def get_model_name(self, model_type: str, version: str | None = None) -> str:
        """Get the human-readable model name for a given type and version."""
        if version is None:
            version = self.get_version(model_type)
        versions = self._versions.get(model_type, {})
        return versions.get(version, {}).get("name", f"{model_type}-{version}")

    def get_model_version_for_user(
        self, model_type: str, user_id: str, session=None
    ) -> tuple[str, str | None, str | None]:
        """
        Get the model version for a specific user, with persistent cohort assignment.

        Returns (version_string, experiment_id, variant_id).
        Falls back to weighted random if DB is unavailable.
        """
        if session is None:
            version = self.get_version(model_type)
            return version, None, None

        try:
            from sqlalchemy import select
            from shared.models.ab_testing import ABExperiment, ABVariant, UserCohortAssignment

            uid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id

            # Check for existing cohort assignment
            existing = session.execute(
                select(UserCohortAssignment)
                .join(ABExperiment, UserCohortAssignment.experiment_id == ABExperiment.id)
                .where(
                    UserCohortAssignment.user_id == uid,
                    ABExperiment.model_type == model_type,
                    ABExperiment.is_active.is_(True),
                )
            ).scalar_one_or_none()

            if existing:
                variant = session.get(ABVariant, existing.variant_id)
                if variant:
                    return (
                        variant.model_version,
                        str(existing.experiment_id),
                        str(existing.variant_id),
                    )

            # Find active experiment for this model type
            experiment = session.execute(
                select(ABExperiment).where(
                    ABExperiment.model_type == model_type,
                    ABExperiment.is_active.is_(True),
                )
            ).scalar_one_or_none()

            if not experiment:
                version = self.get_version(model_type)
                return version, None, None

            # Get variants and do weighted selection
            variants = session.execute(
                select(ABVariant).where(ABVariant.experiment_id == experiment.id)
            ).scalars().all()

            if not variants:
                version = self.get_version(model_type)
                return version, None, None

            choices = list(variants)
            weights = [v.weight for v in choices]
            total = sum(weights)
            if total == 0:
                selected = choices[0]
            else:
                rand = random.uniform(0, total)
                cumulative = 0
                selected = choices[-1]
                for variant in choices:
                    cumulative += variant.weight
                    if rand <= cumulative:
                        selected = variant
                        break

            # Persist cohort assignment
            assignment = UserCohortAssignment(
                user_id=uid,
                experiment_id=experiment.id,
                variant_id=selected.id,
            )
            session.add(assignment)
            session.flush()

            return (
                selected.model_version,
                str(experiment.id),
                str(selected.id),
            )

        except Exception as e:
            logger.warning(f"Failed to get DB-backed model version, falling back: {e}")
            version = self.get_version(model_type)
            return version, None, None

    def register_version(self, model_type: str, version: str, name: str, weight: int = 0):
        """Register a new model version."""
        if model_type not in self._versions:
            self._versions[model_type] = {}
        self._versions[model_type][version] = {"name": name, "weight": weight}
        logger.info(f"Registered model {model_type}/{version}: {name} (weight={weight})")

    def set_ab_weight(self, model_type: str, version: str, weight: int):
        """Update the A/B test weight for a model version."""
        if model_type in self._versions and version in self._versions[model_type]:
            self._versions[model_type][version]["weight"] = weight
            logger.info(f"Updated A/B weight for {model_type}/{version}: {weight}%")


# Singleton instance
registry = ModelRegistry()
