import os
import json
import re
import logging
import time
from pathlib import Path
from django.conf import settings
import google.generativeai as genai
from dotenv import load_dotenv

# Set up logger
logger = logging.getLogger(__name__)

def load_api_key():
    """Load Gemini API key from multiple possible sources"""
    # Try to load from environment directly first
    api_key = os.environ.get('GOOGLE_GEMINI_API_KEY')
    
    # If not found, check if we have credentials JSON file
    if not api_key:
        try:
            # Look for credentials file in the vision app directory
            credentials_path = Path(__file__).parent / 'google_credentials.json'
            if credentials_path.exists():
                with open(credentials_path, 'r') as f:
                    credentials = json.load(f)
                    api_key = credentials.get('api_key')
                    if api_key:
                        print("API key loaded from google_credentials.json")
        except Exception as e:
            print(f"Error loading credentials file: {str(e)}")
    
    # If still not found, try loading from .env file
    if not api_key:
        try:
            # First, try loading from app directory
            app_dir = Path(__file__).parent
            env_path = app_dir / '.env'
            
            # If not there, try project root
            if not env_path.exists():
                project_root = Path(__file__).resolve().parent.parent.parent
                env_path = project_root / '.env'
            
            if env_path.exists():
                load_dotenv(env_path)
                api_key = os.environ.get('GOOGLE_GEMINI_API_KEY')
                if api_key:
                    print(f"API key loaded from .env file at {env_path}")
        except Exception as e:
            print(f"Error loading .env file: {str(e)}")
    
    # If still not found, check Django settings
    if not api_key and hasattr(settings, 'GOOGLE_GEMINI_API_KEY'):
        api_key = settings.GOOGLE_GEMINI_API_KEY
        if api_key:
            print("API key loaded from Django settings")
    
    if not api_key:
        print("API key not found in any configuration")
        
    return api_key

def test_gemini_connection():
    """Test the connection to Gemini API with retries"""
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            api_key = load_api_key()
            if not api_key:
                return {"status": "error", "message": "API key not found in configuration"}
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name="gemini-2.0-flash")

            
            # Removed timeout parameter which was causing the error
            response = model.generate_content(
                "Hello, please respond with 'API connection successful'"
            )
            
            return {"status": "success", "message": response.text}
            
        except Exception as e:
            logger.warning(f"Connection attempt {attempt+1}/{max_retries} failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed to connect to Gemini API after {max_retries} attempts")
                return {"status": "error", "message": f"Connection failed: {str(e)}"}

