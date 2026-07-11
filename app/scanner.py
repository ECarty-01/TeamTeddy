import tempfile
import cv2
from musicScanner.main import process_image   # you will create this function

def run_scan(file):
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        file.save(tmp.name)
        img_path = tmp.name

    # Call your scanner logic
    notes_json = process_image(img_path)

    return notes_json
