from django.contrib import admin
from django.urls import path

admin.site.site_header = "ImagineAI Administration"
admin.site.site_title = "ImagineAI Admin"
admin.site.index_title = "Dashboard"

urlpatterns = [
    path("admin/", admin.site.urls),
]
