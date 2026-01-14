import logging
from sense_hat import SenseHat

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Sensors")

class SensorManager:
    def __init__(self):
        self.sense = None
        try:
            self.sense = SenseHat()
            # self.sense.clear() # Optional: clear matrix
            logger.info("Sense HAT initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Sense HAT: {e}")
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
                logger.error(f"Error reading Sense HAT: {e}")
        
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
            logger.error(f"Error reading CPU temp: {e}")
            return "--°C"
