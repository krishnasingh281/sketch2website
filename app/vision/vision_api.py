import os
from google.cloud import vision
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def extract_text_from_image(image_path):
    """Extracts text from an image using Google Vision API."""
    
    # The GOOGLE_APPLICATION_CREDENTIALS environment variable should 
    # directly point to the JSON file - no need to parse it
    client = vision.ImageAnnotatorClient()

    with open(image_path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations

    return texts[0].description if texts else "No text found in the image"