import base64
import io
import json
import logging
import time

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

from shared.config import get_settings
from shared.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)
settings = get_settings()


def get_bedrock_client():
    kwargs = {
        "service_name": "bedrock-runtime",
        "region_name": settings.bedrock_region,
        "aws_access_key_id": settings.aws_access_key_id,
        "aws_secret_access_key": settings.aws_secret_access_key,
        "config": BotoConfig(
            retries={"max_attempts": 3, "mode": "adaptive"},
            read_timeout=60,
        ),
    }
    return boto3.client(**kwargs)


def invoke_claude(
    prompt: str,
    image_bytes: bytes | None = None,
    content_type: str = "image/jpeg",
    max_tokens: int = 1024,
) -> str:
    """
    Invoke Claude via AWS Bedrock.

    Args:
        prompt: Text prompt for Claude
        image_bytes: Optional image bytes to include in the request
        content_type: MIME type of the image
        max_tokens: Maximum tokens in response

    Returns:
        Claude's text response
    """
    client = get_bedrock_client()

    # Build message content
    content = []

    if image_bytes:
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        media_type = content_type if content_type in ("image/jpeg", "image/png", "image/webp", "image/gif") else "image/jpeg"
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": image_b64,
            },
        })

    content.append({"type": "text", "text": prompt})

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": content}],
        "temperature": 0.3,
    })

    try:
        start_time = time.time()
        response = client.invoke_model(
            modelId=settings.bedrock_model_id,
            body=body,
            contentType="application/json",
        )
        elapsed = time.time() - start_time
        logger.info(f"Bedrock invocation took {elapsed:.2f}s")

        response_body = json.loads(response["body"].read())
        return response_body["content"][0]["text"]

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_msg = e.response["Error"]["Message"]
        logger.error(f"Bedrock error ({error_code}): {error_msg}")
        raise ExternalServiceError("AWS Bedrock", f"{error_code}: {error_msg}")
    except Exception as e:
        logger.exception(f"Unexpected Bedrock error: {e}")
        raise ExternalServiceError("AWS Bedrock", str(e))
