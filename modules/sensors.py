import logging
import threading
from sense_hat import SenseHat

# Configuración de logs
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
            logger.info("Sense HAT inicializado correctamente.")
        except Exception as e:
            logger.error(f"Fallo al inicializar Sense HAT: {e}")
            self.sense = None

    def get_readings(self):
        """Lectura de sensores: temperatura, humedad y presión."""
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
        """Lectura de la temperatura de la CPU."""
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                return f"{int(f.read()) / 1000:.1f}°C"
        except FileNotFoundError:
            return "--°C"
        except Exception as e:
            logger.error(f"Error leyendo temperatura CPU: {e}")
            return "--°C"
    
    def start_button_monitoring(self):
        """Inicia el hilo para monitorizar el botón del joystick."""
        if not self.sense:
            logger.warning("SenseHat no disponible")
            return
        
        if self.is_monitoring:
            logger.warning("Monitorización ya en marcha")
            return
        
        self.is_monitoring = True
        self.button_thread = threading.Thread(target=self._monitor_button, daemon=True)
        self.button_thread.start()
        logger.info("Button monitoring started (middle joystick button)")
    
    def _monitor_button(self):
        """Bucle de monitorización del botón del joystick."""
        import time
        
        last_state = False
        
        while self.is_monitoring:
            try:
                events = self.sense.stick.get_events()
                
                for event in events:
                    if event.direction == 'middle' and event.action == 'pressed':
                        # Solo funciona en Modo Portero
                        current_mode = self.mode_manager.get_mode() if self.mode_manager else 2
                        
                        if current_mode == 1:
                            logger.info("[BOTÓN] Timbre pulsado (Modo 1)")
                            
                            # Sonido de timbre
                            self._play_doorbell_sound()
                            
                            # Foto de quien llama
                            if self.camera:
                                self.camera.capture_doorbell_photo()
                            else:
                                logger.warning("Cámara no disponible")
                        else:
                            logger.info(f"[BOTÓN] Pulsado en modo {current_mode} (ignorado)")
                
                time.sleep(0.1)  
                
            except Exception as e:
                logger.error(f"Error monitoring button: {e}")
                time.sleep(1)
    
    def _play_doorbell_sound(self):
        """Reproduce el sonido del timbre."""
        import os
        import config
        
        if not os.path.exists(config.DOORBELL_SOUND_PATH):
            logger.warning(f"Doorbell sound file not found: {config.DOORBELL_SOUND_PATH}")
            return
        
        try:
            cmd = f"ffplay -nodisp -autoexit -hide_banner -loglevel quiet -volume {config.DOORBELL_SOUND_VOLUME} \"{config.DOORBELL_SOUND_PATH}\" &"
            os.system(cmd)
            logger.info("Sonando timbre...")
        except Exception as e:
            logger.error(f"Error playing doorbell sound: {e}")
    
    def stop_button_monitoring(self):
        """Stop button monitoring."""
        self.is_monitoring = False
        if self.button_thread:
            self.button_thread.join(timeout=2)
        logger.info("Button monitoring stopped")
