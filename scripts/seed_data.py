"""
Seed data script for ImagineAI development environment.

Creates demo users, products, images, analysis results, and processing jobs.
Designed to be run inside the FastAPI Docker container:

    docker compose exec fastapi python scripts/seed_data.py

Or via the Makefile:

    make seed
"""

import asyncio
import sys
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# ---------------------------------------------------------------------------
# Bootstrap: ensure the backend package is on sys.path when executed as a
# standalone script inside the container (PYTHONPATH=/app/backend).
# ---------------------------------------------------------------------------
sys.path.insert(0, "/app/backend")

from fastapi_app.services.auth_service import hash_password
from shared.config import get_settings
from shared.database import async_session_factory, engine
from shared.models import (
    AnalysisResult,
    Base,
    DetectedDefect,
    ExtractedAttribute,
    ProcessingJob,
    JobStep,
    Product,
    ProductImage,
    User,
)

settings = get_settings()

# ---------------------------------------------------------------------------
# Seed data definitions
# ---------------------------------------------------------------------------

USERS = [
    {
        "email": "admin@imagineai.com",
        "password": "admin123456",
        "full_name": "Admin User",
        "is_superuser": True,
        "is_staff": True,
    },
    {
        "email": "demo@imagineai.com",
        "password": "demo12345678",
        "full_name": "Demo User",
        "is_superuser": False,
        "is_staff": False,
    },
    {
        "email": "test@imagineai.com",
        "password": "test12345678",
        "full_name": "Test User",
        "is_superuser": False,
        "is_staff": False,
    },
]

PRODUCTS = [
    # Electronics (3)
    {
        "title": "Wireless Bluetooth Headphones",
        "description": "Premium over-ear headphones with active noise cancellation.",
        "category": "electronics",
        "subcategory": "audio",
        "status": "active",
    },
    {
        "title": "Mechanical Keyboard RGB",
        "description": "Full-size mechanical keyboard with Cherry MX switches and RGB backlighting.",
        "category": "electronics",
        "subcategory": "peripherals",
        "status": "active",
    },
    {
        "title": "Portable Bluetooth Speaker",
        "description": "Waterproof portable speaker with 12-hour battery life.",
        "category": "electronics",
        "subcategory": "audio",
        "status": "processing",
    },
    # Clothing (3)
    {
        "title": "Cotton Crew Neck T-Shirt",
        "description": "Classic fit cotton t-shirt available in multiple colors.",
        "category": "clothing",
        "subcategory": "tops",
        "status": "active",
    },
    {
        "title": "Denim Slim Fit Jeans",
        "description": "Stretch denim jeans with a modern slim fit.",
        "category": "clothing",
        "subcategory": "bottoms",
        "status": "active",
    },
    {
        "title": "Wool Blend Blazer",
        "description": "Tailored wool-blend blazer suitable for business and casual wear.",
        "category": "clothing",
        "subcategory": "outerwear",
        "status": "draft",
    },
    # Footwear (2)
    {
        "title": "Running Shoes Pro",
        "description": "Lightweight running shoes with responsive cushioning.",
        "category": "footwear",
        "subcategory": "athletic",
        "status": "active",
    },
    {
        "title": "Leather Chelsea Boots",
        "description": "Genuine leather Chelsea boots with elastic side panel.",
        "category": "footwear",
        "subcategory": "boots",
        "status": "active",
    },
    # Furniture (2)
    {
        "title": "Ergonomic Office Chair",
        "description": "Adjustable office chair with lumbar support and breathable mesh.",
        "category": "furniture",
        "subcategory": "seating",
        "status": "active",
    },
    {
        "title": "Solid Oak Coffee Table",
        "description": "Mid-century modern coffee table crafted from solid oak.",
        "category": "furniture",
        "subcategory": "tables",
        "status": "draft",
    },
]

