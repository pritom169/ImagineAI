import logging

import torch

from ml.models.classifier import classify_image
from ml.models.defect_detector import detect_defects
from ml.models.feature_extractor import extract_attributes
from ml.models.model_registry import registry

logger = logging.getLogger(__name__)


def run_classification(image_tensor: torch.Tensor, version: str = "v1") -> dict:
    """Run product classification on preprocessed image tensor."""
    logger.info(f"Running product classification (version={version})...")
    result = classify_image(image_tensor, version=version)
    logger.info(f"Classification result: {result['label']} ({result['confidence']:.4f})")
    return result


def run_attribute_extraction(image_tensor: torch.Tensor, version: str = "v1") -> list[dict]:
    """Run attribute extraction on preprocessed image tensor."""
    logger.info(f"Running attribute extraction (version={version})...")
    attributes = extract_attributes(image_tensor, version=version)
    logger.info(f"Extracted {len(attributes)} attributes")
    return attributes


def run_defect_detection(image_tensor: torch.Tensor, version: str = "v1") -> list[dict]:
    """Run defect detection on preprocessed image tensor."""
    logger.info(f"Running defect detection (version={version})...")
    defects = detect_defects(image_tensor, version=version)
    logger.info(f"Detected {len(defects)} defects")
    return defects


def run_full_pipeline(
    image_tensor: torch.Tensor,
    user_id: str | None = None,
    session=None,
) -> dict:
    """
    Run the complete ML inference pipeline with A/B test version selection.

    Returns:
        dict with classification, attributes, defects, and experiment tracking info
    """
    # Determine model versions via registry (with A/B testing)
    clf_version, experiment_id, variant_id = registry.get_model_version_for_user(
        "classifier", user_id, session
    ) if user_id else ("v1", None, None)

    fe_version, _, _ = registry.get_model_version_for_user(
        "feature_extractor", user_id, session
    ) if user_id else ("v1", None, None)

    dd_version, _, _ = registry.get_model_version_for_user(
        "defect_detector", user_id, session
    ) if user_id else ("v1", None, None)

    classification = run_classification(image_tensor, version=clf_version)
    attributes = run_attribute_extraction(image_tensor, version=fe_version)
    defects = run_defect_detection(image_tensor, version=dd_version)

    return {
        "classification": classification,
        "attributes": attributes,
        "defects": defects,
        "experiment_id": experiment_id,
        "variant_id": variant_id,
    }
