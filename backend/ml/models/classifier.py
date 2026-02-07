import logging
from functools import lru_cache

import torch
import torch.nn.functional as F
from torchvision import models
from torchvision.models import EfficientNet_B4_Weights

from ml.config import IMAGENET_TO_ECOMMERCE

logger = logging.getLogger(__name__)


@lru_cache(maxsize=4)
def load_classifier(version: str = "v1"):
    """Load and cache the EfficientNet-B4 classifier with ImageNet weights."""
    logger.info(f"Loading EfficientNet-B4 classifier (version={version})...")
    weights = EfficientNet_B4_Weights.IMAGENET1K_V1
    model = models.efficientnet_b4(weights=weights)
    model.eval()

    categories = weights.meta["categories"]

    logger.info(f"Classifier {version} loaded with {len(categories)} ImageNet classes")
    return model, categories


def classify_image(image_tensor: torch.Tensor, version: str = "v1") -> dict:
    """
    Classify a preprocessed image tensor.

    Returns:
        dict with keys: label, confidence, scores, imagenet_label, model_version
    """
    model, categories = load_classifier(version)

    with torch.no_grad():
        output = model(image_tensor)
        probabilities = F.softmax(output, dim=1)

    # Get top-5 predictions
    top5_prob, top5_idx = torch.topk(probabilities, 5)
    top5_prob = top5_prob.squeeze().tolist()
    top5_idx = top5_idx.squeeze().tolist()

    # Map ImageNet class to category name
    top_imagenet_label = categories[top5_idx[0]]
    top_confidence = top5_prob[0]

    # Map to e-commerce category
    ecommerce_category = IMAGENET_TO_ECOMMERCE.get(top_imagenet_label, "other")

    # Build scores dict with top-5 for transparency
    scores = {}
    for prob, idx in zip(top5_prob, top5_idx):
        imagenet_label = categories[idx]
        ecom_cat = IMAGENET_TO_ECOMMERCE.get(imagenet_label, "other")
        scores[imagenet_label] = {
            "probability": round(prob, 4),
            "ecommerce_category": ecom_cat,
        }

    # Aggregate confidence by e-commerce category
    category_scores = {}
    all_probs = probabilities.squeeze().tolist()
    for idx, prob in enumerate(all_probs):
        if prob > 0.01:  # Filter noise
            cat = IMAGENET_TO_ECOMMERCE.get(categories[idx], "other")
            category_scores[cat] = category_scores.get(cat, 0) + prob

    return {
        "label": ecommerce_category,
        "confidence": round(top_confidence, 4),
        "scores": scores,
        "category_scores": {k: round(v, 4) for k, v in sorted(category_scores.items(), key=lambda x: x[1], reverse=True)[:5]},
        "imagenet_label": top_imagenet_label,
        "model_version": f"efficientnet-b4-{version}",
    }
