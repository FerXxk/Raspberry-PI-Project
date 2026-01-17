import os

# Rutas de Archivos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
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
MAX_USAGE_PERCENT = 85
STORAGE_CLEANUP_PERCENT = 5     # Porcentaje a liberar cuando se limpia por espacio
STORAGE_CLEANUP_INTERVAL = 1800 # 30 min

# Configuración de Audio
VOLUME_LEVEL = 100               # Volumen de reproducción (0-100)

# Configuración de Acceso Remoto
AUTO_START_VPN = True            # Iniciar Tailscale automáticamente con run.py

# Configuración de Telegram
TELEGRAM_TOKEN = "8517781523:AAHmklsFPDFfJQppkvaMlchH3Cpg2PtbFAc"
TELEGRAM_CHAT_ID = "7013484502" 
TELEGRAM_ALERT_DELAY = 2         # Segundos de espera antes de capturar foto para alerta

# Configuración de Modos de Operación
OPERATION_MODE = 2               # Modo por defecto: 1 = Portero, 2 = Video Vigilancia
MODE_DESCRIPTIONS = {
    1: "Modo Portero (Timbre con foto)",
    2: "Modo Video Vigilancia (Grabación por movimiento)"
}
