import os
from django.shortcuts import render
from google.cloud import vision
from .forms import ImageUploadForm
from .vision_api import extract_text_from_image

def upload_image(request):
    extracted_text = None

    if request.method == "POST":
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            image = request.FILES["image"]

            # Save image temporarily
            image_path = f"media/{image.name}"
            with open(image_path, "wb+") as destination:
                for chunk in image.chunks():
                    destination.write(chunk)

            # Process image with Google Vision API
            extracted_text = extract_text_from_image(image_path)

            # Clean up temp image
            os.remove(image_path)

    else:
        form = ImageUploadForm()

    return render(request, "vision/upload.html", {"form": form, "extracted_text": extracted_text})
