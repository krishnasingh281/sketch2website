# app/app/serializers.py
# (Update this path if your serializers are in a different location)

from rest_framework import serializers
from .models import WireframeUpload

class WireframeUploadSerializer(serializers.ModelSerializer):
    """Serializer for wireframe uploads"""
    
    username = serializers.ReadOnlyField(source='user.username')
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = WireframeUpload
        fields = [
            'id', 'title', 'description', 'image', 'image_url',
            'upload_date', 'status', 'username', 'detected_elements',
            'generated_code'
        ]
        read_only_fields = ['user', 'upload_date', 'status', 'detected_elements', 'generated_code']
    
    def get_image_url(self, obj):
        """Get the URL for the image"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None