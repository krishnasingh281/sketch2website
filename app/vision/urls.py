from django.urls import path
from .views import (
    WireframeUploadAPIView,
    wireframe_detail_api,
    user_wireframes_api
)

# URL patterns for the wireframe API endpoints
urlpatterns = [
    # Upload a new wireframe
    path('api/wireframes/upload/', WireframeUploadAPIView.as_view(), name='wireframe_upload_api'),
    
    # Get details of a specific wireframe
    path('api/wireframes/<int:pk>/', wireframe_detail_api, name='wireframe_detail_api'),
    
    # List all wireframes for the current user
    path('api/wireframes/', user_wireframes_api, name='user_wireframes_api'),
]