import logging

import boto3
from botocore.config import Config as BotoConfig

from ml.services.bedrock_client import invoke_claude
from shared.config import get_settings
from shared.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)
settings = get_settings()


DESCRIPTION_PROMPT_TEMPLATE = """You are an expert e-commerce copywriter. Generate a professional product listing description based on the following AI-analyzed product information.

**Product Category:** {category}

**Detected Attributes:**
{attributes_text}

**Defects Found:**
{defects_text}

**Instructions:**
- Write a compelling, accurate product description suitable for an e-commerce listing
- Length: 150-250 words
- Tone: Professional but approachable
- Include the product category, key attributes (color, material, condition)
- If defects were found, mention them honestly but diplomatically
- End with a brief value proposition
- Do NOT include a title/heading, just the description body
- Do NOT use markdown formatting

Generate the product description:"""


def format_attributes(attributes: list[dict]) -> str:
    if not attributes:
        return "No attributes detected"
    lines = []
    for attr in attributes:
        conf = f" (confidence: {attr['confidence']:.0%})" if attr.get("confidence") else ""
        lines.append(f"- {attr['name'].replace('_', ' ').title()}: {attr['value']}{conf}")
    return "\n".join(lines)


def format_defects(defects: list[dict]) -> str:
    if not defects:
        return "No defects detected"
    lines = []
    for defect in defects:
        severity = defect.get("severity", "unknown")
        conf = f" (confidence: {defect['confidence']:.0%})" if defect.get("confidence") else ""
        lines.append(f"- {defect['type'].replace('_', ' ').title()} ({severity} severity){conf}")
    return "\n".join(lines)


def download_image_bytes(s3_bucket: str, s3_key: str) -> bytes:
    """Download image from S3 for Bedrock vision input."""
    kwargs = {
        "service_name": "s3",
        "region_name": settings.aws_region,
        "aws_access_key_id": settings.aws_access_key_id,
        "aws_secret_access_key": settings.aws_secret_access_key,
        "config": BotoConfig(signature_version="s3v4"),
    }
    if settings.s3_endpoint_url:
        kwargs["endpoint_url"] = settings.s3_endpoint_url
    s3 = boto3.client(**kwargs)
    response = s3.get_object(Bucket=s3_bucket, Key=s3_key)
    return response["Body"].read()


def generate_description(
    category: str,
    attributes: list[dict],
    defects: list[dict],
    s3_bucket: str,
    s3_key: str,
) -> dict:
    """
    Generate an AI product description using AWS Bedrock (Claude).

    Args:
        category: Product category from classification
        attributes: List of extracted attributes
        defects: List of detected defects
        s3_bucket: S3 bucket containing the product image
        s3_key: S3 key for the product image

    Returns:
        dict with keys: description, model
    """
    prompt = DESCRIPTION_PROMPT_TEMPLATE.format(
        category=category,
        attributes_text=format_attributes(attributes),
        defects_text=format_defects(defects),
    )

    try:
        # Download image for vision input
        image_bytes = download_image_bytes(s3_bucket, s3_key)

        # Call Claude via Bedrock with both image and text
        description = invoke_claude(
            prompt=prompt,
            image_bytes=image_bytes,
            max_tokens=1024,
        )

        return {
            "description": description.strip(),
            "model": settings.bedrock_model_id,
        }

    except ExternalServiceError:
        raise
    except Exception as e:
        logger.exception(f"Description generation failed: {e}")
        # Fallback: generate without image
        try:
            description = invoke_claude(prompt=prompt, max_tokens=1024)
            return {
                "description": description.strip(),
                "model": settings.bedrock_model_id,
            }
        except Exception:
            # Final fallback: template-based description
            return generate_fallback_description(category, attributes, defects)


def generate_fallback_description(
    category: str,
    attributes: list[dict],
    defects: list[dict],
) -> dict:
    """Generate a simple template-based description when Bedrock is unavailable."""
    attr_map = {a["name"]: a["value"] for a in attributes}
    color = attr_map.get("color", "")
    material = attr_map.get("material", "")
    condition = attr_map.get("condition", "good")

    parts = [f"This {color} {material} {category} product is in {condition} condition."]

    if not defects:
        parts.append("No defects were detected during quality inspection.")
    else:
        defect_types = [d["type"].replace("_", " ") for d in defects]
        parts.append(f"Minor imperfections noted: {', '.join(defect_types)}.")

    parts.append("A great addition to your collection at excellent value.")

    return {
        "description": " ".join(parts),
        "model": "fallback-template",
    }
