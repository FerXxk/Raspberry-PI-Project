import cv2
import time
import datetime
import os
import threading
import libcamera
import logging
from picamera2 import Picamera2
import config
from modules.detector import PersonDetector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Camera")

class VideoCamera:
    def __init__(self, mode_manager=None):
        self.output_frame = None
        self.lock = threading.Lock()
        self.status = "INICIANDO"
        self.recording_start_time = 0
        self.is_running = False
        self.thread = None
        self.mode_manager = mode_manager
        self.telegram_service = None
        
        # Initialize AI detector
        self.detector = PersonDetector() if config.USE_AI_DETECTION else None
        
        # Flag to signal mode change during recording
        self.stop_recording_flag = False
        
        # Init Camera
        try:
            self.picam2 = Picamera2()
            config_cam = self.picam2.create_preview_configuration(
                main={"size": config.RESOLUTION, "format": "RGB888"},
                transform=libcamera.Transform(vflip=True)
            )
            self.picam2.configure(config_cam)
            self.picam2.start()
            logger.info("Picamera2 iniciada correctamente.")
        except Exception as e:
            logger.error(f"Fallo al iniciar Picamera2: {e}")
            self.picam2 = None

    def start(self):
        if self.picam2 and not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._process_video)
            self.thread.daemon = True
            self.thread.start()
            
            # Register mode change observer
            if self.mode_manager:
                self.mode_manager.register_observer(self._on_mode_change)

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join()
        if self.picam2:
            self.picam2.stop()

    def get_frame(self):
        with self.lock:
            if self.output_frame is None:
                return None
            (flag, encodedImage) = cv2.imencode(".jpg", self.output_frame)
            if not flag:
                return None
            return encodedImage.tobytes()

    def get_status(self):
        """Returns status string and recording duration."""
        duration = 0
        if self.status == "GRABANDO":
            duration = int(time.time() - self.recording_start_time)
        return self.status, duration

    def _process_video(self):
        fondo = None
        grabando = False
        ultimo_movimiento_time = 0
        out = None
        self.stop_recording_flag = False
        
        # Ensure NAS path exists
        if not os.path.exists(config.PATH_NAS):
            try:
                os.makedirs(config.PATH_NAS)
            except OSError as e:
                logger.error(f"Error creando el directorio NAS: {e}")
                # We can continue but recording will fail.
        
        time.sleep(2) # Warmup

        while self.is_running:
            try:
                # Check current mode
                current_mode = self.mode_manager.get_mode() if self.mode_manager else 2
                
                # 1. Capture
                frame = self.picam2.capture_array()
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Update shared frame for web streaming (both modes)
                with self.lock:
                    self.output_frame = frame.copy()
                
                # Mode 1: Doorbell - just stream, no motion detection
                if current_mode == 1:
                    self.status = "MODO PORTERO"
                    time.sleep(0.1)  # Reduce CPU usage
                    continue
                
                # Mode 2: Video Surveillance - motion detection
                # 2. Processing
                gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gris = cv2.GaussianBlur(gris, (21, 21), 0)

                if fondo is None:
                    fondo = gris
                    continue

                diferencia = cv2.absdiff(fondo, gris)
                _, umbral = cv2.threshold(diferencia, 25, 255, cv2.THRESH_BINARY)
                umbral = cv2.dilate(umbral, None, iterations=2)

                contornos, _ = cv2.findContours(umbral.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                movimiento_actual = False
                for c in contornos:
                    if cv2.contourArea(c) < config.MIN_AREA:
                        continue
                    movimiento_actual = True
                    break

                ahora = time.time()
                if movimiento_actual:
                    ultimo_movimiento_time = ahora

                # 3. Recording Logic
                if movimiento_actual and not grabando:
                    # AI Filtering
                    if self.detector:
                        has_person, detections = self.detector.detect_person(frame)
                        if not has_person:
                            logger.info("AI: Motion detected but no person recognized. Skipping alert.")
                            movimiento_actual = False # Cancel trigger
                    
                if movimiento_actual and not grabando:
                    grabando = True
                    self.recording_start_time = ahora
                    timestamp = datetime.datetime.now().strftime("%d-%m-%Y__%H-%M-%S")
                    filename = os.path.join(config.PATH_NAS, f"alerta_{timestamp}.avi")
                    
                    logger.info(f"[REC] Start (Person Detected): {filename}" if self.detector else f"[REC] Start: {filename}")
                    
                    # Telegram Alert Trigger (Non-blocking)
                    if hasattr(self, 'telegram_service') and self.telegram_service:
                         # We launch a thread to wait and capture the snapshot so we don't block the video loop
                        threading.Thread(target=self._trigger_telegram_alert, args=(frame.copy(),), daemon=True).start()

                    fourcc = cv2.VideoWriter_fourcc(*'XVID')
                    height, width, _ = frame.shape
                    out = cv2.VideoWriter(filename, fourcc, config.FPS, (width, height))

                if grabando:
                    if out is not None:
                        out.write(frame)
                    
                    duracion_actual = ahora - self.recording_start_time
                    tiempo_quieto = ahora - ultimo_movimiento_time
                    
                    razon_parada = ""
                    if self.stop_recording_flag:
                        razon_parada = "Mode change requested"
                        self.stop_recording_flag = False
                    elif duracion_actual > config.MAX_DURACION:
                        razon_parada = "Max duration exceeded"
                    elif not movimiento_actual and tiempo_quieto > config.TIEMPO_SIN_MOVIMIENTO:
                        razon_parada = "No motion detected"
                    
                    if razon_parada:
                        grabando = False
                        if out is not None:
                            out.release()
                            out = None
                        logger.info(f"[STOP] {razon_parada}. Returning to surveillance.")
                        fondo = gris

                # 4. Status Update
                if grabando:
                    self.status = "GRABANDO"
                else:
                    self.status = "VIGILANDO"

                # 5. Visualization overlay (Mode 2 only)
                if movimiento_actual:
                    for c in contornos:
                        if cv2.contourArea(c) >= config.MIN_AREA:
                            (x, y, wa, ha) = cv2.boundingRect(c)
                            cv2.rectangle(frame, (x, y), (x + wa, y + ha), (0, 255, 0), 2)

            except Exception as e:
                logger.error(f"Error en el bucle de video: {e}")
                time.sleep(0.1)

    def set_telegram_service(self, service):
        self.telegram_service = service
    
    def _on_mode_change(self, old_mode, new_mode):
        """Callback when mode changes. Stop recording if switching from Mode 2."""
        logger.info(f"Camera received mode change: {old_mode} → {new_mode}")
        if old_mode == 2 and new_mode == 1:
            # Switching from surveillance to doorbell - stop any active recording
            self.stop_recording_flag = True
            logger.info("Stopping active recording due to mode change to Mode 1")
    
    def capture_doorbell_photo(self):
        """Capture a single photo for doorbell mode and send via Telegram."""
        if not self.picam2:
            logger.error("Camera not available for doorbell photo")
            return
        
        try:
            logger.info("[DOORBELL] Button pressed - capturing photo")
            
            # Capture frame
            frame = self.picam2.capture_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # Save temp file
            timestamp = datetime.datetime.now().strftime("%d-%m-%Y__%H-%M-%S")
            temp_path = os.path.join(config.BASE_DIR, f"doorbell_{timestamp}.jpg")
            cv2.imwrite(temp_path, frame)
            
            logger.info(f"[DOORBELL] Photo saved: {temp_path}")
            
            # Send via Telegram
            if self.telegram_service:
                self.telegram_service.send_alert(temp_path, caption="🔔 Timbre - Alguien en la puerta")
            
            # Cleanup after a delay (let telegram send first)
            def cleanup():
                time.sleep(5)
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    logger.info(f"[DOORBELL] Photo deleted: {temp_path}")
            
            threading.Thread(target=cleanup, daemon=True).start()
            
        except Exception as e:
            logger.error(f"Error capturing doorbell photo: {e}")

    def _trigger_telegram_alert(self, initial_frame):
        """Waits for configured delay and sends the current best frame (or initial)."""
        time.sleep(config.TELEGRAM_ALERT_DELAY)
        
        # Try to get a fresh frame if possible, else use initial
        frame_to_send = initial_frame
        if self.output_frame is not None:
            # We prefer a fresh frame after 2s as it might show the subject better
            with self.lock:
                frame_to_send = self.output_frame.copy()
        
        # Save temp file
        temp_path = os.path.join(config.BASE_DIR, "telegram_alert.jpg")
        cv2.imwrite(temp_path, frame_to_send)
        
        # Send
        if self.telegram_service:
            self.telegram_service.send_alert(temp_path)