def generate_code_from_wireframe(detected_elements):
    """
    Uses Google's Gemini API to generate HTML/CSS code from detected wireframe elements.
    
    Args:
        detected_elements (dict): The structured data from Vision API containing UI elements
        
    Returns:
        dict: Contains the generated HTML and CSS code, or error information
    """
    try:
        # Get API key using our enhanced function
        api_key = load_api_key()
        if not api_key:
            raise ValueError("GOOGLE_GEMINI_API_KEY environment variable not set and not found in Django settings")
        
        # Configure the Gemini API
        genai.configure(api_key=api_key)
        
        # Create the model
        model = genai.GenerativeModel(model_name="gemini-2.0-flash")

        
        # Prepare the prompt with the detected elements
        prompt = construct_gemini_prompt(detected_elements)
        
        # Generate response from Gemini
        response = model.generate_content(prompt)
        
        # Extract HTML and CSS from the response
        if hasattr(response, 'text'):
            response_text = response.text
        else:
            # Handle different response format for newer API versions
            response_text = response.parts[0].text if hasattr(response, 'parts') else str(response)
        
        generated_code = parse_gemini_response(response_text)
        
        return {
            'status': 'success',
            'html': generated_code.get('html', ''),
            'css': generated_code.get('css', ''),
            'javascript': generated_code.get('javascript', ''),
        }
    
    except Exception as e:
        print(f"Error in Gemini code generation: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }

def construct_gemini_prompt(detected_elements):
    """
    Constructs an effective prompt for Gemini to generate code from wireframe elements.
    
    Args:
        detected_elements (dict): The structured data from Vision API
        
    Returns:
        str: A well-structured prompt for the Gemini API
    """
 
    elements = detected_elements.get('elements', [])
    full_text = detected_elements.get('full_text', '')
    
   
    nav_elements = [e for e in elements if e.get('type') == 'navbar']
    buttons = [e for e in elements if e.get('type') == 'button']
    input_fields = [e for e in elements if e.get('type') == 'input_field']
    headings = [e for e in elements if e.get('type') == 'heading']
    paragraphs = [e for e in elements if e.get('type') == 'paragraph']
    other_elements = [e for e in elements if e.get('type') not in ['navbar', 'button', 'input_field', 'heading', 'paragraph']]
    
    
    prompt = f"""
    As an expert web developer, generate responsive HTML, CSS, and JavaScript code based on these wireframe elements detected from an image.
    
    Here's the full text detected in the wireframe:
    ```
    {full_text}
    ```
    
    Here are the UI elements detected, organized by type:
    
    Navigation Elements:
    ```
    {json.dumps(nav_elements, indent=2)}
    ```
    
    Buttons:
    ```
    {json.dumps(buttons, indent=2)}
    ```
    
    Input Fields:
    ```
    {json.dumps(input_fields, indent=2)}
    ```
    
    Headings:
    ```
    {json.dumps(headings, indent=2)}
    ```
    
    Paragraphs:
    ```
    {json.dumps(paragraphs, indent=2)}
    ```
    
    Other Elements:
    ```
    {json.dumps(other_elements, indent=2)}
    ```
    
    Please generate:
      1. Clean, semantic HTML5 code using appropriate tags (<header>, <nav>, <main>, <section>, <footer>, etc.)
      2. Modern CSS using Flexbox or Grid for layout and responsive design
      3. Any necessary JavaScript for interactive elements, including dark mode toggle

    Follow these guidelines:
      - Create a responsive layout that works on mobile and desktop
      - Position elements according to their relative positions in the wireframe or provided layout
      - Match text content exactly where appropriate
      - Use semantic HTML5 elements and follow accessibility best practices (e.g., ARIA roles, labels)
      - Add appropriate validation for form fields (both HTML5 and JS if needed)
      - Use modern CSS techniques:
      - CSS variables for theming
      - Flexbox and/or Grid for layout
      - Mobile-first media queries
      - Smooth transitions for interactive elements

    Additional Requirement:
      - Implement a Dark Mode toggle using CSS variables and JavaScript
      - Use a button or switch for toggling
      - Store user preference using localStorage
      - Ensure smooth transitions between light and dark themes


    Return your response in the following format:
    
    HTML:
    ```html
    (your HTML code here)
    ```
    
    CSS:
    ```css
    (your CSS code here)
    ```
    
    JavaScript (if needed):
    ```javascript
    (your JavaScript code here)
    ```
    """
    
    return prompt

def parse_gemini_response(response_text):
    """
    Parses the Gemini response to extract HTML, CSS, and JavaScript code.
    
    Args:
        response_text (str): The text response from Gemini
    
    Returns:
        dict: Contains separated HTML, CSS, and JavaScript code
    """
    result = {
        'html': '',
        'css': '',
        'javascript': ''
    }
    
    # Extract HTML
    html_match = re.search(r'```html\s+(.*?)\s+```', response_text, re.DOTALL)
    if html_match:
        result['html'] = html_match.group(1).strip()
    
    # Extract CSS
    css_match = re.search(r'```css\s+(.*?)\s+```', response_text, re.DOTALL)
    if css_match:
        result['css'] = css_match.group(1).strip()
    
    # Extract JavaScript
    js_match = re.search(r'```javascript\s+(.*?)\s+```', response_text, re.DOTALL)
    if js_match:
        result['javascript'] = js_match.group(1).strip()
    
    return result