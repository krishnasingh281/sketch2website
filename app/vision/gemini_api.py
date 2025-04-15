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
            
            # Use Pro model for better results even in testing
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
        
        # Create the model - using Pro version for better quality code generation
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",  # Use Pro instead of Flash for better quality
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
    
    Args:
        detected_elements (dict): The structured data from Vision API
        
    Returns:
        str: A well-structured prompt for the Gemini API
    """
    # Extract elements by type
    elements = detected_elements.get('elements', [])
    full_text = detected_elements.get('full_text', '')
    
    # Determine page type/purpose to guide generation
    page_type = detect_page_type(elements, full_text)
    color_scheme = detect_color_scheme(detected_elements)
    
    # Process elements by type for better organization
    nav_elements = [e for e in elements if e.get('type') == 'navbar']
    buttons = [e for e in elements if e.get('type') == 'button']
    input_fields = [e for e in elements if e.get('type') == 'input_field']
    headings = [e for e in elements if e.get('type') == 'heading']
    paragraphs = [e for e in elements if e.get('type') == 'paragraph']
    images = [e for e in elements if e.get('type') == 'image']
    icons = [e for e in elements if e.get('type') == 'icon']
    lists = [e for e in elements if e.get('type') == 'list']
    cards = [e for e in elements if e.get('type') == 'card']
    forms = [e for e in elements if e.get('type') == 'form']
    other_elements = [e for e in elements if e.get('type') not in [
        'navbar', 'button', 'input_field', 'heading', 'paragraph', 
        'image', 'icon', 'list', 'card', 'form'
    ]]
    
    # Get layout information
    layout_info = analyze_layout(elements)
    
    # Build enhanced prompt with clear instructions and examples
    prompt = f"""
    You are an expert front-end developer specialized in turning wireframes into production-ready code. Generate high-quality, responsive HTML, CSS and JavaScript based on these detected wireframe elements.
    
    # PAGE TYPE
    This appears to be a {page_type} page.
    
    # DETECTED TEXT
    ```
    {full_text}
    ```
    
    # LAYOUT ANALYSIS
    ```
    {json.dumps(layout_info, indent=2)}
    ```
    
    # DETECTED COLOR SCHEME
    ```
    {json.dumps(color_scheme, indent=2)}
    ```
    
    # DETECTED UI ELEMENTS
    
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
    
    Icons:
    ```
    {json.dumps(icons, indent=2)}
    ```
    
    Lists:
    ```
    {json.dumps(lists, indent=2)}
    ```
    
    Cards:
    ```
    {json.dumps(cards, indent=2)}
    ```
    
    Forms:
    ```
    {json.dumps(forms, indent=2)}
    ```
    
    Other Elements:
    ```
    {json.dumps(other_elements, indent=2)}
    ```
    
    # REQUIREMENTS
    1. Create a fully functional, modern website implementation of the wireframe.
    2. Generate pixel-perfect, professional code with excellent design sensibility.
    3. Use the latest front-end best practices.
    
    # CODE SPECIFICATIONS
    
    ## HTML
    - Use semantic HTML5 tags appropriately (header, nav, main, section, article, footer, etc.)
    - Follow WCAG accessibility guidelines (proper ARIA attributes, alt text, etc.)
    - Structure the document logically based on the wireframe layout
    - Use commented sections to organize the code
    - Create properly labeled form elements with proper validation attributes
    
    ## CSS
    - Use modern CSS with variables for consistent theming
    - Implement responsive design with mobile-first approach
    - Use CSS Grid and Flexbox for layouts
    - Include media queries for different screen sizes
    - Add subtle animations and transitions where appropriate
    - Use a cohesive color scheme derived from the wireframe
    - Implement appropriate spacing using consistent padding/margin system
    - Add hover states and focus states for interactive elements
    
    ## JavaScript
    - Implement form validation
    - Add interactivity for dropdowns, modals, or toggles if present
    - Use event listeners for user interactions
    - Include any necessary animations or transitions
    - Implement responsive menu functionality
    - Use modern ES6+ syntax
    - Write clean, commented code
    
    # OUTPUT FORMAT
    Provide your code in the following sections:
    
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
    
    NO EXPLANATIONS OR COMMENTS OUTSIDE THE CODE BLOCKS. PROVIDE ONLY THE CODE BLOCKS WITH CLEAN, PROFESSIONAL CODE. ANY EXPLANATIONS SHOULD BE AS COMMENTS WITHIN THE CODE ITSELF.
    """
    
    return prompt

def detect_page_type(elements, full_text):
    """
    Analyzes elements and text to determine the likely page type
    """
    text_lower = full_text.lower()
    
    # Check for specific keywords
    if any(word in text_lower for word in ['login', 'sign in', 'password', 'username']):
        return 'login/authentication'
    elif any(word in text_lower for word in ['register', 'sign up', 'create account']):
        return 'registration'
    elif any(word in text_lower for word in ['checkout', 'payment', 'order', 'buy now', 'purchase']):
        return 'e-commerce/checkout'
    elif any(word in text_lower for word in ['contact', 'message', 'reach out', 'email us']):
        return 'contact'
    elif any(word in text_lower for word in ['about', 'our story', 'mission', 'team']):
        return 'about'
    elif any(word in text_lower for word in ['product', 'service', 'feature', 'pricing']):
        return 'product/service'
    elif any(word in text_lower for word in ['blog', 'article', 'news', 'post']):
        return 'blog/content'
    elif any(word in text_lower for word in ['dashboard', 'analytics', 'statistics', 'metrics']):
        return 'dashboard/analytics'
    elif any(word in text_lower for word in ['profile', 'account', 'settings', 'preferences']):
        return 'profile/account'
    elif len([e for e in elements if e.get('type') == 'input_field']) > 2:
        return 'form-based'
    elif len([e for e in elements if e.get('type') == 'image']) > 3:
        return 'gallery/portfolio'
    else:
        return 'general landing page'

def detect_color_scheme(detected_elements):
    """
    Extract color information from the detected elements if available.
    Returns a default professional color scheme if no colors detected.
    """
    detected_colors = []
    
    # Try to extract colors from any elements that have color information
    for element in detected_elements.get('elements', []):
        if 'color' in element:
            detected_colors.append(element['color'])
        if 'background_color' in element:
            detected_colors.append(element['background_color'])
            
    # If we have detected colors, use them
    if detected_colors:
        return {
            "detected_colors": detected_colors,
            "note": "These colors were detected from the wireframe elements"
        }
    
    # Otherwise provide a professional default color scheme
    return {
        "primary": "#3f51b5",
        "secondary": "#f50057",
        "text_dark": "#212121",
        "text_light": "#f5f5f5",
        "background": "#ffffff",
        "accent": "#ff4081",
        "note": "Default color scheme (no specific colors detected in wireframe)"
    }

def analyze_layout(elements):
    """
    Analyze the layout structure based on element positions
    """
    # Initialize layout sections
    layout = {
        "has_header": False,
        "has_footer": False,
        "has_sidebar": False,
        "column_structure": "single-column",
        "approximate_sections": []
    }
    
    # Extract position information
    y_positions = []
    x_positions = []
    
    for element in elements:
        if 'position' in element:
            if 'y' in element['position']:
                y_positions.append(element['position']['y'])
            if 'x' in element['position']:
                x_positions.append(element['position']['x'])
    
    # Check for clusters in vertical positions to identify horizontal divisions (sections)
    if y_positions:
        # Simple clustering to find major sections
        y_positions.sort()
        clusters = []
        current_cluster = [y_positions[0]]
        
        # Threshold for considering positions as part of the same section
        threshold = 100  
        
        for i in range(1, len(y_positions)):
            if y_positions[i] - y_positions[i-1] < threshold:
                current_cluster.append(y_positions[i])
            else:
                clusters.append(current_cluster)
                current_cluster = [y_positions[i]]
        
        clusters.append(current_cluster)
        
        # Add sections to layout analysis
        for i, cluster in enumerate(clusters):
            avg_position = sum(cluster) / len(cluster)
            if i == 0 and avg_position < 200:
                layout["has_header"] = True
                layout["approximate_sections"].append("header")
            elif i == len(clusters) - 1 and avg_position > 800:
                layout["has_footer"] = True
                layout["approximate_sections"].append("footer")
            else:
                layout["approximate_sections"].append(f"section_{i}")
    
    # Check for column structure based on x positions
    if x_positions:
        # Analyze the distribution of x positions to determine column structure
        x_positions.sort()
        max_x = max(x_positions) if x_positions else 1000
        left_side = len([x for x in x_positions if x < max_x * 0.3])
        right_side = len([x for x in x_positions if x > max_x * 0.7])
        
        if left_side > len(x_positions) * 0.2 and right_side > len(x_positions) * 0.2:
            layout["column_structure"] = "multi-column"
            
            if left_side > len(x_positions) * 0.3 and right_side < len(x_positions) * 0.2:
                layout["has_sidebar"] = True
                layout["sidebar_position"] = "left"
            elif right_side > len(x_positions) * 0.3 and left_side < len(x_positions) * 0.2:
                layout["has_sidebar"] = True
                layout["sidebar_position"] = "right"
    
    return layout

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
    
    # Validate the extracted content is actually code
    for key in result:
        if result[key] and not is_valid_code_content(result[key], key):
            logger.warning(f"Extracted {key} content doesn't appear to be valid code")
            # Keep the content but log a warning
    
    return result

def is_valid_code_content(content, code_type):
    """
    Performs basic validation to ensure extracted content looks like the expected code type.
    
    Args:
        content (str): The extracted code content
        code_type (str): The type of code ('html', 'css', or 'javascript')
    
    Returns:
        bool: True if content appears to be valid code of the specified type
    """
    if not content or len(content) < 10:
        return False
        
    if code_type == 'html':
        # Check for common HTML indicators
        return ('<' in content and '>' in content and 
                ('<!DOCTYPE' in content.upper() or '<HTML' in content.upper() or 
                 '<HEAD' in content.upper() or '<BODY' in content.upper() or
                 '<div' in content.lower()))
    
    elif code_type == 'css':
        # Check for common CSS indicators
        return ('{' in content and '}' in content and 
                (':' in content or '@media' in content.lower() or 
                 'margin' in content.lower() or 'padding' in content.lower()))
    
    elif code_type == 'javascript':
        # Check for common JS indicators
        return (('function' in content.lower() or 'const' in content.lower() or 
                'let' in content.lower() or 'var' in content.lower() or 
                'document.' in content.lower() or 
                'addEventListener' in content.lower()))
    
    return True