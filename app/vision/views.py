import os
import json
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes

from .models import WireframeUpload
from .serializers import WireframeUploadSerializer
from .vision_api import detect_wireframe_elements


class WireframeUploadAPIView(generics.CreateAPIView):
    """API endpoint for wireframe uploads using DRF generic views"""
    serializer_class = WireframeUploadSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        # Save the wireframe with user from request
        wireframe = serializer.save(user=self.request.user, status='processing')
        
        # Process image with Vision API
        try:
            detected_elements = detect_wireframe_elements(wireframe.image.path)
            wireframe.detected_elements = detected_elements
            wireframe.status = 'completed'
        except Exception as e:
            wireframe.status = 'failed'
            print(f"Error processing wireframe: {e}")
        
        wireframe.save()
    
    def create(self, request, *args, **kwargs):
        # Override create to return updated data after processing
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Get the updated instance and serialize it
        instance = WireframeUpload.objects.get(pk=serializer.instance.pk)
        return Response(
            self.get_serializer(instance).data,
            status=status.HTTP_201_CREATED
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def wireframe_detail_api(request, pk):
    """API endpoint for retrieving a specific wireframe's details"""
    try:
        wireframe = WireframeUpload.objects.get(pk=pk, user=request.user)
        serializer = WireframeUploadSerializer(wireframe)
        return Response(serializer.data)
    except WireframeUpload.DoesNotExist:
        return Response(
            {"error": "Wireframe not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_wireframes_api(request):
    """API endpoint for retrieving all wireframes belonging to the current user"""
    wireframes = WireframeUpload.objects.filter(user=request.user)
    serializer = WireframeUploadSerializer(wireframes, many=True)
    return Response(serializer.data)