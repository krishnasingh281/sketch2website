from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import make_password
from rest_framework import status, generics
from rest_framework.throttling import AnonRateThrottle
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import render, redirect
from django.contrib import messages
from .serializers import UserSeriailzer, RegisterSerializer, LoginSerializer

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # No need to create AlumniProfile here - it's handled in the serializer
        
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSeriailzer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def register_user(request):
    data = request.data

    # Check if username or email already exists
    if User.objects.filter(username=data['username']).exists():
        return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(email=data.get('email', '')).exists():
        return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)

    # Create user with email
    user = User.objects.create(
        username=data['username'],
        email=data.get('email', ''),  # Ensure email is stored
        password=make_password(data['password'])
    )

    return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)


from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny


class LoginView(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            tokens = RefreshToken.for_user(user)
            return Response({
                "refresh": str(tokens),
                "access": str(tokens.access_token),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email
                }
            })
        else:
            print("🚨 Validation Errors:", serializer.errors)  # Debugging
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def logout_user(request):
    try:
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist() 

        return Response({"message": "User logged out successfully"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    
from rest_framework.permissions import IsAuthenticated

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    user = request.user
    return Response({
        "id": user.id,
        "username": user.username,
        "email": user.email
    })






# def register_user(request):
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         email = request.POST.get('email')
#         password = request.POST.get('password')

#         if not username or not email or not password:
#             messages.error(request, 'All fields are required!')
#             return render(request, 'users/register.html')

#         if User.objects.filter(username=username).exists():
#             messages.error(request, 'Username already taken!')
#             return render(request, 'users/register.html')

#         user = User.objects.create_user(username=username, email=email, password=password)
#         messages.success(request, 'Registration successful! You can now login.')
#         return redirect('login')

#     return render(request, 'users/register.html')
