import logging
from functools import lru_cache

import numpy as np
import torch
from torchvision import models
from torchvision.models import EfficientNet_B4_Weights

from ml.config import COLOR_NAMES, CONDITION_LEVELS, MATERIAL_NAMES

logger = logging.getLogger(__name__)


@lru_cache(maxsize=4)
def load_feature_extractor(version: str = "v1"):
    """Load EfficientNet-B4 as a feature extractor (without final classifier layer)."""
    logger.info(f"Loading feature extractor (version={version})...")
    weights = EfficientNet_B4_Weights.IMAGENET1K_V1
    model = models.efficientnet_b4(weights=weights)
    # Remove classifier to use as feature extractor
    model.classifier = torch.nn.Identity()
    model.eval()
    logger.info(f"Feature extractor {version} loaded")
    return model


def extract_color(image_tensor: torch.Tensor) -> dict:
    """
    Extract dominant color from image using average pixel analysis.
    Uses the raw image tensor before normalization for more accurate color detection.
    """
    # Denormalize the tensor (ImageNet normalization)
    mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
    std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
    img = image_tensor.squeeze() * std + mean
    img = img.clamp(0, 1)

    # Get average RGB
    avg_rgb = img.mean(dim=[1, 2]).numpy()
    r, g, b = avg_rgb

    # Simple color classification based on HSV-like rules
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    diff = max_c - min_c

    if diff < 0.1:
        if max_c < 0.2:
            color = "black"
        elif max_c > 0.8:
            color = "white"
        else:
            color = "gray"
    elif r > g and r > b:
        if g > 0.6:
            color = "yellow"
        elif g > 0.4:
            color = "orange"
        elif b > 0.4:
            color = "pink"
        else:
            color = "red"
    elif g > r and g > b:
        color = "green"
    elif b > r and b > g:
        if r > 0.4:
            color = "purple"
        else:
            color = "blue"
    elif r > 0.6 and g > 0.4 and b < 0.3:
        color = "brown"
    else:
        color = "beige"

    confidence = 0.7 + (diff * 0.3)  # Higher contrast = higher confidence
    return {"name": "color", "value": color, "confidence": round(min(confidence, 0.95), 4)}


def extract_material(features: np.ndarray) -> dict:
    """
    Estimate material from extracted features.
    Uses feature vector statistics as a heuristic proxy.
    """
    feat_std = float(np.std(features))
    feat_mean = float(np.mean(features))
    feat_max = float(np.max(features))

    if feat_std > 1.5 and feat_max > 5:
        material = "metal"
        confidence = 0.65
    elif feat_std < 0.8:
        material = "fabric"
        confidence = 0.60
    elif feat_mean > 0.5 and feat_std > 1.0:
        material = "leather"
        confidence = 0.55
    elif feat_max > 4:
        material = "plastic"
        confidence = 0.50
    elif feat_std > 1.2:
        material = "wood"
        confidence = 0.50
    else:
        material = "plastic"
        confidence = 0.45

    return {"name": "material", "value": material, "confidence": round(confidence, 4)}


def extract_condition(features: np.ndarray) -> dict:
    """Estimate product condition from feature analysis."""
    feat_var = float(np.var(features))
    feat_kurtosis = float(np.mean((features - np.mean(features)) ** 4) / (np.std(features) ** 4 + 1e-8))

    if feat_kurtosis < 3 and feat_var < 1.5:
        condition = "new"
        confidence = 0.60
    elif feat_kurtosis < 4:
        condition = "like_new"
        confidence = 0.55
    elif feat_var < 2.5:
        condition = "good"
        confidence = 0.50
    else:
        condition = "fair"
        confidence = 0.45

    return {"name": "condition", "value": condition, "confidence": round(confidence, 4)}


def extract_attributes(image_tensor: torch.Tensor, version: str = "v1") -> list[dict]:
    """
    Extract product attributes from image.

    Returns:
        List of dicts with keys: name, value, confidence
    """
    model = load_feature_extractor(version)

    with torch.no_grad():
        features = model(image_tensor).squeeze().numpy()

    attributes = [
        extract_color(image_tensor),
        extract_material(features),
        extract_condition(features),
    ]

    return attributes
