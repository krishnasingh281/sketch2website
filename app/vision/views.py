from django.shortcuts import render
from .forms import ImageUploadForm
from google.cloud import vision
import os

# Set the path to your Google Cloud service account key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "app/google_vision_key.json"

def upload_image(request):
    extracted_text = None  # Default value

    if request.method == "POST":
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            image = request.FILES["image"]
            
            # Save the image temporarily
            image_path = f"media/{image.name}"
            with open(image_path, "wb+") as destination:
                for chunk in image.chunks():
                    destination.write(chunk)

            # Process the image using Google Vision API
            client = vision.ImageAnnotatorClient()
            with open(image_path, "rb") as image_file:
                content = image_file.read()
                image = vision.Image(content=content)

            response = client.text_detection(image=image)
            extracted_text = response.text_annotations[0].description if response.text_annotations else "No text found"

    else:
        form = ImageUploadForm()

    return render(request, "vision/upload.html", {"form": form, "extracted_text": extracted_text})

