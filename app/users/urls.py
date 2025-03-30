from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import register_user, login_user, RegisterView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', login_user, name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
   
]
