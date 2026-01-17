import os

# Rutas de Archivos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# PATH_NAS = "/mnt/grabaciones_camara/"
# For Windows testing/development, we might want a local fallback, but User has this on Pi. 
# Keeping original path.
PATH_NAS = "/mnt/grabaciones_camara/"

# Configuración de Cámara
FPS = 10.0
RESOLUTION = (640, 480)

# Configuración de Detección de Movimiento
MIN_AREA = 5000                # Sensibilidad: área mínima en píxeles
TIEMPO_SIN_MOVIMIENTO = 5      # Segundos a esperar tras dejar de detectar movimiento

# Configuración de Grabación
MAX_DURACION = 60              # Duración máxima de un clip (segundos)

# Configuración de Almacenamiento
MAX_DAYS_STORAGE = 7
MAX_USAGE_PERCENT = 2
STORAGE_CLEANUP_INTERVAL = 600 # 10 min
