from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import make_password
from rest_framework import status
from django.shortcuts import render, redirect
from django.contrib import messages

User = get_user_model()

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


@api_view(['POST'])
def login_user(request):
    data = request.data
    username_or_email = data.get('username')  # This can be username or email
    password = data.get('password')

    # Find user by username or email
    user = User.objects.filter(username=username_or_email).first() or User.objects.filter(email=username_or_email).first()

    if user and user.check_password(password):
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)

    return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)



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