# Per-product image definitions: list of (original_filename, content_type, is_primary)
PRODUCT_IMAGES = [
    # Product 0: Headphones
    [("headphones_front.jpg", "image/jpeg", True), ("headphones_side.jpg", "image/jpeg", False)],
    # Product 1: Keyboard
    [("keyboard_top.jpg", "image/jpeg", True), ("keyboard_rgb.png", "image/png", False), ("keyboard_side.jpg", "image/jpeg", False)],
    # Product 2: Speaker
    [("speaker_front.jpg", "image/jpeg", True), ("speaker_outdoor.jpg", "image/jpeg", False)],
    # Product 3: T-Shirt
    [("tshirt_front.jpg", "image/jpeg", True), ("tshirt_back.jpg", "image/jpeg", False), ("tshirt_detail.jpg", "image/jpeg", False)],
    # Product 4: Jeans
    [("jeans_front.jpg", "image/jpeg", True), ("jeans_back.jpg", "image/jpeg", False)],
    # Product 5: Blazer
    [("blazer_front.jpg", "image/jpeg", True), ("blazer_detail.jpg", "image/jpeg", False)],
    # Product 6: Running Shoes
    [("shoes_side.jpg", "image/jpeg", True), ("shoes_top.jpg", "image/jpeg", False), ("shoes_sole.jpg", "image/jpeg", False)],
    # Product 7: Chelsea Boots
    [("boots_front.jpg", "image/jpeg", True), ("boots_side.jpg", "image/jpeg", False)],
    # Product 8: Office Chair
    [("chair_front.jpg", "image/jpeg", True), ("chair_side.jpg", "image/jpeg", False), ("chair_back.jpg", "image/jpeg", False)],
    # Product 9: Coffee Table
    [("table_top.jpg", "image/jpeg", True), ("table_angle.jpg", "image/jpeg", False)],
]

# Classification labels for analysis results (keyed by product index)
ANALYSIS_DATA = {
    0: {"label": "headphones", "confidence": 0.96, "description": "Over-ear wireless headphones with cushioned ear cups and an adjustable headband."},
    1: {"label": "keyboard", "confidence": 0.93, "description": "Full-size mechanical keyboard with illuminated keys and a detachable cable."},
    3: {"label": "t-shirt", "confidence": 0.98, "description": "Plain crew-neck cotton t-shirt in navy blue."},
    4: {"label": "jeans", "confidence": 0.91, "description": "Dark-wash slim-fit denim jeans with five-pocket styling."},
    6: {"label": "sneakers", "confidence": 0.95, "description": "Lightweight running sneakers with a mesh upper and rubber outsole."},
    7: {"label": "boots", "confidence": 0.89, "description": "Brown leather Chelsea boots with a rounded toe and low heel."},
    8: {"label": "chair", "confidence": 0.92, "description": "Black mesh ergonomic office chair with armrests and adjustable height."},
}

# Extracted attributes for analysis results (keyed by product index)
ATTRIBUTES_DATA = {
    0: [("color", "black", 0.97), ("material", "plastic/leather", 0.88), ("condition", "new", 0.99)],
    1: [("color", "black", 0.95), ("material", "ABS plastic", 0.82), ("condition", "new", 0.98)],
    3: [("color", "navy blue", 0.96), ("material", "cotton", 0.94), ("condition", "new", 0.99)],
    4: [("color", "dark blue", 0.93), ("material", "denim", 0.97), ("condition", "new", 0.99)],
    6: [("color", "white/grey", 0.91), ("material", "mesh/rubber", 0.86), ("condition", "new", 0.99)],
    7: [("color", "brown", 0.95), ("material", "leather", 0.93), ("condition", "new", 0.98)],
    8: [("color", "black", 0.97), ("material", "mesh/nylon", 0.85), ("condition", "new", 0.99)],
}

# Defects for a subset of products (keyed by product index)
DEFECTS_DATA = {
    1: [
        {
            "defect_type": "scratch",
            "severity": "low",
            "confidence": 0.72,
            "bounding_box": {"x": 120, "y": 85, "width": 45, "height": 12},
            "description": "Minor surface scratch on the spacebar area.",
        },
    ],
    7: [
        {
            "defect_type": "scratch",
            "severity": "low",
            "confidence": 0.65,
            "bounding_box": {"x": 200, "y": 300, "width": 30, "height": 8},
            "description": "Light scuff mark on the toe cap.",
        },
        {
            "defect_type": "dent",
            "severity": "medium",
            "confidence": 0.78,
            "bounding_box": {"x": 50, "y": 150, "width": 20, "height": 20},
            "description": "Small indentation on the left heel.",
        },
    ],
}


# ---------------------------------------------------------------------------
# Seeding logic
# ---------------------------------------------------------------------------


async def check_already_seeded(session: AsyncSession) -> bool:
    """Return True if the admin user already exists."""
    result = await session.execute(select(User).where(User.email == "admin@imagineai.com"))
    return result.scalar_one_or_none() is not None


async def seed_users(session: AsyncSession) -> dict[str, User]:
    """Create demo users and return a mapping of email -> User."""
    users: dict[str, User] = {}
    for user_data in USERS:
        user = User(
            id=uuid.uuid4(),
            email=user_data["email"],
            hashed_password=hash_password(user_data["password"]),
            full_name=user_data["full_name"],
            is_superuser=user_data["is_superuser"],
            is_staff=user_data["is_staff"],
            is_active=True,
        )
        session.add(user)
        users[user.email] = user
        print(f"  [+] User: {user.email} (superuser={user.is_superuser})")

    await session.flush()
    return users


