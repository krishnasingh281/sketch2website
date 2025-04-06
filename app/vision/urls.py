# app/app/urls.py
# (Update this path if your URLs are in a different location)

from django.urls import path
from . import views

urlpatterns = [
    path('api/wireframes/', views.WireframeUploadAPIView.as_view(), name='wireframe-upload'),
    path('api/wireframes/user/', views.user_wireframes_api, name='user-wireframes'),
    path('api/wireframes/<int:pk>/', views.wireframe_detail_api, name='wireframe-detail'),
    path('api/wireframes/<int:pk>/code/', views.generate_code_api, name='wireframe-code'),
    path('api/test-gemini/', views.test_gemini_connection_api, name='test-gemini'),
]