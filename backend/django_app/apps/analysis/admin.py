from django.contrib import admin
from django.utils.html import format_html

from .models import AnalysisResult, DetectedDefect, ExtractedAttribute


class ExtractedAttributeInline(admin.TabularInline):
    model = ExtractedAttribute
    extra = 0
    readonly_fields = ("attribute_name", "attribute_value", "confidence")
    fields = ("attribute_name", "attribute_value", "confidence")

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class DetectedDefectInline(admin.TabularInline):
    model = DetectedDefect
    extra = 0
    readonly_fields = ("defect_type", "severity", "confidence", "bounding_box", "description")
    fields = ("defect_type", "severity", "confidence", "description")

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ("product_image", "classification_label", "confidence_display",
                    "status_badge", "processing_time_display", "created_at")
    list_filter = ("status", "classification_label", "model_version")
    search_fields = ("product_image__original_filename", "classification_label")
    readonly_fields = ("id", "product_image", "model_version", "classification_label",
                       "classification_confidence", "classification_scores",
                       "description_text", "description_model", "processing_time_ms",
                       "status", "error_message", "created_at", "updated_at")
    ordering = ("-created_at",)
    inlines = [ExtractedAttributeInline, DetectedDefectInline]

    fieldsets = (
        (None, {"fields": ("id", "product_image", "status", "model_version")}),
        ("Classification", {"fields": ("classification_label", "classification_confidence",
                                       "classification_scores")}),
        ("Description", {"fields": ("description_text", "description_model")}),
        ("Performance", {"fields": ("processing_time_ms",)}),
        ("Error", {"fields": ("error_message",), "classes": ("collapse",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def has_add_permission(self, request):
        return False

    def confidence_display(self, obj):
        if obj.classification_confidence:
            pct = obj.classification_confidence * 100
            color = "#28a745" if pct > 80 else "#ffc107" if pct > 50 else "#dc3545"
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
                color, pct,
            )
        return "-"
    confidence_display.short_description = "Confidence"

    def status_badge(self, obj):
        colors = {
            "completed": "#28a745",
            "processing": "#007bff",
            "pending": "#6c757d",
            "failed": "#dc3545",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.status.upper(),
        )
    status_badge.short_description = "Status"

    def processing_time_display(self, obj):
        if obj.processing_time_ms:
            if obj.processing_time_ms < 1000:
                return f"{obj.processing_time_ms}ms"
            return f"{obj.processing_time_ms / 1000:.1f}s"
        return "-"
    processing_time_display.short_description = "Duration"
