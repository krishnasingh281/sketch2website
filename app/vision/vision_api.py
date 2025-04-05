import os
import io
from google.cloud import vision
from google.cloud.vision_v1 import types
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

def detect_wireframe_elements(image_path):
    """
    Detects UI elements from a wireframe using Google Vision API.
    Returns structured data about the detected elements.
    """
    # Set the credentials file path explicitly
    credentials_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'google_credentials.json')
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
    
    try:
        # Initialize the client
        client = vision.ImageAnnotatorClient()
        
        # Read image file
        with io.open(image_path, 'rb') as image_file:
            content = image_file.read()

        image = vision.Image(content=content)
        
        # Get text annotations (for labels, buttons, text fields)
        text_response = client.text_detection(image=image)
        
        # Get object localization (for UI components like buttons, input fields)
        object_response = client.object_localization(image=image)
        
        # Process text detections
        texts = text_response.text_annotations
        
        # Extract UI elements based on text and location
        ui_elements = []
        
        # Process the first text annotation which contains all text
        full_text = ""
        if texts:
            full_text = texts[0].description
            
            # Process individual text blocks (after the first full-text item)
            for text in texts[1:]:
                # Get the bounding polygon
                vertices = [(vertex.x, vertex.y) for vertex in text.bounding_poly.vertices]
                
                # Calculate width and height
                width = max(vertices[1][0], vertices[2][0]) - min(vertices[0][0], vertices[3][0])
                height = max(vertices[2][1], vertices[3][1]) - min(vertices[0][1], vertices[1][1])
                
                # Determine the type of UI element based on text and dimensions
                element_type = classify_ui_element(text.description, width, height)
                
                ui_elements.append({
                    'type': element_type,
                    'text': text.description,
                    'position': {
                        'x': vertices[0][0],
                        'y': vertices[0][1]
                    },
                    'width': width,
                    'height': height
                })
        
        # Process object localizations
        for obj in object_response.localized_object_annotations:
            ui_elements.append({
                'type': 'object',
                'name': obj.name,
                'confidence': obj.score,
                'bounding_box': {
                    'x': obj.bounding_poly.normalized_vertices[0].x,
                    'y': obj.bounding_poly.normalized_vertices[0].y,
                    'width': (obj.bounding_poly.normalized_vertices[1].x - obj.bounding_poly.normalized_vertices[0].x),
                    'height': (obj.bounding_poly.normalized_vertices[2].y - obj.bounding_poly.normalized_vertices[0].y)
                }
            })
        
        # Return detected UI elements and full text
        return {
            'elements': ui_elements,
            'full_text': full_text
        }
    except Exception as e:
        print(f"Error in Vision API processing: {str(e)}")
        return {
            'elements': [],
            'full_text': '',
            'error': str(e)
        }

def classify_ui_element(text, width, height):
    """
    Attempt to classify a UI element based on its text and dimensions.
    """
    text_lower = text.lower()
    
    # Check for navigation elements
    if any(nav in text_lower for nav in ['nav', 'menu', 'home', 'about', 'contact']):
        if width > height * 3:  # Horizontal nav
            return 'navbar'
        return 'menu'
    
    # Check for buttons
    if any(btn in text_lower for btn in ['submit', 'send', 'login', 'sign', 'create', 'delete', 'update']):
        return 'button'
    
    # Check for form fields
    if any(field in text_lower for field in ['name', 'email', 'password', 'username', 'address']):
        return 'input_field'
    
    # Check for headers
    if len(text) < 50 and height < 40:
        return 'heading'
    
    # Default to paragraph for longer text
    if len(text) > 50:
        return 'paragraph'
    
    # Default
    return 'text'