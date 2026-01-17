import logging
import os
import cv2
import numpy as np
import config

try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PersonDetector")

class PersonDetector:
    """
    Handles person detection using MediaPipe tasks.
    """
    def __init__(self):
        self.detector = None
        if not MEDIAPIPE_AVAILABLE:
            logger.error("MediaPipe library not found. AI detection will be disabled.")
            return

        if not config.USE_AI_DETECTION:
            logger.info("AI detection is disabled in config.")
            return

        self._initialize_detector()

    def _initialize_detector(self):
        """Initializes the Object Detector task."""
        try:
            if not os.path.exists(config.AI_MODEL_PATH):
                logger.warning(f"AI Model file not found at {config.AI_MODEL_PATH}")
                # We don't fail here, maybe it's downloaded later or shown as error on first detection
                return

            base_options = python.BaseOptions(model_asset_path=config.AI_MODEL_PATH)
            options = vision.ObjectDetectorOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.IMAGE,
                max_results=5,
                score_threshold=config.AI_CONFIDENCE_THRESHOLD,
                category_allowlist=['person']
            )
            self.detector = vision.ObjectDetector.create_from_options(options)
            logger.info("MediaPipe Person Detector initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing MediaPipe detector: {e}")
            self.detector = None

    def detect_person(self, frame):
        """
        Detecta si hay una persona en el frame.
        Retorna (bool, detections)
        """
        if self.detector is None:
            # Re-intentar inicialización si el modelo apareció después
            if os.path.exists(config.AI_MODEL_PATH):
                self._initialize_detector()
            
            if self.detector is None:
                return False, []

        try:
            # Importante: frame viene en BGR (OpenCV). Convertir a RGB para MediaPipe.
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            # Detección
            detection_result = self.detector.detect(mp_image)

            # Filtrar por confianza mínima (ya lo hace el objeto detector, pero podemos ser extra estrictos aquí si falla)
            has_person = False
            for detection in detection_result.detections:
                score = detection.categories[0].score
                if score >= config.AI_CONFIDENCE_THRESHOLD:
                    logger.info(f"IA: Persona detectada con confianza {score:.2f}")
                    has_person = True
                    break
            
            return has_person, detection_result.detections

        except Exception as e:
            logger.error(f"Error during AI detection: {e}")
            return False, []
