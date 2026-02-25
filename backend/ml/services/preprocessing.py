import io
import logging

import boto3
import torch
from botocore.config import Config as BotoConfig
from PIL import Image
from torchvision import transforms

from ml.config import CLASSIFICATION_INPUT_SIZE
from shared.config import get_settings
from shared.exceptions import StorageError

logger = logging.getLogger(__name__)
settings = get_settings()

# Standard ImageNet preprocessing pipeline
preprocess_transform = transforms.Compose([
    transforms.Resize((CLASSIFICATION_INPUT_SIZE, CLASSIFICATION_INPUT_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def get_s3_client():
    kwargs = {
        "service_name": "s3",
        "region_name": settings.aws_region,
        "aws_access_key_id": settings.aws_access_key_id,
        "aws_secret_access_key": settings.aws_secret_access_key,
        "config": BotoConfig(signature_version="s3v4"),
    }
    if settings.s3_endpoint_url:
        kwargs["endpoint_url"] = settings.s3_endpoint_url
    return boto3.client(**kwargs)


def download_and_preprocess(s3_bucket: str, s3_key: str) -> torch.Tensor:
    """
    Download image from S3 and preprocess for model inference.

    Returns:
        Tensor of shape (1, 3, H, W) ready for model input
    """
    logger.info(f"Downloading image from s3://{s3_bucket}/{s3_key}")

    try:
        s3 = get_s3_client()
        response = s3.get_object(Bucket=s3_bucket, Key=s3_key)
        image_bytes = response["Body"].read()
    except Exception as e:
        raise StorageError(f"Failed to download image from S3: {e}")

    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        raise StorageError(f"Failed to open image: {e}")

    logger.info(f"Image size: {image.size}, preprocessing for inference")

    # Apply transforms and add batch dimension
    tensor = preprocess_transform(image).unsqueeze(0)

    return tensor


def preprocess_from_bytes(image_bytes: bytes) -> torch.Tensor:
    """Preprocess image from raw bytes."""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return preprocess_transform(image).unsqueeze(0)
