"""
URL configuration for knowledge_system project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('learning_logs.urls')),
]

# Custom admin titles
admin.site.site_header = "Personal Knowledge & Log Management System"
admin.site.site_title = "Knowledge Admin Portal"
admin.site.index_title = "System Management & Database Administration"
