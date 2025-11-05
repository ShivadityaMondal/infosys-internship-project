# image_processing.py

from PIL import Image
from image_recognization import recognize_image # Import the CLIP-based function

class ProductIdentifier:
    def __init__(self, min_confidence=65.0):
        # The minimum confidence to consider a prediction certain
        self.min_confidence = min_confidence 

    def identify_product(self, image_input):
        try:
            # 1. Handle image input (path or PIL Image object)
            if not isinstance(image_input, Image.Image):
                image = Image.open(image_input) 
            else:
                image = image_input
            
            # 2. Recognize the image using the CLIP model
            label, confidence = recognize_image(image)

            # 3. Apply the confidence threshold
            if confidence >= self.min_confidence:
                return label, confidence
            else:
                # Returns the same low confidence message you had before
                return f"Low confidence ({confidence:.2f}%) — Not certain", confidence

        except Exception as e:
            # Handle file not found or other errors
            return f"Error processing image: {str(e)}", 0.0

# -------------------------------------------------------------
# Optional utility functions (Based on your teacher's second screenshot)
# These are useful for handling file uploads in a web context

import tempfile
import os

def save_temp_file(uploaded_file):
    """Saves an uploaded file to a temporary location."""
    # Note: 'uploaded_file' must be a file-like object with a .read() method
    temp = tempfile.NamedTemporaryFile(delete=False)
    temp.write(uploaded_file.read())
    temp.close()
    return temp.name

def cleanup_temp_file(path):
    """Removes a temporary file."""
    if os.path.exists(path):
        os.remove(path)