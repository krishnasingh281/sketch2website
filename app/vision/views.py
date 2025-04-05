# app/vision/views.py

import os
import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import WireframeUpload
from .forms import ImageUploadForm
from .serializers import WireframeUploadSerializer
from .vision_api import detect_wireframe_elements

# Web form view for wireframe uploads (unchanged)
def upload_wireframe(request):
    """View for handling wireframe uploads via web form"""
    if request.method == "POST":
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Create wireframe upload instance but don't save yet
            wireframe = form.save(commit=False)
            wireframe.user = request.user
            wireframe.status = 'processing'
            wireframe.save()
            
            # Process image with Vision API
            try:
                detected_elements = detect_wireframe_elements(wireframe.image.path)
                wireframe.detected_elements = detected_elements
                wireframe.status = 'completed'
            except Exception as e:
                wireframe.status = 'failed'
                print(f"Error processing wireframe: {e}")
            
            wireframe.save()
            return redirect('wireframe_detail', pk=wireframe.pk)
    else:
        form = ImageUploadForm()
    
    return render(request, "vision/upload.html", {"form": form})

@login_required
def wireframe_detail(request, pk):
    """View for displaying wireframe processing results"""
    try:
        wireframe = WireframeUpload.objects.get(pk=pk, user=request.user)
        return render(request, "vision/detail.html", {"wireframe": wireframe})
    except WireframeUpload.DoesNotExist:
        return redirect('upload_wireframe')

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_upload_wireframe(request):
    """API endpoint for wireframe uploads"""
    serializer = WireframeUploadSerializer(
        data=request.data, 
        context={'request': request}
    )
    
    if serializer.is_valid():
        wireframe = serializer.save()
        
        # Process image with Vision API
        try:
            detected_elements = detect_wireframe_elements(wireframe.image.path)
            wireframe.detected_elements = detected_elements
            wireframe.status = 'completed'
        except Exception as e:
            wireframe.status = 'failed'
            print(f"Error processing wireframe: {e}")
        
        wireframe.save()
        
        # Return updated data
        return Response(
            WireframeUploadSerializer(wireframe).data,
            status=status.HTTP_201_CREATED
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)