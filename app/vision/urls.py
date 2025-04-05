# app/vision/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_wireframe, name='upload_wireframe'),
    path('wireframe/<int:pk>/', views.wireframe_detail, name='wireframe_detail'),
    path('api/upload/', views.api_upload_wireframe, name='api_upload_wireframe'),
]