import uuid

from django.db import models


class AnalysisResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_image = models.OneToOneField(
        "products.ProductImage", on_delete=models.CASCADE, related_name="analysis_result"
    )
    model_version = models.CharField(max_length=50)
    classification_label = models.CharField(max_length=100, blank=True, null=True)
    classification_confidence = models.FloatField(blank=True, null=True)
    classification_scores = models.JSONField(default=dict)
    description_text = models.TextField(blank=True, null=True)
    description_model = models.CharField(max_length=100, blank=True, null=True)
    processing_time_ms = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=20, default="pending")
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "analysis_results"
        ordering = ["-created_at"]
        verbose_name = "Analysis Result"
        verbose_name_plural = "Analysis Results"

    def __str__(self):
        return f"{self.classification_label or 'Pending'} ({self.status})"


class ExtractedAttribute(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analysis_result = models.ForeignKey(
        AnalysisResult, on_delete=models.CASCADE, related_name="extracted_attributes"
    )
    attribute_name = models.CharField(max_length=100)
    attribute_value = models.CharField(max_length=500)
    confidence = models.FloatField(blank=True, null=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        managed = False
        db_table = "extracted_attributes"
        verbose_name = "Extracted Attribute"
        verbose_name_plural = "Extracted Attributes"

    def __str__(self):
        return f"{self.attribute_name}: {self.attribute_value}"


class DetectedDefect(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analysis_result = models.ForeignKey(
        AnalysisResult, on_delete=models.CASCADE, related_name="detected_defects"
    )
    defect_type = models.CharField(max_length=100)
    severity = models.CharField(max_length=20)
    confidence = models.FloatField(blank=True, null=True)
    bounding_box = models.JSONField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "detected_defects"
        verbose_name = "Detected Defect"
        verbose_name_plural = "Detected Defects"

    def __str__(self):
        return f"{self.defect_type} ({self.severity})"
