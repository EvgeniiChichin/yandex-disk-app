from django.urls import path

from .views import FileView


urlpatterns = [
    path("", FileView.as_view(), name="home"),
    path("download/", FileView.as_view(), name="download_multiple_files"),
]
