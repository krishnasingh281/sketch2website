from rest_framework import serializers
from .models import User
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
User = get_user_model()

class UserSeriailzer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username','email', 'password', 'profile_picture','bio', 'first_name', 'last_name']
        read_only_fields = ('id',) 
        
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'profile_picture')
        extra_kwargs = {'email': {'required': True}}

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password': 'Passwords do not match'})
        return data

    def create(self, validated_data):
        # Remove password2 from the validated data
        validated_data.pop('password2')

        # Create user instance without saving password yet
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            profile_picture=validated_data.get('profile_picture')
        )
        user.set_password(validated_data['password'])  # Proper password hashing
        user.save()
        return user
    
class LoginSerializer(serializers.Serializer):  # Changed to Serializer since we're not using model fields
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            # Get the user first by email
            try:
                user = User.objects.get(email=email)
                # Then authenticate with username and password
                authenticated_user = authenticate(username=user.username, password=password)
                if authenticated_user is None:
                    # Use a generic error message for security
                    raise serializers.ValidationError('Invalid credentials')
                
                if not authenticated_user.is_active:
                    raise serializers.ValidationError('User account is disabled')
                
                attrs['user'] = authenticated_user
                return attrs
            except User.DoesNotExist:
                # Same generic error to prevent email enumeration
                raise serializers.ValidationError('Invalid credentials')
        else:
            raise serializers.ValidationError('Must include "email" and "password"')