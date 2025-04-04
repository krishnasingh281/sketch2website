# vision/serializers.py
from rest_framework import serializers
from .models import WireframeUpload

class WireframeUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = WireframeUpload
        fields = ['id', 'image', 'upload_date', 'status', 'detected_elements']
        read_only_fields = ['id', 'upload_date', 'status', 'detected_elements']
        
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['status'] = 'processing'
        return super().create(validated_data)