async def seed_products(
    session: AsyncSession,
    owner: User,
) -> list[Product]:
    """Create demo products assigned to the given user."""
    products: list[Product] = []
    for product_data in PRODUCTS:
        product = Product(
            id=uuid.uuid4(),
            user_id=owner.id,
            title=product_data["title"],
            description=product_data["description"],
            category=product_data["category"],
            subcategory=product_data["subcategory"],
            status=product_data["status"],
            metadata_={},
        )
        session.add(product)
        products.append(product)
        print(f"  [+] Product: {product.title} [{product.category}]")

    await session.flush()
    return products


async def seed_images(
    session: AsyncSession,
    products: list[Product],
) -> dict[int, list[ProductImage]]:
    """Create product images with fake S3 keys. Returns {product_index: [images]}."""
    images_map: dict[int, list[ProductImage]] = {}
    bucket = settings.s3_bucket_name

    for idx, product in enumerate(products):
        img_defs = PRODUCT_IMAGES[idx]
        images_map[idx] = []
        for filename, content_type, is_primary in img_defs:
            s3_key = f"products/{product.user_id}/{product.id}/{filename}"
            image = ProductImage(
                id=uuid.uuid4(),
                product_id=product.id,
                s3_key=s3_key,
                s3_bucket=bucket,
                original_filename=filename,
                content_type=content_type,
                file_size_bytes=1_500_000 + (hash(filename) % 3_000_000),
                width=1920,
                height=1080,
                is_primary=is_primary,
                upload_status="uploaded",
            )
            session.add(image)
            images_map[idx].append(image)

        print(f"  [+] {len(img_defs)} images for: {product.title}")

    await session.flush()
    return images_map


async def seed_analysis_results(
    session: AsyncSession,
    images_map: dict[int, list[ProductImage]],
) -> dict[int, AnalysisResult]:
    """Create analysis results for products that have analysis data defined."""
    results: dict[int, AnalysisResult] = {}

    for product_idx, data in ANALYSIS_DATA.items():
        # Analyze the primary (first) image of the product
        primary_image = images_map[product_idx][0]
        analysis = AnalysisResult(
            id=uuid.uuid4(),
            product_image_id=primary_image.id,
            model_version="v1.2.0",
            classification_label=data["label"],
            classification_confidence=data["confidence"],
            classification_scores={
                data["label"]: data["confidence"],
                "other": round(1.0 - data["confidence"], 4),
            },
            description_text=data["description"],
            description_model="anthropic.claude-3-5-sonnet",
            processing_time_ms=850 + (hash(data["label"]) % 1200),
            status="completed",
        )
        session.add(analysis)
        results[product_idx] = analysis
        print(f"  [+] Analysis: {data['label']} ({data['confidence']:.0%} confidence)")

    await session.flush()
    return results


async def seed_attributes(
    session: AsyncSession,
    analysis_map: dict[int, AnalysisResult],
) -> None:
    """Create extracted attributes for each analysis result."""
    count = 0
    for product_idx, attrs in ATTRIBUTES_DATA.items():
        analysis = analysis_map.get(product_idx)
        if analysis is None:
            continue
        for attr_name, attr_value, confidence in attrs:
            session.add(
                ExtractedAttribute(
                    id=uuid.uuid4(),
                    analysis_result_id=analysis.id,
                    attribute_name=attr_name,
                    attribute_value=attr_value,
                    confidence=confidence,
                    metadata_={},
                )
            )
            count += 1

    await session.flush()
    print(f"  [+] {count} extracted attributes")


async def seed_defects(
    session: AsyncSession,
    analysis_map: dict[int, AnalysisResult],
) -> None:
    """Create detected defects for a subset of analysis results."""
    count = 0
    for product_idx, defects in DEFECTS_DATA.items():
        analysis = analysis_map.get(product_idx)
        if analysis is None:
            continue
        for defect in defects:
            session.add(
                DetectedDefect(
                    id=uuid.uuid4(),
                    analysis_result_id=analysis.id,
                    defect_type=defect["defect_type"],
                    severity=defect["severity"],
                    confidence=defect["confidence"],
                    bounding_box=defect["bounding_box"],
                    description=defect["description"],
                )
            )
            count += 1

    await session.flush()
    print(f"  [+] {count} detected defects")


