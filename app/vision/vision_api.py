from google.cloud import vision
import io

def extract_text_from_image(image_path):
    """Extracts text from an image using Google Vision API."""
    client = vision.ImageAnnotatorClient()

    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()
    
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations

    if texts:
        return texts[0].description  # Extracted text
    else:
        return "No text found in the image"
