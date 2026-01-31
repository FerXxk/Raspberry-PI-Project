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
from modules.samba_service import ensure_samba_started
from modules.mode_manager import ModeManager
import config

def start_storage_manager(manager):
    while True:
        manager.ejecutar_limpieza()
        time.sleep(config.STORAGE_CLEANUP_INTERVAL)

def create_app():
    # Helper para crear la app 
    app = Flask(__name__, template_folder="app/templates", static_folder="app/static")
    app.register_blueprint(main_bp)
    return app

if __name__ == "__main__":
    # Silenciar logs de Werkzeug para una consola más limpia
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    print("Iniciando Sistema de Vigilancia (Restructured)...")
    
    # 0. Descargar modelo de IA si es necesario
    if config.USE_AI_DETECTION:
        try:
            from scripts.download_model import download_model
            download_model()
        except ImportError:
            print("Warning: Could not import download_model. Ensure scripts/download_model.py exists.")
    
    # Servicios base (VPN, Samba)
    start_vpn()
    ensure_samba_started()
    
    # Gestión de modos (Vigilancia / Portero)
    mode_manager = ModeManager()
    
    # Inicialización de módulos
    camera = VideoCamera(mode_manager=mode_manager)
    sensors = SensorManager(mode_manager=mode_manager, camera=camera)
    storage = GestorAlmacenamiento(config.PATH_NAS, config.MAX_DAYS_STORAGE, config.MAX_USAGE_PERCENT, config.STORAGE_CLEANUP_PERCENT)
    telegram = TelegramService(config.TELEGRAM_TOKEN, config.TELEGRAM_CHAT_ID, mode_manager=mode_manager)
    
    # Configuración de la web app y contexto
    app = create_app()
    app.camera = camera
    app.sensors = sensors
    app.telegram = telegram
    app.mode_manager = mode_manager
    
    # Vincular cámara con Telegram para alertas
    camera.set_telegram_service(telegram)
    
    # Inicio de hilos secundarios
    print("Iniciando Cámara...")
    camera.start()
    
    print("Monitorizando botones...")
    sensors.start_button_monitoring()
    
    print("Servicio Telegram activo...")
    telegram.start()
    
    print("Gestor de almacenamiento activo...")
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
    
    # Ejecución del servidor
    try:
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        pass
    finally:
        print("Shutting down...")
        camera.stop()
        sensors.stop_button_monitoring()
