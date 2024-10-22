from django.urls import path

from .views import FileView


urlpatterns = [
    path("", FileView.as_view(), name="home")
]
