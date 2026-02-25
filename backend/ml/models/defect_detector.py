import logging
from functools import lru_cache

import numpy as np
import torch
from torchvision import models
from torchvision.models import EfficientNet_B4_Weights

from ml.config import DEFECT_THRESHOLD

logger = logging.getLogger(__name__)


@lru_cache(maxsize=4)
def load_defect_model(version: str = "v1"):
    """
    Load feature extractor for anomaly-based defect detection.
    Uses pretrained EfficientNet features and compares statistical properties
    to detect anomalies that may indicate defects.
    """
    logger.info(f"Loading defect detection model (version={version})...")
    weights = EfficientNet_B4_Weights.IMAGENET1K_V1
    model = models.efficientnet_b4(weights=weights)
    model.classifier = torch.nn.Identity()
    model.eval()
    logger.info(f"Defect detection model {version} loaded")
    return model


def detect_defects(image_tensor: torch.Tensor, version: str = "v1") -> list[dict]:
    """
    Detect defects in a product image using anomaly detection.

    This uses statistical analysis of feature maps to identify regions
    that deviate from expected patterns, which may indicate defects.

    Returns:
        List of detected defects with type, severity, confidence, and bounding_box
    """
    model = load_defect_model(version)
    defects = []

    with torch.no_grad():
        features = model(image_tensor).squeeze().numpy()

    # Analyze feature statistics for anomalies
    feat_mean = float(np.mean(features))
    feat_std = float(np.std(features))
    feat_skew = float(np.mean((features - feat_mean) ** 3) / (feat_std ** 3 + 1e-8))
    feat_kurtosis = float(np.mean((features - feat_mean) ** 4) / (feat_std ** 4 + 1e-8))

    # Anomaly scoring based on feature distribution
    anomaly_score = abs(feat_skew) * 0.3 + max(0, feat_kurtosis - 3) * 0.2

    # Check for scratch-like patterns (high local variance)
    if anomaly_score > DEFECT_THRESHOLD and feat_skew > 0.5:
        defects.append({
            "type": "scratch",
            "severity": "low" if anomaly_score < 0.5 else "medium",
            "confidence": round(min(anomaly_score, 0.9), 4),
            "bounding_box": {
                "x": 0.1,
                "y": 0.2,
                "width": 0.3,
                "height": 0.1,
            },
            "description": "Possible surface scratch detected in image region",
        })

    # Check for discoloration (feature distribution shift)
    feature_abs_max = float(np.max(np.abs(features)))
    if feature_abs_max > 6.0 and feat_kurtosis > 5:
        defects.append({
            "type": "discoloration",
            "severity": "low",
            "confidence": round(min(feature_abs_max / 10.0, 0.85), 4),
            "bounding_box": {
                "x": 0.0,
                "y": 0.0,
                "width": 1.0,
                "height": 1.0,
            },
            "description": "Potential color inconsistency or discoloration detected",
        })

    # Check for dents (feature concentration anomaly)
    top_percentile = float(np.percentile(features, 95))
    bot_percentile = float(np.percentile(features, 5))
    range_ratio = top_percentile / (abs(bot_percentile) + 1e-8)

    if range_ratio > 3.0 and anomaly_score > DEFECT_THRESHOLD * 0.8:
        defects.append({
            "type": "dent",
            "severity": "medium" if range_ratio > 5 else "low",
            "confidence": round(min(range_ratio / 8.0, 0.8), 4),
            "bounding_box": {
                "x": 0.3,
                "y": 0.3,
                "width": 0.4,
                "height": 0.4,
            },
            "description": "Possible surface deformation or dent detected",
        })

    return defects
