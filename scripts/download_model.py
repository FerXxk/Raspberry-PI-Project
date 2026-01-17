import os
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ModelDownloader")

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/object_detector/efficientdet_lite0/int8/1/efficientdet_lite0.tflite"
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "repository")
MODEL_PATH = os.path.join(MODEL_DIR, "modelo_personas.tflite")

def download_model():
    """Downloads the MediaPipe model if it doesn't exist."""
    if os.path.exists(MODEL_PATH):
        logger.info(f"Model already exists at {MODEL_PATH}")
        return True

    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
        logger.info(f"Created directory: {MODEL_DIR}")

    logger.info(f"Downloading model from {MODEL_URL}...")
    try:
        response = requests.get(MODEL_URL, stream=True)
        response.raise_for_status()
        
        with open(MODEL_PATH, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        logger.info(f"Model downloaded successfully to {MODEL_PATH}")
        return True
    except Exception as e:
        logger.error(f"Error downloading model: {e}")
        return False

if __name__ == "__main__":
    download_model()
