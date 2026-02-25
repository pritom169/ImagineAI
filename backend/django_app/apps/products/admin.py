from django.contrib import admin
from django.utils.html import format_html

from .models import Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    readonly_fields = ("id", "s3_key", "s3_bucket", "original_filename", "content_type",
                       "file_size_bytes", "upload_status", "created_at", "image_preview")
    fields = ("image_preview", "original_filename", "content_type", "file_size_bytes",
              "is_primary", "upload_status", "created_at")

    def image_preview(self, obj):
        if obj.s3_key:
            return format_html(
                '<span style="color: #666; font-size: 12px;">{}</span>',
                obj.s3_key.split("/")[-1],
            )
        return "-"
    image_preview.short_description = "File"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "category", "status", "image_count_display", "created_at")
    list_filter = ("status", "category", "created_at")
    search_fields = ("title", "description", "user__email")
    readonly_fields = ("id", "ai_description", "created_at", "updated_at")
    ordering = ("-created_at",)
    inlines = [ProductImageInline]

    fieldsets = (
        (None, {"fields": ("id", "user", "title", "description")}),
        ("Classification", {"fields": ("category", "subcategory", "status")}),
        ("AI Generated", {"fields": ("ai_description",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def image_count_display(self, obj):
        count = obj.images.count()
        return format_html('<span style="font-weight: bold;">{}</span>', count)
    image_count_display.short_description = "Images"


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "product", "content_type", "file_size_display",
                    "upload_status", "is_primary", "created_at")
    list_filter = ("upload_status", "content_type", "is_primary")
    search_fields = ("original_filename", "s3_key", "product__title")
    readonly_fields = ("id", "s3_key", "s3_bucket", "created_at")

    def file_size_display(self, obj):
        if obj.file_size_bytes:
            if obj.file_size_bytes < 1024:
                return f"{obj.file_size_bytes} B"
            elif obj.file_size_bytes < 1024 * 1024:
                return f"{obj.file_size_bytes / 1024:.1f} KB"
            else:
                return f"{obj.file_size_bytes / (1024 * 1024):.1f} MB"
        return "-"
    file_size_display.short_description = "File Size"
