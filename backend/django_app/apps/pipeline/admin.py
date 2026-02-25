from django.contrib import admin
from django.utils.html import format_html

from .models import JobStep, ProcessingJob


class JobStepInline(admin.TabularInline):
    model = JobStep
    extra = 0
    readonly_fields = ("step_name", "status_badge", "duration_display",
                       "started_at", "completed_at", "error_message")
    fields = ("step_name", "status_badge", "duration_display", "started_at", "completed_at")

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def status_badge(self, obj):
        colors = {
            "completed": "#28a745",
            "running": "#007bff",
            "pending": "#6c757d",
            "failed": "#dc3545",
            "skipped": "#ffc107",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.status.upper(),
        )
    status_badge.short_description = "Status"

    def duration_display(self, obj):
        if obj.duration_ms:
            if obj.duration_ms < 1000:
                return f"{obj.duration_ms}ms"
            return f"{obj.duration_ms / 1000:.1f}s"
        return "-"
    duration_display.short_description = "Duration"


@admin.register(ProcessingJob)
class ProcessingJobAdmin(admin.ModelAdmin):
    list_display = ("id_short", "user", "job_type", "status_badge", "progress_bar",
                    "started_at", "completed_at")
    list_filter = ("status", "job_type", "created_at")
    search_fields = ("id", "user__email", "celery_task_id")
    readonly_fields = ("id", "user", "job_type", "status", "total_images",
                       "processed_images", "failed_images", "celery_task_id",
                       "started_at", "completed_at", "error_message",
                       "created_at", "updated_at")
    ordering = ("-created_at",)
    inlines = [JobStepInline]

    fieldsets = (
        (None, {"fields": ("id", "user", "job_type", "status")}),
        ("Progress", {"fields": ("total_images", "processed_images", "failed_images")}),
        ("Celery", {"fields": ("celery_task_id",)}),
        ("Timing", {"fields": ("started_at", "completed_at")}),
        ("Error", {"fields": ("error_message",), "classes": ("collapse",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def has_add_permission(self, request):
        return False

    def id_short(self, obj):
        return str(obj.id)[:8] + "..."
    id_short.short_description = "Job ID"

    def status_badge(self, obj):
        colors = {
            "completed": "#28a745",
            "processing": "#007bff",
            "queued": "#6c757d",
            "failed": "#dc3545",
            "cancelled": "#ffc107",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.status.upper(),
        )
    status_badge.short_description = "Status"

    def progress_bar(self, obj):
        pct = obj.progress_percentage
        color = "#28a745" if pct == 100 else "#007bff" if pct > 0 else "#6c757d"
        return format_html(
            '<div style="width: 100px; background: #e9ecef; border-radius: 3px;">'
            '<div style="width: {}%; background: {}; height: 18px; border-radius: 3px; '
            'text-align: center; color: white; font-size: 11px; line-height: 18px;">'
            '{}/{}</div></div>',
            max(pct, 8), color, obj.processed_images, obj.total_images,
        )
    progress_bar.short_description = "Progress"
