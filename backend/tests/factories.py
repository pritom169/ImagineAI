import uuid
from datetime import UTC, datetime

import factory

from shared.models.analysis import AnalysisResult, DetectedDefect, ExtractedAttribute
from shared.models.pipeline import JobStep, ProcessingJob
from shared.models.product import Product, ProductImage
from shared.models.user import User
from fastapi_app.services.auth_service import hash_password


class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = factory.LazyFunction(uuid.uuid4)
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    hashed_password = factory.LazyFunction(lambda: hash_password("testpass123"))
    full_name = factory.Faker("name")
    is_active = True
    is_superuser = False
    is_staff = False


class ProductFactory(factory.Factory):
    class Meta:
        model = Product

    id = factory.LazyFunction(uuid.uuid4)
    user_id = factory.LazyFunction(uuid.uuid4)
    title = factory.Faker("catch_phrase")
    description = factory.Faker("paragraph")
    category = factory.Iterator(["electronics", "clothing", "footwear", "furniture"])
    status = "draft"


class ProductImageFactory(factory.Factory):
    class Meta:
        model = ProductImage

    id = factory.LazyFunction(uuid.uuid4)
    product_id = factory.LazyFunction(uuid.uuid4)
    s3_key = factory.LazyAttribute(lambda o: f"uploads/{uuid.uuid4()}/image.jpg")
    s3_bucket = "imagineai-images"
    original_filename = factory.Faker("file_name", extension="jpg")
    content_type = "image/jpeg"
    file_size_bytes = factory.Faker("random_int", min=100000, max=5000000)
    upload_status = "uploaded"


class AnalysisResultFactory(factory.Factory):
    class Meta:
        model = AnalysisResult

    id = factory.LazyFunction(uuid.uuid4)
    product_image_id = factory.LazyFunction(uuid.uuid4)
    model_version = "efficientnet-b4-v1"
    classification_label = factory.Iterator(["electronics", "clothing", "footwear"])
    classification_confidence = factory.Faker("pyfloat", min_value=0.5, max_value=0.99)
    classification_scores = factory.LazyFunction(dict)
    status = "completed"
    processing_time_ms = factory.Faker("random_int", min=500, max=5000)


class ExtractedAttributeFactory(factory.Factory):
    class Meta:
        model = ExtractedAttribute

    id = factory.LazyFunction(uuid.uuid4)
    analysis_result_id = factory.LazyFunction(uuid.uuid4)
    attribute_name = factory.Iterator(["color", "material", "condition"])
    attribute_value = factory.Iterator(["blue", "leather", "new"])
    confidence = factory.Faker("pyfloat", min_value=0.4, max_value=0.95)


class DetectedDefectFactory(factory.Factory):
    class Meta:
        model = DetectedDefect

    id = factory.LazyFunction(uuid.uuid4)
    analysis_result_id = factory.LazyFunction(uuid.uuid4)
    defect_type = factory.Iterator(["scratch", "dent", "discoloration"])
    severity = factory.Iterator(["low", "medium", "high"])
    confidence = factory.Faker("pyfloat", min_value=0.3, max_value=0.9)
    bounding_box = factory.LazyFunction(lambda: {"x": 0.1, "y": 0.2, "width": 0.3, "height": 0.1})


class ProcessingJobFactory(factory.Factory):
    class Meta:
        model = ProcessingJob

    id = factory.LazyFunction(uuid.uuid4)
    user_id = factory.LazyFunction(uuid.uuid4)
    job_type = "single"
    status = "queued"
    total_images = 1
    processed_images = 0
    failed_images = 0
