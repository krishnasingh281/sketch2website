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
                        logger.info("API key loaded from google_credentials.json")
        except Exception as e:
            logger.error(f"Error loading credentials file: {str(e)}")
    
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
                    logger.info(f"API key loaded from .env file at {env_path}")
        except Exception as e:
            logger.error(f"Error loading .env file: {str(e)}")
    
    # If still not found, check Django settings
    if not api_key and hasattr(settings, 'GOOGLE_GEMINI_API_KEY'):
        api_key = settings.GOOGLE_GEMINI_API_KEY
        if api_key:
            logger.info("API key loaded from Django settings")
    
    if not api_key:
        logger.warning("API key not found in any configuration")
        
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
            
            # Keep using flash model as specified
            model = genai.GenerativeModel(model_name="gemini-2.0-flash")
            
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
        
        # Create the model - using Flash as specified for speed
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",  # Using Flash as requested
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,           # Lower temperature for more deterministic code
                top_p=0.95,                # Control diversity
                top_k=40,                  # Another diversity control
                max_output_tokens=8192,    # Allow for longer responses
                stop_sequences=[]          # No early stopping
            ),
            safety_settings=[
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        )
        
        # Prepare the prompt with the detected elements
        prompt = construct_gemini_prompt(detected_elements)
        
        # Add retry logic for more reliability
        max_retries = 3
        retry_delay = 2
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Generate response from Gemini
                response = model.generate_content(prompt)
                
                # Extract HTML and CSS from the response
                if hasattr(response, 'text'):
                    response_text = response.text
                else:
                    # Handle different response format for newer API versions
                    response_text = response.parts[0].text if hasattr(response, 'parts') else str(response)
                
                generated_code = parse_gemini_response(response_text)
                
                # Validate that we got useful code responses
                if not generated_code.get('html').strip():
                    raise ValueError("Generated HTML is empty - retrying")
                
                return {
                    'status': 'success',
                    'html': generated_code.get('html', ''),
                    'css': generated_code.get('css', ''),
                    'javascript': generated_code.get('javascript', ''),
                }
            except Exception as e:
                last_error = e
                logger.warning(f"Generation attempt {attempt+1}/{max_retries} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        
        # If we get here, all attempts failed
        raise last_error or ValueError("Failed to generate code after multiple attempts")
    
    except Exception as e:
        logger.error(f"Error in Gemini code generation: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }

def construct_gemini_prompt(detected_elements):
    """
    Constructs an effective prompt for Gemini to generate code from wireframe elements.
    Optimized for flash model to get better results while maintaining speed.
    
    Args:
        detected_elements (dict): The structured data from Vision API
        
    Returns:
        str: A well-structured prompt for the Gemini API
    """
    # Extract elements by type
    elements = detected_elements.get('elements', [])
    full_text = detected_elements.get('full_text', '')
    
    # Organize elements by type for better presentation to the model
    nav_elements = [e for e in elements if e.get('type') == 'navbar']
    buttons = [e for e in elements if e.get('type') == 'button']
    input_fields = [e for e in elements if e.get('type') == 'input_field']
    headings = [e for e in elements if e.get('type') == 'heading']
    paragraphs = [e for e in elements if e.get('type') == 'paragraph']
    images = [e for e in elements if e.get('type') == 'image']
    forms = [e for e in elements if e.get('type') == 'form']
    other_elements = [e for e in elements if e.get('type') not in [
        'navbar', 'button', 'input_field', 'heading', 'paragraph', 'image', 'form'
    ]]
    
    # Build enhanced prompt optimized for flash model
    prompt = f"""
    As an expert front-end developer, generate clean, responsive HTML, CSS, and JavaScript code based on these wireframe elements.
    
    DETECTED TEXT IN WIREFRAME:
    ```
    {full_text}
    ```
    
    DETECTED UI ELEMENTS:
    
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
    
    Images:
    ```
    {json.dumps(images, indent=2)}
    ```
    
    Forms:
    ```
    {json.dumps(forms, indent=2)}
    ```
    
    Other Elements:
    ```
    {json.dumps(other_elements, indent=2)}
    ```
    
    CODE REQUIREMENTS:
    1. Use semantic HTML5 (header, nav, main, section, footer, etc.)
    2. Create responsive design with CSS Grid and Flexbox
    3. Add clean, modern styling with consistent spacing
    4. Include proper form validation with JavaScript 
    5. Add hover states and transitions for interactive elements
    6. Ensure mobile compatibility with media queries
    7. Use CSS variables for consistent theming
    8. Add appropriate accessibility attributes
    9. Use modern ES6+ JavaScript syntax
    10. Create pixel-perfect implementation of the wireframe
    
    OUTPUT FORMAT:
    Return ONLY code blocks with no explanations outside the blocks:
    
    HTML:
    ```html
    (your complete HTML code here)
    ```
    
    CSS:
    ```css
    (your complete CSS code here)
    ```
    
    JavaScript:
    ```javascript
    (your complete JavaScript code here)
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
    
    # More robust pattern matching with different code block styles
    # Extract HTML - handle both ```html and ```HTML variations
    html_pattern = r'```(?:html|HTML)\s+(.*?)\s+```'
    html_match = re.search(html_pattern, response_text, re.DOTALL)
    if html_match:
        result['html'] = html_match.group(1).strip()
    
    # If no HTML match with explicit language, try to find the first code block
    if not result['html']:
        first_code_block = re.search(r'```\s+(<!DOCTYPE html>.*?)\s+```', response_text, re.DOTALL)
        if first_code_block:
            result['html'] = first_code_block.group(1).strip()
    
    # Extract CSS
    css_pattern = r'```(?:css|CSS)\s+(.*?)\s+```'
    css_match = re.search(css_pattern, response_text, re.DOTALL)
    if css_match:
        result['css'] = css_match.group(1).strip()
    
    # Extract JavaScript
    js_pattern = r'```(?:javascript|JAVASCRIPT|js|JS)\s+(.*?)\s+```'
    js_match = re.search(js_pattern, response_text, re.DOTALL)
    if js_match:
        result['javascript'] = js_match.group(1).strip()
    
    # Fallback for CSS and JS if not found with language tags
    if not result['css'] and '<style>' in response_text and '</style>' in response_text:
        css_match = re.search(r'<style>(.*?)</style>', response_text, re.DOTALL)
        if css_match:
            result['css'] = css_match.group(1).strip()
    
    if not result['javascript'] and '<script>' in response_text and '</script>' in response_text:
        js_match = re.search(r'<script>(.*?)</script>', response_text, re.DOTALL)
        if js_match:
            result['javascript'] = js_match.group(1).strip()
    
    return result