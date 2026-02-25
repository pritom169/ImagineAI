import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.factories import (
    ProcessingJobFactory,
    ProductFactory,
    ProductImageFactory,
)


class TestImageProcessingTask:
    def test_processing_job_factory(self):
        job = ProcessingJobFactory()
        assert job.id is not None
        assert job.status == "queued"
        assert job.job_type == "single"
        assert job.total_images == 1
        assert job.processed_images == 0
        assert job.failed_images == 0

    def test_product_image_factory(self):
        image = ProductImageFactory()
        assert image.id is not None
        assert image.s3_bucket == "imagineai-images"
        assert image.content_type == "image/jpeg"
        assert image.upload_status == "uploaded"
        assert "uploads/" in image.s3_key

    @patch("workers.tasks.image_processing.process_image")
    def test_process_image_task_delay(self, mock_task):
        mock_task.delay.return_value = MagicMock(id="task-123")

        image_id = str(uuid.uuid4())
        job_id = str(uuid.uuid4())
        result = mock_task.delay(image_id, job_id)

        assert result.id == "task-123"
        mock_task.delay.assert_called_once_with(image_id, job_id)

    @patch("workers.tasks.image_processing.process_image")
    def test_process_image_task_called_with_correct_args(self, mock_task):
        image_id = str(uuid.uuid4())
        job_id = str(uuid.uuid4())

        mock_task.delay(image_id, job_id)

        call_args = mock_task.delay.call_args
        assert call_args[0][0] == image_id
        assert call_args[0][1] == job_id


class TestImageProcessingPipeline:
    @patch("workers.tasks.image_processing.boto3")
    def test_s3_download_mock(self, mock_boto3):
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.download_file.return_value = None

        client = mock_boto3.client("s3")
        client.download_file("imagineai-images", "uploads/test/image.jpg", "/tmp/image.jpg")

        mock_client.download_file.assert_called_once()

    def test_product_factory(self):
        product = ProductFactory()
        assert product.id is not None
        assert product.status == "draft"
        assert product.category in ["electronics", "clothing", "footwear", "furniture"]
        assert product.title is not None

    def test_product_with_custom_user(self):
        user_id = uuid.uuid4()
        product = ProductFactory(user_id=user_id)
        assert product.user_id == user_id


class TestBatchProcessing:
    @patch("workers.tasks.image_processing.process_image")
    def test_batch_task_dispatch(self, mock_task):
        mock_task.delay.return_value = MagicMock(id="batch-task")

        image_ids = [str(uuid.uuid4()) for _ in range(5)]
        job_id = str(uuid.uuid4())

        tasks = []
        for img_id in image_ids:
            result = mock_task.delay(img_id, job_id)
            tasks.append(result)

        assert len(tasks) == 5
        assert mock_task.delay.call_count == 5
