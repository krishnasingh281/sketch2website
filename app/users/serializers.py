from rest_framework import serializers
from .models import User
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
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