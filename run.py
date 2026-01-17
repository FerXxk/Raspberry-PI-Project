import os
import time
import threading
from flask import Flask
from app.routes import main_bp
from modules.camera import VideoCamera
from modules.sensors import SensorManager
from modules.storage import GestorAlmacenamiento
from modules.telegram_service import TelegramService
import config

def start_storage_manager(manager):
    while True:
        manager.ejecutar_limpieza()
        time.sleep(config.STORAGE_CLEANUP_INTERVAL)

def create_app():
    # Helper to create app independently if needed for tests
    app = Flask(__name__, template_folder="app/templates", static_folder="app/static")
    app.register_blueprint(main_bp)
    return app

if __name__ == "__main__":
    print("Iniciando Sistema de Vigilancia (Restructured)...")
    
    
    
    # 1. Init Modules
    camera = VideoCamera()
    sensors = SensorManager()
    storage = GestorAlmacenamiento(config.PATH_NAS, config.MAX_DAYS_STORAGE, config.MAX_USAGE_PERCENT)
    telegram = TelegramService(config.TELEGRAM_TOKEN, config.TELEGRAM_CHAT_ID)
    
    # 2. Setup App
    app = create_app()
    # Attach modules to app context for routes to access
    app.camera = camera
    app.sensors = sensors
    app.telegram = telegram
    
    # Wire Camera to Telegram for alerts
    camera.set_telegram_service(telegram)
    
    # 3. Start Background Threads
    # Camera
    print("Starting Camera...")
    camera.start()
    
    # Telegram
    print("Starting Telegram Service...")
    telegram.start()
    
    # Storage
    print("Starting Storage Manager...")
    t_storage = threading.Thread(target=start_storage_manager, args=(storage,))
    t_storage.daemon = True
    t_storage.start()
    
    # 4. Run Server
    try:
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        pass
    finally:
        print("Shutting down...")
        camera.stop()
