import os
import time
import threading
from flask import Flask
from app.routes import main_bp
from modules.camera import VideoCamera
from modules.sensors import SensorManager
from modules.storage import GestorAlmacenamiento
from modules.telegram_service import TelegramService
from modules.vpn_service import start_vpn
from modules.mode_manager import ModeManager
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
    # Suppress output from Werkzeug
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    print("Iniciando Sistema de Vigilancia (Restructured)...")
    
    # 0. Iniciar VPN Tailscale
    start_vpn()
    
    # 1. Init Mode Manager
    mode_manager = ModeManager()
    
    # 2. Init Modules with mode manager
    camera = VideoCamera(mode_manager=mode_manager)
    sensors = SensorManager(mode_manager=mode_manager, camera=camera)
    storage = GestorAlmacenamiento(config.PATH_NAS, config.MAX_DAYS_STORAGE, config.MAX_USAGE_PERCENT, config.STORAGE_CLEANUP_PERCENT)
    telegram = TelegramService(config.TELEGRAM_TOKEN, config.TELEGRAM_CHAT_ID, mode_manager=mode_manager)
    
    # 3. Setup App
    app = create_app()
    # Attach modules to app context for routes to access
    app.camera = camera
    app.sensors = sensors
    app.telegram = telegram
    app.mode_manager = mode_manager
    
    # Wire Camera to Telegram for alerts
    camera.set_telegram_service(telegram)
    
    # 4. Start Background Threads
    # Camera
    print("Starting Camera...")
    camera.start()
    
    # Sensors (button monitoring)
    print("Starting Button Monitoring...")
    sensors.start_button_monitoring()
    
    # Telegram
    print("Starting Telegram Service...")
    telegram.start()
    
    # Storage
    print("Starting Storage Manager...")
    t_storage = threading.Thread(target=start_storage_manager, args=(storage,))
    t_storage.daemon = True
    t_storage.start()
    
    # Print Initial Storage Status
    stats = storage.obtener_estado_detallado()
    if stats:
        print("\n" + "="*40)
        print(" ESTADO DE ALMACENAMIENTO (NAS)")
        print("="*40)
        print(f" Total:     {stats['total_mb']:.2f} MB")
        print(f" Usado:     {stats['used_mb']:.2f} MB")
        print(f" Disponible: {stats['free_mb']:.2f} MB")
        print(f" Uso %:     {stats['percent']:.1f}%")
        print("="*40 + "\n")
    
    # Print Mode Status
    print("="*40)
    print(f" MODO ACTUAL: {mode_manager.get_mode()} - {mode_manager.get_mode_description()}")
    print("="*40 + "\n")
    
    # 5. Run Server
    try:
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        pass
    finally:
        print("Shutting down...")
        camera.stop()
        sensors.stop_button_monitoring()
