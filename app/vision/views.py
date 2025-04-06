import os
import json
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from .models import WireframeUpload
from .serializers import WireframeUploadSerializer
from vision.vision_api import detect_wireframe_elements
from vision.gemini_api import generate_code_from_wireframe
from .formatter import beautify_code

class WireframeUploadAPIView(generics.CreateAPIView):
    """API endpoint for wireframe uploads using DRF generic views"""
    serializer_class = WireframeUploadSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        # Save the wireframe with user from request
        wireframe = serializer.save(user=self.request.user, status='processing')
        
        # Process image with Vision API
        try:
            # Step 1: Detect elements with Vision API
            detected_elements = detect_wireframe_elements(wireframe.image.path)
            wireframe.detected_elements = detected_elements
            
            # Step 2: Generate code with Gemini API
            generated_code = generate_code_from_wireframe(detected_elements)
            wireframe.generated_code = generated_code
            
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_code_api(request, pk):
    """API endpoint for generating/retrieving code for a specific wireframe"""
    try:
        wireframe = WireframeUpload.objects.get(pk=pk, user=request.user)
        
        # Check if code has already been generated
        if not wireframe.generated_code or 'status' in wireframe.generated_code and wireframe.generated_code['status'] == 'error':
            # Generate code if not already available
            if wireframe.detected_elements:
                wireframe.generated_code = generate_code_from_wireframe(wireframe.detected_elements)
                wireframe.save()
            else:
                return Response(
                    {"error": "No detected elements available for this wireframe"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Pretty print response, split html/css for better readability
        generated = wireframe.generated_code or {}
        html_code = generated.get("html", "")
        css_code = generated.get("css", "")

        formatted = beautify_code(html_code, css_code)
        return Response({
        "status": "success",
        "html": formatted["html"],
        "css": formatted["css"]
        }, status=status.HTTP_200_OK)

    except WireframeUpload.DoesNotExist:
        return Response(
            {"error": "Wireframe not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )

        
@api_view(['GET'])
def test_gemini_connection_api(request):
    """API endpoint for testing Gemini API connection"""
    from vision.gemini_api import test_gemini_connection
    result = test_gemini_connection()
    return Response(result)