async def seed_processing_jobs(
    session: AsyncSession,
    demo_user: User,
    images_map: dict[int, list[ProductImage]],
) -> None:
    """Create processing jobs in various statuses."""
    now = datetime.now(UTC)

    # Job 1 -- completed batch job
    job1 = ProcessingJob(
        id=uuid.uuid4(),
        user_id=demo_user.id,
        job_type="batch",
        status="completed",
        total_images=5,
        processed_images=5,
        failed_images=0,
        celery_task_id=str(uuid.uuid4()),
        started_at=now - timedelta(hours=2),
        completed_at=now - timedelta(hours=1, minutes=45),
        metadata_={"source": "seed"},
    )
    session.add(job1)

    # Job 1 steps
    step_names = ["preprocess", "classify", "extract_attributes", "detect_defects", "generate_description"]
    for step_name in step_names:
        session.add(
            JobStep(
                id=uuid.uuid4(),
                job_id=job1.id,
                product_image_id=images_map[0][0].id,
                step_name=step_name,
                status="completed",
                started_at=now - timedelta(hours=2),
                completed_at=now - timedelta(hours=1, minutes=50),
                duration_ms=600 + (hash(step_name) % 800),
                result_data={},
            )
        )
    print("  [+] Job: batch (completed, 5/5 images)")

    # Job 2 -- currently processing
    job2 = ProcessingJob(
        id=uuid.uuid4(),
        user_id=demo_user.id,
        job_type="batch",
        status="processing",
        total_images=3,
        processed_images=1,
        failed_images=0,
        celery_task_id=str(uuid.uuid4()),
        started_at=now - timedelta(minutes=10),
        metadata_={"source": "seed"},
    )
    session.add(job2)

    for i, step_name in enumerate(step_names):
        status = "completed" if i < 2 else ("running" if i == 2 else "pending")
        session.add(
            JobStep(
                id=uuid.uuid4(),
                job_id=job2.id,
                product_image_id=images_map[2][0].id,
                step_name=step_name,
                status=status,
                started_at=now - timedelta(minutes=9) if status != "pending" else None,
                completed_at=now - timedelta(minutes=8) if status == "completed" else None,
                duration_ms=550 if status == "completed" else None,
                result_data={},
            )
        )
    print("  [+] Job: batch (processing, 1/3 images)")

    # Job 3 -- queued single job
    job3 = ProcessingJob(
        id=uuid.uuid4(),
        user_id=demo_user.id,
        job_type="single",
        status="queued",
        total_images=1,
        processed_images=0,
        failed_images=0,
        celery_task_id=None,
        started_at=None,
        metadata_={"source": "seed"},
    )
    session.add(job3)

    for step_name in step_names:
        session.add(
            JobStep(
                id=uuid.uuid4(),
                job_id=job3.id,
                product_image_id=images_map[5][0].id,
                step_name=step_name,
                status="pending",
                result_data={},
            )
        )
    print("  [+] Job: single (queued, 0/1 images)")

    await session.flush()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main() -> None:
    print("=" * 60)
    print("ImagineAI -- Database Seed Script")
    print("=" * 60)
    print()

    async with async_session_factory() as session:
        try:
            # Check idempotency
            if await check_already_seeded(session):
                print("Database already seeded (admin@imagineai.com exists). Skipping.")
                print("To re-seed, drop the database and run migrations first.")
                return

            # Seed users
            print("[1/7] Seeding users...")
            users = await seed_users(session)
            demo_user = users["demo@imagineai.com"]

            # Seed products (assigned to demo user)
            print("\n[2/7] Seeding products...")
            products = await seed_products(session, demo_user)

            # Seed product images
            print("\n[3/7] Seeding product images...")
            images_map = await seed_images(session, products)

            # Seed analysis results
            print("\n[4/7] Seeding analysis results...")
            analysis_map = await seed_analysis_results(session, images_map)

            # Seed extracted attributes
            print("\n[5/7] Seeding extracted attributes...")
            await seed_attributes(session, analysis_map)

            # Seed detected defects
            print("\n[6/7] Seeding detected defects...")
            await seed_defects(session, analysis_map)

            # Seed processing jobs
            print("\n[7/7] Seeding processing jobs...")
            await seed_processing_jobs(session, demo_user, images_map)

            # Commit all changes
            await session.commit()

            print()
            print("=" * 60)
            print("Seeding complete!")
            print()
            print("Demo credentials:")
            print(f"  Admin:  admin@imagineai.com / admin123456")
            print(f"  Demo:   demo@imagineai.com  / demo12345678")
            print(f"  Test:   test@imagineai.com   / test12345678")
            print("=" * 60)

        except Exception as e:
            await session.rollback()
            print(f"\nERROR: Seeding failed -- {e}")
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
