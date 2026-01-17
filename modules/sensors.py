import logging
import threading
from sense_hat import SenseHat

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Sensors")

class SensorManager:
    def __init__(self, mode_manager=None, camera=None):
        self.sense = None
        self.mode_manager = mode_manager
        self.camera = camera
        self.button_thread = None
        self.is_monitoring = False
        
        try:
            self.sense = SenseHat()
            # self.sense.clear() # Optional: clear matrix
            # self.sense.clear() # Optional: clear matrix
            logger.info("Sense HAT inicializado correctamente.")
        except Exception as e:
            logger.error(f"Fallo al inicializar Sense HAT: {e}")
            self.sense = None

    def get_readings(self):
        """Returns a dictionary with temperature, humidity, and pressure."""
        readings = {
            "location_temp": "--°C",
            "humidity": "--%",
            "pressure": "-- hPa",
            "cpu_temp": self._get_cpu_temp()
        }

        if self.sense:
            try:
                temp = self.sense.get_temperature()
                humidity = self.sense.get_humidity()
                pressure = self.sense.get_pressure()
                
                readings["location_temp"] = f"{temp:.1f}°C"
                readings["humidity"] = f"{humidity:.1f}%"
                readings["pressure"] = f"{pressure:.1f} hPa"
            except Exception as e:
                logger.error(f"Error leyendo Sense HAT: {e}")
        
        return readings

    def _get_cpu_temp(self):
        """Reads CPU temperature from system file."""
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                return f"{int(f.read()) / 1000:.1f}°C"
        except FileNotFoundError:
            # Common on simple Windows/Mac dev envs
            return "--°C"
        except Exception as e:
            logger.error(f"Error leyendo temperatura CPU: {e}")
            return "--°C"
    
    def start_button_monitoring(self):
        """Start monitoring the SenseHat joystick button for doorbell."""
        if not self.sense:
            logger.warning("SenseHat not available - button monitoring disabled")
            return
        
        if self.is_monitoring:
            logger.warning("Button monitoring already started")
            return
        
        self.is_monitoring = True
        self.button_thread = threading.Thread(target=self._monitor_button, daemon=True)
        self.button_thread.start()
        logger.info("Button monitoring started (middle joystick button)")
    
    def _monitor_button(self):
        """Monitor the middle button of the joystick for doorbell trigger."""
        import time
        
        last_state = False
        
        while self.is_monitoring:
            try:
                # Get joystick events
                events = self.sense.stick.get_events()
                
                for event in events:
                    # Check for middle button press (direction='middle', action='pressed')
                    if event.direction == 'middle' and event.action == 'pressed':
                        # Only trigger in Mode 1
                        current_mode = self.mode_manager.get_mode() if self.mode_manager else 2
                        
                        if current_mode == 1:
                            logger.info("[BUTTON] Doorbell button pressed in Mode 1")
                            
                            # Play doorbell sound
                            self._play_doorbell_sound()
                            
                            # Capture and send photo
                            if self.camera:
                                self.camera.capture_doorbell_photo()
                            else:
                                logger.warning("Camera not available for doorbell")
                        else:
                            logger.info(f"[BUTTON] Button pressed but in Mode {current_mode} (ignored)")
                
                time.sleep(0.1)  # Small delay to avoid CPU spinning
                
            except Exception as e:
                logger.error(f"Error monitoring button: {e}")
                time.sleep(1)
    
    def _play_doorbell_sound(self):
        """Play doorbell sound effect."""
        import os
        import config
        
        if not os.path.exists(config.DOORBELL_SOUND_PATH):
            logger.warning(f"Doorbell sound file not found: {config.DOORBELL_SOUND_PATH}")
            return
        
        try:
            # Play sound in background using ffplay
            # -nodisp: no display, -autoexit: exit after playing, -volume: set startup volume
            cmd = f"ffplay -nodisp -autoexit -hide_banner -loglevel quiet -volume {config.DOORBELL_SOUND_VOLUME} \"{config.DOORBELL_SOUND_PATH}\" &"
            os.system(cmd)
            logger.info("🔔 Doorbell sound playing")
        except Exception as e:
            logger.error(f"Error playing doorbell sound: {e}")
    
    def stop_button_monitoring(self):
        """Stop button monitoring."""
        self.is_monitoring = False
        if self.button_thread:
            self.button_thread.join(timeout=2)
        logger.info("Button monitoring stopped")
