import uuid

from django.db import models


class ProcessingJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="processing_jobs"
    )
    job_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20, default="queued")
    total_images = models.IntegerField(default=0)
    processed_images = models.IntegerField(default=0)
    failed_images = models.IntegerField(default=0)
    celery_task_id = models.CharField(max_length=255, blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "processing_jobs"
        ordering = ["-created_at"]
        verbose_name = "Processing Job"
        verbose_name_plural = "Processing Jobs"

    def __str__(self):
        return f"Job {self.id} ({self.status})"

    @property
    def progress_percentage(self):
        if self.total_images == 0:
            return 0
        return round((self.processed_images / self.total_images) * 100)


class JobStep(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(ProcessingJob, on_delete=models.CASCADE, related_name="steps")
    product_image = models.ForeignKey(
        "products.ProductImage", on_delete=models.SET_NULL, null=True, blank=True
    )
    step_name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default="pending")
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    duration_ms = models.IntegerField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    result_data = models.JSONField(default=dict)

    class Meta:
        managed = False
        db_table = "job_steps"
        ordering = ["step_name"]
        verbose_name = "Job Step"
        verbose_name_plural = "Job Steps"

    def __str__(self):
        return f"{self.step_name} ({self.status})"
